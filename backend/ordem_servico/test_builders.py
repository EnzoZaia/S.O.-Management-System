from datetime import date

import pytest

from ativo.models import Ativo
from localizacao.models import Localizacao
from ordem_servico.builders import OrdemServicoDiretor
from ordem_servico.models import OrdemServico
from predio.models import Predio
from usuario.models import Usuario


def _criar_localizacao():
    predio = Predio.objects.create(nome_predio="Bloco A")
    return Localizacao.objects.create(predio=predio, desc_localizacao="Sala 101")


def _criar_ativo(localizacao, dt_proxima_preventiva):
    return Ativo.objects.create(
        localizacao=localizacao,
        codigo_patrimonial="PAT-001",
        tipo_ativo="AR_CONDICIONADO",
        periodicidade_preventiva_dias=90,
        dt_proxima_preventiva=dt_proxima_preventiva,
    )


@pytest.mark.django_db
def test_corretiva_e_preventiva_nascem_com_mesmos_defaults_estruturais():
    """As duas rotas de criação (solicitante e automática) devem produzir OS com o mesmo formato de defaults."""
    localizacao = _criar_localizacao()
    solicitante = Usuario.objects.create(nome="Solicitante", email="solicitante@fho.edu.br", senha_hash="x")
    ativo = _criar_ativo(localizacao, dt_proxima_preventiva=date(2026, 10, 1))

    diretor = OrdemServicoDiretor()

    corretiva = diretor.construir_corretiva_do_solicitante(
        usuario=solicitante,
        localizacao=localizacao,
        descricao="Ar-condicionado não liga.",
        categoria_manutencao="REFRIGERACAO",
        prioridade_urgencia="URGENTE",
    )
    preventiva = diretor.construir_preventiva_agrupada(localizacao, "Preventiva agrupada do Bloco A.")

    for ordem_servico in (corretiva, preventiva):
        assert ordem_servico.status_ordem_servico == "EM_TRIAGEM"
        assert ordem_servico.dt_abertura is not None
        assert ordem_servico.pk is not None

    assert corretiva.tipo_manutencao == "CORRETIVA"
    assert preventiva.tipo_manutencao == "PREVENTIVA"
    assert preventiva.categoria_manutencao == "GERAIS"
    assert preventiva.prioridade_urgencia == "NORMAL"


@pytest.mark.django_db
def test_construir_preventiva_agrupada_nao_vincula_um_unico_ativo():
    localizacao = _criar_localizacao()

    ordem_servico = OrdemServicoDiretor().construir_preventiva_agrupada(localizacao, "Preventiva agrupada do Bloco A.")

    assert ordem_servico.pk is not None
    assert ordem_servico.ativo_id is None
    assert ordem_servico.tipo_manutencao == "PREVENTIVA"
    assert ordem_servico.descricao_servico == "Preventiva agrupada do Bloco A."


@pytest.mark.django_db
def test_construir_corretiva_do_solicitante_aplica_campos_extra():
    localizacao = _criar_localizacao()
    ativo = _criar_ativo(localizacao, dt_proxima_preventiva=None)
    solicitante = Usuario.objects.create(nome="Solicitante", email="solicitante2@fho.edu.br", senha_hash="x")

    ordem_servico = OrdemServicoDiretor().construir_corretiva_do_solicitante(
        usuario=solicitante,
        localizacao=localizacao,
        descricao="Bebedouro vazando.",
        categoria_manutencao="GERAIS",
        prioridade_urgencia="NORMAL",
        ativo=ativo,
    )

    assert ordem_servico.ativo_id == ativo.pk
