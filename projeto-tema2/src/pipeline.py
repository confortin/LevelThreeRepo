""""Pipeline: leitura, limpeza, tabela-resumo e graficos do dataset de defeitos.

Uso (a partir de projeto-tema2):
    python src/pipeline.py

Entrada : data/defects_data.csv
Saidas  : output/tabela_resumo.csv, output/grafico_1.png, output/grafico_2.png

Os diagnosticos (nulos, duplicados, negativos, outliers) vem de validate_data.py.
Este arquivo decide o que fazer com eles (limpeza) e gera as saidas.
"""
import textwrap
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # sem interface grafica: so gera arquivos (funciona no Docker)
import matplotlib.pyplot as plt
import pandas as pd

try:  # importado como pacote (pytest) ou executado como script (python src/pipeline.py)
    from src.validate_data import (
        check_missing_and_duplicates,
        check_negative_values,
        load_data,
    )
except ImportError:
    from validate_data import (
        check_missing_and_duplicates,
        check_negative_values,
        load_data,
    )

BASE_DIR = Path(__file__).resolve().parent.parent
OUT_DIR = BASE_DIR / "output"

COLUNAS_ESPERADAS = [
    "defect_id", "product_id", "defect_type", "defect_date",
    "defect_location", "severity", "inspection_method", "repair_cost",
]
COLUNAS_TEXTO = ["defect_type", "defect_location", "severity", "inspection_method"]

# Ordem natural de severidade (se os valores forem texto conhecido)
ORDEM_SEVERIDADE = {
    "low": 0, "minor": 0, "baixa": 0,
    "medium": 1, "moderate": 1, "media": 1, "média": 1,
    "high": 2, "major": 2, "alta": 2,
    "critical": 3, "critica": 3, "crítica": 3,
}

# Cores: destaque em azul, resto em cinza neutro
AZUL = "#2a78d6"
CINZA = "#b5b4ad"
TEXTO = "#0b0b0b"
TEXTO_SEC = "#52514e"
FUNDO = "#fcfcfb"


def carregar():
    df = load_data()
    faltando = [c for c in COLUNAS_ESPERADAS if c not in df.columns]
    if faltando:
        raise KeyError(
            f"Colunas ausentes no CSV: {faltando}. Encontradas: {list(df.columns)}"
        )
    return df


def limpar(df):
    """Aplica as decisoes de limpeza (documentar no README)."""
    df = df.copy()
    print(f"Linhas lidas: {len(df)}")

    # Diagnostico previo (validate_data.py)
    print("\nDiagnostico por coluna:")
    print(check_missing_and_duplicates(df).to_string())
    print(
        f"\nNulos: {int(df.isna().sum().sum())} | "
        f"Linhas duplicadas: {int(df.duplicated().sum())} | "
        f"defect_id repetidos: {int(df['defect_id'].duplicated().sum())}"
    )
    df = df.drop_duplicates().dropna()

    # Decisao 1: data e custo precisam ser validos
    antes = len(df)
    df["defect_date"] = pd.to_datetime(df["defect_date"], errors="coerce")
    df["repair_cost"] = pd.to_numeric(df["repair_cost"], errors="coerce")
    df = df.dropna(subset=["defect_date", "repair_cost"])
    print(f"\n[1] Linhas com data ou custo invalido removidas: {antes - len(df)}")

    # Decisao 2: custo negativo e impossivel (removido); zero e valido (mantido)
    stats = check_negative_values(df[["repair_cost"]])
    print(stats.to_string())
    negativos = int((df["repair_cost"] < 0).sum())
    zeros = int((df["repair_cost"] == 0).sum())
    df = df[df["repair_cost"] >= 0]
    print(f"[2] Custos negativos removidos: {negativos} | zeros mantidos: {zeros}")

    # Decisao 3: outliers (IQR) so sao reportados; custos altos sao reais
    print(f"[3] Outliers de repair_cost (IQR) mantidos: {int(stats.loc['repair_cost', 'outliers_IQR'])}")

    # Decisao 4: remove espacos extras nas colunas de texto
    for c in COLUNAS_TEXTO:
        if pd.api.types.is_string_dtype(df[c]):
            df[c] = df[c].str.strip()
    print("[4] Espacos extras removidos das colunas de texto")

    return df


def tabela_resumo(df):
    """Quantidade, participacao e custo de reparo por tipo de defeito."""
    resumo = df.groupby("defect_type")["repair_cost"].agg(
        defeitos="count", custo_medio="mean", custo_mediano="median", custo_total="sum"
    ).round(2)
    resumo.insert(1, "pct_defeitos", (resumo["defeitos"] / len(df) * 100).round(1))
    resumo = resumo.sort_values("defeitos", ascending=False)
    resumo.loc["Total"] = [
        len(df), 100.0,
        round(df["repair_cost"].mean(), 2),
        round(df["repair_cost"].median(), 2),
        round(df["repair_cost"].sum(), 2),
    ]
    resumo["defeitos"] = resumo["defeitos"].astype(int)
    return resumo


def ordenar_severidade(serie):
    """Ordena por severidade natural; se nao reconhecer os valores, ordem alfabetica/numerica."""
    chaves = [ORDEM_SEVERIDADE.get(str(i).strip().lower()) for i in serie.index]
    if all(k is not None for k in chaves):
        ordem = sorted(range(len(chaves)), key=lambda i: chaves[i])
        return serie.iloc[ordem]
    return serie.sort_index()


def estilizar(ax):
    ax.set_facecolor(FUNDO)
    for lado in ("top", "right", "left"):
        ax.spines[lado].set_visible(False)
    ax.spines["bottom"].set_color(CINZA)
    ax.tick_params(axis="both", colors=TEXTO_SEC, length=0)
    ax.yaxis.grid(True, color="#e6e5e0", linewidth=0.8)
    ax.set_axisbelow(True)


def titular(fig, texto):
    """Titulo (a conclusao) em ate duas linhas, alinhado a esquerda."""
    fig.suptitle(textwrap.fill(texto, 58), x=0.05, ha="left", fontsize=14,
                 fontweight="bold", color=TEXTO)


def barras(ax, rotulos, valores, cores, fmt):
    rotulos = [textwrap.fill(str(r), 12) for r in rotulos]
    rects = ax.bar(rotulos, valores, color=cores, width=0.62)
    topo = max(valores)
    for b, v in zip(rects, valores):
        ax.text(b.get_x() + b.get_width() / 2, v + topo * 0.02, fmt(v),
                ha="center", va="bottom", fontsize=11, color=TEXTO)
    ax.set_ylim(0, topo * 1.15)
    estilizar(ax)


def grafico_1(df):
    """Quantidade de defeitos por tipo."""
    cont = df["defect_type"].value_counts()
    top, pct = cont.index[0], cont.iloc[0] / len(df) * 100

    fig, ax = plt.subplots(figsize=(9, 5.5), facecolor=FUNDO)
    cores = [AZUL if i == 0 else CINZA for i in range(len(cont))]
    barras(ax, cont.index, cont.values, cores, lambda v: f"{v:,.0f}")
    ax.set_xlabel("Tipo de defeito", color=TEXTO_SEC)
    ax.set_ylabel("Quantidade de defeitos", color=TEXTO_SEC)
    titulo = f"{top} é o tipo de defeito mais frequente: {pct:.0f}% dos registros"
    titular(fig, titulo)
    fig.tight_layout(rect=(0, 0, 1, 0.88))
    fig.savefig(OUT_DIR / "grafico_1.png", dpi=150, facecolor=FUNDO)
    plt.close(fig)
    return titulo


def grafico_2(df):
    """Custo medio de reparo por severidade."""
    custo = ordenar_severidade(df.groupby("severity")["repair_cost"].mean())
    maior_i, menor_i = custo.idxmax(), custo.idxmin()
    maior, menor = custo.max(), custo.min()

    fig, ax = plt.subplots(figsize=(9, 5.5), facecolor=FUNDO)
    cores = [AZUL if i == maior_i else CINZA for i in custo.index]
    barras(ax, custo.index.astype(str), custo.values, cores, lambda v: f"{v:,.0f}")
    ax.set_xlabel("Severidade", color=TEXTO_SEC)
    ax.set_ylabel("Custo médio de reparo", color=TEXTO_SEC)
    if menor > 0 and maior / menor >= 1.2:
        titulo = (f"Severidade {maior_i} tem o maior custo médio de reparo: "
                  f"{maior:,.0f} (contra {menor:,.0f} em {menor_i})")
    else:
        titulo = (f"O custo médio de reparo é parecido entre severidades: "
                  f"de {menor:,.0f} a {maior:,.0f}")
    titular(fig, titulo)
    fig.tight_layout(rect=(0, 0, 1, 0.88))
    fig.savefig(OUT_DIR / "grafico_2.png", dpi=150, facecolor=FUNDO)
    plt.close(fig)
    return titulo


def main():
    OUT_DIR.mkdir(exist_ok=True)
    df = limpar(carregar())

    resumo = tabela_resumo(df)
    resumo.to_csv(OUT_DIR / "tabela_resumo.csv")
    print("\nTabela-resumo (salva em output/tabela_resumo.csv):")
    print(resumo.to_string())

    print("\nGraficos:")
    print(" -", grafico_1(df))
    print(" -", grafico_2(df))
    print(f"\nPronto. Arquivos em {OUT_DIR}")


if __name__ == "__main__":
    main()