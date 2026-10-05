import logging
from datetime import date

import pytest
from django.utils import timezone

from ativo.models import Ativo
from historico.models import Historico
from localizacao.models import Localizacao
from ordem_servico.builders import OrdemServicoDiretor
from ordem_servico.models import OrdemServico
from ordem_servico.processadores import (
    ComHistoricoDecorator,
    ComLogDecorator,
    PreventivaFactory,
    ProcessadorDecorator,
    ProcessadorOrdemServico,
)
from predio.models import Predio
from usuario.models import Usuario


class ProcessadorEspiao(ProcessadorOrdemServico):
    """Processador falso: só registra as chamadas recebidas, para provar a delegação."""

    def __init__(self, erro: Exception | None = None) -> None:
        self.chamadas = []
        self._erro = erro

    def finalizar(self, ordem_servico, motivo_tecnico) -> None:
        self.chamadas.append((ordem_servico, motivo_tecnico))
        if self._erro:
            raise self._erro


def _criar_localizacao():
    predio = Predio.objects.create(nome_predio="Bloco A")
    return Localizacao.objects.create(predio=predio, desc_localizacao="Sala 101")


def _criar_os(localizacao, **campos):
    valores = {
        "tipo_manutencao": "CORRETIVA",
        "prioridade_urgencia": "NAO",
        "status_ordem_servico": "APROVADA",
        "dt_abertura": timezone.now(),
        "descricao_servico": "OS de teste.",
    }
    valores.update(campos)
    return OrdemServico.objects.create(localizacao=localizacao, **valores)


def _criar_usuario(email="tecnico.decorator@fho.edu.br"):
    return Usuario.objects.create(nome="Tecnico", email=email, senha_hash="x")


def test_processador_decorator_e_abstrato():
    with pytest.raises(TypeError):
        ProcessadorDecorator(ProcessadorEspiao())


def test_decorators_respeitam_a_interface_do_processador():
    """Decorator e componente são intercambiáveis: quem chama só enxerga ProcessadorOrdemServico."""
    espiao = ProcessadorEspiao()
    decorado = ComLogDecorator(espiao)

    assert isinstance(decorado, ProcessadorOrdemServico)
    assert decorado.processador_envolvido is espiao


@pytest.mark.django_db
def test_com_historico_delega_ao_processador_envolvido_com_os_mesmos_argumentos():
    ordem_servico = _criar_os(_criar_localizacao(), status_ordem_servico="EM_EXECUCAO")
    espiao = ProcessadorEspiao()

    ComHistoricoDecorator(espiao, usuario=_criar_usuario(), status_anterior="APROVADA").finalizar(ordem_servico, "motivo")

    assert espiao.chamadas == [(ordem_servico, "motivo")]


@pytest.mark.django_db
def test_com_historico_grava_texto_identico_ao_da_view_antiga():
    ordem_servico = _criar_os(_criar_localizacao(), status_ordem_servico="CONCLUIDA")
    usuario = _criar_usuario()

    ComHistoricoDecorator(ProcessadorEspiao(), usuario=usuario, status_anterior="APROVADA").finalizar(
        ordem_servico, "  Trocado o filtro.  "
    )

    historicos = Historico.objects.filter(ordem_servico=ordem_servico)
    assert historicos.count() == 1
    assert historicos.get().desc_historico == "Status alterado: APROVADA -> CONCLUIDA. Detalhes: Trocado o filtro."
    assert historicos.get().usuario_id == usuario.pk


@pytest.mark.django_db
@pytest.mark.parametrize("motivo", ["", "   ", None])
def test_com_historico_sem_motivo_omite_detalhes(motivo):
    ordem_servico = _criar_os(_criar_localizacao(), status_ordem_servico="AGUARDANDO_MATERIAL")

    ComHistoricoDecorator(ProcessadorEspiao(), usuario=_criar_usuario(), status_anterior="APROVADA").finalizar(
        ordem_servico, motivo
    )

    assert Historico.objects.get(ordem_servico=ordem_servico).desc_historico == (
        "Status alterado: APROVADA -> AGUARDANDO_MATERIAL."
    )


@pytest.mark.django_db
def test_com_historico_registra_status_pedido_mesmo_quando_preventiva_vira_encerrada():
    localizacao = _criar_localizacao()
    ativo = Ativo.objects.create(
        localizacao=localizacao,
        codigo_patrimonial="PAT-001",
        tipo_ativo="AR_CONDICIONADO",
        periodicidade_preventiva_dias=90,
        dt_proxima_preventiva=date(2026, 10, 1),
    )
    ordem_servico = OrdemServicoDiretor().construir_preventiva_automatica(ativo)
    ordem_servico.status_ordem_servico = "CONCLUIDA"

    processador = ComHistoricoDecorator(
        PreventivaFactory().criar_processador(), usuario=_criar_usuario(), status_anterior="APROVADA"
    )
    processador.finalizar(ordem_servico, "")

    assert ordem_servico.status_ordem_servico == "ENCERRADA"
    assert Historico.objects.get(ordem_servico=ordem_servico).desc_historico == "Status alterado: APROVADA -> CONCLUIDA."


@pytest.mark.django_db
def test_com_log_emite_inicio_e_fim_da_operacao(caplog):
    ordem_servico = _criar_os(_criar_localizacao(), status_ordem_servico="CONCLUIDA")
    espiao = ProcessadorEspiao()

    with caplog.at_level(logging.INFO, logger="ordem_servico.processadores"):
        ComLogDecorator(espiao).finalizar(ordem_servico, "motivo")

    mensagens = [registro.getMessage() for registro in caplog.records]
    assert f"Finalizando OS #{ordem_servico.pk} (CORRETIVA) com status CONCLUIDA." in mensagens
    assert f"OS #{ordem_servico.pk} processada; status final CONCLUIDA." in mensagens
    assert espiao.chamadas == [(ordem_servico, "motivo")]


@pytest.mark.django_db
def test_com_log_registra_falha_e_repropaga_a_excecao(caplog):
    ordem_servico = _criar_os(_criar_localizacao())
    espiao = ProcessadorEspiao(erro=RuntimeError("falhou"))

    with caplog.at_level(logging.INFO, logger="ordem_servico.processadores"):
        with pytest.raises(RuntimeError, match="falhou"):
            ComLogDecorator(espiao).finalizar(ordem_servico, "")

    erros = [registro for registro in caplog.records if registro.levelno == logging.ERROR]
    assert len(erros) == 1
    assert erros[0].getMessage() == f"Falha ao finalizar OS #{ordem_servico.pk}."


@pytest.mark.django_db
def test_decorators_empilhados_delegam_uma_vez_logam_e_gravam_um_historico(caplog):
    """Mesma pilha que a fachada monta: Log(Histórico(processador))."""
    ordem_servico = _criar_os(_criar_localizacao(), status_ordem_servico="AGUARDANDO_TERCEIRO")
    espiao = ProcessadorEspiao()

    pilha = ComLogDecorator(ComHistoricoDecorator(espiao, usuario=_criar_usuario(), status_anterior="APROVADA"))

    with caplog.at_level(logging.INFO, logger="ordem_servico.processadores"):
        pilha.finalizar(ordem_servico, "Aguardando fornecedor.")

    assert espiao.chamadas == [(ordem_servico, "Aguardando fornecedor.")]
    assert Historico.objects.filter(ordem_servico=ordem_servico).count() == 1
    assert Historico.objects.get(ordem_servico=ordem_servico).desc_historico == (
        "Status alterado: APROVADA -> AGUARDANDO_TERCEIRO. Detalhes: Aguardando fornecedor."
    )
    assert any("Finalizando OS" in registro.getMessage() for registro in caplog.records)
