import axios from 'axios'

const api = axios.create({
  baseURL: 'http://127.0.0.1:8000'
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Token salvo expirado/inválido: limpa a sessão e volta para o login em vez de deixar as telas vazias.
api.interceptors.response.use(
  (resposta) => resposta,
  (error) => {
    const enviouToken = !!error.config?.headers?.Authorization
    if (error.response?.status === 401 && enviouToken && error.response.data?.code === 'token_not_valid') {
      localStorage.removeItem('token')
      localStorage.removeItem('usuario')
      if (window.location.pathname !== '/') window.location.assign('/')
    }
    return Promise.reject(error)
  }
)

export default api
