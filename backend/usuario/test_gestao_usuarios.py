import pytest
from django.contrib.auth.hashers import make_password
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from auditoria_usuario.models import AuditoriaUsuario
from perfil.services import ID_POR_PERFIL, perfil_principal, perfis_do_usuario
from usuario.models import Usuario
from utils.apoio_testes import criar_localizacao, criar_os, atribuir

SENHA = "SenhaForte123"


def _criar_usuario(nome, email, nome_grupo=None, **extra):
    from utils.apoio_testes import criar_usuario

    return criar_usuario(nome, email, nome_grupo, senha_hash=make_password(SENHA), **extra)


def _cliente(usuario):
    client = APIClient()
    client.force_authenticate(user=usuario)
    return client


def _token_de(usuario):
    refresh = RefreshToken()
    refresh["id_usuario"] = usuario.id_usuario
    return refresh


@pytest.fixture
def gerente(db):
    return _criar_usuario("Gerente", "gerente.us20@fho.edu.br", "GERENTE")


@pytest.fixture
def tecnico(db):
    return _criar_usuario("Tecnico", "tecnico.us20@fho.edu.br", "TECNICO")


@pytest.mark.django_db
def test_gerente_desativa_usuario_com_auditoria_e_nada_e_apagado(gerente, tecnico):
    resposta = _cliente(gerente).patch(f"/usuario/{tecnico.pk}/situacao/", {"ativo": False}, format="json")

    assert resposta.status_code == 200
    assert resposta.data["dados"]["ativo"] is False

    tecnico.refresh_from_db()
    assert tecnico.ativo is False
    assert tecnico.status_conta == "DESATIVADA"
    assert tecnico.nome == "Tecnico"
    assert tecnico.email == "tecnico.us20@fho.edu.br"

    auditoria = AuditoriaUsuario.objects.get(usuario_alvo=tecnico)
    assert (auditoria.campo, auditoria.valor_anterior, auditoria.valor_novo, auditoria.autor_id) == ("status_conta", "ATIVA", "DESATIVADA", gerente.pk)


@pytest.mark.django_db
def test_gerente_reativa_usuario(gerente, tecnico):
    tecnico.status_conta = "DESATIVADA"
    tecnico.save()

    resposta = _cliente(gerente).patch(f"/usuario/{tecnico.pk}/situacao/", {"ativo": True}, format="json")

    assert resposta.status_code == 200
    tecnico.refresh_from_db()
    assert tecnico.status_conta == "ATIVA"


@pytest.mark.django_db
def test_situacao_sem_campo_ativo_retorna_400(gerente, tecnico):
    resposta = _cliente(gerente).patch(f"/usuario/{tecnico.pk}/situacao/", {}, format="json")

    assert resposta.status_code == 400
    assert "ativo" in resposta.data["erros"]


@pytest.mark.django_db
def test_delete_mantido_para_a_tela_desativa_em_vez_de_renomear(gerente, tecnico):
    resposta = _cliente(gerente).delete(f"/usuario/{tecnico.pk}/")

    assert resposta.status_code == 200
    tecnico.refresh_from_db()
    assert tecnico.ativo is False
    assert "[DESATIVADO]" not in tecnico.nome
    assert AuditoriaUsuario.objects.filter(usuario_alvo=tecnico, campo="status_conta").exists()


@pytest.mark.django_db
def test_listagem_filtra_por_ativo(gerente, tecnico):
    inativo = _criar_usuario("Inativo", "inativo@fho.edu.br", "TECNICO", status_conta="DESATIVADA")
    client = _cliente(gerente)

    padrao = {u["id_usuario"] for u in client.get("/usuario/").data}
    somente_inativos = {u["id_usuario"] for u in client.get("/usuario/?ativo=false").data}
    todos = {u["id_usuario"] for u in client.get("/usuario/?ativo=todos").data}

    assert inativo.pk not in padrao and tecnico.pk in padrao
    assert somente_inativos == {inativo.pk}
    assert {inativo.pk, tecnico.pk, gerente.pk} <= todos


@pytest.mark.django_db
def test_gerente_altera_perfil_com_auditoria(gerente, tecnico):
    resposta = _cliente(gerente).patch(f"/usuario/{tecnico.pk}/", {"grupo": ID_POR_PERFIL["GESTOR"]}, format="json")

    assert resposta.status_code == 200
    assert resposta.data["dados"]["grupo_descricao"] == "GESTOR"
    assert perfis_do_usuario(Usuario.objects.get(pk=tecnico.pk)) == ["GESTOR"]
    auditoria = AuditoriaUsuario.objects.get(usuario_alvo=tecnico, campo="grupo")
    assert (auditoria.valor_anterior, auditoria.valor_novo) == ("TECNICO", "GESTOR")


@pytest.mark.django_db
def test_alterar_para_o_mesmo_perfil_nao_gera_auditoria(gerente, tecnico):
    resposta = _cliente(gerente).patch(f"/usuario/{tecnico.pk}/", {"grupo": ID_POR_PERFIL["TECNICO"], "nome": "Tecnico Renomeado"}, format="json")

    assert resposta.status_code == 200
    assert not AuditoriaUsuario.objects.exists()


@pytest.mark.django_db
@pytest.mark.parametrize("perfil", ["GESTOR", "TECNICO", "SOLICITANTE"])
def test_somente_gerente_altera_perfil_ou_situacao_de_terceiros(perfil, tecnico):
    ator = _criar_usuario("Ator", f"ator.{perfil.lower()}@fho.edu.br", perfil)
    client = _cliente(ator)

    assert client.patch(f"/usuario/{tecnico.pk}/situacao/", {"ativo": False}, format="json").status_code == 403
    assert client.patch(f"/usuario/{tecnico.pk}/", {"grupo": ID_POR_PERFIL["GERENTE"]}, format="json").status_code == 403
    assert client.delete(f"/usuario/{tecnico.pk}/").status_code == 403
    assert client.get(f"/usuario/{tecnico.pk}/auditoria/").status_code == 403

    tecnico.refresh_from_db()
    assert tecnico.ativo is True
    assert perfil_principal(Usuario.objects.get(pk=tecnico.pk)) == "TECNICO"
    assert not AuditoriaUsuario.objects.exists()


@pytest.mark.django_db
def test_gerente_nao_desativa_a_si_mesmo(gerente):
    client = _cliente(gerente)

    assert client.patch(f"/usuario/{gerente.pk}/situacao/", {"ativo": False}, format="json").status_code == 403
    assert client.delete(f"/usuario/{gerente.pk}/").status_code == 403
    gerente.refresh_from_db()
    assert gerente.ativo is True


@pytest.mark.django_db
def test_gerente_nao_remove_o_proprio_perfil_gerente(gerente):
    resposta = _cliente(gerente).patch(f"/usuario/{gerente.pk}/", {"grupo": ID_POR_PERFIL["TECNICO"], "nome": "Novo Nome"}, format="json")

    assert resposta.status_code == 403
    gerente.refresh_from_db()
    assert gerente.nome == "Gerente", "a alteração inteira é desfeita (transação)"
    assert perfis_do_usuario(Usuario.objects.get(pk=gerente.pk)) == ["GERENTE"]


@pytest.mark.django_db
def test_login_de_usuario_desativado_e_recusado_com_403(tecnico):
    tecnico.status_conta = "DESATIVADA"
    tecnico.save()

    resposta = APIClient().post("/authentication/token/", {"email": tecnico.email, "senha": SENHA}, format="json")

    assert resposta.status_code == 403
    assert "desativado" in resposta.data["erro"]


@pytest.mark.django_db
def test_login_com_senha_errada_nao_revela_que_a_conta_esta_desativada(tecnico):
    tecnico.status_conta = "DESATIVADA"
    tecnico.save()

    resposta = APIClient().post("/authentication/token/", {"email": tecnico.email, "senha": "errada123"}, format="json")

    assert resposta.status_code == 401


@pytest.mark.django_db
def test_login_ativo_funciona_e_nao_imprime_a_senha(tecnico, capsys):
    resposta = APIClient().post("/authentication/token/", {"email": tecnico.email, "senha": SENHA}, format="json")

    assert resposta.status_code == 200
    assert "access" in resposta.data
    assert SENHA not in capsys.readouterr().out


@pytest.mark.django_db
def test_token_emitido_antes_da_desativacao_deixa_de_valer(gerente, tecnico):
    token = _token_de(tecnico)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")
    assert client.get("/usuario/meus-dados/").status_code == 200

    _cliente(gerente).patch(f"/usuario/{tecnico.pk}/situacao/", {"ativo": False}, format="json")

    assert client.get("/usuario/meus-dados/").status_code == 401
    refresh = APIClient().post("/authentication/token/refresh/", {"refresh": str(token)}, format="json")
    assert refresh.status_code == 403


@pytest.mark.django_db
def test_refresh_de_usuario_ativo_emite_novo_access(tecnico):
    resposta = APIClient().post("/authentication/token/refresh/", {"refresh": str(_token_de(tecnico))}, format="json")

    assert resposta.status_code == 200
    assert "access" in resposta.data


@pytest.mark.django_db
def test_gerente_le_auditoria_do_usuario(gerente, tecnico):
    client = _cliente(gerente)
    client.patch(f"/usuario/{tecnico.pk}/situacao/", {"ativo": False}, format="json")
    client.patch(f"/usuario/{tecnico.pk}/situacao/", {"ativo": True}, format="json")

    resposta = client.get(f"/usuario/{tecnico.pk}/auditoria/")

    assert resposta.status_code == 200
    registros = resposta.data["dados"]
    assert [r["valor_novo"] for r in registros] == ["ATIVA", "DESATIVADA"]
    assert registros[0]["autor_nome"] == "Gerente"


@pytest.mark.django_db
def test_atribuir_tecnico_por_perfil_sem_permissao_retorna_403(tecnico):
    ordem_servico = criar_os(criar_localizacao("Bloco Z", "Sala Z"))

    resposta = _cliente(tecnico).patch(f"/ordem-servico/{ordem_servico.pk}/atribuir-tecnico/", {"tecnico": tecnico.pk}, format="json")

    assert resposta.status_code == 403


@pytest.mark.django_db
def test_grupo_emula_lista_fixa_dos_quatro_perfis(gerente, tecnico):
    resposta = _cliente(gerente).get("/grupo/")

    assert resposta.status_code == 200
    assert resposta.data["dados"] == [
        {"id_grupo": 1, "desc_grupo": "GERENTE"},
        {"id_grupo": 2, "desc_grupo": "GESTOR"},
        {"id_grupo": 3, "desc_grupo": "TECNICO"},
        {"id_grupo": 4, "desc_grupo": "SOLICITANTE"},
    ]
    assert _cliente(gerente).get("/grupo/3/").data["dados"] == {"id_grupo": 3, "desc_grupo": "TECNICO"}
    assert _cliente(gerente).get("/grupo/9/").status_code == 404
    assert _cliente(tecnico).get("/grupo/").status_code == 403


@pytest.mark.django_db
def test_listagem_traz_id_grupo_e_grupo_descricao_do_perfil(gerente, tecnico):
    por_id = {u["id_usuario"]: u for u in _cliente(gerente).get("/usuario/").data}

    assert por_id[tecnico.pk]["grupo_descricao"] == "TECNICO"
    assert por_id[tecnico.pk]["id_grupo"] == 3
    assert por_id[tecnico.pk]["ativo"] is True


@pytest.mark.django_db
def test_rebaixar_tecnico_com_atribuicoes_e_recusado_sem_perder_o_perfil(gerente, tecnico):
    ordem_servico = criar_os(criar_localizacao())
    atribuir(ordem_servico, tecnico, gerente)

    resposta = _cliente(gerente).patch(f"/usuario/{tecnico.pk}/", {"grupo": ID_POR_PERFIL["SOLICITANTE"]}, format="json")

    assert resposta.status_code == 400
    assert "grupo" in resposta.data["erros"]
    assert perfis_do_usuario(Usuario.objects.get(pk=tecnico.pk)) == ["TECNICO"]


@pytest.mark.django_db
def test_promover_tecnico_com_atribuicoes_mantem_o_registro_tecnico_e_passa_a_gestor(gerente, tecnico):
    ordem_servico = criar_os(criar_localizacao())
    atribuir(ordem_servico, tecnico, gerente)

    resposta = _cliente(gerente).patch(f"/usuario/{tecnico.pk}/", {"grupo": ID_POR_PERFIL["GESTOR"]}, format="json")

    assert resposta.status_code == 200
    assert resposta.data["dados"]["grupo_descricao"] == "GESTOR"
    assert perfis_do_usuario(Usuario.objects.get(pk=tecnico.pk)) == ["GESTOR", "TECNICO"]
