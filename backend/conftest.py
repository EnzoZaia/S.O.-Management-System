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
from django.conf import settings
from django.test.utils import setup_databases, teardown_databases

APPS_COM_TABELAS_EXTERNAS = [
    "usuario",
    "perfil",
    "predio",
    "localizacao",
    "ordem_servico",
    "historico",
    "ativo",
    "os_participante",
    "validacao",
    "auditoria_usuario",
    "notificacao",
    "evidencia_os",
    "preventiva_grupo",
    "inteligencia",
]


class _SemMigrations(dict):
    def __contains__(self, item):
        return True

    def __getitem__(self, item):
        return None


def _marcar_models_como_gerenciados():
    for app_label in APPS_COM_TABELAS_EXTERNAS:
        for model in apps.get_app_config(app_label).get_models():
            model._meta.managed = True


@pytest.fixture(scope="session")
def django_db_setup(request, django_test_environment, django_db_blocker):
    _marcar_models_como_gerenciados()
    settings.MIGRATION_MODULES = _SemMigrations()

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


@pytest.fixture(autouse=True)
def _limpar_cache_entre_testes():
    from django.core.cache import cache

    cache.clear()
    yield
    cache.clear()
