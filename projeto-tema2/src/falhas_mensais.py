from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt

BASE_DIR = Path(__file__).resolve().parent.parent
CSV_PATH = BASE_DIR / "data" / "defects_data.csv"
if not CSV_PATH.exists():
    raise FileNotFoundError(f"{CSV_PATH} nao encontrado. Baixe defects_data.csv.")

df = pd.read_csv(CSV_PATH)
df["defect_date"] = pd.to_datetime(df["defect_date"], errors="coerce")

# Falhas por categoria (defect_type), mes a mes
tabela_mensal = (
    df.assign(mes=df["defect_date"].dt.to_period("M").astype(str))
    .groupby(["mes", "defect_type"]).size()
    .unstack(fill_value=0)
    .sort_index()
)

cores = {"Structural": "#d62728", "Functional": "#1f77b4", "Cosmetic": "#2ca02c"}
cols = [c for c in ["Structural", "Functional", "Cosmetic"] if c in tabela_mensal.columns]

ax = tabela_mensal[cols].plot(kind="bar", figsize=(11, 6), color=[cores[c] for c in cols], width=0.8)
ax.set_title("Falhas por categoria de defeito, mes a mes")
ax.set_xlabel("Mes")
ax.set_ylabel("Numero de registros de defeito")
ax.legend(title="Tipo de defeito")
plt.xticks(rotation=45)
plt.tight_layout()

OUT_DIR = BASE_DIR / "figs"
OUT_DIR.mkdir(exist_ok=True)
out_path = OUT_DIR / "falhas_por_categoria_mes.png"
plt.savefig(out_path, dpi=150)
print(f"Grafico salvo em {out_path}")
print(tabela_mensal[cols])
