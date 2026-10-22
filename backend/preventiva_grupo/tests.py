from datetime import timedelta

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from ativo.models import Ativo
from ativo.services import calcular_proxima_preventiva
from localizacao.models import Localizacao
from ordem_servico.models import OrdemServico
from perfil.models import Gestor, Tecnico
from predio.models import Predio
from preventiva_grupo.catalogo import catalogo_do_tipo
from preventiva_grupo.models import ChecklistItemAtivo, OrdemServicoAtivo
from utils.apoio_testes import criar_usuario

BASE = "/ordem-servico/preventivas-agrupadas/"


def _cliente(usuario):
    client = APIClient()
    client.force_authenticate(user=usuario)
    return client


@pytest.fixture
def cenario(db):
    bloco_a = Predio.objects.create(nome_predio="Bloco A")
    bloco_b = Predio.objects.create(nome_predio="Bloco B")
    sala_a1 = Localizacao.objects.create(predio=bloco_a, desc_localizacao="A1")
    sala_a2 = Localizacao.objects.create(predio=bloco_a, desc_localizacao="A2")
    sala_b1 = Localizacao.objects.create(predio=bloco_b, desc_localizacao="B1")
    vencida = timezone.localdate() - timedelta(days=2)
    ar1 = Ativo.objects.create(localizacao=sala_a1, codigo_patrimonial="PAT-A1", tipo_ativo="AR_CONDICIONADO", marca="LG", modelo="Dual", periodicidade_preventiva_dias=30, dt_proxima_preventiva=vencida)
    ar2 = Ativo.objects.create(localizacao=sala_a2, codigo_patrimonial="PAT-A2", tipo_ativo="AR_CONDICIONADO", periodicidade_preventiva_dias=30, dt_proxima_preventiva=vencida)
    beb = Ativo.objects.create(localizacao=sala_a1, codigo_patrimonial="PAT-B1", tipo_ativo="BEBEDOURO", periodicidade_preventiva_dias=180, dt_proxima_preventiva=vencida)
    outro = Ativo.objects.create(localizacao=sala_b1, codigo_patrimonial="PAT-X", tipo_ativo="AR_CONDICIONADO", periodicidade_preventiva_dias=30)
    gestor = criar_usuario("Gestor", "gestor.prev@fho.edu.br", "GESTOR")
    tecnico = criar_usuario("Tec", "tec.prev@fho.edu.br", "TECNICO")
    Tecnico.objects.filter(usuario=tecnico).update(gestor=Gestor.objects.get(usuario=gestor))
    return {"bloco_a": bloco_a, "ar1": ar1, "ar2": ar2, "beb": beb, "outro": outro, "gestor": gestor, "tecnico": tecnico}


def _gerar(cenario, ativos=None):
    ativos = ativos or [cenario["ar1"].pk, cenario["ar2"].pk, cenario["beb"].pk]
    return _cliente(cenario["gestor"]).post(BASE, {"predio": cenario["bloco_a"].pk, "tecnico": cenario["tecnico"].pk, "ativos": ativos}, format="json")


def _responder_checklist(cenario, id_os, ativo, resultado="EXECUTADO"):
    itens = [{"item": codigo, "resultado": resultado, **({"motivo": "Peça indisponível no estoque."} if resultado == "NAO_EXECUTADO" else {})}
             for codigo, _ in catalogo_do_tipo(ativo.tipo_ativo)["itens"]]
    return _cliente(cenario["tecnico"]).patch(f"{BASE}{id_os}/ativos/{ativo.pk}/checklist/", {"itens": itens}, format="json")


def test_gera_uma_unica_os_para_varios_ativos_do_mesmo_predio(cenario):
    resposta = _gerar(cenario)

    assert resposta.status_code == 201
    grupo = resposta.data["dados"]
    assert grupo["predio"] == cenario["bloco_a"].pk
    assert grupo["tecnico"] == cenario["tecnico"].pk and grupo["tecnico_nome"] == "Tec"
    assert grupo["status_ordem_servico"] == "APROVADA"
    assert sorted(item["ativo"] for item in grupo["itens"]) == sorted([cenario["ar1"].pk, cenario["ar2"].pk, cenario["beb"].pk])
    assert all(item["resultado"] == "PENDENTE" for item in grupo["itens"])
    assert OrdemServico.objects.count() == 1
    ordem = OrdemServico.objects.get()
    assert (ordem.tipo_manutencao, ordem.ativo_id) == ("PREVENTIVA", None)
    assert ChecklistItemAtivo.objects.count() == 8 + 8 + 6


def test_ativos_de_predios_diferentes_sao_recusados(cenario):
    resposta = _gerar(cenario, [cenario["ar1"].pk, cenario["outro"].pk])

    assert resposta.status_code == 400
    assert "mesmo prédio" in resposta.data["mensagem"]
    assert not OrdemServico.objects.exists()


def test_tecnico_e_ativos_sao_obrigatorios(cenario):
    resposta = _cliente(cenario["gestor"]).post(BASE, {"predio": cenario["bloco_a"].pk, "ativos": []}, format="json")

    assert resposta.status_code == 400
    assert {"tecnico", "ativos"} <= set(resposta.data["erros"])


def test_ativo_ja_em_ordem_ativa_nao_entra_em_outra(cenario):
    _gerar(cenario, [cenario["ar1"].pk])

    resposta = _gerar(cenario, [cenario["ar1"].pk, cenario["ar2"].pk])

    assert resposta.status_code == 409


def test_tecnico_nao_gera_ordem_agrupada(cenario):
    resposta = _cliente(cenario["tecnico"]).post(BASE, {"predio": cenario["bloco_a"].pk, "tecnico": cenario["tecnico"].pk, "ativos": [cenario["ar1"].pk]}, format="json")

    assert resposta.status_code == 403


def test_listagem_por_perfil(cenario):
    id_os = _gerar(cenario).data["dados"]["id_ordem_servico"]

    assert [g["id_ordem_servico"] for g in _cliente(cenario["gestor"]).get(BASE).data["dados"]] == [id_os]
    assert [g["id_ordem_servico"] for g in _cliente(cenario["tecnico"]).get(BASE).data["dados"]] == [id_os]
    outro_tecnico = criar_usuario("Outro", "outro.prev@fho.edu.br", "TECNICO")
    assert _cliente(outro_tecnico).get(BASE).data["dados"] == []


def test_checklist_por_ativo_associado_ao_patrimonio(cenario):
    id_os = _gerar(cenario).data["dados"]["id_ordem_servico"]

    dados = _cliente(cenario["tecnico"]).get(f"{BASE}{id_os}/checklist/").data["dados"]

    por_patrimonio = {item["codigo_patrimonial"]: item for item in dados["ativos"]}
    assert len(por_patrimonio["PAT-A1"]["itens"]) == 8
    assert len(por_patrimonio["PAT-B1"]["itens"]) == 6
    assert por_patrimonio["PAT-A1"]["tipo_ativo"] == "AR_CONDICIONADO"
    assert all(item["resultado"] == "PENDENTE" for item in por_patrimonio["PAT-A1"]["itens"])


def test_salvar_checklist_valida_motivo_e_inicia_execucao(cenario):
    id_os = _gerar(cenario).data["dados"]["id_ordem_servico"]
    url = f"{BASE}{id_os}/ativos/{cenario['ar1'].pk}/checklist/"
    client = _cliente(cenario["tecnico"])

    sem_motivo = client.patch(url, {"itens": [{"item": 1, "resultado": "NAO_EXECUTADO"}]}, format="json")
    assert sem_motivo.status_code == 400

    ok = client.patch(url, {"itens": [{"item": 1, "resultado": "EXECUTADO"}, {"item": 2, "resultado": "NAO_EXECUTADO", "motivo": "Filtro não disponível."}]}, format="json")
    assert ok.status_code == 200
    assert [item["resultado"] for item in ok.data["dados"]["itens"][:3]] == ["EXECUTADO", "NAO_EXECUTADO", "PENDENTE"]
    assert OrdemServico.objects.get(pk=id_os).status_ordem_servico == "EM_EXECUCAO"


def test_concluir_ativo_com_checklist_incompleto_retorna_400(cenario):
    id_os = _gerar(cenario).data["dados"]["id_ordem_servico"]
    _cliente(cenario["tecnico"]).patch(f"{BASE}{id_os}/ativos/{cenario['ar1'].pk}/checklist/", {"itens": [{"item": 1, "resultado": "EXECUTADO"}]}, format="json")

    resposta = _cliente(cenario["tecnico"]).patch(f"{BASE}{id_os}/resultados/", {"itens": [{"ativo": cenario["ar1"].pk, "resultado": "CONCLUIDO"}]}, format="json")

    assert resposta.status_code == 400
    assert "checklist incompleto" in resposta.data["mensagem"].lower()
    assert OrdemServicoAtivo.objects.get(ativo=cenario["ar1"]).resultado == "PENDENTE"


def test_fluxo_completo_atualiza_so_os_concluidos_devolve_pendentes_e_encerra(cenario):
    id_os = _gerar(cenario).data["dados"]["id_ordem_servico"]
    tecnico = _cliente(cenario["tecnico"])
    for ativo in (cenario["ar1"], cenario["ar2"]):
        assert _responder_checklist(cenario, id_os, ativo).status_code == 200

    sem_motivo = tecnico.patch(f"{BASE}{id_os}/resultados/", {"itens": [{"ativo": cenario["beb"].pk, "resultado": "NAO_CONCLUIDO"}]}, format="json")
    assert sem_motivo.status_code == 400

    parcial = tecnico.patch(f"{BASE}{id_os}/resultados/", {"itens": [{"ativo": cenario["ar1"].pk, "resultado": "CONCLUIDO"}]}, format="json")
    assert parcial.status_code == 200
    assert parcial.data["dados"]["status_ordem_servico"] == "EM_EXECUCAO"

    final = tecnico.patch(f"{BASE}{id_os}/resultados/", {"itens": [
        {"ativo": cenario["ar2"].pk, "resultado": "CONCLUIDO"},
        {"ativo": cenario["beb"].pk, "resultado": "NAO_CONCLUIDO", "motivo": "Registro de água travado no local."},
    ]}, format="json")

    assert final.status_code == 200
    assert final.data["dados"]["status_ordem_servico"] == "ENCERRADA"
    hoje = timezone.localdate()
    for ativo in (cenario["ar1"], cenario["ar2"]):
        ativo.refresh_from_db()
        assert ativo.dt_ultima_preventiva == hoje
        assert ativo.dt_proxima_preventiva == calcular_proxima_preventiva(hoje, 30)
    cenario["beb"].refresh_from_db()
    assert cenario["beb"].dt_ultima_preventiva is None
    item_beb = next(item for item in final.data["dados"]["grupo"]["itens"] if item["ativo"] == cenario["beb"].pk)
    assert (item_beb["resultado"], item_beb["motivo"]) == ("NAO_CONCLUIDO", "Registro de água travado no local.")
    assert OrdemServico.objects.get(pk=id_os).dt_conclusao is not None

    depois = tecnico.patch(f"{BASE}{id_os}/resultados/", {"itens": [{"ativo": cenario["beb"].pk, "resultado": "CONCLUIDO"}]}, format="json")
    assert depois.status_code == 409

    nova = _gerar(cenario, [cenario["beb"].pk])
    assert nova.status_code == 201


def test_gestor_registra_resultado_sem_checklist(cenario):
    id_os = _gerar(cenario, [cenario["ar1"].pk]).data["dados"]["id_ordem_servico"]

    resposta = _cliente(cenario["gestor"]).patch(f"{BASE}{id_os}/resultados/", {"itens": [{"ativo": cenario["ar1"].pk, "resultado": "CONCLUIDO"}]}, format="json")

    assert resposta.status_code == 200
    assert resposta.data["dados"]["status_ordem_servico"] == "ENCERRADA"


def test_guia_pdf_com_ativos_materiais_ferramentas_epis_e_checklists(cenario):
    id_os = _gerar(cenario).data["dados"]["id_ordem_servico"]

    resposta = _cliente(cenario["tecnico"]).get(f"{BASE}{id_os}/guia/")

    assert resposta.status_code == 200
    assert resposta["Content-Type"] == "application/pdf"
    assert f"guia-preventiva-OS-{id_os}.pdf" in resposta["Content-Disposition"]
    assert resposta.content.startswith(b"%PDF")

    from preventiva_grupo.guia_pdf import consolidar_recursos

    materiais, ferramentas, epis = consolidar_recursos(OrdemServicoAtivo.objects.filter(ordem_servico_id=id_os).select_related("ativo"))
    filtros = next(m for m in materiais if m["descricao"] == "Filtro de ar")
    assert filtros["quantidade"] == 2
    assert "Alicate amperímetro" in ferramentas
    assert "Luvas de proteção" in epis


def test_ordem_agrupada_fora_do_escopo_retorna_404(cenario):
    id_os = _gerar(cenario).data["dados"]["id_ordem_servico"]
    outro_tecnico = criar_usuario("Outro", "outro2.prev@fho.edu.br", "TECNICO")

    assert _cliente(outro_tecnico).get(f"{BASE}{id_os}/checklist/").status_code == 404
    assert _cliente(outro_tecnico).get(f"{BASE}{id_os}/guia/").status_code == 404


def test_guia_usa_recursos_do_plano_do_predio_quando_cadastrados(cenario):
    from preventiva_grupo.guia_pdf import consolidar_recursos
    from preventiva_grupo.models import PlanoAcaoRecurso, PlanoDeAcao, PlanoManutencaoPreventiva, RecursoManutencao

    plano = PlanoManutencaoPreventiva.objects.create(predio=cenario["bloco_a"], tipo_ativo="AR_CONDICIONADO", ciclo_dias=45)
    acao = PlanoDeAcao.objects.create(plano_manutencao=plano, descricao="Preventiva de ar-condicionado")
    filtro = RecursoManutencao.objects.create(nome="Filtro G4", tipo="MATERIAL", unidade_medida="un")
    escada = RecursoManutencao.objects.create(nome="Escada", tipo="FERRAMENTA", unidade_medida="un")
    capacete = RecursoManutencao.objects.create(nome="Capacete", tipo="EPI", unidade_medida="un")
    for recurso, quantidade in ((filtro, 2), (escada, 1), (capacete, 1)):
        PlanoAcaoRecurso.objects.create(plano_acao=acao, recurso=recurso, quantidade=quantidade)
    id_os = _gerar(cenario).data["dados"]["id_ordem_servico"]

    materiais, ferramentas, epis = consolidar_recursos(OrdemServicoAtivo.objects.filter(ordem_servico_id=id_os).select_related("ativo__localizacao"))

    assert {"descricao": "Filtro G4", "quantidade": 4.0, "unidade": "un"} in materiais
    assert "Escada" in ferramentas and "Capacete" in epis
    assert any(m["descricao"] == "Elemento filtrante" for m in materiais)
