import hashlib
import json
import logging
import socket
import threading
import urllib.error
import urllib.request

from django.conf import settings
from django.core.cache import cache as cache_padrao

from inteligencia.provedores import (
    MENSAGEM_INVALIDA,
    ProvedorGemini,
    ProvedorGrok,
    ProvedorIA,
    RespostaInvalidaError,
    resolver_provedor,
)

logger = logging.getLogger(__name__)

MENSAGEM_INDISPONIVEL = "O serviço de inteligência artificial está indisponível no momento. Tente novamente mais tarde."
MENSAGEM_NAO_CONFIGURADO = "O serviço de inteligência artificial não está configurado neste ambiente."

PROVEDOR_GEMINI = ProvedorGemini.nome
PROVEDOR_GROK = ProvedorGrok.nome

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


class ClienteIA:
    _instancia = None
    _trava = threading.Lock()

    def __init__(self, transporte=None, provedor: ProvedorIA | None = None):
        self._transporte = transporte or enviar_http
        self._provedor_fixo = provedor

    @classmethod
    def instancia(cls):
        with cls._trava:
            if cls._instancia is None:
                cls._instancia = ClienteIACacheProxy(cls())
            return cls._instancia

    @classmethod
    def resetar_instancia(cls):
        with cls._trava:
            cls._instancia = None

    @property
    def estrategia(self) -> ProvedorIA:
        return self._provedor_fixo or resolver_provedor()

    @property
    def provedor(self) -> str:
        return self.estrategia.nome

    @property
    def modelo(self) -> str:
        return self.estrategia.modelo

    def configurado(self) -> bool:
        return self.estrategia.configurado()

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

    def gerar(self, sistema, conteudo, max_tokens=None):
        estrategia = self.estrategia
        if not estrategia.configurado():
            raise IAIndisponivelError(MENSAGEM_NAO_CONFIGURADO)

        url, cabecalhos, corpo = estrategia.montar_requisicao(sistema, conteudo, max_tokens or settings.IA_MAX_TOKENS)
        dados = self._chamar(url, cabecalhos, corpo)
        if not isinstance(dados, dict):
            raise IAIndisponivelError(MENSAGEM_INVALIDA, invalida=True)

        try:
            texto = estrategia.extrair_texto(dados)
        except RespostaInvalidaError as erro:
            raise IAIndisponivelError(erro.mensagem, invalida=True) from erro
        if not texto:
            raise IAIndisponivelError(MENSAGEM_INVALIDA, invalida=True)
        return texto


class ClienteIACacheProxy:
    PREFIXO_CHAVE = 'techorder:ia:'

    def __init__(self, cliente: ClienteIA, cache=None, segundos=None):
        self._cliente = cliente
        self._cache = cache or cache_padrao
        self._segundos = segundos

    @property
    def provedor(self) -> str:
        return self._cliente.provedor

    @property
    def modelo(self) -> str:
        return self._cliente.modelo

    def configurado(self) -> bool:
        return self._cliente.configurado()

    def _validade(self) -> int:
        return settings.IA_CACHE_SEGUNDOS if self._segundos is None else self._segundos

    def _chave(self, sistema, conteudo, max_tokens) -> str:
        assinatura = json.dumps([self.provedor, self.modelo, sistema, conteudo, max_tokens], ensure_ascii=False, sort_keys=True, default=str)
        return self.PREFIXO_CHAVE + hashlib.sha256(assinatura.encode('utf-8')).hexdigest()

    def gerar(self, sistema, conteudo, max_tokens=None):
        validade = self._validade()
        if validade <= 0:
            return self._cliente.gerar(sistema, conteudo, max_tokens)

        chave = self._chave(sistema, conteudo, max_tokens)
        resposta = self._cache.get(chave)
        if resposta is not None:
            return resposta

        resposta = self._cliente.gerar(sistema, conteudo, max_tokens)
        self._cache.set(chave, resposta, validade)
        return resposta
