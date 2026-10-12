from rest_framework import serializers
from historico.models import Historico
from ordem_servico.constantes import DESCRICAO_HISTORICO_TRIGGER, status_para_api
from utils.historico import texto_mudanca_status

class HistoricoSerializer(serializers.ModelSerializer):
    usuario_nome = serializers.CharField(source='usuario.nome', read_only=True, default=None)
    tecnico_nome = serializers.CharField(source='tecnico.nome', read_only=True, default=None)

    class Meta:
        model = Historico
        fields = '__all__'

    def to_representation(self, instance):
        dados = super().to_representation(instance)
        dados['status_anterior'] = status_para_api(instance.status_anterior) if instance.status_anterior else None
        dados['status_novo'] = status_para_api(instance.status_novo) if instance.status_novo else None
        if instance.status_novo and (not instance.desc_historico or instance.desc_historico == DESCRICAO_HISTORICO_TRIGGER):
            dados['desc_historico'] = texto_mudanca_status(instance.status_anterior, instance.status_novo)
        return dados

    def validate_desc_historico(self, value):
        if not value.strip():
            raise serializers.ValidationError("A descrição do histórico é obrigatória.")

        if len(value.strip()) < 5:
            raise serializers.ValidationError("A descrição do histórico deve ter pelo menos 5 caracteres.")

        return value
