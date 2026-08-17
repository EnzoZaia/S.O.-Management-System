from rest_framework import serializers
from ativo.models import Ativo
from ativo.services import calcular_proxima_preventiva, criar_ou_atualizar_os_preventiva_para_ativo

class AtivoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ativo
        fields = '__all__'
        read_only_fields = ['id_ativo', 'dt_proxima_preventiva']
    
    # Sobrescreve o método create para calcular a data da próxima manutenção preventiva com base na data da última manutenção e na periodicidade, garantindo que a data calculada seja um dia útil.
    def create(self, validated_data):
        dt_ultima = validated_data.get('dt_ultima_preventiva')
        periodicidade = validated_data.get('periodicidade_preventiva_dias')

        if dt_ultima and periodicidade:
            validated_data['dt_proxima_preventiva'] = calcular_proxima_preventiva(
                dt_ultima,
                periodicidade,
                validated_data.get('localizacao')
            )

        ativo = super().create(validated_data)

        if ativo.dt_proxima_preventiva:
            criar_ou_atualizar_os_preventiva_para_ativo(ativo)

        return ativo
    
    # Sobrescreve o método update para atualizar as informações do ativo, incluindo a data da próxima manutenção preventiva, garantindo que a data calculada seja um dia útil.
    def update(self, instance, validated_data):
        instance.periodicidade_preventiva_dias = validated_data.get(
            'periodicidade_preventiva_dias',
            instance.periodicidade_preventiva_dias
        )

        instance.dt_ultima_preventiva = validated_data.get(
            'dt_ultima_preventiva',
            instance.dt_ultima_preventiva
        )

        if instance.dt_ultima_preventiva and instance.periodicidade_preventiva_dias:
            instance.dt_proxima_preventiva = calcular_proxima_preventiva(
                instance.dt_ultima_preventiva,
                instance.periodicidade_preventiva_dias,
                instance.localizacao,
                instance
            )

        instance.save()

        if instance.dt_proxima_preventiva:
            criar_ou_atualizar_os_preventiva_para_ativo(instance)

        return instance