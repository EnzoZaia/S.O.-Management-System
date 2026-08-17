from rest_framework import serializers
from localizacao.models import Localizacao

# Serializer para o modelo Localizacao
class LocalizacaoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Localizacao
        fields = '__all__'
    
    # Validação para o campo desc_localizacao
    def validate_desc_localizacao(self, value):
        if not value.strip():
            raise serializers.ValidationError("A descrição da localização é obrigatória.")

        if len(value.strip()) < 3:
            raise serializers.ValidationError("A localização deve ter pelo menos 3 caracteres.")

        return value