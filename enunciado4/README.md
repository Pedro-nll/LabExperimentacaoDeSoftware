# Laboratório 04 — Visualização de Dados com Python

Este repositório contém os dados e scripts necessários para construir dashboards e visualizações para o trabalho de TIS 6 / Laboratório de Experimentação de Software.

O estudo investiga a presença e o impacto de políticas de uso de Inteligência Artificial em repositórios open-source populares do GitHub. A análise busca compreender:

1. O nível de adoção dessas políticas;
2. Os tipos de políticas que emergem a partir da clusterização textual;
3. A relação entre políticas de IA e métricas de engajamento;
4. A relação entre políticas de IA e métricas de colaboração, responsividade e eficiência do fluxo de contribuição.

Embora o enunciado original do Lab04 sugira ferramentas como Power BI, Tableau ou Looker Studio, este projeto utilizará Python para gerar dashboards, gráficos e artefatos de visualização reprodutíveis.

---

## 1. Objetivo do Dashboard

O dashboard deve apresentar, de forma clara e autoexplicativa, os resultados do estudo sobre políticas de IA em projetos open-source.

A estrutura esperada é:

1. Caracterização do dataset;
2. Visualizações para a RQ1;
3. Visualizações para a RQ2;
4. Visualizações para a RQ3;
5. Síntese final com os principais achados.

Cada visualização deve conter:

- Título claro;
- Eixos com labels descritivas;
- Indicação da métrica representada;
- Preferência por mediana quando a distribuição for assimétrica;
- Comparações entre grupos com e sem política de IA;
- Comparações entre clusters de políticas, quando aplicável;
- Texto interpretativo curto explicando o que o gráfico mostra.

---

## 2. Estrutura dos Dados

Os dados estão organizados da seguinte forma:

```text
enunciado4/
├── data/
│   ├── clusters/
│   │   ├── cluster_0.csv
│   │   ├── cluster_1.csv
│   │   ├── cluster_2.csv
│   │   ├── cluster_summary.csv
│   │   └── repos_com_politica_1000.csv
│   │
│   ├── tables/
│   │   ├── rq1_adoption_summary.csv
│   │   ├── rq1_cluster_summary.csv
│   │   ├── rq1_policy_file_distribution.csv
│   │   ├── rq1_repository_policy_summary.csv
│   │   ├── rq2_engagement_by_cluster.csv
│   │   ├── rq2_engagement_by_policy_presence.csv
│   │   ├── rq3_collaboration_by_cluster.csv
│   │   └── rq3_collaboration_by_policy_presence.csv
│   │
│   └── top_repos_filtered.csv
```

## 3. Descrição dos Arquivos e Modelos de Dados

Esta seção descreve os arquivos atualmente disponíveis em `data/` e `data/tables/`, com base nas colunas reais dos CSVs já presentes no projeto.

---

### 3.1. `data/top_repos_filtered.csv`

Arquivo com os 1000 repositórios open-source selecionados para o estudo.

#### Colunas

| Coluna | Descrição |
|---|---|
| `repo_name` | Nome completo do repositório no formato `owner/repository` |
| `link` | URL do repositório no GitHub |
| `stars` | Número de estrelas do repositório |
| `most_recent_activity` | Data/hora da atividade mais recente identificada |
| `age_days` | Idade do repositório em dias |

#### Uso no dashboard

Este arquivo deve ser usado para a **caracterização geral do dataset**.

Visualizações recomendadas:

- Card com total de repositórios analisados;
- Distribuição de estrelas dos repositórios;
- Distribuição da idade dos repositórios;
- Distribuição da atividade recente;
- Ranking dos repositórios mais populares por estrelas;
- Relação entre idade do repositório e número de estrelas.

#### Gráficos sugeridos

1. **Histograma de estrelas**
   - Eixo X: `stars`
   - Eixo Y: quantidade de repositórios
   - Usar escala logarítmica se a distribuição estiver muito assimétrica.

2. **Histograma de idade dos repositórios**
   - Eixo X: `age_days`
   - Eixo Y: quantidade de repositórios.

3. **Scatter plot: idade vs. estrelas**
   - Eixo X: `age_days`
   - Eixo Y: `stars`
   - Objetivo: observar se projetos mais antigos tendem a concentrar mais estrelas.

4. **Tabela dos top repositórios**
   - Colunas: `repo_name`, `stars`, `age_days`, `most_recent_activity`.

---

### 3.2. `data/tables/rq1_adoption_summary.csv`

Arquivo com o resumo de adoção de políticas de IA nos repositórios analisados.

#### Colunas

| Coluna | Descrição |
|---|---|
| `metric` | Nome da métrica calculada |
| `value` | Valor da métrica |

#### Métricas presentes

| Métrica | Interpretação |
|---|---|
| `total_repositories` | Total de repositórios analisados |
| `repositories_with_policy` | Quantidade de repositórios com política de IA |
| `repositories_without_policy` | Quantidade de repositórios sem política de IA |
| `policy_adoption_percentage` | Percentual de repositórios com política de IA |
| `no_policy_percentage` | Percentual de repositórios sem política de IA |

No dataset atual, foram analisados 1000 repositórios. Destes, 125 possuem política de IA identificada, representando 12,5% da amostra. Os outros 875 repositórios, equivalentes a 87,5%, não possuem política de IA identificada.

#### Uso no dashboard

Este arquivo responde diretamente à primeira parte da RQ1: o nível de adoção de políticas de IA.

Visualizações recomendadas:

1. **Cards de KPI**
   - Total de repositórios;
   - Repositórios com política de IA;
   - Repositórios sem política de IA;
   - Percentual de adoção.

2. **Gráfico de barras: adoção de política**
   - Categorias:
     - Com política de IA;
     - Sem política de IA.
   - Valores:
     - Quantidade de repositórios.

3. **Barra percentual empilhada**
   - Mostrar a proporção entre repositórios com e sem política.

#### Interpretação esperada

A visualização deve deixar claro que a adoção de políticas de IA ainda é minoritária entre os repositórios open-source populares analisados. Mesmo entre projetos populares, apenas uma pequena parcela documenta explicitamente regras ou orientações sobre o uso de IA.

---

### 3.3. `data/tables/rq1_cluster_summary.csv`

Arquivo com o resumo dos clusters identificados entre os repositórios com política de IA.

#### Colunas

| Coluna | Descrição |
|---|---|
| `cluster` | Identificador numérico do cluster |
| `cluster_label` | Nome interpretativo atribuído ao cluster |
| `unique_repositories` | Quantidade de repositórios únicos no cluster |
| `policy_mentions` | Quantidade de menções de política no cluster |
| `percentage_of_policy_repositories` | Percentual dos repositórios com política pertencentes ao cluster |
| `median_policy_words` | Mediana de palavras nos textos de política do cluster |
| `mean_policy_words` | Média de palavras nos textos de política do cluster |

#### Clusters atuais

| Cluster | Label | Repositórios únicos | Percentual |
|---:|---|---:|---:|
| 0 | Governança ampla do uso de IA | 94 | 75,2% |
| 1 | Responsabilidade humana sobre contribuições assistidas por IA | 15 | 12,0% |
| 2 | Declaração obrigatória do uso de IA | 16 | 12,8% |

#### Uso no dashboard

Este arquivo responde à segunda parte da RQ1: quais tipos de política emergem.

Visualizações recomendadas:

1. **Gráfico de barras por cluster**
   - Eixo X: `cluster_label`
   - Eixo Y: `unique_repositories`
   - Objetivo: mostrar qual tipo de política é mais frequente.

2. **Gráfico percentual por cluster**
   - Eixo X: `cluster_label`
   - Eixo Y: `percentage_of_policy_repositories`
   - Objetivo: mostrar a proporção de cada tipo entre os repositórios com política.

3. **Comparação do tamanho dos textos por cluster**
   - Métricas:
     - `median_policy_words`
     - `mean_policy_words`
   - Objetivo: verificar se certos tipos de política tendem a ser mais detalhados.

4. **Tabela interpretativa dos clusters**
   - Cluster;
   - Label;
   - Quantidade de repositórios;
   - Percentual;
   - Mediana de palavras.

#### Interpretação esperada

O cluster mais frequente é o de **Governança ampla do uso de IA**, representando 75,2% dos repositórios com política. Isso indica que, quando políticas existem, elas tendem a ser mais gerais e abrangentes, em vez de focarem apenas em obrigações específicas, como declaração explícita do uso de IA.

---

### 3.4. `data/tables/rq2_engagement_by_policy_presence.csv`

Arquivo com métricas de engajamento agrupadas pela presença ou ausência de política de IA.

#### Colunas de identificação

| Coluna | Descrição |
|---|---|
| `has_ai_policy` | Grupo analisado: `With AI Policy` ou `Without AI Policy` |
| `n_repositories` | Número de repositórios no grupo |

#### Métricas de Pull Requests

| Coluna | Descrição |
|---|---|
| `prs_total_mean` | Média de PRs totais por grupo |
| `prs_total_median` | Mediana de PRs totais por grupo |
| `prs_opened_mean` | Média de PRs abertas |
| `prs_opened_median` | Mediana de PRs abertas |
| `prs_merged_mean` | Média de PRs mergeadas |
| `prs_merged_median` | Mediana de PRs mergeadas |
| `prs_closed_mean` | Média de PRs fechadas |
| `prs_closed_median` | Mediana de PRs fechadas |

#### Métricas de Issues

| Coluna | Descrição |
|---|---|
| `issues_total_mean` | Média de issues totais |
| `issues_total_median` | Mediana de issues totais |
| `issues_opened_mean` | Média de issues abertas |
| `issues_opened_median` | Mediana de issues abertas |
| `issues_closed_mean` | Média de issues fechadas |
| `issues_closed_median` | Mediana de issues fechadas |

#### Métricas de engajamento

| Coluna | Descrição |
|---|---|
| `unique_collaborators_mean` | Média de colaboradores únicos |
| `unique_collaborators_median` | Mediana de colaboradores únicos |
| `avg_pr_comments_mean` | Média de comentários por PR |
| `avg_pr_comments_median` | Mediana de comentários por PR |
| `avg_issue_comments_mean` | Média de comentários por issue |
| `avg_issue_comments_median` | Mediana de comentários por issue |
| `avg_pr_reviews_mean` | Média de reviews por PR |
| `avg_pr_reviews_median` | Mediana de reviews por PR |

#### Uso no dashboard

Este arquivo deve responder à RQ2 no nível de comparação entre:

- Repositórios com política de IA;
- Repositórios sem política de IA.

#### Visualizações recomendadas

Para a RQ2, o dashboard deve priorizar medianas, pois métricas de GitHub costumam ter distribuições muito assimétricas.

1. **PRs totais por presença de política**
   - Eixo X: `has_ai_policy`
   - Eixo Y: `prs_total_median`
   - Interpretação: comparar volume típico de contribuições via PR.

2. **PRs mergeadas por presença de política**
   - Eixo X: `has_ai_policy`
   - Eixo Y: `prs_merged_median`
   - Interpretação: comparar volume típico de contribuições aceitas.

3. **Issues totais por presença de política**
   - Eixo X: `has_ai_policy`
   - Eixo Y: `issues_total_median`
   - Interpretação: comparar volume típico de discussões, bugs ou solicitações.

4. **Colaboradores únicos por presença de política**
   - Eixo X: `has_ai_policy`
   - Eixo Y: `unique_collaborators_median`
   - Interpretação: comparar o tamanho típico da comunidade colaboradora.

5. **Comentários por PR**
   - Eixo X: `has_ai_policy`
   - Eixo Y: `avg_pr_comments_median`
   - Interpretação: observar se PRs em projetos com política geram mais discussão.

6. **Comentários por issue**
   - Eixo X: `has_ai_policy`
   - Eixo Y: `avg_issue_comments_median`
   - Interpretação: observar se issues em projetos com política têm mais interação.

7. **Reviews por PR**
   - Eixo X: `has_ai_policy`
   - Eixo Y: `avg_pr_reviews_median`
   - Interpretação: observar se projetos com política passam por processos de revisão mais intensos.

#### Valores observados no dataset atual

Algumas diferenças relevantes observadas:

| Métrica | Sem política | Com política |
|---|---:|---:|
| Mediana de PRs totais | 1405,5 | 5908,5 |
| Mediana de PRs mergeadas | 885,5 | 4018,5 |
| Mediana de issues fechadas | 1670,0 | 3680,5 |
| Mediana de colaboradores únicos | 91,0 | 97,5 |
| Mediana de comentários por PR | 1,440 | 2,032 |
| Mediana de comentários por issue | 3,140 | 4,109 |
| Mediana de reviews por PR | 0,589 | 1,314 |

#### Interpretação esperada

Os repositórios com política de IA apresentam medianas maiores em PRs totais, PRs mergeadas, issues fechadas, comentários e reviews. Isso sugere uma associação entre presença de política de IA e maior engajamento nos projetos analisados.

No entanto, essa interpretação deve ser feita com cuidado. A presença de política pode estar associada a projetos maiores, mais maduros ou mais organizados, e não necessariamente ser a causa direta do maior engajamento.

---

### 3.5. `data/tables/rq3_collaboration_by_policy_presence.csv`

Arquivo com métricas de colaboração, responsividade e eficiência agrupadas pela presença ou ausência de política de IA.

#### Colunas de identificação

| Coluna | Descrição |
|---|---|
| `has_ai_policy` | Grupo analisado: `With AI Policy` ou `Without AI Policy` |
| `n_repositories` | Número de repositórios no grupo |

#### Métricas de eficiência do fluxo

| Coluna | Descrição |
|---|---|
| `prs_merge_rate_mean` | Média da taxa de merge de PRs |
| `prs_merge_rate_median` | Mediana da taxa de merge de PRs |
| `prs_closed_no_merge_rate_mean` | Média da taxa de PRs fechadas sem merge |
| `prs_closed_no_merge_rate_median` | Mediana da taxa de PRs fechadas sem merge |
| `median_pr_cycle_hours_mean` | Média da mediana do tempo de ciclo dos PRs, em horas |
| `median_pr_cycle_hours_median` | Mediana do tempo de ciclo dos PRs, em horas |
| `mean_pr_cycle_hours_mean` | Média do tempo médio de ciclo dos PRs, em horas |
| `mean_pr_cycle_hours_median` | Mediana do tempo médio de ciclo dos PRs, em horas |

#### Métricas de responsividade

| Coluna | Descrição |
|---|---|
| `median_issue_first_response_hours_mean` | Média da mediana do tempo até primeira resposta em issues |
| `median_issue_first_response_hours_median` | Mediana do tempo até primeira resposta em issues |
| `median_pr_first_response_hours_mean` | Média da mediana do tempo até primeira resposta em PRs |
| `median_pr_first_response_hours_median` | Mediana do tempo até primeira resposta em PRs |
| `median_pr_first_review_hours_mean` | Média da mediana do tempo até primeira revisão em PRs |
| `median_pr_first_review_hours_median` | Mediana do tempo até primeira revisão em PRs |

#### Métricas de estabilidade do processo

| Coluna | Descrição |
|---|---|
| `avg_pr_commits_mean` | Média de commits por PR |
| `avg_pr_commits_median` | Mediana de commits por PR |
| `avg_pr_reviews_mean` | Média de reviews por PR |
| `avg_pr_reviews_median` | Mediana de reviews por PR |
| `avg_reviews_until_approval_mean` | Média de reviews até aprovação |
| `avg_reviews_until_approval_median` | Mediana de reviews até aprovação |

#### Uso no dashboard

Este arquivo deve responder à RQ3 no nível de comparação entre:

- Repositórios com política de IA;
- Repositórios sem política de IA.

#### Visualizações recomendadas

1. **Taxa de merge de PRs**
   - Eixo X: `has_ai_policy`
   - Eixo Y: `prs_merge_rate_median`
   - Unidade: percentual.
   - Interpretação: comparar a eficiência de aceitação de PRs.

2. **Taxa de fechamento sem merge**
   - Eixo X: `has_ai_policy`
   - Eixo Y: `prs_closed_no_merge_rate_median`
   - Unidade: percentual.
   - Interpretação: observar se projetos com política rejeitam ou fecham menos PRs sem merge.

3. **Tempo de ciclo de PR**
   - Eixo X: `has_ai_policy`
   - Eixo Y: `median_pr_cycle_hours_median`
   - Unidade: horas ou dias.
   - Recomendação: converter horas para dias no gráfico.

4. **Tempo até primeira resposta em issues**
   - Eixo X: `has_ai_policy`
   - Eixo Y: `median_issue_first_response_hours_median`
   - Unidade: horas ou dias.

5. **Tempo até primeira resposta em PRs**
   - Eixo X: `has_ai_policy`
   - Eixo Y: `median_pr_first_response_hours_median`
   - Unidade: horas ou dias.

6. **Tempo até primeira revisão em PRs**
   - Eixo X: `has_ai_policy`
   - Eixo Y: `median_pr_first_review_hours_median`
   - Unidade: horas ou dias.

7. **Commits por PR**
   - Eixo X: `has_ai_policy`
   - Eixo Y: `avg_pr_commits_median`.

8. **Reviews até aprovação**
   - Eixo X: `has_ai_policy`
   - Eixo Y: `avg_reviews_until_approval_median`.

#### Valores observados no dataset atual

| Métrica | Sem política | Com política |
|---|---:|---:|
| Mediana da taxa de merge | 69,608% | 75,267% |
| Mediana da taxa de fechamento sem merge | 25,155% | 21,472% |
| Mediana do ciclo de PR | 20,450 h | 16,927 h |
| Mediana do tempo médio de ciclo de PR | 334,359 h | 214,923 h |
| Mediana até primeira resposta em PR | 4,039 h | 2,681 h |
| Mediana até primeira revisão em PR | 11,682 h | 6,216 h |
| Mediana de commits por PR | 3,025 | 3,918 |
| Mediana de reviews por PR | 0,589 | 1,314 |
| Mediana de reviews até aprovação | 1,429 | 1,919 |

#### Interpretação esperada

Os repositórios com política de IA apresentam, na amostra atual:

- Maior taxa mediana de merge;
- Menor taxa mediana de fechamento sem merge;
- Menor tempo mediano de ciclo de PR;
- Menor tempo até primeira resposta em PRs;
- Menor tempo até primeira revisão em PRs;
- Mais reviews por PR;
- Mais reviews até aprovação.

Isso sugere que repositórios com política de IA estão associados a fluxos de contribuição mais ativos, responsivos e estruturados. Porém, assim como na RQ2, essa associação não deve ser interpretada como causalidade direta.

---

## 4. Questões de Pesquisa

### RQ1 — Adoção e Classificação

**RQ1:** Qual é o nível de adoção de políticas de uso de IA em repositórios open-source populares e quais padrões ou tipos de políticas emergem?

A RQ1 deve ser respondida com os arquivos:

- `rq1_adoption_summary.csv`;
- `rq1_cluster_summary.csv`;
- `top_repos_filtered.csv`.

#### Métricas principais

- Total de repositórios analisados;
- Total de repositórios com política de IA;
- Total de repositórios sem política de IA;
- Percentual de adoção de políticas de IA;
- Quantidade de repositórios por cluster;
- Percentual de repositórios por cluster;
- Tamanho médio e mediano dos textos de política por cluster.

#### Visualizações obrigatórias

1. **Cards de adoção**
   - Total de repositórios: `total_repositories`;
   - Repositórios com política: `repositories_with_policy`;
   - Repositórios sem política: `repositories_without_policy`;
   - Percentual de adoção: `policy_adoption_percentage`.

2. **Gráfico de adoção**
   - Com política vs. sem política;
   - Usar valores absolutos e percentual.

3. **Distribuição dos tipos de política**
   - Usar `rq1_cluster_summary.csv`;
   - Eixo X: `cluster_label`;
   - Eixo Y: `unique_repositories`.

4. **Percentual dos clusters**
   - Eixo X: `cluster_label`;
   - Eixo Y: `percentage_of_policy_repositories`.

5. **Tamanho dos textos por cluster**
   - Comparar `median_policy_words` e `mean_policy_words`.

#### Interpretação que o dashboard deve permitir

O dashboard deve mostrar que a adoção de políticas de IA é baixa na amostra geral, com apenas 12,5% dos repositórios analisados apresentando política identificada. Entre esses repositórios, o tipo mais comum é o de governança ampla do uso de IA, representando 75,2% dos casos com política.

---

### RQ2 — Impacto no Engajamento

**RQ2:** Como a presença e o tipo de política de IA se relacionam com o volume de contribuições e o nível de engajamento em projetos open-source?

A RQ2 deve ser respondida, nesta etapa, com o arquivo:

- `rq2_engagement_by_policy_presence.csv`.

Caso exista ou seja adicionado posteriormente, o arquivo abaixo deve complementar a análise por tipo de política:

- `rq2_engagement_by_cluster.csv`.

#### Métricas principais

##### Volume de contribuições

- `prs_total_median`;
- `prs_opened_median`;
- `prs_merged_median`;
- `prs_closed_median`;
- `issues_total_median`;
- `issues_opened_median`;
- `issues_closed_median`.

##### Engajamento

- `unique_collaborators_median`;
- `avg_pr_comments_median`;
- `avg_issue_comments_median`;
- `avg_pr_reviews_median`.

#### Visualizações obrigatórias

1. **PRs totais por presença de política**
   - Y: `prs_total_median`.

2. **PRs mergeadas por presença de política**
   - Y: `prs_merged_median`.

3. **Issues totais por presença de política**
   - Y: `issues_total_median`.

4. **Colaboradores únicos por presença de política**
   - Y: `unique_collaborators_median`.

5. **Comentários por PR e por issue**
   - Y:
     - `avg_pr_comments_median`;
     - `avg_issue_comments_median`.

6. **Reviews por PR**
   - Y: `avg_pr_reviews_median`.

7. **Heatmap de engajamento**
   - Linhas: `has_ai_policy`;
   - Colunas: principais métricas medianas;
   - Valores normalizados, para facilitar comparação visual.

#### Interpretação que o dashboard deve permitir

O dashboard deve permitir comparar se projetos com política de IA apresentam maior ou menor atividade do que projetos sem política. Pelos dados atuais, os projetos com política apresentam medianas superiores em quase todas as métricas de engajamento, especialmente em PRs totais, PRs mergeadas, comentários e reviews.

A interpretação recomendada é:

> Projetos com política de IA estão associados a maior volume de contribuições e maior engajamento na amostra analisada. No entanto, essa diferença pode estar relacionada ao fato de projetos maiores e mais maduros serem mais propensos a documentar políticas.

---

### RQ3 — Impacto na Colaboração

**RQ3:** Como a presença e o tipo de política de IA se relacionam com a responsividade e a eficiência do fluxo de contribuição nos projetos?

A RQ3 deve ser respondida, nesta etapa, com o arquivo:

- `rq3_collaboration_by_policy_presence.csv`.

Caso exista ou seja adicionado posteriormente, o arquivo abaixo deve complementar a análise por tipo de política:

- `rq3_collaboration_by_cluster.csv`.

#### Métricas principais

##### Eficiência do fluxo

- `prs_merge_rate_median`;
- `prs_closed_no_merge_rate_median`;
- `median_pr_cycle_hours_median`;
- `mean_pr_cycle_hours_median`.

##### Responsividade

- `median_issue_first_response_hours_median`;
- `median_pr_first_response_hours_median`;
- `median_pr_first_review_hours_median`.

##### Estabilidade do processo

- `avg_pr_commits_median`;
- `avg_pr_reviews_median`;
- `avg_reviews_until_approval_median`.

#### Visualizações obrigatórias

1. **Taxa de merge**
   - Y: `prs_merge_rate_median`;
   - Unidade: percentual.

2. **Taxa de fechamento sem merge**
   - Y: `prs_closed_no_merge_rate_median`;
   - Unidade: percentual.

3. **Tempo de ciclo de PR**
   - Y: `median_pr_cycle_hours_median`;
   - Converter de horas para dias quando fizer sentido.

4. **Tempo até primeira resposta em PR**
   - Y: `median_pr_first_response_hours_median`.

5. **Tempo até primeira revisão em PR**
   - Y: `median_pr_first_review_hours_median`.

6. **Tempo até primeira resposta em issue**
   - Y: `median_issue_first_response_hours_median`.

7. **Commits por PR**
   - Y: `avg_pr_commits_median`.

8. **Reviews até aprovação**
   - Y: `avg_reviews_until_approval_median`.

9. **Heatmap de colaboração**
   - Linhas: `has_ai_policy`;
   - Colunas: principais métricas medianas;
   - Valores normalizados.

#### Interpretação que o dashboard deve permitir

O dashboard deve mostrar se a presença de política de IA está associada a maior responsividade e eficiência no processo colaborativo.

Com os dados atuais, repositórios com política de IA apresentam:

- Maior taxa de merge;
- Menor taxa de fechamento sem merge;
- Menor tempo de ciclo de PR;
- Menor tempo até primeira resposta em PR;
- Menor tempo até primeira revisão;
- Maior número de reviews por PR.

A interpretação recomendada é:

> Repositórios com política de IA parecem apresentar um fluxo de colaboração mais responsivo e estruturado. Ainda assim, a análise deve ser interpretada como associação, não como evidência causal.

---

## 5. Layout Recomendado do Dashboard

O dashboard deve ser organizado em seções que contem uma história coerente sobre os dados.

---

### Página 1 — Overview do Estudo

Objetivo: apresentar o contexto geral do estudo e os principais números da amostra.

Elementos:

- Título do estudo;
- Breve descrição do objetivo;
- Card: total de repositórios analisados;
- Card: repositórios com política de IA;
- Card: percentual de adoção;
- Card: número de clusters identificados;
- Gráfico de adoção: com política vs. sem política;
- Ranking dos repositórios com mais estrelas.

Dados usados:

- `top_repos_filtered.csv`;
- `rq1_adoption_summary.csv`;
- `rq1_cluster_summary.csv`.

---

### Página 2 — Caracterização do Dataset

Objetivo: caracterizar os 1000 repositórios analisados.

Elementos:

- Distribuição de estrelas;
- Distribuição de idade dos repositórios;
- Distribuição de atividade recente;
- Scatter plot de idade vs. estrelas;
- Tabela com os principais repositórios.

Dados usados:

- `top_repos_filtered.csv`.

---

### Página 3 — RQ1: Adoção e Tipos de Política

Objetivo: responder qual é o nível de adoção e quais tipos de política emergem.

Elementos:

- Cards de adoção;
- Gráfico com política vs. sem política;
- Barras por cluster;
- Percentual por cluster;
- Comparação do tamanho dos textos de política por cluster;
- Tabela interpretativa dos clusters.

Dados usados:

- `rq1_adoption_summary.csv`;
- `rq1_cluster_summary.csv`.

---

### Página 4 — RQ2: Engajamento

Objetivo: responder como a presença de política de IA se relaciona com engajamento.

Elementos:

- PRs totais por presença de política;
- PRs mergeadas por presença de política;
- Issues totais por presença de política;
- Colaboradores únicos por presença de política;
- Comentários por PR;
- Comentários por issue;
- Reviews por PR;
- Heatmap de métricas de engajamento.

Dados usados:

- `rq2_engagement_by_policy_presence.csv`.

Quando disponível, adicionar:

- `rq2_engagement_by_cluster.csv`.

---

### Página 5 — RQ3: Colaboração

Objetivo: responder como a presença de política de IA se relaciona com responsividade e eficiência do fluxo de contribuição.

Elementos:

- Taxa de merge;
- Taxa de fechamento sem merge;
- Tempo de ciclo de PR;
- Tempo até primeira resposta em PR;
- Tempo até primeira resposta em issue;
- Tempo até primeira revisão em PR;
- Commits por PR;
- Reviews por PR;
- Reviews até aprovação;
- Heatmap de métricas de colaboração.

Dados usados:

- `rq3_collaboration_by_policy_presence.csv`.

Quando disponível, adicionar:

- `rq3_collaboration_by_cluster.csv`.

---

### Página 6 — Síntese dos Achados

Objetivo: consolidar os principais resultados.

Elementos:

- Principais achados da RQ1;
- Principais achados da RQ2;
- Principais achados da RQ3;
- Observação sobre associação vs. causalidade;
- Limitações da análise;
- Sugestões de gráficos para o artigo final.

---
## 6. Diretrizes de Visualização

As visualizações devem ser construídas para responder às RQs de forma clara, comparável e reutilizável no artigo final. O dashboard deve priorizar gráficos simples, interpretáveis e consistentes entre as seções.

---

### 6.1. Uso de média e mediana

Quando o CSV possuir média e mediana para a mesma métrica, o dashboard deve usar a **mediana como valor principal**.

Usar como métrica principal:

```text
prs_total_median
```

Evitar como métrica principal:

```text
prs_total_mean
```

A média pode ser apresentada como complemento em:

- Tabelas auxiliares;
- Tooltips;
- Texto interpretativo;
- Gráficos comparativos secundários.

A justificativa é que métricas de repositórios GitHub, como estrelas, PRs, issues e comentários, tendem a ter distribuições assimétricas e podem ser fortemente influenciadas por outliers.

### 6.2. Conversão de unidades

Métricas temporais em horas devem ser apresentadas de forma legível.

Regras recomendadas:

- Se o valor for menor que 48 horas, manter em horas;
- Se o valor for maior que 48 horas, converter para dias;
- Em um mesmo gráfico, usar sempre a mesma unidade;
- Informar a unidade diretamente no título ou no eixo.

Exemplo:

```python
df["median_pr_cycle_days"] = df["median_pr_cycle_hours_median"] / 24
```

Exemplo de label:

```text
Tempo mediano de ciclo de PR (dias)
```

### 6.3. Labels recomendadas

#### Presença de política

| Valor no CSV | Label no gráfico |
|---|---|
| `With AI Policy` | Com política de IA |
| `Without AI Policy` | Sem política de IA |

#### Clusters

| Cluster | Label |
|---:|---|
| 0 | Governança ampla do uso de IA |
| 1 | Responsabilidade humana sobre contribuições assistidas por IA |
| 2 | Declaração obrigatória do uso de IA |

Sempre que possível, evitar mostrar apenas `cluster_0`, `cluster_1` ou `cluster_2` nos gráficos. Usar labels interpretativas melhora a leitura do dashboard e facilita o uso das figuras no artigo.

### 6.4. Tipos de gráfico recomendados

| Objetivo | Tipo de gráfico |
|---|---|
| Mostrar KPIs | Cards |
| Comparar dois grupos | Barras verticais ou horizontais |
| Comparar clusters | Barras horizontais |
| Comparar várias métricas | Heatmap |
| Mostrar distribuição | Histograma ou boxplot |
| Mostrar ranking | Barras horizontais |
| Mostrar relação entre duas variáveis | Scatter plot |
| Comparar proporções | Barras percentuais |
| Investigar tendência | Scatter plot com linha de tendência ou boxplots por faixa |

### 6.5. Estilo visual

O dashboard deve manter consistência visual entre as RQs.

Recomendações:

- Usar a mesma paleta para **Com política** e **Sem política** em todos os gráficos;
- Usar a mesma ordem dos grupos em todos os gráficos;
- Usar títulos descritivos;
- Evitar gráficos excessivamente carregados;
- Preferir barras horizontais quando os labels forem longos;
- Mostrar o número de repositórios do grupo quando possível;
- Evitar conclusões causais nos títulos dos gráficos.

Exemplo de bom título:

```text
Mediana de PRs mergeadas por presença de política de IA
```

Evitar:

```text
Políticas de IA aumentam PRs mergeadas
```

---

## 7. Análise Complementar: Relação entre Popularidade, Idade e Adoção de Políticas

Além das três RQs principais, é interessante incluir uma análise complementar para investigar se a adoção de políticas de IA está associada a características estruturais dos repositórios, especialmente:

- Popularidade, medida pelo número de estrelas;
- Maturidade, medida pela idade do repositório em dias.

Essa análise ajuda a contextualizar os resultados das RQs 2 e 3. Se projetos com política também forem, em geral, mais antigos ou mais populares, parte das diferenças de engajamento e colaboração pode estar relacionada ao perfil desses projetos, e não apenas à existência da política.

### 7.1. Pergunta complementar

Projetos mais antigos ou com mais estrelas tendem a ter maior probabilidade de possuir políticas de IA?

Essa pergunta não substitui as RQs principais, mas ajuda a interpretar os resultados.

### 7.2. Dados necessários

Arquivos principais:

- `data/top_repos_filtered.csv`;
- `data/tables/rq1_repository_policy_summary.csv`, caso disponível;
- Uma versão enriquecida de `top_repos_filtered.csv` contendo uma coluna como `has_ai_policy`.

Caso `top_repos_filtered.csv` ainda não possua uma coluna indicando presença de política, o agente deve criar essa informação fazendo o cruzamento entre:

- `top_repos_filtered.csv`, usando `repo_name`;
- Arquivo com repositórios com política, usando `repo`, `repo_name` ou campo equivalente.

A coluna final recomendada é:

```text
has_ai_policy
```

Com os valores:

- `With AI Policy`;
- `Without AI Policy`.

### 7.3. Variáveis analisadas

| Variável | Coluna esperada | Interpretação |
|---|---|---|
| Popularidade | `stars` | Número de estrelas do repositório |
| Idade | `age_days` | Idade do repositório em dias |
| Presença de política | `has_ai_policy` | Indica se o repositório possui política de IA |

### 7.4. Visualizações recomendadas

#### 7.4.1. Distribuição de estrelas por presença de política

Tipo de gráfico recomendado:

- Boxplot;
- Violin plot;
- Barras com mediana.

Eixos:

- X: `has_ai_policy`;
- Y: `stars`.

Recomendações:

- Usar escala logarítmica no eixo Y se houver grande assimetria;
- Mostrar a mediana de estrelas por grupo;
- Indicar o número de repositórios em cada grupo.

Pergunta respondida:

> Repositórios com política de IA tendem a ser mais populares?

#### 7.4.2. Distribuição de idade por presença de política

Tipo de gráfico recomendado:

- Boxplot;
- Violin plot;
- Barras com mediana.

Eixos:

- X: `has_ai_policy`;
- Y: `age_days`.

Também pode ser útil converter idade para anos:

```python
df["age_years"] = df["age_days"] / 365
```

Pergunta respondida:

> Repositórios com política de IA tendem a ser mais antigos?

#### 7.4.3. Taxa de adoção por faixa de estrelas

Criar faixas de popularidade a partir da coluna `stars`.

Exemplo de faixas:

- Baixa popularidade;
- Média popularidade;
- Alta popularidade;
- Muito alta popularidade.

Ou usar quartis:

```python
df["stars_group"] = pd.qcut(
    df["stars"],
    q=4,
    labels=["Q1 - Menos estrelas", "Q2", "Q3", "Q4 - Mais estrelas"],
)
```

Visualização recomendada:

- Barras percentuais.

Eixos:

- X: `stars_group`;
- Y: percentual de repositórios com política.

Pergunta respondida:

> A adoção de políticas cresce conforme a popularidade do repositório aumenta?

#### 7.4.4. Taxa de adoção por faixa de idade

Criar faixas de idade a partir da coluna `age_days`.

Exemplo usando quartis:

```python
df["age_group"] = pd.qcut(
    df["age_days"],
    q=4,
    labels=["Q1 - Mais recentes", "Q2", "Q3", "Q4 - Mais antigos"],
)
```

Visualização recomendada:

- Barras percentuais.

Eixos:

- X: `age_group`;
- Y: percentual de repositórios com política.

Pergunta respondida:

> Projetos mais antigos apresentam maior adoção de políticas de IA?

#### 7.4.5. Scatter plot: estrelas vs. idade

Tipo de gráfico recomendado:

- Scatter plot.

Eixos:

- X: `age_days`;
- Y: `stars`;
- Cor: `has_ai_policy`.

Recomendações:

- Usar escala logarítmica em `stars`, se necessário;
- Adicionar transparência nos pontos;
- Usar cores diferentes para projetos com e sem política;
- Incluir linha de tendência apenas se ela facilitar a leitura.

Pergunta respondida:

> Repositórios com política se concentram em alguma região específica da relação idade-popularidade?

### 7.5. Métricas complementares sugeridas

A análise pode incluir uma tabela-resumo com:

| Grupo | N repositórios | Mediana de estrelas | Média de estrelas | Mediana de idade | Média de idade |
|---|---:|---:|---:|---:|---:|
| Sem política de IA | ... | ... | ... | ... | ... |
| Com política de IA | ... | ... | ... | ... | ... |

Também pode incluir:

- Percentual de adoção por quartil de estrelas;
- Percentual de adoção por quartil de idade;
- Correlação entre estrelas e presença de política;
- Correlação entre idade e presença de política.

Para correlação com variável binária, o agente pode usar:

- Comparação de medianas;
- Mann-Whitney U Test, se quiser incluir análise estatística;
- Regressão logística simples, se quiser estimar associação.

Essas análises estatísticas são opcionais. O dashboard deve priorizar visualizações claras.

### 7.6. Interpretação esperada

A interpretação deve ser cuidadosa e não causal.

Exemplo adequado:

> Repositórios com política de IA parecem concentrar maior número de estrelas e/ou maior idade mediana. Isso sugere que a adoção de políticas pode estar associada a projetos mais maduros, populares ou organizados.

Evitar:

> Ter mais estrelas causa adoção de políticas de IA.

Ou:

> Projetos antigos criam políticas de IA por causa da idade.

A análise deve ser usada principalmente para contextualizar as RQs 2 e 3. Caso os projetos com política sejam mais populares ou antigos, isso deve ser mencionado como possível fator de confusão.

Essa seção extra é importante para defender a análise: se os projetos com política forem muito mais populares ou antigos, isso vira um possível **fator de confusão** para RQ2 e RQ3, desde que seja mostrado e discutido.

---

## 8. Artefatos Esperados

O agente deve gerar os seguintes artefatos:

```text
outputs/
├── figures/
│   ├── dataset_stars_distribution.png
│   ├── dataset_age_distribution.png
│   ├── dataset_age_vs_stars.png
│   ├── dataset_top_repositories_by_stars.png
│   │
│   ├── rq1_policy_adoption.png
│   ├── rq1_cluster_distribution.png
│   ├── rq1_cluster_percentages.png
│   ├── rq1_policy_text_size_by_cluster.png
│   │
│   ├── rq2_prs_total_by_policy_presence.png
│   ├── rq2_prs_merged_by_policy_presence.png
│   ├── rq2_issues_total_by_policy_presence.png
│   ├── rq2_unique_collaborators_by_policy_presence.png
│   ├── rq2_comments_reviews_by_policy_presence.png
│   ├── rq2_engagement_heatmap.png
│   │
│   ├── rq3_merge_rate_by_policy_presence.png
│   ├── rq3_closed_no_merge_rate_by_policy_presence.png
│   ├── rq3_pr_cycle_time_by_policy_presence.png
│   ├── rq3_first_response_time_by_policy_presence.png
│   ├── rq3_first_review_time_by_policy_presence.png
│   ├── rq3_process_stability_by_policy_presence.png
│   ├── rq3_collaboration_heatmap.png
│   │
│   ├── complementary_stars_by_policy_presence.png
│   ├── complementary_age_by_policy_presence.png
│   ├── complementary_policy_adoption_by_stars_group.png
│   ├── complementary_policy_adoption_by_age_group.png
│   └── complementary_age_vs_stars_by_policy_presence.png
│
├── dashboard/
│   └── dashboard.html
│
└── tables/
    ├── cleaned_top_repos.csv
    ├── cleaned_top_repos_with_policy_presence.csv
    ├── cleaned_rq1_adoption.csv
    ├── cleaned_rq1_clusters.csv
    ├── cleaned_rq2_engagement_policy_presence.csv
    ├── cleaned_rq3_collaboration_policy_presence.csv
    └── complementary_policy_presence_by_repository_profile.csv
```

---

## 9. Requisitos para o Agente de IA

Ao implementar o dashboard, o agente deve:

- Ler os CSVs diretamente das pastas `data/`, `data/tables/` e `data/clusters/`;
- Validar se as colunas esperadas existem antes de gerar cada gráfico;
- Não inventar métricas que não estejam nos arquivos;
- Usar mediana como valor principal quando houver média e mediana;
- Usar labels em português nos gráficos;
- Traduzir `With AI Policy` para `Com política de IA`;
- Traduzir `Without AI Policy` para `Sem política de IA`;
- Salvar todos os gráficos em `outputs/figures/`;
- Gerar um dashboard final em HTML, Streamlit ou Plotly;
- Incluir texto interpretativo curto para cada gráfico;
- Separar claramente a caracterização do dataset, RQ1, RQ2, RQ3 e análise complementar;
- Evitar interpretações causais;
- Destacar o número de repositórios de cada grupo nos gráficos;
- Garantir que o dashboard possa ser executado localmente;
- Criar uma versão enriquecida de `top_repos_filtered.csv` com a coluna `has_ai_policy`, caso ela ainda não exista;
- Usar essa versão enriquecida para analisar idade, estrelas e presença de política.

---

## 10. Interpretação Geral Esperada

O dashboard deve contar a seguinte história:

- O estudo analisou 1000 repositórios open-source populares;
- Apenas uma parcela minoritária dos repositórios possui política de IA identificada;
- Entre os repositórios com política, o tipo mais comum é o de governança ampla do uso de IA;
- Repositórios com política de IA apresentam maior mediana de PRs, issues, comentários e reviews;
- Repositórios com política de IA também apresentam maior taxa de merge, menor tempo de resposta e menor tempo de revisão;
- A análise complementar deve indicar se esses repositórios com política também são mais antigos ou mais populares;
- Caso projetos com política tenham mais estrelas ou maior idade, isso deve ser tratado como possível fator de contexto;
- Os resultados sugerem associação entre presença de política de IA e projetos mais ativos, maduros ou organizados;
- A análise não deve afirmar causalidade, pois projetos maiores, mais antigos ou mais populares podem ser mais propensos tanto a ter políticas quanto a apresentar maior engajamento.

---

## 11. Sugestão de Estrutura do Dashboard

O dashboard pode ser organizado em páginas ou abas.

### Página 1 — Overview

Objetivo: apresentar o contexto geral do estudo.

Elementos:

- Título do estudo;
- Breve descrição do objetivo;
- Total de repositórios analisados;
- Total de repositórios com política;
- Percentual de adoção;
- Número de clusters;
- Gráfico simples de adoção;
- Principais insights em texto.

### Página 2 — Caracterização do Dataset

Objetivo: caracterizar os repositórios analisados.

Elementos:

- Distribuição de estrelas;
- Distribuição de idade;
- Ranking dos repositórios mais populares;
- Scatter plot idade vs. estrelas;
- Tabela com repositórios principais.

### Página 3 — RQ1: Adoção e Tipos de Política

Objetivo: responder à RQ1.

Elementos:

- Cards de adoção;
- Gráfico com política vs. sem política;
- Distribuição por cluster;
- Percentual por cluster;
- Tamanho dos textos de política por cluster;
- Tabela interpretativa dos clusters.

### Página 4 — RQ2: Engajamento

Objetivo: responder à RQ2.

Elementos:

- PRs totais por presença de política;
- PRs mergeadas por presença de política;
- Issues totais por presença de política;
- Colaboradores únicos;
- Comentários por PR;
- Comentários por issue;
- Reviews por PR;
- Heatmap de engajamento.

### Página 5 — RQ3: Colaboração

Objetivo: responder à RQ3.

Elementos:

- Taxa de merge;
- Taxa de fechamento sem merge;
- Tempo de ciclo de PR;
- Tempo até primeira resposta em PR;
- Tempo até primeira resposta em issue;
- Tempo até primeira revisão em PR;
- Commits por PR;
- Reviews até aprovação;
- Heatmap de colaboração.

### Página 6 — Análise Complementar: Perfil dos Repositórios com Política

Objetivo: investigar se repositórios com política de IA são mais antigos ou mais populares.

Elementos:

- Boxplot de estrelas por presença de política;
- Boxplot de idade por presença de política;
- Taxa de adoção por faixa de estrelas;
- Taxa de adoção por faixa de idade;
- Scatter plot idade vs. estrelas colorido por presença de política;
- Tabela comparando medianas de estrelas e idade.

### Página 7 — Síntese dos Achados

Objetivo: consolidar os resultados.

Elementos:

- Principais achados da RQ1;
- Principais achados da RQ2;
- Principais achados da RQ3;
- Principais achados da análise complementar;
- Limitações;
- Observação sobre associação vs. causalidade;
- Sugestões de figuras para o artigo final.

---

## 12. Checklist Final

Antes de finalizar o dashboard, verificar:

- [ ] O dataset geral foi caracterizado com `top_repos_filtered.csv`;
- [ ] A adoção de políticas foi apresentada com `rq1_adoption_summary.csv`;
- [ ] Os clusters foram apresentados com `rq1_cluster_summary.csv`;
- [ ] A RQ1 foi respondida;
- [ ] A RQ2 foi respondida com métricas de engajamento por presença de política;
- [ ] A RQ3 foi respondida com métricas de colaboração por presença de política;
- [ ] A análise complementar de idade, estrelas e presença de política foi incluída;
- [ ] Foi criada uma versão enriquecida do dataset com `has_ai_policy`, se necessário;
- [ ] Os gráficos usam labels claras;
- [ ] Os gráficos indicam unidades;
- [ ] Métricas em horas foram apresentadas de forma legível;
- [ ] Medianas foram priorizadas;
- [ ] Médias foram usadas apenas como complemento;
- [ ] Os gráficos indicam o número de repositórios por grupo quando possível;
- [ ] As interpretações evitam causalidade;
- [ ] Os arquivos foram salvos em `outputs/`;
- [ ] O dashboard final pode ser reproduzido localmente.
