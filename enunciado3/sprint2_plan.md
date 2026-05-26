# Sprint 2 Plan (Lab03S02)

**Objetivo**
Implementar e validar o pipeline automatizado de coleta e cálculo de métricas para o universo definido; produzir datasets completos prontos para análise.

TL;DR: automatizar coleta em escala, normalizar registros, calcular todas as métricas necessárias e validar com checagens automáticas e amostras manuais.

## Passos
1. Consolidar o contrato de dados final (schema CSV/Parquet) e listar colunas obrigatórias.
2. Gerar a lista canonizada dos 200 repositórios (`enunciado3/data/repos_canonizados.csv`).
3. Ajustar os scripts existentes para escala: paginação, backoff, checkpoint por repositório e logs estruturados.
4. Executar coleta incremental em batches (usar `GITHUB_TOKEN` em `.env`); começar por piloto de ~50 repos e depois escalar a 200.
5. Normalizar dados brutos em `enunciado3/output/prs_normalized.csv` (limpeza de texto, timezone, remoção de bots, tratamento de nulos).
6. Derivar todas as métricas por PR (nº arquivos, linhas adicionadas/removidas, tempo de análise, participantes, comentários, nº de revisões, `final_feedback`, etc.).
7. Agregar medidas (medianas gerais) e gerar `enunciado3/output/metrics_summary.csv` e `enunciado3/output/feedback_summary.csv`.
8. Validar automaticamente (schema, valores finitos, sem duplicatas) e manualmente (amostra aleatória ≥30 PRs).
9. Documentar o processo, salvar checkpoints e versionar artefatos prontos para análise.

## Arquivos relevantes
- `enunciado3/README.md` — atualizar seção de execução da Sprint 2.
- `enunciado3/scripts/collect_cr_repos.py` — seleção de repositórios.
- `enunciado3/scripts/collect_cr_prs.py` — coleta PR-level (ajustar para escala).
- `enunciado3/scripts/github_cr.py` — helpers (rate-limit, checkpoints, parsing).
- `enunciado3/scripts/summarize_cr_metrics.py` — sumarização das métricas (ajustar se necessário).
- `enunciado3/data/repos_canonizados.csv` — output esperado da seleção.
- `enunciado3/data/checkpoint.json` — checkpoints de execução.
- `enunciado3/output/` — local dos CSVs, logs e resumos.

## Comandos recomendados (exemplos)
```bash
# Seleção dos 200 repositórios elegíveis
python3 enunciado3/scripts/collect_cr_repos.py \
  --output enunciado3/data/repos_canonizados.csv --target 200 --per-page 100 --min-prs 100 --review-scan-limit 10

# Coleta incremental em batches (use .env com GITHUB_TOKEN)
python3 enunciado3/scripts/collect_cr_prs.py \
  --repos-csv enunciado3/data/repos_canonizados.csv --output enunciado3/output --repo-limit 20 --pr-limit 1000 --checkpoint enunciado3/data/checkpoint.json

# Reexecutar para próximos batches (retoma por checkpoint)
python3 enunciado3/scripts/collect_cr_prs.py \
  --repos-csv enunciado3/data/repos_canonizados.csv --output enunciado3/output --repo-limit 20 --pr-limit 1000 --checkpoint enunciado3/data/checkpoint.json

# Sumarizar métricas após coleta completa
python3 enunciado3/scripts/summarize_cr_metrics.py \
  --input-dir enunciado3/output --output-csv enunciado3/output/metrics_summary.csv --feedback-output-csv enunciado3/output/feedback_summary.csv
```

## Verificação e critérios de aceite
- `enunciado3/data/repos_canonizados.csv` existe e tem 200 entradas válidas.
- `enunciado3/output/` contém um subdiretório por repositório processado e `prs.csv` com linhas por PR.
- `enunciado3/output/prs_normalized.csv` (ou arquivos por-repo) contém colunas obrigatórias e sem valores críticos vazios.
- `enunciado3/output/metrics_summary.csv` e `enunciado3/output/feedback_summary.csv` existem e mostram valores coerentes (ex.: mediana de `analysis_hours`, distribuição de `final_feedback`).
- Checkpoints permitem retomar sem reprocessar tudo.

## Decisões operacionais
- `final_feedback` será extraído do estado final da última review humana disponível; quando inexistente, marcar `no_review`/`NA`.
- Entrega principal em CSV; usar Parquet opcionalmente para performance/armazenamento.
- Rodar em batches (p.ex. 20 repos por execução) para evitar rate limits; paralelizar por repositório se recurso disponível.

## Próximos passos
1. Executar seleção de 200 repositórios.
2. Rodar coleta em batches, monitorando `enunciado3/output/pipeline_run_log.csv`.
3. Normalizar e sumarizar.
4. Validar amostras manuais e ajustar regras.
5. Anexar resultados e evidências para o relatório final.
