from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

from ordem_servico.acesso import resolver_fabrica_acesso
from ordem_servico.fachada import OrdemServicoFacade, OperacaoOrdemServicoError
from ordem_servico.models import OrdemServico
from ordem_servico.serializers import OrdemServicoSerializer, AtribuirTecnicoSerializer
from usuario.models import Usuario
from utils.responses import resposta_sucesso, resposta_erro
from utils.permissions import usuario_tem_grupo
from utils.permissions import IsGerenteOuGestorOuTecnico

class OrdemServicoListCreateView(generics.ListCreateAPIView):
    serializer_class = OrdemServicoSerializer

    # Remove IsAuthenticated fixo e define a regra por método
    def get_permissions(self):
        if self.request.method == 'POST':
            return [AllowAny(),]
        return [IsAuthenticated()]

    #permission_classes = (IsAuthenticated,)

    # Delega ao Abstract Factory de acesso: a mesma fábrica resolve o escopo de
    # listagem e a regra de dashboard do perfil, então os dois nunca divergem.
    def get_queryset(self):
        fabrica = resolver_fabrica_acesso(self.request.user)
        return fabrica.criar_escopo_consulta().filtrar(self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={'request': request})

        if serializer.is_valid():
            # Totem (AllowAny) chega sem usuário autenticado: a fachada trata o fallback do histórico.
            usuario_autenticado = request.user if request.user and request.user.is_authenticated else None

            ordem_servico = OrdemServicoFacade().abrir(usuario_autenticado, serializer.validated_data)

            return resposta_sucesso("Ordem de serviço aberta com sucesso.", OrdemServicoSerializer(ordem_servico).data, status.HTTP_201_CREATED)

        return resposta_erro("Erro ao abrir ordem de serviço.", serializer.errors)

class OrdemServicoRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = OrdemServicoSerializer
    
    def get_permissions(self):
        if self.request.method in ['PATCH', 'PUT', 'DELETE']:
            return [IsAuthenticated(), IsGerenteOuGestorOuTecnico()]
        return [IsAuthenticated()]

    def get_queryset(self):
        fabrica = resolver_fabrica_acesso(self.request.user)
        return fabrica.criar_escopo_consulta().filtrar(self.request.user)

    def retrieve(self, request, *args, **kwargs):
        ordem_servico = self.get_object()
        return resposta_sucesso("Ordem de serviço encontrada com sucesso.", self.get_serializer(ordem_servico).data)

    def update(self, request, *args, **kwargs):
        parcial = kwargs.pop("partial", False)
        ordem_servico = self.get_object()
        fachada = OrdemServicoFacade()

        # Checa status final antes de validar o payload para manter a precedência de erros da API.
        try:
            fachada.garantir_alteracao_permitida(ordem_servico)
        except OperacaoOrdemServicoError as erro:
            return resposta_erro(erro.mensagem, None)

        serializer = self.get_serializer(ordem_servico, data=request.data, partial=parcial)

        if serializer.is_valid():
            motivo_tecnico = request.data.get("observacao", "")

            try:
                ordem_servico = fachada.alterar_status(ordem_servico, request.user, serializer.validated_data, motivo_tecnico)
            except OperacaoOrdemServicoError as erro:
                return resposta_erro(erro.mensagem, None)

            return resposta_sucesso("Ordem de serviço atualizada com sucesso.", self.get_serializer(ordem_servico).data)

        return resposta_erro("Erro ao atualizar ordem de serviço.", serializer.errors)

class OrdemServicoDestroyView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = OrdemServicoSerializer
    permission_classes = (IsAuthenticated,)

    def destroy(self, request, *args, **kwargs):
        ordem_servico = self.get_object()

        try:
            OrdemServicoFacade().cancelar(ordem_servico, request.user)
        except OperacaoOrdemServicoError as erro:
            return resposta_erro(erro.mensagem, None)

        return resposta_sucesso("Ordem de serviço cancelada com sucesso.", None)

class OrdemServicoAtribuirTecnicoView(APIView):
    permission_classes = (IsAuthenticated, IsGerenteOuGestorOuTecnico)

    def patch(self, request, pk):

        if not usuario_tem_grupo(request.user, "GESTOR") and not usuario_tem_grupo(request.user, "GERENTE"):
            return resposta_erro("Sem permissão.", None)

        try:
            os = OrdemServico.objects.get(pk=pk)
        except:
            return resposta_erro("OS não encontrada.", None)

        serializer = AtribuirTecnicoSerializer(data=request.data)

        if not serializer.is_valid():
            return resposta_erro("Erro.", serializer.errors)

        tecnico = Usuario.objects.get(id_usuario=serializer.validated_data["tecnico"])

        try:
            OrdemServicoFacade().atribuir_tecnico(os, tecnico, request.user)
        except OperacaoOrdemServicoError as erro:
            return resposta_erro(erro.mensagem, None)

        return resposta_sucesso("Técnico atribuído", None)

class DashboardIndicadoresView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        usuario = request.user
        periodo = request.query_params.get('periodo', '30d')

        fabrica = resolver_fabrica_acesso(usuario)
        dados_dashboard = fabrica.criar_regra_dashboard().calcular_indicadores(usuario, periodo)

        return resposta_sucesso("Indicadores carregados com sucesso.", dados_dashboard)