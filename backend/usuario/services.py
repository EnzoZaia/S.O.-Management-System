import logging
import uuid
from datetime import timedelta

from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
from django.utils import timezone

from auditoria_usuario.models import AuditoriaUsuario
from perfil import services as perfis
from perfil.models import TIPO_VINCULO_ALUNO
from usuario.models import STATUS_CONTA_ATIVA, STATUS_CONTA_DESATIVADA, STATUS_CONTA_PENDENTE, Usuario

logger = logging.getLogger(__name__)

SEGUNDOS_ENTRE_REENVIOS = 60


class RegraUsuarioError(Exception):
    def __init__(self, mensagem: str, status_code: int = 400, erros=None) -> None:
        super().__init__(mensagem)
        self.mensagem = mensagem
        self.status_code = status_code
        self.erros = erros


class TokenConfirmacaoInvalidoError(RegraUsuarioError):
    pass


class TokenConfirmacaoExpiradoError(RegraUsuarioError):
    pass


def novo_token_confirmacao(usuario: Usuario) -> None:
    usuario.token_confirmacao_email = str(uuid.uuid4())
    usuario.dt_expiracao_token = timezone.now() + timedelta(hours=settings.HORAS_VALIDADE_TOKEN_CONFIRMACAO)


def link_confirmacao(usuario: Usuario) -> str:
    return f"{settings.FRONTEND_URL}/confirmar-email/{usuario.token_confirmacao_email}"


def enviar_email_confirmacao(usuario: Usuario, senha_inicial: str | None = None) -> bool:
    linhas = [
        f"Olá, {usuario.nome}!",
        "",
        "Seu cadastro no sistema TechOrder foi criado com sucesso.",
        "",
        "Confirme seu e-mail acessando o link abaixo:",
        link_confirmacao(usuario),
        "",
    ]
    if senha_inicial:
        linhas += [
            "Após confirmar, você poderá acessar o sistema com:",
            f"E-mail: {usuario.email}",
            f"Senha: {senha_inicial}",
            "",
        ]
    linhas.append(f"Este link expira em {settings.HORAS_VALIDADE_TOKEN_CONFIRMACAO} horas.")

    try:
        send_mail(
            subject="Confirmação de cadastro - TechOrder",
            message="\n".join(linhas),
            from_email=None,
            recipient_list=[usuario.email],
            fail_silently=False,
        )
        return True
    except Exception:
        logger.exception("Falha ao enviar e-mail de confirmação para o usuário #%s.", usuario.pk)
        return False


@transaction.atomic
def confirmar_email(token: str) -> Usuario:
    usuario = Usuario.objects.select_for_update().filter(token_confirmacao_email=token).first()

    if usuario is None:
        raise TokenConfirmacaoInvalidoError("Link de confirmação inválido ou já utilizado.")

    if usuario.dt_expiracao_token and usuario.dt_expiracao_token < timezone.now():
        raise TokenConfirmacaoExpiradoError("Link de confirmação expirado. Solicite um novo envio.")

    usuario.email_confirmado = True
    usuario.token_confirmacao_email = None
    usuario.dt_expiracao_token = None
    if usuario.status_conta != STATUS_CONTA_DESATIVADA:
        usuario.status_conta = STATUS_CONTA_ATIVA
    usuario.save()

    if not perfis.perfis_do_usuario(usuario):
        try:
            perfis.criar_perfil(usuario, perfis.SOLICITANTE, tipo_vinculo=TIPO_VINCULO_ALUNO)
        except perfis.PerfilError as erro:
            raise RegraUsuarioError(erro.mensagem, erro.status_code) from erro

    return Usuario.objects.select_related('perfil_solicitante').get(pk=usuario.pk)


def reenviar_confirmacao(email: str) -> None:
    usuario = Usuario.objects.filter(email=email.strip().lower()).first()

    if usuario is None or usuario.email_confirmado or not usuario.ativo:
        return

    if usuario.dt_expiracao_token:
        emitido_em = usuario.dt_expiracao_token - timedelta(hours=settings.HORAS_VALIDADE_TOKEN_CONFIRMACAO)
        if timezone.now() - emitido_em < timedelta(seconds=SEGUNDOS_ENTRE_REENVIOS):
            return

    novo_token_confirmacao(usuario)
    usuario.save(update_fields=['token_confirmacao_email', 'dt_expiracao_token'])
    enviar_email_confirmacao(usuario)


def registrar_auditoria(usuario_alvo: Usuario, autor: Usuario, campo: str, valor_anterior, valor_novo) -> AuditoriaUsuario:
    return AuditoriaUsuario.objects.create(
        usuario_alvo=usuario_alvo,
        autor=autor,
        campo=campo,
        valor_anterior=None if valor_anterior is None else str(valor_anterior),
        valor_novo=None if valor_novo is None else str(valor_novo),
        dt_registro=timezone.now(),
    )


@transaction.atomic
def alterar_perfil(usuario: Usuario, novo_perfil: str, autor: Usuario) -> bool:
    anterior = perfis.perfil_principal(usuario)

    if anterior == novo_perfil:
        return False

    if usuario.pk == autor.pk and anterior == perfis.GERENTE:
        raise RegraUsuarioError("Você não pode remover o seu próprio perfil de gerente.", 403)

    try:
        perfis.definir_perfil(usuario, novo_perfil)
    except perfis.PerfilError as erro:
        raise RegraUsuarioError(erro.mensagem, erro.status_code, {"grupo": [erro.mensagem]}) from erro

    registrar_auditoria(usuario, autor, 'grupo', anterior, novo_perfil)
    return True


def status_conta_para(usuario: Usuario, ativo: bool) -> str:
    if not ativo:
        return STATUS_CONTA_DESATIVADA
    return STATUS_CONTA_ATIVA if usuario.email_confirmado else STATUS_CONTA_PENDENTE


@transaction.atomic
def alterar_situacao(usuario: Usuario, ativo: bool, autor: Usuario) -> bool:
    if usuario.ativo == ativo:
        return False

    if usuario.pk == autor.pk and not ativo:
        raise RegraUsuarioError("Você não pode desativar a sua própria conta.", 403)

    anterior = usuario.status_conta
    usuario.status_conta = status_conta_para(usuario, ativo)
    usuario.save(update_fields=['status_conta'])
    registrar_auditoria(usuario, autor, 'status_conta', anterior, usuario.status_conta)
    return True
