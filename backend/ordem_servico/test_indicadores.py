from datetime import timedelta

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from ativo.models import Ativo
from historico.models import Historico
from localizacao.models import Localizacao
from os_participante.models import OsParticipante
from perfil.models import Gestor, Tecnico
from predio.models import Predio
from utils.apoio_testes import criar_localizacao, criar_os, criar_usuario
from validacao.models import ValidacaoAtendimento

URL_GERENCIAIS = "/ordem-servico/indicadores-gerenciais/"


def _cliente(usuario):
    client = APIClient()
    client.force_authenticate(user=usuario)
    return client


def test_painel_do_gestor_filtra_escopo_ranking_e_gargalos(db):
    localizacao = criar_localizacao()
    gestor = criar_usuario("Gestor", "gestor.ind@fho.edu.br", "GESTOR")
    Gestor.objects.filter(usuario=gestor).update(area_atuacao="REFRIGERACAO")
    outro_gestor = criar_usuario("Outro", "outro.ind@fho.edu.br", "GESTOR")
    da_equipe = criar_usuario("Ana", "ana.ind@fho.edu.br", "TECNICO")
    de_fora = criar_usuario("Bia", "bia.ind@fho.edu.br", "TECNICO")
    Tecnico.objects.filter(usuario=da_equipe).update(gestor=Gestor.objects.get(usuario=gestor))
    Tecnico.objects.filter(usuario=de_fora).update(gestor=Gestor.objects.get(usuario=outro_gestor))

    criar_os(localizacao, categoria_manutencao="REFRIGERACAO")
    criar_os(localizacao, categoria_manutencao="ELETRICA")
    criar_os(localizacao, tecnico=da_equipe, gestor=gestor, status_ordem_servico="AGUARDANDO_MATERIAL")
    criar_os(localizacao, tecnico=da_equipe, gestor=gestor, status_ordem_servico="ENCERRADA", dt_conclusao=timezone.now())
    criar_os(localizacao, tecnico=de_fora, gestor=outro_gestor, status_ordem_servico="AGUARDANDO_TERCEIRO")

    dados = _cliente(gestor).get("/ordem-servico/dashboard/indicadores/?periodo=ano").data["dados"]

    assert dados["totalOrdens"] == 3
    assert dados["gargalos"] == {"sem_triagem": 1, "sem_tecnico": 0, "aguardando_material": 1, "dependente_terceiro": 0}
    assert dados["solucionadas"] == 1
    assert [t["nome"] for t in dados["rankingTecnicos"]] == ["Ana"]


@pytest.fixture
def base_gerencial(db):
    bloco = Predio.objects.create(nome_predio="Bloco Central")
    sala = Localizacao.objects.create(predio=bloco, desc_localizacao="Sala 10")
    ativo = Ativo.objects.create(localizacao=sala, codigo_patrimonial="PAT-IND", tipo_ativo="AR_CONDICIONADO", periodicidade_preventiva_dias=30)
    agora = timezone.now()
    maria = criar_usuario("Maria", "maria.ind@fho.edu.br", "SOLICITANTE")
    joao = criar_usuario("Joao", "joao.ind@fho.edu.br", "SOLICITANTE")
    ana = criar_usuario("Ana", "ana.ger@fho.edu.br", "SOLICITANTE")

    primeira = criar_os(sala, ativo=ativo, solicitante=maria, status_ordem_servico="ENCERRADA", dt_abertura=agora - timedelta(days=10), dt_conclusao=agora - timedelta(days=9))
    segunda = criar_os(sala, ativo=ativo, solicitante=joao, status_ordem_servico="CONCLUIDA", dt_abertura=agora - timedelta(days=5), dt_conclusao=agora - timedelta(days=4))
    criar_os(sala, solicitante=ana, status_ordem_servico="EM_EXECUCAO", dt_abertura=agora - timedelta(days=2))
    criar_os(sala, status_ordem_servico="EM_TRIAGEM", dt_abertura=agora - timedelta(days=200))

    OsParticipante.objects.create(ordem_servico=primeira, usuario=joao)
    OsParticipante.objects.create(ordem_servico=primeira, usuario=ana)
    Historico.objects.create(ordem_servico=segunda, status_anterior="AGUARDANDO_VALIDACAO", status_novo="EM_EXECUCAO", desc_historico="Reprovada.")
    ValidacaoAtendimento.objects.create(ordem_servico=primeira, usuario=maria, resultado="APROVADA", nota=4, dt_validacao=agora - timedelta(days=8))
    ValidacaoAtendimento.objects.create(ordem_servico=segunda, usuario=joao, resultado="APROVADA", nota=2, dt_validacao=agora - timedelta(days=3))
    return {"gerente": criar_usuario("Gerente", "gerente.ind@fho.edu.br", "GERENTE")}


def test_indicadores_gerenciais_globais(base_gerencial):
    dados = _cliente(base_gerencial["gerente"]).get(f"{URL_GERENCIAIS}?periodo=30d").data["dados"]

    assert dados["volume_total"] == 3
    assert dados["backlog_ativo"] == 2
    assert dados["total_solucionadas"] == 2
    assert dados["mttr_horas"] == 24.0
    assert dados["taxa_resolucao_primeira_intervencao"] == 50.0
    assert dados["satisfacao_media"] == 3.0 and dados["total_avaliacoes"] == 2
    assert dados["reincidencias"] == 1 and dados["taxa_reincidencia"] == pytest.approx(33.3)
    assert dados["usuarios_afetados"] == 3 + 1 + 1
    assert dados["distribuicao_por_ativo"][0] == {"id_ativo": dados["distribuicao_por_ativo"][0]["id_ativo"], "codigo_patrimonial": "PAT-IND", "tipo_ativo": "AR_CONDICIONADO", "total": 2}
    assert dados["predios_mais_ocorrencias"][0]["predio_nome"] == "Bloco Central"
    assert dados["distribuicao_por_localizacao"][0]["total"] == 3
    assert dados["saude_ativos"]["total_ativos"] == 1


def test_filtro_de_periodo_aplicado_a_todos(base_gerencial):
    hoje = timezone.localdate()
    url = f"{URL_GERENCIAIS}?inicio={(hoje - timedelta(days=3)).isoformat()}&fim={hoje.isoformat()}"

    dados = _cliente(base_gerencial["gerente"]).get(url).data["dados"]

    assert dados["volume_total"] == 1
    assert dados["total_solucionadas"] == 0
    assert dados["total_avaliacoes"] == 1
    assert dados["periodo"]["codigo"] == "personalizado"


def test_periodo_invalido_e_perfis_sem_acesso(base_gerencial):
    assert _cliente(base_gerencial["gerente"]).get(f"{URL_GERENCIAIS}?periodo=xyz").status_code == 400
    assert _cliente(base_gerencial["gerente"]).get(f"{URL_GERENCIAIS}?inicio=2026-13-01").status_code == 400
    gestor = criar_usuario("Gestor", "gestor.ger@fho.edu.br", "GESTOR")
    assert _cliente(gestor).get(URL_GERENCIAIS).status_code == 403
