import { createRouter, createWebHistory } from 'vue-router'
import LoginView from '@/views/LoginView.vue'
import ConfirmarEmailView from '../views/ConfirmarEmailView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/confirmar-email/:token',
      name: 'confirmar-email',
      component: ConfirmarEmailView
    },
    {
      path: '/cadastro',
      name: 'cadastro',
      component: () => import('@/views/CadastroView.vue'),
    },
    {
      path: '/',
      name: 'login',
      component: LoginView,
    },
    {
      path: '/abrir-os',
      name: 'abrir-os',
      component: () => import('@/views/AbrirOsView.vue'),
    },
    {
      path: '/dashboard-gerente',
      component: () => import('@/views/DashboardGerenteView.vue'),
      redirect: '/dashboard-gerente/indicadores',
      children: [
        {
          path: 'indicadores',
          component: () => import('@/views/IndicadoresView.vue'),
        },
        {
          path: 'funcionarios',
          component: () => import('@/views/FuncionariosView.vue'),
        },
        {
          path: 'ordens',
          component: () => import('@/views/OrdensView.vue'),
        },
        {
          path: 'ativos',
          component: () => import('@/views/AtivosView.vue'),
        },
        {
          path: 'historico',
          component: () => import('@/views/HistoricoView.vue')
        },
      ],
    },
    {
      path: '/dashboard-gestor',
      component: () => import('@/views/DashboardGestorView.vue'),
      redirect: '/dashboard-gestor/indicadores',
      children: [
        {
          path: 'ordens',
          component: () => import('@/views/OrdensGestorView.vue'),
        },
        {
          path: 'indicadores',
          component: () => import('@/views/IndicadoresGestorView.vue'),
        },
        {
          path: 'ativos',
          component: () => import('@/views/AtivosView.vue'),
        },
        {
          path: 'historico',
          component: () => import('@/views/HistoricoView.vue')
        },
      ],
    },
    {
      path: '/dashboard-tecnico',
      component: () => import('@/views/DashboardTecnicoView.vue'),
      redirect: '/dashboard-tecnico/ordens',
      children: [
        {
          path: 'ordens',
          component: () => import('@/views/OrdensTecnicoView.vue'),
        },
        {
          path: 'ativos',
          component: () => import('@/views/AtivosView.vue'),
        },
        {
          path: 'historico',
          component: () => import('@/views/HistoricoView.vue')
        },
      ],
    },
    {
      path: '/dashboard-solicitante',
      component: () => import('@/views/DashboardSolicitanteView.vue'),
      redirect: '/dashboard-solicitante/portal',
      children: [
        {
          path: 'portal',
          component: () => import('@/views/PortalSolicitanteView.vue'),
        },
      ],
    },
    {
      path: '/dashboard',
      redirect: '/dashboard-solicitante/portal',
    },
    {
      path: '/perfil',
      name: 'perfil',
      component: () => import('@/views/PerfilView.vue'),
    },
  ],
})

export default router
