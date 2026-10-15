export const EVIDENCIAS_POR_ENVIO_MAX = 5
export const EVIDENCIAS_TOTAL_MAX = 10
export const IMAGEM_TAMANHO_MAX_MB = 5
export const VIDEO_TAMANHO_MAX_MB = 30

export const TIPOS_IMAGEM = ['image/jpeg', 'image/png', 'image/webp']
export const TIPOS_VIDEO = ['video/mp4', 'video/webm', 'video/quicktime']
export const ACCEPT_EVIDENCIAS = [...TIPOS_IMAGEM, ...TIPOS_VIDEO].join(',')

export const DESCRICAO_LIMITES =
  `Fotos (JPG, PNG, WEBP) até ${IMAGEM_TAMANHO_MAX_MB} MB e vídeos curtos (MP4, WEBM, MOV) até ${VIDEO_TAMANHO_MAX_MB} MB. ` +
  `Até ${EVIDENCIAS_POR_ENVIO_MAX} arquivos por envio e ${EVIDENCIAS_TOTAL_MAX} por ordem.`

const MB = 1024 * 1024

// CA2: valida formato, tamanho e quantidade antes de enviar.
export function validarArquivosEvidencia(arquivos: File[], jaEnviadas: number): string | null {
  if (arquivos.length === 0) return 'Selecione ao menos um arquivo.'
  if (arquivos.length > EVIDENCIAS_POR_ENVIO_MAX) {
    return `Envie no máximo ${EVIDENCIAS_POR_ENVIO_MAX} arquivos por vez.`
  }
  if (jaEnviadas + arquivos.length > EVIDENCIAS_TOTAL_MAX) {
    return `Esta ordem aceita no máximo ${EVIDENCIAS_TOTAL_MAX} evidências (já há ${jaEnviadas}).`
  }
  for (const arq of arquivos) {
    const imagem = TIPOS_IMAGEM.includes(arq.type)
    const video = TIPOS_VIDEO.includes(arq.type)
    if (!imagem && !video) return `"${arq.name}" não é um formato permitido. ${DESCRICAO_LIMITES}`
    const limite = imagem ? IMAGEM_TAMANHO_MAX_MB : VIDEO_TAMANHO_MAX_MB
    if (arq.size > limite * MB) return `"${arq.name}" passa de ${limite} MB.`
  }
  return null
}