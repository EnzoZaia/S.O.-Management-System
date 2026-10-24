<template>
  <div v-if="!indisponivel" data-testid="guia-checklist">
    <div class="flex items-center justify-between gap-3 mb-2">
      <p class="text-[11px] font-bold text-gray-400 uppercase tracking-wider">📋 Guia e checklist da preventiva</p>
      <button v-if="ativos.length" @click="baixar" :disabled="baixando"
        class="px-3 py-1.5 text-xs font-bold text-indigo-600 bg-white border border-indigo-200 hover:bg-indigo-50 rounded-lg cursor-pointer disabled:opacity-50">
        {{ baixando ? 'Gerando PDF...' : '⬇️ Baixar guia (PDF)' }}
      </button>
    </div>

    <div class="bg-gray-50/50 rounded-2xl border border-gray-100 p-5 space-y-3">
      <div v-if="loading" class="text-center text-gray-400 font-medium py-3">A carregar checklist...</div>
      <div v-else-if="erroCarga" class="text-center text-sm text-red-600 font-semibold py-3">{{ erroCarga }}</div>

      <template v-else>
        <p v-if="!editavel" class="text-[11px] font-semibold text-gray-500">
          O checklist é preenchido durante a execução. Inicie a ordem para responder os itens.
        </p>

        <div v-for="a in ativos" :key="a.ativo" class="bg-white border border-gray-200 rounded-xl overflow-hidden"
          data-testid="checklist-ativo">
          <button type="button" @click="alternar(a.ativo)"
            class="w-full flex items-center justify-between gap-3 p-4 text-left cursor-pointer hover:bg-gray-50">
            <div class="min-w-0">
              <p class="text-sm font-bold text-gray-800 truncate">
                ❄️ {{ a.nome }}
                <span class="ml-1 text-[10px] font-bold px-1.5 py-0.5 bg-purple-100 text-purple-700 border border-purple-200 rounded">PAT: {{ a.codigo_patrimonial }}</span>
              </p>
              <p class="text-[11px] text-gray-500 mt-0.5">{{ contarRespondidos(a.itens) }}/{{ a.itens.length }} itens respondidos</p>
            </div>
            <span :class="classeResultado(a.resultado)" class="text-[10px] font-bold px-2 py-0.5 rounded-full border whitespace-nowrap">
              {{ rotuloResultado(a.resultado) }}
            </span>
          </button>

          <div v-if="aberto === a.ativo" class="border-t border-gray-100 p-4 space-y-3">
            <p v-if="a.resultado === 'NAO_CONCLUIDO' && a.motivo" class="text-xs text-orange-700 italic">"{{ a.motivo }}"</p>

            <ul class="space-y-2">
              <li v-for="item in a.itens" :key="item.id_item" class="border border-gray-100 rounded-lg p-3 space-y-2">
                <p class="text-sm text-gray-800 font-semibold">{{ item.descricao }}</p>
                <div class="grid grid-cols-2 gap-2">
                  <button type="button" :disabled="!podeEditar(a)" @click="marcar(a.ativo, item, 'EXECUTADO')"
                    :class="item.resultado === 'EXECUTADO' ? 'bg-emerald-600 text-white border-emerald-600' : 'bg-white text-emerald-700 border-emerald-200 hover:bg-emerald-50'"
                    class="py-1.5 rounded-lg border text-xs font-bold cursor-pointer disabled:cursor-not-allowed disabled:opacity-60">✅ Executado</button>
                  <button type="button" :disabled="!podeEditar(a)" @click="marcar(a.ativo, item, 'NAO_EXECUTADO')"
                    :class="item.resultado === 'NAO_EXECUTADO' ? 'bg-orange-500 text-white border-orange-500' : 'bg-white text-orange-600 border-orange-200 hover:bg-orange-50'"
                    class="py-1.5 rounded-lg border text-xs font-bold cursor-pointer disabled:cursor-not-allowed disabled:opacity-60">⏭️ Não executado</button>
                </div>
                <div v-if="item.resultado === 'NAO_EXECUTADO'" class="space-y-1">
                  <input v-model="item.motivo" type="text" :disabled="!podeEditar(a)" :maxlength="MOTIVO_MAX"
                    placeholder="Motivo de não ter executado *" :aria-label="`Motivo do item ${item.descricao}`"
                    :class="erros[a.ativo]?.itens[item.id_item] ? 'border-red-500' : 'border-gray-200'"
                    class="w-full bg-gray-50 border text-gray-700 text-sm rounded-lg px-3 py-2 outline-none focus:ring-2 focus:ring-orange-400 disabled:opacity-60" />
                  <p v-if="erros[a.ativo]?.itens[item.id_item]" role="alert" class="text-[11px] font-medium text-red-600">{{ erros[a.ativo]?.itens[item.id_item] }}</p>
                </div>
              </li>
            </ul>

            <template v-if="podeEditar(a)">
              <p v-if="erros[a.ativo]?.geral" role="alert" class="text-xs font-semibold text-red-600">{{ erros[a.ativo]?.geral }}</p>

              <div v-if="mostrarMotivo[a.ativo]" class="space-y-1">
                <label class="text-[11px] font-bold text-gray-500 uppercase tracking-wider">Motivo de não concluir o ativo *</label>
                <textarea v-model="motivoAtivo[a.ativo]" rows="2" :maxlength="MOTIVO_MAX" placeholder="Por que este ativo não foi concluído?"
                  :class="erros[a.ativo]?.motivo ? 'border-red-500' : 'border-gray-200'"
                  class="w-full bg-gray-50 border text-gray-700 text-sm rounded-lg p-3 outline-none focus:ring-2 focus:ring-orange-400 resize-none"></textarea>
                <p v-if="erros[a.ativo]?.motivo" role="alert" class="text-[11px] font-medium text-red-600">{{ erros[a.ativo]?.motivo }}</p>
              </div>

              <div class="flex flex-wrap justify-end gap-2 pt-1">
                <button @click="salvar(a)" :disabled="salvando !== null"
                  class="px-4 py-2 text-xs font-bold text-gray-600 bg-white border border-gray-200 hover:bg-gray-100 rounded-lg cursor-pointer disabled:opacity-50">
                  {{ salvando === a.ativo ? 'Salvando...' : '💾 Salvar progresso' }}
                </button>
                <button @click="naoConcluir(a)" :disabled="salvando !== null"
                  class="px-4 py-2 text-xs font-bold text-orange-600 bg-orange-50 border border-orange-200 hover:bg-orange-100 rounded-lg cursor-pointer disabled:opacity-50">
                  {{ mostrarMotivo[a.ativo] ? 'Confirmar não concluído' : '↩️ Não concluído' }}
                </button>
                <button @click="concluir(a)" :disabled="salvando !== null"
                  class="px-4 py-2 text-xs font-bold text-white bg-emerald-600 hover:bg-emerald-700 rounded-lg shadow-sm cursor-pointer disabled:opacity-50">
                  ✅ Concluir ativo
                </button>
              </div>
            </template>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import Swal from 'sweetalert2'
import {
  ChecklistError, baixarGuiaPdf, buscarChecklist, registrarResultadoAtivo, salvarChecklistAtivo,
} from '@/services/checklistPreventivaService'
import type {
  AtivoChecklist, ErroChecklist, ErrosChecklistAtivo, ItemChecklist, ResultadoAtivoChecklist, ResultadoChecklistItem,
} from '@/types/checklistPreventiva'
import {
  contarRespondidos, montarItensEnvio, temErros, validarConclusaoExecutada, validarNaoConcluido, validarRascunho,
} from '@/utils/validacaoChecklist'
import { MOTIVO_MAX } from '@/utils/validacaoPreventivaGrupo'

const props = defineProps<{ idOrdem: number; status?: string; editavel: boolean }>()
const emit = defineEmits<{
  (e: 'agrupada', valor: boolean): void
  (e: 'atualizado'): void
}>()

const ativos = ref<AtivoChecklist[]>([])
const loading = ref(true)
const indisponivel = ref(false)
const erroCarga = ref('')
const baixando = ref(false)
const salvando = ref<number | null>(null)
const aberto = ref<number | null>(null)
const erros = ref<Record<number, ErrosChecklistAtivo>>({})
const motivoAtivo = ref<Record<number, string>>({})
const mostrarMotivo = ref<Record<number, boolean>>({})

const toast = Swal.mixin({ toast: true, position: 'top-end', showConfirmButton: false, timer: 3000, timerProgressBar: true })

const podeEditar = (a: AtivoChecklist) => props.editavel && a.resultado === 'PENDENTE'

function rotuloResultado(r: ResultadoAtivoChecklist) {
  return { PENDENTE: 'Pendente', CONCLUIDO: 'Concluído', NAO_CONCLUIDO: 'Não concluído' }[r]
}

function classeResultado(r: ResultadoAtivoChecklist) {
  if (r === 'CONCLUIDO') return 'bg-emerald-100 text-emerald-700 border-emerald-200'
  if (r === 'NAO_CONCLUIDO') return 'bg-orange-100 text-orange-700 border-orange-200'
  return 'bg-gray-100 text-gray-600 border-gray-200'
}

function alternar(id: number) {
  aberto.value = aberto.value === id ? null : id
}

function marcar(idAtivo: number, item: ItemChecklist, resultado: ResultadoChecklistItem) {
  item.resultado = resultado
  if (resultado === 'EXECUTADO') item.motivo = null
  erros.value = { ...erros.value, [idAtivo]: { itens: {} } }
}

/** `preservarRascunho`: mantém as respostas ainda não salvas dos outros ativos ao recarregar. */
async function carregar(preservarRascunho = false, ativoAlvo?: number) {
  loading.value = ativos.value.length === 0
  erroCarga.value = ''
  try {
    const dados = await buscarChecklist(props.idOrdem)
    const locais = new Map(ativos.value.map((a) => [a.ativo, a]))
    ativos.value = dados.ativos.map((s) => {
      const local = locais.get(s.ativo)
      return preservarRascunho && local && s.resultado === 'PENDENTE' && s.ativo !== ativoAlvo ? { ...s, itens: local.itens } : s
    })
    indisponivel.value = false
    emit('agrupada', ativos.value.length > 0)
    if (ativos.value.length === 0) indisponivel.value = true
  } catch (e) {
    if (e instanceof ChecklistError && e.info.tipo === 'INDISPONIVEL') {
      // ordem sem checklist agrupado (ex.: preventiva de um único ativo): a seção some
      ativos.value = []
      indisponivel.value = true
      emit('agrupada', false)
    } else {
      console.error('Erro ao carregar checklist', e)
      erroCarga.value = 'Não foi possível carregar o checklist.'
    }
  } finally {
    loading.value = false
  }
}

const MENSAGENS: Record<ErroChecklist['tipo'], { titulo: string; texto: string }> = {
  INDISPONIVEL: { titulo: 'Recurso indisponível', texto: 'O servidor ainda não oferece o guia/checklist desta ordem.' },
  FORA_ESCOPO: { titulo: 'Sem permissão', texto: 'Esta ordem não está atribuída a você.' },
  CHECKLIST_INCOMPLETO: { titulo: 'Checklist incompleto', texto: 'Responda todos os itens do checklist antes de concluir o ativo.' },
  STATUS_INVALIDO: { titulo: 'Ação indisponível', texto: 'O status da ordem mudou. A tela foi atualizada.' },
  VALIDACAO: { titulo: 'Dados inválidos', texto: 'Revise os itens e motivos informados.' },
  GENERICO: { titulo: 'Erro', texto: 'Não foi possível concluir a operação. Tente novamente.' },
}

async function tratarErro(e: unknown) {
  if (!(e instanceof ChecklistError)) {
    console.error('Erro no checklist', e)
    await Swal.fire({ title: 'Erro', text: MENSAGENS.GENERICO.texto, icon: 'error' })
    return
  }
  const { titulo, texto } = MENSAGENS[e.info.tipo]
  await Swal.fire({
    title: titulo, text: e.info.tipo === 'INDISPONIVEL' ? texto : e.info.mensagem || texto,
    icon: e.info.tipo === 'GENERICO' ? 'error' : 'info', confirmButtonColor: '#2563eb',
  })
  if (e.info.tipo === 'STATUS_INVALIDO' || e.info.tipo === 'CHECKLIST_INCOMPLETO') {
    await carregar(true)
    emit('atualizado')
  }
}

async function baixar() {
  baixando.value = true
  try {
    await baixarGuiaPdf(props.idOrdem)
  } catch (e) {
    await tratarErro(e)
  } finally {
    baixando.value = false
  }
}

async function salvar(a: AtivoChecklist) {
  const e = validarRascunho(a.itens)
  erros.value = { ...erros.value, [a.ativo]: e }
  if (temErros(e) || salvando.value !== null) return
  salvando.value = a.ativo
  try {
    await salvarChecklistAtivo(props.idOrdem, a.ativo, montarItensEnvio(a.itens))
    toast.fire({ icon: 'success', title: 'Progresso salvo!' })
  } catch (err) {
    await tratarErro(err)
  } finally {
    salvando.value = null
  }
}

async function finalizar(a: AtivoChecklist, resultado: 'CONCLUIDO' | 'NAO_CONCLUIDO', motivo?: string) {
  salvando.value = a.ativo
  try {
    // Ativo "não concluído" pode não ter nenhum item respondido; o backend recusa salvar lista vazia.
    const itensEnvio = montarItensEnvio(a.itens)
    if (itensEnvio.length) await salvarChecklistAtivo(props.idOrdem, a.ativo, itensEnvio)
    const resposta = await registrarResultadoAtivo(props.idOrdem, a.ativo, resultado, motivo)
    await carregar(true, a.ativo)
    emit('atualizado')
    const encerrada = resposta.status_ordem_servico === 'ENCERRADA'
    await Swal.fire({
      title: 'Resultado registrado!',
      text: encerrada ? 'Todos os ativos têm resultado: a ordem foi encerrada automaticamente.' : undefined,
      icon: 'success', timer: 2500, showConfirmButton: false,
    })
  } catch (err) {
    await tratarErro(err)
  } finally {
    salvando.value = null
  }
}

// CA3: checklist incompleto impede a conclusão como executado.
async function concluir(a: AtivoChecklist) {
  const e = validarConclusaoExecutada(a.itens)
  erros.value = { ...erros.value, [a.ativo]: e }
  if (temErros(e) || salvando.value !== null) return
  await finalizar(a, 'CONCLUIDO')
}

async function naoConcluir(a: AtivoChecklist) {
  if (!mostrarMotivo.value[a.ativo]) {
    mostrarMotivo.value = { ...mostrarMotivo.value, [a.ativo]: true }
    return
  }
  const motivo = motivoAtivo.value[a.ativo] ?? ''
  const e = validarNaoConcluido(a.itens, motivo)
  erros.value = { ...erros.value, [a.ativo]: e }
  if (temErros(e) || salvando.value !== null) return
  await finalizar(a, 'NAO_CONCLUIDO', motivo.trim())
}

watch(() => props.idOrdem, () => { ativos.value = []; aberto.value = null; erros.value = {}; carregar() })
watch(() => props.status, () => carregar(true))
onMounted(() => carregar())
</script>