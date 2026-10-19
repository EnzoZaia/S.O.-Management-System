<template>
  <div class="w-full animate-fade-in bg-white p-5 rounded-xl border border-gray-200 shadow-sm" data-testid="form-conclusao">
    <h3 class="text-sm font-bold text-gray-800 mb-4 flex items-center gap-2"><span>📝</span> Relatório de Conclusão</h3>

    <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
      <div class="space-y-1.5">
        <label class="text-[11px] font-bold text-gray-500 uppercase tracking-wider">O que foi consertado? *</label>
        <select v-model="form.tipoEquipamento" @change="aoTrocarTipo"
          :class="erros.equipamento ? 'border-red-500' : 'border-gray-200'"
          class="w-full bg-gray-50 border text-gray-700 text-sm font-bold rounded-lg px-3 py-2.5 outline-none focus:ring-2 focus:ring-emerald-500 cursor-pointer">
          <option value="" disabled>Selecione...</option>
          <option value="AR_CONDICIONADO">❄️ Ar Condicionado</option>
          <option value="OUTROS">🔧 Outros Equipamentos / Geral</option>
        </select>
      </div>

      <div v-if="form.tipoEquipamento === 'AR_CONDICIONADO'" class="space-y-1.5">
        <label class="text-[11px] font-bold text-emerald-600 uppercase tracking-wider">Qual Ar Condicionado? *</label>
        <select v-model="form.patrimonio" @change="erros = { ...erros, equipamento: undefined }"
          :class="erros.equipamento ? 'border-red-500' : 'border-emerald-200'"
          class="w-full bg-emerald-50/30 border text-gray-800 text-sm font-bold rounded-lg px-3 py-2.5 outline-none focus:ring-2 focus:ring-emerald-500 cursor-pointer">
          <option value="" disabled>{{ ativos.length ? 'Selecione o equipamento...' : 'Nenhum ar-condicionado cadastrado' }}</option>
          <option v-for="a in ativos" :key="a.codigo_patrimonial" :value="a.codigo_patrimonial">{{ a.nomeLimpo }}</option>
        </select>
      </div>
    </div>
    <p v-if="erros.equipamento" role="alert" class="text-[11px] font-medium text-red-600 -mt-2 mb-3">{{ erros.equipamento }}</p>

    <div class="space-y-1.5 mb-4">
      <label for="obs-tecnica" class="text-[11px] font-bold text-gray-500 uppercase tracking-wider">Observação técnica *</label>
      <textarea id="obs-tecnica" v-model="form.observacao" @blur="validarCampo('observacao')" rows="3" :maxlength="OBSERVACAO_MAX"
        placeholder="Descreva o que foi feito..."
        :class="erros.observacao ? 'border-red-500 focus:ring-red-400' : 'border-gray-200 focus:ring-emerald-500'"
        class="w-full bg-gray-50 border text-gray-700 text-sm rounded-lg p-3 outline-none focus:ring-2 resize-none"></textarea>
      <div class="flex justify-between text-[11px]">
        <span class="text-red-600 font-medium">{{ erros.observacao }}</span>
        <span class="text-gray-400 font-semibold">{{ form.observacao.trim().length }}/{{ OBSERVACAO_MAX }}</span>
      </div>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
      <div v-if="exigirCausaRaiz" class="space-y-1.5">
        <label class="text-[11px] font-bold text-gray-500 uppercase tracking-wider">Causa raiz *</label>
        <select v-model="form.causaRaiz" @change="erros = { ...erros, causaRaiz: undefined }"
          :class="erros.causaRaiz ? 'border-red-500' : 'border-gray-200'"
          class="w-full bg-gray-50 border text-gray-700 text-sm font-bold rounded-lg px-3 py-2.5 outline-none focus:ring-2 focus:ring-emerald-500 cursor-pointer">
          <option value="" disabled>Selecione...</option>
          <option v-for="c in CAUSAS_RAIZ" :key="c.valor" :value="c.valor">{{ c.rotulo }}</option>
        </select>
        <p v-if="erros.causaRaiz" role="alert" class="text-[11px] font-medium text-red-600">{{ erros.causaRaiz }}</p>
      </div>

      <div class="space-y-1.5">
        <label for="dt-final" class="text-[11px] font-bold text-gray-500 uppercase tracking-wider">Data e hora final *</label>
        <input id="dt-final" v-model="form.dataHoraFinal" type="datetime-local" :max="agoraParaInput()"
          @change="erros = { ...erros, dataHoraFinal: undefined }"
          :class="erros.dataHoraFinal ? 'border-red-500' : 'border-gray-200'"
          class="w-full bg-gray-50 border text-gray-700 text-sm font-bold rounded-lg px-3 py-2.5 outline-none focus:ring-2 focus:ring-emerald-500" />
        <p v-if="erros.dataHoraFinal" role="alert" class="text-[11px] font-medium text-red-600">{{ erros.dataHoraFinal }}</p>
      </div>
    </div>

    <div v-if="exigirCausaRaiz && form.causaRaiz === 'OUTRA'" class="space-y-1.5 mb-4">
      <label for="causa-detalhe" class="text-[11px] font-bold text-gray-500 uppercase tracking-wider">Descreva a causa raiz *</label>
      <input id="causa-detalhe" v-model="form.causaDetalhe" type="text" :maxlength="CAUSA_DETALHE_MAX" @blur="validarCampo('causaDetalhe')"
        :class="erros.causaDetalhe ? 'border-red-500' : 'border-gray-200'"
        class="w-full bg-gray-50 border text-gray-700 text-sm rounded-lg px-3 py-2.5 outline-none focus:ring-2 focus:ring-emerald-500" />
      <p v-if="erros.causaDetalhe" role="alert" class="text-[11px] font-medium text-red-600">{{ erros.causaDetalhe }}</p>
    </div>

    <div class="space-y-2 mb-5">
      <div class="flex items-center justify-between">
        <label class="text-[11px] font-bold text-gray-500 uppercase tracking-wider">Insumos extraordinários (opcional)</label>
        <button type="button" @click="adicionarInsumo" :disabled="form.insumos.length >= INSUMOS_MAX"
          class="text-xs font-bold text-indigo-600 hover:text-indigo-800 cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed">+ Adicionar insumo</button>
      </div>
      <div v-for="(ins, i) in form.insumos" :key="i" class="flex items-center gap-2">
        <input v-model="ins.descricao" type="text" placeholder="Ex: Capacitor 35µF" :aria-label="`Insumo ${i + 1}`"
          class="flex-1 bg-gray-50 border border-gray-200 text-gray-700 text-sm rounded-lg px-3 py-2 outline-none focus:ring-2 focus:ring-emerald-500" />
        <input v-model="ins.quantidade" type="text" placeholder="Qtd" :aria-label="`Quantidade do insumo ${i + 1}`"
          class="w-20 bg-gray-50 border border-gray-200 text-gray-700 text-sm rounded-lg px-3 py-2 outline-none focus:ring-2 focus:ring-emerald-500" />
        <button type="button" @click="removerInsumo(i)" class="text-red-500 font-bold cursor-pointer" :aria-label="`Remover insumo ${i + 1}`">✕</button>
      </div>
      <p v-if="erros.insumos" role="alert" class="text-[11px] font-medium text-red-600">{{ erros.insumos }}</p>
    </div>

    <div class="bg-blue-50 border border-blue-100 rounded-xl p-3 text-xs text-blue-800 font-semibold mb-4" v-if="exigirCausaRaiz">
      Ao concluir, a ordem segue para validação do solicitante. O técnico não encerra diretamente uma corretiva.
    </div>

    <div class="flex justify-end gap-3 pt-4 border-t border-gray-100">
      <button @click="emit('cancelar')" :disabled="enviando"
        class="px-5 py-2.5 text-sm font-bold text-gray-600 bg-white border border-gray-200 hover:bg-gray-100 rounded-xl cursor-pointer disabled:opacity-50">Voltar</button>
      <button @click="confirmar" :disabled="enviando"
        class="px-5 py-2.5 text-sm font-bold text-white bg-emerald-600 hover:bg-emerald-700 rounded-xl shadow-sm cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2">
        <span>💾</span> {{ enviando ? 'Salvando...' : 'Confirmar conclusão' }}
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import type { AtivoOpcao, CampoConclusao, DadosConclusao, ErrosConclusao, FormularioConclusao } from '@/types/execucao'
import {
  CAUSAS_RAIZ, CAUSA_DETALHE_MAX, INSUMOS_MAX, OBSERVACAO_MAX,
  agoraParaInput, montarDadosConclusao, validarConclusao,
} from '@/utils/validacaoExecucao'

const props = defineProps<{
  ativos: AtivoOpcao[]
  inicioExecucao: string | null
  enviando: boolean
  exigirCausaRaiz: boolean
  errosServidor?: ErrosConclusao
}>()
const emit = defineEmits<{
  (e: 'cancelar'): void
  (e: 'confirmar', dados: DadosConclusao): void
}>()

const form = ref<FormularioConclusao>({
  tipoEquipamento: '',
  patrimonio: '',
  observacao: '',
  causaRaiz: '',
  causaDetalhe: '',
  dataHoraFinal: agoraParaInput(),
  insumos: [],
})
const erros = ref<ErrosConclusao>({})

watch(() => props.errosServidor, (novos) => { if (novos) erros.value = { ...erros.value, ...novos } })

function opcoes() {
  return { exigirCausaRaiz: props.exigirCausaRaiz, inicioExecucao: props.inicioExecucao }
}

function aoTrocarTipo() {
  form.value.patrimonio = ''
  erros.value = { ...erros.value, equipamento: undefined }
}

function validarCampo(campo: CampoConclusao) {
  erros.value = { ...erros.value, [campo]: validarConclusao(form.value, opcoes())[campo] }
}

function adicionarInsumo() {
  if (form.value.insumos.length < INSUMOS_MAX) form.value.insumos.push({ descricao: '', quantidade: '' })
}

function removerInsumo(indice: number) {
  form.value.insumos = form.value.insumos.filter((_, i) => i !== indice)
  erros.value = { ...erros.value, insumos: undefined }
}

function confirmar() {
  erros.value = validarConclusao(form.value, opcoes()) // CA3
  if (Object.values(erros.value).some(Boolean)) return
  emit('confirmar', montarDadosConclusao(form.value, props.ativos))
}
</script>