import json
import logging
import socket
import threading
import urllib.error
import urllib.request

from django.conf import settings

logger = logging.getLogger(__name__)

MENSAGEM_INDISPONIVEL = "O serviço de inteligência artificial está indisponível no momento. Tente novamente mais tarde."
MENSAGEM_NAO_CONFIGURADO = "O serviço de inteligência artificial não está configurado neste ambiente."
MENSAGEM_INVALIDA = "O serviço de inteligência artificial retornou uma resposta vazia ou inválida."
MENSAGEM_BLOQUEADA = "O serviço de inteligência artificial não pôde responder a esta solicitação."

PROVEDOR_GEMINI = 'gemini'
PROVEDOR_GROK = 'grok'

URL_GEMINI = "https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent"
URL_GROK = "https://api.x.ai/v1/chat/completions"

MOTIVOS_BLOQUEIO_GEMINI = {'SAFETY', 'PROHIBITED_CONTENT', 'BLOCKLIST', 'SPII', 'RECITATION', 'IMAGE_SAFETY'}
STATUS_HTTP_REPETIVEIS = {408, 429, 500, 502, 503, 504}


class IAIndisponivelError(Exception):
    def __init__(self, mensagem=MENSAGEM_INDISPONIVEL, invalida=False):
        super().__init__(mensagem)
        self.mensagem = mensagem
        self.invalida = invalida


class FalhaTransporte(Exception):
    def __init__(self, status=None):
        super().__init__(f"Falha HTTP {status}" if status else "Falha de conexão")
        self.status = status


def enviar_http(url, cabecalhos, corpo, timeout):
    requisicao = urllib.request.Request(
        url,
        data=json.dumps(corpo).encode('utf-8'),
        headers={'Content-Type': 'application/json', **cabecalhos},
        method='POST',
    )
    try:
        with urllib.request.urlopen(requisicao, timeout=timeout) as resposta:
            return json.loads(resposta.read().decode('utf-8'))
    except urllib.error.HTTPError as erro:
        raise FalhaTransporte(erro.code) from erro
    except (urllib.error.URLError, TimeoutError, socket.timeout, ConnectionError, ValueError) as erro:
        raise FalhaTransporte() from erro


def _partes_gemini(conteudo):
    if isinstance(conteudo, str):
        return [{'text': conteudo}]
    partes = []
    for bloco in conteudo:
        if bloco.get('type') == 'document':
            fonte = bloco['source']
            if fonte['type'] == 'base64':
                partes.append({'inline_data': {'mime_type': fonte['media_type'], 'data': fonte['data']}})
            else:
                partes.append({'text': f"Documento: {bloco.get('title', '')}\n{fonte['data']}"})
        else:
            partes.append({'text': bloco.get('text', '')})
    return partes


def _texto_grok(conteudo):
    if isinstance(conteudo, str):
        return conteudo
    trechos = []
    for bloco in conteudo:
        if bloco.get('type') == 'document':
            fonte = bloco['source']
            if fonte['type'] == 'base64':
                trechos.append(f"[Manual em PDF \"{bloco.get('title', '')}\" não pôde ser enviado a este provedor.]")
            else:
                trechos.append(f"Documento: {bloco.get('title', '')}\n{fonte['data']}")
        else:
            trechos.append(bloco.get('text', ''))
    return '\n\n'.join(trechos)


class ClienteIA:
    _instancia = None
    _trava = threading.Lock()

    def __init__(self, transporte=None):
        self._transporte = transporte or enviar_http

    @classmethod
    def instancia(cls):
        with cls._trava:
            if cls._instancia is None:
                cls._instancia = cls()
            return cls._instancia

    @classmethod
    def resetar_instancia(cls):
        with cls._trava:
            cls._instancia = None

    @property
    def provedor(self):
        return (settings.IA_PROVEDOR or PROVEDOR_GEMINI).strip().lower()

    @property
    def modelo(self):
        if self.provedor == PROVEDOR_GROK:
            return settings.GROK_MODEL
        return settings.GEMINI_MODEL

    def _chave(self):
        if self.provedor == PROVEDOR_GROK:
            return settings.GROK_API_KEY
        return settings.GEMINI_API_KEY

    def configurado(self):
        return self.provedor in (PROVEDOR_GEMINI, PROVEDOR_GROK) and bool(self._chave())

    def _montar_requisicao(self, sistema, conteudo, max_tokens):
        if self.provedor == PROVEDOR_GROK:
            return URL_GROK, {'Authorization': f"Bearer {self._chave()}"}, {
                'model': self.modelo,
                'max_tokens': max_tokens,
                'temperature': 0.3,
                'messages': [
                    {'role': 'system', 'content': sistema},
                    {'role': 'user', 'content': _texto_grok(conteudo)},
                ],
            }
        return URL_GEMINI.format(modelo=self.modelo), {'x-goog-api-key': self._chave()}, {
            'system_instruction': {'parts': [{'text': sistema}]},
            'contents': [{'role': 'user', 'parts': _partes_gemini(conteudo)}],
            'generationConfig': {'maxOutputTokens': max_tokens, 'temperature': 0.3},
        }

    def _chamar(self, url, cabecalhos, corpo):
        tentativas = 1 + max(settings.IA_MAX_RETRIES, 0)
        for tentativa in range(1, tentativas + 1):
            try:
                return self._transporte(url, cabecalhos, corpo, settings.IA_TIMEOUT_SEGUNDOS)
            except FalhaTransporte as erro:
                repetivel = erro.status is None or erro.status in STATUS_HTTP_REPETIVEIS
                logger.warning("Falha na chamada ao provedor de IA %s (tentativa %s): %s", self.provedor, tentativa, erro)
                if not repetivel or tentativa == tentativas:
                    raise IAIndisponivelError() from erro

    def _extrair_gemini(self, dados):
        if (dados.get('promptFeedback') or {}).get('blockReason'):
            raise IAIndisponivelError(MENSAGEM_BLOQUEADA, invalida=True)
        candidatos = dados.get('candidates') or []
        if not candidatos:
            raise IAIndisponivelError(MENSAGEM_INVALIDA, invalida=True)
        candidato = candidatos[0]
        if candidato.get('finishReason') in MOTIVOS_BLOQUEIO_GEMINI:
            raise IAIndisponivelError(MENSAGEM_BLOQUEADA, invalida=True)
        partes = (candidato.get('content') or {}).get('parts') or []
        return '\n'.join(parte['text'] for parte in partes if parte.get('text') and not parte.get('thought')).strip()

    def _extrair_grok(self, dados):
        escolhas = dados.get('choices') or []
        if not escolhas:
            raise IAIndisponivelError(MENSAGEM_INVALIDA, invalida=True)
        if escolhas[0].get('finish_reason') == 'content_filter':
            raise IAIndisponivelError(MENSAGEM_BLOQUEADA, invalida=True)
        return str((escolhas[0].get('message') or {}).get('content') or '').strip()

    def gerar(self, sistema, conteudo, max_tokens=None):
        if not self.configurado():
            raise IAIndisponivelError(MENSAGEM_NAO_CONFIGURADO)

        url, cabecalhos, corpo = self._montar_requisicao(sistema, conteudo, max_tokens or settings.IA_MAX_TOKENS)
        dados = self._chamar(url, cabecalhos, corpo)
        if not isinstance(dados, dict):
            raise IAIndisponivelError(MENSAGEM_INVALIDA, invalida=True)

        texto = self._extrair_grok(dados) if self.provedor == PROVEDOR_GROK else self._extrair_gemini(dados)
        if not texto:
            raise IAIndisponivelError(MENSAGEM_INVALIDA, invalida=True)
        return texto
