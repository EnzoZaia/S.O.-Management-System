from rest_framework import serializers
from grupo.models import Grupo

# Serializer para o modelo "Grupo"
class GrupoSerializer(serializers.ModelSerializer):
    # Configurações do serializer
    class Meta:
        model = Grupo
        fields = '__all__'

    # Validações personalizadas para os campos do modelo
    def validate_desc_grupo(self, value):
        if not value.strip():
            raise serializers.ValidationError("A descrição do grupo é obrigatória.")

        grupos_validos = ["GERENTE", "GESTOR", "TECNICO", "SOLICITANTE"]

        if value.upper() not in grupos_validos:
            raise serializers.ValidationError("Grupo inválido. Use: GERENTE, GESTOR, TECNICO ou SOLICITANTE.")

        return value.upper()

    # Validação personalizada para o campo "desc_permissao"
    def validate_desc_permissao(self, value):
        if value and len(value.strip()) < 5:
            raise serializers.ValidationError("A descrição da permissão está muito curta.")

        return value