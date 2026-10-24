from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken
from rest_framework.exceptions import AuthenticationFailed
from usuario.models import Usuario

class CustomJWTAuthentication(JWTAuthentication):

    def get_user(self, validated_token):
        try:
            user_id = validated_token.get('id_usuario')
            if user_id is None:
                raise InvalidToken('Token sem id_usuario')
            usuario = Usuario.objects.get(id_usuario=user_id)
        except Usuario.DoesNotExist:
            raise AuthenticationFailed('Usuário não encontrado')

        if not usuario.ativo:
            raise AuthenticationFailed('Usuário desativado. Procure o gerente do sistema.', code='usuario_inativo')

        return usuario


class OptionalJWTAuthentication(CustomJWTAuthentication):
    """Para endpoints públicos: token inválido/expirado vira requisição anônima em vez de 401."""

    def authenticate(self, request):
        try:
            return super().authenticate(request)
        except (InvalidToken, AuthenticationFailed):
            return None
