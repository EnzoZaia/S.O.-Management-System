import os
from dataclasses import dataclass

from django.conf import settings
from django.db import transaction
from django.db.models import Max
from django.utils import timezone

from evidencia_os.models import TIPO_IMAGEM, TIPO_VIDEO, EvidenciaOrdem
from ordem_servico.constantes import STATUS_ATIVOS, status_para_api
from ordem_servico.models import OrdemServico
from utils.historico import registrar_historico

MB = 1024 * 1024

ASSINATURAS = {
    'jpg': ('image/jpeg', TIPO_IMAGEM),
    'jpeg': ('image/jpeg', TIPO_IMAGEM),
    'png': ('image/png', TIPO_IMAGEM),
    'webp': ('image/webp', TIPO_IMAGEM),
    'mp4': ('video/mp4', TIPO_VIDEO),
    'mov': ('video/quicktime', TIPO_VIDEO),
    'webm': ('video/webm', TIPO_VIDEO),
}


class EvidenciaError(Exception):
    def __init__(self, mensagem, status_code=400):
        super().__init__(mensagem)
        self.mensagem = mensagem
        self.status_code = status_code


@dataclass
class ArquivoValidado:
    arquivo: object
    tipo_arquivo: str
    tipo_conteudo: str


def descricao_limites():
    imagens = ', '.join(formato.upper() for formato in settings.EVIDENCIA_FORMATOS_IMAGEM)
    videos = ', '.join(formato.upper() for formato in settings.EVIDENCIA_FORMATOS_VIDEO)
    return (
        f"Fotos ({imagens}) até {settings.EVIDENCIA_IMAGEM_TAMANHO_MAX_MB} MB e vídeos curtos ({videos}) "
        f"até {settings.EVIDENCIA_VIDEO_TAMANHO_MAX_MB} MB; até {settings.EVIDENCIA_MAX_POR_ENVIO} arquivos por envio "
        f"e {settings.EVIDENCIA_MAX_POR_ORDEM} por ordem."
    )


def detectar_formato(cabecalho: bytes):
    if cabecalho.startswith(b'\xff\xd8\xff'):
        return 'jpg'
    if cabecalho.startswith(b'\x89PNG\r\n\x1a\n'):
        return 'png'
    if cabecalho[:4] == b'RIFF' and cabecalho[8:12] == b'WEBP':
        return 'webp'
    if cabecalho.startswith(b'\x1a\x45\xdf\xa3'):
        return 'webm'
    if cabecalho[4:8] == b'ftyp':
        marca = cabecalho[8:12]
        return 'mov' if marca == b'qt  ' else 'mp4'
    return None


def _formatos_permitidos():
    return set(settings.EVIDENCIA_FORMATOS_IMAGEM) | set(settings.EVIDENCIA_FORMATOS_VIDEO)


def _mesmo_formato(extensao, detectado):
    equivalentes = {'jpg': {'jpg', 'jpeg'}}
    return extensao in equivalentes.get(detectado, {detectado})


def validar_arquivo(arquivo) -> ArquivoValidado:
    nome = arquivo.name or 'arquivo'
    extensao = os.path.splitext(nome)[1].lower().lstrip('.')
    permitidos = _formatos_permitidos()

    if extensao not in permitidos:
        raise EvidenciaError(f'"{nome}" não é um formato permitido. {descricao_limites()}')

    posicao = arquivo.tell() if hasattr(arquivo, 'tell') else 0
    arquivo.seek(0)
    cabecalho = arquivo.read(32)
    arquivo.seek(posicao)

    detectado = detectar_formato(cabecalho)
    if detectado is None or not _mesmo_formato(extensao, detectado):
        raise EvidenciaError(f'O conteúdo de "{nome}" não corresponde a uma imagem ou vídeo válido. {descricao_limites()}')

    tipo_conteudo, tipo_arquivo = ASSINATURAS[detectado]
    limite_mb = settings.EVIDENCIA_IMAGEM_TAMANHO_MAX_MB if tipo_arquivo == TIPO_IMAGEM else settings.EVIDENCIA_VIDEO_TAMANHO_MAX_MB
    if arquivo.size > limite_mb * MB:
        rotulo = 'imagens' if tipo_arquivo == TIPO_IMAGEM else 'vídeos'
        raise EvidenciaError(f'"{nome}" passa do limite de {limite_mb} MB para {rotulo}.', 413)

    return ArquivoValidado(arquivo=arquivo, tipo_arquivo=tipo_arquivo, tipo_conteudo=tipo_conteudo)


def validar_lote(arquivos, ja_enviadas):
    if not arquivos:
        raise EvidenciaError(f"Selecione ao menos um arquivo no campo 'arquivos'. {descricao_limites()}")
    if len(arquivos) > settings.EVIDENCIA_MAX_POR_ENVIO:
        raise EvidenciaError(f"Envie no máximo {settings.EVIDENCIA_MAX_POR_ENVIO} arquivos por vez.")
    if ja_enviadas + len(arquivos) > settings.EVIDENCIA_MAX_POR_ORDEM:
        raise EvidenciaError(
            f"Esta ordem aceita no máximo {settings.EVIDENCIA_MAX_POR_ORDEM} evidências (já há {ja_enviadas})."
        )
    return [validar_arquivo(arquivo) for arquivo in arquivos]


@transaction.atomic
def anexar_evidencias(ordem_servico, usuario, arquivos):
    ordem_servico = OrdemServico.objects.select_for_update().get(pk=ordem_servico.pk)

    if ordem_servico.status_ordem_servico not in STATUS_ATIVOS:
        raise EvidenciaError(
            "Esta ordem não aceita novas evidências nesta etapa "
            f"(status atual: {status_para_api(ordem_servico.status_ordem_servico)}).",
            409,
        )

    ja_enviadas = EvidenciaOrdem.objects.filter(ordem_servico=ordem_servico).count()
    validados = validar_lote(arquivos, ja_enviadas)

    proxima = (EvidenciaOrdem.objects.filter(ordem_servico=ordem_servico).aggregate(maximo=Max('sequencia'))['maximo'] or 0) + 1
    agora = timezone.now()
    criadas = []
    for deslocamento, item in enumerate(validados):
        criadas.append(EvidenciaOrdem.objects.create(
            ordem_servico=ordem_servico,
            usuario=usuario,
            sequencia=proxima + deslocamento,
            tipo_arquivo=item.tipo_arquivo,
            tipo_conteudo=item.tipo_conteudo,
            arquivo=item.arquivo,
            nome_original=(item.arquivo.name or 'arquivo')[:255],
            tamanho_bytes=item.arquivo.size,
            dt_envio=agora,
        ))

    registrar_historico(ordem_servico, usuario, f"{usuario.nome} anexou {len(criadas)} evidência(s).")
    return criadas
