import logging
from datetime import date

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from ativo.models import Ativo
from grupo.models import Grupo
from grupo_usuario.models import GrupoUsuario
from historico.models import Historico
from localizacao.models import Localizacao
from ordem_servico.builders import OrdemServicoDiretor
from ordem_servico.fachada import (
    OrdemServicoFacade,
    OrdemServicoStatusFinalError,
    TecnicoInvalidoError,
)
from ordem_servico.models import OrdemServico
from ordem_servico.processadores import (
    ComHistoricoDecorator,
    ComLogDecorator,
    CorretivaFactory,
    ProcessadorOrdemServico,
    ProcessadorOrdemServicoFactory,
)
from predio.models import Predio
from usuario.models import Usuario

STATUS_FINAIS = ["ENCERRADA", "CANCELADA"]


def _criar_usuario_com_grupo(nome, email, nome_grupo=None):
    usuario = Usuario.objects.create(nome=nome, email=email, senha_hash="x")
    if nome_grupo:
        grupo, _ = Grupo.objects.get_or_create(desc_grupo=nome_grupo)
        GrupoUsuario.objects.create(usuario=usuario, grupo=grupo)
    return usuario


def _criar_localizacao():
    predio = Predio.objects.create(nome_predio="Bloco A")
    return Localizacao.objects.create(predio=predio, desc_localizacao="Sala 101")


def _criar_os(localizacao, **campos):
    valores = {
        "tipo_manutencao": "CORRETIVA",
        "prioridade_urgencia": "NAO",
        "status_ordem_servico": "ABERTA",
        "dt_abertura": timezone.now(),
        "descricao_servico": "OS de teste.",
    }
    valores.update(campos)
    return OrdemServico.objects.create(localizacao=localizacao, **valores)


def _descricoes_historico(ordem_servico):
    return list(Historico.objects.filter(ordem_servico=ordem_servico).values_list("desc_historico", flat=True))


@pytest.mark.django_db
def test_abrir_com_usuario_autenticado_monta_corretiva_e_registra_historico_uma_vez():
    localizacao = _criar_localizacao()
    solicitante = _criar_usuario_com_grupo("Maria", "maria.fachada@fho.edu.br", "SOLICITANTE")

    ordem_servico = OrdemServicoFacade().abrir(solicitante, {
        "localizacao": localizacao,
        "descricao_servico": "Lâmpada queimada no corredor.",
        "categoria_manutencao": "ELETRICA",
        "prioridade_urgencia": "SIM",
        "status_ordem_servico": "CONCLUIDA",
        "tipo_manutencao": "PREVENTIVA",
    })

    assert ordem_servico.pk is not None
    assert ordem_servico.solicitante_id == solicitante.pk
    assert ordem_servico.tipo_manutencao == "CORRETIVA"
    assert ordem_servico.status_ordem_servico == "ABERTA"
    assert ordem_servico.categoria_manutencao == "ELETRICA"
    assert _descricoes_historico(ordem_servico) == ["Ordem de serviço aberta por Maria. Status inicial: ABERTA."]


@pytest.mark.django_db
def test_abrir_anonimo_usa_primeiro_usuario_para_assinar_o_historico():
    localizacao = _criar_localizacao()
    admin = _criar_usuario_com_grupo("Admin", "admin.fachada@fho.edu.br")

    ordem_servico = OrdemServicoFacade().abrir(None, {
        "localizacao": localizacao,
        "descricao_servico": "Torneira da recepção pingando.",
        "prioridade_urgencia": "NAO",
    })

    historico = Historico.objects.get(ordem_servico=ordem_servico)
    assert ordem_servico.solicitante is None
    assert historico.usuario_id == admin.pk
    assert historico.desc_historico == "Ordem de serviço aberta por Usuário Anônimo. Status inicial: ABERTA."


@pytest.mark.django_db
def test_abrir_repassa_campos_extra_ao_diretor():
    localizacao = _criar_localizacao()
    ativo = Ativo.objects.create(localizacao=localizacao, codigo_patrimonial="PAT-009", tipo_ativo="BEBEDOURO")
    solicitante = _criar_usuario_com_grupo("Joao", "joao.fachada@fho.edu.br")

    ordem_servico = OrdemServicoFacade().abrir(solicitante, {
        "localizacao": localizacao,
        "descricao_servico": "Bebedouro sem água gelada.",
        "prioridade_urgencia": "NAO",
        "ativo": ativo,
    })

    assert ordem_servico.ativo_id == ativo.pk


@pytest.mark.django_db
def test_alterar_status_para_concluida_finaliza_e_registra_historico_uma_vez():
    localizacao = _criar_localizacao()
    tecnico = _criar_usuario_com_grupo("Tecnico", "tecnico.fachada@fho.edu.br", "TECNICO")
    ordem_servico = _criar_os(localizacao, tecnico=tecnico, status_ordem_servico="APROVADA")

    OrdemServicoFacade().alterar_status(
        ordem_servico, tecnico, {"status_ordem_servico": "CONCLUIDA"}, "Reator trocado."
    )

    ordem_servico.refresh_from_db()
    assert ordem_servico.status_ordem_servico == "CONCLUIDA"
    assert ordem_servico.dt_conclusao is not None
    assert _descricoes_historico(ordem_servico) == ["Status alterado: APROVADA -> CONCLUIDA. Detalhes: Reator trocado."]


@pytest.mark.django_db
def test_alterar_status_de_preventiva_concluida_persiste_encerrada():
    localizacao = _criar_localizacao()
    ativo = Ativo.objects.create(
        localizacao=localizacao,
        codigo_patrimonial="PAT-001",
        tipo_ativo="AR_CONDICIONADO",
        periodicidade_preventiva_dias=90,
        dt_proxima_preventiva=date(2026, 10, 1),
    )
    ordem_servico = OrdemServicoDiretor().construir_preventiva_automatica(ativo)
    tecnico = _criar_usuario_com_grupo("Tecnico", "tecnico.prev@fho.edu.br", "TECNICO")

    OrdemServicoFacade().alterar_status(ordem_servico, tecnico, {"status_ordem_servico": "CONCLUIDA"})

    ordem_servico.refresh_from_db()
    assert ordem_servico.status_ordem_servico == "ENCERRADA"
    assert _descricoes_historico(ordem_servico) == ["Status alterado: ABERTA -> CONCLUIDA."]


@pytest.mark.django_db
def test_alterar_sem_mudar_status_aplica_campos_e_nao_registra_historico():
    localizacao = _criar_localizacao()
    gestor = _criar_usuario_com_grupo("Gestor", "gestor.fachada@fho.edu.br", "GESTOR")
    ordem_servico = _criar_os(localizacao, status_ordem_servico="APROVADA")

    OrdemServicoFacade().alterar_status(ordem_servico, gestor, {
        "status_ordem_servico": "APROVADA",
        "descricao_servico": "Descrição corrigida pelo gestor.",
    })

    ordem_servico.refresh_from_db()
    assert ordem_servico.descricao_servico == "Descrição corrigida pelo gestor."
    assert _descricoes_historico(ordem_servico) == []


@pytest.mark.django_db
@pytest.mark.parametrize("status_final", STATUS_FINAIS)
def test_alterar_status_bloqueia_os_em_status_final(status_final):
    localizacao = _criar_localizacao()
    tecnico = _criar_usuario_com_grupo("Tecnico", "tecnico.bloq@fho.edu.br", "TECNICO")
    ordem_servico = _criar_os(localizacao, status_ordem_servico=status_final)

    with pytest.raises(OrdemServicoStatusFinalError) as erro:
        OrdemServicoFacade().alterar_status(ordem_servico, tecnico, {"status_ordem_servico": "APROVADA"})

    assert erro.value.mensagem == "Esta ordem não pode mais ser alterada."
    ordem_servico.refresh_from_db()
    assert ordem_servico.status_ordem_servico == status_final
    assert _descricoes_historico(ordem_servico) == []


@pytest.mark.django_db
def test_alterar_status_envolve_o_processador_da_fabrica_em_historico_e_log(caplog):
    """A fachada monta Log(Histórico(processador da fábrica)); o processador real é trocado por um espião."""
    processadores_criados = []

    class ProcessadorEspiao(ProcessadorOrdemServico):
        def __init__(self):
            self.chamadas = 0

        def finalizar(self, ordem_servico, motivo_tecnico):
            self.chamadas += 1

    class FabricaEspia(ProcessadorOrdemServicoFactory):
        def criar_processador(self):
            processador = ProcessadorEspiao()
            processadores_criados.append(processador)
            return processador

    fachada = OrdemServicoFacade(resolver_fabrica_processador=lambda tipo: FabricaEspia())
    localizacao = _criar_localizacao()
    tecnico = _criar_usuario_com_grupo("Tecnico", "tecnico.espiao@fho.edu.br", "TECNICO")
    ordem_servico = _criar_os(localizacao, status_ordem_servico="APROVADA")

    with caplog.at_level(logging.INFO, logger="ordem_servico.processadores"):
        fachada.alterar_status(ordem_servico, tecnico, {"status_ordem_servico": "EM_EXECUCAO"})

    assert len(processadores_criados) == 1
    assert processadores_criados[0].chamadas == 1
    assert _descricoes_historico(ordem_servico) == ["Status alterado: APROVADA -> EM_EXECUCAO."]
    assert any("Finalizando OS" in registro.getMessage() for registro in caplog.records)


@pytest.mark.django_db
def test_montar_processador_empilha_log_por_fora_do_historico():
    localizacao = _criar_localizacao()
    ordem_servico = _criar_os(localizacao)

    pilha = OrdemServicoFacade()._montar_processador(ordem_servico, usuario=None, status_anterior="ABERTA")

    assert isinstance(pilha, ComLogDecorator)
    assert isinstance(pilha.processador_envolvido, ComHistoricoDecorator)
    assert isinstance(
        pilha.processador_envolvido.processador_envolvido,
        type(CorretivaFactory().criar_processador()),
    )


@pytest.mark.django_db
def test_atribuir_tecnico_aprova_os_aberta_define_gestor_e_registra_historico():
    localizacao = _criar_localizacao()
    gestor = _criar_usuario_com_grupo("Gestor", "gestor.atrib@fho.edu.br", "GESTOR")
    tecnico = _criar_usuario_com_grupo("Carlos", "carlos.atrib@fho.edu.br", "TECNICO")
    ordem_servico = _criar_os(localizacao)

    OrdemServicoFacade().atribuir_tecnico(ordem_servico, tecnico, gestor)

    ordem_servico.refresh_from_db()
    assert ordem_servico.tecnico_id == tecnico.pk
    assert ordem_servico.gestor_id == gestor.pk
    assert ordem_servico.status_ordem_servico == "APROVADA"
    assert _descricoes_historico(ordem_servico) == ["Técnico atribuído: Carlos"]


@pytest.mark.django_db
def test_atribuir_tecnico_preserva_gestor_existente_e_status_nao_aberto():
    localizacao = _criar_localizacao()
    gestor_original = _criar_usuario_com_grupo("Gestor 1", "gestor1.atrib@fho.edu.br", "GESTOR")
    gerente = _criar_usuario_com_grupo("Gerente", "gerente.atrib@fho.edu.br", "GERENTE")
    tecnico = _criar_usuario_com_grupo("Carlos", "carlos2.atrib@fho.edu.br", "TECNICO")
    ordem_servico = _criar_os(localizacao, gestor=gestor_original, status_ordem_servico="AGUARDANDO_MATERIAL")

    OrdemServicoFacade().atribuir_tecnico(ordem_servico, tecnico, gerente)

    ordem_servico.refresh_from_db()
    assert ordem_servico.gestor_id == gestor_original.pk
    assert ordem_servico.status_ordem_servico == "AGUARDANDO_MATERIAL"


@pytest.mark.django_db
def test_atribuir_usuario_que_nao_e_tecnico_e_rejeitado_sem_alterar_a_os():
    localizacao = _criar_localizacao()
    gestor = _criar_usuario_com_grupo("Gestor", "gestor.rej@fho.edu.br", "GESTOR")
    solicitante = _criar_usuario_com_grupo("Ana", "ana.rej@fho.edu.br", "SOLICITANTE")
    ordem_servico = _criar_os(localizacao)

    with pytest.raises(TecnicoInvalidoError) as erro:
        OrdemServicoFacade().atribuir_tecnico(ordem_servico, solicitante, gestor)

    assert erro.value.mensagem == "Usuário não é técnico."
    ordem_servico.refresh_from_db()
    assert ordem_servico.tecnico is None
    assert ordem_servico.status_ordem_servico == "ABERTA"
    assert _descricoes_historico(ordem_servico) == []


@pytest.mark.django_db
def test_cancelar_marca_cancelada_com_data_e_registra_historico():
    localizacao = _criar_localizacao()
    gerente = _criar_usuario_com_grupo("Gerente", "gerente.canc@fho.edu.br", "GERENTE")
    ordem_servico = _criar_os(localizacao, status_ordem_servico="APROVADA")

    OrdemServicoFacade().cancelar(ordem_servico, gerente)

    ordem_servico.refresh_from_db()
    assert ordem_servico.status_ordem_servico == "CANCELADA"
    assert ordem_servico.dt_conclusao is not None
    assert _descricoes_historico(ordem_servico) == ["OS cancelada por Gerente"]


@pytest.mark.django_db
@pytest.mark.parametrize("status_final", STATUS_FINAIS)
def test_cancelar_bloqueia_os_em_status_final(status_final):
    localizacao = _criar_localizacao()
    gerente = _criar_usuario_com_grupo("Gerente", "gerente.canc2@fho.edu.br", "GERENTE")
    ordem_servico = _criar_os(localizacao, status_ordem_servico=status_final)

    with pytest.raises(OrdemServicoStatusFinalError) as erro:
        OrdemServicoFacade().cancelar(ordem_servico, gerente)

    assert erro.value.mensagem == "Esta ordem já está encerrada ou cancelada."
    ordem_servico.refresh_from_db()
    assert ordem_servico.status_ordem_servico == status_final
    assert ordem_servico.dt_conclusao is None
    assert _descricoes_historico(ordem_servico) == []


@pytest.mark.django_db
def test_api_patch_status_registra_um_unico_historico():
    """Regressão: a view não pode mais gravar o histórico de status; só o ComHistoricoDecorator grava."""
    localizacao = _criar_localizacao()
    tecnico = _criar_usuario_com_grupo("Tecnico", "tecnico.api@fho.edu.br", "TECNICO")
    ordem_servico = _criar_os(localizacao, tecnico=tecnico, status_ordem_servico="APROVADA")

    client = APIClient()
    client.force_authenticate(user=tecnico)
    resposta = client.patch(f"/ordem-servico/{ordem_servico.pk}/", {
        "status_ordem_servico": "EM_EXECUCAO",
        "observacao": "Iniciando atendimento.",
    })

    assert resposta.status_code == 200
    assert resposta.data["status"] == "sucesso"
    assert resposta.data["mensagem"] == "Ordem de serviço atualizada com sucesso."
    assert resposta.data["dados"]["status_ordem_servico"] == "EM_EXECUCAO"
    assert _descricoes_historico(ordem_servico) == [
        "Status alterado: APROVADA -> EM_EXECUCAO. Detalhes: Iniciando atendimento."
    ]


@pytest.mark.django_db
@pytest.mark.parametrize("status_final", STATUS_FINAIS)
def test_api_patch_em_status_final_retorna_400_antes_de_validar_payload(status_final):
    localizacao = _criar_localizacao()
    gerente = _criar_usuario_com_grupo("Gerente", "gerente.api@fho.edu.br", "GERENTE")
    ordem_servico = _criar_os(localizacao, status_ordem_servico=status_final)

    client = APIClient()
    client.force_authenticate(user=gerente)
    resposta = client.patch(f"/ordem-servico/{ordem_servico.pk}/", {"status_ordem_servico": "INEXISTENTE"})

    assert resposta.status_code == 400
    assert resposta.data == {"status": "erro", "mensagem": "Esta ordem não pode mais ser alterada.", "erros": None}


@pytest.mark.django_db
def test_api_patch_payload_invalido_mantem_mensagem_de_validacao():
    localizacao = _criar_localizacao()
    gerente = _criar_usuario_com_grupo("Gerente", "gerente.inv@fho.edu.br", "GERENTE")
    ordem_servico = _criar_os(localizacao, status_ordem_servico="APROVADA")

    client = APIClient()
    client.force_authenticate(user=gerente)
    resposta = client.patch(f"/ordem-servico/{ordem_servico.pk}/", {"status_ordem_servico": "INEXISTENTE"})

    assert resposta.status_code == 400
    assert resposta.data["mensagem"] == "Erro ao atualizar ordem de serviço."
    assert "status_ordem_servico" in resposta.data["erros"]
    assert _descricoes_historico(ordem_servico) == []


@pytest.mark.django_db
def test_api_post_autenticado_registra_historico_de_abertura_uma_vez():
    localizacao = _criar_localizacao()
    solicitante = _criar_usuario_com_grupo("Maria", "maria.api@fho.edu.br", "SOLICITANTE")

    client = APIClient()
    client.force_authenticate(user=solicitante)
    resposta = client.post("/ordem-servico/", {
        "localizacao": localizacao.pk,
        "descricao_servico": "Porta do laboratório emperrada.",
        "categoria_manutencao": "GERAIS",
        "prioridade_urgencia": "NAO",
    })

    assert resposta.status_code == 201
    assert resposta.data["mensagem"] == "Ordem de serviço aberta com sucesso."
    ordem_servico = OrdemServico.objects.get(pk=resposta.data["dados"]["id_ordem_servico"])
    assert ordem_servico.solicitante_id == solicitante.pk
    assert _descricoes_historico(ordem_servico) == ["Ordem de serviço aberta por Maria. Status inicial: ABERTA."]


@pytest.mark.django_db
def test_api_atribuir_tecnico_caminho_feliz_e_usuario_nao_tecnico():
    localizacao = _criar_localizacao()
    gestor = _criar_usuario_com_grupo("Gestor", "gestor.api@fho.edu.br", "GESTOR")
    tecnico = _criar_usuario_com_grupo("Carlos", "carlos.api@fho.edu.br", "TECNICO")
    solicitante = _criar_usuario_com_grupo("Ana", "ana.api@fho.edu.br", "SOLICITANTE")
    ordem_servico = _criar_os(localizacao)

    client = APIClient()
    client.force_authenticate(user=gestor)
    url = f"/ordem-servico/{ordem_servico.pk}/atribuir-tecnico/"

    resposta_invalida = client.patch(url, {"tecnico": solicitante.pk})
    assert resposta_invalida.status_code == 400
    assert resposta_invalida.data == {"status": "erro", "mensagem": "Usuário não é técnico.", "erros": None}

    resposta = client.patch(url, {"tecnico": tecnico.pk})
    assert resposta.status_code == 200
    assert resposta.data == {"status": "sucesso", "mensagem": "Técnico atribuído", "dados": None}
    assert _descricoes_historico(ordem_servico) == ["Técnico atribuído: Carlos"]
