from rest_framework import serializers
from django.contrib.auth.hashers import make_password
from django.db import transaction

import uuid
from datetime import timedelta
from django.utils import timezone
from django.conf import settings

from usuario.models import Usuario
from grupo.models import Grupo
from grupo_usuario.models import GrupoUsuario

class UsuarioSerializer(serializers.ModelSerializer):
    senha = serializers.CharField(write_only=True)
    grupo = serializers.IntegerField(write_only=True)
    grupo_descricao = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Usuario
        fields = ['id_usuario', 'nome', 'email', 'senha', 'grupo', 'grupo_descricao']
        read_only_fields = ['id_usuario', 'grupo_descricao']

    def get_grupo_descricao(self, obj):
        vinculo = GrupoUsuario.objects.filter(usuario=obj).select_related('grupo').first()
        if vinculo:
            return vinculo.grupo.desc_grupo
        return None

    def validate_nome(self, value):
        if not value.strip():
            raise serializers.ValidationError("O nome é obrigatório.")
        return value

    def validate_email(self, value):
        email = value.strip().lower()

        if not email.endswith(settings.DOMINIOS_EMAIL_PERMITIDOS):
            raise serializers.ValidationError(f"O e-mail deve terminar com um dos domínios permitidos: {', '.join(settings.DOMINIOS_EMAIL_PERMITIDOS)}.")
        usuario_existente = Usuario.objects.filter(email=email).first()

        if usuario_existente and usuario_existente.email_confirmado:
            raise serializers.ValidationError("Já existe um usuário ativo com este e-mail.")

        return email

    @transaction.atomic
    def create(self, validated_data):
        senha = validated_data.pop('senha')
        id_grupo = validated_data.pop('grupo')

        grupo = Grupo.objects.get(id_grupo=id_grupo)
        email = validated_data['email']
        token = str(uuid.uuid4())

        usuario_existente = Usuario.objects.filter(email=email).first()

        if usuario_existente and not usuario_existente.email_confirmado:
            usuario = usuario_existente
        else:
            usuario = None

        if usuario:
            usuario.nome = validated_data['nome']
            usuario.senha_hash = make_password(senha)
            usuario.token_confirmacao_email = token
            usuario.dt_expiracao_token = timezone.now() + timedelta(hours=24)
            usuario.save()

            GrupoUsuario.objects.update_or_create(
                usuario=usuario,
                defaults={'grupo': grupo}
            )

        else:
            usuario = Usuario.objects.create(
            nome=validated_data['nome'],
            email=email,
            senha_hash=make_password(senha),
            email_confirmado=False,
            token_confirmacao_email=token,
            dt_expiracao_token=timezone.now() + timedelta(hours=24)
        )

        GrupoUsuario.objects.create(usuario=usuario, grupo=grupo)

        usuario.senha_temporaria = senha
        return usuario

class UsuarioMeusDadosSerializer(serializers.ModelSerializer):
    senha = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = Usuario
        fields = ['id_usuario', 'nome', 'email', 'senha']
        read_only_fields = ['id_usuario']

    def validate_nome(self, value):
        if not value.strip():
            raise serializers.ValidationError("O nome é obrigatório.")
        return value

    def validate_email(self, value):
        email = value.strip().lower()
        usuario_logado = self.instance

        if not email.endswith(settings.DOMINIOS_EMAIL_PERMITIDOS):
            raise serializers.ValidationError(f"O e-mail deve terminar com um dos domínios permitidos: {', '.join(settings.DOMINIOS_EMAIL_PERMITIDOS)}.")

        if Usuario.objects.exclude(id_usuario=usuario_logado.id_usuario).filter(email=email).exists():
            raise serializers.ValidationError("Já existe um usuário com este e-mail.")

        return email

    def update(self, instance, validated_data):
        senha = validated_data.pop('senha', None)

        instance.nome = validated_data.get('nome', instance.nome)
        instance.email = validated_data.get('email', instance.email)

        if senha:
            instance.senha_hash = make_password(senha)

        instance.save()
        return instance
