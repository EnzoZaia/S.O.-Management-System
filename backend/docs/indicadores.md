# Indicadores do TechOrder: fórmulas

Este documento descreve como o backend calcula os indicadores. O código fica em `ordem_servico/indicadores.py`, `ordem_servico/acesso.py` e `ativo/saude.py`.

## Período (US16)

O período vale para todos os indicadores da mesma resposta.

Ele é informado de um destes jeitos:
- `?periodo=` com um dos valores abaixo;
- `?inicio=AAAA-MM-DD&fim=AAAA-MM-DD`, que inclui o dia final.

| Código | Intervalo |
|---|---|
| `30d` (padrão) | agora − 30 dias até agora |
| `mes_atual` | dia 1 do mês atual até agora |
| `mes_passado` | dia 1 do mês anterior até o dia 1 do mês atual |
| `ano` | 1º de janeiro do ano atual até agora |

Nas fórmulas abaixo:
- "abertas no período" significa `data_abertura` dentro do intervalo;
- "concluídas no período" significa status CONCLUIDA ou ENCERRADA com `data_conclusao` dentro do intervalo.

## Indicadores gerenciais globais (US16)

Endpoint: `GET /ordem-servico/indicadores-gerenciais/`. Acesso exclusivo do perfil GERENTE.

| Indicador | Fórmula |
|---|---|
| `volume_total` | quantidade de OS abertas no período (corretivas e preventivas) |
| `backlog_ativo` | OS hoje em status ativo (EM_TRIAGEM, APROVADA, ATRIBUIDA, EM_EXECUCAO, PAUSADA, AGUARDANDO_MATERIAL, AGUARDANDO_TERCEIRO, AGUARDANDO_VALIDACAO, REABERTA) abertas antes do fim do período |
| `total_solucionadas` | OS concluídas no período |
| `mttr_horas` | média de `data_conclusao − data_abertura`, em horas, das corretivas concluídas no período |
| `taxa_resolucao_primeira_intervencao` | corretivas concluídas no período sem retrabalho ÷ corretivas concluídas no período × 100 (definição de retrabalho abaixo) |
| `satisfacao_media` / `total_avaliacoes` | média e quantidade das notas (1 a 5) de `validacao_atendimento` registradas no período |
| `reincidencias` / `taxa_reincidencia` | corretivas abertas no período cujo ativo teve outra corretiva concluída (ou aberta, se ainda não concluída) menos de 15 dias antes; a taxa é o resultado ÷ corretivas abertas no período × 100 |
| `usuarios_afetados` | soma, nas OS abertas no período, do solicitante original mais os participantes (US05); cada pessoa conta uma vez por OS e o solicitante não é contado de novo como participante |
| `distribuicao_por_ativo` | top 10 ativos por quantidade de OS abertas no período |
| `distribuicao_por_localizacao` | top 10 salas por quantidade de OS abertas no período |
| `predios_mais_ocorrencias` | top 5 prédios por quantidade de OS abertas no período |
| `saude_ativos` | situação atual do Health Score (US17) de todos os ativos: quantidade por classificação e nota média; não depende do período |

Uma corretiva concluída tem **retrabalho** quando passou por pelo menos um destes casos:
- foi reprovada na validação (AGUARDANDO_VALIDACAO → EM_EXECUCAO no histórico);
- foi reaberta (status REABERTA).

Taxas sem denominador voltam `null`.

## Painel do gestor (US15)

Endpoint: `GET /ordem-servico/dashboard/indicadores/`. O cálculo é o mesmo do painel original, mas a base de OS vem do escopo do gestor.

Entram no escopo as OS:
- em que ele é o gestor da última atribuição;
- atribuídas a técnicos da equipe dele;
- em triagem (ABERTA ou REABERTA) ou REPROVADA cuja categoria é compatível com a área de atuação dele.

A **equipe** do gestor reúne:
- os técnicos com `tecnico.gestor_id` igual ao dele;
- os técnicos sem gestor cuja área é compatível com a dele.

A área `TODAS`, ou uma área vazia, é compatível com qualquer categoria.

O `rankingTecnicos` mostra apenas técnicos da equipe.

Gargalos (`gargalos`):

| Gargalo | Cálculo |
|---|---|
| `sem_triagem` | quantidade de OS em ABERTA mais REABERTA |
| `sem_tecnico` | quantidade de OS APROVADA ou ATRIBUIDA sem técnico |
| `aguardando_material` | quantidade de OS em AGUARDANDO_MATERIAL |
| `dependente_terceiro` | quantidade de OS em AGUARDANDO_TERCEIRO |

## Asset Health Score (US17)

Endpoints:
- `GET /ativo/<id>/saude/`;
- `GET /ativo/saude/`, que aceita `?predio=` e `?classificacao=` e ordena da pior nota para a melhor.

O cálculo é determinístico e não usa IA. Começa em 100 e o resultado fica limitado entre 0 e 100.

| Fator | Penalidade | Regra |
|---|---|---|
| `PREVENTIVA_ATRASADA` | −25 | `data_proxima_preventiva` anterior a hoje |
| `CORRETIVAS_RECENTES` | −10 por OS | corretivas CONCLUIDA ou ENCERRADA com `data_conclusao` nos últimos 60 dias |
| `REINCIDENCIA` | −15 por ocorrência | corretiva aberta menos de 15 dias depois da conclusão (ou abertura) de outra corretiva do mesmo ativo, considerando as abertas nos últimos 60 dias |
| `OCORRENCIA_URGENTE` | −20 (uma vez) | ao menos uma corretiva com prioridade URGENTE aberta nos últimos 30 dias |

Corretivas canceladas não entram em nenhum fator.

| Nota | Classificação |
|---|---|
| 80 a 100 | SAUDAVEL (Saudável) |
| 60 a 79 | ATENCAO (Atenção) |
| 40 a 59 | CRITICO (Crítico) |
| abaixo de 40 | MUITO_CRITICO (Muito Crítico) |

Os códigos são os mesmos do enum `classificacao_score` do banco.

## Programação de preventiva (US12)

**Intervalo padrão por tipo de ativo** (configurável por variável de ambiente):

| Tipo de ativo | Intervalo | Variável |
|---|---|---|
| AR_CONDICIONADO | 30 dias | `INTERVALO_PREVENTIVA_AR_CONDICIONADO_DIAS` |
| BEBEDOURO | 180 dias | `INTERVALO_PREVENTIVA_BEBEDOURO_DIAS` |
| demais tipos | 90 dias | `INTERVALO_PREVENTIVA_PADRAO_DIAS` |

**Próxima preventiva** = próximo dia útil a partir de (última preventiva concluída + intervalo). Fins de semana e feriados nacionais/SP são ignorados (`ativo/calendario_feriados.py`).

**Alerta de proximidade:** dispara quando uma corretiva é aberta para um ativo cuja preventiva está prevista para daqui a 0 a 7 dias. O limite é configurado em `DIAS_ALERTA_PREVENTIVA_PROXIMA`.
