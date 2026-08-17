from rest_framework.permissions import BasePermission
from grupo_usuario.models import GrupoUsuario

def usuario_tem_grupo(usuario, nome_grupo):
    if not usuario:
        return False

    return GrupoUsuario.objects.filter(usuario=usuario, grupo__desc_grupo=nome_grupo).exists()

class IsGerente(BasePermission):
    def has_permission(self, request, view):
        return request.user and usuario_tem_grupo(request.user, "GERENTE")


class IsGestor(BasePermission):
    def has_permission(self, request, view):
        return request.user and usuario_tem_grupo(request.user, "GESTOR")


class IsTecnico(BasePermission):
    def has_permission(self, request, view):
        return request.user and usuario_tem_grupo(request.user, "TECNICO")


class IsSolicitante(BasePermission):
    def has_permission(self, request, view):
        return request.user and usuario_tem_grupo(request.user, "SOLICITANTE")
    
class IsGerenteOuGestorOuTecnico(BasePermission):
    def has_permission(self, request, view):
        return (request.user and (usuario_tem_grupo(request.user, "GERENTE") or usuario_tem_grupo(request.user, "GESTOR") or usuario_tem_grupo(request.user, "TECNICO")))