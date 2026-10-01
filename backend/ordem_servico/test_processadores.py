from datetime import date

import pytest

from ativo.models import Ativo
from localizacao.models import Localizacao
from ordem_servico.builders import OrdemServicoDiretor
from ordem_servico.models import OrdemServico
from ordem_servico.processadores import (
    CorretivaFactory,
    PreventivaFactory,
    ProcessadorCorretiva,
    ProcessadorPreventiva,
    obter_fabrica_processador,
)
from predio.models import Predio
from usuario.models import Usuario


def _criar_localizacao():
    predio = Predio.objects.create(nome_predio="Bloco A")
    return Localizacao.objects.create(predio=predio, desc_localizacao="Sala 101")


def _criar_ativo(localizacao, **extra):
    return Ativo.objects.create(
        localizacao=localizacao,
        codigo_patrimonial="PAT-001",
        tipo_ativo="AR_CONDICIONADO",
        periodicidade_preventiva_dias=90,
        **extra,
    )


def test_obter_fabrica_processador_resolve_corretiva_e_preventiva():
    assert isinstance(obter_fabrica_processador("CORRETIVA"), CorretivaFactory)
    assert isinstance(obter_fabrica_processador("PREVENTIVA"), PreventivaFactory)


def test_obter_fabrica_processador_usa_corretiva_como_default():
    assert isinstance(obter_fabrica_processador("TIPO_DESCONHECIDO"), CorretivaFactory)


def test_fabricas_produzem_o_processador_correto():
    assert isinstance(CorretivaFactory().criar_processador(), ProcessadorCorretiva)
    assert isinstance(PreventivaFactory().criar_processador(), ProcessadorPreventiva)


@pytest.mark.django_db
def test_processador_corretiva_concluida_com_tag_vincula_ativo_e_recalcula_datas():
    localizacao = _criar_localizacao()
    ativo = _criar_ativo(localizacao)
    solicitante = Usuario.objects.create(nome="Solicitante", email="sol1@fho.edu.br", senha_hash="x")

    ordem_servico = OrdemServicoDiretor().construir_corretiva_do_solicitante(
        usuario=solicitante,
        localizacao=localizacao,
        descricao="Ar-condicionado não gela.",
        categoria_manutencao="REFRIGERACAO",
        prioridade_urgencia="SIM",
    )
    ordem_servico.status_ordem_servico = "CONCLUIDA"

    processador = CorretivaFactory().criar_processador()
    processador.finalizar(ordem_servico, f"Reparo feito. [PAT: {ativo.codigo_patrimonial}]")
    ordem_servico.save()

    ordem_servico.refresh_from_db()
    ativo.refresh_from_db()

    assert ordem_servico.dt_conclusao is not None
    assert ordem_servico.ativo_id == ativo.pk
    assert ativo.dt_ultima_preventiva is not None
    assert ativo.dt_proxima_preventiva is not None
    assert OrdemServico.objects.filter(ativo=ativo, tipo_manutencao="PREVENTIVA").exists()


@pytest.mark.django_db
def test_processador_corretiva_concluida_sem_tag_nao_quebra():
    localizacao = _criar_localizacao()
    solicitante = Usuario.objects.create(nome="Solicitante", email="sol2@fho.edu.br", senha_hash="x")

    ordem_servico = OrdemServicoDiretor().construir_corretiva_do_solicitante(
        usuario=solicitante,
        localizacao=localizacao,
        descricao="Torneira vazando.",
        categoria_manutencao="GERAIS",
        prioridade_urgencia="NAO",
    )
    ordem_servico.status_ordem_servico = "CONCLUIDA"

    processador = CorretivaFactory().criar_processador()
    processador.finalizar(ordem_servico, "Resolvido sem precisar de ativo.")
    ordem_servico.save()

    ordem_servico.refresh_from_db()
    assert ordem_servico.dt_conclusao is not None
    assert ordem_servico.ativo is None


@pytest.mark.django_db
def test_processador_preventiva_concluida_e_auto_encerrada():
    localizacao = _criar_localizacao()
    ativo = _criar_ativo(localizacao, dt_proxima_preventiva=date(2026, 10, 1))

    ordem_servico = OrdemServicoDiretor().construir_preventiva_automatica(ativo)
    ordem_servico.status_ordem_servico = "CONCLUIDA"

    processador = PreventivaFactory().criar_processador()
    processador.finalizar(ordem_servico, "Preventiva realizada.")
    ordem_servico.save()

    ordem_servico.refresh_from_db()
    assert ordem_servico.status_ordem_servico == "ENCERRADA"
    assert ordem_servico.dt_conclusao is not None
