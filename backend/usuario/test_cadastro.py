from datetime import timedelta

import pytest
from django.contrib.auth.hashers import check_password
from django.core import mail
from django.utils import timezone
from rest_framework.test import APIClient

from perfil.models import Solicitante
from perfil.services import ID_POR_PERFIL, perfis_do_usuario
from usuario.models import Usuario
from utils.apoio_testes import criar_usuario

URL_CADASTRO = "/usuario/"
URL_REENVIO = "/usuario/reenviar-confirmacao/"


def _payload(**extra):
    dados = {"nome": "Maria Souza", "email": "maria.souza@fho.edu.br", "senha": "SenhaForte123"}
    dados.update(extra)
    return dados


def _criar_gerente():
    return criar_usuario("Gerente", "gerente.cad@fho.edu.br", "GERENTE")


def _recarregar(usuario):
    return Usuario.objects.get(pk=usuario.pk)


@pytest.mark.django_db
def test_auto_cadastro_cria_conta_pendente_solicitante_e_envia_email_sem_senha(settings):
    settings.FRONTEND_URL = "http://front.teste"

    resposta = APIClient().post(URL_CADASTRO, _payload(), format="json")

    assert resposta.status_code == 201
    assert resposta.data["status"] == "sucesso"
    assert "senha" not in resposta.data["dados"]

    usuario = Usuario.objects.get(email="maria.souza@fho.edu.br")
    assert usuario.email_confirmado is False
    assert usuario.ativo is True
    assert usuario.status_conta == "PENDENTE"
    assert usuario.ra is None
    assert check_password("SenhaForte123", usuario.senha_hash)
    assert usuario.dt_expiracao_token > timezone.now() + timedelta(hours=23)
    assert perfis_do_usuario(usuario) == []

    assert len(mail.outbox) == 1
    corpo = mail.outbox[0].body
    assert f"http://front.teste/confirmar-email/{usuario.token_confirmacao_email}" in corpo
    assert "SenhaForte123" not in corpo


@pytest.mark.django_db
def test_auto_cadastro_normaliza_email_para_minusculas():
    resposta = APIClient().post(URL_CADASTRO, _payload(email="  Maria.Souza@FHO.edu.br "), format="json")

    assert resposta.status_code == 201
    assert Usuario.objects.filter(email="maria.souza@fho.edu.br").exists()


@pytest.mark.django_db
@pytest.mark.parametrize("campo", ["nome", "email", "senha"])
def test_auto_cadastro_campo_ausente_retorna_erro_no_campo(campo):
    dados = _payload()
    dados.pop(campo)

    resposta = APIClient().post(URL_CADASTRO, dados, format="json")

    assert resposta.status_code == 400
    assert resposta.data["status"] == "erro"
    assert campo in resposta.data["erros"]
    assert not Usuario.objects.exists()


@pytest.mark.django_db
def test_auto_cadastro_senha_curta_e_dominio_invalido():
    resposta = APIClient().post(URL_CADASTRO, _payload(senha="1234567", email="maria@yahoo.com"), format="json")

    assert resposta.status_code == 400
    assert "senha" in resposta.data["erros"]
    assert "email" in resposta.data["erros"]


@pytest.mark.django_db
def test_auto_cadastro_email_ja_confirmado_e_recusado():
    criar_usuario("Existente", "maria.souza@fho.edu.br")

    resposta = APIClient().post(URL_CADASTRO, _payload(), format="json")

    assert resposta.status_code == 400
    assert "email" in resposta.data["erros"]


@pytest.mark.django_db
def test_auto_cadastro_nao_sobrescreve_cadastro_pendente_de_outra_pessoa():
    original = Usuario.objects.create(
        nome="Dona Original", email="maria.souza@fho.edu.br", senha_hash="hash-original", email_confirmado=False,
        token_confirmacao_email="tok-original", dt_expiracao_token=timezone.now() + timedelta(hours=10),
    )

    resposta = APIClient().post(URL_CADASTRO, _payload(), format="json")

    assert resposta.status_code == 400
    assert "reenviar" in resposta.data["erros"]["email"][0]
    original.refresh_from_db()
    assert original.senha_hash == "hash-original"
    assert original.token_confirmacao_email == "tok-original"


@pytest.mark.django_db
def test_gerente_cadastra_funcionario_com_grupo_e_listagem_segue_restrita():
    gerente = _criar_gerente()
    client = APIClient()
    client.force_authenticate(user=gerente)

    resposta = client.post(URL_CADASTRO, _payload(email="tecnico.novo@fho.edu.br", grupo=ID_POR_PERFIL["TECNICO"]), format="json")

    assert resposta.status_code == 201
    assert resposta.data["dados"]["grupo_descricao"] == "TECNICO"
    assert resposta.data["dados"]["id_grupo"] == ID_POR_PERFIL["TECNICO"]
    assert resposta.data["dados"]["grupos"] == ["TECNICO"]

    solicitante = criar_usuario("Sol", "sol.lista@fho.edu.br", "SOLICITANTE")
    outro = APIClient()
    outro.force_authenticate(user=solicitante)
    assert outro.get(URL_CADASTRO).status_code == 403


@pytest.mark.django_db
def test_gerente_sem_grupo_recebe_erro_no_campo_grupo():
    gerente = _criar_gerente()
    client = APIClient()
    client.force_authenticate(user=gerente)

    resposta = client.post(URL_CADASTRO, _payload(), format="json")

    assert resposta.status_code == 400
    assert "grupo" in resposta.data["erros"]


@pytest.mark.django_db
def test_confirmar_email_gera_ra_de_6_digitos_e_ativa_conta():
    APIClient().post(URL_CADASTRO, _payload(), format="json")
    usuario = Usuario.objects.get(email="maria.souza@fho.edu.br")

    resposta = APIClient().get(f"/usuario/confirmar-email/{usuario.token_confirmacao_email}/")

    assert resposta.status_code == 200
    ra = resposta.data["dados"]["ra"]
    assert len(ra) == 6 and ra.isdigit()

    usuario = _recarregar(usuario)
    assert usuario.email_confirmado is True
    assert usuario.status_conta == "ATIVA"
    assert usuario.ra == ra
    assert usuario.token_confirmacao_email is None
    solicitante = Solicitante.objects.get(usuario=usuario)
    assert (solicitante.tipo_vinculo, solicitante.identificador_vinculo) == ("ALUNO", ra)
    assert perfis_do_usuario(usuario) == ["SOLICITANTE"]


@pytest.mark.django_db
def test_confirmar_email_gera_ra_unico_mesmo_com_colisao(monkeypatch):
    outro = criar_usuario("Já tem RA", "ra@fho.edu.br")
    Solicitante.objects.create(usuario=outro, tipo_vinculo="ALUNO", identificador_vinculo="111111")
    pendente = Usuario.objects.create(
        nome="Pendente", email="pendente@fho.edu.br", senha_hash="x",
        token_confirmacao_email="tok-colisao", dt_expiracao_token=timezone.now() + timedelta(hours=1),
    )
    candidatos = iter(["111111", "222222"])
    monkeypatch.setattr("perfil.services.gerar_identificador_candidato", lambda: next(candidatos))

    resposta = APIClient().get("/usuario/confirmar-email/tok-colisao/")

    assert resposta.status_code == 200
    assert resposta.data["dados"]["ra"] == "222222"
    assert _recarregar(pendente).ra == "222222"


@pytest.mark.django_db
def test_confirmar_email_token_invalido():
    resposta = APIClient().get("/usuario/confirmar-email/nao-existe/")

    assert resposta.status_code == 400
    assert "inválido" in resposta.data["mensagem"]
    assert "expirad" not in resposta.data["mensagem"].lower()


@pytest.mark.django_db
def test_confirmar_email_token_expirado_mantem_conta_pendente():
    usuario = Usuario.objects.create(
        nome="Atrasado", email="atrasado@fho.edu.br", senha_hash="x",
        token_confirmacao_email="tok-velho", dt_expiracao_token=timezone.now() - timedelta(minutes=1),
    )

    resposta = APIClient().get("/usuario/confirmar-email/tok-velho/")

    assert resposta.status_code == 400
    assert "expirado" in resposta.data["mensagem"]
    usuario = _recarregar(usuario)
    assert usuario.email_confirmado is False
    assert usuario.status_conta == "PENDENTE"
    assert usuario.ra is None


@pytest.mark.django_db
def test_reenviar_confirmacao_gera_novo_token_para_conta_pendente():
    usuario = Usuario.objects.create(
        nome="Atrasado", email="atrasado@fho.edu.br", senha_hash="x",
        token_confirmacao_email="tok-velho", dt_expiracao_token=timezone.now() - timedelta(hours=1),
    )

    resposta = APIClient().post(URL_REENVIO, {"email": "Atrasado@fho.edu.br"}, format="json")

    assert resposta.status_code == 200
    usuario.refresh_from_db()
    assert usuario.token_confirmacao_email != "tok-velho"
    assert usuario.dt_expiracao_token > timezone.now() + timedelta(hours=23)
    assert len(mail.outbox) == 1
    assert usuario.token_confirmacao_email in mail.outbox[0].body

    assert APIClient().get("/usuario/confirmar-email/tok-velho/").status_code == 400
    assert APIClient().get(f"/usuario/confirmar-email/{usuario.token_confirmacao_email}/").status_code == 200


@pytest.mark.django_db
def test_reenviar_confirmacao_nao_revela_se_email_existe():
    criar_usuario("Confirmado", "ok@fho.edu.br")

    inexistente = APIClient().post(URL_REENVIO, {"email": "ninguem@fho.edu.br"}, format="json")
    confirmado = APIClient().post(URL_REENVIO, {"email": "ok@fho.edu.br"}, format="json")

    assert inexistente.status_code == confirmado.status_code == 200
    assert inexistente.data["mensagem"] == confirmado.data["mensagem"]
    assert len(mail.outbox) == 0


@pytest.mark.django_db
def test_reenviar_confirmacao_sem_email_retorna_400():
    resposta = APIClient().post(URL_REENVIO, {}, format="json")

    assert resposta.status_code == 400
    assert "email" in resposta.data["erros"]


@pytest.mark.django_db
def test_reenviar_confirmacao_respeita_intervalo_minimo_entre_envios():
    usuario = Usuario.objects.create(nome="Pendente", email="pend@fho.edu.br", senha_hash="x")
    client = APIClient()

    client.post(URL_REENVIO, {"email": "pend@fho.edu.br"}, format="json")
    usuario.refresh_from_db()
    primeiro_token = usuario.token_confirmacao_email
    client.post(URL_REENVIO, {"email": "pend@fho.edu.br"}, format="json")
    usuario.refresh_from_db()

    assert usuario.token_confirmacao_email == primeiro_token
    assert len(mail.outbox) == 1


@pytest.mark.django_db
def test_reenviar_confirmacao_tem_throttle_por_ip(settings):
    settings.REST_FRAMEWORK = {**settings.REST_FRAMEWORK, "DEFAULT_THROTTLE_RATES": {
        **settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"], "reenvio_confirmacao": "2/hour",
    }}
    from rest_framework.throttling import ScopedRateThrottle
    from rest_framework.settings import api_settings

    original = ScopedRateThrottle.THROTTLE_RATES
    ScopedRateThrottle.THROTTLE_RATES = api_settings.DEFAULT_THROTTLE_RATES
    try:
        client = APIClient()
        codigos = [client.post(URL_REENVIO, {"email": "x@fho.edu.br"}, format="json").status_code for _ in range(3)]
    finally:
        ScopedRateThrottle.THROTTLE_RATES = original

    assert codigos == [200, 200, 429]


@pytest.mark.django_db
def test_confirmacao_de_funcionario_cadastrado_pelo_gerente_nao_cria_perfil_de_solicitante():
    gerente = _criar_gerente()
    client = APIClient()
    client.force_authenticate(user=gerente)
    client.post(URL_CADASTRO, _payload(email="tec.conf@fho.edu.br", grupo=ID_POR_PERFIL["TECNICO"]), format="json")
    usuario = Usuario.objects.get(email="tec.conf@fho.edu.br")

    resposta = APIClient().get(f"/usuario/confirmar-email/{usuario.token_confirmacao_email}/")

    assert resposta.status_code == 200
    assert resposta.data["dados"]["ra"] is None
    assert perfis_do_usuario(_recarregar(usuario)) == ["TECNICO"]


@pytest.mark.django_db
def test_confirmacao_nao_reativa_conta_desativada():
    usuario = Usuario.objects.create(
        nome="Bloqueado", email="bloq@fho.edu.br", senha_hash="x", status_conta="DESATIVADA",
        token_confirmacao_email="tok-bloq", dt_expiracao_token=timezone.now() + timedelta(hours=1),
    )

    assert APIClient().get("/usuario/confirmar-email/tok-bloq/").status_code == 200
    assert _recarregar(usuario).status_conta == "DESATIVADA"
