import pytest
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_listar_usuarios_sem_autenticacao_e_negado():
    """Regressão: permission_classes estava comentado e liberava o endpoint."""
    client = APIClient()

    resposta = client.get("/usuario/")

    assert resposta.status_code in (401, 403)


@pytest.mark.django_db
def test_criar_usuario_sem_autenticacao_e_negado():
    client = APIClient()

    resposta = client.post("/usuario/", {
        "nome": "Invasor",
        "email": "invasor@gmail.com",
        "senha": "qualquercoisa123",
        "grupo": 1,
    })

    assert resposta.status_code in (401, 403)
