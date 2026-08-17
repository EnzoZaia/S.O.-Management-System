from rest_framework import serializers
from predio.models import Predio

# Serializer para o modelo Predio, que define como os dados do prédio serão convertidos para JSON e validados.
class PredioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Predio
        fields = '__all__'
    
    # Método de validação para o campo 'nome_predio', garantindo que ele não seja vazio e tenha pelo menos 2 caracteres.
    def validate_nome_predio(self, value):
        if not value.strip():
            raise serializers.ValidationError("O nome do prédio é obrigatório.")

        if len(value.strip()) < 2:
            raise serializers.ValidationError("O nome do prédio deve ter pelo menos 2 caracteres.")

        return value