from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent


def load_data():
    return pd.read_csv(BASE_DIR / "data" / "manufacturing_defect_dataset.csv")


def check_missing_and_duplicates(df):
    """Resumo por coluna: tipo, nulos, % de nulos, únicos e duplicados."""
    return pd.DataFrame({
        "dtype": df.dtypes,
        "nulls": df.isna().sum(),
        "null_%": (df.isna().mean() * 100).round(2),
        "unique": df.nunique(),
        "duplicated_values": df.apply(lambda c: c.duplicated().sum()),
    })


def check_negative_values(df):
    """Estatísticas das colunas numéricas, com negativos, zeros e outliers (IQR)."""
    num = df.select_dtypes(include="number")
    stats = num.describe().T[["min", "max", "mean", "std"]]
    stats["negatives"] = (num < 0).sum()
    stats["zeros"] = (num == 0).sum()

    q1, q3 = num.quantile(0.25), num.quantile(0.75)
    iqr = q3 - q1
    stats["outliers_IQR"] = ((num < q1 - 1.5 * iqr) | (num > q3 + 1.5 * iqr)).sum()
    return stats


def check_constant_columns(df):
    """Lista de colunas com 1 valor único (ou nenhum)."""
    return [c for c in df.columns if df[c].nunique() <= 1]


if __name__ == "__main__":
    df = load_data()
    print(check_missing_and_duplicates(df))
    print(check_negative_values(df))
    print("Constant columns:", check_constant_columns(df))