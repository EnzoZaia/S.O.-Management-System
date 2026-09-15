import pytest
from rest_framework.test import APIClient

from grupo.models import Grupo
from grupo_usuario.models import GrupoUsuario
from usuario.models import Usuario


def _criar_usuario(nome, email):
    return Usuario.objects.create(nome=nome, email=email, senha_hash="x", email_confirmado=True)


@pytest.mark.django_db
def test_criar_vinculo_grupo_usuario_com_dados_validos_e_persistido():
    """
    Regressão: validate() usava data.get('id_usuario')/data.get('id_grupo'),
    mas os campos do serializer se chamam 'usuario'/'grupo' (nomes do model),
    então a validação nunca reconhecia os dados enviados.
    """
    grupo_gerente = Grupo.objects.create(desc_grupo="GERENTE")
    grupo_tecnico = Grupo.objects.create(desc_grupo="TECNICO")

    usuario_gerente = _criar_usuario("Gerente", "gerente@fho.edu.br")
    GrupoUsuario.objects.create(usuario=usuario_gerente, grupo=grupo_gerente)

    usuario_alvo = _criar_usuario("Tecnico Novo", "tecnico.novo@fho.edu.br")

    client = APIClient()
    client.force_authenticate(user=usuario_gerente)

    resposta = client.post("/grupo-usuario/", {
        "usuario": usuario_alvo.pk,
        "grupo": grupo_tecnico.pk,
    })

    assert resposta.status_code == 201
    assert GrupoUsuario.objects.filter(usuario=usuario_alvo, grupo=grupo_tecnico).exists()


@pytest.mark.django_db
def test_criar_vinculo_duplicado_e_rejeitado():
    grupo_gerente = Grupo.objects.create(desc_grupo="GERENTE")
    grupo_tecnico = Grupo.objects.create(desc_grupo="TECNICO")

    usuario_gerente = _criar_usuario("Gerente", "gerente2@fho.edu.br")
    GrupoUsuario.objects.create(usuario=usuario_gerente, grupo=grupo_gerente)

    usuario_alvo = _criar_usuario("Tecnico Existente", "tecnico.existente@fho.edu.br")
    GrupoUsuario.objects.create(usuario=usuario_alvo, grupo=grupo_tecnico)

    client = APIClient()
    client.force_authenticate(user=usuario_gerente)

    resposta = client.post("/grupo-usuario/", {
        "usuario": usuario_alvo.pk,
        "grupo": grupo_tecnico.pk,
    })

    assert resposta.status_code == 400
