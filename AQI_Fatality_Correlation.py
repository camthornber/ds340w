"""Calculate Pearson correlation between county AQI and case fatality rate."""

from pathlib import Path

import pandas as pd
from scipy.stats import pearsonr


def main():
    data_path = Path(__file__).resolve().parent / "countyLevelData.csv"
    columns = ["Average_AQI", "Case_Fatality_Rate_Pct"]
    data = pd.read_csv(data_path, usecols=columns)
    # Use only pairs with two valid, finite numeric values.
    pairs = data.apply(pd.to_numeric, errors="coerce")
    pairs = pairs.replace([float("inf"), float("-inf")], float("nan")).dropna()
    if len(pairs) < 3:
        raise ValueError("At least three complete county pairs are required.")
    if (pairs.nunique() < 2).any():
        raise ValueError("Both columns must contain varying values.")

    result = pearsonr(pairs["Average_AQI"], pairs["Case_Fatality_Rate_Pct"])
    print("Pearson correlation: Average_AQI vs. Case_Fatality_Rate_Pct")
    print(f"Counties included: {len(pairs):,}")
    print(f"Rows excluded (missing or invalid values): {len(data) - len(pairs):,}")
    print(f"Correlation coefficient (r): {result.statistic:.6f}")
    print(f"Two-sided p-value: {result.pvalue:.6g}")


if __name__ == "__main__":
    main()
