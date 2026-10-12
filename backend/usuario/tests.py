import pytest
from rest_framework.test import APIClient

from perfil.services import perfis_do_usuario
from usuario.models import Usuario


@pytest.mark.django_db
def test_listar_usuarios_sem_autenticacao_e_negado():
    """Regressão: permission_classes estava comentado e liberava o endpoint."""
    client = APIClient()

    resposta = client.get("/usuario/")

    assert resposta.status_code in (401, 403)


@pytest.mark.django_db
def test_auto_cadastro_publico_ignora_grupo_informado_e_nao_concede_perfil():
    client = APIClient()

    resposta = client.post("/usuario/", {
        "nome": "Invasor Teste",
        "email": "invasor@gmail.com",
        "senha": "qualquercoisa123",
        "grupo": 1,
    })

    assert resposta.status_code == 201
    usuario = Usuario.objects.get(email="invasor@gmail.com")
    assert usuario.email_confirmado is False
    assert usuario.status_conta == "PENDENTE"
    assert perfis_do_usuario(usuario) == []
