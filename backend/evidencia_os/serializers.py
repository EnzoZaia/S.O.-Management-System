from rest_framework import serializers

from evidencia_os.models import EvidenciaOrdem


class EvidenciaOrdemSerializer(serializers.ModelSerializer):
    ordem = serializers.IntegerField(source='sequencia', read_only=True)
    url = serializers.SerializerMethodField()
    enviado_por = serializers.IntegerField(source='usuario_id', read_only=True)
    enviado_por_nome = serializers.CharField(source='usuario.nome', read_only=True, default=None)

    class Meta:
        model = EvidenciaOrdem
        fields = ['id_evidencia_ordem', 'ordem', 'nome_original', 'tipo_arquivo', 'tipo_conteudo', 'tamanho_bytes', 'url', 'enviado_por', 'enviado_por_nome', 'dt_envio']

    def get_url(self, obj):
        if not obj.arquivo:
            return None
        request = self.context.get('request')
        return request.build_absolute_uri(obj.arquivo.url) if request else obj.arquivo.url
