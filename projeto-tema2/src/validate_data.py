from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
df = pd.read_csv(BASE_DIR / "data" / "manufacturing_defect_dataset.csv")

# 1. One-row-per-column summary
report = pd.DataFrame({
    "dtype": df.dtypes,
    "nulls": df.isna().sum(),
    "null_%": (df.isna().mean() * 100).round(2),
    "unique": df.nunique(),
    "duplicated_values": df.apply(lambda c: c.duplicated().sum()),
})
print(report)

# 2. Numeric columns: range and outliers (IQR rule)
num = df.select_dtypes(include="number")
stats = num.describe().T[["min", "max", "mean", "std"]]
stats["negatives"] = (num < 0).sum()
stats["zeros"] = (num == 0).sum()

q1, q3 = num.quantile(0.25), num.quantile(0.75)
iqr = q3 - q1
stats["outliers_IQR"] = ((num < q1 - 1.5 * iqr) | (num > q3 + 1.5 * iqr)).sum()
print(stats)

# 3. Categorical/text columns: labels, casing, whitespace, placeholders
for col in df.select_dtypes(include=["object", "category"]):
    s = df[col].astype(str)
    print(f"\n--- {col} ---")
    print(df[col].value_counts(dropna=False).head(20))
    print("leading/trailing spaces:", (s != s.str.strip()).sum())
    print("case variants:", s.str.lower().nunique(), "vs", s.nunique(), "unique")
    print("placeholders:", s.str.strip().str.lower().isin(["", "na", "n/a", "null", "none", "?", "-"]).sum())

# 4. Columns that should be numeric but contain text
for col in df.select_dtypes(include="object"):
    converted = pd.to_numeric(df[col], errors="coerce")
    if converted.notna().mean() > 0.9:
        print(f"{col}: mostly numeric, bad values:", df.loc[converted.isna() & df[col].notna(), col].unique()[:10])

# 5. Flag constant columns
print("Constant columns:", [c for c in df.columns if df[c].nunique() <= 1])