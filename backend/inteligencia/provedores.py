from abc import ABC, abstractmethod

from django.conf import settings

MENSAGEM_INVALIDA = "O serviço de inteligência artificial retornou uma resposta vazia ou inválida."
MENSAGEM_BLOQUEADA = "O serviço de inteligência artificial não pôde responder a esta solicitação."

MOTIVOS_BLOQUEIO_GEMINI = {'SAFETY', 'PROHIBITED_CONTENT', 'BLOCKLIST', 'SPII', 'RECITATION', 'IMAGE_SAFETY'}


class RespostaInvalidaError(Exception):
    def __init__(self, mensagem=MENSAGEM_INVALIDA):
        super().__init__(mensagem)
        self.mensagem = mensagem


class ProvedorIA(ABC):
    nome = ''

    @property
    @abstractmethod
    def modelo(self) -> str:
        ...

    @property
    @abstractmethod
    def chave(self) -> str:
        ...

    def configurado(self) -> bool:
        return bool(self.chave)

    @abstractmethod
    def montar_requisicao(self, sistema, conteudo, max_tokens):
        ...

    @abstractmethod
    def extrair_texto(self, dados: dict) -> str:
        ...


class ProvedorGemini(ProvedorIA):
    nome = 'gemini'
    URL = "https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent"

    @property
    def modelo(self):
        return settings.GEMINI_MODEL

    @property
    def chave(self):
        return settings.GEMINI_API_KEY

    @staticmethod
    def _partes(conteudo):
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

    def montar_requisicao(self, sistema, conteudo, max_tokens):
        return self.URL.format(modelo=self.modelo), {'x-goog-api-key': self.chave}, {
            'system_instruction': {'parts': [{'text': sistema}]},
            'contents': [{'role': 'user', 'parts': self._partes(conteudo)}],
            'generationConfig': {'maxOutputTokens': max_tokens, 'temperature': 0.3},
        }

    def extrair_texto(self, dados):
        if (dados.get('promptFeedback') or {}).get('blockReason'):
            raise RespostaInvalidaError(MENSAGEM_BLOQUEADA)
        candidatos = dados.get('candidates') or []
        if not candidatos:
            raise RespostaInvalidaError()
        candidato = candidatos[0]
        if candidato.get('finishReason') in MOTIVOS_BLOQUEIO_GEMINI:
            raise RespostaInvalidaError(MENSAGEM_BLOQUEADA)
        partes = (candidato.get('content') or {}).get('parts') or []
        return '\n'.join(parte['text'] for parte in partes if parte.get('text') and not parte.get('thought')).strip()


class ProvedorGrok(ProvedorIA):
    nome = 'grok'
    URL = "https://api.x.ai/v1/chat/completions"

    @property
    def modelo(self):
        return settings.GROK_MODEL

    @property
    def chave(self):
        return settings.GROK_API_KEY

    @staticmethod
    def _texto(conteudo):
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

    def montar_requisicao(self, sistema, conteudo, max_tokens):
        return self.URL, {'Authorization': f"Bearer {self.chave}"}, {
            'model': self.modelo,
            'max_tokens': max_tokens,
            'temperature': 0.3,
            'messages': [
                {'role': 'system', 'content': sistema},
                {'role': 'user', 'content': self._texto(conteudo)},
            ],
        }

    def extrair_texto(self, dados):
        escolhas = dados.get('choices') or []
        if not escolhas:
            raise RespostaInvalidaError()
        if escolhas[0].get('finish_reason') == 'content_filter':
            raise RespostaInvalidaError(MENSAGEM_BLOQUEADA)
        return str((escolhas[0].get('message') or {}).get('content') or '').strip()


class ProvedorNaoConfigurado(ProvedorIA):
    def __init__(self, nome):
        self.nome = nome

    @property
    def modelo(self):
        return ''

    @property
    def chave(self):
        return ''

    def montar_requisicao(self, sistema, conteudo, max_tokens):
        raise NotImplementedError

    def extrair_texto(self, dados):
        raise NotImplementedError


PROVEDORES = {
    ProvedorGemini.nome: ProvedorGemini,
    ProvedorGrok.nome: ProvedorGrok,
}


def registrar_provedor(classe_provedor) -> None:
    PROVEDORES[classe_provedor.nome] = classe_provedor


def resolver_provedor(nome=None) -> ProvedorIA:
    nome = (nome or settings.IA_PROVEDOR or ProvedorGemini.nome).strip().lower()
    classe = PROVEDORES.get(nome)
    return classe() if classe else ProvedorNaoConfigurado(nome)
