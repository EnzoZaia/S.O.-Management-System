from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import generics
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from auditoria_usuario.models import AuditoriaUsuario
from auditoria_usuario.serializers import AuditoriaUsuarioSerializer
from perfil import services as perfis
from usuario import services
from usuario.models import STATUS_CONTA_DESATIVADA, Usuario
from usuario.serializers import (
    AlterarSituacaoSerializer,
    ReenviarConfirmacaoSerializer,
    UsuarioMeusDadosSerializer,
    UsuarioSerializer,
)
from perfil.equipes import ids_tecnicos_da_equipe
from utils.permissions import IsGerente, IsGerenteOuGestor, usuario_tem_grupo
from utils.responses import resposta_sucesso, resposta_erro


def _usuarios_com_grupo():
    return Usuario.objects.select_related('perfil_gerente', 'perfil_gestor', 'perfil_tecnico', 'perfil_solicitante')


def _filtro_ativo(valor):
    if valor is None or valor == '':
        return True
    valor = str(valor).strip().lower()
    if valor in ('todos', 'all'):
        return None
    return valor in ('true', '1', 'sim')


class UsuarioListCreateView(generics.ListCreateAPIView):
    serializer_class = UsuarioSerializer
    throttle_scope = 'cadastro_publico'

    def get_permissions(self):
        if self.request.method == 'POST':
            return [AllowAny()]
        return [IsAuthenticated(), IsGerenteOuGestor()]

    def get_throttles(self):
        if self.request.method == 'POST' and not self._pelo_gerente():
            return [ScopedRateThrottle()]
        return []

    def _pelo_gerente(self) -> bool:
        usuario = self.request.user
        return bool(usuario and usuario.is_authenticated and usuario_tem_grupo(usuario, "GERENTE"))

    def get_queryset(self):
        queryset = _usuarios_com_grupo().order_by('nome')
        ativo = _filtro_ativo(self.request.query_params.get('ativo'))
        if ativo is not None:
            queryset = queryset.exclude(status_conta=STATUS_CONTA_DESATIVADA) if ativo else queryset.filter(status_conta=STATUS_CONTA_DESATIVADA)
        if not self._pelo_gerente():
            queryset = queryset.filter(id_usuario__in=ids_tecnicos_da_equipe(self.request.user))
        return queryset

    def get_serializer_context(self):
        contexto = super().get_serializer_context()
        contexto['pelo_gerente'] = self._pelo_gerente()
        return contexto

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        if not serializer.is_valid():
            return resposta_erro("Erro ao cadastrar usuário.", serializer.errors)

        usuario = serializer.save()
        email_enviado = services.enviar_email_confirmacao(usuario, senha_inicial=usuario.senha_temporaria)

        if email_enviado:
            mensagem = "Cadastro realizado. Enviamos um link de confirmação para o seu e-mail."
        else:
            mensagem = "Cadastro realizado, mas não foi possível enviar o e-mail de confirmação agora. Use a opção de reenviar."

        return resposta_sucesso(mensagem, UsuarioSerializer(usuario).data, status.HTTP_201_CREATED)

class UsuarioRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Usuario.objects.all()
    serializer_class = UsuarioSerializer
    permission_classes = (IsAuthenticated, IsGerente)

    http_method_names = ['get', 'delete', 'put', 'patch']

    def get_queryset(self):
        return _usuarios_com_grupo()

    def retrieve(self, request, *args, **kwargs):
        usuario = self.get_object()
        serializer = self.get_serializer(usuario)

        return resposta_sucesso("Usuário encontrado com sucesso.", serializer.data)

    def update(self, request, *args, **kwargs):
        usuario = self.get_object()

        novo_email = request.data.get('email')
        if novo_email:
            novo_email = str(novo_email).strip().lower()
            if Usuario.objects.exclude(id_usuario=usuario.id_usuario).filter(email=novo_email).exists():
                return resposta_erro("Erro ao atualizar usuário.", {"email": ["Já existe um usuário com este e-mail."]})

        id_grupo = request.data.get('grupo')
        novo_perfil = None
        if id_grupo not in (None, ''):
            try:
                novo_perfil = perfis.PERFIL_POR_ID.get(int(id_grupo))
            except (TypeError, ValueError):
                novo_perfil = None
            if novo_perfil is None:
                return resposta_erro("Erro ao atualizar usuário.", {"grupo": ["Grupo informado não existe."]})

        try:
            with transaction.atomic():
                usuario.nome = request.data.get('nome', usuario.nome)
                usuario.email = novo_email or usuario.email

                nova_senha = request.data.get('senha')
                if nova_senha:
                    usuario.senha_hash = make_password(nova_senha)

                usuario.save()

                if novo_perfil is not None:
                    services.alterar_perfil(usuario, novo_perfil, request.user)
        except services.RegraUsuarioError as erro:
            return resposta_erro(erro.mensagem, erro.erros, erro.status_code)

        usuario = _usuarios_com_grupo().get(pk=usuario.pk)
        return resposta_sucesso("Usuário atualizado com sucesso.", UsuarioSerializer(usuario).data)

    def destroy(self, request, *args, **kwargs):
        usuario = self.get_object()

        try:
            services.alterar_situacao(usuario, False, request.user)
        except services.RegraUsuarioError as erro:
            return resposta_erro(erro.mensagem, erro.erros, erro.status_code)

        return resposta_sucesso("Usuário desativado com sucesso.", None, status.HTTP_200_OK)


class UsuarioSituacaoView(APIView):
    permission_classes = (IsAuthenticated, IsGerente)

    def patch(self, request, pk):
        usuario = get_object_or_404(Usuario, pk=pk)

        serializer = AlterarSituacaoSerializer(data=request.data)
        if not serializer.is_valid():
            return resposta_erro("Erro ao alterar a situação do usuário.", serializer.errors)

        ativo = serializer.validated_data['ativo']

        try:
            alterado = services.alterar_situacao(usuario, ativo, request.user)
        except services.RegraUsuarioError as erro:
            return resposta_erro(erro.mensagem, erro.erros, erro.status_code)

        if not alterado:
            mensagem = "O usuário já estava nesta situação."
        else:
            mensagem = "Usuário ativado com sucesso." if ativo else "Usuário desativado com sucesso."

        usuario = _usuarios_com_grupo().get(pk=usuario.pk)
        return resposta_sucesso(mensagem, UsuarioSerializer(usuario).data)


class UsuarioAuditoriaView(APIView):
    permission_classes = (IsAuthenticated, IsGerente)

    def get(self, request, pk):
        usuario = get_object_or_404(Usuario, pk=pk)
        registros = (
            AuditoriaUsuario.objects.filter(usuario_alvo=usuario)
            .select_related('autor', 'usuario_alvo')
            .order_by('-dt_registro', '-id_auditoria')
        )
        return resposta_sucesso("Auditoria carregada com sucesso.", AuditoriaUsuarioSerializer(registros, many=True).data)


class UsuarioMeusDadosView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        serializer = UsuarioSerializer(request.user)

        return resposta_sucesso("Dados do usuário encontrados com sucesso.", serializer.data)

    def patch(self, request):
        serializer = UsuarioMeusDadosSerializer(request.user, data=request.data, partial=True)

        if serializer.is_valid():
            usuario = serializer.save()

            return resposta_sucesso("Dados atualizados com sucesso.", UsuarioMeusDadosSerializer(usuario).data)

        return resposta_erro("Erro ao atualizar seus dados.", serializer.errors)


class ConfirmarEmailView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request, token):
        try:
            usuario = services.confirmar_email(token)
        except services.RegraUsuarioError as erro:
            return resposta_erro(erro.mensagem, None, erro.status_code)

        return resposta_sucesso("E-mail confirmado com sucesso. Agora você já pode acessar o sistema.", {"ra": usuario.ra})


class ReenviarConfirmacaoView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_scope = 'reenvio_confirmacao'

    throttle_classes = [ScopedRateThrottle]

    def post(self, request):
        serializer = ReenviarConfirmacaoSerializer(data=request.data)
        if not serializer.is_valid():
            return resposta_erro("Informe um e-mail válido.", serializer.errors)

        services.reenviar_confirmacao(serializer.validated_data['email'])

        return resposta_sucesso(
            "Se houver um cadastro pendente para este e-mail, enviamos um novo link de confirmação "
            f"(válido por {settings.HORAS_VALIDADE_TOKEN_CONFIRMACAO} horas).",
            None,
        )
