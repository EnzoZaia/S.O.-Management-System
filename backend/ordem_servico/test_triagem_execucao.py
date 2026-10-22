import pytest
from rest_framework.test import APIClient

from ativo.models import Ativo
from historico.models import Historico
from ordem_servico.models import OrdemServico
from perfil.models import Gestor
from utils.apoio_testes import atribuir, criar_localizacao, criar_os, criar_usuario


def _cliente(usuario):
    client = APIClient()
    client.force_authenticate(user=usuario)
    return client


def _patch(usuario, ordem_servico, corpo):
    return _cliente(usuario).patch(f"/ordem-servico/{ordem_servico.pk}/", corpo, format="json")


def _ultimo_historico(ordem_servico):
    return Historico.objects.filter(ordem_servico=ordem_servico).exclude(tipo_evento="ATRIBUICAO").order_by("-id_historico_ordem_servico").first()


@pytest.fixture
def cenario(db):
    localizacao = criar_localizacao()
    gestor = criar_usuario("Gestor", "gestor.tri@fho.edu.br", "GESTOR")
    tecnico = criar_usuario("Tec", "tec.tri@fho.edu.br", "TECNICO")
    solicitante = criar_usuario("Sol", "sol.tri@fho.edu.br", "SOLICITANTE")
    return {"localizacao": localizacao, "gestor": gestor, "tecnico": tecnico, "solicitante": solicitante}


def test_aprovacao_exige_categoria_e_prioridade_e_registra_historico(cenario):
    ordem_servico = criar_os(cenario["localizacao"], solicitante=cenario["solicitante"])

    sem_dados = _patch(cenario["gestor"], ordem_servico, {"status_ordem_servico": "APROVADA", "observacao": "Triagem aprovada."})
    assert sem_dados.status_code == 400
    assert "categoria_manutencao" in sem_dados.data["erros"]
    assert "prioridade_urgencia" in sem_dados.data["erros"]

    invalida = _patch(cenario["gestor"], ordem_servico, {"status_ordem_servico": "APROVADA", "categoria_manutencao": "XYZ", "prioridade_urgencia": "SIM"})
    assert invalida.status_code == 400
    assert "categoria_manutencao" in invalida.data["erros"]

    resposta = _patch(cenario["gestor"], ordem_servico, {
        "status_ordem_servico": "APROVADA", "categoria_manutencao": "ELETRICA", "prioridade_urgencia": "SIM",
        "observacao": "Triagem aprovada. Categoria: Elétrica; prioridade: Urgente.",
    })

    assert resposta.status_code == 200
    ordem_servico.refresh_from_db()
    assert (ordem_servico.status_ordem_servico, ordem_servico.categoria_manutencao, ordem_servico.prioridade_urgencia) == ("APROVADA", "ELETRICA", "URGENTE")
    historico = _ultimo_historico(ordem_servico)
    assert historico.usuario_id == cenario["gestor"].pk
    assert (historico.status_anterior, historico.status_novo) == ("EM_TRIAGEM", "APROVADA")
    assert historico.desc_historico == "Status alterado: ABERTA -> APROVADA. Detalhes: Triagem aprovada. Categoria: Elétrica; prioridade: Urgente."


@pytest.mark.parametrize("decisao", ["REPROVADA", "CANCELADA"])
def test_reprovacao_e_cancelamento_exigem_justificativa(cenario, decisao):
    ordem_servico = criar_os(cenario["localizacao"])

    sem_justificativa = _patch(cenario["gestor"], ordem_servico, {"status_ordem_servico": decisao})
    curta = _patch(cenario["gestor"], ordem_servico, {"status_ordem_servico": decisao, "observacao": "curta"})
    assert sem_justificativa.status_code == 400 and "observacao" in sem_justificativa.data["erros"]
    assert curta.status_code == 400

    resposta = _patch(cenario["gestor"], ordem_servico, {"status_ordem_servico": decisao, "observacao": "Fora do escopo de manutenção predial."})

    assert resposta.status_code == 200
    ordem_servico.refresh_from_db()
    assert ordem_servico.status_ordem_servico == decisao
    assert "Detalhes: Fora do escopo de manutenção predial." in _ultimo_historico(ordem_servico).desc_historico


def test_tecnico_nao_faz_triagem(cenario):
    ordem_servico = criar_os(cenario["localizacao"], tecnico=cenario["tecnico"])

    resposta = _patch(cenario["tecnico"], ordem_servico, {"status_ordem_servico": "CANCELADA", "observacao": "Não quero atender esta ordem."})

    assert resposta.status_code == 403


def test_reprovar_fora_da_triagem_retorna_400_de_status(cenario):
    ordem_servico = criar_os(cenario["localizacao"], tecnico=cenario["tecnico"], gestor=cenario["gestor"], status_ordem_servico="EM_EXECUCAO")

    resposta = _patch(cenario["gestor"], ordem_servico, {"status_ordem_servico": "REPROVADA", "observacao": "Não era para ter sido aprovada."})

    assert resposta.status_code == 400
    assert "status" in resposta.data["mensagem"]


def test_gestor_so_triagem_no_proprio_escopo_de_area(cenario):
    Gestor.objects.filter(usuario=cenario["gestor"]).update(area_atuacao="REFRIGERACAO")
    eletrica = criar_os(cenario["localizacao"], categoria_manutencao="ELETRICA", descricao_servico="Tomada sem energia no laboratório.")
    refrigeracao = criar_os(cenario["localizacao"], categoria_manutencao="REFRIGERACAO", descricao_servico="Ar-condicionado sem gelar na sala.")
    sem_categoria = criar_os(cenario["localizacao"], descricao_servico="Problema ainda sem categoria definida.")

    ids = {o["id_ordem_servico"] for o in _cliente(cenario["gestor"]).get("/ordem-servico/").data}
    assert ids == {refrigeracao.pk, sem_categoria.pk}

    fora = _patch(cenario["gestor"], eletrica, {"status_ordem_servico": "CANCELADA", "observacao": "Fora do meu escopo de atuação."})
    assert fora.status_code == 404
    eletrica.refresh_from_db()
    assert eletrica.status_ordem_servico == "EM_TRIAGEM"


def test_execucao_completa_registra_inicio_pausa_e_conclusao(cenario):
    ativo = Ativo.objects.create(localizacao=cenario["localizacao"], codigo_patrimonial="PAT-EX", tipo_ativo="AR_CONDICIONADO")
    ordem_servico = criar_os(cenario["localizacao"], solicitante=cenario["solicitante"], status_ordem_servico="APROVADA")
    atribuir(ordem_servico, cenario["tecnico"], cenario["gestor"])

    assert _patch(cenario["tecnico"], ordem_servico, {"status_ordem_servico": "EM_EXECUCAO", "observacao": "Técnico iniciou o serviço."}).status_code == 200
    sem_motivo = _patch(cenario["tecnico"], ordem_servico, {"status_ordem_servico": "AGUARDANDO_MATERIAL"})
    assert sem_motivo.status_code == 400 and "observacao" in sem_motivo.data["erros"]
    assert _patch(cenario["tecnico"], ordem_servico, {"status_ordem_servico": "AGUARDANDO_MATERIAL", "observacao": "Falta capacitor 35uF."}).status_code == 200
    assert _patch(cenario["tecnico"], ordem_servico, {"status_ordem_servico": "EM_EXECUCAO", "observacao": "Técnico retomou o serviço."}).status_code == 200

    incompleta = _patch(cenario["tecnico"], ordem_servico, {"status_ordem_servico": "CONCLUIDA"})
    assert incompleta.status_code == 400
    assert {"observacao", "causa_raiz"} <= set(incompleta.data["erros"])

    resposta = _patch(cenario["tecnico"], ordem_servico, {
        "status_ordem_servico": "CONCLUIDA", "observacao": "Serviço concluído [PAT: PAT-EX]. Capacitor trocado.",
        "causa_raiz": "Desgaste natural", "ativo": ativo.pk,
    })

    assert resposta.status_code == 200
    assert resposta.data["dados"]["status_ordem_servico"] == "AGUARDANDO_VALIDACAO"
    ordem_servico.refresh_from_db()
    assert ordem_servico.causa_raiz == "Desgaste natural"
    assert ordem_servico.ativo_id == ativo.pk
    eventos = list(Historico.objects.filter(ordem_servico=ordem_servico, status_novo__isnull=False).order_by("id_historico_ordem_servico").values_list("status_novo", flat=True))
    assert eventos == ["EM_EXECUCAO", "AGUARDANDO_MATERIAL", "EM_EXECUCAO", "AGUARDANDO_VALIDACAO"]

    historico = _cliente(cenario["tecnico"]).get(f"/ordem-servico/{ordem_servico.pk}/historico/").data
    assert all("data_registro" in evento and "status_novo" in evento for evento in historico)


def test_tecnico_so_altera_ordens_atribuidas_a_ele(cenario):
    outro = criar_usuario("Outro", "outro.tri@fho.edu.br", "TECNICO")
    ordem_servico = criar_os(cenario["localizacao"], tecnico=outro, status_ordem_servico="APROVADA")

    resposta = _patch(cenario["tecnico"], ordem_servico, {"status_ordem_servico": "EM_EXECUCAO", "observacao": "Tentando iniciar."})

    assert resposta.status_code == 404


def test_nao_inicia_execucao_sem_tecnico_nem_conclui_sem_ter_iniciado(cenario):
    sem_tecnico = criar_os(cenario["localizacao"], status_ordem_servico="APROVADA")
    resposta = _patch(cenario["gestor"], sem_tecnico, {"status_ordem_servico": "EM_EXECUCAO"})
    assert resposta.status_code in (400, 404)

    aprovada = criar_os(cenario["localizacao"], tecnico=cenario["tecnico"], status_ordem_servico="APROVADA")
    direto = _patch(cenario["tecnico"], aprovada, {"status_ordem_servico": "CONCLUIDA", "observacao": "Concluído sem iniciar.", "causa_raiz": "Mau uso"})
    assert direto.status_code == 400
    assert "status" in direto.data["mensagem"]
    assert OrdemServico.objects.get(pk=aprovada.pk).status_ordem_servico == "APROVADA"
