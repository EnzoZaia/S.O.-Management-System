import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from ativo.models import Ativo
from historico.models import Historico
from historico.serializers import HistoricoSerializer
from ordem_servico.fachada import OrdemServicoFacade
from ordem_servico.models import OrdemServico
from os_participante.models import OsParticipante
from utils.apoio_testes import atribuir, criar_localizacao, criar_os, criar_usuario
from utils.historico import registrar_mudanca_status
from validacao.models import ValidacaoAtendimento


def _cliente(usuario):
    client = APIClient()
    client.force_authenticate(user=usuario)
    return client


@pytest.mark.django_db
def test_registrar_mudanca_status_reaproveita_a_linha_gravada_pelo_trigger():
    ordem_servico = criar_os(criar_localizacao(), status_ordem_servico="EM_EXECUCAO")
    tecnico = criar_usuario("Tecnico", "tec.trigger@fho.edu.br", "TECNICO")
    Historico.objects.create(
        ordem_servico=ordem_servico, usuario=None, desc_historico="Mudança de status",
        status_anterior="APROVADA", status_novo="EM_EXECUCAO", tipo_evento="INICIO",
    )

    registrar_mudanca_status(ordem_servico, tecnico, "APROVADA", "EM_EXECUCAO", "Iniciando.")

    linhas = Historico.objects.filter(ordem_servico=ordem_servico)
    assert linhas.count() == 1
    linha = linhas.get()
    assert linha.desc_historico == "Status alterado: APROVADA -> EM_EXECUCAO. Detalhes: Iniciando."
    assert linha.usuario_id == tecnico.pk
    assert linha.tipo_evento == "INICIO"


@pytest.mark.django_db
def test_registrar_mudanca_status_sem_trigger_insere_com_colunas_estruturadas():
    ordem_servico = criar_os(criar_localizacao())
    gestor = criar_usuario("Gestor", "gestor.trigger@fho.edu.br", "GESTOR")

    registrar_mudanca_status(ordem_servico, gestor, "EM_TRIAGEM", "AGUARDANDO_MATERIAL")

    linha = Historico.objects.get(ordem_servico=ordem_servico)
    assert (linha.status_anterior, linha.status_novo, linha.tipo_evento) == ("EM_TRIAGEM", "AGUARDANDO_MATERIAL", "PAUSA_MATERIAL")
    assert linha.desc_historico == "Status alterado: ABERTA -> AGUARDANDO_MATERIAL."


@pytest.mark.django_db
def test_serializer_do_historico_traduz_linha_crua_do_trigger_para_o_contrato_da_api():
    ordem_servico = criar_os(criar_localizacao())
    linha = Historico.objects.create(
        ordem_servico=ordem_servico, desc_historico="Mudança de status",
        status_anterior="EM_TRIAGEM", status_novo="APROVADA",
    )

    dados = HistoricoSerializer(linha).data

    assert dados["desc_historico"] == "Status alterado: ABERTA -> APROVADA."
    assert dados["status_anterior"] == "ABERTA"
    assert dados["status_novo"] == "APROVADA"


@pytest.mark.django_db
def test_api_expoe_aberta_e_sim_nao_mas_grava_valores_do_enum_do_banco():
    localizacao = criar_localizacao()
    gestor = criar_usuario("Gestor", "gestor.enum@fho.edu.br", "GESTOR")

    criada = APIClient().post("/ordem-servico/", {
        "localizacao": localizacao.pk,
        "descricao_servico": "Lâmpada queimada no corredor.",
        "categoria_manutencao": "ELETRICA",
        "prioridade_urgencia": "SIM",
    }, format="json")

    assert criada.status_code == 201
    assert criada.data["dados"]["status_ordem_servico"] == "ABERTA"
    assert criada.data["dados"]["prioridade_urgencia"] == "SIM"
    ordem_servico = OrdemServico.objects.get(pk=criada.data["dados"]["id_ordem_servico"])
    assert (ordem_servico.status_ordem_servico, ordem_servico.prioridade_urgencia) == ("EM_TRIAGEM", "URGENTE")

    alterada = _cliente(gestor).patch(f"/ordem-servico/{ordem_servico.pk}/", {"prioridade_urgencia": "NAO"}, format="json")

    assert alterada.status_code == 200
    ordem_servico.refresh_from_db()
    assert ordem_servico.prioridade_urgencia == "NORMAL"
    assert alterada.data["dados"]["prioridade_urgencia"] == "NAO"


@pytest.mark.django_db
def test_patch_com_status_aberta_e_aceito_e_traduzido():
    gerente = criar_usuario("Gerente", "gerente.enum@fho.edu.br", "GERENTE")
    ordem_servico = criar_os(criar_localizacao(), status_ordem_servico="APROVADA")

    resposta = _cliente(gerente).patch(f"/ordem-servico/{ordem_servico.pk}/", {"status_ordem_servico": "ABERTA"}, format="json")

    assert resposta.status_code == 200
    ordem_servico.refresh_from_db()
    assert ordem_servico.status_ordem_servico == "EM_TRIAGEM"


@pytest.mark.django_db
def test_dashboard_usa_aberta_como_chave_dos_status():
    gerente = criar_usuario("Gerente", "gerente.dash@fho.edu.br", "GERENTE")
    criar_os(criar_localizacao())

    dados = _cliente(gerente).get("/ordem-servico/dashboard/indicadores/").data["dados"]

    assert dados["statusDetalhados"]["ABERTA"] == 1
    assert "EM_TRIAGEM" not in dados["statusDetalhados"]
    assert dados["abertas"] == 1


@pytest.mark.django_db
def test_corretiva_duplicada_para_o_mesmo_ativo_retorna_409():
    localizacao = criar_localizacao()
    ativo = Ativo.objects.create(localizacao=localizacao, codigo_patrimonial="PAT-DUP", tipo_ativo="BEBEDOURO")
    criar_os(localizacao, ativo=ativo)

    resposta = APIClient().post("/ordem-servico/", {
        "localizacao": localizacao.pk,
        "ativo": ativo.pk,
        "descricao_servico": "Bebedouro vazando de novo.",
        "categoria_manutencao": "GERAIS",
        "prioridade_urgencia": "NAO",
    }, format="json")

    assert resposta.status_code == 409
    assert resposta.data["dados"]["ordem_existente"]["ativo_patrimonio"] == "PAT-DUP"
    assert resposta.data["dados"]["pode_presenciar"] is False
    assert OrdemServico.objects.filter(ativo=ativo).count() == 1


@pytest.mark.django_db
def test_os_aberta_por_quem_nao_e_solicitante_fica_sem_solicitante_mas_com_autor_no_historico():
    tecnico = criar_usuario("Tecnico", "tec.abre@fho.edu.br", "TECNICO")

    resposta = _cliente(tecnico).post("/ordem-servico/", {
        "localizacao": criar_localizacao().pk,
        "descricao_servico": "Tomada solta no laboratório.",
        "categoria_manutencao": "ELETRICA",
        "prioridade_urgencia": "NAO",
    }, format="json")

    assert resposta.status_code == 201
    ordem_servico = OrdemServico.objects.get(pk=resposta.data["dados"]["id_ordem_servico"])
    assert ordem_servico.solicitante_id is None
    assert Historico.objects.get(ordem_servico=ordem_servico).usuario_id == tecnico.pk


@pytest.mark.django_db
def test_tecnico_e_gestor_da_os_vem_da_ultima_atribuicao():
    localizacao = criar_localizacao()
    gestor = criar_usuario("Gestor", "gestor.resp@fho.edu.br", "GESTOR")
    primeiro = criar_usuario("Ana", "ana.resp@fho.edu.br", "TECNICO")
    segundo = criar_usuario("Bia", "bia.resp@fho.edu.br", "TECNICO")
    ordem_servico = criar_os(localizacao, tecnico=primeiro, gestor=gestor)
    atribuir(ordem_servico, segundo, gestor)

    recarregada = OrdemServico.objects.com_responsaveis().get(pk=ordem_servico.pk)
    assert (recarregada.tecnico_id, recarregada.tecnico_nome) == (segundo.pk, "Bia")
    assert (recarregada.gestor_id, recarregada.gestor_nome) == (gestor.pk, "Gestor")

    lista_primeiro = _cliente(primeiro).get("/ordem-servico/").data
    lista_segundo = _cliente(segundo).get("/ordem-servico/").data
    assert lista_primeiro == []
    assert [o["id_ordem_servico"] for o in lista_segundo] == [ordem_servico.pk]
    assert lista_segundo[0]["tecnico_nome"] == "Bia"
    assert lista_segundo[0]["gestor_nome"] == "Gestor"


@pytest.mark.django_db
def test_avaliacao_por_participante_que_nao_aprovou_grava_linha_propria_sem_resultado():
    localizacao = criar_localizacao()
    solicitante = criar_usuario("Sol", "sol.part@fho.edu.br", "SOLICITANTE")
    participante = criar_usuario("Part", "part.part@fho.edu.br", "SOLICITANTE")
    tecnico = criar_usuario("Tec", "tec.part@fho.edu.br", "TECNICO")
    ordem_servico = criar_os(localizacao, solicitante=solicitante, tecnico=tecnico, status_ordem_servico="EM_EXECUCAO")
    OsParticipante.objects.create(ordem_servico=ordem_servico, usuario=participante, dt_vinculo=timezone.now())
    fachada = OrdemServicoFacade()
    fachada.alterar_status(ordem_servico, tecnico, {"status_ordem_servico": "CONCLUIDA", "causa_raiz": "Desgaste natural"}, "Serviço concluído no local.")
    fachada.validar(ordem_servico, solicitante, aprovada=True)

    resposta = _cliente(participante).post(f"/ordem-servico/{ordem_servico.pk}/avaliar/", {"nota": 4}, format="json")

    assert resposta.status_code == 201
    assert resposta.data["dados"]["avaliacao"]["avaliado_por_nome"] == "Part"
    linha = ValidacaoAtendimento.objects.get(ordem_servico=ordem_servico, usuario=participante)
    assert (linha.resultado, linha.nota) == (None, 4)
    assert ValidacaoAtendimento.ultima_da_os(ordem_servico).usuario_id == solicitante.pk
