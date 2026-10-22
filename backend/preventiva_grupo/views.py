from django.http import Http404, HttpResponse
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from ordem_servico.acesso import resolver_fabrica_acesso
from ordem_servico.constantes import STATUS_FINAIS
from ordem_servico.fachada import OperacaoOrdemServicoError, TecnicoInvalidoError
from ordem_servico.models import OrdemServico
from ordem_servico.transicoes import RegraTransicaoError
from preventiva_grupo.guia_pdf import gerar_guia_pdf
from preventiva_grupo.services import (
    PreventivaAgrupadaService,
    PreventivaGrupoError,
    montar_checklist,
    montar_grupo,
    ordens_agrupadas,
)
from utils.permissions import IsGerenteOuGestor, IsGerenteOuGestorOuTecnico
from utils.responses import resposta_erro, resposta_sucesso


def _ordens_agrupadas_do_usuario(usuario):
    escopo = resolver_fabrica_acesso(usuario).criar_escopo_consulta().filtrar(usuario)
    return escopo.filter(id_ordem_servico__in=ordens_agrupadas().values('id_ordem_servico'))


def _obter_ordem(usuario, pk):
    ordem_servico = _ordens_agrupadas_do_usuario(usuario).filter(pk=pk).first()
    if ordem_servico is None:
        raise Http404
    return ordem_servico


def _resposta_erro_grupo(erro):
    return resposta_erro(erro.mensagem, getattr(erro, 'erros', None), getattr(erro, 'status_code', status.HTTP_400_BAD_REQUEST))


class PreventivaAgrupadaListCreateView(APIView):
    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAuthenticated(), IsGerenteOuGestor()]
        return [IsAuthenticated(), IsGerenteOuGestorOuTecnico()]

    def get(self, request):
        ordens = _ordens_agrupadas_do_usuario(request.user).order_by('-id_ordem_servico')
        if str(request.query_params.get('ativas', '')).lower() in ('true', '1', 'sim'):
            ordens = ordens.exclude(status_ordem_servico__in=STATUS_FINAIS)
        grupos = [montar_grupo(ordem) for ordem in ordens]
        predio = request.query_params.get('predio')
        if predio:
            grupos = [grupo for grupo in grupos if str(grupo['predio']) == str(predio)]
        return resposta_sucesso("Ordens preventivas agrupadas carregadas com sucesso.", grupos)

    def post(self, request):
        dados = request.data
        try:
            ordem_servico = PreventivaAgrupadaService().gerar(
                request.user, dados.get('predio'), dados.get('tecnico'), dados.get('ativos'),
            )
        except PreventivaGrupoError as erro:
            return _resposta_erro_grupo(erro)
        except TecnicoInvalidoError as erro:
            return resposta_erro(erro.mensagem, {'tecnico': [erro.mensagem]})
        except RegraTransicaoError as erro:
            return _resposta_erro_grupo(erro)
        except OperacaoOrdemServicoError as erro:
            return resposta_erro(erro.mensagem, None)

        ordem_servico = OrdemServico.objects.com_responsaveis().get(pk=ordem_servico.pk)
        return resposta_sucesso("Ordem preventiva agrupada gerada com sucesso.", montar_grupo(ordem_servico), status.HTTP_201_CREATED)


class PreventivaAgrupadaResultadosView(APIView):
    permission_classes = (IsAuthenticated, IsGerenteOuGestorOuTecnico)

    def patch(self, request, pk):
        ordem_servico = _obter_ordem(request.user, pk)
        try:
            PreventivaAgrupadaService().registrar_resultados(ordem_servico, request.data.get('itens'), request.user)
        except PreventivaGrupoError as erro:
            return _resposta_erro_grupo(erro)

        ordem_servico = _obter_ordem(request.user, pk)
        grupo = montar_grupo(ordem_servico)
        return resposta_sucesso("Resultados registrados com sucesso.", {'status_ordem_servico': grupo['status_ordem_servico'], 'grupo': grupo})


class PreventivaAgrupadaChecklistView(APIView):
    permission_classes = (IsAuthenticated, IsGerenteOuGestorOuTecnico)

    def get(self, request, pk):
        return resposta_sucesso("Checklist carregado com sucesso.", montar_checklist(_obter_ordem(request.user, pk)))


class PreventivaAgrupadaChecklistAtivoView(APIView):
    permission_classes = (IsAuthenticated, IsGerenteOuGestorOuTecnico)

    def patch(self, request, pk, ativo):
        ordem_servico = _obter_ordem(request.user, pk)
        try:
            dados = PreventivaAgrupadaService().salvar_checklist(ordem_servico, ativo, request.data.get('itens'), request.user)
        except PreventivaGrupoError as erro:
            return _resposta_erro_grupo(erro)
        return resposta_sucesso("Checklist salvo com sucesso.", dados)


class PreventivaAgrupadaGuiaView(APIView):
    permission_classes = (IsAuthenticated, IsGerenteOuGestorOuTecnico)

    def get(self, request, pk):
        ordem_servico = _obter_ordem(request.user, pk)
        resposta = HttpResponse(gerar_guia_pdf(ordem_servico), content_type='application/pdf')
        resposta['Content-Disposition'] = f'attachment; filename="guia-preventiva-OS-{ordem_servico.pk}.pdf"'
        return resposta
