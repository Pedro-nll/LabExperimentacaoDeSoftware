Tema: Qualidade de codigo

Universo: Java - top 1000 repositorios

## RQs

RQ1: Qualidade x popularidade?

RQ2: Qualidade x maturidade?

RQ3: Qualidade x atividade?

RQ4: Qualidade x tamanho?

## Metricas

Popularidade = numero de estrelas

Tamanho = LOC + comentarios

Atividade = numero de releases

Maturidade = idade

Qualidade (ferramenta CK):
- CBO = acoplamento
- DIT = tamanho da arvore de heranca
- LCOM = falta de coesao entre metodos
- LCOM* = versao normalizada de coesao

## Hipoteses

1. A popularidade do repositorio nao esta diretamente atrelada a qualidade interna.
2. Quanto mais velho o repositorio, mais divida tecnica acumulada e pior qualidade.
3. Quanto mais ativo o repositorio, mais dificil manter qualidade constante.
4. Quanto maior o repositorio, mais dificil manter coesao.

## Sprint 1 (Lab02S01)

Objetivo do sprint:
- Gerar lista de 1.000 repositorios Java (paginacao de 10).
- Automatizar clone + coleta de metricas com CK.
- Entregar CSV consolidado de medicao de 1 repositorio (prova de funcionamento).

Restricoes:
- Nao usar artefatos do enunciado 1.
- Escopo do sprint e infraestrutura de coleta, nao conclusao estatistica final.

### Plano de execucao

1. Definir contrato de dados do sprint
- Colunas minimas para a lista de repositorios: owner, repo, full_name, html_url, stargazers_count, forks_count, open_issues_count, language, created_at, pushed_at, default_branch.
- Chave unica: owner/repo.

2. Coletar os 1.000 repositorios Java
- Usar API do GitHub com pagina de 10 itens.
- Implementar retry com backoff e checkpoint por pagina.
- Exportar CSV canonico com 1.000 entradas Java unicas.

3. Preparar e executar CK
- Build do CK via Maven para gerar JAR standalone.
- Executar CK por repositorio com parametros padrao:
	- use jars = true
	- max files per partition = 0
	- variables and fields = false

4. Executar piloto ponta a ponta em 1 repositorio
- Clonar 1 repositorio da lista.
- Rodar CK.
- Consolidar CBO, DIT, LCOM e LCOM* com media, mediana e desvio padrao.

5. Gerar evidencias
- Salvar CSV de repositorios coletados.
- Salvar logs de execucao.
- Salvar CSV consolidado do piloto.

## Criterios de aceite do Sprint 1

1. O CSV de repositorios possui exatamente 1.000 entradas Java unicas.
2. A automacao gera arquivos CSV do CK para o repositorio piloto.
3. O CSV final do piloto contem CBO, DIT, LCOM e LCOM* com media, mediana e desvio padrao.
4. O processo e reexecutavel em ambiente limpo seguindo este README.

## Como executar (alvo)

1. Coleta dos repositorios Java
- `python enunciado2/scripts/collect_java_repos.py --output enunciado2/data/java_top1000.csv --target 1000 --per-page 10`

2. Build do CK
- `python enunciado2/scripts/setup_ck.py --ck-dir enunciado2/tools/ck --build`

3. Piloto de clone + CK em 1 repositorio
- `python enunciado2/scripts/run_ck_pipeline.py --repos-csv enunciado2/data/java_top1000.csv --sample-size 1 --workspace enunciado2/work --output enunciado2/output --workers 1`

4. Execucao paralela do lote completo
- `python enunciado2/scripts/run_ck_pipeline.py --repos-csv enunciado2/data/java_top1000.csv --sample-size 1000 --workspace enunciado2/work --output enunciado2/output --workers 4`

python enunciado2/scripts/run_ck_pipeline.py --repos-csv enunciado2/data/java_top1000.csv --sample-size 1000 --workspace enunciado2/work --output enunciado2/output --ck-dir enunciado2/tools/ck --workers 4 --timeout-minutes 30

5. Consolidacao das metricas do piloto
- `python enunciado2/scripts/summarize_ck_metrics.py --input-dir enunciado2/output --output-csv enunciado2/output/pilot_metrics_summary.csv`

6. Graficos de dispersao por RQ
- `python enunciado2/scripts/plot_rq_scatter.py --repos-csv enunciado2/data/java_top1000.csv --ck-summary-csv enunciado2/output/ck_summary.csv --output-dir enunciado2/output/rq_graphs`

Observacao:
- O RQ3 ainda nao tem a contagem de releases na base atual; enquanto isso, o grafico usa `days_since_push` como proxy explicito para a exploracao inicial.
- O RQ4 usa `LOC` do CK como proxy de tamanho ate a base ter a soma `LOC + comentarios` calculada separadamente.