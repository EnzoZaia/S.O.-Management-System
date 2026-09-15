from rest_framework import serializers
from grupo_usuario.models import GrupoUsuario
from usuario.models import Usuario
from grupo.models import Grupo

# Serializer para o modelo GrupoUsuario
class GrupoUsuarioSerializer(serializers.ModelSerializer):
    # Declarados explicitamente: como 'usuario' é a chave primária do model
    # (ForeignKey com primary_key=True), o ModelSerializer o gera como um
    # inteiro puro em vez de PrimaryKeyRelatedField, quebrando o create().
    usuario = serializers.PrimaryKeyRelatedField(queryset=Usuario.objects.all())
    grupo = serializers.PrimaryKeyRelatedField(queryset=Grupo.objects.all())

    class Meta:
        model = GrupoUsuario
        fields = '__all__'

    # Validação personalizada para garantir que a associação usuário/grupo seja única
    def validate(self, data):
        usuario = data.get("usuario")
        grupo = data.get("grupo")

        if usuario is not None and grupo is not None:
            queryset = GrupoUsuario.objects.filter(usuario=usuario, grupo=grupo)
            if self.instance is not None:
                queryset = queryset.exclude(pk=self.instance.pk)
            if queryset.exists():
                raise serializers.ValidationError("Este usuário já está vinculado a este grupo.")

        return data