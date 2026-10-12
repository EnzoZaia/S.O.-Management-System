import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from localizacao.models import Localizacao
from ordem_servico.fachada import OrdemServicoFacade
from ordem_servico.models import OrdemServico
from os_participante.models import OsParticipante
from predio.models import Predio
from usuario.models import Usuario
from utils.apoio_testes import criar_os, criar_usuario


def _usuario(nome, email, grupo=None):
    return criar_usuario(nome, email, grupo)


def _cliente(usuario):
    client = APIClient()
    client.force_authenticate(user=usuario)
    return client


@pytest.fixture
def cenario(db):
    predio = Predio.objects.create(nome_predio="Bloco C")
    localizacao = Localizacao.objects.create(predio=predio, desc_localizacao="Sala 3")
    maria = _usuario("Maria", "maria.portal@fho.edu.br", "SOLICITANTE")
    joao = _usuario("Joao", "joao.portal@fho.edu.br", "SOLICITANTE")
    ana = _usuario("Ana", "ana.portal@fho.edu.br", "SOLICITANTE")
    tecnico = _usuario("Carlos", "carlos.portal@fho.edu.br", "TECNICO")
    gestor = _usuario("Gestor", "gestor.portal@fho.edu.br", "GESTOR")

    fachada = OrdemServicoFacade()
    dados = {"localizacao": localizacao, "prioridade_urgencia": "NORMAL", "categoria_manutencao": "GERAIS"}
    os_maria = fachada.abrir(maria, {**dados, "descricao_servico": "Porta emperrada da sala."})
    os_joao = fachada.abrir(joao, {**dados, "descricao_servico": "Janela quebrada da sala."})
    os_ana = fachada.abrir(ana, {**dados, "descricao_servico": "Cadeira quebrada na sala."})
    OsParticipante.objects.create(ordem_servico=os_joao, usuario=maria, dt_vinculo=timezone.now())
    fachada.atribuir_tecnico(os_maria, tecnico, gestor)

    return {"maria": maria, "joao": joao, "ana": ana, "tecnico": tecnico,
            "os_maria": os_maria, "os_joao": os_joao, "os_ana": os_ana}


def test_solicitante_lista_as_proprias_e_as_presenciadas(cenario):
    resposta = _cliente(cenario["maria"]).get("/ordem-servico/")

    assert resposta.status_code == 200
    por_id = {o["id_ordem_servico"]: o for o in resposta.data}
    assert set(por_id) == {cenario["os_maria"].pk, cenario["os_joao"].pk}
    assert por_id[cenario["os_joao"].pk]["vinculo_presenciei"] is True
    assert por_id[cenario["os_maria"].pk]["vinculo_presenciei"] is False


def test_tecnico_nome_so_aparece_apos_atribuicao(cenario):
    por_id = {o["id_ordem_servico"]: o for o in _cliente(cenario["maria"]).get("/ordem-servico/").data}

    assert por_id[cenario["os_maria"].pk]["tecnico"] == cenario["tecnico"].pk
    assert por_id[cenario["os_maria"].pk]["tecnico_nome"] == "Carlos"
    assert por_id[cenario["os_joao"].pk]["tecnico"] is None
    assert por_id[cenario["os_joao"].pk]["tecnico_nome"] is None


def test_participante_ve_detalhe_e_quem_nao_participa_recebe_404(cenario):
    assert _cliente(cenario["maria"]).get(f"/ordem-servico/{cenario['os_joao'].pk}/").status_code == 200
    assert _cliente(cenario["maria"]).get(f"/ordem-servico/{cenario['os_ana'].pk}/").status_code == 404


def test_historico_do_escopo_traz_usuario_nome(cenario):
    resposta = _cliente(cenario["maria"]).get(f"/ordem-servico/{cenario['os_joao'].pk}/historico/")

    assert resposta.status_code == 200
    assert len(resposta.data) == 1
    assert resposta.data[0]["usuario_nome"] == "Joao"
    assert "aberta por Joao" in resposta.data[0]["desc_historico"]


def test_historico_fora_do_escopo_vem_vazio(cenario):
    resposta = _cliente(cenario["maria"]).get(f"/ordem-servico/{cenario['os_ana'].pk}/historico/")

    assert resposta.status_code == 200
    assert resposta.data == []


def test_historico_geral_do_solicitante_inclui_presenciadas(cenario):
    ids = {h["ordem_servico"] for h in _cliente(cenario["maria"]).get("/historico/").data}

    assert ids == {cenario["os_maria"].pk, cenario["os_joao"].pk}


def test_dashboard_do_solicitante_conta_presenciadas_sem_duplicar(cenario):
    OsParticipante.objects.create(ordem_servico=cenario["os_maria"], usuario=cenario["joao"], dt_vinculo=timezone.now())
    OsParticipante.objects.create(ordem_servico=cenario["os_maria"], usuario=cenario["ana"], dt_vinculo=timezone.now())

    dados = _cliente(cenario["maria"]).get("/ordem-servico/dashboard/indicadores/").data["dados"]

    assert dados["totalOrdens"] == 2
    assert sum(dados["statusDetalhados"].values()) == 2


def test_listagem_nao_duplica_os_com_varios_participantes(cenario):
    OsParticipante.objects.create(ordem_servico=cenario["os_maria"], usuario=cenario["joao"], dt_vinculo=timezone.now())
    OsParticipante.objects.create(ordem_servico=cenario["os_maria"], usuario=cenario["ana"], dt_vinculo=timezone.now())

    ids = [o["id_ordem_servico"] for o in _cliente(cenario["maria"]).get("/ordem-servico/").data]

    assert sorted(ids) == sorted({cenario["os_maria"].pk, cenario["os_joao"].pk})
