import { createRouter, createWebHistory } from 'vue-router'
import LoginView from '@/views/LoginView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
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
        { path: 'historico', 
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
        { path: 'historico', 
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
        { path: 'historico', 
          component: () => import('@/views/HistoricoView.vue') 
        },
      ],
    },
    {
      path: '/perfil',
      name: 'perfil',
      component: () => import('@/views/PerfilView.vue'),
    },
  ],
})

export default router
