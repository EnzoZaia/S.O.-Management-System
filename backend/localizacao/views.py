from rest_framework import generics, status
from localizacao.models import Localizacao
from localizacao.serializers import LocalizacaoSerializer
from utils.responses import resposta_sucesso, resposta_erro
from rest_framework.permissions import IsAuthenticated, AllowAny
from utils.permissions import IsGerente

class LocalizacaoListCreateView(generics.ListCreateAPIView):
    queryset = Localizacao.objects.all()
    serializer_class = LocalizacaoSerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAuthenticated(), IsGerente()]
        return [AllowAny()]

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return resposta_sucesso("Localizações listadas com sucesso.", serializer.data)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            localizacao = serializer.save()
            return resposta_sucesso("Localização cadastrada com sucesso.", LocalizacaoSerializer(localizacao).data, status.HTTP_201_CREATED)

        return resposta_erro("Erro ao cadastrar localização.", serializer.errors)

class LocalizacaoRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Localizacao.objects.all()
    serializer_class = LocalizacaoSerializer

    def retrieve(self, request, *args, **kwargs):
        localizacao = self.get_object()
        return resposta_sucesso("Localização encontrada com sucesso.", self.get_serializer(localizacao).data)

    def update(self, request, *args, **kwargs):
        parcial = kwargs.pop("partial", False)
        localizacao = self.get_object()
        serializer = self.get_serializer(localizacao, data=request.data, partial=parcial)

        if serializer.is_valid():
            localizacao = serializer.save()
            return resposta_sucesso("Localização atualizada com sucesso.", LocalizacaoSerializer(localizacao).data)

        return resposta_erro("Erro ao atualizar localização.", serializer.errors)

    def destroy(self, request, *args, **kwargs):
        localizacao = self.get_object()
        localizacao.delete()
        return resposta_sucesso("Localização removida com sucesso.", None, status.HTTP_204_NO_CONTENT)
