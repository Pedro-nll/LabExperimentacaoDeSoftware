# Desenho do Experimento - Lab 05

## Contexto do experimento

Este documento reune ideias iniciais para o desenho do experimento do Lab 05, cujo objetivo e comparar quantitativamente APIs REST e GraphQL. O estudo sera orientado pelas duas perguntas de pesquisa definidas no enunciado:

- RQ1: Respostas as consultas GraphQL sao mais rapidas que respostas as consultas REST?
- RQ2: Respostas as consultas GraphQL tem tamanho menor que respostas as consultas REST?

A proposta inicial e realizar um experimento controlado e pareado usando a API do GitHub como objeto experimental, pois ela oferece interfaces REST e GraphQL sobre entidades equivalentes. Essa escolha tambem aproveita a familiaridade ja adquirida nos laboratorios anteriores com repositorios, Pull Requests, issues e metadados do GitHub.

## A. Hipoteses nula e alternativa

Como o experimento possui duas perguntas de pesquisa, a ideia e definir um par de hipoteses para cada dimensao analisada: tempo de resposta e tamanho da resposta.

### RQ1 - Tempo de resposta

- H0_RQ1: Nao ha diferenca estatisticamente significativa entre o tempo de resposta das consultas GraphQL e o tempo de resposta das consultas REST.
- H1_RQ1: Ha diferenca estatisticamente significativa entre o tempo de resposta das consultas GraphQL e o tempo de resposta das consultas REST.

### RQ2 - Tamanho da resposta

- H0_RQ2: Nao ha diferenca estatisticamente significativa entre o tamanho das respostas GraphQL e o tamanho das respostas REST.
- H1_RQ2: Ha diferenca estatisticamente significativa entre o tamanho das respostas GraphQL e o tamanho das respostas REST.


### Observacao importante

As hipoteses foram mantidas em formato nao direcional. Essa decisao e mais conservadora porque GraphQL pode reduzir overfetching e numero de requisicoes, mas tambem pode ter custo adicional de resolucao no servidor. Assim, a analise estatistica deve primeiro verificar se existe diferenca significativa entre as abordagens; depois, a direcao da diferenca sera interpretada a partir dos resultados observados.

## B1. Variaveis dependentes

As variaveis dependentes sao os resultados medidos apos a aplicacao de cada tratamento.

| Variavel | Descricao | Unidade | Relacao com RQ |
| --- | --- | --- | --- |
| Tempo de resposta | Intervalo entre o envio da requisicao e o recebimento completo da resposta | Milissegundos | RQ1 |
| Tamanho da resposta bruta | Tamanho do corpo retornado pela API antes de qualquer processamento local | Bytes ou KB | RQ2 |
| Status da requisicao | Codigo HTTP ou indicador de sucesso/falha da consulta | Categoria | Controle de validade |
| Numero de requisicoes necessarias | Quantidade de chamadas exigidas para completar um mesmo cenario | Contagem | Analise complementar |

Para as respostas principais do laboratorio, as metricas centrais devem ser tempo de resposta e tamanho da resposta bruta. As demais ajudam a explicar resultados e a identificar casos invalidos.

## B2. Variaveis independentes

As variaveis independentes sao os fatores controlados ou manipulados no experimento.

| Variavel | Valores propostos | Papel no experimento |
| --- | --- | --- |
| Tipo de API | REST, GraphQL | Fator principal comparado |
| Cenario de consulta | Repositorio, issues, pull requests, detalhes combinados | Controla a complexidade da tarefa |
| Objeto consultado | Repositorios selecionados do GitHub | Mantem equivalencia entre tratamentos |
| Ordem de execucao | REST primeiro, GraphQL primeiro, alternado/randomizado | Reduz vies por cache e variacao temporal |
| Rodada de medicao | 1..N repeticoes | Permite estimar variabilidade |
| Janela de execucao | Horario/data da coleta | Controle de ameaca externa |

A variavel independente principal e o tipo de API. As demais devem ser controladas para garantir que REST e GraphQL estejam sendo comparados em condicoes equivalentes.

## C. Tratamentos

Os tratamentos sao as duas formas de executar a mesma tarefa de consulta.

### Tratamento 1 - REST

Executar consultas usando a API REST do GitHub. Para cada cenario, devem ser chamados os endpoints REST necessarios para obter os dados definidos no protocolo experimental.

Exemplos de cenarios REST:

- Consultar metadados de um repositorio.
- Consultar os ultimos Pull Requests de um repositorio.
- Consultar issues recentes de um repositorio.
- Consultar repositorio + PRs + issues, possivelmente exigindo mais de uma chamada REST.

### Tratamento 2 - GraphQL

Executar consultas equivalentes usando a API GraphQL do GitHub. Para cada cenario, deve ser escrita uma query selecionando apenas os campos necessarios para representar a mesma informacao obtida via REST.

Exemplos de cenarios GraphQL:

- Consultar os mesmos metadados do repositorio.
- Consultar os ultimos Pull Requests com os mesmos campos.
- Consultar issues recentes com os mesmos campos.
- Consultar repositorio + PRs + issues em uma unica query, quando possivel.

### Ideia de comparacao justa

Para cada cenario, deve existir uma especificacao clara dos campos necessarios. O REST pode retornar campos extras por natureza da API; esses bytes extras devem ser mantidos na medicao de tamanho porque fazem parte do custo real de consumir REST. Entretanto, para evitar uma comparacao artificial, os cenarios nao devem pedir dados que apenas uma das APIs consiga representar.

## D. Objetos experimentais

A proposta inicial e usar repositorios publicos do GitHub como objetos experimentais.

### Objeto principal

- API do GitHub REST.
- API do GitHub GraphQL.
- Repositorios publicos populares como unidades consultadas.

### Amostra sugerida

Selecionar os 100 repositorios Python mais populares do GitHub, ordenados por numero de estrelas.

Os criterios de selecao da amostra sao:

- linguagem principal Python, usando a busca do GitHub com `language:Python`;
- ordenacao decrescente por estrelas;
- repositorios publicos e acessiveis pelas APIs REST e GraphQL;
- coleta dos 100 primeiros resultados retornados pela busca;
- registro de metadados como estrelas, forks, issues abertas, data de criacao, data de atualizacao e branch padrao.

Essa amostra deixa o experimento mais bem delimitado: em vez de comparar repositorios de dominios e linguagens muito diferentes, o estudo passa a observar o comportamento das APIs em um conjunto de projetos populares de uma mesma linguagem.

### Cenarios de consulta sugeridos

| Cenario | Descricao | Justificativa |
| --- | --- | --- |
| C1 - Metadados de repositorio | Nome, dono, estrelas, forks, linguagem principal, data de criacao e data de atualizacao | Consulta simples e comum |
| C2 - Pull Requests recentes | Lista dos 10 PRs mais recentemente atualizados, com titulo, estado, autor, datas e contagens basicas | Reaproveita dominio do Lab 3 |
| C3 - Issues recentes | Lista das 10 issues mais recentemente atualizadas, com titulo, estado, autor, datas e comentarios | Representa colecao paginada |
| C4 - Consulta combinada | Metadados do repositorio + 10 PRs recentes + 10 issues recentes | Tende a evidenciar diferencas entre REST e GraphQL |

O cenario C4 e especialmente interessante porque GraphQL pode recuperar dados relacionados em uma unica query, enquanto REST pode exigir multiplas requisicoes. Por outro lado, os cenarios C1, C2 e C3 ajudam a observar se GraphQL continua vantajoso em consultas mais simples.

## E. Tipo de projeto experimental

O desenho recomendado e um experimento controlado, quantitativo, pareado e intra-sujeitos.

### Caracterizacao

- Controlado: os cenarios, campos consultados, repositorios, ambiente e scripts serao definidos previamente.
- Quantitativo: a comparacao sera baseada em metricas numericas de tempo e tamanho.
- Pareado: cada repositorio/cenario sera medido nos dois tratamentos, REST e GraphQL.
- Intra-sujeitos: o mesmo objeto experimental sera submetido aos dois tratamentos.

### Unidade experimental

A unidade experimental pode ser definida como:

> Uma execucao de um cenario de consulta para um repositorio especifico usando uma tecnologia especifica.

Exemplo:

> C2 - Pull Requests recentes do repositorio `facebook/react`, executado via GraphQL, na repeticao 12.

### Estrategia de controle

Para reduzir vieses:

- Randomizar a ordem REST/GraphQL;
- usar o mesmo token, maquina, rede e periodo de coleta;
- registrar timestamp, status da resposta e eventuais erros;
- Descartar medicoes com erro HTTP, rate limit ou timeout (e relatar isso no final);
- Utilizar dois tokens da API do github para o rate limit de uma não afetar a outra.

### Analise estatistica sugerida

Como as medicoes serao pareadas, as comparacoes devem considerar pares REST vs GraphQL para o mesmo repositorio, cenario e rodada.

Testes possiveis:

- Wilcoxon signed-rank test, caso as distribuicoes sejam assimetricas ou nao normais.
- t-test pareado, caso a diferenca entre pares seja aproximadamente normal.
- Mediana, media, desvio padrao, intervalo interquartil e boxplots para analise descritiva.

O teste de Wilcoxon parece uma boa escolha inicial, pois tempos de resposta de rede costumam ser assimetricos e sensiveis a outliers.

## F. Quantidade de medicoes

A quantidade de medicoes deve equilibrar confiabilidade estatistica, tempo de execucao e limites da API.

### Proposta adotada

- Repositorios: 100 repositorios Python mais populares do GitHub.
- Cenarios por repositorio: 4.
- Tratamentos por cenario: 2.
- Repeticoes oficiais por tratamento: 30.

Com essa configuracao:

- Medicoes oficiais: 100 repositorios x 4 cenarios x 2 tratamentos x 30 repeticoes = 24.000 medicoes.

Essa escala e maior que a proposta inicial, mas combina bem com a amostra definida de 100 repositorios. O uso de checkpoint, retry, randomizacao da ordem de execucao e dois tokens de API deve reduzir perdas durante uma execucao longa. Como as medicoes com erro HTTP, rate limit ou timeout serao descartadas da analise principal, o dataset final tambem deve registrar esses casos para permitir relatar a taxa de falha.

### Alternativa mais economica

Caso o tempo de execucao ou o limite da API se torne um problema:

- Repositorios: 100.
- Cenarios: 3.
- Tratamentos: 2.
- Repeticoes: 10.

Total:

- 100 x 3 x 2 x 10 = 6.000 medicoes oficiais.

Essa alternativa preserva a amostra de repositorios Python, mas reduz o numero de repeticoes e pode ser usada caso a execucao completa fique muito demorada.

### Campos a registrar por medicao

Cada linha do dataset experimental deve conter pelo menos:

| Campo | Exemplo |
| --- | --- |
| `measurement_id` | identificador unico da medicao |
| `timestamp` | data e hora da execucao |
| `api_type` | `REST` ou `GraphQL` |
| `scenario_id` | `C1`, `C2`, `C3`, `C4` |
| `repository` | `owner/name` |
| `run_number` | repeticao da medicao |
| `order_index` | posicao na sequencia de execucao |
| `http_status` | codigo de status |
| `elapsed_ms` | tempo total medido |
| `response_bytes` | tamanho do corpo da resposta |
| `request_count` | numero de chamadas usadas no cenario |
| `error` | mensagem de erro, se houver |

## G. Ameacas a validade

### Validade interna

- Variacao da rede: latencia, instabilidade local e congestionamento podem afetar o tempo de resposta.
- Cache: chamadas repetidas podem ser beneficiadas por caches do cliente, da rede ou do servidor.
- Ordem de execucao: mesmo com randomizacao, ainda podem existir efeitos temporais entre uma chamada e outra.
- Rate limit: aproximacao do limite da API pode alterar tempos de resposta ou gerar falhas.
- Diferencas de autenticacao: o uso de dois tokens reduz competicao por rate limit, mas tokens diferentes podem ter limites ou permissoes ligeiramente diferentes.
- Medicao local: o tempo medido no cliente inclui rede, serializacao e download, nao apenas processamento do servidor.
- Descarte de falhas: remover medicoes com erro HTTP, timeout ou rate limit pode reduzir ruido, mas tambem pode ocultar diferencas de estabilidade entre REST e GraphQL.

Mitigacoes:

- randomizar a ordem dos tratamentos;
- registrar timestamp e status;
- usar o mesmo ambiente, a mesma rede e o mesmo periodo de coleta;
- registrar qual token foi usado por tipo de API, sem salvar o valor do token;
- aplicar timeouts padronizados;
- usar retry com backoff para falhas transientes;
- manter checkpoint para retomada da coleta;
- descartar medicoes invalidas da analise principal e relatar a taxa de descarte no relatorio.

### Validade de construto

- Equivalencia dos dados: REST e GraphQL podem nao retornar exatamente os mesmos campos ou estruturas.
- Tamanho da resposta: medir JSON bruto pode favorecer GraphQL, mas isso tambem representa uma diferenca real de overfetching.
- Tempo de resposta: em cenarios combinados, uma chamada GraphQL pode substituir varias chamadas REST.
- Complexidade da query: consultas GraphQL mal escritas podem prejudicar o desempenho e enviesar o resultado.
- Issues via REST e GraphQL: a consulta REST de issues sera feita pela API de busca para evitar misturar Pull Requests com issues, enquanto GraphQL usara a conexao `issues`.

Mitigacoes:

- definir previamente os campos esperados em cada cenario;
- medir o tempo total necessario para completar a tarefa, nao apenas uma chamada isolada quando REST exigir multiplos endpoints;
- manter as queries GraphQL simples e equivalentes aos endpoints REST;
- documentar todas as queries e endpoints usados.

### Validade externa

- Generalizacao limitada: resultados obtidos com GitHub podem nao representar outras APIs.
- Dominio especifico: repositorios, issues e PRs podem ter padroes diferentes de outros tipos de sistemas.
- Amostra de repositorios Python populares: projetos muito populares de Python podem ter infraestrutura, comunidade e volume de dados diferentes de projetos pequenos ou de outras linguagens.
- Momento da coleta: desempenho da API pode variar conforme horario, carga do servidor e condicoes externas.

Mitigacoes:

- documentar data, horario, ambiente e criterios de selecao;
- manter a lista final dos 100 repositorios coletados como artefato do experimento;
- evitar conclusoes universais sobre REST e GraphQL, tratando os resultados como evidencia para o contexto analisado.

### Validade de conclusao

- Medicoes descartadas por erro podem reduzir o numero de pares validos.
- Outliers de rede podem distorcer medias.
- Distribuicoes assimetricas podem invalidar testes parametricos simples.
- Multiplas comparacoes por cenario podem aumentar chance de falso positivo.

Mitigacoes:

- usar analise pareada;
- reportar mediana e intervalo interquartil alem da media;
- aplicar Wilcoxon quando os dados nao forem normais;
- apresentar graficos de distribuicao e boxplots;
- separar analise geral e analise por cenario;
- filtrar a analise principal para pares REST/GraphQL validos do mesmo repositorio, cenario e repeticao.

## Decisoes fechadas para a preparacao

- O objeto experimental sera a API do GitHub, comparando REST e GraphQL.
- A lista final sera composta pelos 100 repositorios Python mais populares do GitHub no momento da coleta.
- Os campos dos cenarios serao simples e comparaveis: metadados de repositorio, PRs recentes, issues recentes e uma consulta combinada.
- O tamanho principal sera o tamanho bruto do corpo da resposta em bytes.
- REST sera medido pelo tempo total necessario para completar a mesma tarefa. Assim, em cenarios que exigirem multiplas chamadas REST, o tempo e o tamanho serao agregados.
- O numero recomendado de repeticoes sera 30 por tratamento, cenario e repositorio.

## Recomendacao inicial

A versao mais equilibrada do experimento e comparar REST e GraphQL em tarefas equivalentes, medindo o tempo total e o tamanho total necessarios para completar cada cenario. Essa escolha favorece uma comparacao pratica: nao apenas "qual chamada isolada e mais rapida", mas "qual abordagem entrega a mesma informacao com menor custo para o cliente".

Para o proximo passo, a preparacao do experimento pode comecar pela implementacao de scripts que:

1. leem uma lista de repositorios;
2. executam os cenarios em REST e GraphQL;
3. alternam a ordem de execucao;
4. registram tempo, tamanho, status e erros;
5. salvam tudo em CSV para analise estatistica posterior.
