from django.http import Http404
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from perfil.services import PERFIL_POR_ID, lista_perfis
from utils.permissions import IsGerente
from utils.responses import resposta_sucesso


class GrupoListView(APIView):
    permission_classes = (IsAuthenticated, IsGerente)

    def get(self, request):
        return resposta_sucesso("Grupos listados com sucesso.", lista_perfis())


class GrupoDetailView(APIView):
    permission_classes = (IsAuthenticated, IsGerente)

    def get(self, request, pk):
        nome = PERFIL_POR_ID.get(pk)
        if nome is None:
            raise Http404
        return resposta_sucesso("Grupo encontrado com sucesso.", {'id_grupo': pk, 'desc_grupo': nome})
