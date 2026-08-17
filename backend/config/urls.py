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
from ativo.views import AtivoListCreateView, AtivoRetrieveUpdateDestroyView, AtivoHistoricoView # <--- Import atualizado aqui!

urlpatterns = [
    path('admin/', admin.site.urls),
    
    path('usuario/meus-dados/', UsuarioMeusDadosView.as_view(), name='usuario-meus-dados-view'), # Endpoint para o usuário autenticado visualizar e atualizar seus próprios dados
    path('usuario/', UsuarioListCreateView.as_view(), name='usuario-list-create'), # Endpoint para listar e criar usuários, acessível apenas para usuários autenticados e com a permissão de gerente
    path('usuario/<int:pk>/', UsuarioRetrieveUpdateDestroyView.as_view(), name='usuario-detail-view'), # Endpoint para recuperar, atualizar e deletar um usuário específico, acessível apenas para usuários autenticados e com a permissão de gerente
    path('usuario/confirmar-email/<str:token>/', ConfirmarEmailView.as_view(), name='usuario-confirmar-email'), # Endpoint para confirmar o e-mail do usuário utilizando o token de confirmação, acessível para qualquer pessoa que tenha o link de confirmação (geralmente enviado por e-mail após o cadastro).

    path('grupo/', GrupoListCreateView.as_view(), name='grupo-list-create'), # Endpoint para listar e criar grupos, acessível apenas para usuários autenticados e com a permissão de gerente
    path('grupo/<int:pk>/', GrupoRetrieveUpdateDestroyView.as_view(), name='grupo-detail-view'), # Endpoint para recuperar, atualizar e deletar um grupo específico, acessível apenas para usuários autenticados e com a permissão de gerente

    path('grupo-usuario/', GrupoUsuarioListCreateView.as_view(), name='grupo-usuario-list-create'), # Endpoint para listar e criar associações entre grupos e usuários, acessível apenas para usuários autenticados e com a permissão de gerente
    path('grupo-usuario/<int:pk>/', GrupoUsuarioRetrieveUpdateDestroyView.as_view(), name='grupo-usuario-detail-view'), # Endpoint para recuperar, atualizar e deletar uma associação específica entre grupo e usuário, acessível apenas para usuários autenticados e com a permissão de gerente

    path('historico/', HistoricoListView.as_view(), name='historico-list'), # Endpoint para listar todos os históricos de ordens de serviço, acessível apenas para usuários autenticados. Os técnicos só podem visualizar os históricos das ordens de serviço atribuídas a eles, enquanto os gerentes podem visualizar todos os históricos.
    path('ordem-servico/<int:pk>/historico/', HistoricoOrdemServicoListView.as_view(), name='historico-ordem-servico'), # Endpoint para listar os históricos de uma ordem de serviço específica, acessível apenas para usuários autenticados. Os técnicos só podem visualizar os históricos das ordens de serviço atribuídas a eles, enquanto os gerentes podem visualizar todos os históricos.

    path('localizacao/', LocalizacaoListCreateView.as_view(), name='localizacao-list-create'), # Endpoint para listar e criar localizações, acessível para usuários autenticados.
    path('localizacao/<int:pk>/', LocalizacaoRetrieveUpdateDestroyView.as_view(), name='localizacao-detail-view'), # Endpoint para recuperar, atualizar e deletar uma localização específica, acessível para usuários autenticados. A atualização e exclusão são restritas a usuários com a permissão de gerente.

    path('ordem-servico/', OrdemServicoListCreateView.as_view(), name='ordem-servico-list-create'), # Endpoint para listar e criar ordens de serviço, acessível para usuários autenticados.
    path('ordem-servico/<int:pk>/', OrdemServicoRetrieveUpdateDestroyView.as_view(), name='ordem-servico-detail-view'), # Endpoint para recuperar, atualizar e deletar uma ordem de serviço específica, acessível para usuários autenticados. A atualização e exclusão são restritas ao solicitante da ordem ou a usuários com a permissão de gerente.
    path('ordem-servico/<int:pk>/atribuir-tecnico/', OrdemServicoAtribuirTecnicoView.as_view(), name='ordem-servico-atribuir-tecnico'), # Endpoint para atribuir um técnico a uma ordem de serviço específica, acessível apenas para usuários autenticados e com a permissão de gerente.
    path('ordem-servico/dashboard/indicadores/', DashboardIndicadoresView.as_view(), name='dashboard-indicadores'),

    path('predio/', PredioListCreateView.as_view(), name='predio-list-create'), # Endpoint para listar e criar prédios, acessível para usuários autenticados.
    path('predio/<int:pk>/', PredioRetrieveUpdateDestroyView.as_view(), name='predio-detail-view'), # Endpoint para recuperar, atualizar e deletar um prédio específico, acessível para usuários autenticados. A atualização e exclusão são restritas a usuários com a permissão de gerente.

    path('authentication/token/', TokenObtainPairView.as_view(), name='token-obtain-pair'), #login e geração dos tokens
    path('authentication/token/refresh/', TokenRefreshView.as_view(), name='token-refresh'), #renova o access token usando refresh token
    path('authentication/token/verify/', TokenVerifyView.as_view(), name='token-verify'), #verifica se o token ainda é válido

    path('ativo/', AtivoListCreateView.as_view(), name='ativo-list-create'), # Endpoint para listar e criar ativos, acessível para usuários autenticados.
    path('ativo/<int:pk>/', AtivoRetrieveUpdateDestroyView.as_view(), name='ativo-detail-view'), # Endpoint para recuperar, atualizar e deletar um ativo específico, acessível para usuários autenticados. A atualização e exclusão são restritas a usuários com a permissão de gerente. 
    
    path('ativo/<int:pk>/historico/', AtivoHistoricoView.as_view(), name='ativo-historico'), # <--- Endpoint NOVO para a linha do tempo do modal!
]