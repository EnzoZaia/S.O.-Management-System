from rest_framework import generics, status
from grupo_usuario.models import GrupoUsuario
from grupo_usuario.serializers import GrupoUsuarioSerializer
from utils.responses import resposta_sucesso, resposta_erro
from rest_framework.permissions import IsAuthenticated
from utils.permissions import IsGerente

class GrupoUsuarioListCreateView(generics.ListCreateAPIView):
    queryset = GrupoUsuario.objects.all()
    serializer_class = GrupoUsuarioSerializer
    permission_classes = (IsAuthenticated, IsGerente)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            grupo_usuario = serializer.save()
            return resposta_sucesso("Grupo-Usuário cadastrado com sucesso.", GrupoUsuarioSerializer(grupo_usuario).data,  status.HTTP_201_CREATED)

        return resposta_erro("Erro ao cadastrar grupo-usuário.", serializer.errors)

class GrupoUsuarioRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = GrupoUsuario.objects.all()
    serializer_class = GrupoUsuarioSerializer
    permission_classes = [IsAuthenticated, IsGerente]

    def retrieve(self, request, *args, **kwargs):
        grupo_usuario = self.get_object()
        return resposta_sucesso("Grupo-Usuário encontrado com sucesso.", self.get_serializer(grupo_usuario).data)

    def update(self, request, *args, **kwargs):
        parcial = kwargs.pop("partial", False)
        grupo_usuario = self.get_object()
        serializer = self.get_serializer(grupo_usuario, data=request.data, partial=parcial)

        if serializer.is_valid():
            grupo_usuario = serializer.save()
            return resposta_sucesso("Grupo-Usuário atualizado com sucesso.", GrupoUsuarioSerializer(grupo_usuario).data)

        return resposta_erro("Erro ao atualizar grupo-usuário.", serializer.errors)

    def destroy(self, request, *args, **kwargs):
        grupo_usuario = self.get_object()
        grupo_usuario.delete()
        return resposta_sucesso("Grupo-Usuário removido com sucesso.", None, status.HTTP_204_NO_CONTENT)
