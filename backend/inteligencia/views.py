from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from inteligencia.cliente import IAIndisponivelError
from inteligencia.services import consultar_assistente, gerar_insight
from ordem_servico.constantes import STATUS_ATIVOS, TIPO_CORRETIVA, status_para_api
from ordem_servico.indicadores import PeriodoInvalidoError, calcular_indicadores_gerenciais, resolver_periodo
from ordem_servico.models import OrdemServico
from utils.historico import registrar_historico
from utils.permissions import IsGerente
from utils.responses import resposta_erro, resposta_sucesso

PERGUNTA_MIN = 5
PERGUNTA_MAX = 1000


class AssistenteTecnicoView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, pk):
        ordem_servico = get_object_or_404(OrdemServico.objects.select_related('ativo'), pk=pk)

        if ordem_servico.tecnico_id != request.user.pk:
            self.permission_denied(request, message="Somente o técnico atribuído a esta ordem pode consultar o assistente.")

        if ordem_servico.tipo_manutencao != TIPO_CORRETIVA:
            return resposta_erro("O assistente técnico está disponível apenas para ordens corretivas.", None)

        if ordem_servico.status_ordem_servico not in STATUS_ATIVOS:
            return resposta_erro(
                f"O assistente só pode ser usado em ordens em andamento (status atual: {status_para_api(ordem_servico.status_ordem_servico)}).",
                None,
            )

        pergunta = str(request.data.get('pergunta') or '').strip()
        if len(pergunta) < PERGUNTA_MIN or len(pergunta) > PERGUNTA_MAX:
            mensagem = f"Escreva a pergunta com {PERGUNTA_MIN} a {PERGUNTA_MAX} caracteres."
            return resposta_erro(mensagem, {'pergunta': [mensagem]})

        try:
            dados = consultar_assistente(ordem_servico, pergunta, request.user)
        except IAIndisponivelError as erro:
            return resposta_erro(erro.mensagem, None, status.HTTP_503_SERVICE_UNAVAILABLE)

        registrar_historico(ordem_servico, request.user, f"{request.user.nome} consultou o assistente técnico de IA.")
        return resposta_sucesso("Resposta do assistente gerada com sucesso.", {'pergunta': pergunta, **dados})


class TechOrderIntelligenceView(APIView):
    permission_classes = (IsAuthenticated, IsGerente)

    def post(self, request):
        try:
            periodo = resolver_periodo(request.data.get('periodo'), request.data.get('inicio'), request.data.get('fim'))
        except PeriodoInvalidoError as erro:
            return resposta_erro(str(erro), {'periodo': [str(erro)]})

        indicadores = calcular_indicadores_gerenciais(periodo)
        try:
            dados = gerar_insight(indicadores, request.user)
        except IAIndisponivelError as erro:
            return resposta_erro(erro.mensagem, None, status.HTTP_503_SERVICE_UNAVAILABLE)

        return resposta_sucesso("Análise do TechOrder Intelligence gerada com sucesso.", dados)
