<template>
  <div>
    <p class="text-[11px] font-bold text-gray-400 uppercase tracking-wider mb-2">📎 Evidências</p>
    <div class="bg-gray-50/50 rounded-2xl border border-gray-100 p-5 space-y-4">
      <div v-if="loading" class="text-center text-gray-400 font-medium py-4">A carregar evidências...</div>
      <div v-else-if="erroCarga" class="text-center text-sm text-red-600 font-semibold py-4">{{ erroCarga }}</div>
      <div v-else-if="evidencias.length === 0" class="text-center text-gray-400 font-medium py-4" data-testid="sem-evidencias">
        Nenhuma evidência anexada.
      </div>
      <ul v-else class="grid grid-cols-1 sm:grid-cols-2 gap-3" data-testid="lista-evidencias">
        <li v-for="ev in evidencias" :key="ev.id_evidencia_ordem" class="bg-white border border-gray-200 rounded-xl overflow-hidden shadow-sm">
          <a v-if="ev.tipo_arquivo === 'IMAGEM'" :href="ev.url" target="_blank" rel="noopener">
            <img :src="ev.url" :alt="ev.nome_original" class="w-full h-40 object-cover" />
          </a>
          <video v-else :src="ev.url" controls preload="metadata" class="w-full h-40 bg-black"></video>
          <div class="p-3">
            <p class="text-xs font-bold text-gray-800 truncate" :title="ev.nome_original">#{{ ev.ordem }} · {{ ev.nome_original }}</p>
            <p class="text-[11px] text-gray-500 mt-0.5">
              {{ ev.enviado_por_nome || 'Participante' }} · {{ formatarDataHora(ev.dt_envio) }}
            </p>
          </div>
        </li>
      </ul>

      <div v-if="podeEnviar" class="border-t border-gray-100 pt-4 space-y-2">
        <label class="flex items-center justify-center gap-2 border-2 border-dashed border-gray-200 rounded-lg py-3 text-xs font-bold text-indigo-600 hover:bg-indigo-50 cursor-pointer">
          📎 Selecionar fotos ou vídeos
          <input type="file" :accept="ACCEPT_EVIDENCIAS" multiple class="hidden" :disabled="enviando" @change="aoEscolher" />
        </label>
        <p class="text-[11px] text-gray-500">{{ DESCRICAO_LIMITES }}</p>

        <ul v-if="selecionados.length" class="space-y-1">
          <li v-for="(arq, i) in selecionados" :key="arq.name + i" class="flex items-center justify-between bg-white border border-gray-100 rounded-lg px-3 py-1.5 text-xs text-gray-700">
            <span class="truncate pr-2">{{ arq.type.startsWith('video/') ? '🎞️' : '🖼️' }} {{ arq.name }}</span>
            <button type="button" @click="remover(i)" :disabled="enviando" class="text-red-500 font-bold cursor-pointer" :aria-label="`Remover ${arq.name}`">✕</button>
          </li>
        </ul>
        <p v-if="erroSelecao" role="alert" class="text-[11px] text-red-600 font-medium">{{ erroSelecao }}</p>

        <div class="flex justify-end">
          <button @click="enviar" :disabled="!selecionados.length || enviando"
            class="px-5 py-2 text-xs font-bold text-white bg-indigo-600 hover:bg-indigo-700 rounded-lg shadow-sm cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed">
            {{ enviando ? 'Enviando...' : 'Enviar evidências' }}
          </button>
        </div>
      </div>
      <p v-else-if="!somenteLeitura" class="text-[11px] text-gray-400 font-semibold border-t border-gray-100 pt-3">
        O envio de evidências não está disponível na etapa atual desta ordem.
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import Swal from 'sweetalert2'
import { EvidenciaError, enviarEvidencias, listarEvidencias } from '@/services/evidenciaService'
import type { EvidenciaOrdem } from '@/types/portal'
import { formatarDataHora } from '@/utils/statusOrdem'
import { ACCEPT_EVIDENCIAS, DESCRICAO_LIMITES, validarArquivosEvidencia } from '@/utils/validacaoEvidencia'

// somenteLeitura: perfis que apenas visualizam (técnico, gestor, gerente) não veem a área de envio nem o aviso de bloqueio.
const props = withDefaults(
  defineProps<{ idOrdem: number; podeEnviar?: boolean; somenteLeitura?: boolean }>(),
  { podeEnviar: false, somenteLeitura: false },
)

const evidencias = ref<EvidenciaOrdem[]>([])
const selecionados = ref<File[]>([])
const loading = ref(true)
const enviando = ref(false)
const erroCarga = ref('')
const erroSelecao = ref('')

async function carregar() {
  loading.value = true
  erroCarga.value = ''
  try {
    evidencias.value = await listarEvidencias(props.idOrdem)
  } catch (e) {
    console.error('Erro ao carregar evidências', e)
    evidencias.value = []
    erroCarga.value = 'Não foi possível carregar as evidências.'
  } finally {
    loading.value = false
  }
}

function aoEscolher(evento: Event) {
  const input = evento.target as HTMLInputElement
  const novos = [...selecionados.value, ...Array.from(input.files ?? [])]
  input.value = ''
  erroSelecao.value = validarArquivosEvidencia(novos, evidencias.value.length) ?? ''
  if (!erroSelecao.value) selecionados.value = novos
}

function remover(indice: number) {
  selecionados.value = selecionados.value.filter((_, i) => i !== indice)
  erroSelecao.value = ''
}

async function enviar() {
  if (enviando.value) return
  erroSelecao.value = validarArquivosEvidencia(selecionados.value, evidencias.value.length) ?? ''
  if (erroSelecao.value) return

  enviando.value = true
  try {
    await enviarEvidencias(props.idOrdem, selecionados.value)
    selecionados.value = []
    await carregar()
    Swal.fire({ title: 'Evidências enviadas!', icon: 'success', timer: 2000, showConfirmButton: false })
  } catch (e) {
    if (e instanceof EvidenciaError) {
      const titulos = { SEM_PERMISSAO: 'Sem permissão', STATUS_INVALIDO: 'Ação indisponível', ARQUIVO_INVALIDO: 'Arquivo recusado', GENERICO: 'Erro' }
      await Swal.fire({
        title: titulos[e.info.tipo],
        text: e.info.mensagem,
        icon: e.info.tipo === 'GENERICO' ? 'error' : 'info',
        confirmButtonColor: '#2563eb',
      })
      if (e.info.tipo === 'STATUS_INVALIDO' || e.info.tipo === 'SEM_PERMISSAO') selecionados.value = []
    } else {
      console.error('Erro ao enviar evidências', e)
      Swal.fire({ title: 'Erro', text: 'Não foi possível enviar as evidências. Tente novamente.', icon: 'error' })
    }
  } finally {
    enviando.value = false
  }
}

watch(() => props.idOrdem, () => { selecionados.value = []; erroSelecao.value = ''; carregar() })
onMounted(carregar)
</script>