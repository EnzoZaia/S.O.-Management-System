import os

from rest_framework import serializers

from validacao.models import EvidenciaValidacao, ValidacaoAtendimento

JUSTIFICATIVA_MIN = 10
JUSTIFICATIVA_MAX = 200
EVIDENCIAS_MAX = 3
EVIDENCIA_TAMANHO_MAX_MB = 5
NOTA_MIN = 1
NOTA_MAX = 5
COMENTARIO_MAX = 300
EXTENSOES_IMAGEM_PERMITIDAS = ('.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.heic', '.heif')


class EvidenciaValidacaoSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()

    class Meta:
        model = EvidenciaValidacao
        fields = ['id_evidencia', 'nome_original', 'url', 'dt_upload']

    def get_url(self, obj):
        if not obj.arquivo:
            return None
        request = self.context.get('request')
        return request.build_absolute_uri(obj.arquivo.url) if request else obj.arquivo.url


class ValidacaoAtendimentoSerializer(serializers.ModelSerializer):
    aprovada = serializers.BooleanField(read_only=True)
    respondido_por_nome = serializers.CharField(source='usuario.nome', read_only=True, default=None)
    dt_resposta = serializers.DateTimeField(source='dt_validacao', read_only=True)
    evidencias = serializers.SerializerMethodField()

    class Meta:
        model = ValidacaoAtendimento
        fields = ['id_validacao', 'aprovada', 'resultado', 'justificativa', 'respondido_por_nome', 'dt_resposta', 'evidencias']

    def get_evidencias(self, obj):
        evidencias = obj.evidencias.filter(dt_upload__gte=obj.dt_validacao)
        return EvidenciaValidacaoSerializer(evidencias, many=True, context=self.context).data


class AvaliacaoSerializer(serializers.ModelSerializer):
    id_avaliacao = serializers.IntegerField(source='id_validacao', read_only=True)
    avaliado_por_nome = serializers.CharField(source='usuario.nome', read_only=True, default=None)
    dt_avaliacao = serializers.DateTimeField(source='dt_validacao', read_only=True)

    class Meta:
        model = ValidacaoAtendimento
        fields = ['id_avaliacao', 'nota', 'comentario', 'avaliado_por_nome', 'dt_avaliacao']


class AvaliarOrdemServicoSerializer(serializers.Serializer):
    MENSAGEM_NOTA = f"A nota deve ser um número inteiro de {NOTA_MIN} a {NOTA_MAX}."

    nota = serializers.IntegerField(
        min_value=NOTA_MIN,
        max_value=NOTA_MAX,
        error_messages={
            'required': "Selecione uma nota de 1 a 5 estrelas.",
            'null': "Selecione uma nota de 1 a 5 estrelas.",
            'invalid': MENSAGEM_NOTA,
            'min_value': MENSAGEM_NOTA,
            'max_value': MENSAGEM_NOTA,
        },
    )
    comentario = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
        max_length=COMENTARIO_MAX,
        error_messages={'max_length': f"Use no máximo {COMENTARIO_MAX} caracteres."},
    )

    def validate_nota(self, valor):
        if isinstance(self.initial_data.get('nota'), bool):
            raise serializers.ValidationError(self.MENSAGEM_NOTA)
        return valor


class ValidarOrdemServicoSerializer(serializers.Serializer):
    aprovada = serializers.BooleanField()
    justificativa = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    evidencias = serializers.ListField(child=serializers.FileField(), required=False, allow_empty=True)

    def validate_evidencias(self, arquivos):
        if len(arquivos) > EVIDENCIAS_MAX:
            raise serializers.ValidationError(f"Envie no máximo {EVIDENCIAS_MAX} imagens.")

        for arquivo in arquivos:
            extensao = os.path.splitext(arquivo.name or '')[1].lower()
            tipo = (getattr(arquivo, 'content_type', '') or '').lower()

            if not tipo.startswith('image/') or extensao not in EXTENSOES_IMAGEM_PERMITIDAS:
                raise serializers.ValidationError(f'"{arquivo.name}" não é uma imagem aceita.')

            if arquivo.size > EVIDENCIA_TAMANHO_MAX_MB * 1024 * 1024:
                raise serializers.ValidationError(f'"{arquivo.name}" passa de {EVIDENCIA_TAMANHO_MAX_MB} MB.')

        return arquivos

    def validate(self, dados):
        if 'aprovada' not in self.initial_data:
            raise serializers.ValidationError({'aprovada': ["Informe se o serviço foi aprovado (true/false)."]})

        justificativa = (dados.get('justificativa') or '').strip()

        if not dados['aprovada']:
            if not justificativa:
                raise serializers.ValidationError({'justificativa': ["Informe o motivo da reprovação."]})
            if len(justificativa) < JUSTIFICATIVA_MIN:
                raise serializers.ValidationError({'justificativa': [f"Descreva o motivo com pelo menos {JUSTIFICATIVA_MIN} caracteres."]})

        if len(justificativa) > JUSTIFICATIVA_MAX:
            raise serializers.ValidationError({'justificativa': [f"Use no máximo {JUSTIFICATIVA_MAX} caracteres."]})

        dados['justificativa'] = justificativa or None
        return dados
