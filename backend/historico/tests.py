import pytest
from rest_framework.test import APIClient

from utils.apoio_testes import criar_usuario


@pytest.mark.django_db
def test_listar_historico_autenticado_nao_estoura_erro():
    """
    Regressão: permission_classes = (IsAuthenticated) sem vírgula não é uma
    tupla, o que fazia DRF falhar com TypeError ao montar get_permissions().
    """
    usuario = criar_usuario("Gerente", "gerente.historico@fho.edu.br", "GERENTE")

    client = APIClient()
    client.force_authenticate(user=usuario)

    resposta = client.get("/historico/")

    assert resposta.status_code == 200
