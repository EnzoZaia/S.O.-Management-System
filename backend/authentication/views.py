from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.hashers import check_password

from rest_framework.permissions import AllowAny 
from rest_framework.parsers import JSONParser

from usuario.models import Usuario
from perfil.services import perfis_do_usuario

class TokenObtainPairView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    parser_classes = [JSONParser]

    def post(self, request):
        email = (request.data.get('email') or '').strip().lower()

        senha = request.data.get('senha') or request.data.get('password')

        if not email or not senha:
            return Response({'erro': 'E-mail e senha são obrigatórios.'}, status=status.HTTP_400_BAD_REQUEST)

        usuario = Usuario.objects.filter(email__iexact=email).first()
        if usuario is None:
            return Response({'erro': 'Credenciais inválidas.'}, status=status.HTTP_401_UNAUTHORIZED)

        if not check_password(senha, usuario.senha_hash):
            return Response({'erro': 'Credenciais inválidas.'}, status=status.HTTP_401_UNAUTHORIZED)

        if not usuario.ativo:
            return Response({'erro': 'Usuário desativado. Procure o gerente do sistema.'}, status=status.HTTP_403_FORBIDDEN)

        if not usuario.email_confirmado:
            return Response({'erro': 'E-mail ainda não confirmado. Verifique sua caixa de entrada.'}, status=status.HTTP_403_FORBIDDEN)

        grupos_usuario = perfis_do_usuario(usuario)

        refresh = RefreshToken()
        refresh['id_usuario'] = usuario.id_usuario
        refresh['nome'] = usuario.nome
        refresh['email'] = usuario.email
        refresh['grupos'] = grupos_usuario

        access = refresh.access_token
        access['id_usuario'] = usuario.id_usuario
        access['nome'] = usuario.nome
        access['email'] = usuario.email
        access['grupos'] = grupos_usuario

        return Response({'refresh': str(refresh), 'access': str(access), 'usuario': {'id_usuario': usuario.id_usuario, 'nome': usuario.nome, 'email': usuario.email, 'ra': usuario.ra, 'grupos': grupos_usuario}})


class TokenRefreshView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    parser_classes = [JSONParser]

    def post(self, request):
        token_refresh = request.data.get('refresh')
        if not token_refresh:
            return Response({'erro': 'O refresh token é obrigatório.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            refresh = RefreshToken(token_refresh)
        except TokenError:
            return Response({'erro': 'Token inválido ou expirado.'}, status=status.HTTP_401_UNAUTHORIZED)

        usuario = Usuario.objects.filter(id_usuario=refresh.get('id_usuario')).first()
        if usuario is None:
            return Response({'erro': 'Token inválido ou expirado.'}, status=status.HTTP_401_UNAUTHORIZED)

        if not usuario.ativo:
            return Response({'erro': 'Usuário desativado. Procure o gerente do sistema.'}, status=status.HTTP_403_FORBIDDEN)

        access = refresh.access_token
        for claim in ('id_usuario', 'nome', 'email', 'grupos'):
            if claim in refresh:
                access[claim] = refresh[claim]

        return Response({'access': str(access)})
