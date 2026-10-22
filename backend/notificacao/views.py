from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from notificacao.models import Notificacao
from utils.responses import resposta_sucesso


class NotificacaoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notificacao
        fields = ['id_notificacao', 'tipo', 'titulo', 'mensagem', 'ordem_servico', 'lida', 'dt_criacao', 'dt_leitura']


class NotificacaoListView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        notificacoes = Notificacao.objects.filter(usuario=request.user).order_by('-dt_criacao', '-id_notificacao')
        if str(request.query_params.get('nao_lidas', '')).lower() in ('true', '1', 'sim'):
            notificacoes = notificacoes.filter(lida=False)
        dados = {
            'nao_lidas': Notificacao.objects.filter(usuario=request.user, lida=False).count(),
            'notificacoes': NotificacaoSerializer(notificacoes[:100], many=True).data,
        }
        return resposta_sucesso("Notificações carregadas com sucesso.", dados)


class NotificacaoLidaView(APIView):
    permission_classes = (IsAuthenticated,)

    def patch(self, request, pk):
        notificacao = get_object_or_404(Notificacao, pk=pk, usuario=request.user)
        if not notificacao.lida:
            notificacao.lida = True
            notificacao.dt_leitura = timezone.now()
            notificacao.save(update_fields=['lida', 'dt_leitura'])
        return resposta_sucesso("Notificação marcada como lida.", NotificacaoSerializer(notificacao).data)
