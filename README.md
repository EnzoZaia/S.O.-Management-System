# TechOrder
### Sistema de Gestão de Ordens de Serviço de Manutenção

Projeto desenvolvido no **Projeto Interdisciplinar III – Sistemas de Informação (2026)** com o objetivo de criar uma plataforma web para **gestão inteligente de ordens de serviço de manutenção**, permitindo controle completo do ciclo de atendimento, desde a abertura da solicitação até a validação final do serviço executado.

---

# 📌 Visão Geral

O **TechOrder** é um sistema web que centraliza e organiza a gestão de solicitações de manutenção em ambientes institucionais ou organizacionais.

O sistema permite:

- Registrar solicitações de manutenção
- Classificar e priorizar ordens de serviço
- Encaminhar automaticamente demandas aos gestores responsáveis
- Atribuir atividades a técnicos
- Acompanhar o andamento da execução
- Monitorar dependências de materiais ou terceiros
- Validar a conclusão do serviço com o solicitante
- Gerar relatórios e indicadores gerenciais

A solução busca resolver problemas comuns em processos de manutenção descentralizados, como falta de rastreabilidade, dificuldade de priorização e ausência de indicadores confiáveis.

---

# 🚩 Problema que o Projeto Resolve

Em muitos ambientes organizacionais, o controle de ordens de serviço ocorre de forma:

- Descentralizada
- Baseada em planilhas ou comunicação informal
- Sem padronização de classificação
- Com pouca visibilidade do andamento das demandas

Isso gera problemas como:

- Ordens sem priorização adequada
- Encaminhamento incorreto para equipes
- Retrabalho
- Atrasos por falta de acompanhamento de materiais
- Baixa visibilidade da produtividade das equipes técnicas

O **TechOrder** surge como uma solução para **centralizar, padronizar e monitorar todo o processo de manutenção**.

---

# 🎯 Objetivos do Sistema

O objetivo principal do projeto é desenvolver um **sistema web de gestão de ordens de serviço** capaz de:

- Centralizar solicitações de manutenção
- Organizar o fluxo operacional de atendimento
- Automatizar o direcionamento de demandas
- Monitorar execução e dependências
- Registrar histórico completo das atividades
- Gerar indicadores de desempenho

Ao final do projeto, espera-se disponibilizar um sistema que ofereça **maior controle operacional, rastreabilidade e suporte à tomada de decisão gerencial**.

---

# ⚙️ Funcionalidades Principais

## Cadastro e abertura de ordens de serviço

- Registro de solicitações com descrição do problema
- Classificação por tipo de serviço
- Indicação de local, prédio e departamento
- Identificação do solicitante

## Classificação e roteamento

Classificação por natureza do serviço:
- Preventiva
- Corretiva
- Preditiva
- Melhoria

Definição de prioridade:
- Emergência
- Urgente
- Programada
- Planejada

Direcionamento automático para gestores responsáveis.

---

## Gestão do ciclo de vida da ordem

O sistema controla diferentes **status da ordem de serviço**:
- Solicitada
- Aprovada
- Aguardando peças
- Aguardando terceiro
- Concluída
- Reprovada

Também registra **histórico completo de movimentações**.

---

## Gestão da execução

Os técnicos podem:
- Registrar início e término da execução
- Inserir observações técnicas
- Anexar evidências
- Atualizar o andamento da atividade

---

## Validação da conclusão

Após a execução:
1. A ordem é enviada ao solicitante
2. O solicitante valida ou rejeita o serviço
3. Caso rejeitado, a ordem retorna ao técnico responsável

Isso garante **controle real da conclusão do serviço**.

---

## Monitoramento de materiais e terceiros

O sistema permite marcar ordens como:
- Aguardando material
- Aguardando fornecedor
- Aguardando empresa terceirizada

Além disso, registra o **tempo de espera em cada situação**.

---

# 📊 Indicadores e Relatórios

O sistema gera indicadores como:
- Técnico com mais ordens abertas
- Ordens concluídas por semana
- Ordens concluídas por mês
- Ordens aguardando material
- Ordens aguardando terceiros
- Prédio com maior número de manutenções
- Tempo médio de atendimento
- Tempo médio por status
- Relatórios gráficos de desempenho operacional

Esses indicadores auxiliam na **gestão da produtividade e eficiência operacional**.

---

# 👥 Perfis de Usuário

O sistema possui diferentes níveis de acesso.

### Solicitante
- Abrir ordem de serviço
- Validar conclusão do serviço

### Técnico
- Visualizar ordens atribuídas
- Registrar execução
- Concluir atividades

### Gestor / Supervisor
- Classificar prioridades
- Aprovar e redistribuir ordens
- Atribuir técnicos
- Acompanhar indicadores

### Gerente de Projeto
- Acesso completo ao sistema

### Administrador
- Gestão de usuários
- Parametrizações do sistema

---

# 🏗 Arquitetura do Sistema

O projeto segue uma arquitetura baseada em **aplicação web com API REST**, organizada de forma modular e versionada utilizando Git.

## Tecnologias utilizadas

### Backend
- Python
- Django

### Frontend (Este repositório)
- Vue.js 3
- Tailwind CSS 4
- Vite

### Banco de Dados
- Supabase

### Ferramentas
- Git / GitHub
- GitHub Projects (gestão do projeto)
- Postman (testes de API)

---

# 🔧 Instruções Técnicas do Front-end

Essas instruções são baseadas na estrutura Vue 3 + Vite.

### Pré-requisitos
- [Node.js](https://nodejs.org/) (versão LTS recomendada)

### Project Setup
Instalar dependências:
```sh
npm install
```

---

# 👨‍💻 Equipe do Projeto

Projeto desenvolvido pelos alunos do curso de **Sistemas de Informação – FHO**

- Arthur Peixoto Lacerda (Banco de Dados)
- Enzo Zaia Soares (Front-end)
- Guilherme Henrique Cavarsan (Back-End)
- Octavio Thim Dias (Engenheiro de Software)
- Rodolfo Henrique Ribeiro Zanchetta (Scrum master)
