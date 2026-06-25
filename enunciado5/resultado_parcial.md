# Resultado parcial - Lab 05

## 1. Contexto da execucao

O experimento foi executado parcialmente em duas rodadas de coleta. Nesse periodo, foram registradas 843 medicoes brutas em `enunciado5/output/measurements.csv`. Apos a preparacao dos dados, foram obtidos 419 pares validos REST/GraphQL, isto e, medicoes em que o mesmo repositorio, cenario e repeticao possuem uma execucao REST e uma execucao GraphQL bem-sucedidas.

A amostra planejada no desenho do experimento e composta pelos 100 repositorios Python mais populares do GitHub. A execucao parcial cobriu 38 repositorios com pelo menos um par valido. Os repositorios com maior quantidade de pares validos ainda sao os primeiros processados antes do ajuste da ordem de execucao:

| Repositorio | Pares validos |
| --- | ---: |
| `public-apis/public-apis` | 120 |
| `EbookFoundation/free-programming-books` | 119 |
| `donnemartin/system-design-primer` | 41 |
| Demais 35 repositorios | 139 |

Foram registradas 3 medicoes sem sucesso. Essas medicoes foram descartadas da analise pareada principal, mas permanecem registradas em `failure_summary.csv`.

Assim, os resultados abaixo devem ser interpretados como uma analise inicial. Eles permitem responder provisoriamente as RQs, mas ainda nao substituem a execucao completa planejada.

## 2. Dados e artefatos gerados

Foram gerados os seguintes artefatos para apoiar a analise, o relatorio final e o dashboard:

| Artefato | Finalidade |
| --- | --- |
| `enunciado5/output/measurements.csv` | Medicoes brutas REST e GraphQL |
| `enunciado5/output/analysis/paired_measurements.csv` | Pares REST/GraphQL validos |
| `enunciado5/output/analysis/scenario_summary.csv` | Estatisticas descritivas por cenario |
| `enunciado5/output/analysis/wilcoxon_summary.csv` | Testes pareados de Wilcoxon |
| `enunciado5/output/analysis/failure_summary.csv` | Falhas descartadas da analise principal |
| `enunciado5/output/analysis/figures/` | Graficos para RQ1 e RQ2 |

Os quatro cenarios analisados foram:

| Cenario | Descricao |
| --- | --- |
| C1 | Metadados do repositorio |
| C2 | Pull Requests recentes |
| C3 | Issues recentes |
| C4 | Consulta combinada: metadados + PRs + issues |

## 3. Resultados por cenario

### RQ1 - Respostas GraphQL sao mais rapidas que REST?

| Cenario | Pares | Mediana REST (ms) | Mediana GraphQL (ms) | Delta mediano | Delta % | p-valor |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| C1 | 124 | 411.452 | 409.990 | -2.032 | -0.456% | 0.32217923 |
| C2 | 105 | 836.155 | 634.985 | -184.347 | -21.052% | 0.00000000 |
| C3 | 95 | 655.940 | 489.904 | -180.604 | -27.434% | 0.00000000 |
| C4 | 95 | 1961.426 | 805.217 | -1103.527 | -58.803% | 0.00000000 |

![Tempo mediano por cenario](output/analysis/figures/rq1_tempo_mediano_por_cenario.png)

![Delta percentual de tempo](output/analysis/figures/rq1_delta_percentual_tempo.png)

### Interpretacao da RQ1

Nos dados parciais, GraphQL apresentou menor tempo mediano em todos os cenarios. Entretanto, a diferenca em C1 foi muito pequena e nao apresentou significancia estatistica pelo teste pareado de Wilcoxon (`p = 0.32217923`). Isso indica que, para uma consulta simples de metadados de repositorio, REST e GraphQL se comportaram de forma muito parecida.

Nos cenarios C2, C3 e C4, a diferenca foi mais clara. GraphQL reduziu o tempo mediano em aproximadamente 21,1% para PRs recentes, 27,4% para issues recentes e 58,8% para a consulta combinada. O melhor resultado aparece no cenario C4, em que REST precisa agregar multiplas chamadas, enquanto GraphQL consegue obter os dados relacionados em uma unica query.

Conclusao parcial para RQ1: GraphQL foi mais rapido nos cenarios de consulta mais ricos, especialmente na consulta combinada. Para consultas simples de metadados, os dados parciais nao sustentam uma diferenca significativa.

## 4. Tamanho das respostas

### RQ2 - Respostas GraphQL tem tamanho menor que REST?

| Cenario | Pares | Mediana REST (bytes) | Mediana GraphQL (bytes) | Delta mediano | Delta % | p-valor |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| C1 | 124 | 6825 | 489 | -6378 | -93.372% | 0.00000000 |
| C2 | 105 | 177110 | 2685 | -174426 | -98.498% | 0.00000000 |
| C3 | 95 | 31805 | 2223 | -29582 | -93.053% | 0.00000000 |
| C4 | 95 | 227066 | 5316 | -221750 | -97.659% | 0.00000000 |

![Tamanho mediano por cenario](output/analysis/figures/rq2_tamanho_mediano_por_cenario.png)

![Delta percentual de tamanho](output/analysis/figures/rq2_delta_percentual_tamanho.png)

### Interpretacao da RQ2

Nos dados parciais, GraphQL produziu respostas brutas muito menores que REST em todos os cenarios. As reducoes medianas ficaram acima de 93% em todos os casos, chegando a 98,5% no cenario de Pull Requests recentes.

Esse resultado e coerente com a principal diferenca entre as abordagens: em GraphQL, a query solicita apenas os campos necessarios para o experimento; em REST, os endpoints retornam um conjunto maior de atributos por padrao. Como o experimento mede o tamanho bruto da resposta, esse overfetching aparece diretamente na metrica de bytes.

Conclusao parcial para RQ2: com os dados coletados ate agora, GraphQL apresentou respostas brutas substancialmente menores que REST em todos os cenarios analisados.

## 5. Resposta inicial as perguntas de pesquisa

| RQ | Resultado parcial |
| --- | --- |
| RQ1 | Parcialmente favoravel a GraphQL. GraphQL foi mais rapido em C2, C3 e C4, mas C1 ficou praticamente empatado e sem diferenca estatisticamente significativa. |
| RQ2 | Favoravel a GraphQL. GraphQL retornou respostas brutas muito menores em todos os cenarios, com reducoes medianas superiores a 93%. |

De forma geral, os resultados iniciais indicam que o principal beneficio observado de GraphQL e a reducao do tamanho da resposta. O ganho de tempo tambem aparece, mas depende mais do tipo de consulta: quanto mais combinada e relacional e a consulta, maior tende a ser a vantagem de GraphQL.

## 6. Ameacas a validade da analise parcial

A principal ameaca e a cobertura ainda parcial da amostra. Embora a lista dos 100 repositorios Python tenha sido coletada, as medicoes efetivas cobriram 38 repositorios com pelo menos um par valido, e apenas os primeiros repositorios possuem muitas repeticoes. Isso limita a validade externa dos resultados, pois repositorios muito populares podem ter caracteristicas especificas de volume, cache, atividade e estrutura de dados.

Tambem ha uma diferenca de cobertura entre cenarios: C1 possui 124 pares validos, C2 possui 105, C3 possui 95 e C4 possui 95. Essa assimetria ocorreu porque a coleta foi interrompida antes da conclusao de todos os ciclos planejados.

Por fim, os tempos medidos incluem rede, latencia local, processamento da API e transferencia do corpo da resposta. Assim, os resultados devem ser interpretados como custo percebido pelo cliente, e nao como tempo puro de processamento no servidor.

## 7. Ajuste realizado no script de execucao

Durante a analise parcial, foi identificado que o script `run_experiment.py` percorria muitos ciclos dos primeiros repositorios antes de avancar para os demais. Isso explica por que uma execucao de aproximadamente 30 minutos produziu dados concentrados em apenas 3 repositorios.

O script foi ajustado para percorrer primeiro as rodadas e depois os repositorios/cenarios. Com essa mudanca, execucoes interrompidas tendem a produzir amostras parciais mais distribuidas entre os 100 repositorios, melhorando a utilidade de coletas incompletas.

## 8. Conclusao parcial

Com base nos 419 pares validos coletados, a evidencia inicial aponta que GraphQL reduz fortemente o tamanho bruto das respostas em relacao a REST. Para tempo de resposta, GraphQL tambem foi mais rapido na maioria dos cenarios, principalmente quando a consulta envolve dados combinados.

Entretanto, como a execucao parcial ainda nao cobriu todos os 100 repositorios planejados com repeticoes completas, a conclusao final deve ser apresentada com cautela. O resultado atual e suficiente para uma analise inicial e para orientar o relatorio, mas a execucao completa aumentaria a robustez do estudo.
