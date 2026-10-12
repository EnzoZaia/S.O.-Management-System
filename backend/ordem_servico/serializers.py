from rest_framework import serializers
from ordem_servico.constantes import (
    CATEGORIAS_MANUTENCAO,
    PRIORIDADE_DA_API,
    PRIORIDADE_PARA_API,
    PRIORIDADES_VALIDAS,
    STATUS_VALIDOS,
    TIPOS_MANUTENCAO,
    status_da_api,
    status_para_api,
)
from ativo.models import Ativo
from ordem_servico.fachada import OrdemServicoFacade
from ordem_servico.models import OrdemServico


class StatusOrdemServicoField(serializers.CharField):
    def to_representation(self, value):
        return status_para_api(value)

    def to_internal_value(self, data):
        valor = status_da_api(super().to_internal_value(data).strip().upper())
        if valor not in STATUS_VALIDOS:
            raise serializers.ValidationError("Status inválido.")
        return valor


class PrioridadeUrgenciaField(serializers.CharField):
    def to_representation(self, value):
        return PRIORIDADE_PARA_API.get(value, value)

    def to_internal_value(self, data):
        valor = super().to_internal_value(data).strip().upper()
        valor = PRIORIDADE_DA_API.get(valor, valor)
        if valor not in PRIORIDADES_VALIDAS:
            raise serializers.ValidationError("Valor inválido. Use: SIM ou NAO.")
        return valor


class OrdemServicoSerializer(serializers.ModelSerializer):
    status_ordem_servico = StatusOrdemServicoField(required=False)
    prioridade_urgencia = PrioridadeUrgenciaField(required=False)

    predio_nome = serializers.CharField(source='localizacao.predio.nome_predio', read_only=True, default="Totem")
    localizacao_nome = serializers.CharField(source='localizacao.desc_localizacao', read_only=True, default="")
    solicitante_nome = serializers.CharField(source='solicitante.nome', read_only=True, default="Totem (Anônimo)")
    tecnico = serializers.IntegerField(source='tecnico_id', read_only=True, default=None)
    tecnico_nome = serializers.CharField(read_only=True, default=None)
    gestor = serializers.IntegerField(source='gestor_id', read_only=True, default=None)
    gestor_nome = serializers.CharField(read_only=True, default=None)
    ativo_nome = serializers.SerializerMethodField()
    ativo_patrimonio = serializers.CharField(source='ativo.codigo_patrimonial', read_only=True, default="")
    ativo_ultima_preventiva = serializers.DateField(source='ativo.dt_ultima_preventiva', read_only=True, default=None)
    ativo_proxima_preventiva = serializers.DateField(source='ativo.dt_proxima_preventiva', read_only=True, default=None)
    vinculo_presenciei = serializers.SerializerMethodField()
    total_afetados = serializers.IntegerField(read_only=True)

    class Meta:
        model = OrdemServico
        fields = '__all__'
        read_only_fields = ['id_ordem_servico', 'id_solicitacao', 'solicitante', 'dt_abertura', 'dt_conclusao']

    def get_vinculo_presenciei(self, obj):
        ids_vinculados = self._ids_os_presenciadas()
        return obj.id_ordem_servico in ids_vinculados

    def _ids_os_presenciadas(self):
        if '_ids_os_presenciadas' in self.context:
            return self.context['_ids_os_presenciadas']

        request = self.context.get('request')
        usuario = getattr(request, 'user', None)
        ids = set()

        if usuario is not None and getattr(usuario, 'is_authenticated', False):
            from os_participante.models import OsParticipante
            ids = set(OsParticipante.objects.filter(usuario=usuario).values_list('ordem_servico_id', flat=True))

        if isinstance(self.context, dict):
            self.context['_ids_os_presenciadas'] = ids
        return ids

    def get_ativo_nome(self, obj):
        if obj.ativo:
            return f"{obj.ativo.marca} {obj.ativo.modelo}"
        return ""

    def validate_tipo_manutencao(self, value):
        if value not in TIPOS_MANUTENCAO:
            raise serializers.ValidationError("Tipo de manutenção inválido. Use: CORRETIVA ou PREVENTIVA.")

        return value

    def validate_categoria_manutencao(self, value):
        if value not in CATEGORIAS_MANUTENCAO:
            raise serializers.ValidationError("Categoria de manutenção inválida. Use: REFRIGERACAO, ELETRICA ou GERAIS.")

        return value

    def validate_descricao_servico(self, value):
        if not value.strip():
            raise serializers.ValidationError("A descrição é obrigatória.")
        if len(value.strip()) < 10:
            raise serializers.ValidationError("A descrição deve ter pelo menos 10 caracteres.")
        return value

    def create(self, validated_data):
        request = self.context.get('request')

        if request and request.user and request.user.is_authenticated:
            usuario_solicitante = request.user
        else:
            usuario_solicitante = None

        return OrdemServicoFacade().abrir(usuario_solicitante, validated_data)

class AbrirOrdemServicoSerializer(OrdemServicoSerializer):
    MENSAGEM_ATIVO_OBRIGATORIO = "Informe o ativo com problema (id do ativo ou código patrimonial)."

    codigo_patrimonial = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta(OrdemServicoSerializer.Meta):
        extra_kwargs = {
            'localizacao': {'required': False, 'error_messages': {'does_not_exist': "Localização não encontrada."}},
            'ativo': {'error_messages': {'does_not_exist': "Ativo não encontrado."}},
            'descricao_servico': {'error_messages': {'required': "A descrição é obrigatória.", 'blank': "A descrição é obrigatória."}},
        }

    def validate(self, dados):
        erros = {}
        ativo = dados.get('ativo')
        codigo = (dados.pop('codigo_patrimonial', '') or '').strip()

        if codigo:
            ativo_pelo_codigo = Ativo.objects.select_related('localizacao').filter(codigo_patrimonial__iexact=codigo).first()
            if ativo_pelo_codigo is None:
                erros['codigo_patrimonial'] = ["Patrimônio não encontrado."]
            elif ativo is not None and ativo.pk != ativo_pelo_codigo.pk:
                erros['codigo_patrimonial'] = ["O código patrimonial não corresponde ao ativo informado."]
            else:
                ativo = ativo_pelo_codigo

        if ativo is None and not codigo and self.context.get('exige_ativo'):
            erros['ativo'] = [self.MENSAGEM_ATIVO_OBRIGATORIO]

        localizacao = dados.get('localizacao')
        if ativo is not None and 'codigo_patrimonial' not in erros:
            if localizacao is None:
                localizacao = ativo.localizacao
            elif localizacao.pk != ativo.localizacao_id:
                erros['localizacao'] = [f"A localização informada não corresponde à do ativo ({ativo.localizacao.desc_localizacao})."]

        if localizacao is None and 'localizacao' not in erros and 'codigo_patrimonial' not in erros:
            erros['localizacao'] = ["Informe a localização."]

        if erros:
            raise serializers.ValidationError(erros)

        dados['ativo'] = ativo
        dados['localizacao'] = localizacao
        return dados


class AtribuirTecnicoSerializer(serializers.Serializer):
    tecnico = serializers.IntegerField()
