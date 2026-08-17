from rest_framework import serializers
from grupo_usuario.models import GrupoUsuario
from usuario.models import Usuario
from grupo.models import Grupo

# Serializer para o modelo GrupoUsuario
class GrupoUsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = GrupoUsuario
        fields = '__all__'
    
    # Validação personalizada para garantir que o usuário e o grupo existam e que a associação seja única
    def validate(self, data):
        id_usuario = data.get("id_usuario")
        id_grupo = data.get("id_grupo")

        if not Usuario.objects.filter(id_usuario=id_usuario).exists():
            raise serializers.ValidationError({"id_usuario": "Usuário informado não existe."})

        if not Grupo.objects.filter(id_grupo=id_grupo).exists():
            raise serializers.ValidationError({"id_grupo": "Grupo informado não existe."})

        if GrupoUsuario.objects.filter(id_usuario=id_usuario, id_grupo=id_grupo).exists():
            raise serializers.ValidationError("Este usuário já está vinculado a este grupo.")

        return data