import api from '@/services/api'
import type { EventoHistorico, OrdemPortal, ResultadoValidacao } from '@/types/portal'


export async function listarMinhasOrdens(): Promise<OrdemPortal[]> {
  const { data } = await api.get('/ordem-servico/')
  const lista: OrdemPortal[] = data?.dados || data || []
  return [...lista].sort(
    (a, b) => new Date(b.dt_abertura).getTime() - new Date(a.dt_abertura).getTime(),
  )
}


export async function buscarHistoricoOrdem(id: number): Promise<EventoHistorico[]> {
  const { data } = await api.get(`/ordem-servico/${id}/historico/`)
  const lista: EventoHistorico[] = data?.dados || data || []
  return [...lista].sort(
    (a, b) => new Date(b.data_registro).getTime() - new Date(a.data_registro).getTime(),
  )
}


export async function validarOrdem(id: number, resultado: ResultadoValidacao) {
  const { data } = await api.patch(`/ordem-servico/${id}/validar/`, resultado)
  return data
}