import pytest
from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from rest_framework.test import APIClient

from historico.models import Historico
from localizacao.models import Localizacao
from ordem_servico.fachada import OrdemServicoFacade, RespostaJaRegistradaError
from ordem_servico.models import OrdemServico
from os_participante.models import OsParticipante
from predio.models import Predio
from usuario.models import Usuario
from utils.apoio_testes import criar_os, criar_usuario
from validacao.models import EvidenciaValidacao, ValidacaoAtendimento

PNG = b"\x89PNG\r\n\x1a\n" + b"0" * 64


def _usuario(nome, email, grupo=None):
    return criar_usuario(nome, email, grupo)


def _cliente(usuario):
    client = APIClient()
    client.force_authenticate(user=usuario)
    return client


def _historico(ordem_servico):
    return list(
        Historico.objects.filter(ordem_servico=ordem_servico)
        .exclude(tipo_evento="ATRIBUICAO")
        .order_by("id_historico_ordem_servico")
        .values_list("desc_historico", flat=True)
    )


@pytest.fixture
def cenario(db):
    predio = Predio.objects.create(nome_predio="Bloco A")
    localizacao = Localizacao.objects.create(predio=predio, desc_localizacao="Sala 1")
    solicitante = _usuario("Solicitante", "sol.val@fho.edu.br", "SOLICITANTE")
    tecnico = _usuario("Tecnico", "tec.val@fho.edu.br", "TECNICO")
    gestor = _usuario("Gestor", "gestor.val@fho.edu.br", "GESTOR")
    ordem_servico = criar_os(
        localizacao, solicitante=solicitante, tecnico=tecnico, gestor=gestor,
        status_ordem_servico="EM_EXECUCAO", descricao_servico="Ar-condicionado pingando.",
    )
    return {"os": ordem_servico, "solicitante": solicitante, "tecnico": tecnico, "gestor": gestor, "localizacao": localizacao}


def _concluir_pelo_tecnico(cenario):
    resposta = _cliente(cenario["tecnico"]).patch(
        f"/ordem-servico/{cenario['os'].pk}/",
        {"status_ordem_servico": "CONCLUIDA", "observacao": "Dreno desobstruído."},
        format="json",
    )
    assert resposta.status_code == 200
    cenario["os"].refresh_from_db()
    return resposta


def test_tecnico_conclui_corretiva_e_ela_vai_para_aguardando_validacao(cenario):
    resposta = _concluir_pelo_tecnico(cenario)

    assert resposta.data["dados"]["status_ordem_servico"] == "AGUARDANDO_VALIDACAO"
    ordem_servico = cenario["os"]
    assert ordem_servico.status_ordem_servico == "AGUARDANDO_VALIDACAO"
    assert ValidacaoAtendimento.inicio_ciclo_atual(ordem_servico) is not None
    assert ordem_servico.dt_conclusao is None
    assert _historico(ordem_servico) == ["Status alterado: EM_EXECUCAO -> AGUARDANDO_VALIDACAO. Detalhes: Dreno desobstruído."]


def test_solicitante_aprova_e_os_fica_concluida(cenario):
    _concluir_pelo_tecnico(cenario)

    resposta = _cliente(cenario["solicitante"]).patch(f"/ordem-servico/{cenario['os'].pk}/validar/", {"aprovada": True}, format="json")

    assert resposta.status_code == 200
    dados = resposta.data["dados"]
    assert dados["status_ordem_servico"] == "CONCLUIDA"
    assert dados["validacao"]["aprovada"] is True
    assert dados["validacao"]["respondido_por_nome"] == "Solicitante"
    assert dados["validacao"]["dt_resposta"]

    cenario["os"].refresh_from_db()
    assert cenario["os"].status_ordem_servico == "CONCLUIDA"
    assert cenario["os"].dt_conclusao is not None
    assert _historico(cenario["os"])[-1] == "Status alterado: AGUARDANDO_VALIDACAO -> CONCLUIDA. Detalhes: Serviço aprovado por Solicitante."


def test_reprovacao_volta_ao_mesmo_tecnico_registra_justificativa_e_alerta_gestor(cenario, django_capture_on_commit_callbacks):
    _concluir_pelo_tecnico(cenario)

    with django_capture_on_commit_callbacks(execute=True):
        resposta = _cliente(cenario["solicitante"]).patch(
            f"/ordem-servico/{cenario['os'].pk}/validar/",
            {"aprovada": False, "justificativa": "Continua pingando no mesmo lugar."},
            format="json",
        )

    assert resposta.status_code == 200
    assert resposta.data["dados"]["status_ordem_servico"] == "EM_EXECUCAO"
    assert resposta.data["dados"]["validacao"]["justificativa"] == "Continua pingando no mesmo lugar."

    cenario["os"].refresh_from_db()
    assert cenario["os"].status_ordem_servico == "EM_EXECUCAO"
    assert cenario["os"].tecnico_id == cenario["tecnico"].pk
    historico = _historico(cenario["os"])
    assert "Justificativa: Continua pingando no mesmo lugar." in historico[-2]
    assert historico[-1] == "Alerta de reprovação enviado ao gestor Gestor."
    assert len(mail.outbox) == 1
    assert mail.outbox[0].to == ["gestor.val@fho.edu.br"]


@pytest.mark.parametrize("justificativa", [None, "", "curta", "x" * 201])
def test_reprovacao_exige_justificativa_de_10_a_200(cenario, justificativa):
    _concluir_pelo_tecnico(cenario)
    corpo = {"aprovada": False}
    if justificativa is not None:
        corpo["justificativa"] = justificativa

    resposta = _cliente(cenario["solicitante"]).patch(f"/ordem-servico/{cenario['os'].pk}/validar/", corpo, format="json")

    assert resposta.status_code == 400
    assert "justificativa" in resposta.data["erros"]
    cenario["os"].refresh_from_db()
    assert cenario["os"].status_ordem_servico == "AGUARDANDO_VALIDACAO"


def test_validar_sem_campo_aprovada_retorna_400(cenario):
    _concluir_pelo_tecnico(cenario)

    resposta = _cliente(cenario["solicitante"]).patch(f"/ordem-servico/{cenario['os'].pk}/validar/", {}, format="json")

    assert resposta.status_code == 400
    assert "aprovada" in resposta.data["erros"]


def test_reprovacao_multipart_com_evidencias(cenario, settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    _concluir_pelo_tecnico(cenario)

    resposta = _cliente(cenario["solicitante"]).patch(
        f"/ordem-servico/{cenario['os'].pk}/validar/",
        {
            "aprovada": "false",
            "justificativa": "Segue pingando, foto anexa.",
            "evidencias": [
                SimpleUploadedFile("foto1.png", PNG, content_type="image/png"),
                SimpleUploadedFile("foto2.png", PNG, content_type="image/png"),
            ],
        },
        format="multipart",
    )

    assert resposta.status_code == 200
    evidencias = EvidenciaValidacao.objects.filter(validacao__ordem_servico=cenario["os"])
    assert evidencias.count() == 2
    assert {e.nome_original for e in evidencias} == {"foto1.png", "foto2.png"}
    assert all((tmp_path / e.arquivo.name).exists() for e in evidencias)
    assert len(resposta.data["dados"]["validacao"]["evidencias"]) == 2


def test_evidencias_acima_do_limite_ou_nao_imagem_sao_recusadas(cenario, settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    _concluir_pelo_tecnico(cenario)
    url = f"/ordem-servico/{cenario['os'].pk}/validar/"
    client = _cliente(cenario["solicitante"])
    base = {"aprovada": "false", "justificativa": "Segue pingando, foto anexa."}

    quatro = [SimpleUploadedFile(f"f{i}.png", PNG, content_type="image/png") for i in range(4)]
    grande = SimpleUploadedFile("grande.png", PNG + b"0" * (5 * 1024 * 1024), content_type="image/png")
    pdf = SimpleUploadedFile("doc.pdf", b"%PDF-1.4", content_type="application/pdf")

    for arquivos in (quatro, [grande], [pdf]):
        resposta = client.patch(url, {**base, "evidencias": arquivos}, format="multipart")
        assert resposta.status_code == 400
        assert "evidencias" in resposta.data["erros"]

    assert not ValidacaoAtendimento.objects.exists()


def test_validar_fora_de_aguardando_validacao_retorna_400(cenario):
    resposta = _cliente(cenario["solicitante"]).patch(f"/ordem-servico/{cenario['os'].pk}/validar/", {"aprovada": True}, format="json")

    assert resposta.status_code == 400
    assert "aguardando" in resposta.data["mensagem"]


def test_usuario_sem_vinculo_recebe_403(cenario):
    _concluir_pelo_tecnico(cenario)
    estranho = _usuario("Estranho", "estranho@fho.edu.br", "SOLICITANTE")

    for ator in (estranho, cenario["tecnico"], cenario["gestor"]):
        resposta = _cliente(ator).patch(f"/ordem-servico/{cenario['os'].pk}/validar/", {"aprovada": True}, format="json")
        assert resposta.status_code == 403

    assert APIClient().patch(f"/ordem-servico/{cenario['os'].pk}/validar/", {"aprovada": True}, format="json").status_code == 401


def test_validar_os_inexistente_retorna_404(cenario):
    resposta = _cliente(cenario["solicitante"]).patch("/ordem-servico/999999/validar/", {"aprovada": True}, format="json")

    assert resposta.status_code == 404


def test_participante_vinculado_pode_validar_e_primeira_resposta_vence(cenario):
    participante = _usuario("Participante", "part.val@fho.edu.br", "SOLICITANTE")
    OsParticipante.objects.create(ordem_servico=cenario["os"], usuario=participante, dt_vinculo=timezone.now())
    _concluir_pelo_tecnico(cenario)
    url = f"/ordem-servico/{cenario['os'].pk}/validar/"

    primeira = _cliente(participante).patch(url, {"aprovada": True}, format="json")
    segunda = _cliente(cenario["solicitante"]).patch(url, {"aprovada": False, "justificativa": "Não concordo com isso."}, format="json")

    assert primeira.status_code == 200
    assert segunda.status_code == 409
    assert "já foi respondida" in segunda.data["mensagem"]
    assert segunda.data["dados"]["aprovada"] is True
    assert segunda.data["dados"]["respondido_por_nome"] == "Participante"
    assert ValidacaoAtendimento.objects.filter(ordem_servico=cenario["os"]).count() == 1
    cenario["os"].refresh_from_db()
    assert cenario["os"].status_ordem_servico == "CONCLUIDA"


def test_reprovada_e_concluida_de_novo_abre_novo_ciclo(cenario):
    _concluir_pelo_tecnico(cenario)
    url = f"/ordem-servico/{cenario['os'].pk}/validar/"
    client = _cliente(cenario["solicitante"])
    assert client.patch(url, {"aprovada": False, "justificativa": "Ainda com defeito aqui."}, format="json").status_code == 200

    assert client.patch(url, {"aprovada": True}, format="json").status_code == 409

    _concluir_pelo_tecnico(cenario)
    resposta = client.patch(url, {"aprovada": True}, format="json")

    assert resposta.status_code == 200
    respostas = ValidacaoAtendimento.objects.filter(ordem_servico=cenario["os"])
    assert respostas.count() == 1
    assert respostas.get().resultado == "APROVADA"
    assert respostas.get().justificativa is None
    assert any("Justificativa: Ainda com defeito aqui." in texto for texto in _historico(cenario["os"]))


def test_fachada_segunda_resposta_no_mesmo_ciclo_levanta_conflito(cenario):
    _concluir_pelo_tecnico(cenario)
    fachada = OrdemServicoFacade()
    fachada.validar(cenario["os"], cenario["solicitante"], aprovada=True)

    with pytest.raises(RespostaJaRegistradaError) as erro:
        fachada.validar(cenario["os"], cenario["solicitante"], aprovada=False, justificativa="Mudei de ideia agora.")

    assert erro.value.registro.aprovada is True


def test_get_validacao_retorna_ultima_ou_null(cenario):
    client = _cliente(cenario["solicitante"])
    url = f"/ordem-servico/{cenario['os'].pk}/validacao/"

    vazio = client.get(url)
    assert vazio.status_code == 200
    assert vazio.data["dados"] is None

    _concluir_pelo_tecnico(cenario)
    client.patch(f"/ordem-servico/{cenario['os'].pk}/validar/", {"aprovada": True}, format="json")

    resposta = client.get(url)
    assert resposta.data["dados"]["aprovada"] is True
    assert resposta.data["dados"]["respondido_por_nome"] == "Solicitante"


def test_get_validacao_de_os_fora_do_escopo_retorna_403(cenario):
    estranho = _usuario("Estranho", "estranho2@fho.edu.br", "SOLICITANTE")

    assert _cliente(estranho).get(f"/ordem-servico/{cenario['os'].pk}/validacao/").status_code == 403
    assert _cliente(cenario["gestor"]).get(f"/ordem-servico/{cenario['os'].pk}/validacao/").status_code == 200


def test_os_sem_gestor_reprovada_registra_alerta_sem_email(cenario, django_capture_on_commit_callbacks):
    cenario["os"] = criar_os(
        cenario["localizacao"], solicitante=cenario["solicitante"],
        status_ordem_servico="EM_EXECUCAO", descricao_servico="OS sem técnico nem gestor definidos.",
    )
    OrdemServicoFacade().alterar_status(cenario["os"], cenario["gestor"], {"status_ordem_servico": "CONCLUIDA"})

    with django_capture_on_commit_callbacks(execute=True):
        resposta = _cliente(cenario["solicitante"]).patch(
            f"/ordem-servico/{cenario['os'].pk}/validar/",
            {"aprovada": False, "justificativa": "Continua com o mesmo defeito."},
            format="json",
        )

    assert resposta.status_code == 200
    assert "sem gestor" in _historico(cenario["os"])[-1]
    assert len(mail.outbox) == 0


def test_dashboard_conta_aguardando_validacao(cenario):
    _concluir_pelo_tecnico(cenario)
    gerente = _usuario("Gerente", "gerente.val@fho.edu.br", "GERENTE")

    dados = _cliente(gerente).get("/ordem-servico/dashboard/indicadores/").data["dados"]

    assert dados["statusDetalhados"]["AGUARDANDO_VALIDACAO"] == 1
    assert dados["pendencias"]["aguardando_validacao"] == 1
    assert dados["aguardandoValidacao"] == 1


def test_patch_aceita_status_aguardando_validacao_e_trata_como_conclusao(cenario):
    resposta = _cliente(cenario["tecnico"]).patch(
        f"/ordem-servico/{cenario['os'].pk}/", {"status_ordem_servico": "AGUARDANDO_VALIDACAO"}, format="json",
    )

    assert resposta.status_code == 200
    cenario["os"].refresh_from_db()
    assert cenario["os"].status_ordem_servico == "AGUARDANDO_VALIDACAO"
    assert ValidacaoAtendimento.inicio_ciclo_atual(cenario["os"]) is not None
