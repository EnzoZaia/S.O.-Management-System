import logging
import threading

import anthropic
from django.conf import settings

logger = logging.getLogger(__name__)

MODELOS_COM_FALLBACK = {'claude-opus-5-5', 'claude-opus-5', 'claude-fable-5-1', 'claude-sonnet-5-5'}
BETA_FALLBACK = 'server-side-fallback-2026-07-01'
MENSAGEM_INDISPONIVEL = "O serviço de inteligência artificial está indisponível no momento. Tente novamente mais tarde."
MENSAGEM_NAO_CONFIGURADO = "O serviço de inteligência artificial não está configurado neste ambiente."


class IAIndisponivelError(Exception):
    def __init__(self, mensagem=MENSAGEM_INDISPONIVEL, invalida=False):
        super().__init__(mensagem)
        self.mensagem = mensagem
        self.invalida = invalida


class ClienteIA:
    PROVEDOR = 'anthropic'
    _instancia = None
    _trava = threading.Lock()

    def __init__(self, fabrica_cliente=None):
        self._fabrica_cliente = fabrica_cliente or self._criar_cliente_anthropic
        self._cliente = None

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

    @staticmethod
    def configurado():
        return bool(settings.ANTHROPIC_API_KEY)

    @property
    def modelo(self):
        return settings.ANTHROPIC_MODEL

    @staticmethod
    def _criar_cliente_anthropic():
        return anthropic.Anthropic(
            api_key=settings.ANTHROPIC_API_KEY,
            timeout=settings.ANTHROPIC_TIMEOUT_SEGUNDOS,
            max_retries=settings.ANTHROPIC_MAX_RETRIES,
        )

    def _obter_cliente(self):
        if self._cliente is None:
            self._cliente = self._fabrica_cliente()
        return self._cliente

    def gerar(self, sistema, conteudo, max_tokens=None):
        if not self.configurado():
            raise IAIndisponivelError(MENSAGEM_NAO_CONFIGURADO)

        parametros = {
            'model': self.modelo,
            'max_tokens': max_tokens or settings.ANTHROPIC_MAX_TOKENS,
            'system': sistema,
            'messages': [{'role': 'user', 'content': conteudo}],
            'output_config': {'effort': 'medium'},
        }

        try:
            cliente = self._obter_cliente()
            if self.modelo in MODELOS_COM_FALLBACK:
                resposta = cliente.beta.messages.create(betas=[BETA_FALLBACK], fallbacks='default', **parametros)
            else:
                resposta = cliente.messages.create(**parametros)
        except anthropic.APITimeoutError as erro:
            logger.warning("Tempo esgotado na chamada ao provedor de IA: %s", erro)
            raise IAIndisponivelError() from erro
        except anthropic.APIConnectionError as erro:
            logger.warning("Falha de conexão com o provedor de IA: %s", erro)
            raise IAIndisponivelError() from erro
        except anthropic.RateLimitError as erro:
            logger.warning("Limite de uso do provedor de IA atingido: %s", erro)
            raise IAIndisponivelError() from erro
        except anthropic.APIStatusError as erro:
            logger.warning("Provedor de IA respondeu com erro %s: %s", erro.status_code, erro)
            raise IAIndisponivelError() from erro
        except anthropic.AnthropicError as erro:
            logger.warning("Erro do SDK do provedor de IA: %s", erro)
            raise IAIndisponivelError() from erro

        if getattr(resposta, 'stop_reason', None) == 'refusal':
            raise IAIndisponivelError("O serviço de inteligência artificial não pôde responder a esta solicitação.", invalida=True)

        texto = '\n'.join(
            bloco.text for bloco in getattr(resposta, 'content', []) or []
            if getattr(bloco, 'type', None) == 'text' and getattr(bloco, 'text', None)
        ).strip()
        if not texto:
            raise IAIndisponivelError("O serviço de inteligência artificial retornou uma resposta vazia ou inválida.", invalida=True)
        return texto
