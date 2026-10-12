from rest_framework.permissions import BasePermission

def usuario_tem_grupo(usuario, nome_grupo):
    from perfil.services import usuario_tem_perfil

    return usuario_tem_perfil(usuario, nome_grupo)


def usuario_participa_da_os(usuario, ordem_servico):
    if not usuario or not getattr(usuario, 'is_authenticated', False):
        return False

    if ordem_servico.solicitante_id == usuario.pk:
        return True

    from os_participante.models import OsParticipante

    return OsParticipante.objects.filter(ordem_servico=ordem_servico, usuario=usuario).exists()

class IsGerente(BasePermission):
    message = "Somente o gerente pode realizar esta ação."

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


class IsGerenteOuGestor(BasePermission):
    message = "Somente gestor ou gerente podem realizar esta ação."

    def has_permission(self, request, view):
        return request.user and (usuario_tem_grupo(request.user, "GERENTE") or usuario_tem_grupo(request.user, "GESTOR"))


class IsSolicitanteOuParticipanteDaOS(BasePermission):
    message = "Somente o solicitante ou um participante vinculado pode realizar esta ação nesta ordem."

    def has_object_permission(self, request, view, obj):
        return usuario_participa_da_os(request.user, obj)
