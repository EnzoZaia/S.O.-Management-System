from datetime import date, timedelta

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from ativo.calendario_feriados import GerenciadorCalendarioFeriados
from ativo.models import Ativo
from ativo.saude import calcular_saude, classificar, saude_dos_ativos
from ativo.services import calcular_proxima_preventiva, registrar_preventiva_concluida
from historico.models import Historico
from ordem_servico.models import OrdemServico
from utils.apoio_testes import criar_localizacao, criar_os, criar_usuario


def _cliente(usuario):
    client = APIClient()
    client.force_authenticate(user=usuario)
    return client


@pytest.fixture
def gerente(db):
    return criar_usuario("Gerente", "gerente.prev@fho.edu.br", "GERENTE")


def test_proxima_preventiva_soma_intervalo_e_cai_em_dia_util():
    assert calcular_proxima_preventiva(date(2026, 8, 7), 30) == date(2026, 9, 8)
    assert calcular_proxima_preventiva(date(2026, 11, 25), 30) == date(2026, 12, 28)
    assert calcular_proxima_preventiva(date(2026, 9, 1), 30) == date(2026, 10, 1)


@pytest.mark.django_db
@pytest.mark.parametrize("tipo, intervalo", [("AR_CONDICIONADO", 30), ("BEBEDOURO", 180)])
def test_cadastro_de_ativo_usa_intervalo_por_tipo_e_nao_gera_os_isolada(gerente, tipo, intervalo):
    localizacao = criar_localizacao()

    resposta = _cliente(gerente).post("/ativo/", {
        "localizacao": localizacao.pk, "codigo_patrimonial": f"PAT-{tipo}", "tipo_ativo": tipo, "dt_ultima_preventiva": "2026-09-01",
    }, format="json")

    assert resposta.status_code == 201
    dados = resposta.data["dados"]
    assert dados["periodicidade_preventiva_dias"] == intervalo
    esperado = GerenciadorCalendarioFeriados.instancia().proximo_dia_util(date(2026, 9, 1) + timedelta(days=intervalo))
    assert dados["dt_proxima_preventiva"] == esperado.isoformat()
    assert not OrdemServico.objects.exists()


@pytest.mark.django_db
def test_intervalo_por_tipo_e_configuravel(gerente, settings):
    settings.INTERVALO_PREVENTIVA_DIAS = {"AR_CONDICIONADO": 45, "BEBEDOURO": 90}

    resposta = _cliente(gerente).post("/ativo/", {
        "localizacao": criar_localizacao().pk, "codigo_patrimonial": "PAT-CFG", "tipo_ativo": "AR_CONDICIONADO",
    }, format="json")

    assert resposta.data["dados"]["periodicidade_preventiva_dias"] == 45


@pytest.mark.django_db
def test_recalculo_individual_apos_conclusao():
    ativo = Ativo.objects.create(localizacao=criar_localizacao(), codigo_patrimonial="PAT-R", tipo_ativo="BEBEDOURO", periodicidade_preventiva_dias=180)

    registrar_preventiva_concluida(ativo, date(2026, 10, 5))

    ativo.refresh_from_db()
    assert ativo.dt_ultima_preventiva == date(2026, 10, 5)
    assert ativo.dt_proxima_preventiva == calcular_proxima_preventiva(date(2026, 10, 5), 180)


@pytest.mark.django_db
def test_corretiva_aberta_ate_7_dias_antes_da_preventiva_gera_alerta(gerente):
    localizacao = criar_localizacao()
    solicitante = criar_usuario("Sol", "sol.prev@fho.edu.br", "SOLICITANTE")
    proxima = Ativo.objects.create(
        localizacao=localizacao, codigo_patrimonial="PAT-PERTO", tipo_ativo="AR_CONDICIONADO",
        periodicidade_preventiva_dias=30, dt_proxima_preventiva=timezone.localdate() + timedelta(days=5),
    )
    distante = Ativo.objects.create(
        localizacao=localizacao, codigo_patrimonial="PAT-LONGE", tipo_ativo="AR_CONDICIONADO",
        periodicidade_preventiva_dias=30, dt_proxima_preventiva=timezone.localdate() + timedelta(days=20),
    )
    client = _cliente(solicitante)
    corpo = {"descricao_servico": "Ar-condicionado pingando muito.", "prioridade_urgencia": "NAO"}

    perto = client.post("/ordem-servico/", {**corpo, "ativo": proxima.pk}, format="json")
    longe = client.post("/ordem-servico/", {**corpo, "ativo": distante.pk}, format="json")

    assert perto.data["dados"]["alerta_preventiva"]["dias_para_preventiva"] == 5
    assert longe.data["dados"]["alerta_preventiva"] is None
    assert Historico.objects.filter(ordem_servico_id=perto.data["dados"]["id_ordem_servico"], desc_historico__startswith="Alerta de proximidade").exists()


def test_classificacao_do_health_score():
    assert classificar(100)[0] == "SAUDAVEL"
    assert classificar(80)[0] == "SAUDAVEL"
    assert classificar(79)[0] == "ATENCAO"
    assert classificar(60)[0] == "ATENCAO"
    assert classificar(59)[0] == "CRITICO"
    assert classificar(40)[0] == "CRITICO"
    assert classificar(39)[0] == "MUITO_CRITICO"


@pytest.mark.django_db
def test_health_score_aplica_cada_fator_e_limita_em_zero():
    localizacao = criar_localizacao()
    agora = timezone.now()
    ativo = Ativo.objects.create(
        localizacao=localizacao, codigo_patrimonial="PAT-SAUDE", tipo_ativo="AR_CONDICIONADO",
        periodicidade_preventiva_dias=30, dt_proxima_preventiva=timezone.localdate() - timedelta(days=3),
    )
    criar_os(localizacao, ativo=ativo, status_ordem_servico="ENCERRADA", dt_abertura=agora - timedelta(days=40), dt_conclusao=agora - timedelta(days=38))
    criar_os(localizacao, ativo=ativo, status_ordem_servico="ENCERRADA", dt_abertura=agora - timedelta(days=30), dt_conclusao=agora - timedelta(days=29))
    criar_os(localizacao, ativo=ativo, status_ordem_servico="EM_EXECUCAO", prioridade_urgencia="URGENTE", dt_abertura=agora - timedelta(days=5))

    resultado = saude_dos_ativos([ativo])[0]

    fatores = {fator["fator"]: fator for fator in resultado["fatores"]}
    assert fatores["PREVENTIVA_ATRASADA"]["pontos"] == -25
    assert fatores["CORRETIVAS_RECENTES"]["quantidade"] == 2 and fatores["CORRETIVAS_RECENTES"]["pontos"] == -20
    assert fatores["REINCIDENCIA"]["quantidade"] == 1 and fatores["REINCIDENCIA"]["pontos"] == -15
    assert fatores["OCORRENCIA_URGENTE"]["pontos"] == -20
    assert resultado["nota"] == 20
    assert resultado["classificacao"] == "MUITO_CRITICO"

    corretivas = [
        {'dt_abertura': agora - timedelta(days=d), 'dt_conclusao': agora - timedelta(days=d - 1), 'status_ordem_servico': 'ENCERRADA', 'prioridade_urgencia': 'URGENTE'}
        for d in (50, 40, 30, 20, 10)
    ]
    assert calcular_saude(ativo, corretivas, agora)["nota"] == 0


@pytest.mark.django_db
def test_endpoints_de_saude(gerente):
    localizacao = criar_localizacao()
    saudavel = Ativo.objects.create(localizacao=localizacao, codigo_patrimonial="PAT-OK", tipo_ativo="BEBEDOURO", periodicidade_preventiva_dias=180, dt_proxima_preventiva=timezone.localdate() + timedelta(days=60))
    atrasado = Ativo.objects.create(localizacao=localizacao, codigo_patrimonial="PAT-ATR", tipo_ativo="BEBEDOURO", periodicidade_preventiva_dias=180, dt_proxima_preventiva=timezone.localdate() - timedelta(days=1))
    client = _cliente(gerente)

    individual = client.get(f"/ativo/{saudavel.pk}/saude/").data["dados"]
    assert (individual["nota"], individual["classificacao"], individual["fatores"]) == (100, "SAUDAVEL", [])

    lista = client.get("/ativo/saude/").data["dados"]
    assert [item["id_ativo"] for item in lista] == [atrasado.pk, saudavel.pk]
    assert lista[0]["nota"] == 75 and lista[0]["classificacao"] == "ATENCAO"

    solicitante = criar_usuario("Sol", "sol.saude@fho.edu.br", "SOLICITANTE")
    assert _cliente(solicitante).get("/ativo/saude/").status_code == 403


@pytest.mark.django_db
def test_ciclo_do_plano_do_predio_tem_precedencia_sobre_o_intervalo_padrao(gerente):
    from preventiva_grupo.models import PlanoManutencaoPreventiva

    localizacao = criar_localizacao()
    PlanoManutencaoPreventiva.objects.create(predio_id=localizacao.predio_id, tipo_ativo="AR_CONDICIONADO", ciclo_dias=60)

    resposta = _cliente(gerente).post("/ativo/", {
        "localizacao": localizacao.pk, "codigo_patrimonial": "PAT-PLANO", "tipo_ativo": "AR_CONDICIONADO",
    }, format="json")

    assert resposta.data["dados"]["periodicidade_preventiva_dias"] == 60
