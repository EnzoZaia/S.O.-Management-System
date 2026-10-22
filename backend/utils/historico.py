from django.db import connection
from django.utils import timezone
from historico.models import Historico
from ordem_servico.constantes import DESCRICAO_HISTORICO_TRIGGER, EVENTO_ATRIBUICAO, EVENTO_POR_STATUS_NOVO, status_para_api


def definir_usuario_da_sessao(usuario):
    if connection.vendor != 'postgresql':
        return
    valor = str(usuario.pk) if usuario is not None and getattr(usuario, 'pk', None) else ''
    with connection.cursor() as cursor:
        cursor.execute("SELECT set_config('app.usuario_id', %s, true)", [valor])


def registrar_historico(ordem_servico, usuario, descricao):
    return Historico.objects.create(ordem_servico=ordem_servico, usuario=usuario, data_registro=timezone.now(), desc_historico=descricao)


def registrar_atribuicao(ordem_servico, responsavel, tecnico, descricao=None):
    return Historico.objects.create(
        ordem_servico=ordem_servico,
        usuario=responsavel,
        tecnico=tecnico,
        tipo_evento=EVENTO_ATRIBUICAO,
        data_registro=timezone.now(),
        desc_historico=descricao or f"Técnico atribuído: {tecnico.nome}",
    )


def texto_mudanca_status(status_anterior, status_novo, detalhes=""):
    texto = f"Status alterado: {status_para_api(status_anterior)} -> {status_para_api(status_novo)}."
    if detalhes and str(detalhes).strip():
        texto += f" Detalhes: {str(detalhes).strip()}"
    return texto


def registrar_mudanca_status(ordem_servico, usuario, status_anterior, status_novo, detalhes=""):
    descricao = texto_mudanca_status(status_anterior, status_novo, detalhes)

    registro_do_trigger = (
        Historico.objects.filter(
            ordem_servico=ordem_servico,
            status_anterior=status_anterior,
            status_novo=status_novo,
            desc_historico=DESCRICAO_HISTORICO_TRIGGER,
        )
        .order_by('-id_historico_ordem_servico')
        .first()
    )

    if registro_do_trigger is not None:
        registro_do_trigger.desc_historico = descricao
        campos = ['desc_historico']
        if registro_do_trigger.usuario_id is None and usuario is not None:
            registro_do_trigger.usuario = usuario
            campos.append('usuario')
        registro_do_trigger.save(update_fields=campos)
        return registro_do_trigger

    return Historico.objects.create(
        ordem_servico=ordem_servico,
        usuario=usuario,
        data_registro=timezone.now(),
        desc_historico=descricao,
        status_anterior=status_anterior,
        status_novo=status_novo,
        tipo_evento=EVENTO_POR_STATUS_NOVO.get(status_novo),
    )
