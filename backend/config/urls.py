"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path
from usuario.views import (
    UsuarioListCreateView, UsuarioRetrieveUpdateDestroyView, UsuarioMeusDadosView, ConfirmarEmailView,
    ReenviarConfirmacaoView, UsuarioSituacaoView, UsuarioAuditoriaView,
)
from perfil.views import GrupoListView, GrupoDetailView
from historico.views import HistoricoListView, HistoricoOrdemServicoListView
from localizacao.views import LocalizacaoListCreateView, LocalizacaoRetrieveUpdateDestroyView
from ordem_servico.views import (
    OrdemServicoListCreateView, OrdemServicoRetrieveUpdateDestroyView, OrdemServicoAtribuirTecnicoView, DashboardIndicadoresView,
    OrdemServicoValidarView, OrdemServicoValidacaoView, OrdemServicoAvaliarView, OrdemServicoAvaliacaoView,
    OrdemServicoVerificarDuplicidadeView, OrdemServicoPresencieiView, OrdemServicoEvidenciasView,
    IndicadoresGerenciaisView,
)
from preventiva_grupo.views import (
    PreventivaAgrupadaListCreateView, PreventivaAgrupadaResultadosView, PreventivaAgrupadaChecklistView,
    PreventivaAgrupadaChecklistAtivoView, PreventivaAgrupadaGuiaView,
)
from notificacao.views import NotificacaoListView, NotificacaoLidaView
from inteligencia.views import AssistenteTecnicoView, TechOrderIntelligenceView
from predio.views import PredioListCreateView, PredioRetrieveUpdateDestroyView
from authentication.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.views import TokenVerifyView
from ativo.views import AtivoListCreateView, AtivoRetrieveUpdateDestroyView, AtivoHistoricoView, AtivoSaudeListView, AtivoSaudeView

urlpatterns = [
    path('admin/', admin.site.urls),

    path('usuario/meus-dados/', UsuarioMeusDadosView.as_view(), name='usuario-meus-dados-view'),
    path('usuario/', UsuarioListCreateView.as_view(), name='usuario-list-create'),
    path('usuario/<int:pk>/', UsuarioRetrieveUpdateDestroyView.as_view(), name='usuario-detail-view'),
    path('usuario/confirmar-email/<str:token>/', ConfirmarEmailView.as_view(), name='usuario-confirmar-email'),
    path('usuario/reenviar-confirmacao/', ReenviarConfirmacaoView.as_view(), name='usuario-reenviar-confirmacao'),
    path('usuario/<int:pk>/situacao/', UsuarioSituacaoView.as_view(), name='usuario-situacao'),
    path('usuario/<int:pk>/auditoria/', UsuarioAuditoriaView.as_view(), name='usuario-auditoria'),

    path('grupo/', GrupoListView.as_view(), name='grupo-list'),
    path('grupo/<int:pk>/', GrupoDetailView.as_view(), name='grupo-detail-view'),

    path('historico/', HistoricoListView.as_view(), name='historico-list'),
    path('ordem-servico/<int:pk>/historico/', HistoricoOrdemServicoListView.as_view(), name='historico-ordem-servico'),

    path('localizacao/', LocalizacaoListCreateView.as_view(), name='localizacao-list-create'),
    path('localizacao/<int:pk>/', LocalizacaoRetrieveUpdateDestroyView.as_view(), name='localizacao-detail-view'),

    path('ordem-servico/', OrdemServicoListCreateView.as_view(), name='ordem-servico-list-create'),
    path('ordem-servico/<int:pk>/', OrdemServicoRetrieveUpdateDestroyView.as_view(), name='ordem-servico-detail-view'),
    path('ordem-servico/<int:pk>/atribuir-tecnico/', OrdemServicoAtribuirTecnicoView.as_view(), name='ordem-servico-atribuir-tecnico'),
    path('ordem-servico/preventivas-agrupadas/', PreventivaAgrupadaListCreateView.as_view(), name='preventivas-agrupadas'),
    path('ordem-servico/preventivas-agrupadas/<int:pk>/resultados/', PreventivaAgrupadaResultadosView.as_view(), name='preventivas-agrupadas-resultados'),
    path('ordem-servico/preventivas-agrupadas/<int:pk>/checklist/', PreventivaAgrupadaChecklistView.as_view(), name='preventivas-agrupadas-checklist'),
    path('ordem-servico/preventivas-agrupadas/<int:pk>/ativos/<int:ativo>/checklist/', PreventivaAgrupadaChecklistAtivoView.as_view(), name='preventivas-agrupadas-checklist-ativo'),
    path('ordem-servico/preventivas-agrupadas/<int:pk>/guia/', PreventivaAgrupadaGuiaView.as_view(), name='preventivas-agrupadas-guia'),
    path('ordem-servico/<int:pk>/evidencias/', OrdemServicoEvidenciasView.as_view(), name='ordem-servico-evidencias'),
    path('ordem-servico/<int:pk>/assistente/', AssistenteTecnicoView.as_view(), name='ordem-servico-assistente'),
    path('indicadores/intelligence/', TechOrderIntelligenceView.as_view(), name='techorder-intelligence'),
    path('notificacao/', NotificacaoListView.as_view(), name='notificacao-list'),
    path('notificacao/<int:pk>/lida/', NotificacaoLidaView.as_view(), name='notificacao-lida'),
    path('ordem-servico/verificar-duplicidade/', OrdemServicoVerificarDuplicidadeView.as_view(), name='ordem-servico-verificar-duplicidade'),
    path('ordem-servico/<int:pk>/presenciei/', OrdemServicoPresencieiView.as_view(), name='ordem-servico-presenciei'),
    path('ordem-servico/<int:pk>/validar/', OrdemServicoValidarView.as_view(), name='ordem-servico-validar'),
    path('ordem-servico/<int:pk>/validacao/', OrdemServicoValidacaoView.as_view(), name='ordem-servico-validacao'),
    path('ordem-servico/<int:pk>/avaliar/', OrdemServicoAvaliarView.as_view(), name='ordem-servico-avaliar'),
    path('ordem-servico/<int:pk>/avaliacao/', OrdemServicoAvaliacaoView.as_view(), name='ordem-servico-avaliacao'),
    path('ordem-servico/indicadores-gerenciais/', IndicadoresGerenciaisView.as_view(), name='indicadores-gerenciais'),
    path('ordem-servico/dashboard/indicadores/', DashboardIndicadoresView.as_view(), name='dashboard-indicadores'),

    path('predio/', PredioListCreateView.as_view(), name='predio-list-create'),
    path('predio/<int:pk>/', PredioRetrieveUpdateDestroyView.as_view(), name='predio-detail-view'),

    path('authentication/token/', TokenObtainPairView.as_view(), name='token-obtain-pair'),
    path('authentication/token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('authentication/token/verify/', TokenVerifyView.as_view(), name='token-verify'),

    path('ativo/', AtivoListCreateView.as_view(), name='ativo-list-create'),
    path('ativo/<int:pk>/', AtivoRetrieveUpdateDestroyView.as_view(), name='ativo-detail-view'),

    path('ativo/saude/', AtivoSaudeListView.as_view(), name='ativo-saude-list'),
    path('ativo/<int:pk>/saude/', AtivoSaudeView.as_view(), name='ativo-saude'),
    path('ativo/<int:pk>/historico/', AtivoHistoricoView.as_view(), name='ativo-historico'),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
