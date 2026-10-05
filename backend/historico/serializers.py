from rest_framework import serializers
from historico.models import Historico

class HistoricoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Historico
        fields = '__all__'

    def validate_desc_historico(self, value):
        if not value.strip():
            raise serializers.ValidationError("A descrição do histórico é obrigatória.")

        if len(value.strip()) < 5:
            raise serializers.ValidationError("A descrição do histórico deve ter pelo menos 5 caracteres.")

        return value
