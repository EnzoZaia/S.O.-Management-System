from rest_framework import serializers
from ativo.models import Ativo
from ativo.services import intervalo_preventiva_dias, recalcular_programacao

class AtivoSerializer(serializers.ModelSerializer):
    periodicidade_preventiva_dias = serializers.IntegerField(min_value=1, required=False)

    class Meta:
        model = Ativo
        fields = '__all__'
        read_only_fields = ['id_ativo', 'dt_proxima_preventiva']

    def create(self, validated_data):
        if not validated_data.get('periodicidade_preventiva_dias'):
            localizacao = validated_data.get('localizacao')
            validated_data['periodicidade_preventiva_dias'] = intervalo_preventiva_dias(
                validated_data.get('tipo_ativo'), localizacao.predio_id if localizacao else None,
            )

        ativo = Ativo(**validated_data)
        recalcular_programacao(ativo)
        ativo.save()
        return ativo

    def update(self, instance, validated_data):
        for campo, valor in validated_data.items():
            setattr(instance, campo, valor)

        if 'periodicidade_preventiva_dias' in validated_data or 'dt_ultima_preventiva' in validated_data or not instance.dt_proxima_preventiva:
            recalcular_programacao(instance)

        instance.save()
        return instance
