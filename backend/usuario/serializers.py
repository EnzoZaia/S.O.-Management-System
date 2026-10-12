from rest_framework import serializers
from django.contrib.auth.hashers import make_password
from django.db import transaction

from django.conf import settings

from perfil import services as perfis
from usuario.models import STATUS_CONTA_PENDENTE, Usuario
from usuario.services import novo_token_confirmacao

SENHA_TAMANHO_MINIMO = 8


class UsuarioSerializer(serializers.ModelSerializer):
    senha = serializers.CharField(write_only=True, error_messages={'required': "A senha é obrigatória.", 'blank': "A senha é obrigatória."})
    grupo = serializers.IntegerField(write_only=True, required=False)
    grupo_descricao = serializers.SerializerMethodField(read_only=True)
    id_grupo = serializers.SerializerMethodField(read_only=True)
    grupos = serializers.SerializerMethodField(read_only=True)
    ra = serializers.CharField(read_only=True, default=None)
    ativo = serializers.BooleanField(read_only=True)

    class Meta:
        model = Usuario
        fields = ['id_usuario', 'nome', 'email', 'senha', 'grupo', 'id_grupo', 'grupo_descricao', 'grupos', 'ra', 'ativo', 'status_conta', 'email_confirmado']
        read_only_fields = ['id_usuario', 'grupo_descricao', 'id_grupo', 'grupos', 'ra', 'ativo', 'status_conta', 'email_confirmado']
        extra_kwargs = {
            'nome': {'error_messages': {'required': "O nome é obrigatório.", 'blank': "O nome é obrigatório."}},
            'email': {'validators': [], 'error_messages': {'required': "O e-mail é obrigatório.", 'blank': "O e-mail é obrigatório."}},
        }

    @property
    def _pelo_gerente(self) -> bool:
        return bool(self.context.get('pelo_gerente'))

    def get_grupo_descricao(self, obj):
        return perfis.perfil_principal(obj)

    def get_id_grupo(self, obj):
        return perfis.ID_POR_PERFIL.get(perfis.perfil_principal(obj))

    def get_grupos(self, obj):
        return perfis.perfis_do_usuario(obj)

    def validate_nome(self, value):
        if not value.strip():
            raise serializers.ValidationError("O nome é obrigatório.")
        return value.strip()

    def validate_senha(self, value):
        if len(value) < SENHA_TAMANHO_MINIMO:
            raise serializers.ValidationError(f"A senha deve ter pelo menos {SENHA_TAMANHO_MINIMO} caracteres.")
        return value

    def validate_email(self, value):
        email = value.strip().lower()

        if not email.endswith(settings.DOMINIOS_EMAIL_PERMITIDOS):
            raise serializers.ValidationError(f"O e-mail deve terminar com um dos domínios permitidos: {', '.join(settings.DOMINIOS_EMAIL_PERMITIDOS)}.")
        usuario_existente = Usuario.objects.filter(email=email).first()

        if usuario_existente is None:
            return email

        if usuario_existente.email_confirmado:
            raise serializers.ValidationError("Já existe um usuário cadastrado com este e-mail.")

        if not self._pelo_gerente:
            raise serializers.ValidationError("Já existe um cadastro pendente para este e-mail. Use a opção de reenviar o e-mail de confirmação.")

        return email

    def validate(self, dados):
        if self._pelo_gerente:
            id_grupo = dados.get('grupo')
            if id_grupo is None:
                raise serializers.ValidationError({'grupo': ["Informe o cargo (grupo) do usuário."]})
            if id_grupo not in perfis.PERFIL_POR_ID:
                raise serializers.ValidationError({'grupo': ["Grupo informado não existe."]})
        else:
            dados.pop('grupo', None)
        return dados

    @transaction.atomic
    def create(self, validated_data):
        senha = validated_data.pop('senha')
        id_grupo = validated_data.pop('grupo', None)

        email = validated_data['email']
        usuario = Usuario.objects.filter(email=email, email_confirmado=False).first() if self._pelo_gerente else None

        if usuario is None:
            usuario = Usuario(email=email, email_confirmado=False, status_conta=STATUS_CONTA_PENDENTE)

        usuario.nome = validated_data['nome']
        usuario.senha_hash = make_password(senha)
        novo_token_confirmacao(usuario)
        usuario.save()

        if self._pelo_gerente:
            perfis.definir_perfil(usuario, perfis.PERFIL_POR_ID[id_grupo])

        usuario.senha_temporaria = senha if self._pelo_gerente else None
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


class AlterarSituacaoSerializer(serializers.Serializer):
    ativo = serializers.BooleanField()

    def validate(self, dados):
        if 'ativo' not in self.initial_data:
            raise serializers.ValidationError({'ativo': ["Informe a situação (true para ativo, false para inativo)."]})
        return dados


class ReenviarConfirmacaoSerializer(serializers.Serializer):
    email = serializers.EmailField(error_messages={'required': "O e-mail é obrigatório.", 'blank': "O e-mail é obrigatório.", 'invalid': "Informe um e-mail válido."})
