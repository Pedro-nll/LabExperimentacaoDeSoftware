from __future__ import annotations

import html
import os
from pathlib import Path

os.environ.setdefault("MPLBACKEND", "Agg")

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "outputs"
FIGURES_DIR = OUTPUT_DIR / "figures"
DASHBOARD_DIR = OUTPUT_DIR / "dashboard"
TABLES_DIR = OUTPUT_DIR / "tables"
MPL_CACHE_DIR = OUTPUT_DIR / ".mplcache"

for directory in (FIGURES_DIR, DASHBOARD_DIR, TABLES_DIR, MPL_CACHE_DIR):
    directory.mkdir(parents=True, exist_ok=True)

os.environ.setdefault("MPLCONFIGDIR", str(MPL_CACHE_DIR))

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import seaborn as sns


POLICY_LABELS = {
    "With AI Policy": "Com politica de IA",
    "Without AI Policy": "Sem politica de IA",
}

POLICY_ORDER = ["Without AI Policy", "With AI Policy"]
POLICY_COLORS = {
    "Sem politica de IA": "#4C78A8",
    "Com politica de IA": "#2A9D8F",
}
CLUSTER_COLOR = "#6F6A9E"
SECONDARY_COLOR = "#E9C46A"

sns.set_theme(
    style="whitegrid",
    context="notebook",
    rc={
        "figure.dpi": 140,
        "savefig.dpi": 180,
        "axes.titlesize": 13,
        "axes.labelsize": 10,
        "xtick.labelsize": 9,
        "ytick.labelsize": 9,
        "font.family": "DejaVu Sans",
    },
)


def read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Arquivo nao encontrado: {path}")
    return pd.read_csv(path)


def require_columns(df: pd.DataFrame, cols: list[str], name: str) -> None:
    missing = [col for col in cols if col not in df.columns]
    if missing:
        raise ValueError(f"{name} nao possui as colunas esperadas: {missing}")


def savefig(name: str) -> None:
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / name, bbox_inches="tight", facecolor="white")
    plt.close()


def policy_label(value: str) -> str:
    return POLICY_LABELS.get(value, value)


def add_bar_labels(ax, fmt="{:.0f}", padding=3):
    for container in ax.containers:
        ax.bar_label(container, fmt=fmt, padding=padding, fontsize=8)


def format_float(value: float, decimals: int = 1) -> str:
    return f"{value:,.{decimals}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def build_enriched_top_repos(top_repos: pd.DataFrame, policy_repos: pd.DataFrame) -> pd.DataFrame:
    require_columns(top_repos, ["repo_name", "link", "stars", "most_recent_activity", "age_days"], "top_repos_filtered.csv")
    require_columns(policy_repos, ["repo"], "rq1_repository_policy_summary.csv")

    policy_set = set(policy_repos["repo"].dropna().astype(str))
    enriched = top_repos.copy()
    enriched["has_ai_policy"] = np.where(
        enriched["repo_name"].astype(str).isin(policy_set),
        "With AI Policy",
        "Without AI Policy",
    )
    enriched["has_ai_policy_label"] = enriched["has_ai_policy"].map(policy_label)
    enriched["age_years"] = enriched["age_days"] / 365
    return enriched


def save_clean_tables(
    top_repos: pd.DataFrame,
    enriched_top_repos: pd.DataFrame,
    adoption: pd.DataFrame,
    clusters: pd.DataFrame,
    rq2_policy: pd.DataFrame,
    rq3_policy: pd.DataFrame,
) -> pd.DataFrame:
    top_repos.to_csv(TABLES_DIR / "cleaned_top_repos.csv", index=False)
    enriched_top_repos.to_csv(TABLES_DIR / "cleaned_top_repos_with_policy_presence.csv", index=False)
    adoption.to_csv(TABLES_DIR / "cleaned_rq1_adoption.csv", index=False)
    clusters.to_csv(TABLES_DIR / "cleaned_rq1_clusters.csv", index=False)
    rq2_policy.to_csv(TABLES_DIR / "cleaned_rq2_engagement_policy_presence.csv", index=False)
    rq3_policy.to_csv(TABLES_DIR / "cleaned_rq3_collaboration_policy_presence.csv", index=False)

    profile = (
        enriched_top_repos.groupby("has_ai_policy_label", as_index=False)
        .agg(
            n_repositories=("repo_name", "count"),
            median_stars=("stars", "median"),
            mean_stars=("stars", "mean"),
            median_age_days=("age_days", "median"),
            mean_age_days=("age_days", "mean"),
        )
        .sort_values("has_ai_policy_label")
    )
    profile.to_csv(TABLES_DIR / "complementary_policy_presence_by_repository_profile.csv", index=False)
    return profile


def plot_dataset_figures(top_repos: pd.DataFrame, enriched: pd.DataFrame) -> None:
    plt.figure(figsize=(8, 4.5))
    sns.histplot(top_repos["stars"], bins=35, color="#4C78A8")
    plt.xscale("log")
    plt.title("Distribuicao de estrelas dos repositorios")
    plt.xlabel("Estrelas (escala logaritmica)")
    plt.ylabel("Quantidade de repositorios")
    savefig("dataset_stars_distribution.png")

    plt.figure(figsize=(8, 4.5))
    sns.histplot(top_repos["age_days"] / 365, bins=30, color="#2A9D8F")
    plt.title("Distribuicao da idade dos repositorios")
    plt.xlabel("Idade do repositorio (anos)")
    plt.ylabel("Quantidade de repositorios")
    savefig("dataset_age_distribution.png")

    plt.figure(figsize=(8, 5))
    sns.scatterplot(
        data=top_repos,
        x="age_days",
        y="stars",
        color="#4C78A8",
        alpha=0.65,
        edgecolor=None,
        s=26,
    )
    plt.yscale("log")
    plt.title("Relacao entre idade e estrelas")
    plt.xlabel("Idade do repositorio (dias)")
    plt.ylabel("Estrelas (escala logaritmica)")
    savefig("dataset_age_vs_stars.png")

    top15 = top_repos.nlargest(15, "stars").sort_values("stars")
    plt.figure(figsize=(9, 6))
    sns.barplot(data=top15, y="repo_name", x="stars", color="#6F6A9E")
    plt.title("Top 15 repositorios por estrelas")
    plt.xlabel("Estrelas")
    plt.ylabel("")
    savefig("dataset_top_repositories_by_stars.png")

    plt.figure(figsize=(8, 5))
    sns.scatterplot(
        data=enriched,
        x="age_days",
        y="stars",
        hue="has_ai_policy_label",
        hue_order=["Sem politica de IA", "Com politica de IA"],
        palette=POLICY_COLORS,
        alpha=0.72,
        edgecolor=None,
        s=30,
    )
    plt.yscale("log")
    plt.title("Idade vs. estrelas por presenca de politica de IA")
    plt.xlabel("Idade do repositorio (dias)")
    plt.ylabel("Estrelas (escala logaritmica)")
    plt.legend(title="")
    savefig("complementary_age_vs_stars_by_policy_presence.png")


def plot_rq1_figures(adoption: pd.DataFrame, clusters: pd.DataFrame) -> dict[str, float]:
    require_columns(adoption, ["metric", "value"], "rq1_adoption_summary.csv")
    require_columns(
        clusters,
        [
            "cluster",
            "cluster_label",
            "unique_repositories",
            "percentage_of_policy_repositories",
            "median_policy_words",
            "mean_policy_words",
        ],
        "rq1_cluster_summary.csv",
    )
    metrics = dict(zip(adoption["metric"], adoption["value"]))

    adoption_plot = pd.DataFrame(
        {
            "Grupo": ["Com politica de IA", "Sem politica de IA"],
            "Repositorios": [
                float(metrics["repositories_with_policy"]),
                float(metrics["repositories_without_policy"]),
            ],
        }
    )
    plt.figure(figsize=(7, 4.5))
    ax = sns.barplot(
        data=adoption_plot,
        x="Grupo",
        y="Repositorios",
        palette=[POLICY_COLORS["Com politica de IA"], POLICY_COLORS["Sem politica de IA"]],
        hue="Grupo",
        legend=False,
    )
    add_bar_labels(ax, fmt="{:.0f}")
    plt.title("Adocao de politicas de IA")
    plt.xlabel("")
    plt.ylabel("Quantidade de repositorios")
    savefig("rq1_policy_adoption.png")

    cluster_sorted = clusters.sort_values("unique_repositories")
    plt.figure(figsize=(9, 5))
    ax = sns.barplot(data=cluster_sorted, y="cluster_label", x="unique_repositories", color=CLUSTER_COLOR)
    add_bar_labels(ax, fmt="{:.0f}")
    plt.title("Distribuicao dos tipos de politica")
    plt.xlabel("Repositorios unicos")
    plt.ylabel("")
    savefig("rq1_cluster_distribution.png")

    plt.figure(figsize=(9, 5))
    ax = sns.barplot(data=cluster_sorted, y="cluster_label", x="percentage_of_policy_repositories", color="#2A9D8F")
    add_bar_labels(ax, fmt="{:.1f}%")
    plt.title("Percentual dos clusters entre repositorios com politica")
    plt.xlabel("Percentual dos repositorios com politica")
    plt.ylabel("")
    savefig("rq1_cluster_percentages.png")

    text_size = clusters.melt(
        id_vars=["cluster_label"],
        value_vars=["median_policy_words", "mean_policy_words"],
        var_name="Metrica",
        value_name="Palavras",
    )
    text_size["Metrica"] = text_size["Metrica"].map(
        {
            "median_policy_words": "Mediana",
            "mean_policy_words": "Media",
        }
    )
    plt.figure(figsize=(10, 5))
    ax = sns.barplot(data=text_size, x="Palavras", y="cluster_label", hue="Metrica", palette=[CLUSTER_COLOR, SECONDARY_COLOR])
    add_bar_labels(ax, fmt="{:.1f}", padding=2)
    plt.title("Tamanho dos textos de politica por cluster")
    plt.xlabel("Quantidade de palavras")
    plt.ylabel("")
    plt.legend(title="")
    savefig("rq1_policy_text_size_by_cluster.png")

    return metrics


def plot_rq2_figures(rq2_policy: pd.DataFrame) -> None:
    rq2 = rq2_policy.copy()
    rq2["Grupo"] = rq2["has_ai_policy"].map(policy_label)
    rq2["order"] = rq2["has_ai_policy"].map({value: idx for idx, value in enumerate(POLICY_ORDER)})
    rq2 = rq2.sort_values("order")

    simple_specs = [
        ("rq2_prs_total_by_policy_presence.png", "prs_total_median", "Mediana de PRs totais por presenca de politica de IA", "PRs totais (mediana)"),
        ("rq2_prs_merged_by_policy_presence.png", "prs_merged_median", "Mediana de PRs mergeadas por presenca de politica de IA", "PRs mergeadas (mediana)"),
        ("rq2_issues_total_by_policy_presence.png", "issues_total_median", "Mediana de issues totais por presenca de politica de IA", "Issues totais (mediana)"),
        ("rq2_unique_collaborators_by_policy_presence.png", "unique_collaborators_median", "Mediana de colaboradores unicos por presenca de politica de IA", "Colaboradores unicos (mediana)"),
    ]
    for filename, metric, title, ylabel in simple_specs:
        plt.figure(figsize=(7, 4.5))
        ax = sns.barplot(data=rq2, x="Grupo", y=metric, hue="Grupo", palette=POLICY_COLORS, legend=False)
        add_bar_labels(ax, fmt="{:.1f}")
        plt.title(title)
        plt.xlabel("")
        plt.ylabel(ylabel)
        savefig(filename)

    comments = rq2.melt(
        id_vars=["Grupo"],
        value_vars=["avg_pr_comments_median", "avg_issue_comments_median", "avg_pr_reviews_median"],
        var_name="Metrica",
        value_name="Valor",
    )
    comments["Metrica"] = comments["Metrica"].map(
        {
            "avg_pr_comments_median": "Comentarios por PR",
            "avg_issue_comments_median": "Comentarios por issue",
            "avg_pr_reviews_median": "Reviews por PR",
        }
    )
    plt.figure(figsize=(9, 5))
    ax = sns.barplot(data=comments, x="Metrica", y="Valor", hue="Grupo", palette=POLICY_COLORS)
    add_bar_labels(ax, fmt="{:.2f}", padding=2)
    plt.title("Comentarios e reviews por presenca de politica de IA")
    plt.xlabel("")
    plt.ylabel("Valor mediano")
    plt.legend(title="")
    savefig("rq2_comments_reviews_by_policy_presence.png")

    heat_cols = [
        "prs_total_median",
        "prs_merged_median",
        "issues_total_median",
        "unique_collaborators_median",
        "avg_pr_comments_median",
        "avg_issue_comments_median",
        "avg_pr_reviews_median",
    ]
    heat = rq2.set_index("Grupo")[heat_cols]
    heat_norm = (heat - heat.min()) / (heat.max() - heat.min())
    heat_norm = heat_norm.fillna(0)
    heat_norm.columns = [
        "PRs totais",
        "PRs mergeadas",
        "Issues totais",
        "Colaboradores",
        "Com. PR",
        "Com. issue",
        "Reviews PR",
    ]
    plt.figure(figsize=(10, 3.2))
    sns.heatmap(heat_norm, annot=heat.round(2), fmt=".2f", cmap="YlGnBu", cbar_kws={"label": "Valor normalizado"})
    plt.title("Heatmap de engajamento por presenca de politica")
    plt.xlabel("")
    plt.ylabel("")
    savefig("rq2_engagement_heatmap.png")


def plot_rq3_figures(rq3_policy: pd.DataFrame) -> None:
    rq3 = rq3_policy.copy()
    rq3["Grupo"] = rq3["has_ai_policy"].map(policy_label)
    rq3["order"] = rq3["has_ai_policy"].map({value: idx for idx, value in enumerate(POLICY_ORDER)})
    rq3 = rq3.sort_values("order")

    simple_specs = [
        ("rq3_merge_rate_by_policy_presence.png", "prs_merge_rate_median", "Taxa mediana de merge por presenca de politica de IA", "Taxa de merge (%)", "{:.1f}%"),
        ("rq3_closed_no_merge_rate_by_policy_presence.png", "prs_closed_no_merge_rate_median", "Taxa mediana de fechamento sem merge", "Taxa de fechamento sem merge (%)", "{:.1f}%"),
    ]
    for filename, metric, title, ylabel, fmt in simple_specs:
        plt.figure(figsize=(7, 4.5))
        ax = sns.barplot(data=rq3, x="Grupo", y=metric, hue="Grupo", palette=POLICY_COLORS, legend=False)
        add_bar_labels(ax, fmt=fmt)
        plt.title(title)
        plt.xlabel("")
        plt.ylabel(ylabel)
        savefig(filename)

    cycle = rq3[["Grupo", "median_pr_cycle_hours_median", "mean_pr_cycle_hours_median"]].copy()
    cycle["Ciclo mediano do PR"] = cycle["median_pr_cycle_hours_median"] / 24
    cycle["Tempo medio de ciclo do PR"] = cycle["mean_pr_cycle_hours_median"] / 24
    cycle_long = cycle.melt(id_vars=["Grupo"], value_vars=["Ciclo mediano do PR", "Tempo medio de ciclo do PR"], var_name="Metrica", value_name="Dias")
    plt.figure(figsize=(8, 5))
    ax = sns.barplot(data=cycle_long, x="Metrica", y="Dias", hue="Grupo", palette=POLICY_COLORS)
    add_bar_labels(ax, fmt="{:.1f}", padding=2)
    plt.title("Tempo de ciclo de PR por presenca de politica")
    plt.xlabel("")
    plt.ylabel("Dias")
    plt.legend(title="")
    savefig("rq3_pr_cycle_time_by_policy_presence.png")

    response = rq3.melt(
        id_vars=["Grupo"],
        value_vars=["median_issue_first_response_hours_median", "median_pr_first_response_hours_median"],
        var_name="Metrica",
        value_name="Horas",
    )
    response["Metrica"] = response["Metrica"].map(
        {
            "median_issue_first_response_hours_median": "Primeira resposta em issue",
            "median_pr_first_response_hours_median": "Primeira resposta em PR",
        }
    )
    plt.figure(figsize=(8, 5))
    ax = sns.barplot(data=response, x="Metrica", y="Horas", hue="Grupo", palette=POLICY_COLORS)
    add_bar_labels(ax, fmt="{:.1f} h", padding=2)
    plt.title("Tempo ate primeira resposta")
    plt.xlabel("")
    plt.ylabel("Horas")
    plt.legend(title="")
    savefig("rq3_first_response_time_by_policy_presence.png")

    plt.figure(figsize=(7, 4.5))
    ax = sns.barplot(data=rq3, x="Grupo", y="median_pr_first_review_hours_median", hue="Grupo", palette=POLICY_COLORS, legend=False)
    add_bar_labels(ax, fmt="{:.1f} h")
    plt.title("Tempo ate primeira revisao em PR")
    plt.xlabel("")
    plt.ylabel("Horas")
    savefig("rq3_first_review_time_by_policy_presence.png")

    stability = rq3.melt(
        id_vars=["Grupo"],
        value_vars=["avg_pr_commits_median", "avg_pr_reviews_median", "avg_reviews_until_approval_median"],
        var_name="Metrica",
        value_name="Valor",
    )
    stability["Metrica"] = stability["Metrica"].map(
        {
            "avg_pr_commits_median": "Commits por PR",
            "avg_pr_reviews_median": "Reviews por PR",
            "avg_reviews_until_approval_median": "Reviews ate aprovacao",
        }
    )
    plt.figure(figsize=(9, 5))
    ax = sns.barplot(data=stability, x="Metrica", y="Valor", hue="Grupo", palette=POLICY_COLORS)
    add_bar_labels(ax, fmt="{:.2f}", padding=2)
    plt.title("Estabilidade do processo colaborativo")
    plt.xlabel("")
    plt.ylabel("Valor mediano")
    plt.legend(title="")
    savefig("rq3_process_stability_by_policy_presence.png")

    heat_cols = [
        "prs_merge_rate_median",
        "prs_closed_no_merge_rate_median",
        "median_pr_cycle_hours_median",
        "median_issue_first_response_hours_median",
        "median_pr_first_response_hours_median",
        "median_pr_first_review_hours_median",
        "avg_pr_commits_median",
        "avg_pr_reviews_median",
        "avg_reviews_until_approval_median",
    ]
    heat = rq3.set_index("Grupo")[heat_cols]
    heat_norm = (heat - heat.min()) / (heat.max() - heat.min())
    heat_norm = heat_norm.fillna(0)
    heat_norm.columns = [
        "Merge",
        "Sem merge",
        "Ciclo PR",
        "Resp. issue",
        "Resp. PR",
        "Review PR",
        "Commits",
        "Reviews",
        "Aprovacao",
    ]
    plt.figure(figsize=(11, 3.2))
    sns.heatmap(heat_norm, annot=heat.round(2), fmt=".2f", cmap="YlGnBu", cbar_kws={"label": "Valor normalizado"})
    plt.title("Heatmap de colaboracao por presenca de politica")
    plt.xlabel("")
    plt.ylabel("")
    savefig("rq3_collaboration_heatmap.png")


def plot_complementary_figures(enriched: pd.DataFrame) -> None:
    order = ["Sem politica de IA", "Com politica de IA"]

    plt.figure(figsize=(7, 4.8))
    sns.boxplot(data=enriched, x="has_ai_policy_label", y="stars", order=order, palette=POLICY_COLORS, hue="has_ai_policy_label", legend=False)
    plt.yscale("log")
    plt.title("Distribuicao de estrelas por presenca de politica")
    plt.xlabel("")
    plt.ylabel("Estrelas (escala logaritmica)")
    savefig("complementary_stars_by_policy_presence.png")

    plt.figure(figsize=(7, 4.8))
    sns.boxplot(data=enriched, x="has_ai_policy_label", y="age_years", order=order, palette=POLICY_COLORS, hue="has_ai_policy_label", legend=False)
    plt.title("Distribuicao de idade por presenca de politica")
    plt.xlabel("")
    plt.ylabel("Idade do repositorio (anos)")
    savefig("complementary_age_by_policy_presence.png")

    stars_groups = pd.qcut(
        enriched["stars"],
        q=4,
        labels=["Q1 - Menos estrelas", "Q2", "Q3", "Q4 - Mais estrelas"],
        duplicates="drop",
    )
    stars_adoption = (
        enriched.assign(stars_group=stars_groups)
        .groupby("stars_group", observed=True)
        .agg(policy_rate=("has_ai_policy", lambda values: (values == "With AI Policy").mean() * 100), n=("repo_name", "count"))
        .reset_index()
    )
    plt.figure(figsize=(8, 4.8))
    ax = sns.barplot(data=stars_adoption, x="stars_group", y="policy_rate", color="#2A9D8F")
    add_bar_labels(ax, fmt="{:.1f}%")
    plt.title("Taxa de adocao por faixa de estrelas")
    plt.xlabel("Faixa de estrelas")
    plt.ylabel("Repositorios com politica (%)")
    savefig("complementary_policy_adoption_by_stars_group.png")

    age_groups = pd.qcut(
        enriched["age_days"],
        q=4,
        labels=["Q1 - Mais recentes", "Q2", "Q3", "Q4 - Mais antigos"],
        duplicates="drop",
    )
    age_adoption = (
        enriched.assign(age_group=age_groups)
        .groupby("age_group", observed=True)
        .agg(policy_rate=("has_ai_policy", lambda values: (values == "With AI Policy").mean() * 100), n=("repo_name", "count"))
        .reset_index()
    )
    plt.figure(figsize=(8, 4.8))
    ax = sns.barplot(data=age_adoption, x="age_group", y="policy_rate", color="#6F6A9E")
    add_bar_labels(ax, fmt="{:.1f}%")
    plt.title("Taxa de adocao por faixa de idade")
    plt.xlabel("Faixa de idade")
    plt.ylabel("Repositorios com politica (%)")
    savefig("complementary_policy_adoption_by_age_group.png")


def table_html(df: pd.DataFrame, columns: list[str] | None = None, max_rows: int = 8) -> str:
    shown = df.copy()
    if columns:
        shown = shown[columns]
    shown = shown.head(max_rows)
    return shown.to_html(index=False, classes="data-table", border=0, escape=True)


def image_card(filename: str, caption: str) -> str:
    return f"""
    <figure class="viz">
      <button class="image-open" type="button" data-full="../figures/{html.escape(filename)}" data-caption="{html.escape(caption)}" aria-label="Abrir grafico: {html.escape(caption)}">
        <img src="../figures/{html.escape(filename)}" alt="{html.escape(caption)}">
      </button>
      <figcaption>{html.escape(caption)}</figcaption>
    </figure>
    """


def plotly_card(title: str, chart_html: str, caption: str, wide: bool = False) -> str:
    card_class = "viz chart-card chart-card-wide" if wide else "viz chart-card"
    return f"""
    <figure class="{card_class}">
      <h3>{html.escape(title)}</h3>
      <div class="chart-frame">{chart_html}</div>
      <figcaption>{html.escape(caption)}</figcaption>
    </figure>
    """


def plotly_fragment(fig: go.Figure, include_plotlyjs: bool = False, height: int = 430) -> str:
    fig.update_layout(
        template="plotly_white",
        title=None,
        height=height,
        margin=dict(l=64, r=24, t=18, b=72),
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff",
        font=dict(family="system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif", size=12, color="#17202a"),
        hoverlabel=dict(bgcolor="#17202a", font_color="#ffffff"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    )
    fig.update_xaxes(automargin=True)
    fig.update_yaxes(automargin=True)
    return fig.to_html(
        full_html=False,
        include_plotlyjs=include_plotlyjs,
        config={"displaylogo": False, "responsive": True},
        default_width="100%",
        default_height=f"{height}px",
    )


def heatmap_figure(data: pd.DataFrame, title: str) -> go.Figure:
    normalized = (data - data.min()) / (data.max() - data.min())
    normalized = normalized.fillna(0)
    fig = go.Figure(
        data=go.Heatmap(
            z=normalized.values,
            x=list(normalized.columns),
            y=list(normalized.index),
            text=data.round(2).astype(str).values,
            texttemplate="%{text}",
            colorscale="YlGnBu",
            colorbar=dict(title="Normalizado"),
            hovertemplate="Grupo: %{y}<br>Metrica: %{x}<br>Valor normalizado: %{z:.2f}<br>Valor real: %{text}<extra></extra>",
        )
    )
    fig.update_layout(title=title)
    return fig


def build_interactive_charts(
    top_repos: pd.DataFrame,
    enriched: pd.DataFrame,
    adoption_metrics: dict[str, float],
    clusters: pd.DataFrame,
    rq2_policy: pd.DataFrame,
    rq3_policy: pd.DataFrame,
) -> dict[str, str]:
    charts: dict[str, str] = {}
    include_js = True

    def add(name: str, fig: go.Figure, height: int = 430) -> None:
        nonlocal include_js
        charts[name] = plotly_fragment(fig, include_plotlyjs=include_js, height=height)
        include_js = False

    fig = px.histogram(
        top_repos.assign(age_years=top_repos["age_days"] / 365),
        x="age_years",
        nbins=30,
        title="Distribuicao da idade dos repositorios",
        labels={"age_years": "Idade do repositorio (anos)", "count": "Quantidade"},
        color_discrete_sequence=["#2A9D8F"],
    )
    fig.update_traces(hovertemplate="Idade: %{x:.1f} anos<br>Repositorios: %{y}<extra></extra>")
    add("dataset_age_distribution", fig, height=400)

    star_bins = np.logspace(
        np.log10(top_repos["stars"].min()),
        np.log10(top_repos["stars"].max()),
        26,
    )
    star_distribution = (
        pd.cut(top_repos["stars"], bins=star_bins, include_lowest=True)
        .value_counts()
        .sort_index()
        .reset_index()
    )
    star_distribution.columns = ["Faixa", "Repositorios"]
    star_distribution["Inicio"] = star_distribution["Faixa"].apply(lambda interval: interval.left)
    star_distribution["Fim"] = star_distribution["Faixa"].apply(lambda interval: interval.right)
    star_distribution["Faixa"] = star_distribution.apply(
        lambda row: f"{row['Inicio'] / 1000:.0f}k-{row['Fim'] / 1000:.0f}k",
        axis=1,
    )
    fig = px.bar(
        star_distribution,
        x="Faixa",
        y="Repositorios",
        title="Distribuicao de estrelas por faixas",
        labels={"Faixa": "Faixa de estrelas", "Repositorios": "Quantidade"},
        color_discrete_sequence=["#4C78A8"],
        custom_data=["Inicio", "Fim"],
    )
    fig.update_traces(
        hovertemplate="Estrelas: %{customdata[0]:,.0f} - %{customdata[1]:,.0f}<br>Repositorios: %{y}<extra></extra>"
    )
    fig.update_xaxes(tickangle=-35)
    add("dataset_stars_distribution", fig, height=400)

    adoption_plot = pd.DataFrame(
        {
            "Grupo": ["Com politica de IA", "Sem politica de IA"],
            "Repositorios": [
                float(adoption_metrics["repositories_with_policy"]),
                float(adoption_metrics["repositories_without_policy"]),
            ],
        }
    )
    fig = px.bar(
        adoption_plot,
        x="Grupo",
        y="Repositorios",
        color="Grupo",
        color_discrete_map=POLICY_COLORS,
        text="Repositorios",
        title="Adocao de politicas de IA",
        labels={"Repositorios": "Quantidade de repositorios"},
    )
    fig.update_traces(hovertemplate="Grupo: %{x}<br>Repositorios: %{y}<extra></extra>")
    add("rq1_policy_adoption", fig)

    cluster_sorted = clusters.sort_values("unique_repositories")
    fig = px.bar(
        cluster_sorted,
        y="cluster_label",
        x="unique_repositories",
        orientation="h",
        title="Distribuicao dos tipos de politica",
        labels={"cluster_label": "", "unique_repositories": "Repositorios unicos"},
        color_discrete_sequence=[CLUSTER_COLOR],
        text="unique_repositories",
    )
    fig.update_traces(hovertemplate="Cluster: %{y}<br>Repositorios: %{x}<extra></extra>")
    add("rq1_cluster_distribution", fig, height=460)

    fig = px.bar(
        cluster_sorted,
        y="cluster_label",
        x="percentage_of_policy_repositories",
        orientation="h",
        title="Percentual dos clusters entre repositorios com politica",
        labels={"cluster_label": "", "percentage_of_policy_repositories": "Percentual dos repositorios com politica"},
        color_discrete_sequence=["#2A9D8F"],
        text="percentage_of_policy_repositories",
    )
    fig.update_traces(texttemplate="%{text:.1f}%", hovertemplate="Cluster: %{y}<br>Percentual: %{x:.1f}%<extra></extra>")
    add("rq1_cluster_percentages", fig, height=460)

    text_size = clusters.melt(
        id_vars=["cluster_label"],
        value_vars=["median_policy_words", "mean_policy_words"],
        var_name="Metrica",
        value_name="Palavras",
    )
    text_size["Metrica"] = text_size["Metrica"].map({"median_policy_words": "Mediana", "mean_policy_words": "Media"})
    fig = px.bar(
        text_size,
        x="Palavras",
        y="cluster_label",
        color="Metrica",
        orientation="h",
        barmode="group",
        title="Tamanho dos textos de politica por cluster",
        labels={"cluster_label": "", "Palavras": "Quantidade de palavras"},
        color_discrete_sequence=[CLUSTER_COLOR, SECONDARY_COLOR],
    )
    fig.update_traces(hovertemplate="Cluster: %{y}<br>Palavras: %{x:.1f}<extra></extra>")
    add("rq1_policy_text_size_by_cluster", fig, height=480)

    rq2 = rq2_policy.copy()
    rq2["Grupo"] = rq2["has_ai_policy"].map(policy_label)
    rq2["order"] = rq2["has_ai_policy"].map({value: idx for idx, value in enumerate(POLICY_ORDER)})
    rq2 = rq2.sort_values("order")
    for name, metric, title, label in [
        ("rq2_prs_total", "prs_total_median", "Mediana de PRs totais por presenca de politica de IA", "PRs totais (mediana)"),
        ("rq2_prs_merged", "prs_merged_median", "Mediana de PRs mergeadas por presenca de politica de IA", "PRs mergeadas (mediana)"),
        ("rq2_issues_total", "issues_total_median", "Mediana de issues totais por presenca de politica de IA", "Issues totais (mediana)"),
        ("rq2_unique_collaborators", "unique_collaborators_median", "Mediana de colaboradores unicos por presenca de politica de IA", "Colaboradores unicos (mediana)"),
    ]:
        fig = px.bar(rq2, x="Grupo", y=metric, color="Grupo", color_discrete_map=POLICY_COLORS, text=metric, title=title, labels={metric: label})
        fig.update_traces(hovertemplate="Grupo: %{x}<br>Valor: %{y:,.1f}<extra></extra>")
        add(name, fig)

    comments = rq2.melt(
        id_vars=["Grupo"],
        value_vars=["avg_pr_comments_median", "avg_issue_comments_median", "avg_pr_reviews_median"],
        var_name="Metrica",
        value_name="Valor",
    )
    comments["Metrica"] = comments["Metrica"].map(
        {
            "avg_pr_comments_median": "Comentarios por PR",
            "avg_issue_comments_median": "Comentarios por issue",
            "avg_pr_reviews_median": "Reviews por PR",
        }
    )
    fig = px.bar(comments, x="Metrica", y="Valor", color="Grupo", barmode="group", color_discrete_map=POLICY_COLORS, title="Comentarios e reviews por presenca de politica")
    fig.update_traces(hovertemplate="Metrica: %{x}<br>Valor mediano: %{y:.2f}<extra></extra>")
    add("rq2_comments_reviews", fig)

    heat_cols = [
        "prs_total_median",
        "prs_merged_median",
        "issues_total_median",
        "unique_collaborators_median",
        "avg_pr_comments_median",
        "avg_issue_comments_median",
        "avg_pr_reviews_median",
    ]
    heat = rq2.set_index("Grupo")[heat_cols]
    heat.columns = ["PRs totais", "PRs mergeadas", "Issues totais", "Colaboradores", "Com. PR", "Com. issue", "Reviews PR"]
    add("rq2_engagement_heatmap", heatmap_figure(heat, "Heatmap de engajamento por presenca de politica"), height=430)

    rq3 = rq3_policy.copy()
    rq3["Grupo"] = rq3["has_ai_policy"].map(policy_label)
    rq3["order"] = rq3["has_ai_policy"].map({value: idx for idx, value in enumerate(POLICY_ORDER)})
    rq3 = rq3.sort_values("order")
    for name, metric, title, label in [
        ("rq3_merge_rate", "prs_merge_rate_median", "Taxa mediana de merge por presenca de politica de IA", "Taxa de merge (%)"),
        ("rq3_closed_no_merge_rate", "prs_closed_no_merge_rate_median", "Taxa mediana de fechamento sem merge", "Taxa de fechamento sem merge (%)"),
    ]:
        fig = px.bar(rq3, x="Grupo", y=metric, color="Grupo", color_discrete_map=POLICY_COLORS, text=metric, title=title, labels={metric: label})
        fig.update_traces(texttemplate="%{text:.1f}%", hovertemplate="Grupo: %{x}<br>Valor: %{y:.1f}%<extra></extra>")
        add(name, fig)

    cycle = rq3[["Grupo", "median_pr_cycle_hours_median", "mean_pr_cycle_hours_median"]].copy()
    cycle["Ciclo mediano do PR"] = cycle["median_pr_cycle_hours_median"] / 24
    cycle["Tempo medio de ciclo do PR"] = cycle["mean_pr_cycle_hours_median"] / 24
    cycle_long = cycle.melt(id_vars=["Grupo"], value_vars=["Ciclo mediano do PR", "Tempo medio de ciclo do PR"], var_name="Metrica", value_name="Dias")
    fig = px.bar(cycle_long, y="Metrica", x="Dias", color="Grupo", barmode="group", orientation="h", color_discrete_map=POLICY_COLORS, title="Tempo de ciclo de PR por presenca de politica")
    fig.update_traces(hovertemplate="Metrica: %{y}<br>Dias: %{x:.1f}<extra></extra>")
    add("rq3_pr_cycle_time", fig, height=400)

    response = rq3.melt(
        id_vars=["Grupo"],
        value_vars=["median_issue_first_response_hours_median", "median_pr_first_response_hours_median"],
        var_name="Metrica",
        value_name="Horas",
    )
    response["Metrica"] = response["Metrica"].map(
        {
            "median_issue_first_response_hours_median": "Primeira resposta em issue",
            "median_pr_first_response_hours_median": "Primeira resposta em PR",
        }
    )
    fig = px.bar(response, y="Metrica", x="Horas", color="Grupo", barmode="group", orientation="h", color_discrete_map=POLICY_COLORS, title="Tempo ate primeira resposta")
    fig.update_traces(hovertemplate="Metrica: %{y}<br>Horas: %{x:.1f}<extra></extra>")
    add("rq3_first_response_time", fig, height=400)

    fig = px.bar(rq3, x="Grupo", y="median_pr_first_review_hours_median", color="Grupo", color_discrete_map=POLICY_COLORS, text="median_pr_first_review_hours_median", title="Tempo ate primeira revisao em PR", labels={"median_pr_first_review_hours_median": "Horas"})
    fig.update_traces(hovertemplate="Grupo: %{x}<br>Horas: %{y:.1f}<extra></extra>")
    add("rq3_first_review_time", fig)

    stability = rq3.melt(
        id_vars=["Grupo"],
        value_vars=["avg_pr_commits_median", "avg_pr_reviews_median", "avg_reviews_until_approval_median"],
        var_name="Metrica",
        value_name="Valor",
    )
    stability["Metrica"] = stability["Metrica"].map(
        {
            "avg_pr_commits_median": "Commits por PR",
            "avg_pr_reviews_median": "Reviews por PR",
            "avg_reviews_until_approval_median": "Reviews ate aprovacao",
        }
    )
    fig = px.bar(stability, y="Metrica", x="Valor", color="Grupo", barmode="group", orientation="h", color_discrete_map=POLICY_COLORS, title="Estabilidade do processo colaborativo")
    fig.update_traces(hovertemplate="Metrica: %{y}<br>Valor: %{x:.2f}<extra></extra>")
    add("rq3_process_stability", fig, height=430)

    heat_cols = [
        "prs_merge_rate_median",
        "prs_closed_no_merge_rate_median",
        "median_pr_cycle_hours_median",
        "median_issue_first_response_hours_median",
        "median_pr_first_response_hours_median",
        "median_pr_first_review_hours_median",
        "avg_pr_commits_median",
        "avg_pr_reviews_median",
        "avg_reviews_until_approval_median",
    ]
    heat = rq3.set_index("Grupo")[heat_cols]
    heat.columns = ["Merge", "Sem merge", "Ciclo PR", "Resp. issue", "Resp. PR", "Review PR", "Commits", "Reviews", "Aprovacao"]
    add("rq3_collaboration_heatmap", heatmap_figure(heat, "Heatmap de colaboracao por presenca de politica"), height=450)

    order = ["Sem politica de IA", "Com politica de IA"]
    fig = px.box(enriched, x="has_ai_policy_label", y="stars", color="has_ai_policy_label", category_orders={"has_ai_policy_label": order}, color_discrete_map=POLICY_COLORS, log_y=True, title="Distribuicao de estrelas por presenca de politica", labels={"has_ai_policy_label": "", "stars": "Estrelas (escala logaritmica)"})
    fig.update_traces(hovertemplate="Grupo: %{x}<br>Estrelas: %{y:,.0f}<extra></extra>")
    add("complementary_stars", fig)

    fig = px.box(enriched, x="has_ai_policy_label", y="age_years", color="has_ai_policy_label", category_orders={"has_ai_policy_label": order}, color_discrete_map=POLICY_COLORS, title="Distribuicao de idade por presenca de politica", labels={"has_ai_policy_label": "", "age_years": "Idade do repositorio (anos)"})
    fig.update_traces(hovertemplate="Grupo: %{x}<br>Idade: %{y:.1f} anos<extra></extra>")
    add("complementary_age", fig)

    stars_groups = pd.qcut(enriched["stars"], q=4, labels=["Q1 - Menos estrelas", "Q2", "Q3", "Q4 - Mais estrelas"], duplicates="drop")
    stars_adoption = (
        enriched.assign(stars_group=stars_groups)
        .groupby("stars_group", observed=True)
        .agg(policy_rate=("has_ai_policy", lambda values: (values == "With AI Policy").mean() * 100), n=("repo_name", "count"))
        .reset_index()
    )
    fig = px.bar(stars_adoption, x="stars_group", y="policy_rate", text="policy_rate", title="Taxa de adocao por faixa de estrelas", labels={"stars_group": "Faixa de estrelas", "policy_rate": "Repositorios com politica (%)"}, color_discrete_sequence=["#2A9D8F"])
    fig.update_traces(texttemplate="%{text:.1f}%", hovertemplate="Faixa: %{x}<br>Taxa: %{y:.1f}%<extra></extra>")
    add("complementary_policy_adoption_stars", fig)

    age_groups = pd.qcut(enriched["age_days"], q=4, labels=["Q1 - Mais recentes", "Q2", "Q3", "Q4 - Mais antigos"], duplicates="drop")
    age_adoption = (
        enriched.assign(age_group=age_groups)
        .groupby("age_group", observed=True)
        .agg(policy_rate=("has_ai_policy", lambda values: (values == "With AI Policy").mean() * 100), n=("repo_name", "count"))
        .reset_index()
    )
    fig = px.bar(age_adoption, x="age_group", y="policy_rate", text="policy_rate", title="Taxa de adocao por faixa de idade", labels={"age_group": "Faixa de idade", "policy_rate": "Repositorios com politica (%)"}, color_discrete_sequence=[CLUSTER_COLOR])
    fig.update_traces(texttemplate="%{text:.1f}%", hovertemplate="Faixa: %{x}<br>Taxa: %{y:.1f}%<extra></extra>")
    add("complementary_policy_adoption_age", fig)

    fig = px.scatter(
        enriched,
        x="age_days",
        y="stars",
        color="has_ai_policy_label",
        color_discrete_map=POLICY_COLORS,
        log_y=True,
        hover_data={"repo_name": True, "age_days": ":,.0f", "stars": ":,.0f", "has_ai_policy_label": False},
        title="Idade vs. estrelas por presenca de politica de IA",
        labels={"age_days": "Idade do repositorio (dias)", "stars": "Estrelas (escala logaritmica)", "has_ai_policy_label": ""},
    )
    add("complementary_age_vs_stars", fig, height=560)

    return charts


def metric_card(label: str, value: str, note: str = "") -> str:
    return f"""
    <div class="metric-card">
      <span>{html.escape(label)}</span>
      <strong>{html.escape(value)}</strong>
      <small>{html.escape(note)}</small>
    </div>
    """


def build_dashboard(
    top_repos: pd.DataFrame,
    enriched: pd.DataFrame,
    adoption_metrics: dict[str, float],
    clusters: pd.DataFrame,
    rq2_policy: pd.DataFrame,
    rq3_policy: pd.DataFrame,
    profile: pd.DataFrame,
) -> None:
    top5 = top_repos.nlargest(5, "stars")[["repo_name", "stars", "age_days", "most_recent_activity"]]
    cluster_top = clusters.sort_values("unique_repositories", ascending=False).iloc[0]
    with_policy_profile = profile[profile["has_ai_policy_label"] == "Com politica de IA"].iloc[0]
    without_policy_profile = profile[profile["has_ai_policy_label"] == "Sem politica de IA"].iloc[0]
    median_stars = format_float(float(top_repos["stars"].median()), 0)
    median_age_years = format_float(float((top_repos["age_days"] / 365).median()), 1)

    cards = "\n".join(
        [
            metric_card("Repositorios analisados", str(int(adoption_metrics["total_repositories"])), "amostra do GitHub"),
            metric_card("Com politica de IA", str(int(adoption_metrics["repositories_with_policy"])), f"{format_float(float(adoption_metrics['policy_adoption_percentage']), 1)}% da amostra"),
            metric_card("Mediana de estrelas", median_stars, "popularidade tipica"),
            metric_card("Idade mediana", f"{median_age_years} anos", "maturidade tipica"),
        ]
    )
    charts = build_interactive_charts(top_repos, enriched, adoption_metrics, clusters, rq2_policy, rq3_policy)

    html_text = f"""<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Dashboard Lab04 - Politicas de IA em Repositorios Open Source</title>
  <style>
    :root {{
      --ink: #17202a;
      --muted: #647084;
      --line: #d8dee8;
      --panel: #ffffff;
      --surface: #f6f8fb;
      --panel-soft: #fbfcfe;
      --chart-bg: #ffffff;
      --table-head: #edf2f7;
      --callout-bg: #edf8f6;
      --callout-text: #24443f;
      --tab-active: #2f5f78;
      --blue: #4c78a8;
      --green: #2a9d8f;
      --purple: #6f6a9e;
      --amber: #e9c46a;
      --shadow: 0 10px 30px rgba(23, 32, 42, 0.08);
    }}
    body.dark-theme {{
      --ink: #e7edf5;
      --muted: #a9b6c8;
      --line: #314052;
      --panel: #182231;
      --surface: #101722;
      --panel-soft: #141e2b;
      --chart-bg: #182231;
      --table-head: #223044;
      --callout-bg: #14312f;
      --callout-text: #c4f0e8;
      --tab-active: #2a9d8f;
      --shadow: 0 12px 34px rgba(0, 0, 0, 0.28);
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      color: var(--ink);
      background: var(--surface);
      font: 15px/1.55 system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }}
    .app-shell {{
      width: min(1280px, calc(100% - 32px));
      margin: 0 auto;
      padding: 22px 0 34px;
    }}
    header {{
      display: grid;
      grid-template-columns: minmax(0, 1fr) auto;
      gap: 24px;
      align-items: end;
      padding: 8px 0 18px;
    }}
    h1 {{
      margin: 0;
      font-size: clamp(28px, 3vw, 42px);
      line-height: 1.08;
      letter-spacing: 0;
    }}
    h2 {{
      margin: 0;
      font-size: 24px;
      letter-spacing: 0;
    }}
    h3 {{
      margin: 0 0 12px;
      font-size: 17px;
      letter-spacing: 0;
    }}
    p {{ margin: 0; }}
    .lead {{
      max-width: 880px;
      margin-top: 10px;
      color: var(--muted);
      font-size: 16px;
    }}
    .badge {{
      padding: 8px 12px;
      border: 1px solid var(--line);
      border-radius: 999px;
      color: var(--muted);
      background: var(--panel);
      font-size: 13px;
      font-weight: 700;
      white-space: nowrap;
    }}
    .header-actions {{
      display: flex;
      justify-content: flex-end;
      align-items: center;
      gap: 10px;
    }}
    .theme-toggle {{
      min-height: 38px;
      padding: 8px 12px;
      border: 1px solid var(--line);
      border-radius: 8px;
      color: var(--ink);
      background: var(--panel);
      font: inherit;
      font-size: 13px;
      font-weight: 750;
      cursor: pointer;
    }}
    .theme-toggle:hover {{
      border-color: var(--tab-active);
    }}
    .toolbar {{
      position: sticky;
      top: 0;
      z-index: 3;
      margin: 0 -16px;
      padding: 10px 16px;
      border-bottom: 1px solid var(--line);
      background: color-mix(in srgb, var(--surface) 94%, transparent);
      backdrop-filter: blur(8px);
    }}
    .tabs {{
      display: flex;
      gap: 8px;
      overflow-x: auto;
    }}
    .tab-button {{
      flex: 0 0 auto;
      min-height: 38px;
      padding: 8px 13px;
      border: 1px solid var(--line);
      border-radius: 8px;
      color: var(--muted);
      background: var(--panel);
      font: inherit;
      font-size: 13px;
      font-weight: 750;
      cursor: pointer;
    }}
    .tab-button[aria-selected="true"] {{
      color: #fff;
      border-color: var(--tab-active);
      background: var(--tab-active);
      box-shadow: var(--shadow);
    }}
    .hero-panel {{
      margin-top: 18px;
      padding: 22px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: var(--panel);
      box-shadow: var(--shadow);
    }}
    .metrics {{
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 12px;
    }}
    .metric-card {{
      min-height: 104px;
      padding: 16px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: var(--panel);
    }}
    .metric-card span {{
      display: block;
      color: var(--muted);
      font-size: 13px;
      font-weight: 700;
      text-transform: uppercase;
    }}
    .metric-card strong {{
      display: block;
      margin-top: 8px;
      font-size: 28px;
      line-height: 1;
    }}
    .metric-card small {{
      display: block;
      margin-top: 8px;
      color: var(--muted);
    }}
    .tab-panel {{
      display: none;
      margin-top: 16px;
      padding: 22px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: var(--panel);
      box-shadow: var(--shadow);
    }}
    .tab-panel.active {{ display: block; }}
    .section-head {{
      display: grid;
      grid-template-columns: minmax(0, 1fr) auto;
      gap: 20px;
      align-items: start;
      margin-bottom: 18px;
    }}
    .section-copy {{
      max-width: 820px;
      margin-top: 8px;
      color: var(--muted);
    }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(12, minmax(0, 1fr));
      gap: 16px;
      align-items: start;
      margin-top: 18px;
    }}
    .viz {{
      grid-column: span 6;
      margin: 0;
      padding: 14px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: var(--panel);
      box-shadow: 0 4px 14px rgba(23, 32, 42, 0.04);
    }}
    .image-open {{
      display: block;
      width: 100%;
      padding: 0;
      border: 0;
      background: transparent;
      cursor: zoom-in;
    }}
    .image-open:focus-visible {{
      outline: 3px solid var(--tab-active);
      outline-offset: 4px;
      border-radius: 6px;
    }}
    .viz img {{
      display: block;
      width: 100%;
      height: auto;
    }}
    .chart-card h3 {{
      min-height: 24px;
      margin-bottom: 10px;
      color: var(--ink);
      font-size: 16px;
    }}
    .chart-card-wide {{ grid-column: 1 / -1; }}
    .chart-frame {{
      min-height: 430px;
      overflow: hidden;
      border-radius: 6px;
      background: var(--chart-bg);
    }}
    figcaption {{
      margin-top: 8px;
      color: var(--muted);
      font-size: 13px;
    }}
    .callout {{
      max-width: 980px;
      margin: 16px 0 0;
      padding: 14px 16px;
      border-left: 4px solid var(--green);
      border-radius: 0 8px 8px 0;
      background: var(--callout-bg);
      color: var(--callout-text);
    }}
    .stat-strip {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
      gap: 12px;
      margin-top: 18px;
    }}
    .mini-stat {{
      padding: 13px 14px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: var(--panel-soft);
    }}
    .mini-stat b {{
      display: block;
      font-size: 20px;
      line-height: 1.1;
    }}
    .mini-stat span {{
      color: var(--muted);
      font-size: 13px;
    }}
    .data-table {{
      width: 100%;
      border-collapse: collapse;
      margin-top: 14px;
      overflow: hidden;
      border: 1px solid var(--line);
      background: var(--panel);
    }}
    .data-table th, .data-table td {{
      padding: 9px 10px;
      border-bottom: 1px solid var(--line);
      text-align: left;
      font-size: 13px;
    }}
    .data-table th {{ background: var(--table-head); }}
    footer {{
      padding-top: 18px;
      color: var(--muted);
      font-size: 13px;
    }}
    .image-modal {{
      position: fixed;
      inset: 0;
      z-index: 10;
      display: none;
      padding: 24px;
      background: rgba(5, 9, 14, 0.82);
    }}
    .image-modal.open {{
      display: grid;
      place-items: center;
    }}
    .modal-content {{
      position: relative;
      width: min(96vw, 1320px);
      max-height: 92vh;
      padding: 14px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: var(--panel);
      box-shadow: 0 22px 70px rgba(0, 0, 0, 0.42);
    }}
    .modal-close {{
      position: absolute;
      top: 10px;
      right: 10px;
      width: 38px;
      height: 38px;
      border: 1px solid var(--line);
      border-radius: 8px;
      color: var(--ink);
      background: var(--panel);
      font-size: 22px;
      line-height: 1;
      cursor: pointer;
    }}
    .modal-image {{
      display: block;
      width: 100%;
      max-height: calc(92vh - 90px);
      object-fit: contain;
      padding-top: 28px;
    }}
    .modal-caption {{
      margin-top: 10px;
      color: var(--muted);
      font-size: 14px;
    }}
    @media (max-width: 760px) {{
      .app-shell {{ width: min(100% - 20px, 1280px); }}
      header, .section-head {{ grid-template-columns: 1fr; }}
      .badge {{ justify-self: start; }}
      .metrics {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
      .hero-panel, .tab-panel {{ padding: 14px; }}
      .grid {{ grid-template-columns: 1fr; }}
      .viz, .chart-card-wide {{ grid-column: 1; }}
      .image-modal {{ padding: 10px; }}
    }}
  </style>
</head>
<body>
  <div class="app-shell">
    <header>
      <div>
      <h1>Politicas de uso de IA em repositorios open source populares</h1>
      <p class="lead">Dashboard do Laboratorio 04 para caracterizar a amostra e responder as questoes de pesquisa sobre politicas de IA, engajamento e colaboracao no GitHub.</p>
      </div>
      <div class="header-actions">
        <button class="theme-toggle" type="button" aria-pressed="false">Modo escuro</button>
        <div class="badge">Lab04 - BI</div>
      </div>
    </header>

    <div class="hero-panel">
      <div class="metrics">{cards}</div>
      <div class="stat-strip">
        <div class="mini-stat"><b>{str(int(adoption_metrics["repositories_with_policy"]))}</b><span>repositorios com politica identificada</span></div>
        <div class="mini-stat"><b>{str(len(clusters))}</b><span>clusters/tipos de politica</span></div>
        <div class="mini-stat"><b>{format_float(float(with_policy_profile['median_stars']), 0)}</b><span>mediana de estrelas com politica</span></div>
        <div class="mini-stat"><b>{format_float(float(without_policy_profile['median_stars']), 0)}</b><span>mediana de estrelas sem politica</span></div>
      </div>
      <div class="grid">
        {plotly_card("Distribuicao da idade", charts["dataset_age_distribution"], "Passe o mouse nas barras para ver a quantidade de repositorios por faixa de idade.")}
        {plotly_card("Distribuicao de estrelas", charts["dataset_stars_distribution"], "As faixas do eixo X foram calculadas em intervalos logaritmicos para reduzir a distorcao causada por repositorios extremamente populares.")}
      </div>
    </div>

    <div class="toolbar" role="tablist" aria-label="Secoes do dashboard">
      <div class="tabs">
        <button class="tab-button" type="button" role="tab" aria-selected="true" aria-controls="rq1" data-tab="rq1">RQ1: Adocao</button>
        <button class="tab-button" type="button" role="tab" aria-selected="false" aria-controls="rq2" data-tab="rq2">RQ2: Engajamento</button>
        <button class="tab-button" type="button" role="tab" aria-selected="false" aria-controls="rq3" data-tab="rq3">RQ3: Colaboracao</button>
        <button class="tab-button" type="button" role="tab" aria-selected="false" aria-controls="complementar" data-tab="complementar">Complementar</button>
        <button class="tab-button" type="button" role="tab" aria-selected="false" aria-controls="sintese" data-tab="sintese">Sintese</button>
      </div>
    </div>

    <section id="rq1" class="tab-panel active" role="tabpanel">
      <div class="section-head">
        <div>
          <h2>RQ1 - Adocao e tipos de politica</h2>
          <p class="section-copy"><strong>Pergunta:</strong> Qual e o nivel de adocao de politicas de uso de IA em repositorios open source populares e quais padroes ou tipos de politicas emergem?</p>
        </div>
      </div>
      <div class="grid">
        {plotly_card("Adocao de politicas de IA", charts["rq1_policy_adoption"], "Comparacao interativa entre repositorios com e sem politica de IA.")}
        {plotly_card("Distribuicao dos tipos de politica", charts["rq1_cluster_distribution"], "Quantidade de repositorios por tipo de politica identificado.", wide=True)}
        {plotly_card("Percentual dos clusters", charts["rq1_cluster_percentages"], "Participacao percentual de cada cluster entre os repositorios com politica.", wide=True)}
        {plotly_card("Tamanho dos textos de politica", charts["rq1_policy_text_size_by_cluster"], "Comparacao entre media e mediana do tamanho dos textos de politica.", wide=True)}
      </div>
      <div class="callout">Apenas {format_float(float(adoption_metrics['policy_adoption_percentage']), 1)}% da amostra possui politica identificada. Entre esses casos, o cluster mais frequente e "{html.escape(str(cluster_top['cluster_label']))}", com {int(cluster_top['unique_repositories'])} repositorios.</div>
      <h3>Resumo dos clusters</h3>
      {table_html(clusters, ["cluster", "cluster_label", "unique_repositories", "percentage_of_policy_repositories", "median_policy_words"])}
    </section>

    <section id="rq2" class="tab-panel" role="tabpanel">
      <div class="section-head">
        <div>
          <h2>RQ2 - Engajamento</h2>
          <p class="section-copy"><strong>Pergunta:</strong> Como a presenca e o tipo de politica de IA se relacionam com o volume de contribuicoes e o nivel de engajamento em projetos open source?</p>
        </div>
      </div>
      <div class="grid">
        {plotly_card("PRs totais", charts["rq2_prs_total"], "Volume tipico de PRs por presenca de politica.")}
        {plotly_card("PRs mergeadas", charts["rq2_prs_merged"], "Volume tipico de PRs mergeadas por presenca de politica.")}
        {plotly_card("Issues totais", charts["rq2_issues_total"], "Volume tipico de issues por presenca de politica.")}
        {plotly_card("Colaboradores unicos", charts["rq2_unique_collaborators"], "Comunidade colaboradora tipica por grupo.")}
        {plotly_card("Comentarios e reviews", charts["rq2_comments_reviews"], "Comentarios e reviews como indicadores de interacao.")}
        {plotly_card("Heatmap de engajamento", charts["rq2_engagement_heatmap"], "Comparacao normalizada das principais metricas de engajamento.", wide=True)}
      </div>
      <div class="callout">Os repositorios com politica apresentam medianas maiores em PRs, issues, comentarios e reviews. A leitura recomendada e associativa: projetos maiores ou mais maduros podem ser mais propensos a documentar politicas.</div>
    </section>

    <section id="rq3" class="tab-panel" role="tabpanel">
      <div class="section-head">
        <div>
          <h2>RQ3 - Colaboracao, responsividade e eficiencia</h2>
          <p class="section-copy"><strong>Pergunta:</strong> Como a presenca e o tipo de politica de IA se relacionam com a responsividade e a eficiencia do fluxo de contribuicao nos projetos?</p>
        </div>
      </div>
      <div class="grid">
        {plotly_card("Taxa de merge", charts["rq3_merge_rate"], "Taxa mediana de merge de PRs por grupo.")}
        {plotly_card("Fechamento sem merge", charts["rq3_closed_no_merge_rate"], "Taxa mediana de PRs fechadas sem merge.")}
        {plotly_card("Tempo de ciclo de PR", charts["rq3_pr_cycle_time"], "Tempo de ciclo de PR convertido para dias.", wide=True)}
        {plotly_card("Tempo ate primeira resposta", charts["rq3_first_response_time"], "Tempo ate primeira resposta em issues e PRs.", wide=True)}
        {plotly_card("Tempo ate primeira revisao", charts["rq3_first_review_time"], "Tempo ate primeira revisao de PR.")}
        {plotly_card("Estabilidade do processo", charts["rq3_process_stability"], "Commits, reviews e reviews ate aprovacao.", wide=True)}
        {plotly_card("Heatmap de colaboracao", charts["rq3_collaboration_heatmap"], "Comparacao normalizada das principais metricas de colaboracao.", wide=True)}
      </div>
      <div class="callout">Na amostra, projetos com politica apresentam maior taxa de merge, menor taxa de fechamento sem merge e menor tempo ate primeira revisao. Esses resultados indicam associacao, nao causalidade.</div>
    </section>

    <section id="complementar" class="tab-panel" role="tabpanel">
      <div class="section-head">
        <div>
          <h2>Analise complementar - popularidade, idade e politicas</h2>
          <p class="section-copy">Esta etapa contextualiza RQ2 e RQ3 ao investigar se repositorios com politica de IA tambem tendem a ser mais populares ou mais antigos.</p>
        </div>
      </div>
      <div class="grid">
        {plotly_card("Estrelas por presenca de politica", charts["complementary_stars"], "Distribuicao de estrelas por presenca de politica.")}
        {plotly_card("Idade por presenca de politica", charts["complementary_age"], "Distribuicao de idade por presenca de politica.")}
        {plotly_card("Adocao por faixa de estrelas", charts["complementary_policy_adoption_stars"], "Taxa de adocao por quartil de estrelas.")}
        {plotly_card("Adocao por faixa de idade", charts["complementary_policy_adoption_age"], "Taxa de adocao por quartil de idade.")}
        {plotly_card("Idade vs. estrelas", charts["complementary_age_vs_stars"], "Dispersao idade vs. estrelas colorida por presenca de politica.", wide=True)}
      </div>
      <div class="callout">Mediana de estrelas com politica: {format_float(float(with_policy_profile['median_stars']), 1)}. Sem politica: {format_float(float(without_policy_profile['median_stars']), 1)}. Essa diferenca deve ser tratada como possivel fator de contexto para as comparacoes.</div>
      <h3>Resumo por perfil</h3>
      {table_html(profile)}
    </section>

    <section id="sintese" class="tab-panel" role="tabpanel">
      <h2>Sintese dos achados</h2>
      <ul>
        <li>A adocao explicita de politicas de IA e baixa na amostra geral.</li>
        <li>Entre os repositorios com politica, predomina o cluster de governanca ampla do uso de IA.</li>
        <li>Repositorios com politica apresentam maiores medianas de PRs, issues, comentarios e reviews.</li>
        <li>Repositorios com politica tambem apresentam sinais de fluxo colaborativo mais responsivo e estruturado.</li>
        <li>A analise complementar deve ser usada para discutir possiveis fatores de confusao, como popularidade e maturidade dos projetos.</li>
        <li>Nenhuma visualizacao deve ser interpretada como evidencia causal direta.</li>
      </ul>
    </section>

  <footer>
    Dashboard gerado automaticamente a partir dos CSVs em <code>enunciado4/data</code>. Figuras e tabelas foram salvas em <code>enunciado4/outputs</code>.
  </footer>
  </div>
  <div class="image-modal" aria-hidden="true">
    <div class="modal-content" role="dialog" aria-modal="true" aria-label="Visualizacao ampliada do grafico">
      <button class="modal-close" type="button" aria-label="Fechar imagem ampliada">&times;</button>
      <img class="modal-image" src="" alt="">
      <div class="modal-caption"></div>
    </div>
  </div>
  <script>
    const buttons = [...document.querySelectorAll(".tab-button")];
    const panels = [...document.querySelectorAll(".tab-panel")];
    const themeToggle = document.querySelector(".theme-toggle");
    const imageButtons = [...document.querySelectorAll(".image-open")];
    const imageModal = document.querySelector(".image-modal");
    const modalImage = document.querySelector(".modal-image");
    const modalCaption = document.querySelector(".modal-caption");
    const modalClose = document.querySelector(".modal-close");

    function activateTab(tabId) {{
      buttons.forEach((button) => {{
        button.setAttribute("aria-selected", String(button.dataset.tab === tabId));
      }});
      panels.forEach((panel) => {{
        panel.classList.toggle("active", panel.id === tabId);
      }});
      setTimeout(() => {{
        document.querySelectorAll(`#${{tabId}} .js-plotly-plot`).forEach((chart) => Plotly.Plots.resize(chart));
      }}, 50);
    }}

    buttons.forEach((button) => {{
      button.addEventListener("click", () => activateTab(button.dataset.tab));
    }});

    function applyTheme(theme) {{
      const isDark = theme === "dark";
      document.body.classList.toggle("dark-theme", isDark);
      themeToggle.setAttribute("aria-pressed", String(isDark));
      themeToggle.textContent = isDark ? "Modo claro" : "Modo escuro";
      updatePlotlyTheme(isDark);
    }}

    function updatePlotlyTheme(isDark) {{
      if (!window.Plotly) return;
      const colors = isDark
        ? {{
            bg: "#182231",
            ink: "#e7edf5",
            muted: "#a9b6c8",
            grid: "#314052",
            hoverBg: "#e7edf5",
            hoverInk: "#101722",
          }}
        : {{
            bg: "#ffffff",
            ink: "#17202a",
            muted: "#647084",
            grid: "#e7edf3",
            hoverBg: "#17202a",
            hoverInk: "#ffffff",
          }};

      document.querySelectorAll(".js-plotly-plot").forEach((chart) => {{
        Plotly.relayout(chart, {{
          paper_bgcolor: colors.bg,
          plot_bgcolor: colors.bg,
          "font.color": colors.ink,
          "xaxis.color": colors.muted,
          "xaxis.gridcolor": colors.grid,
          "xaxis.zerolinecolor": colors.grid,
          "yaxis.color": colors.muted,
          "yaxis.gridcolor": colors.grid,
          "yaxis.zerolinecolor": colors.grid,
          "legend.font.color": colors.ink,
          "hoverlabel.bgcolor": colors.hoverBg,
          "hoverlabel.font.color": colors.hoverInk,
        }});
      }});
    }}

    const savedTheme = localStorage.getItem("dashboard-theme") || "light";
    applyTheme(savedTheme);

    themeToggle.addEventListener("click", () => {{
      const nextTheme = document.body.classList.contains("dark-theme") ? "light" : "dark";
      localStorage.setItem("dashboard-theme", nextTheme);
      applyTheme(nextTheme);
    }});

    function openImageModal(src, caption) {{
      modalImage.src = src;
      modalImage.alt = caption;
      modalCaption.textContent = caption;
      imageModal.classList.add("open");
      imageModal.setAttribute("aria-hidden", "false");
      modalClose.focus();
    }}

    function closeImageModal() {{
      imageModal.classList.remove("open");
      imageModal.setAttribute("aria-hidden", "true");
      modalImage.src = "";
    }}

    imageButtons.forEach((button) => {{
      button.addEventListener("click", () => openImageModal(button.dataset.full, button.dataset.caption));
    }});

    modalClose.addEventListener("click", closeImageModal);
    imageModal.addEventListener("click", (event) => {{
      if (event.target === imageModal) {{
        closeImageModal();
      }}
    }});
    document.addEventListener("keydown", (event) => {{
      if (event.key === "Escape" && imageModal.classList.contains("open")) {{
        closeImageModal();
      }}
    }});
  </script>
</body>
</html>
"""
    (DASHBOARD_DIR / "dashboard.html").write_text(html_text, encoding="utf-8")


def main() -> None:
    data_dir = BASE_DIR / "data"
    tables_dir = data_dir / "tables"

    top_repos = read_csv(data_dir / "top_repos_filtered.csv")
    adoption = read_csv(tables_dir / "rq1_adoption_summary.csv")
    clusters = read_csv(tables_dir / "rq1_cluster_summary.csv")
    policy_repos = read_csv(tables_dir / "rq1_repository_policy_summary.csv")
    rq2_policy = read_csv(tables_dir / "rq2_engagement_by_policy_presence.csv")
    rq3_policy = read_csv(tables_dir / "rq3_collaboration_by_policy_presence.csv")

    enriched = build_enriched_top_repos(top_repos, policy_repos)
    profile = save_clean_tables(top_repos, enriched, adoption, clusters, rq2_policy, rq3_policy)

    plot_dataset_figures(top_repos, enriched)
    adoption_metrics = plot_rq1_figures(adoption, clusters)
    plot_rq2_figures(rq2_policy)
    plot_rq3_figures(rq3_policy)
    plot_complementary_figures(enriched)

    build_dashboard(top_repos, enriched, adoption_metrics, clusters, rq2_policy, rq3_policy, profile)
    print(f"Dashboard gerado em: {DASHBOARD_DIR / 'dashboard.html'}")
    print(f"Figuras geradas em: {FIGURES_DIR}")
    print(f"Tabelas limpas geradas em: {TABLES_DIR}")


if __name__ == "__main__":
    main()
