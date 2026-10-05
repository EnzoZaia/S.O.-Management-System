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
from django.contrib import admin
from django.urls import path
from usuario.views import UsuarioListCreateView, UsuarioRetrieveUpdateDestroyView, UsuarioMeusDadosView, ConfirmarEmailView
from grupo.views import GrupoListCreateView, GrupoRetrieveUpdateDestroyView
from grupo_usuario.views import GrupoUsuarioListCreateView, GrupoUsuarioRetrieveUpdateDestroyView
from historico.views import HistoricoListView, HistoricoOrdemServicoListView
from localizacao.views import LocalizacaoListCreateView, LocalizacaoRetrieveUpdateDestroyView
from ordem_servico.views import OrdemServicoListCreateView, OrdemServicoRetrieveUpdateDestroyView, OrdemServicoAtribuirTecnicoView, DashboardIndicadoresView
from predio.views import PredioListCreateView, PredioRetrieveUpdateDestroyView
from authentication.views import TokenObtainPairView
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView
from ativo.views import AtivoListCreateView, AtivoRetrieveUpdateDestroyView, AtivoHistoricoView

urlpatterns = [
    path('admin/', admin.site.urls),

    path('usuario/meus-dados/', UsuarioMeusDadosView.as_view(), name='usuario-meus-dados-view'),
    path('usuario/', UsuarioListCreateView.as_view(), name='usuario-list-create'),
    path('usuario/<int:pk>/', UsuarioRetrieveUpdateDestroyView.as_view(), name='usuario-detail-view'),
    path('usuario/confirmar-email/<str:token>/', ConfirmarEmailView.as_view(), name='usuario-confirmar-email'),

    path('grupo/', GrupoListCreateView.as_view(), name='grupo-list-create'),
    path('grupo/<int:pk>/', GrupoRetrieveUpdateDestroyView.as_view(), name='grupo-detail-view'),

    path('grupo-usuario/', GrupoUsuarioListCreateView.as_view(), name='grupo-usuario-list-create'),
    path('grupo-usuario/<int:pk>/', GrupoUsuarioRetrieveUpdateDestroyView.as_view(), name='grupo-usuario-detail-view'),

    path('historico/', HistoricoListView.as_view(), name='historico-list'),
    path('ordem-servico/<int:pk>/historico/', HistoricoOrdemServicoListView.as_view(), name='historico-ordem-servico'),

    path('localizacao/', LocalizacaoListCreateView.as_view(), name='localizacao-list-create'),
    path('localizacao/<int:pk>/', LocalizacaoRetrieveUpdateDestroyView.as_view(), name='localizacao-detail-view'),

    path('ordem-servico/', OrdemServicoListCreateView.as_view(), name='ordem-servico-list-create'),
    path('ordem-servico/<int:pk>/', OrdemServicoRetrieveUpdateDestroyView.as_view(), name='ordem-servico-detail-view'),
    path('ordem-servico/<int:pk>/atribuir-tecnico/', OrdemServicoAtribuirTecnicoView.as_view(), name='ordem-servico-atribuir-tecnico'),
    path('ordem-servico/dashboard/indicadores/', DashboardIndicadoresView.as_view(), name='dashboard-indicadores'),

    path('predio/', PredioListCreateView.as_view(), name='predio-list-create'),
    path('predio/<int:pk>/', PredioRetrieveUpdateDestroyView.as_view(), name='predio-detail-view'),

    path('authentication/token/', TokenObtainPairView.as_view(), name='token-obtain-pair'),
    path('authentication/token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('authentication/token/verify/', TokenVerifyView.as_view(), name='token-verify'),

    path('ativo/', AtivoListCreateView.as_view(), name='ativo-list-create'),
    path('ativo/<int:pk>/', AtivoRetrieveUpdateDestroyView.as_view(), name='ativo-detail-view'),

    path('ativo/<int:pk>/historico/', AtivoHistoricoView.as_view(), name='ativo-historico'),
]
