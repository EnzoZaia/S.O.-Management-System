from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from ordem_servico.constantes import (
    AGUARDANDO_MATERIAL,
    AGUARDANDO_TERCEIRO,
    AGUARDANDO_VALIDACAO,
    APROVADA,
    ATRIBUIDA,
    CANCELADA,
    CATEGORIAS_MANUTENCAO,
    CONCLUIDA,
    EM_EXECUCAO,
    EM_TRIAGEM,
    ENCERRADA,
    PAUSADA,
    REABERTA,
    REPROVADA,
    STATUS_FINAIS,
    TIPO_CORRETIVA,
    status_para_api,
)
from utils.permissions import usuario_tem_grupo

STATUS_TRIAGEM = (EM_TRIAGEM, REABERTA)
STATUS_PAUSA = (AGUARDANDO_MATERIAL, AGUARDANDO_TERCEIRO, PAUSADA)
STATUS_PRONTOS_PARA_EXECUCAO = (APROVADA, ATRIBUIDA, REABERTA) + STATUS_PAUSA
STATUS_CONCLUSAO = (CONCLUIDA, AGUARDANDO_VALIDACAO)

JUSTIFICATIVA_TRIAGEM_MIN = 10
DETALHE_PAUSA_MIN = 5
OBSERVACAO_CONCLUSAO_MIN = 10


class RegraTransicaoError(Exception):
    def __init__(self, mensagem, erros=None, status_code=400):
        super().__init__(mensagem)
        self.mensagem = mensagem
        self.erros = erros
        self.status_code = status_code


@dataclass
class ContextoTransicao:
    ordem_servico: object
    usuario: object
    status_anterior: str
    novo_status: str
    dados: dict = field(default_factory=dict)
    observacao: str = ''

    @property
    def observacao_limpa(self):
        return (self.observacao or '').strip()

    @property
    def eh_gestao(self):
        return usuario_tem_grupo(self.usuario, 'GERENTE') or usuario_tem_grupo(self.usuario, 'GESTOR')

    def valor(self, campo):
        if campo in self.dados and self.dados[campo] not in (None, ''):
            return self.dados[campo]
        return getattr(self.ordem_servico, campo, None)


class RegraTransicao(ABC):
    MENSAGEM_STATUS = "Esta ordem não pode ir de {anterior} para {novo} (status atual: {anterior})."

    @abstractmethod
    def validar(self, contexto: ContextoTransicao) -> None:
        ...

    def exigir_origem(self, contexto, origens):
        if contexto.status_anterior not in origens:
            raise RegraTransicaoError(self.MENSAGEM_STATUS.format(
                anterior=status_para_api(contexto.status_anterior), novo=status_para_api(contexto.novo_status),
            ))

    @staticmethod
    def exigir_gestao(contexto, acao):
        if not contexto.eh_gestao:
            raise RegraTransicaoError(f"Somente gestor ou gerente podem {acao}.", None, 403)

    @staticmethod
    def exigir_observacao(contexto, minimo, mensagem_vazia):
        texto = contexto.observacao_limpa
        if not texto:
            raise RegraTransicaoError(mensagem_vazia, {'observacao': [mensagem_vazia]})
        if len(texto) < minimo:
            mensagem = f"Descreva com pelo menos {minimo} caracteres."
            raise RegraTransicaoError(mensagem, {'observacao': [mensagem]})


class RegraAprovacaoTriagem(RegraTransicao):
    def validar(self, contexto):
        self.exigir_gestao(contexto, "aprovar a triagem")
        self.exigir_origem(contexto, STATUS_TRIAGEM)
        erros = {}
        if contexto.valor('categoria_manutencao') not in CATEGORIAS_MANUTENCAO:
            erros['categoria_manutencao'] = ["Selecione a categoria técnica (REFRIGERACAO, ELETRICA ou GERAIS)."]
        if 'prioridade_urgencia' not in contexto.dados:
            erros['prioridade_urgencia'] = ["Selecione a prioridade (SIM ou NAO)."]
        if erros:
            raise RegraTransicaoError("Revise os dados da triagem.", erros)


class RegraReprovacaoTriagem(RegraTransicao):
    def validar(self, contexto):
        self.exigir_gestao(contexto, "reprovar a triagem")
        self.exigir_origem(contexto, STATUS_TRIAGEM)
        self.exigir_observacao(contexto, JUSTIFICATIVA_TRIAGEM_MIN, "Informe a justificativa da reprovação.")


class RegraCancelamento(RegraTransicao):
    def validar(self, contexto):
        self.exigir_gestao(contexto, "cancelar a ordem")
        self.exigir_observacao(contexto, JUSTIFICATIVA_TRIAGEM_MIN, "Informe a justificativa do cancelamento.")


class RegraInicioExecucao(RegraTransicao):
    def validar(self, contexto):
        self.exigir_origem(contexto, STATUS_PRONTOS_PARA_EXECUCAO)
        if not contexto.ordem_servico.tecnico_id:
            raise RegraTransicaoError("Atribua um técnico antes de iniciar a execução (status atual sem técnico).")


class RegraPausa(RegraTransicao):
    def validar(self, contexto):
        self.exigir_origem(contexto, (EM_EXECUCAO,))
        self.exigir_observacao(contexto, DETALHE_PAUSA_MIN, "Informe o motivo da pausa.")


class RegraConclusao(RegraTransicao):
    def validar(self, contexto):
        self.exigir_origem(contexto, (EM_EXECUCAO,) + STATUS_PAUSA)
        erros = {}
        texto = contexto.observacao_limpa
        if not texto:
            erros['observacao'] = ["Informe a observação técnica."]
        elif len(texto) < OBSERVACAO_CONCLUSAO_MIN:
            erros['observacao'] = [f"Descreva com pelo menos {OBSERVACAO_CONCLUSAO_MIN} caracteres."]
        if contexto.ordem_servico.tipo_manutencao == TIPO_CORRETIVA and not str(contexto.valor('causa_raiz') or '').strip():
            erros['causa_raiz'] = ["Informe a causa raiz."]
        if erros:
            raise RegraTransicaoError("Revise os dados da conclusão.", erros)


class RegraSomenteGestao(RegraTransicao):
    def validar(self, contexto):
        self.exigir_gestao(contexto, f"definir o status {status_para_api(contexto.novo_status)}")


REGRAS_POR_STATUS = {
    APROVADA: RegraAprovacaoTriagem(),
    REPROVADA: RegraReprovacaoTriagem(),
    CANCELADA: RegraCancelamento(),
    EM_EXECUCAO: RegraInicioExecucao(),
    AGUARDANDO_MATERIAL: RegraPausa(),
    AGUARDANDO_TERCEIRO: RegraPausa(),
    PAUSADA: RegraPausa(),
    CONCLUIDA: RegraConclusao(),
    AGUARDANDO_VALIDACAO: RegraConclusao(),
    ENCERRADA: RegraSomenteGestao(),
    EM_TRIAGEM: RegraSomenteGestao(),
    REABERTA: RegraSomenteGestao(),
    ATRIBUIDA: RegraSomenteGestao(),
}


class ValidadorTransicao:
    def __init__(self, regras=None):
        self._regras = regras or REGRAS_POR_STATUS

    def validar(self, contexto: ContextoTransicao) -> None:
        if contexto.status_anterior in STATUS_FINAIS:
            raise RegraTransicaoError("Esta ordem não pode mais ser alterada.")
        regra = self._regras.get(contexto.novo_status)
        if regra is not None:
            regra.validar(contexto)
