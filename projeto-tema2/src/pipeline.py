"""Pipeline: leitura, limpeza, tabela-resumo e graficos do dataset de defeitos.

Uso (a partir de projeto-tema2):
    python src/pipeline.py

Entrada : data/defects_data.csv
Saidas  : output/tabela_resumo.csv, output/grafico_1.png, output/grafico_2.png
"""
import textwrap
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # sem interface grafica: so gera arquivos (funciona no Docker)
import matplotlib.pyplot as plt
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
CSV_PATH = BASE_DIR / "data" / "defects_data.csv"
OUT_DIR = BASE_DIR / "output"

# Colunas de identificacao: numericas, mas nao entram em estatisticas
COLUNAS_ID = ["defect_id", "product_id"]
COLUNAS_TEXTO = ["defect_type", "defect_location", "severity", "inspection_method"]
# Ordem da severidade, da mais leve para a mais grave (decisao 3)
ORDEM_SEVERIDADE = ["Minor", "Moderate", "Critical"]

# Cores (paleta de referencia): destaque em azul, resto em cinza neutro
AZUL = "#2a78d6"
CINZA = "#b5b4ad"
TEXTO = "#0b0b0b"
TEXTO_SEC = "#52514e"
FUNDO = "#fcfcfb"


def carregar():
    if not CSV_PATH.exists():
        raise FileNotFoundError(
            f"{CSV_PATH} nao encontrado. Coloque defects_data.csv "
            "na pasta data/ (ou monte a pasta como volume em /app/data no Docker)."
        )
    return pd.read_csv(CSV_PATH)


def limpar(df):
    """Aplica as tres decisoes de limpeza documentadas no README."""
    df = df.copy()
    print(f"Linhas lidas: {len(df)}")

    # Checagem previa: nulos e linhas duplicadas
    print(f"Nulos: {int(df.isna().sum().sum())} | Linhas duplicadas: {int(df.duplicated().sum())}")
    df = df.drop_duplicates().dropna()

    # Decisao 1: outliers pelo IQR so em repair_cost (ids nao sao medidas).
    # Nenhuma linha e removida: custos altos sao reparos reais, nao erros.
    custo = df["repair_cost"]
    q1, q3 = custo.quantile(0.25), custo.quantile(0.75)
    iqr = q3 - q1
    outliers = int(((custo < q1 - 1.5 * iqr) | (custo > q3 + 1.5 * iqr)).sum())
    negativos = int((custo < 0).sum())
    print(f"[1] Outliers (IQR) em repair_cost: {outliers} | negativos: {negativos} -> nenhuma linha removida")

    # Decisao 2: defect_date vira data (formato M/D/AAAA) e ganha a coluna mes.
    # Datas invalidas viram NaT e a linha e descartada.
    df["defect_date"] = pd.to_datetime(df["defect_date"], format="%m/%d/%Y", errors="coerce")
    invalidas = int(df["defect_date"].isna().sum())
    df = df.dropna(subset=["defect_date"])
    df["mes"] = df["defect_date"].dt.to_period("M").astype(str)
    print(f"[2] defect_date convertida para data ({invalidas} invalidas removidas) e coluna mes criada")

    # Decisao 3: textos sem espacos nas pontas e severidade como categoria ordenada.
    for c in COLUNAS_TEXTO:
        df[c] = df[c].str.strip()
    df["severity"] = pd.Categorical(df["severity"], categories=ORDEM_SEVERIDADE, ordered=True)
    df["is_critical"] = (df["severity"] == "Critical").astype(int)
    print("[3] Textos padronizados, severity ordenada (Minor < Moderate < Critical) e coluna is_critical criada")

    return df


def tabela_resumo(df):
    """Contagem, participacao, custo e % de criticos por tipo de defeito."""
    grupo = df.groupby("defect_type")
    resumo = pd.DataFrame({
        "registros": grupo.size(),
        "pct_registros": (grupo.size() / len(df) * 100).round(1),
        "custo_medio": grupo["repair_cost"].mean().round(2),
        "custo_total": grupo["repair_cost"].sum().round(2),
        "pct_critico": (grupo["is_critical"].mean() * 100).round(1),
    })
    resumo.loc["Total"] = [
        len(df), 100.0, round(df["repair_cost"].mean(), 2),
        round(df["repair_cost"].sum(), 2), round(df["is_critical"].mean() * 100, 1),
    ]
    resumo["registros"] = resumo["registros"].astype(int)
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
    # "\$" evita que o matplotlib trate o texto entre dois $ como formula
    fig.suptitle(textwrap.fill(texto, 58).replace("$", r"\$"), x=0.05, ha="left", fontsize=14,
                 fontweight="bold", color=TEXTO)


def barras(ax, rotulos, valores, cores, formato, teto):
    """Barras com o valor escrito em cima; formato e uma funcao valor -> texto."""
    barras_ = ax.bar(rotulos, valores, color=cores, width=0.62)
    for b, v in zip(barras_, valores):
        ax.text(b.get_x() + b.get_width() / 2, v + teto * 0.01, formato(v),
                ha="center", va="bottom", fontsize=11, color=TEXTO)
    ax.set_ylim(0, teto)
    estilizar(ax)


def grafico_1(df):
    """Custo medio de reparo por severidade."""
    custo = df.groupby("severity", observed=True)["repair_cost"].mean()
    maior = custo.idxmax()
    variacao = (custo.max() - custo.min()) / custo.min() * 100

    fig, ax = plt.subplots(figsize=(9, 5.5), facecolor=FUNDO)
    cores = [AZUL if s == maior else CINZA for s in custo.index]
    barras(ax, custo.index.astype(str), custo.values, cores,
           lambda v: f"${v:.0f}", custo.max() * 1.2)
    ax.set_xlabel("Severidade do defeito", color=TEXTO_SEC)
    ax.set_ylabel("Custo médio de reparo", color=TEXTO_SEC)
    if variacao <= 10:
        titulo = (f"A severidade quase não muda o custo de reparo: a média fica entre "
                  f"${custo.min():.0f} e ${custo.max():.0f}")
    else:
        titulo = (f"Defeitos {maior} têm o maior custo médio de reparo "
                  f"(${custo.max():.0f}, {variacao:.0f}% acima do menor)")
    titular(fig, titulo)
    fig.tight_layout(rect=(0, 0, 1, 0.88))
    fig.savefig(OUT_DIR / "grafico_1.png", dpi=150, facecolor=FUNDO)
    plt.close(fig)
    return titulo


def grafico_2(df):
    """Percentual de defeitos criticos por metodo de inspecao."""
    taxa = (df.groupby("inspection_method")["is_critical"].mean() * 100).sort_values(ascending=False)
    menor, maior = taxa.min(), taxa.max()

    fig, ax = plt.subplots(figsize=(9, 5.5), facecolor=FUNDO)
    cores = [AZUL if v == maior else CINZA for v in taxa.values]
    barras(ax, taxa.index, taxa.values, cores, lambda v: f"{v:.0f}%", 110)
    ax.set_yticks([0, 25, 50, 75, 100])
    ax.set_yticklabels([f"{t}%" for t in [0, 25, 50, 75, 100]])
    ax.set_xlabel("Método de inspeção", color=TEXTO_SEC)
    ax.set_ylabel("Defeitos críticos", color=TEXTO_SEC)
    if maior - menor <= 5:
        titulo = (f"O método de inspeção não muda a parcela de defeitos críticos: "
                  f"ela fica entre {menor:.0f}% e {maior:.0f}%")
    else:
        titulo = (f"{taxa.idxmax()} encontra mais defeitos críticos: "
                  f"{maior:.0f}% contra {menor:.0f}% no método com menos")
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
