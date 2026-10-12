import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from historico.models import Historico
from localizacao.models import Localizacao
from ordem_servico.models import OrdemServico
from os_participante.models import OsParticipante
from predio.models import Predio
from usuario.models import Usuario
from validacao.models import ValidacaoAtendimento
from utils.apoio_testes import criar_os, criar_usuario


def _usuario(nome, email, grupo=None):
    return criar_usuario(nome, email, grupo)


def _cliente(usuario):
    client = APIClient()
    client.force_authenticate(user=usuario)
    return client


@pytest.fixture
def cenario(db):
    predio = Predio.objects.create(nome_predio="Bloco B")
    localizacao = Localizacao.objects.create(predio=predio, desc_localizacao="Sala 2")
    solicitante = _usuario("Solicitante", "sol.ava@fho.edu.br", "SOLICITANTE")
    tecnico = _usuario("Carlos", "tec.ava@fho.edu.br", "TECNICO")
    ordem_servico = criar_os(
        localizacao, solicitante=solicitante, tecnico=tecnico,
        status_ordem_servico="EM_EXECUCAO", descricao_servico="Tomada sem energia.",
    )
    return {"os": ordem_servico, "solicitante": solicitante, "tecnico": tecnico}


def _ate_concluida(cenario, aprovada=True):
    _cliente(cenario["tecnico"]).patch(f"/ordem-servico/{cenario['os'].pk}/", {"status_ordem_servico": "CONCLUIDA"}, format="json")
    corpo = {"aprovada": aprovada} if aprovada else {"aprovada": False, "justificativa": "Tomada continua sem energia."}
    resposta = _cliente(cenario["solicitante"]).patch(f"/ordem-servico/{cenario['os'].pk}/validar/", corpo, format="json")
    assert resposta.status_code == 200


def _avaliar(usuario, ordem_servico, corpo):
    return _cliente(usuario).post(f"/ordem-servico/{ordem_servico.pk}/avaliar/", corpo, format="json")


def test_avaliacao_registra_nota_e_encerra_a_os(cenario):
    _ate_concluida(cenario)

    resposta = _avaliar(cenario["solicitante"], cenario["os"], {"nota": 5, "comentario": "Rápido e caprichoso."})

    assert resposta.status_code == 201
    dados = resposta.data["dados"]
    assert dados["status_ordem_servico"] == "ENCERRADA"
    assert dados["avaliacao"]["nota"] == 5
    assert dados["avaliacao"]["comentario"] == "Rápido e caprichoso."
    assert dados["avaliacao"]["avaliado_por_nome"] == "Solicitante"
    assert dados["avaliacao"]["dt_avaliacao"]

    cenario["os"].refresh_from_db()
    assert cenario["os"].status_ordem_servico == "ENCERRADA"
    avaliacao = ValidacaoAtendimento.objects.get(ordem_servico=cenario["os"], nota__isnull=False)
    assert avaliacao.aprovada is True
    assert avaliacao.nota == 5
    assert Historico.objects.filter(ordem_servico=cenario["os"], desc_historico__contains="CONCLUIDA -> ENCERRADA").exists()


def test_comentario_e_opcional(cenario):
    _ate_concluida(cenario)

    resposta = _avaliar(cenario["solicitante"], cenario["os"], {"nota": 3})

    assert resposta.status_code == 201
    assert resposta.data["dados"]["avaliacao"]["comentario"] is None


@pytest.mark.parametrize("nota", [None, 0, 6, "abc", 4.5, True])
def test_nota_obrigatoria_de_1_a_5(cenario, nota):
    _ate_concluida(cenario)
    corpo = {} if nota is None else {"nota": nota}

    resposta = _avaliar(cenario["solicitante"], cenario["os"], corpo)

    assert resposta.status_code == 400
    assert "nota" in resposta.data["erros"]
    assert not any(p in resposta.data["mensagem"].lower() for p in ("status", "aguardando", "valida"))
    cenario["os"].refresh_from_db()
    assert cenario["os"].status_ordem_servico == "CONCLUIDA"


def test_comentario_acima_de_300_caracteres_e_recusado(cenario):
    _ate_concluida(cenario)

    resposta = _avaliar(cenario["solicitante"], cenario["os"], {"nota": 4, "comentario": "x" * 301})

    assert resposta.status_code == 400
    assert "comentario" in resposta.data["erros"]


def test_avaliacao_duplicada_retorna_409_com_a_existente(cenario):
    _ate_concluida(cenario)
    _avaliar(cenario["solicitante"], cenario["os"], {"nota": 4})

    resposta = _avaliar(cenario["solicitante"], cenario["os"], {"nota": 1})

    assert resposta.status_code == 409
    assert "já foi avaliado" in resposta.data["mensagem"]
    assert resposta.data["dados"]["nota"] == 4
    assert ValidacaoAtendimento.objects.filter(nota__isnull=False).count() == 1


def test_avaliar_antes_da_validacao_aprovada_retorna_400(cenario):
    resposta = _avaliar(cenario["solicitante"], cenario["os"], {"nota": 5})
    assert resposta.status_code == 400
    assert "status" in resposta.data["mensagem"]

    _ate_concluida(cenario, aprovada=False)
    resposta = _avaliar(cenario["solicitante"], cenario["os"], {"nota": 5})
    assert resposta.status_code == 400
    assert not ValidacaoAtendimento.objects.filter(nota__isnull=False).exists()


def test_concluida_legada_sem_validacao_nao_pode_ser_avaliada(cenario):
    cenario["os"].status_ordem_servico = "CONCLUIDA"
    cenario["os"].save()

    resposta = _avaliar(cenario["solicitante"], cenario["os"], {"nota": 5})

    assert resposta.status_code == 400
    assert "valida" in resposta.data["mensagem"]


def test_somente_participantes_avaliam(cenario):
    _ate_concluida(cenario)
    estranho = _usuario("Estranho", "estranho.ava@fho.edu.br", "SOLICITANTE")
    participante = _usuario("Participante", "part.ava@fho.edu.br", "SOLICITANTE")
    OsParticipante.objects.create(ordem_servico=cenario["os"], usuario=participante, dt_vinculo=timezone.now())

    assert _avaliar(estranho, cenario["os"], {"nota": 5}).status_code == 403
    assert _avaliar(cenario["tecnico"], cenario["os"], {"nota": 5}).status_code == 403
    assert _avaliar(participante, cenario["os"], {"nota": 5}).status_code == 201


def test_get_avaliacao_retorna_registro_ou_null(cenario):
    client = _cliente(cenario["solicitante"])
    url = f"/ordem-servico/{cenario['os'].pk}/avaliacao/"

    assert client.get(url).data["dados"] is None

    _ate_concluida(cenario)
    _avaliar(cenario["solicitante"], cenario["os"], {"nota": 2, "comentario": "Demorou."})

    dados = client.get(url).data["dados"]
    assert dados["nota"] == 2
    assert dados["avaliado_por_nome"] == "Solicitante"


def test_dashboard_traz_satisfacao_media_total_e_media_por_tecnico(cenario):
    _ate_concluida(cenario)
    _avaliar(cenario["solicitante"], cenario["os"], {"nota": 4})

    segunda = criar_os(
        cenario["os"].localizacao, solicitante=cenario["solicitante"], tecnico=cenario["tecnico"],
        status_ordem_servico="EM_EXECUCAO", descricao_servico="Outra tomada sem energia.",
    )
    _ate_concluida({**cenario, "os": segunda})
    _avaliar(cenario["solicitante"], segunda, {"nota": 5})

    gerente = _usuario("Gerente", "gerente.ava@fho.edu.br", "GERENTE")
    dados = _cliente(gerente).get("/ordem-servico/dashboard/indicadores/").data["dados"]

    assert dados["satisfacaoMedia"] == 4.5
    assert dados["totalAvaliacoes"] == 2
    ranking = {t["nome"]: t for t in dados["rankingTecnicos"]}
    assert ranking["Carlos"]["satisfacao_media"] == 4.5
    assert ranking["Carlos"]["total_avaliacoes"] == 2
    assert ranking["Carlos"]["total"] == 2


def test_dashboard_sem_avaliacoes_retorna_media_nula(cenario):
    gerente = _usuario("Gerente", "gerente.ava2@fho.edu.br", "GERENTE")

    dados = _cliente(gerente).get("/ordem-servico/dashboard/indicadores/").data["dados"]

    assert dados["satisfacaoMedia"] is None
    assert dados["totalAvaliacoes"] == 0
