from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny

from ordem_servico.acesso import resolver_fabrica_acesso
from ativo.models import Ativo
from ordem_servico.fachada import (
    CorretivaDuplicadaError,
    OrdemServicoFacade,
    OrdemServicoInativaError,
    OperacaoOrdemServicoError,
    RespostaJaRegistradaError,
)
from ordem_servico.models import OrdemServico
from ordem_servico.participacao import corretiva_ativa_do_ativo, situacao_participacao
from ordem_servico.transicoes import RegraTransicaoError
from ordem_servico.indicadores import PeriodoInvalidoError, calcular_indicadores_gerenciais, resolver_periodo
from evidencia_os.models import EvidenciaOrdem
from evidencia_os.serializers import EvidenciaOrdemSerializer
from evidencia_os.services import EvidenciaError, anexar_evidencias
from ordem_servico.serializers import AbrirOrdemServicoSerializer, OrdemServicoSerializer, AtribuirTecnicoSerializer
from usuario.models import Usuario
from utils.responses import resposta_sucesso, resposta_erro, resposta_conflito
from utils.permissions import (
    IsGerente,
    IsGerenteOuGestor,
    IsGerenteOuGestorOuTecnico,
    IsSolicitanteOuParticipanteDaOS,
    usuario_participa_da_os,
    usuario_tem_grupo,
)
from validacao.models import ValidacaoAtendimento
from validacao.serializers import (
    AvaliacaoSerializer,
    AvaliarOrdemServicoSerializer,
    ValidacaoAtendimentoSerializer,
    ValidarOrdemServicoSerializer,
)

_RELACIONADOS_OS = ('localizacao__predio', 'solicitante', 'ativo')


def _escopo_do_usuario(usuario):
    fabrica = resolver_fabrica_acesso(usuario)
    return fabrica.criar_escopo_consulta().filtrar(usuario).com_total_afetados().select_related(*_RELACIONADOS_OS)


def _usuario_autenticado(request):
    usuario = getattr(request, 'user', None)
    return usuario if usuario is not None and getattr(usuario, 'is_authenticated', False) else None


def _resposta_duplicidade(ordem_existente, usuario, mensagem):
    return resposta_conflito(mensagem, situacao_participacao(ordem_existente, usuario))


def _primeiro_erro(erros) -> str:
    for valor in erros.values():
        if isinstance(valor, (list, tuple)) and valor:
            return str(valor[0])
        if isinstance(valor, dict):
            return _primeiro_erro(valor)
        if valor:
            return str(valor)
    return "Dados inválidos."

class OrdemServicoListCreateView(generics.ListCreateAPIView):
    serializer_class = OrdemServicoSerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            return [AllowAny(),]
        return [IsAuthenticated()]

    def get_queryset(self):
        return _escopo_do_usuario(self.request.user)

    def create(self, request, *args, **kwargs):
        usuario_autenticado = _usuario_autenticado(request)
        contexto = {
            'request': request,
            'exige_ativo': bool(usuario_autenticado and usuario_tem_grupo(usuario_autenticado, "SOLICITANTE")),
        }
        serializer = AbrirOrdemServicoSerializer(data=request.data, context=contexto)

        if serializer.is_valid():
            try:
                ordem_servico = OrdemServicoFacade().abrir(usuario_autenticado, serializer.validated_data)
            except CorretivaDuplicadaError as erro:
                if erro.ordem_existente is None:
                    return resposta_erro(erro.mensagem, {"ativo": [erro.mensagem]}, status.HTTP_409_CONFLICT)
                return _resposta_duplicidade(erro.ordem_existente, usuario_autenticado, erro.mensagem)

            return resposta_sucesso("Ordem de serviço aberta com sucesso.", OrdemServicoSerializer(ordem_servico, context={'request': request}).data, status.HTTP_201_CREATED)

        return resposta_erro("Erro ao abrir ordem de serviço.", serializer.errors)

class OrdemServicoRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = OrdemServicoSerializer

    def get_permissions(self):
        if self.request.method in ['PATCH', 'PUT', 'DELETE']:
            return [IsAuthenticated(), IsGerenteOuGestorOuTecnico()]
        return [IsAuthenticated()]

    def get_queryset(self):
        return _escopo_do_usuario(self.request.user)

    def retrieve(self, request, *args, **kwargs):
        ordem_servico = self.get_object()
        return resposta_sucesso("Ordem de serviço encontrada com sucesso.", self.get_serializer(ordem_servico).data)

    def update(self, request, *args, **kwargs):
        parcial = kwargs.pop("partial", False)
        ordem_servico = self.get_object()
        fachada = OrdemServicoFacade()

        try:
            fachada.garantir_alteracao_permitida(ordem_servico)
        except OperacaoOrdemServicoError as erro:
            return resposta_erro(erro.mensagem, None)

        serializer = self.get_serializer(ordem_servico, data=request.data, partial=parcial)

        if serializer.is_valid():
            motivo_tecnico = request.data.get("observacao", "")

            try:
                ordem_servico = fachada.alterar_status(ordem_servico, request.user, serializer.validated_data, motivo_tecnico)
            except RegraTransicaoError as erro:
                return resposta_erro(erro.mensagem, erro.erros, erro.status_code)
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
    permission_classes = (IsAuthenticated, IsGerenteOuGestor)

    def patch(self, request, pk):
        os = get_object_or_404(_escopo_do_usuario(request.user), pk=pk)

        serializer = AtribuirTecnicoSerializer(data=request.data)

        if not serializer.is_valid():
            return resposta_erro("Erro.", serializer.errors)

        tecnico = Usuario.objects.filter(id_usuario=serializer.validated_data["tecnico"]).first()
        if tecnico is None:
            return resposta_erro("Técnico informado não existe.", {"tecnico": ["Técnico informado não existe."]})

        justificativa = request.data.get("justificativa") or request.data.get("observacao") or ""

        try:
            OrdemServicoFacade().atribuir_tecnico(os, tecnico, request.user, justificativa)
        except RegraTransicaoError as erro:
            return resposta_erro(erro.mensagem, erro.erros, erro.status_code)
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


class _OrdemServicoDoParticipanteView(APIView):
    permission_classes = (IsAuthenticated, IsSolicitanteOuParticipanteDaOS)

    def obter_ordem_servico(self, request, pk) -> OrdemServico:
        ordem_servico = get_object_or_404(OrdemServico, pk=pk)
        self.check_object_permissions(request, ordem_servico)
        return ordem_servico


class _LeituraOrdemServicoView(APIView):
    permission_classes = (IsAuthenticated,)

    def obter_ordem_servico(self, request, pk) -> OrdemServico:
        ordem_servico = get_object_or_404(OrdemServico, pk=pk)
        visivel = _escopo_do_usuario(request.user).filter(pk=pk).exists() or usuario_participa_da_os(request.user, ordem_servico)
        if not visivel:
            self.permission_denied(request, message="Você não tem acesso a esta ordem de serviço.")
        return ordem_servico


class OrdemServicoValidarView(_OrdemServicoDoParticipanteView):
    def patch(self, request, pk):
        ordem_servico = self.obter_ordem_servico(request, pk)

        serializer = ValidarOrdemServicoSerializer(data=request.data)
        if not serializer.is_valid():
            return resposta_erro(_primeiro_erro(serializer.errors), serializer.errors)

        dados = serializer.validated_data

        try:
            validacao = OrdemServicoFacade().validar(
                ordem_servico,
                request.user,
                aprovada=dados['aprovada'],
                justificativa=dados.get('justificativa'),
                evidencias=dados.get('evidencias') or (),
            )
        except RespostaJaRegistradaError as erro:
            return resposta_conflito(erro.mensagem, ValidacaoAtendimentoSerializer(erro.registro, context={'request': request}).data)
        except OperacaoOrdemServicoError as erro:
            return resposta_erro(erro.mensagem, None)

        ordem_servico.refresh_from_db(fields=['status_ordem_servico'])
        mensagem = "Serviço aprovado com sucesso." if validacao.aprovada else "Serviço reprovado. A ordem retornou ao técnico e o gestor foi alertado."

        return resposta_sucesso(mensagem, {
            'status_ordem_servico': ordem_servico.status_ordem_servico,
            'validacao': ValidacaoAtendimentoSerializer(validacao, context={'request': request}).data,
        })


class OrdemServicoValidacaoView(_LeituraOrdemServicoView):
    def get(self, request, pk):
        ordem_servico = self.obter_ordem_servico(request, pk)
        validacao = ValidacaoAtendimento.ultima_da_os(ordem_servico)

        if validacao is None:
            return resposta_sucesso("Nenhuma validação registrada para esta ordem.", None)

        return resposta_sucesso("Validação encontrada com sucesso.", ValidacaoAtendimentoSerializer(validacao, context={'request': request}).data)


class OrdemServicoAvaliarView(_OrdemServicoDoParticipanteView):
    def post(self, request, pk):
        ordem_servico = self.obter_ordem_servico(request, pk)

        serializer = AvaliarOrdemServicoSerializer(data=request.data)
        if not serializer.is_valid():
            return resposta_erro("Não foi possível registrar a avaliação. Verifique os campos informados.", serializer.errors)

        try:
            avaliacao = OrdemServicoFacade().avaliar(
                ordem_servico,
                request.user,
                nota=serializer.validated_data['nota'],
                comentario=serializer.validated_data.get('comentario'),
            )
        except RespostaJaRegistradaError as erro:
            return resposta_conflito(erro.mensagem, AvaliacaoSerializer(erro.registro).data)
        except OperacaoOrdemServicoError as erro:
            return resposta_erro(erro.mensagem, None)

        ordem_servico.refresh_from_db(fields=['status_ordem_servico'])

        return resposta_sucesso("Avaliação registrada e ordem encerrada com sucesso.", {
            'status_ordem_servico': ordem_servico.status_ordem_servico,
            'avaliacao': AvaliacaoSerializer(avaliacao).data,
        }, status.HTTP_201_CREATED)


class OrdemServicoAvaliacaoView(_LeituraOrdemServicoView):
    def get(self, request, pk):
        ordem_servico = self.obter_ordem_servico(request, pk)
        avaliacao = ValidacaoAtendimento.avaliacao_da_os(ordem_servico)

        if avaliacao is None:
            return resposta_sucesso("Nenhuma avaliação registrada para esta ordem.", None)

        return resposta_sucesso("Avaliação encontrada com sucesso.", AvaliacaoSerializer(avaliacao).data)



class OrdemServicoVerificarDuplicidadeView(APIView):
    permission_classes = (AllowAny,)

    def get(self, request):
        id_ativo = (request.query_params.get('ativo') or '').strip()
        codigo = (request.query_params.get('codigo_patrimonial') or '').strip()

        if not id_ativo and not codigo:
            return resposta_erro("Informe o ativo ou o código patrimonial.", {"ativo": ["Informe o ativo ou o código patrimonial."]})

        if id_ativo:
            if not id_ativo.isdigit():
                return resposta_erro("Ativo inválido.", {"ativo": ["Informe um id de ativo numérico."]})
            ativo = Ativo.objects.filter(pk=int(id_ativo)).first()
            if ativo is None:
                return resposta_erro("Ativo não encontrado.", {"ativo": ["Ativo não encontrado."]})
        else:
            ativo = Ativo.objects.filter(codigo_patrimonial__iexact=codigo).first()
            if ativo is None:
                return resposta_erro("Patrimônio não encontrado.", {"codigo_patrimonial": ["Patrimônio não encontrado."]})

        existente = corretiva_ativa_do_ativo(ativo)
        if existente is None:
            return resposta_sucesso(
                "Nenhuma ordem em andamento para este ativo.",
                {"duplicada": False, "ordem_existente": None, "pode_presenciar": False, "ja_vinculado": False},
            )

        dados = {"duplicada": True, **situacao_participacao(existente, _usuario_autenticado(request))}
        return resposta_sucesso(OrdemServicoFacade.MENSAGEM_CORRETIVA_DUPLICADA, dados)


class OrdemServicoPresencieiView(APIView):
    permission_classes = (IsAuthenticated,)

    def _obter(self, pk):
        return get_object_or_404(OrdemServico.objects.select_related('localizacao__predio', 'ativo'), pk=pk)

    def _dados(self, ordem_servico, usuario):
        recarregada = (
            OrdemServico.objects.com_total_afetados()
            .select_related('localizacao__predio', 'ativo')
            .get(pk=ordem_servico.pk)
        )
        situacao = situacao_participacao(recarregada, usuario)
        return {
            "ordem": situacao["ordem_existente"],
            "ja_vinculado": situacao["ja_vinculado"],
            "vinculo_presenciei": situacao["ja_vinculado"] and recarregada.solicitante_id != usuario.pk,
        }

    def post(self, request, pk):
        ordem_servico = self._obter(pk)

        try:
            criado = OrdemServicoFacade().presenciar(ordem_servico, request.user)
        except OrdemServicoInativaError as erro:
            return resposta_erro(erro.mensagem, None)

        if not criado:
            return resposta_sucesso("Você já participa desta ordem de serviço.", self._dados(ordem_servico, request.user))

        return resposta_sucesso(
            "Registramos que você também presenciou este problema.",
            self._dados(ordem_servico, request.user),
            status.HTTP_201_CREATED,
        )

    def delete(self, request, pk):
        ordem_servico = self._obter(pk)

        try:
            removido = OrdemServicoFacade().deixar_de_presenciar(ordem_servico, request.user)
        except OrdemServicoInativaError as erro:
            return resposta_erro(erro.mensagem, None)

        if not removido:
            return resposta_erro("Você não está vinculado a esta ordem como participante.", None, status.HTTP_404_NOT_FOUND)

        return resposta_sucesso("Vínculo de participante removido.", self._dados(ordem_servico, request.user))


class OrdemServicoEvidenciasView(_LeituraOrdemServicoView):
    def get(self, request, pk):
        ordem_servico = self.obter_ordem_servico(request, pk)
        evidencias = EvidenciaOrdem.objects.filter(ordem_servico=ordem_servico).select_related('usuario').order_by('sequencia')
        return resposta_sucesso(
            "Evidências carregadas com sucesso.",
            EvidenciaOrdemSerializer(evidencias, many=True, context={'request': request}).data,
        )

    def post(self, request, pk):
        ordem_servico = get_object_or_404(OrdemServico, pk=pk)
        if not usuario_participa_da_os(request.user, ordem_servico):
            self.permission_denied(request, message="Somente o solicitante ou um participante vinculado pode enviar evidências desta ordem.")

        try:
            criadas = anexar_evidencias(ordem_servico, request.user, request.FILES.getlist('arquivos'))
        except EvidenciaError as erro:
            return resposta_erro(erro.mensagem, {'arquivos': [erro.mensagem]}, erro.status_code)

        return resposta_sucesso(
            "Evidências enviadas com sucesso.",
            EvidenciaOrdemSerializer(criadas, many=True, context={'request': request}).data,
            status.HTTP_201_CREATED,
        )


class IndicadoresGerenciaisView(APIView):
    permission_classes = (IsAuthenticated, IsGerente)

    def get(self, request):
        try:
            periodo = resolver_periodo(
                request.query_params.get('periodo'), request.query_params.get('inicio'), request.query_params.get('fim'),
            )
        except PeriodoInvalidoError as erro:
            return resposta_erro(str(erro), {'periodo': [str(erro)]})
        return resposta_sucesso("Indicadores gerenciais calculados com sucesso.", calcular_indicadores_gerenciais(periodo))
