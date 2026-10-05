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
        prioridade_urgencia="SIM",
    )
    preventiva = diretor.construir_preventiva_automatica(ativo)

    for ordem_servico in (corretiva, preventiva):
        assert ordem_servico.status_ordem_servico == "ABERTA"
        assert ordem_servico.dt_abertura is not None
        assert ordem_servico.pk is not None

    assert corretiva.tipo_manutencao == "CORRETIVA"
    assert preventiva.tipo_manutencao == "PREVENTIVA"
    assert preventiva.categoria_manutencao == "GERAIS"
    assert preventiva.prioridade_urgencia == "NAO"


@pytest.mark.django_db
def test_construir_preventiva_automatica_atualiza_os_existente_em_vez_de_duplicar():
    localizacao = _criar_localizacao()
    ativo = _criar_ativo(localizacao, dt_proxima_preventiva=date(2026, 10, 1))

    diretor = OrdemServicoDiretor()

    primeira = diretor.construir_preventiva_automatica(ativo)

    ativo.dt_proxima_preventiva = date(2026, 11, 15)
    ativo.save()

    segunda = diretor.construir_preventiva_automatica(ativo)

    assert primeira.pk == segunda.pk
    assert OrdemServico.objects.filter(ativo=ativo, tipo_manutencao="PREVENTIVA").count() == 1
    assert "15/11/2026" in segunda.descricao_servico


@pytest.mark.django_db
def test_construir_preventiva_automatica_sem_proxima_data_nao_cria_os():
    localizacao = _criar_localizacao()
    ativo = _criar_ativo(localizacao, dt_proxima_preventiva=None)

    resultado = OrdemServicoDiretor().construir_preventiva_automatica(ativo)

    assert resultado is None
    assert not OrdemServico.objects.filter(ativo=ativo).exists()


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
        prioridade_urgencia="NAO",
        ativo=ativo,
    )

    assert ordem_servico.ativo_id == ativo.pk
