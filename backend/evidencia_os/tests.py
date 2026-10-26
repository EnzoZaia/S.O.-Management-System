import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from rest_framework.test import APIClient

from evidencia_os.models import EvidenciaOrdem
from os_participante.models import OsParticipante
from utils.apoio_testes import criar_localizacao, criar_os, criar_usuario

JPEG = b"\xff\xd8\xff\xe0" + b"0" * 60
PNG = b"\x89PNG\r\n\x1a\n" + b"0" * 60
WEBP = b"RIFF\x00\x00\x00\x00WEBPVP8 " + b"0" * 60
MP4 = b"\x00\x00\x00\x18ftypisom" + b"0" * 60
MOV = b"\x00\x00\x00\x14ftypqt  " + b"0" * 60
WEBM = b"\x1a\x45\xdf\xa3" + b"0" * 60


def _arquivo(nome, conteudo, tipo="application/octet-stream"):
    return SimpleUploadedFile(nome, conteudo, content_type=tipo)


def _cliente(usuario=None):
    client = APIClient()
    if usuario is not None:
        client.force_authenticate(user=usuario)
    return client


@pytest.fixture
def cenario(db, settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    solicitante = criar_usuario("Maria", "maria.ev@fho.edu.br", "SOLICITANTE")
    participante = criar_usuario("Joao", "joao.ev@fho.edu.br", "SOLICITANTE")
    tecnico = criar_usuario("Tec", "tec.ev@fho.edu.br", "TECNICO")
    gestor = criar_usuario("Gestor", "gestor.ev@fho.edu.br", "GESTOR")
    ordem_servico = criar_os(criar_localizacao(), solicitante=solicitante, tecnico=tecnico, gestor=gestor, status_ordem_servico="EM_TRIAGEM")
    OsParticipante.objects.create(ordem_servico=ordem_servico, usuario=participante, dt_vinculo=timezone.now())
    return {"os": ordem_servico, "solicitante": solicitante, "participante": participante, "tecnico": tecnico, "gestor": gestor, "tmp": tmp_path}


def _url(cenario):
    return f"/ordem-servico/{cenario['os'].pk}/evidencias/"


def test_solicitante_envia_fotos_e_videos_com_ordem_autor_e_data(cenario):
    resposta = _cliente(cenario["solicitante"]).post(_url(cenario), {"arquivos": [
        _arquivo("foto.jpg", JPEG, "image/jpeg"), _arquivo("tela.png", PNG, "image/png"), _arquivo("video.mp4", MP4, "video/mp4"),
    ]}, format="multipart")

    assert resposta.status_code == 201
    dados = resposta.data["dados"]
    assert [item["ordem"] for item in dados] == [1, 2, 3]
    assert [item["tipo_arquivo"] for item in dados] == ["IMAGEM", "IMAGEM", "VIDEO"]
    assert all(item["enviado_por_nome"] == "Maria" and item["dt_envio"] and item["url"] for item in dados)
    assert all((cenario["tmp"] / evidencia.arquivo.name).exists() for evidencia in EvidenciaOrdem.objects.all())


def test_participante_continua_a_sequencia(cenario):
    _cliente(cenario["solicitante"]).post(_url(cenario), {"arquivos": [_arquivo("a.jpg", JPEG)]}, format="multipart")

    resposta = _cliente(cenario["participante"]).post(_url(cenario), {"arquivos": [_arquivo("b.webp", WEBP), _arquivo("c.webm", WEBM), _arquivo("d.mov", MOV)]}, format="multipart")

    assert resposta.status_code == 201
    assert [item["ordem"] for item in resposta.data["dados"]] == [2, 3, 4]
    assert resposta.data["dados"][0]["enviado_por_nome"] == "Joao"


@pytest.mark.parametrize("ator", ["tecnico", "gestor"])
def test_quem_nao_e_solicitante_nem_participante_recebe_403(cenario, ator):
    resposta = _cliente(cenario[ator]).post(_url(cenario), {"arquivos": [_arquivo("a.jpg", JPEG)]}, format="multipart")

    assert resposta.status_code == 403
    assert not EvidenciaOrdem.objects.exists()


@pytest.mark.parametrize("status_os", ["APROVADA", "EM_EXECUCAO", "AGUARDANDO_VALIDACAO", "ENCERRADA", "CANCELADA", "CONCLUIDA"])
def test_evidencia_so_e_aceita_antes_da_triagem(cenario, status_os):
    cenario["os"].status_ordem_servico = status_os
    cenario["os"].save()

    resposta = _cliente(cenario["solicitante"]).post(_url(cenario), {"arquivos": [_arquivo("a.jpg", JPEG)]}, format="multipart")

    assert resposta.status_code == 409
    assert "status" in resposta.data["mensagem"]


def test_extensao_nao_permitida_retorna_400_com_limites(cenario):
    resposta = _cliente(cenario["solicitante"]).post(_url(cenario), {"arquivos": [_arquivo("doc.pdf", b"%PDF-1.4")]}, format="multipart")

    assert resposta.status_code == 400
    assert "5 MB" in resposta.data["mensagem"] and "30 MB" in resposta.data["mensagem"]


def test_conteudo_falso_com_extensao_de_imagem_e_recusado_e_nao_armazenado(cenario):
    resposta = _cliente(cenario["solicitante"]).post(_url(cenario), {"arquivos": [
        _arquivo("ok.jpg", JPEG), _arquivo("malicioso.png", b"MZ\x90\x00 executavel disfarcado", "image/png"),
    ]}, format="multipart")

    assert resposta.status_code == 400
    assert "não corresponde" in resposta.data["mensagem"]
    assert not EvidenciaOrdem.objects.exists()
    assert not list(cenario["tmp"].rglob("*.*"))


def test_extensao_diferente_do_conteudo_e_recusada(cenario):
    resposta = _cliente(cenario["solicitante"]).post(_url(cenario), {"arquivos": [_arquivo("foto.png", JPEG, "image/png")]}, format="multipart")

    assert resposta.status_code == 400


def test_arquivo_acima_do_limite_retorna_413_com_o_limite(cenario, settings):
    settings.EVIDENCIA_IMAGEM_TAMANHO_MAX_MB = 1

    resposta = _cliente(cenario["solicitante"]).post(
        _url(cenario), {"arquivos": [_arquivo("grande.jpg", JPEG + b"0" * (1024 * 1024))]}, format="multipart",
    )

    assert resposta.status_code == 413
    assert "1 MB" in resposta.data["mensagem"]


def test_limites_de_quantidade_sao_configuraveis(cenario, settings):
    settings.EVIDENCIA_MAX_POR_ENVIO = 2
    settings.EVIDENCIA_MAX_POR_ORDEM = 3
    client = _cliente(cenario["solicitante"])

    muitos = client.post(_url(cenario), {"arquivos": [_arquivo(f"{i}.jpg", JPEG) for i in range(3)]}, format="multipart")
    assert muitos.status_code == 400
    assert "no máximo 2" in muitos.data["mensagem"]

    assert client.post(_url(cenario), {"arquivos": [_arquivo("1.jpg", JPEG), _arquivo("2.jpg", JPEG)]}, format="multipart").status_code == 201
    estouro = client.post(_url(cenario), {"arquivos": [_arquivo("3.jpg", JPEG), _arquivo("4.jpg", JPEG)]}, format="multipart")
    assert estouro.status_code == 400
    assert "máximo 3" in estouro.data["mensagem"]


def test_envio_sem_arquivos_retorna_400(cenario):
    resposta = _cliente(cenario["solicitante"]).post(_url(cenario), {}, format="multipart")

    assert resposta.status_code == 400
    assert "arquivos" in resposta.data["erros"]


def test_perfis_autorizados_listam_com_autoria_em_ordem(cenario):
    _cliente(cenario["solicitante"]).post(_url(cenario), {"arquivos": [_arquivo("a.jpg", JPEG), _arquivo("b.png", PNG)]}, format="multipart")

    for ator in ("solicitante", "participante", "tecnico", "gestor"):
        resposta = _cliente(cenario[ator]).get(_url(cenario))
        assert resposta.status_code == 200
        assert [item["ordem"] for item in resposta.data["dados"]] == [1, 2]
        assert resposta.data["dados"][0]["enviado_por_nome"] == "Maria"

    estranho = criar_usuario("Estranho", "estranho.ev@fho.edu.br", "SOLICITANTE")
    assert _cliente(estranho).get(_url(cenario)).status_code == 403
    assert _cliente().get(_url(cenario)).status_code == 401


def test_gerente_visualiza_evidencias_da_abertura(cenario):
    _cliente(cenario["solicitante"]).post(_url(cenario), {"arquivos": [_arquivo("a.jpg", JPEG)]}, format="multipart")
    gerente = criar_usuario("Gerente", "gerente.ev@fho.edu.br", "GERENTE")

    resposta = _cliente(gerente).get(_url(cenario))

    assert resposta.status_code == 200
    assert [item["nome_original"] for item in resposta.data["dados"]] == ["a.jpg"]


def _ativo(localizacao, codigo="PAT-EV-1"):
    from ativo.models import Ativo
    return Ativo.objects.create(localizacao=localizacao, codigo_patrimonial=codigo, tipo_ativo="AR_CONDICIONADO", periodicidade_preventiva_dias=90)


def test_abertura_anonima_com_ativo_e_imagem(db, settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    localizacao = criar_localizacao("Bloco E", "Lab 1")
    ativo = _ativo(localizacao)

    resposta = _cliente().post("/ordem-servico/", {
        "localizacao": localizacao.pk, "ativo": ativo.pk,
        "descricao_servico": "[ALUNO: 123] - Problema: ar pingando",
        "arquivos": [_arquivo("foto.png", PNG, "image/png")],
    }, format="multipart")

    assert resposta.status_code == 201
    id_os = resposta.data["dados"]["id_ordem_servico"]
    evidencia = EvidenciaOrdem.objects.get(ordem_servico_id=id_os)
    assert evidencia.usuario_id is None
    assert resposta.data["dados"]["ativo"] == ativo.pk

    gestor = criar_usuario("Gestor E", "gestor.e@fho.edu.br", "GESTOR")
    lista = _cliente(gestor).get(f"/ordem-servico/{id_os}/evidencias/")
    assert lista.status_code == 200
    assert lista.data["dados"][0]["enviado_por_nome"] == "Solicitante anônimo"


def test_abertura_com_imagem_invalida_nao_cria_a_ordem(db, settings, tmp_path):
    from ordem_servico.models import OrdemServico
    settings.MEDIA_ROOT = tmp_path
    localizacao = criar_localizacao("Bloco F", "Sala 2")

    resposta = _cliente().post("/ordem-servico/", {
        "localizacao": localizacao.pk, "descricao_servico": "[ALUNO: 123] - Problema: cadeira quebrada",
        "arquivos": [_arquivo("foto.png", b"nao e imagem" * 10, "image/png")],
    }, format="multipart")

    assert resposta.status_code == 400
    assert "arquivos" in resposta.data["erros"]
    assert not OrdemServico.objects.exists()
    assert not EvidenciaOrdem.objects.exists()


def test_lista_publica_de_ativos_traz_so_o_necessario(db):
    localizacao = criar_localizacao("Bloco G", "Sala 3")
    outra = criar_localizacao("Bloco H", "Sala 4")
    ativo = _ativo(localizacao, "PAT-G")
    _ativo(outra, "PAT-H")

    resposta = _cliente().get(f"/ativo/publico/?localizacao={localizacao.pk}", HTTP_AUTHORIZATION="Bearer token.velho")

    assert resposta.status_code == 200
    assert resposta.data["dados"] == [{"id_ativo": ativo.pk, "codigo_patrimonial": "PAT-G", "tipo_ativo": "AR_CONDICIONADO", "localizacao": localizacao.pk}]
