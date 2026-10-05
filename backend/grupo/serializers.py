from rest_framework import serializers
from grupo.models import Grupo

class GrupoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Grupo
        fields = '__all__'

    def validate_desc_grupo(self, value):
        if not value.strip():
            raise serializers.ValidationError("A descrição do grupo é obrigatória.")

        grupos_validos = ["GERENTE", "GESTOR", "TECNICO", "SOLICITANTE"]

        if value.upper() not in grupos_validos:
            raise serializers.ValidationError("Grupo inválido. Use: GERENTE, GESTOR, TECNICO ou SOLICITANTE.")

        return value.upper()

    def validate_desc_permissao(self, value):
        if value and len(value.strip()) < 5:
            raise serializers.ValidationError("A descrição da permissão está muito curta.")

        return value
