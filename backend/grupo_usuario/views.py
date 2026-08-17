from rest_framework import generics, status
from grupo_usuario.models import GrupoUsuario
from grupo_usuario.serializers import GrupoUsuarioSerializer
from utils.responses import resposta_sucesso, resposta_erro
from rest_framework.permissions import IsAuthenticated
from utils.permissions import IsGerente
# Create your views here.

# Views para o modelo GrupoUsuario
class GrupoUsuarioListCreateView(generics.ListCreateAPIView):
    queryset = GrupoUsuario.objects.all()
    serializer_class = GrupoUsuarioSerializer
    permission_classes = (IsAuthenticated, IsGerente)

    # Sobrescreve o método create para fornecer respostas personalizadas
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            grupo_usuario = serializer.save()
            return resposta_sucesso("Grupo-Usuário cadastrado com sucesso.", GrupoUsuarioSerializer(grupo_usuario).data,  status.HTTP_201_CREATED)

        return resposta_erro("Erro ao cadastrar grupo-usuário.", serializer.errors)

class GrupoUsuarioRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView): # Permite recuperar, atualizar ou deletar um GrupoUsuario específico
    queryset = GrupoUsuario.objects.all()
    serializer_class = GrupoUsuarioSerializer
    permission_classes = [IsAuthenticated, IsGerente]

    # Sobrescreve os métodos para fornecer respostas personalizadas
    def retrieve(self, request, *args, **kwargs):
        grupo_usuario = self.get_object()
        return resposta_sucesso("Grupo-Usuário encontrado com sucesso.", self.get_serializer(grupo_usuario).data)

    # Sobrescreve o método update para fornecer respostas personalizadas
    def update(self, request, *args, **kwargs):
        parcial = kwargs.pop("partial", False)
        grupo_usuario = self.get_object()
        serializer = self.get_serializer(grupo_usuario, data=request.data, partial=parcial)

        if serializer.is_valid():
            grupo_usuario = serializer.save()
            return resposta_sucesso("Grupo-Usuário atualizado com sucesso.", GrupoUsuarioSerializer(grupo_usuario).data)

        return resposta_erro("Erro ao atualizar grupo-usuário.", serializer.errors)
    
    # Sobrescreve o método destroy para fornecer respostas personalizadas
    def destroy(self, request, *args, **kwargs):
        grupo_usuario = self.get_object()
        grupo_usuario.delete()
        return resposta_sucesso("Grupo-Usuário removido com sucesso.", None, status.HTTP_204_NO_CONTENT)