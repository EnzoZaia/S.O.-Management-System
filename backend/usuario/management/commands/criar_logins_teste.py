from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand
from django.db import transaction

from perfil.services import definir_perfil
from usuario.models import STATUS_CONTA_ATIVA, Usuario

SENHA_PADRAO = 'Teste@2026'

LOGINS_TESTE = [
    ('Gerente Demo', 'gerente.demo@fho.edu.br', 'GERENTE'),
    ('Gestor Demo', 'gestor.demo@fho.edu.br', 'GESTOR'),
    ('Tecnico Demo', 'tecnico.demo@fho.edu.br', 'TECNICO'),
]


class Command(BaseCommand):
    help = 'Cria (ou restaura) logins permanentes de teste, um por perfil. Pode ser executado várias vezes.'

    @transaction.atomic
    def handle(self, *args, **options):
        for nome, email, desc_grupo in LOGINS_TESTE:
            usuario, _ = Usuario.objects.update_or_create(
                email=email,
                defaults={
                    'nome': nome,
                    'senha_hash': make_password(SENHA_PADRAO),
                    'email_confirmado': True,
                    'token_confirmacao_email': None,
                    'dt_expiracao_token': None,
                    'status_conta': STATUS_CONTA_ATIVA,
                },
            )
            definir_perfil(usuario, desc_grupo)
            self.stdout.write(f'{desc_grupo:<8} {email}  /  {SENHA_PADRAO}')
