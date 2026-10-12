import type { ErrosCadastro, FormularioCadastro } from '@/types/cadastro'

export const DOMINIOS_EMAIL_PERMITIDOS = ['@gmail.com', '@fho.edu.br'] as const
export const SENHA_TAMANHO_MINIMO = 8

const REGEX_EMAIL = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

export function normalizarEmail(email: string): string {
  return email.trim().toLowerCase()
}

export function validarEmail(email: string): string | null {
  const valor = normalizarEmail(email)
  if (!valor) return 'O e-mail é obrigatório.'
  if (!REGEX_EMAIL.test(valor)) return 'Informe um e-mail válido.'
  if (!DOMINIOS_EMAIL_PERMITIDOS.some((dominio) => valor.endsWith(dominio))) {
    return `Use um e-mail com um dos domínios: ${DOMINIOS_EMAIL_PERMITIDOS.join(', ')}.`
  }
  return null
}

export function validarCadastro(form: FormularioCadastro): ErrosCadastro {
  const erros: ErrosCadastro = {}

  if (!form.nome.trim()) erros.nome = 'O nome completo é obrigatório.'
  else if (form.nome.trim().split(/\s+/).length < 2) erros.nome = 'Informe o nome completo (nome e sobrenome).'

  const erroEmail = validarEmail(form.email)
  if (erroEmail) erros.email = erroEmail

  if (!form.senha) erros.senha = 'A senha é obrigatória.'
  else if (form.senha.length < SENHA_TAMANHO_MINIMO) {
    erros.senha = `A senha deve ter pelo menos ${SENHA_TAMANHO_MINIMO} caracteres.`
  }

  if (!form.confirmarSenha) erros.confirmarSenha = 'Confirme a senha.'
  else if (form.senha !== form.confirmarSenha) erros.confirmarSenha = 'As senhas não coincidem.'

  return erros
}