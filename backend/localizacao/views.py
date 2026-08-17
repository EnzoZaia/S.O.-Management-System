from rest_framework import generics, status
from localizacao.models import Localizacao
from localizacao.serializers import LocalizacaoSerializer
from utils.responses import resposta_sucesso, resposta_erro
from rest_framework.permissions import IsAuthenticated, AllowAny
from utils.permissions import IsGerente
# Create your views here.

# Views para a tabela localizacao, utilizando as permissões e regras de negócio definidas para cada tipo de usuário (apenas gerentes podem acessar os endpoints de localização).
class LocalizacaoListCreateView(generics.ListCreateAPIView):
    queryset = Localizacao.objects.all()
    serializer_class = LocalizacaoSerializer

    # Gerencia dinamicamente: GET (listar) é público, POST (criar) exige Gerente logado
    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAuthenticated(), IsGerente()]
        return [AllowAny()]

    # Sobrescreve o método list para envelopar no padrão de resposta do projeto (usando .dados ou .data)
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        # Se o seu front-end espera a chave 'dados', usamos ela aqui
        return resposta_sucesso("Localizações listadas com sucesso.", serializer.data)

    # Sobrescreve o método create para criar uma nova localização (apenas gerentes)
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            localizacao = serializer.save()
            return resposta_sucesso("Localização cadastrada com sucesso.", LocalizacaoSerializer(localizacao).data, status.HTTP_201_CREATED)

        return resposta_erro("Erro ao cadastrar localização.", serializer.errors)

# View para recuperar, atualizar e deletar uma localização específica, aplicando as regras de acesso e as validações necessárias para cada tipo de usuário (apenas gerentes podem acessar este endpoint). O método update também realiza as validações necessárias para os campos da localização.
class LocalizacaoRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Localizacao.objects.all()
    serializer_class = LocalizacaoSerializer
    #permission_classes = (IsAuthenticated, IsGerente)

    # Sobrescreve o método retrieve para recuperar uma localização específica, aplicando as regras de acesso definidas para cada grupo (apenas gerentes podem acessar este endpoint). O método retorna uma resposta de sucesso com os dados da localização encontrada.
    def retrieve(self, request, *args, **kwargs):
        localizacao = self.get_object()
        return resposta_sucesso("Localização encontrada com sucesso.", self.get_serializer(localizacao).data)

    # Sobrescreve o método update para atualizar uma localização específica, aplicando as regras de acesso definidas para cada grupo (apenas gerentes podem acessar este endpoint). O método também realiza as validações necessárias para os campos da localização e retorna uma resposta de sucesso com os dados da localização atualizada.
    def update(self, request, *args, **kwargs):
        parcial = kwargs.pop("partial", False)
        localizacao = self.get_object()
        serializer = self.get_serializer(localizacao, data=request.data, partial=parcial)

        if serializer.is_valid():
            localizacao = serializer.save()
            return resposta_sucesso("Localização atualizada com sucesso.", LocalizacaoSerializer(localizacao).data)

        return resposta_erro("Erro ao atualizar localização.", serializer.errors)

    # Sobrescreve o método destroy para deletar uma localização específica, aplicando as regras de acesso definidas para cada grupo (apenas gerentes podem acessar este endpoint). O método retorna uma resposta de sucesso indicando que a localização foi removida com sucesso.
    def destroy(self, request, *args, **kwargs):
        localizacao = self.get_object()
        localizacao.delete()
        return resposta_sucesso("Localização removida com sucesso.", None, status.HTTP_204_NO_CONTENT)