from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated

from ativo.models import Ativo
from ativo.serializers import AtivoSerializer
from utils.responses import resposta_sucesso, resposta_erro
from utils.permissions import IsGerente, IsGestor,IsGerenteOuGestorOuTecnico
from rest_framework.views import APIView
from ordem_servico.models import OrdemServico
from ordem_servico.serializers import OrdemServicoSerializer

# Create your views here.
# As views AtivoListCreateView e AtivoRetrieveUpdateDestroyView são responsáveis por lidar com as operações de listagem, criação, recuperação, atualização e exclusão de ativos. Elas utilizam os serializers para validar e transformar os dados, e as permissões para garantir que apenas usuários autorizados possam realizar certas ações. As respostas são formatadas usando funções de resposta personalizada para manter a consistência na comunicação com o cliente.
class AtivoListCreateView(generics.ListCreateAPIView):
    queryset = Ativo.objects.all().order_by('id_ativo')
    serializer_class = AtivoSerializer

    # O método get_permissions é sobrescrito para retornar diferentes conjuntos de permissões dependendo do método HTTP da requisição. Para requisições POST, que correspondem à criação de um novo ativo, são exigidas as permissões IsAuthenticated e IsGerenteOuGestorOuTecnico, garantindo que apenas usuários autenticados com os papéis de gerente, gestor ou técnico possam criar ativos. Para outros métodos, como GET, apenas a permissão IsAuthenticated é exigida, permitindo que qualquer usuário autenticado possa listar os ativos.
    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAuthenticated(), IsGerenteOuGestorOuTecnico()]

        return [IsAuthenticated()]

    def get_queryset(self):
        queryset = Ativo.objects.all().order_by('id_ativo')

        localizacao = self.request.query_params.get('localizacao')
        tipo_ativo = self.request.query_params.get('tipo_ativo')

        if localizacao:
            queryset = queryset.filter(localizacao_id=localizacao)

        if tipo_ativo:
            queryset = queryset.filter(tipo_ativo=tipo_ativo)

        return queryset

    # Sobrescreve o método list para retornar uma resposta personalizada ao listar os ativos, utilizando a função resposta_sucesso para formatar a resposta de maneira consistente.
    def list(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_queryset(), many=True)

        return resposta_sucesso("Ativos listados com sucesso.", serializer.data)

    # Sobrescreve o método create para criar um novo ativo, utilizando a função resposta_sucesso para formatar a resposta de maneira consistente em caso de sucesso, e resposta_erro em caso de falha na validação dos dados.
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            ativo = serializer.save()

            return resposta_sucesso("Ativo cadastrado com sucesso.", AtivoSerializer(ativo).data, status.HTTP_201_CREATED)

        return resposta_erro("Erro ao cadastrar ativo.", serializer.errors)

# A view AtivoRetrieveUpdateDestroyView é responsável por lidar com as operações de recuperação, atualização e exclusão de um ativo específico, identificado pelo seu ID. Ela utiliza permissões para garantir que apenas usuários autorizados possam realizar atualizações ou exclusões, e formata as respostas utilizando funções de resposta personalizada para manter a consistência na comunicação com o cliente. O método update é sobrescrito para permitir apenas a atualização da periodicidade da manutenção preventiva, garantindo que outras informações do ativo não sejam alteradas inadvertidamente.
class AtivoRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Ativo.objects.all()
    serializer_class = AtivoSerializer

    # O método get_permissions é sobrescrito para retornar diferentes conjuntos de permissões dependendo do método HTTP da requisição. Para requisições PATCH, PUT e DELETE, que correspondem à atualização e exclusão de um ativo, são exigidas as permissões IsAuthenticated e IsGerenteOuGestorOuTecnico, garantindo que apenas usuários autenticados com os papéis de gerente, gestor ou técnico possam atualizar ou excluir ativos. Para outros métodos, como GET, apenas a permissão IsAuthenticated é exigida, permitindo que qualquer usuário autenticado possa recuperar os detalhes de um ativo específico.
    def get_permissions(self):
        if self.request.method in ['PATCH', 'PUT', 'DELETE']:
            return [IsAuthenticated(), IsGerenteOuGestorOuTecnico()]

        return [IsAuthenticated()]

    # Sobrescreve o método retrieve para retornar uma resposta personalizada ao recuperar um ativo específico, utilizando a função resposta_sucesso para formatar a resposta de maneira consistente.
    def retrieve(self, request, *args, **kwargs):
        ativo = self.get_object()
        serializer = self.get_serializer(ativo)

        return resposta_sucesso("Ativo encontrado com sucesso.", serializer.data)

    # Sobrescreve o método update para permitir apenas a atualização da periodicidade da manutenção preventiva, garantindo que outras informações do ativo não sejam alteradas inadvertidamente. Ele verifica os campos recebidos na requisição e, se houver campos que não sejam permitidos, retorna uma resposta de erro. Caso contrário, ele procede com a atualização utilizando o serializer e retorna uma resposta de sucesso ou erro conforme o resultado da validação.
    def update(self, request, *args, **kwargs):
        parcial = kwargs.pop("partial", False)
        ativo = self.get_object()

        serializer = self.get_serializer(ativo, data=request.data, partial=parcial)

        if serializer.is_valid():
            ativo = serializer.save()
            return resposta_sucesso("Ativo atualizado com sucesso.", AtivoSerializer(ativo).data)

        return resposta_erro("Erro ao atualizar ativo.", serializer.errors)

    # Sobrescreve o método destroy para excluir um ativo específico, utilizando a função resposta_sucesso para formatar a resposta de maneira consistente em caso de sucesso.
    def destroy(self, request, *args, **kwargs):
        ativo = self.get_object()
        ativo.delete()

        return resposta_sucesso("Ativo removido com sucesso.", None, status.HTTP_200_OK)
    
class AtivoHistoricoView(APIView):
    """
    Retorna todo o histórico de manutenções (Ordens de Serviço concluídas) 
    vinculadas a um ativo específico.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            # Busca todas as OS's concluídas ou encerradas para o ativo especificado
            historico = OrdemServico.objects.filter(
                ativo_id=pk, 
                status_ordem_servico__in=['CONCLUIDA', 'ENCERRADA']
            ).order_by('-dt_conclusao')
            
            serializer = OrdemServicoSerializer(historico, many=True)
            return resposta_sucesso("Histórico carregado com sucesso.", serializer.data)
            
        except Exception as e:
            return resposta_erro(f"Erro ao buscar histórico: {str(e)}", None)