from notificacao.canais import CanalComposto, CanalEmail, CanalSistema, Mensagem

TIPO_OS_ATRIBUIDA = 'OS_ATRIBUIDA'
TIPO_OS_REATRIBUIDA = 'OS_REATRIBUIDA'
TIPO_OS_REPROVADA = 'OS_REPROVADA'


def criar_canal(enviar_email=True):
    canal = CanalComposto([CanalSistema()])
    if enviar_email:
        canal.adicionar(CanalEmail())
    return canal


def notificar(usuario, tipo, titulo, mensagem, ordem_servico=None, enviar_email=True, canal=None):
    canal = canal or criar_canal(enviar_email)
    return canal.enviar(Mensagem(destinatario=usuario, tipo=tipo, titulo=titulo, texto=mensagem, ordem_servico=ordem_servico))
