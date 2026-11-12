import api from '@/services/api'

export interface Notificacao {
  id_notificacao: number
  tipo: string
  titulo: string
  mensagem: string
  ordem_servico: number | null
  lida: boolean
  dt_criacao: string
  dt_leitura: string | null
}

export interface ListaNotificacoes {
  nao_lidas: number
  notificacoes: Notificacao[]
}

export async function listarNotificacoes(): Promise<ListaNotificacoes> {
  const { data } = await api.get('/notificacao/')
  return {
    nao_lidas: data?.dados?.nao_lidas ?? 0,
    notificacoes: data?.dados?.notificacoes ?? [],
  }
}

export async function marcarComoLida(id: number): Promise<void> {
  await api.patch(`/notificacao/${id}/lida/`)
}
