import pytest
from django.db import IntegrityError
from rest_framework.test import APIClient

from ativo.models import Ativo
from historico.models import Historico
from ordem_servico.builders import OrdemServicoDiretor
from ordem_servico.constantes import STATUS_ATIVOS
from ordem_servico.fachada import OrdemServicoFacade
from ordem_servico.models import OrdemServico
from os_participante.models import OsParticipante
from utils.apoio_testes import criar_localizacao, criar_os, criar_usuario

URL = "/ordem-servico/"
URL_VERIFICAR = "/ordem-servico/verificar-duplicidade/"


def _cliente(usuario=None):
    client = APIClient()
    if usuario is not None:
        client.force_authenticate(user=usuario)
    return client


@pytest.fixture
def cenario(db):
    localizacao = criar_localizacao("Bloco D", "Sala 4")
    outra_sala = criar_localizacao("Bloco E", "Sala 5")
    ativo = Ativo.objects.create(localizacao=localizacao, codigo_patrimonial="PAT-100", tipo_ativo="AR_CONDICIONADO")
    maria = criar_usuario("Maria", "maria.us02@fho.edu.br", "SOLICITANTE")
    joao = criar_usuario("Joao", "joao.us02@fho.edu.br", "SOLICITANTE")
    return {"localizacao": localizacao, "outra_sala": outra_sala, "ativo": ativo, "maria": maria, "joao": joao}


def _payload(**extra):
    dados = {"descricao_servico": "Ar-condicionado pingando na sala.", "categoria_manutencao": "REFRIGERACAO", "prioridade_urgencia": "NAO"}
    dados.update(extra)
    return dados


def test_solicitante_registra_corretiva_pelo_id_do_ativo_com_local_inferido(cenario):
    resposta = _cliente(cenario["maria"]).post(URL, _payload(ativo=cenario["ativo"].pk), format="json")

    assert resposta.status_code == 201
    dados = resposta.data["dados"]
    assert dados["status_ordem_servico"] == "ABERTA"
    assert dados["localizacao"] == cenario["localizacao"].pk
    assert dados["ativo"] == cenario["ativo"].pk
    assert dados["solicitante"] == cenario["maria"].pk
    assert dados["total_afetados"] == 1
    ordem_servico = OrdemServico.objects.get(pk=dados["id_ordem_servico"])
    assert ordem_servico.status_ordem_servico == "EM_TRIAGEM"
    historico = Historico.objects.get(ordem_servico=ordem_servico)
    assert historico.usuario_id == cenario["maria"].pk
    assert historico.data_registro is not None
    assert "aberta por Maria" in historico.desc_historico


def test_solicitante_registra_corretiva_pelo_codigo_patrimonial(cenario):
    resposta = _cliente(cenario["maria"]).post(URL, _payload(codigo_patrimonial="pat-100", localizacao=cenario["localizacao"].pk), format="json")

    assert resposta.status_code == 201
    assert resposta.data["dados"]["ativo"] == cenario["ativo"].pk


def test_solicitante_sem_ativo_recebe_erro_no_campo_ativo(cenario):
    resposta = _cliente(cenario["maria"]).post(URL, _payload(localizacao=cenario["localizacao"].pk), format="json")

    assert resposta.status_code == 400
    assert "ativo" in resposta.data["erros"]
    assert not OrdemServico.objects.exists()


@pytest.mark.parametrize("campo, valor", [("codigo_patrimonial", "PAT-NAO-EXISTE"), ("ativo", 999999)])
def test_patrimonio_inexistente_retorna_400_no_campo(cenario, campo, valor):
    resposta = _cliente(cenario["maria"]).post(URL, _payload(**{campo: valor}), format="json")

    assert resposta.status_code == 400
    assert campo in resposta.data["erros"]


def test_localizacao_divergente_da_do_ativo_retorna_400(cenario):
    resposta = _cliente(cenario["maria"]).post(URL, _payload(ativo=cenario["ativo"].pk, localizacao=cenario["outra_sala"].pk), format="json")

    assert resposta.status_code == 400
    assert "localizacao" in resposta.data["erros"]


def test_descricao_ausente_retorna_400_no_campo(cenario):
    dados = _payload(ativo=cenario["ativo"].pk)
    dados.pop("descricao_servico")

    resposta = _cliente(cenario["maria"]).post(URL, dados, format="json")

    assert resposta.status_code == 400
    assert "descricao_servico" in resposta.data["erros"]


def test_totem_anonimo_continua_sem_ativo_mas_exige_localizacao(cenario):
    sem_local = _cliente().post(URL, {"descricao_servico": "[ALUNO: 123] - Problema: Torneira pingando.", "prioridade_urgencia": "NAO"}, format="json")
    com_local = _cliente().post(URL, {
        "localizacao": cenario["localizacao"].pk,
        "descricao_servico": "[ALUNO: 123] - Problema: Torneira pingando.",
        "prioridade_urgencia": "NAO",
    }, format="json")

    assert sem_local.status_code == 400
    assert "localizacao" in sem_local.data["erros"]
    assert com_local.status_code == 201
    assert com_local.data["dados"]["ativo"] is None


def test_duplicidade_retorna_409_com_ordem_existente_e_opcao_de_presenciar(cenario):
    _cliente(cenario["maria"]).post(URL, _payload(ativo=cenario["ativo"].pk), format="json")

    resposta = _cliente(cenario["joao"]).post(URL, _payload(ativo=cenario["ativo"].pk), format="json")

    assert resposta.status_code == 409
    assert "presenciou" in resposta.data["mensagem"]
    dados = resposta.data["dados"]
    assert dados["pode_presenciar"] is True
    assert dados["ja_vinculado"] is False
    existente = dados["ordem_existente"]
    assert existente["status_ordem_servico"] == "ABERTA"
    assert existente["ativo_patrimonio"] == "PAT-100"
    assert existente["localizacao_nome"] == "Sala 4"
    assert existente["total_afetados"] == 1
    assert "solicitante_nome" not in existente
    assert OrdemServico.objects.count() == 1


def test_duplicidade_para_quem_ja_e_o_solicitante_indica_ja_vinculado(cenario):
    _cliente(cenario["maria"]).post(URL, _payload(ativo=cenario["ativo"].pk), format="json")

    dados = _cliente(cenario["maria"]).post(URL, _payload(ativo=cenario["ativo"].pk), format="json").data["dados"]

    assert dados["ja_vinculado"] is True
    assert dados["pode_presenciar"] is False


@pytest.mark.parametrize("status_os", STATUS_ATIVOS)
def test_todo_status_ativo_bloqueia_nova_corretiva(cenario, status_os):
    criar_os(cenario["localizacao"], ativo=cenario["ativo"], status_ordem_servico=status_os)

    resposta = _cliente(cenario["maria"]).post(URL, _payload(ativo=cenario["ativo"].pk), format="json")

    assert resposta.status_code == 409


@pytest.mark.parametrize("status_os", ["ENCERRADA", "CANCELADA", "CONCLUIDA", "REPROVADA"])
def test_status_fora_do_conjunto_ativo_nao_bloqueia(cenario, status_os):
    criar_os(cenario["localizacao"], ativo=cenario["ativo"], status_ordem_servico=status_os)

    resposta = _cliente(cenario["maria"]).post(URL, _payload(ativo=cenario["ativo"].pk), format="json")

    assert resposta.status_code == 201


def test_preventiva_ativa_nao_bloqueia_corretiva(cenario):
    criar_os(cenario["localizacao"], ativo=cenario["ativo"], tipo_manutencao="PREVENTIVA")

    assert _cliente(cenario["maria"]).post(URL, _payload(ativo=cenario["ativo"].pk), format="json").status_code == 201


def test_erro_do_trigger_de_duplicidade_tambem_vira_409(cenario, monkeypatch):
    existente = criar_os(cenario["localizacao"], ativo=cenario["ativo"])
    monkeypatch.setattr(OrdemServicoFacade, "_garantir_sem_corretiva_ativa", staticmethod(lambda ativo, bloquear=False: None))

    def _trigger(self, **kwargs):
        raise IntegrityError(f"Já existe corretiva ativa para o ativo {cenario['ativo'].pk}")

    monkeypatch.setattr(OrdemServicoDiretor, "construir_corretiva_do_solicitante", _trigger)

    resposta = _cliente(cenario["joao"]).post(URL, _payload(ativo=cenario["ativo"].pk), format="json")

    assert resposta.status_code == 409
    assert resposta.data["dados"]["ordem_existente"]["id_ordem_servico"] == existente.pk


def test_verificar_duplicidade_sem_ordem_ativa(cenario):
    resposta = _cliente(cenario["maria"]).get(URL_VERIFICAR, {"ativo": cenario["ativo"].pk})

    assert resposta.status_code == 200
    assert resposta.data["dados"] == {"duplicada": False, "ordem_existente": None, "pode_presenciar": False, "ja_vinculado": False}


def test_verificar_duplicidade_com_ordem_ativa_por_codigo_e_anonimo(cenario):
    existente = criar_os(cenario["localizacao"], ativo=cenario["ativo"], solicitante=cenario["maria"])

    autenticado = _cliente(cenario["joao"]).get(URL_VERIFICAR, {"codigo_patrimonial": "PAT-100"}).data["dados"]
    anonimo = _cliente().get(URL_VERIFICAR, {"ativo": cenario["ativo"].pk}).data["dados"]

    assert autenticado["duplicada"] is True
    assert autenticado["ordem_existente"]["id_ordem_servico"] == existente.pk
    assert autenticado["pode_presenciar"] is True
    assert anonimo["pode_presenciar"] is False


@pytest.mark.parametrize("parametros, campo", [({}, "ativo"), ({"ativo": "abc"}, "ativo"), ({"ativo": 999999}, "ativo"), ({"codigo_patrimonial": "X-1"}, "codigo_patrimonial")])
def test_verificar_duplicidade_com_parametro_invalido_retorna_400(cenario, parametros, campo):
    resposta = _cliente(cenario["maria"]).get(URL_VERIFICAR, parametros)

    assert resposta.status_code == 400
    assert campo in resposta.data["erros"]


def test_presenciar_cria_vinculo_e_e_idempotente(cenario):
    ordem_servico = criar_os(cenario["localizacao"], ativo=cenario["ativo"], solicitante=cenario["maria"])
    url = f"/ordem-servico/{ordem_servico.pk}/presenciei/"

    primeira = _cliente(cenario["joao"]).post(url)
    segunda = _cliente(cenario["joao"]).post(url)

    assert primeira.status_code == 201
    assert primeira.data["dados"]["vinculo_presenciei"] is True
    assert primeira.data["dados"]["ordem"]["total_afetados"] == 2
    assert segunda.status_code == 200
    assert "já participa" in segunda.data["mensagem"]
    assert segunda.data["dados"]["ordem"]["total_afetados"] == 2
    assert OsParticipante.objects.filter(ordem_servico=ordem_servico).count() == 1
    assert Historico.objects.filter(ordem_servico=ordem_servico, desc_historico__contains="também presenciou").count() == 1


def test_solicitante_original_presenciar_nao_cria_vinculo(cenario):
    ordem_servico = criar_os(cenario["localizacao"], ativo=cenario["ativo"], solicitante=cenario["maria"])

    resposta = _cliente(cenario["maria"]).post(f"/ordem-servico/{ordem_servico.pk}/presenciei/")

    assert resposta.status_code == 200
    assert resposta.data["dados"]["ja_vinculado"] is True
    assert resposta.data["dados"]["vinculo_presenciei"] is False
    assert resposta.data["dados"]["ordem"]["total_afetados"] == 1
    assert not OsParticipante.objects.exists()


@pytest.mark.parametrize("status_os", ["ENCERRADA", "CANCELADA"])
def test_presenciar_os_finalizada_retorna_400(cenario, status_os):
    ordem_servico = criar_os(cenario["localizacao"], solicitante=cenario["maria"], status_ordem_servico=status_os)

    resposta = _cliente(cenario["joao"]).post(f"/ordem-servico/{ordem_servico.pk}/presenciei/")

    assert resposta.status_code == 400
    assert "status" in resposta.data["mensagem"]
    assert not OsParticipante.objects.exists()


def test_presenciar_exige_autenticacao_e_os_existente(cenario):
    ordem_servico = criar_os(cenario["localizacao"], solicitante=cenario["maria"])

    assert _cliente().post(f"/ordem-servico/{ordem_servico.pk}/presenciei/").status_code == 401
    assert _cliente(cenario["joao"]).post("/ordem-servico/999999/presenciei/").status_code == 404


def test_tecnico_tambem_pode_presenciar(cenario):
    tecnico = criar_usuario("Tec", "tec.us05@fho.edu.br", "TECNICO")
    ordem_servico = criar_os(cenario["localizacao"], solicitante=cenario["maria"])

    assert _cliente(tecnico).post(f"/ordem-servico/{ordem_servico.pk}/presenciei/").status_code == 201


def test_apos_vinculo_os_aparece_no_portal_do_participante(cenario):
    ordem_servico = criar_os(cenario["localizacao"], ativo=cenario["ativo"], solicitante=cenario["maria"])
    client = _cliente(cenario["joao"])
    assert client.get(URL).data == []

    client.post(f"/ordem-servico/{ordem_servico.pk}/presenciei/")

    lista = client.get(URL).data
    assert [o["id_ordem_servico"] for o in lista] == [ordem_servico.pk]
    assert lista[0]["vinculo_presenciei"] is True
    assert lista[0]["total_afetados"] == 2
    assert client.get(f"{URL}{ordem_servico.pk}/").status_code == 200
    assert client.get(f"{URL}{ordem_servico.pk}/historico/").status_code == 200


def test_total_afetados_sem_solicitante_conta_so_participantes_e_sem_n_mais_um(cenario, django_assert_max_num_queries):
    gerente = criar_usuario("Gerente", "gerente.us05@fho.edu.br", "GERENTE")
    totem = criar_os(cenario["localizacao"])
    for usuario in (cenario["maria"], cenario["joao"]):
        OsParticipante.objects.create(ordem_servico=totem, usuario=usuario)
    for indice in range(5):
        criar_os(cenario["localizacao"], solicitante=cenario["maria"], descricao_servico=f"OS extra {indice} para contagem.")

    with django_assert_max_num_queries(8):
        lista = _cliente(gerente).get(URL).data

    por_id = {o["id_ordem_servico"]: o for o in lista}
    assert por_id[totem.pk]["total_afetados"] == 2
    assert all(o["total_afetados"] == 1 for id_os, o in por_id.items() if id_os != totem.pk)


def test_desvincular_participante(cenario):
    ordem_servico = criar_os(cenario["localizacao"], solicitante=cenario["maria"])
    url = f"/ordem-servico/{ordem_servico.pk}/presenciei/"
    client = _cliente(cenario["joao"])

    assert client.delete(url).status_code == 404
    client.post(url)
    resposta = client.delete(url)

    assert resposta.status_code == 200
    assert resposta.data["dados"]["ordem"]["total_afetados"] == 1
    assert not OsParticipante.objects.exists()
