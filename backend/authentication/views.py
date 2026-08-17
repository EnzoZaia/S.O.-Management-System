from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.hashers import check_password

# Importações para garantir o funcionamento com o Axios
from rest_framework.permissions import AllowAny 
from rest_framework.parsers import JSONParser

from usuario.models import Usuario
from grupo_usuario.models import GrupoUsuario

class TokenObtainPairView(APIView):
    # Libera o acesso e garante a leitura do JSON vindo do Vue
    permission_classes = [AllowAny]
    authentication_classes = [] # Adicionei ass Zaia
    parser_classes = [JSONParser]

    def post(self, request):
        print(f"DADOS RECEBIDOS PELO DJANGO: {request.data}")

        email = request.data.get('email')
        
        # Tenta pegar 'senha'. Se não encontrar (por causa do cache do Vue), pega 'password'
        senha = request.data.get('senha') or request.data.get('password')

        # Validando se email e senha foram fornecidos
        if not email or not senha:
            return Response({'erro': 'E-mail e senha são obrigatórios.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            usuario = Usuario.objects.get(email=email)
        except Usuario.DoesNotExist:
            return Response({'erro': 'Credenciais inválidas.'}, status=status.HTTP_401_UNAUTHORIZED)
        
        if not usuario.email_confirmado:
            return Response({'erro': 'E-mail ainda não confirmado. Verifique sua caixa de entrada.'}, status=status.HTTP_403_FORBIDDEN)

        # Verificando a senha (usando o campo senha_hash do seu modelo)
        if not check_password(senha, usuario.senha_hash):
            return Response({'erro': 'Credenciais inválidas.'}, status=status.HTTP_401_UNAUTHORIZED)

        # Buscando os grupos do utilizador
        vinculos = GrupoUsuario.objects.filter(usuario=usuario).select_related('grupo')

        grupos_usuario = [vinculo.grupo.desc_grupo for vinculo in vinculos]

        # Gerando os tokens (Refresh e Access)
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

        # Resposta final para o Vue
        return Response({'refresh': str(refresh), 'access': str(access), 'usuario': {'id_usuario': usuario.id_usuario, 'nome': usuario.nome, 'email': usuario.email, 'grupos': grupos_usuario}})