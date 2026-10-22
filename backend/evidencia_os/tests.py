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
    ordem_servico = criar_os(criar_localizacao(), solicitante=solicitante, tecnico=tecnico, gestor=gestor, status_ordem_servico="EM_EXECUCAO")
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


@pytest.mark.parametrize("status_os", ["ENCERRADA", "CANCELADA", "CONCLUIDA"])
def test_status_fora_da_etapa_retorna_409(cenario, status_os):
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
