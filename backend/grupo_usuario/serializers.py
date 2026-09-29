from rest_framework import serializers
from grupo_usuario.models import GrupoUsuario
from usuario.models import Usuario
from grupo.models import Grupo

class GrupoUsuarioSerializer(serializers.ModelSerializer):
    usuario = serializers.PrimaryKeyRelatedField(queryset=Usuario.objects.all())
    grupo = serializers.PrimaryKeyRelatedField(queryset=Grupo.objects.all())

    class Meta:
        model = GrupoUsuario
        fields = '__all__'

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
