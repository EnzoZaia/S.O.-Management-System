"""
Os models do projeto usam `managed = False` porque as tabelas já existem
num Postgres externo (Supabase) e não são criadas por migration do Django.

Isso não afeta o banco real: só o banco de testes efêmero (SQLite, criado e
destruído a cada rodada de `pytest`) precisa que o Django crie essas tabelas
para exercer o ORM nos testes. Por isso marcamos `managed = True` nesses
models especificamente durante a montagem do banco de testes, antes de
`setup_databases` rodar as migrations.
"""
import pytest
from django.apps import apps
from django.test.utils import setup_databases, teardown_databases

APPS_COM_TABELAS_EXTERNAS = [
    "usuario",
    "grupo",
    "grupo_usuario",
    "predio",
    "localizacao",
    "ordem_servico",
    "historico",
    "ativo",
]


def _marcar_models_como_gerenciados():
    for app_label in APPS_COM_TABELAS_EXTERNAS:
        for model in apps.get_app_config(app_label).get_models():
            model._meta.managed = True


@pytest.fixture(scope="session")
def django_db_setup(request, django_test_environment, django_db_blocker):
    _marcar_models_como_gerenciados()

    with django_db_blocker.unblock():
        db_cfg = setup_databases(
            verbosity=request.config.option.verbose,
            interactive=False,
        )

    yield

    def teardown_database():
        with django_db_blocker.unblock():
            teardown_databases(db_cfg, verbosity=request.config.option.verbose)

    request.addfinalizer(teardown_database)
