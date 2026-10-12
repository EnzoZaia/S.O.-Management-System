from rest_framework import serializers

from auditoria_usuario.models import AuditoriaUsuario


class AuditoriaUsuarioSerializer(serializers.ModelSerializer):
    autor_nome = serializers.CharField(source='autor.nome', read_only=True)
    usuario_alvo_nome = serializers.CharField(source='usuario_alvo.nome', read_only=True)

    class Meta:
        model = AuditoriaUsuario
        fields = ['id_auditoria', 'usuario_alvo', 'usuario_alvo_nome', 'autor', 'autor_nome', 'campo', 'valor_anterior', 'valor_novo', 'dt_registro']
