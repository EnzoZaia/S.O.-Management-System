from rest_framework import generics, status
from grupo.models import Grupo
from grupo.serializers import GrupoSerializer
from utils.responses import resposta_sucesso, resposta_erro
from rest_framework.permissions import IsAuthenticated
from utils.permissions import IsGerente

class GrupoListCreateView(generics.ListCreateAPIView):
    queryset = Grupo.objects.all()
    serializer_class = GrupoSerializer
    permission_classes = (IsAuthenticated, IsGerente)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            grupo = serializer.save()
            return resposta_sucesso("Grupo cadastrado com sucesso.", GrupoSerializer(grupo).data, status.HTTP_201_CREATED)

        return resposta_erro("Erro ao cadastrar grupo.", serializer.errors)

class GrupoRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Grupo.objects.all()
    serializer_class = GrupoSerializer
    permission_classes = (IsAuthenticated, IsGerente)

    def retrieve(self, request, *args, **kwargs):
        grupo = self.get_object()
        return resposta_sucesso("Grupo encontrado com sucesso.", self.get_serializer(grupo).data)

    def update(self, request, *args, **kwargs):
        parcial = kwargs.pop("partial", False)
        grupo = self.get_object()
        serializer = self.get_serializer(grupo, data=request.data, partial=parcial)

        if serializer.is_valid():
            grupo = serializer.save()
            return resposta_sucesso("Grupo atualizado com sucesso.", GrupoSerializer(grupo).data)

        return resposta_erro("Erro ao atualizar grupo.", serializer.errors)

    def destroy(self, request, *args, **kwargs):
        grupo = self.get_object()
        grupo.delete()
        return resposta_sucesso("Grupo removido com sucesso.", None, status.HTTP_204_NO_CONTENT)
