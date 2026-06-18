# Scripts do Lab 05

## Ordem de execucao

1. Coletar a amostra dos 100 repositorios Python mais populares:

```bash
python enunciado5/scripts/collect_top_python_repos.py
```

2. Executar um smoke test pequeno:

```bash
python enunciado5/scripts/run_experiment.py --repo-limit 2 --runs 1 --scenarios C1,C2
```

3. Executar o experimento completo:

```bash
python enunciado5/scripts/run_experiment.py --runs 30 --scenarios C1,C2,C3,C4
```

4. Preparar os dados pareados para analise, relatorio e dashboard:

```bash
python enunciado5/scripts/prepare_analysis_data.py
```

## Tokens

Os scripts usam `GITHUB_REST_TOKEN` para REST e `GITHUB_GRAPHQL_TOKEN` para GraphQL. Se essas variaveis nao existirem, usam `GITHUB_TOKEN` como fallback.

## Saidas principais

- `enunciado5/data/top_python_repos.csv`: amostra de repositorios.
- `enunciado5/data/top_python_repos.checkpoint.json`: checkpoint da amostra.
- `enunciado5/output/measurements.csv`: medicoes do experimento.
- `enunciado5/output/measurements.checkpoint.json`: checkpoint das medicoes.
- `enunciado5/output/analysis/paired_measurements.csv`: pares REST/GraphQL validos.
- `enunciado5/output/analysis/scenario_summary.csv`: resumo por cenario e metrica.
- `enunciado5/output/analysis/failure_summary.csv`: falhas descartadas da analise principal.

O CSV de medicoes ja inclui `pair_id`, `api_type`, `scenario_id`, `elapsed_ms`, `response_bytes`, `success`, `error` e `request_count`, para facilitar a analise pareada REST vs GraphQL no relatorio e no dashboard.
