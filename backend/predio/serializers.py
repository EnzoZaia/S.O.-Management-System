from rest_framework import serializers
from predio.models import Predio

class PredioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Predio
        fields = '__all__'

    def validate_nome_predio(self, value):
        if not value.strip():
            raise serializers.ValidationError("O nome do prédio é obrigatório.")

        if len(value.strip()) < 2:
            raise serializers.ValidationError("O nome do prédio deve ter pelo menos 2 caracteres.")

        return value
