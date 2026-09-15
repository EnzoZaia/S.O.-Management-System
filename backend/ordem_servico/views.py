from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.utils import timezone
from rest_framework.response import Response

from ordem_servico.acesso import resolver_fabrica_acesso
from ordem_servico.models import OrdemServico
from ordem_servico.processadores import obter_fabrica_processador
from ordem_servico.serializers import OrdemServicoSerializer, AtribuirTecnicoSerializer
from usuario.models import Usuario
from utils.responses import resposta_sucesso, resposta_erro
from utils.permissions import usuario_tem_grupo
from utils.historico import registrar_historico
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
            ordem_servico = serializer.save()

            # Define as variáveis de verificação de autenticação
            usuario_autenticado = request.user if request.user and request.user.is_authenticated else None
            
            if usuario_autenticado:
                usuario_historico = usuario_autenticado
                nome_solicitante = request.user.nome
            else:
                # IMPORTANTE: Busca o primeiro usuário do banco para assinar o histórico do totem
                from usuario.models import Usuario
                usuario_historico = Usuario.objects.first() # Pega o administrador ou usuário ID 1 do banco
                nome_solicitante = "Usuário Anônimo"

            # Agora passamos um objeto de usuário válido que nunca será nulo
            registrar_historico(
                ordem_servico, 
                usuario_historico, 
                f"Ordem de serviço aberta por {nome_solicitante}. Status inicial: ABERTA."
            )

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
        usuario = request.user

        if ordem_servico.status_ordem_servico in ["ENCERRADA", "CANCELADA"]:
            return resposta_erro("Esta ordem não pode mais ser alterada.", None)

        dados = request.data.copy()
        novo_status = dados.get("status_ordem_servico")
        status_anterior = ordem_servico.status_ordem_servico

        serializer = self.get_serializer(ordem_servico, data=dados, partial=parcial)

        if serializer.is_valid():
            ordem_servico = serializer.save()

            if novo_status and novo_status != status_anterior:
                motivo_tecnico = request.data.get("observacao", dados.get("observacao", ""))

                fabrica = obter_fabrica_processador(ordem_servico.tipo_manutencao)
                processador = fabrica.criar_processador()
                processador.finalizar(ordem_servico, motivo_tecnico)

                if novo_status == "CONCLUIDA":
                    ordem_servico.save()

                texto_historico = f"Status alterado: {status_anterior} -> {novo_status}."
                if motivo_tecnico and str(motivo_tecnico).strip():
                    texto_historico += f" Detalhes: {str(motivo_tecnico).strip()}"

                registrar_historico(ordem_servico, usuario, texto_historico)

            return resposta_sucesso("Ordem de serviço atualizada com sucesso.", self.get_serializer(ordem_servico).data)

        return resposta_erro("Erro ao atualizar ordem de serviço.", serializer.errors)

class OrdemServicoDestroyView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = OrdemServicoSerializer
    permission_classes = (IsAuthenticated,)

    def destroy(self, request, *args, **kwargs):
        ordem_servico = self.get_object()
        usuario = request.user

        if ordem_servico.status_ordem_servico in ["ENCERRADA", "CANCELADA"]:
            return resposta_erro("Esta ordem já está encerrada ou cancelada.", None)

        ordem_servico.status_ordem_servico = "CANCELADA"
        ordem_servico.dt_conclusao = timezone.now()
        ordem_servico.save()

        registrar_historico(
            ordem_servico,
            usuario,
            f"OS cancelada por {usuario.nome}"
        )

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

        if not usuario_tem_grupo(tecnico, "TECNICO"):
            return resposta_erro("Usuário não é técnico.", None)

        os.tecnico = tecnico

        if os.gestor is None:
            os.gestor = request.user

        if os.status_ordem_servico == "ABERTA":
            os.status_ordem_servico = "APROVADA"

        os.save()

        registrar_historico(os, request.user, f"Técnico atribuído: {tecnico.nome}")

        return resposta_sucesso("Técnico atribuído", None)

class DashboardIndicadoresView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        usuario = request.user
        periodo = request.query_params.get('periodo', '30d')

        fabrica = resolver_fabrica_acesso(usuario)
        dados_dashboard = fabrica.criar_regra_dashboard().calcular_indicadores(usuario, periodo)

        return resposta_sucesso("Indicadores carregados com sucesso.", dados_dashboard)