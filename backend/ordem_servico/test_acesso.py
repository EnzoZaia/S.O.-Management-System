import pytest
from django.utils import timezone

from grupo.models import Grupo
from grupo_usuario.models import GrupoUsuario
from localizacao.models import Localizacao
from ordem_servico.acesso import (
    GerenteAcessoFactory,
    GestorAcessoFactory,
    SolicitanteAcessoFactory,
    TecnicoAcessoFactory,
    resolver_fabrica_acesso,
)
from ordem_servico.models import OrdemServico
from predio.models import Predio
from usuario.models import Usuario


def _criar_usuario_com_grupo(nome, email, nome_grupo):
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


@pytest.mark.django_db
def test_resolver_fabrica_acesso_por_grupo():
    localizacao = _criar_localizacao()  # garante apps carregados; não usado diretamente aqui

    gerente = _criar_usuario_com_grupo("Gerente", "gerente.acesso@fho.edu.br", "GERENTE")
    gestor = _criar_usuario_com_grupo("Gestor", "gestor.acesso@fho.edu.br", "GESTOR")
    tecnico = _criar_usuario_com_grupo("Tecnico", "tecnico.acesso@fho.edu.br", "TECNICO")
    solicitante = _criar_usuario_com_grupo("Solicitante", "solicitante.acesso@fho.edu.br", "SOLICITANTE")

    assert isinstance(resolver_fabrica_acesso(gerente), GerenteAcessoFactory)
    assert isinstance(resolver_fabrica_acesso(gestor), GestorAcessoFactory)
    assert isinstance(resolver_fabrica_acesso(tecnico), TecnicoAcessoFactory)
    assert isinstance(resolver_fabrica_acesso(solicitante), SolicitanteAcessoFactory)


@pytest.mark.django_db
def test_resolver_fabrica_acesso_sem_grupo_usa_solicitante_como_default():
    usuario_sem_grupo = Usuario.objects.create(nome="Sem Grupo", email="semgrupo@fho.edu.br", senha_hash="x")

    assert isinstance(resolver_fabrica_acesso(usuario_sem_grupo), SolicitanteAcessoFactory)


@pytest.mark.django_db
def test_tecnico_ve_apenas_suas_proprias_os_na_listagem_e_no_dashboard():
    """Consistência cruzada: o total do dashboard do técnico bate com a contagem da listagem dele."""
    localizacao = _criar_localizacao()
    tecnico_a = _criar_usuario_com_grupo("Tecnico A", "tecnico.a@fho.edu.br", "TECNICO")
    tecnico_b = _criar_usuario_com_grupo("Tecnico B", "tecnico.b@fho.edu.br", "TECNICO")

    _criar_os(localizacao, tecnico=tecnico_a)
    _criar_os(localizacao, tecnico=tecnico_a)
    _criar_os(localizacao, tecnico=tecnico_b)

    fabrica = resolver_fabrica_acesso(tecnico_a)

    listagem = fabrica.criar_escopo_consulta().filtrar(tecnico_a)
    dashboard = fabrica.criar_regra_dashboard().calcular_indicadores(tecnico_a, periodo="ano")

    assert listagem.count() == 2
    assert dashboard["totalOrdens"] == listagem.count()


@pytest.mark.django_db
def test_solicitante_ve_apenas_suas_proprias_os_na_listagem_e_no_dashboard():
    localizacao = _criar_localizacao()
    solicitante_a = _criar_usuario_com_grupo("Solicitante A", "sol.a@fho.edu.br", "SOLICITANTE")
    solicitante_b = _criar_usuario_com_grupo("Solicitante B", "sol.b@fho.edu.br", "SOLICITANTE")

    _criar_os(localizacao, solicitante=solicitante_a)
    _criar_os(localizacao, solicitante=solicitante_b)
    _criar_os(localizacao, solicitante=solicitante_b)

    fabrica = resolver_fabrica_acesso(solicitante_a)

    listagem = fabrica.criar_escopo_consulta().filtrar(solicitante_a)
    dashboard = fabrica.criar_regra_dashboard().calcular_indicadores(solicitante_a, periodo="ano")

    assert listagem.count() == 1
    assert dashboard["totalOrdens"] == listagem.count()


@pytest.mark.django_db
def test_gestor_dashboard_inclui_reprovada_mas_listagem_nao():
    """Nuance preservada intencionalmente: o Gestor vê REPROVADA no dashboard, mas não na listagem principal."""
    localizacao = _criar_localizacao()
    gestor = _criar_usuario_com_grupo("Gestor", "gestor.nuance@fho.edu.br", "GESTOR")

    _criar_os(localizacao, status_ordem_servico="REPROVADA")

    fabrica = resolver_fabrica_acesso(gestor)

    listagem = fabrica.criar_escopo_consulta().filtrar(gestor)
    dashboard = fabrica.criar_regra_dashboard().calcular_indicadores(gestor, periodo="ano")

    assert listagem.filter(status_ordem_servico="REPROVADA").count() == 0
    assert dashboard["statusDetalhados"]["REPROVADA"] == 1


@pytest.mark.django_db
def test_gerente_ve_todas_as_os_na_listagem_e_no_dashboard():
    localizacao = _criar_localizacao()
    gerente = _criar_usuario_com_grupo("Gerente Total", "gerente.total@fho.edu.br", "GERENTE")

    _criar_os(localizacao)
    _criar_os(localizacao)

    fabrica = resolver_fabrica_acesso(gerente)

    listagem = fabrica.criar_escopo_consulta().filtrar(gerente)
    dashboard = fabrica.criar_regra_dashboard().calcular_indicadores(gerente, periodo="ano")

    assert listagem.count() == 2
    assert dashboard["totalOrdens"] == 2
