#!/usr/bin/env python3
"""Generate the final Lab 05 report and dashboard."""

from __future__ import annotations

import base64
from pathlib import Path
from typing import Dict, List

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "output"
ANALYSIS = OUTPUT / "analysis"
FIGURES = ANALYSIS / "figures"
REPORT_DIR = OUTPUT / "relatorio"
DASHBOARD_DIR = OUTPUT / "dashboard"


def fmt_num(value: float, decimals: int = 3) -> str:
    return f"{value:,.{decimals}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def fmt_int(value: float) -> str:
    return f"{int(round(value)):,.0f}".replace(",", ".")


def fmt_pct(value: float) -> str:
    return f"{value:.3f}%".replace(".", ",")


def load_data() -> Dict[str, pd.DataFrame]:
    return {
        "measurements": pd.read_csv(OUTPUT / "measurements.csv"),
        "paired": pd.read_csv(ANALYSIS / "paired_measurements.csv"),
        "summary": pd.read_csv(ANALYSIS / "scenario_summary.csv"),
        "wilcoxon": pd.read_csv(ANALYSIS / "wilcoxon_summary.csv"),
        "failures": pd.read_csv(ANALYSIS / "failure_summary.csv"),
        "repos": pd.read_csv(ROOT / "data" / "top_python_repos.csv"),
    }


def table_html(headers: List[str], rows: List[List[str]], class_name: str = "") -> str:
    cls = f' class="{class_name}"' if class_name else ""
    head = "".join(f"<th>{h}</th>" for h in headers)
    body = "\n".join("<tr>" + "".join(f"<td>{cell}</td>" for cell in row) + "</tr>" for row in rows)
    return f"<table{cls}><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>"


def image_data_uri(path: Path) -> str:
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def scenario_rows(wilcoxon: pd.DataFrame, metric: str) -> List[List[str]]:
    rows: List[List[str]] = []
    for _, row in wilcoxon[wilcoxon["metric"] == metric].sort_values("scenario_id").iterrows():
        rows.append(
            [
                str(row["scenario_id"]),
                fmt_int(row["n_pairs"]),
                fmt_num(float(row["rest_median"])),
                fmt_num(float(row["graphql_median"])),
                fmt_num(float(row["median_delta"])),
                fmt_pct(float(row["median_delta_pct"])),
                f"{float(row['p_value']):.8f}",
            ]
        )
    return rows


def stats(data: Dict[str, pd.DataFrame]) -> Dict[str, int]:
    paired = data["paired"]
    measurements = data["measurements"]
    return {
        "measurements": len(measurements),
        "valid_pairs": len(paired),
        "repos": paired["repository"].nunique(),
        "failures": int((measurements["success"] != 1).sum()),
    }


def dashboard_grouped_bar_svg(title: str, labels: List[str], rest_values: List[float], gql_values: List[float], unit: str) -> str:
    width, height = 560, 260
    left, top = 94, 42
    bar_h, gap, pair_gap = 10, 5, 24
    plot_w = width - left - 82
    max_value = max(rest_values + gql_values) or 1
    rows = []
    for i, label in enumerate(labels):
        y = top + i * (bar_h * 2 + gap + pair_gap)
        rv = rest_values[i]
        gv = gql_values[i]
        rw = max(1, rv / max_value * plot_w)
        gw = max(1, gv / max_value * plot_w)
        rows.append(f'<text x="12" y="{y + 15}" class="axis">{label}</text>')
        rows.append(f'<rect x="{left}" y="{y}" width="{rw:.2f}" height="{bar_h}" fill="#33464d"></rect>')
        rows.append(f'<rect x="{left}" y="{y + bar_h + gap}" width="{gw:.2f}" height="{bar_h}" fill="#10b8aa"></rect>')
        rows.append(f'<text x="{left + rw + 6:.2f}" y="{y + 9}" class="value">{fmt_num(rv, 1)}{unit}</text>')
        rows.append(f'<text x="{left + gw + 6:.2f}" y="{y + bar_h + gap + 9}" class="value">{fmt_num(gv, 1)}{unit}</text>')
    return f"""
    <svg class="svg-chart" viewBox="0 0 {width} {height}" role="img" aria-label="{title}">
      <style>.axis{{font:12px system-ui;fill:#516068}}.value{{font:10px system-ui;fill:#516068}}.title{{font:700 14px system-ui;fill:#17202a}}.legend{{font:11px system-ui;fill:#516068}}</style>
      <text x="12" y="22" class="title">{title}</text>
      <rect x="365" y="12" width="10" height="10" fill="#33464d"></rect><text x="380" y="21" class="legend">REST</text>
      <rect x="435" y="12" width="10" height="10" fill="#10b8aa"></rect><text x="450" y="21" class="legend">GraphQL</text>
      {''.join(rows)}
    </svg>
    """


def dashboard_single_bar_svg(title: str, labels: List[str], values: List[float], suffix: str, color: str = "#10b8aa") -> str:
    width, height = 420, 228
    left, top = 58, 42
    bar_h, gap = 20, 18
    plot_w = width - left - 86
    max_value = max(abs(v) for v in values) or 1
    rows = []
    for i, label in enumerate(labels):
        y = top + i * (bar_h + gap)
        value = values[i]
        bw = max(1, abs(value) / max_value * plot_w)
        x = left if value >= 0 else left + plot_w - bw
        fill = color if value >= 0 else "#ff5a5f"
        rows.append(f'<text x="12" y="{y + 14}" class="axis">{label}</text>')
        rows.append(f'<rect x="{left}" y="{y}" width="{plot_w}" height="{bar_h}" fill="#eef3f5"></rect>')
        rows.append(f'<rect x="{x:.2f}" y="{y}" width="{bw:.2f}" height="{bar_h}" fill="{fill}"></rect>')
        rows.append(f'<text x="{left + plot_w + 8}" y="{y + 14}" class="value">{fmt_num(value, 1)}{suffix}</text>')
    return f"""
    <svg class="svg-chart" viewBox="0 0 {width} {height}" role="img" aria-label="{title}">
      <style>.axis{{font:12px system-ui;fill:#516068}}.value{{font:11px system-ui;fill:#17202a}}.title{{font:700 14px system-ui;fill:#17202a}}</style>
      <text x="12" y="22" class="title">{title}</text>
      {''.join(rows)}
    </svg>
    """


def dashboard_donut_svg(title: str, value: float, subtitle: str) -> str:
    # Stroke-dasharray uses a 100-unit path length for easy percentage rendering.
    return f"""
    <svg class="donut" viewBox="0 0 180 160" role="img" aria-label="{title}">
      <style>.dt{{font:700 13px system-ui;fill:#17202a}}.dv{{font:700 28px system-ui;fill:#17202a}}.ds{{font:11px system-ui;fill:#516068}}</style>
      <text x="12" y="18" class="dt">{title}</text>
      <circle cx="90" cy="82" r="44" fill="none" stroke="#e8eef2" stroke-width="18"></circle>
      <circle cx="90" cy="82" r="44" fill="none" stroke="#10b8aa" stroke-width="18" pathLength="100" stroke-dasharray="{value:.1f} 100" stroke-linecap="round" transform="rotate(-90 90 82)"></circle>
      <text x="90" y="88" text-anchor="middle" class="dv">{fmt_num(value, 1)}%</text>
      <text x="90" y="112" text-anchor="middle" class="ds">{subtitle}</text>
    </svg>
    """


def build_report_html(data: Dict[str, pd.DataFrame]) -> str:
    st = stats(data)
    wilcoxon = data["wilcoxon"]
    repos = data["repos"]

    rq1_table = table_html(
        ["Cenario", "Pares", "REST mediana (ms)", "GraphQL mediana (ms)", "Delta", "Delta %", "p-valor"],
        scenario_rows(wilcoxon, "elapsed_ms"),
    )
    rq2_table = table_html(
        ["Cenario", "Pares", "REST mediana (bytes)", "GraphQL mediana (bytes)", "Delta", "Delta %", "p-valor"],
        scenario_rows(wilcoxon, "response_bytes"),
    )
    metrics_table = table_html(
        ["Metrica", "Descricao", "Unidade", "RQ"],
        [
            ["elapsed_ms", "Tempo total entre envio da requisicao e recebimento da resposta", "ms", "RQ1"],
            ["response_bytes", "Tamanho bruto do corpo da resposta retornada pela API", "bytes", "RQ2"],
            ["request_count", "Numero de chamadas usadas para completar o cenario", "contagem", "Controle"],
            ["success/error", "Indicador de sucesso e falhas descartadas da analise pareada", "categoria", "Controle"],
        ],
    )
    rq_table = table_html(
        ["RQ", "Pergunta de pesquisa"],
        [
            ["RQ1", "Respostas as consultas GraphQL sao mais rapidas que respostas as consultas REST?"],
            ["RQ2", "Respostas as consultas GraphQL tem tamanho menor que respostas as consultas REST?"],
        ],
    )
    hypothesis_table = table_html(
        ["RQ", "Hipotese nula", "Hipotese alternativa"],
        [
            ["RQ1", "Nao ha diferenca significativa entre o tempo de resposta de GraphQL e REST.", "Ha diferenca significativa entre o tempo de resposta de GraphQL e REST."],
            ["RQ2", "Nao ha diferenca significativa entre o tamanho das respostas GraphQL e REST.", "Ha diferenca significativa entre o tamanho das respostas GraphQL e REST."],
        ],
    )
    objectives_table = table_html(
        ["Objetivo", "Descricao"],
        [
            ["OE01", "Selecionar os 100 repositorios Python mais populares do GitHub."],
            ["OE02", "Executar cenarios equivalentes usando REST e GraphQL."],
            ["OE03", "Medir tempo de resposta e tamanho bruto da resposta."],
            ["OE04", "Aplicar analise pareada e teste de Wilcoxon."],
            ["OE05", "Interpretar os resultados em relacao as RQs do laboratorio."],
        ],
    )
    steps_table = table_html(
        ["Etapa", "Descricao"],
        [
            ["1", "Coleta da lista dos 100 repositorios Python mais populares."],
            ["2", "Execucao dos cenarios C1, C2, C3 e C4 em REST e GraphQL."],
            ["3", "Registro das medicoes brutas em CSV com checkpoint e retry."],
            ["4", "Formacao de pares validos REST/GraphQL por repositorio, cenario e rodada."],
            ["5", "Calculo de medianas, deltas e teste pareado de Wilcoxon."],
            ["6", "Geracao de graficos, dashboard e relatorio final."],
        ],
    )
    decisions_table = table_html(
        ["Decisao", "Justificativa"],
        [
            ["API do GitHub", "Disponibiliza interfaces REST e GraphQL maduras sobre objetos equivalentes."],
            ["Repositorios Python populares", "Delimita a amostra e reduz variacao entre linguagens."],
            ["30 repeticoes", "Permite observar variabilidade de rede e estabilizar medianas."],
            ["Analise pareada", "Compara REST e GraphQL para o mesmo repositorio, cenario e rodada."],
            ["Tamanho bruto", "Representa o custo direto de transferencia percebido pelo cliente."],
        ],
    )
    failures = data["failures"].copy()
    failure_rows = [
        [str(row.api_type), str(row.scenario_id), str(row.http_status), str(row.error), fmt_int(row["count"])]
        for _, row in failures.iterrows()
    ]
    failure_table = table_html(["API", "Cenario", "Status", "Erro", "Quantidade"], failure_rows)

    css = """
    @page { size: A4; margin: 2.1cm 1.8cm; }
    body { font-family: Arial, Helvetica, sans-serif; color: #222; line-height: 1.45; font-size: 11.5pt; }
    .cover { page-break-after: always; text-align: center; padding-top: 4.8cm; }
    .cover h1 { font-size: 24pt; line-height: 1.2; font-weight: 500; margin: 0 0 1.2cm; }
    .cover .author { font-size: 13pt; margin-bottom: .25cm; }
    .cover .date { font-size: 12pt; margin-bottom: .8cm; }
    .cover .link { font-size: 10.5pt; }
    .toc { page-break-after: always; }
    .toc h2 { font-size: 16pt; font-weight: 500; margin-bottom: .5cm; }
    .toc-line { display: flex; justify-content: space-between; border-bottom: 1px dotted #aaa; margin: 5px 0; gap: 8px; }
    h2 { font-size: 17pt; margin: 0 0 12px; font-weight: 600; }
    h3 { font-size: 13.5pt; margin: 18px 0 8px; font-weight: 600; }
    h4 { font-size: 12pt; margin: 14px 0 6px; font-weight: 600; }
    section { page-break-before: always; }
    section.first { page-break-before: auto; }
    p { margin: 0 0 11px; text-align: justify; }
    table { width: 100%; border-collapse: collapse; margin: 10px 0 16px; font-size: 9.7pt; }
    th, td { border: 1px solid #cbd5df; padding: 6px 7px; vertical-align: top; }
    th { background: #eef3f7; text-align: left; }
    img.figure { display: block; max-width: 100%; margin: 12px auto 18px; border: 1px solid #d7dee8; }
    .note { background: #f3f7fb; border-left: 4px solid #2A9D8F; padding: 10px 12px; margin: 12px 0; }
    .page-num { color: #777; }
    """

    toc_items = [
        ("GraphQL vs REST - Um experimento controlado", "1"),
        ("1 - Introducao", "2"),
        ("1.1 - Contextualizacao", "2"),
        ("1.1.1 - Restricoes e riscos", "2"),
        ("1.2 - Problema foco do experimento", "2"),
        ("1.3 - Questoes de Pesquisa", "2"),
        ("1.4 - Hipoteses", "2"),
        ("2 - Objetivo", "2"),
        ("2.1 - Objetivo principal", "2"),
        ("2.2 - Objetivos especificos", "2"),
        ("3 - Metodologia", "2"),
        ("3.1 - Passo a passo do experimento", "2"),
        ("3.2 - Decisoes", "2"),
        ("3.3 - Materiais utilizados", "2"),
        ("3.4 - Metodos utilizados", "2"),
        ("3.5 - Metricas e suas unidades", "2"),
        ("4 - Visualizacao dos Resultados", "2"),
        ("5 - Discussao dos Resultados", "2"),
        ("6 - Conclusao", "2"),
        ("6.1 - Trabalhos futuros", "2"),
        ("7 - Reprodutibilidade", "3"),
    ]
    toc_html = "\n".join(f'<div class="toc-line"><span>{label}</span><span class="page-num">{page}</span></div>' for label, page in toc_items)

    return f"""<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <title>GraphQL vs REST - Um experimento controlado</title>
  <style>{css}</style>
</head>
<body>
  <div class="cover">
    <h1>GraphQL vs REST - Um experimento controlado</h1>
    <div class="author">Pedro Negri Leao Lambert</div>
    <div class="date">25/06/2026</div>
    <div class="link">Link para repo/dados:<br>https://github.com/Pedro-nll/LabExperimentacaoDeSoftware/tree/enunciado5</div>
  </div>

  <div class="toc">
    {toc_html}
  </div>

  <section class="first">
    <h2>1 - Introducao</h2>
    <h3>1.1 - Contextualizacao</h3>
    <p>APIs Web sao uma parte essencial da integracao entre sistemas de software. Historicamente, muitas APIs foram construidas com base no estilo REST, em que clientes acessam recursos por endpoints predefinidos. GraphQL surge como uma alternativa em que o cliente declara explicitamente os campos desejados, permitindo recuperar dados relacionados em uma unica consulta e reduzir o retorno de informacoes nao utilizadas.</p>
    <p>Neste laboratorio, o foco esta na comparacao experimental entre REST e GraphQL em um contexto controlado. A API do GitHub foi usada como objeto experimental porque oferece as duas interfaces sobre entidades equivalentes, como repositorios, Pull Requests e issues.</p>

    <h3>1.1.1 - Restricoes e riscos</h3>
    <p>O experimento mede o custo percebido pelo cliente, incluindo rede, latencia, serializacao, processamento da API e transferencia da resposta. Portanto, os tempos obtidos nao representam apenas processamento interno do servidor. Alem disso, os resultados se limitam ao contexto da API do GitHub e aos 100 repositorios Python mais populares no momento da coleta.</p>
    <p>Outra restricao e que GraphQL foi configurado para retornar apenas os campos necessarios ao experimento, enquanto REST retorna os campos padrao de cada endpoint. Essa diferenca faz parte da comparacao pratica entre as abordagens, mas deve ser considerada ao interpretar a reducao de tamanho das respostas.</p>

    <h3>1.2 - Problema foco do experimento</h3>
    <p>O problema foco e avaliar, de forma quantitativa, se consultas GraphQL apresentam beneficios mensuraveis em relacao a consultas REST equivalentes. O estudo observa duas dimensoes: tempo de resposta e tamanho bruto da resposta retornada pela API.</p>

    <h3>1.3 - Questoes de Pesquisa</h3>
    {rq_table}

    <h3>1.4 - Hipoteses</h3>
    {hypothesis_table}
  </section>

  <section>
    <h2>2 - Objetivo</h2>
    <h3>2.1 - Objetivo principal</h3>
    <p>O objetivo principal deste experimento e comparar quantitativamente as respostas de consultas REST e GraphQL na API do GitHub, verificando diferencas em tempo de resposta e tamanho bruto da resposta para cenarios equivalentes.</p>

    <h3>2.2 - Objetivos especificos</h3>
    {objectives_table}
  </section>

  <section>
    <h2>3 - Metodologia</h2>
    <p>A metodologia foi organizada como um experimento controlado, quantitativo e pareado. Cada unidade experimental corresponde a uma execucao de um cenario para um repositorio especifico, em uma rodada especifica, usando REST ou GraphQL. As comparacoes foram feitas entre pares equivalentes.</p>

    <h3>3.1 - Passo a passo do experimento</h3>
    {steps_table}

    <h3>3.2 - Decisoes</h3>
    {decisions_table}

    <h3>3.3 - Materiais utilizados</h3>
    <p>Foram utilizados dados publicos da API do GitHub, scripts Python desenvolvidos para a coleta, arquivos CSV de saida, graficos em PNG e tabelas de estatisticas descritivas e testes estatisticos. A amostra contem {fmt_int(st['repos'])} repositorios Python populares. A coleta completa gerou {fmt_int(st['measurements'])} medicoes brutas e {fmt_int(st['valid_pairs'])} pares validos.</p>
    {failure_table}

    <h3>3.4 - Metodos utilizados</h3>
    <p>Foram calculadas estatisticas descritivas, como media e mediana, para tempo de resposta e tamanho bruto. Como as medicoes sao pareadas, foi aplicado o teste de Wilcoxon para comparar REST e GraphQL em cada cenario. A interpretacao priorizou medianas e deltas percentuais, pois tempos de rede e tamanhos de resposta podem apresentar distribuicoes assimetricas.</p>

    <h3>3.5 - Metricas e suas unidades</h3>
    {metrics_table}
  </section>

  <section>
    <h2>4 - Visualizacao dos Resultados</h2>
    <p>A tabela a seguir apresenta a comparacao de tempo de resposta. Valores negativos de delta indicam vantagem de GraphQL.</p>
    {rq1_table}
    <img class="figure" src="../analysis/figures/rq1_tempo_mediano_por_cenario.png" alt="Tempo mediano por cenario">
    <img class="figure" src="../analysis/figures/rq1_delta_percentual_tempo.png" alt="Delta percentual de tempo">
    <p>A proxima tabela apresenta a comparacao do tamanho bruto das respostas em bytes.</p>
    {rq2_table}
    <img class="figure" src="../analysis/figures/rq2_tamanho_mediano_por_cenario.png" alt="Tamanho mediano por cenario">
    <img class="figure" src="../analysis/figures/rq2_delta_percentual_tamanho.png" alt="Delta percentual de tamanho">
  </section>

  <section>
    <h2>5 - Discussao dos Resultados</h2>
    <p>Os resultados indicam que GraphQL reduziu fortemente o tamanho bruto das respostas em todos os cenarios. As reducoes medianas variaram de 92,326% em C1 a 98,448% em C2. Esse comportamento era esperado, pois GraphQL permite selecionar apenas os campos necessarios, enquanto REST retorna estruturas maiores por padrao.</p>
    <p>Em relacao ao tempo de resposta, a interpretacao e mais nuanceada. GraphQL foi mais rapido nos cenarios C2, C3 e C4, mas nao em C1. No cenario de metadados simples, REST apresentou uma mediana ligeiramente menor. Ja na consulta combinada, GraphQL teve ganho expressivo, pois substituiu tres chamadas REST por uma unica consulta.</p>
    <p>Portanto, os resultados sugerem que GraphQL e especialmente vantajoso quando a tarefa envolve dados relacionados ou quando ha risco de overfetching. Para consultas simples, a diferenca de tempo pode ser pequena ou ate favorecer REST.</p>
  </section>

  <section>
    <h2>6 - Conclusao</h2>
    <p>Com base em {fmt_int(st['measurements'])} medicoes brutas e {fmt_int(st['valid_pairs'])} pares validos, conclui-se que GraphQL retornou respostas substancialmente menores que REST em todos os cenarios analisados. Para tempo de resposta, GraphQL foi mais rapido em consultas de PRs, issues e dados combinados, mas nao na consulta simples de metadados.</p>
    <p>Assim, a resposta final para RQ1 e parcialmente favoravel a GraphQL: ha vantagem em cenarios mais ricos, mas nao em todos os casos. A resposta para RQ2 e favoravel a GraphQL: as respostas foram consistentemente menores.</p>

    <h3>6.1 - Trabalhos futuros</h3>
    <p>Como trabalhos futuros, seria interessante repetir o experimento em outras APIs que tambem oferecam REST e GraphQL, comparar diferentes linguagens de repositorios, executar medicoes em horarios distintos e incluir tamanho compactado como metrica complementar.</p>
  </section>

  <section>
    <h2>7 - Reprodutibilidade</h2>
    <p>Os scripts e dados estao organizados em `enunciado5/`. A amostra foi gerada em `data/top_python_repos.csv`, as medicoes brutas em `output/measurements.csv` e as tabelas finais em `output/analysis/`.</p>
    <p>Comandos principais:</p>
    <pre>python enunciado5/scripts/collect_top_python_repos.py
python enunciado5/scripts/run_experiment.py --runs 30 --scenarios C1,C2,C3,C4
python enunciado5/scripts/prepare_analysis_data.py
python enunciado5/scripts/generate_figures.py
python enunciado5/scripts/generate_final_artifacts.py</pre>
  </section>
</body>
</html>"""


def build_dashboard_html(data: Dict[str, pd.DataFrame]) -> str:
    st = stats(data)
    wilcoxon = data["wilcoxon"]
    paired = data["paired"]
    repos = data["repos"].copy()
    time_rows = wilcoxon[wilcoxon["metric"] == "elapsed_ms"].sort_values("scenario_id")
    size_rows = wilcoxon[wilcoxon["metric"] == "response_bytes"].sort_values("scenario_id")
    labels = [str(v) for v in time_rows["scenario_id"].tolist()]

    rest_time = [float(v) for v in time_rows["rest_median"].tolist()]
    gql_time = [float(v) for v in time_rows["graphql_median"].tolist()]
    rest_size_kb = [float(v) / 1000.0 for v in size_rows["rest_median"].tolist()]
    gql_size_kb = [float(v) / 1000.0 for v in size_rows["graphql_median"].tolist()]
    time_delta = [float(v) for v in time_rows["median_delta_pct"].tolist()]
    size_delta = [float(v) for v in size_rows["median_delta_pct"].tolist()]

    gql_time_wins = (paired["graphql_elapsed_ms"] < paired["rest_elapsed_ms"]).mean() * 100.0
    gql_size_wins = (paired["graphql_response_bytes"] < paired["rest_response_bytes"]).mean() * 100.0
    c4_gain = abs(float(time_rows[time_rows["scenario_id"] == "C4"]["median_delta_pct"].iloc[0]))
    size_gain = abs(float(size_rows["median_delta_pct"].median()))
    rest_requests = paired["rest_request_count"].mean()
    gql_requests = paired["graphql_request_count"].mean()

    time_chart = dashboard_grouped_bar_svg("Tempo mediano por cenario", labels, rest_time, gql_time, " ms")
    size_chart = dashboard_grouped_bar_svg("Tamanho mediano por cenario", labels, rest_size_kb, gql_size_kb, " KB")
    time_delta_chart = dashboard_single_bar_svg("Delta de tempo GraphQL vs REST", labels, time_delta, "%", color="#10b8aa")
    size_delta_chart = dashboard_single_bar_svg("Reducao de tamanho GraphQL", labels, size_delta, "%", color="#10b8aa")
    donut_time = dashboard_donut_svg("GraphQL mais rapido", gql_time_wins, "dos pares")
    donut_size = dashboard_donut_svg("GraphQL menor", gql_size_wins, "dos pares")

    repos["short_name"] = repos["full_name"].astype(str).str.replace("EbookFoundation/", "Ebook/", regex=False)
    top_repo_rows = []
    for _, row in repos.sort_values("stargazers_count", ascending=False).head(5).iterrows():
        top_repo_rows.append(
            [
                str(row["rank"]),
                str(row["short_name"])[:28],
                fmt_int(float(row["stargazers_count"])),
            ]
        )
    dataset_table = table_html(["#", "Repositorio", "Stars"], top_repo_rows, "compact-table")
    stars_median = float(repos["stargazers_count"].median())
    forks_median = float(repos["forks_count"].median())
    issues_median = float(repos["open_issues_count"].median())

    css = """
    :root { --ink:#17202a; --muted:#63717a; --line:#dfe5e8; --rest:#33464d; --gql:#10b8aa; --accent:#ff5a5f; --bg:#eceff1; --panel:#ffffff; }
    * { box-sizing: border-box; }
    html, body { min-height:100%; }
    body { margin:0; font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; background:var(--bg); color:var(--ink); }
    .board { height:100vh; overflow:hidden; padding:8px; display:grid; grid-template-columns:repeat(12, minmax(0,1fr)); grid-template-rows:repeat(6, minmax(0,1fr)); gap:8px; }
    .tile { background:var(--panel); border:1px solid var(--line); box-shadow:0 1px 3px rgba(0,0,0,.05); padding:12px; overflow:hidden; min-width:0; min-height:0; }
    .tile h2, .tile h3 { margin:0 0 8px; font-size:12px; text-transform:uppercase; color:#536169; letter-spacing:.02em; }
    .hero { grid-column:1 / 5; grid-row:1 / 3; display:flex; flex-direction:column; justify-content:space-between; }
    .hero h1 { margin:0; font-size:28px; line-height:1.05; letter-spacing:0; }
    .hero p { margin:8px 0 0; color:var(--muted); font-size:13px; line-height:1.35; }
    .kpi { display:flex; flex-direction:column; justify-content:space-between; }
    .k1 { grid-column:5 / 7; grid-row:1 / 2; }
    .k2 { grid-column:7 / 9; grid-row:1 / 2; }
    .k3 { grid-column:9 / 11; grid-row:1 / 2; }
    .k4 { grid-column:11 / 13; grid-row:1 / 2; }
    .kpi strong { font-size:29px; line-height:1; font-weight:500; color:#24323a; }
    .kpi span { font-size:12px; color:var(--muted); text-transform:uppercase; }
    .kpi small { color:var(--muted); font-size:11px; }
    .time-chart { grid-column:5 / 10; grid-row:2 / 5; }
    .size-chart { grid-column:1 / 5; grid-row:3 / 5; }
    .donut-time { grid-column:10 / 13; grid-row:2 / 4; }
    .donut-size { grid-column:5 / 7; grid-row:5 / 7; }
    .delta-time { grid-column:7 / 10; grid-row:5 / 7; }
    .delta-size { grid-column:1 / 5; grid-row:5 / 7; }
    .dataset-tile { grid-column:10 / 13; grid-row:4 / 6; }
    .result { grid-column:10 / 13; grid-row:6 / 7; background:#17202a; color:#fff; }
    .result h2 { color:#a7b2b8; }
    .result strong { display:block; font-size:18px; line-height:1.1; margin-bottom:5px; }
    .result p { margin:0; color:#d8e0e4; line-height:1.25; font-size:11px; }
    .svg-chart { width:100%; height:100%; display:block; }
    .donut { width:100%; height:100%; display:block; }
    table { width:100%; border-collapse:collapse; font-size:12px; }
    th,td { border-bottom:1px solid var(--line); padding:5px 5px; text-align:left; white-space:nowrap; }
    th { color:#536169; font-weight:700; font-size:11px; text-transform:uppercase; }
    .legend-line { display:flex; gap:12px; align-items:center; color:var(--muted); font-size:12px; }
    .dot { width:10px; height:10px; display:inline-block; border-radius:50%; margin-right:5px; }
    .progress { height:12px; background:#edf2f4; margin-top:10px; position:relative; }
    .progress span { position:absolute; left:0; top:0; bottom:0; width:99.98%; background:var(--gql); }
    @media (max-width: 1000px) {
      .board { height:auto; overflow:visible; grid-template-columns:repeat(6, 1fr); grid-auto-rows:minmax(110px, auto); }
      .hero,.time-chart,.size-chart,.delta-size,.dataset-tile,.result { grid-column:span 6; grid-row:auto; }
      .kpi,.donut-time,.donut-size,.delta-time { grid-column:span 3; grid-row:auto; }
    }
    .dataset-stats { display:grid; grid-template-columns:repeat(3, 1fr); gap:6px; margin:6px 0 8px; }
    .dataset-stats div { background:#f3f6f8; padding:6px; min-width:0; }
    .dataset-stats span { display:block; color:var(--muted); font-size:10px; text-transform:uppercase; }
    .dataset-stats strong { font-size:15px; font-weight:600; }
    @media (max-width: 620px) { .board { grid-template-columns:1fr; } .hero,.time-chart,.size-chart,.delta-size,.dataset-tile,.result,.kpi,.donut-time,.donut-size,.delta-time { grid-column:span 1; grid-row:auto; } }
    """

    return f"""<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Dashboard Lab05 - GraphQL vs REST</title>
  <style>{css}</style>
</head>
<body>
  <main class="board">
    <section class="tile hero">
      <div>
        <h1>GraphQL vs REST</h1>
        <p>Experimento controlado com API do GitHub, repositorios Python populares e quatro cenarios comparaveis.</p>
      </div>
      <div>
        <div class="legend-line"><span><i class="dot" style="background:var(--rest)"></i>REST</span><span><i class="dot" style="background:var(--gql)"></i>GraphQL</span><span><i class="dot" style="background:var(--accent)"></i>pior caso GQL</span></div>
        <div class="progress"><span></span></div>
      </div>
    </section>

    <section class="tile kpi k1"><span>Medicoes</span><strong>{fmt_int(st["measurements"])}</strong><small>coleta completa</small></section>
    <section class="tile kpi k2"><span>Pares validos</span><strong>{fmt_int(st["valid_pairs"])}</strong><small>REST + GraphQL</small></section>
    <section class="tile kpi k3"><span>Repositorios</span><strong>{fmt_int(st["repos"])}</strong><small>Python populares</small></section>
    <section class="tile kpi k4"><span>Falhas</span><strong>{fmt_int(st["failures"])}</strong><small>descartadas</small></section>

    <section class="tile time-chart">{time_chart}</section>
    <section class="tile size-chart">{size_chart}</section>
    <section class="tile donut-time">{donut_time}</section>
    <section class="tile donut-size">{donut_size}</section>

    <section class="tile delta-time">{time_delta_chart}</section>
    <section class="tile delta-size">{size_delta_chart}</section>

    <section class="tile dataset-tile">
      <h2>Dataset</h2>
      <div class="dataset-stats">
        <div><span>Stars med.</span><strong>{fmt_int(stars_median)}</strong></div>
        <div><span>Forks med.</span><strong>{fmt_int(forks_median)}</strong></div>
        <div><span>Issues med.</span><strong>{fmt_int(issues_median)}</strong></div>
      </div>
      {dataset_table}
    </section>

    <section class="tile result">
      <h2>Resultado para fala</h2>
      <strong>GraphQL vence em tamanho; tempo depende do cenario.</strong>
      <p>C1 fica competitivo para REST. C2, C3 e principalmente C4 favorecem GraphQL.</p>
    </section>
  </main>
</body>
</html>"""


def main() -> int:
    data = load_data()
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    DASHBOARD_DIR.mkdir(parents=True, exist_ok=True)

    report_html = build_report_html(data)
    dashboard_html = build_dashboard_html(data)

    (REPORT_DIR / "relatorio_final_lab05.html").write_text(report_html, encoding="utf-8")
    (DASHBOARD_DIR / "dashboard.html").write_text(dashboard_html, encoding="utf-8")

    print(f"Wrote {REPORT_DIR / 'relatorio_final_lab05.html'}")
    print(f"Wrote {DASHBOARD_DIR / 'dashboard.html'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
