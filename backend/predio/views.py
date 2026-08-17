from rest_framework import generics, status
from predio.models import Predio
from predio.serializers import PredioSerializer
from utils.responses import resposta_sucesso, resposta_erro
from rest_framework.permissions import IsAuthenticated, AllowAny

# Create your views here.

# View para listar e criar prédios.
class PredioListCreateView(generics.ListCreateAPIView):
    queryset = Predio.objects.all().order_by('nome_predio') # Adicionado order_by para vir em ordem alfabética no select
    serializer_class = PredioSerializer
    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()] # Libera a listagem para o totem público
        return [IsAuthenticated()] # Trava a criação de novos prédios

    # Sobrescreve o método list para envelopar a listagem no padrão de resposta do projeto
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return resposta_sucesso("Prédios listados com sucesso.", serializer.data)

    # Sobrescreve o método create para fornecer uma resposta personalizada ao criar um prédio
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            predio = serializer.save()
            return resposta_sucesso("Prédio cadastrado com sucesso.", PredioSerializer(predio).data, status.HTTP_201_CREATED)

        return resposta_erro("Erro ao cadastrar prédio.", serializer.errors)

# View para recuperar, atualizar e deletar um prédio específico.
class PredioRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Predio.objects.all()
    serializer_class = PredioSerializer
    #permission_classes = (IsAuthenticated,)

    # Sobrescreve o método retrieve para fornecer uma resposta personalizada ao recuperar um prédio
    def retrieve(self, request, *args, **kwargs):
        predio = self.get_object()
        return resposta_sucesso("Prédio encontrado com sucesso.", self.get_serializer(predio).data)

    # Sobrescreve o método update para fornecer uma resposta personalizada ao atualizar um prédio
    def update(self, request, *args, **kwargs):
        parcial = kwargs.pop("partial", False)
        predio = self.get_object()
        serializer = self.get_serializer(predio, data=request.data, partial=parcial)

        if serializer.is_valid():
            predio = serializer.save()
            return resposta_sucesso("Prédio atualizado com sucesso.", PredioSerializer(predio).data)

        return resposta_erro("Erro ao atualizar prédio.", serializer.errors)

    # Sobrescreve o método destroy para fornecer uma resposta personalizada ao deletar um prédio
    def destroy(self, request, *args, **kwargs):
        predio = self.get_object()
        predio.delete()
        return resposta_sucesso("Prédio removido com sucesso.", None, status.HTTP_204_NO_CONTENT)