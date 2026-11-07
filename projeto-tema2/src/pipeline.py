"""Pipeline: leitura, limpeza, tabela-resumo e graficos do dataset de defeitos.

Uso (a partir de projeto-tema2):
    python src/pipeline.py

Entrada : data/manufacturing_defect_dataset.csv
Saidas  : output/tabela_resumo.csv, output/grafico_1.png, output/grafico_2.png
"""
import re
import textwrap
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # sem interface grafica: so gera arquivos (funciona no Docker)
import matplotlib.pyplot as plt
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
CSV_PATH = BASE_DIR / "data" / "manufacturing_defect_dataset.csv"
OUT_DIR = BASE_DIR / "output"

# Colunas onde zero e um valor legitimo (decisao 2 do README)
COLUNAS_ZERO_VALIDO = ["DeliveryDelay", "MaintenanceHours", "SafetyIncidents"]

# Cores (paleta de referencia): destaque em azul, resto em cinza neutro
AZUL = "#2a78d6"
CINZA = "#b5b4ad"
TEXTO = "#0b0b0b"
TEXTO_SEC = "#52514e"
FUNDO = "#fcfcfb"


def para_snake_case(nome):
    """DefectStatus -> defect_status."""
    return re.sub(r"(?<!^)(?=[A-Z])", "_", nome).lower()


def carregar():
    if not CSV_PATH.exists():
        raise FileNotFoundError(
            f"{CSV_PATH} nao encontrado. Coloque manufacturing_defect_dataset.csv "
            "na pasta data/ (ou monte a pasta como volume em /app/data no Docker)."
        )
    return pd.read_csv(CSV_PATH)


def limpar(df):
    """Aplica as tres decisoes de limpeza documentadas no README."""
    df = df.copy()
    print(f"Linhas lidas: {len(df)}")

    # Checagem previa: nulos e linhas duplicadas (o README informa que nao ha)
    print(f"Nulos: {int(df.isna().sum().sum())} | Linhas duplicadas: {int(df.duplicated().sum())}")
    df = df.drop_duplicates().dropna()

    # Decisao 1: outliers pelo IQR, ignorando colunas binarias (0/1).
    # Nenhuma linha e removida: o IQR marcaria o grupo minoritario do alvo.
    num = df.select_dtypes(include="number")
    binarias = [c for c in num.columns if set(num[c].unique()) <= {0, 1}]
    continuas = [c for c in num.columns if c not in binarias]
    q1, q3 = num[continuas].quantile(0.25), num[continuas].quantile(0.75)
    iqr = q3 - q1
    outliers = ((num[continuas] < q1 - 1.5 * iqr) | (num[continuas] > q3 + 1.5 * iqr)).sum()
    print(f"[1] Colunas binarias ignoradas no IQR: {binarias}")
    print(f"[1] Outliers (IQR) nas demais colunas: {int(outliers.sum())} -> nenhuma linha removida")

    # Decisao 2: zeros sao validos nessas colunas, nada e imputado ou removido.
    zeros = {c: int((df[c] == 0).sum()) for c in COLUNAS_ZERO_VALIDO}
    print(f"[2] Zeros mantidos como valores validos: {zeros}")

    # Decisao 3: nomes em snake_case e rotulo legivel para o alvo.
    df = df.rename(columns={c: para_snake_case(c) for c in df.columns})
    df["defect_label"] = df["defect_status"].map({1: "Defeito", 0: "Sem defeito"})
    print("[3] Colunas renomeadas para snake_case e coluna defect_label criada")

    return df


def tabela_resumo(df):
    """Contagem, participacao e medias das principais variaveis por grupo."""
    colunas = [
        "defect_rate", "quality_score", "maintenance_hours", "production_volume",
        "delivery_delay", "safety_incidents", "supplier_quality", "downtime_percentage",
    ]
    resumo = df.groupby("defect_label")[colunas].mean().round(2)
    resumo.insert(0, "pecas", df["defect_label"].value_counts())
    resumo.insert(1, "pct_pecas", (df["defect_label"].value_counts(normalize=True) * 100).round(1))
    total = df[colunas].mean().round(2)
    total["pecas"] = len(df)
    total["pct_pecas"] = 100.0
    resumo.loc["Total"] = total[resumo.columns]
    resumo["pecas"] = resumo["pecas"].astype(int)
    return resumo


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


def barras(ax, rotulos, valores, cores):
    barras_ = ax.bar(rotulos, valores, color=cores, width=0.62)
    for b, v in zip(barras_, valores):
        ax.text(b.get_x() + b.get_width() / 2, v + 1.2, f"{v:.0f}%",
                ha="center", va="bottom", fontsize=11, color=TEXTO)
    ax.set_ylim(0, 110)
    ax.set_yticks([0, 25, 50, 75, 100])
    ax.set_yticklabels([f"{t}%" for t in [0, 25, 50, 75, 100]])
    estilizar(ax)


def grafico_1(df):
    """Taxa de defeito por faixa de defect_rate."""
    faixas = pd.cut(df["defect_rate"], [0, 1, 2, 3, 4, 5],
                    labels=["0-1", "1-2", "2-3", "3-4", "4-5"])
    taxa = df.groupby(faixas, observed=True)["defect_status"].mean() * 100
    abaixo = df.loc[df["defect_rate"] <= 3, "defect_status"].mean() * 100
    acima = df.loc[df["defect_rate"] > 3, "defect_status"].mean() * 100

    fig, ax = plt.subplots(figsize=(9, 5.5), facecolor=FUNDO)
    cores = [CINZA if f in ("0-1", "1-2", "2-3") else AZUL for f in taxa.index]
    barras(ax, taxa.index.astype(str), taxa.values, cores)
    ax.set_xlabel("Faixa de defect_rate (%)", color=TEXTO_SEC)
    ax.set_ylabel("Peças com defeito", color=TEXTO_SEC)
    if acima > abaixo:
        titulo = (f"Acima de 3% de defect_rate, {acima:.0f}% das peças têm defeito "
                  f"(contra {abaixo:.0f}% abaixo)")
    else:
        titulo = (f"Taxa de defeito não sobe com defect_rate: {acima:.0f}% acima de 3% "
                  f"e {abaixo:.0f}% abaixo")
    titular(fig, titulo)
    fig.tight_layout(rect=(0, 0, 1, 0.88))
    fig.savefig(OUT_DIR / "grafico_1.png", dpi=150, facecolor=FUNDO)
    plt.close(fig)
    return titulo


def grafico_2(df):
    """Taxa de defeito por nivel de atraso de entrega."""
    taxa = df.groupby("delivery_delay")["defect_status"].mean() * 100
    menor, maior = taxa.min(), taxa.max()

    fig, ax = plt.subplots(figsize=(9, 5.5), facecolor=FUNDO)
    barras(ax, taxa.index.astype(str), taxa.values, [AZUL] * len(taxa))
    ax.set_xlabel("Atraso de entrega (delivery_delay, dias)", color=TEXTO_SEC)
    ax.set_ylabel("Peças com defeito", color=TEXTO_SEC)
    if maior - menor <= 5:
        titulo = (f"O atraso de entrega não muda a taxa de defeitos: "
                  f"ela fica entre {menor:.0f}% e {maior:.0f}% em todos os níveis")
    else:
        titulo = (f"A taxa de defeitos varia de {menor:.0f}% a {maior:.0f}% "
                  "conforme o atraso de entrega")
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