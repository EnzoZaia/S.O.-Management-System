import pytest
from rest_framework.test import APIClient

from grupo.models import Grupo
from grupo_usuario.models import GrupoUsuario
from usuario.models import Usuario


@pytest.mark.django_db
def test_listar_historico_autenticado_nao_estoura_erro():
    """
    Regressão: permission_classes = (IsAuthenticated) sem vírgula não é uma
    tupla, o que fazia DRF falhar com TypeError ao montar get_permissions().
    """
    grupo_gerente = Grupo.objects.create(desc_grupo="GERENTE")
    usuario = Usuario.objects.create(
        nome="Gerente", email="gerente.historico@fho.edu.br", senha_hash="x", email_confirmado=True
    )
    GrupoUsuario.objects.create(usuario=usuario, grupo=grupo_gerente)

    client = APIClient()
    client.force_authenticate(user=usuario)

    resposta = client.get("/historico/")

    assert resposta.status_code == 200
