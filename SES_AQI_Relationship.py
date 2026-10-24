"""Calculate the mean county AQI for each socioeconomic status label."""

from pathlib import Path

import pandas as pd


def main():
    data_path = Path(__file__).resolve().parent / "countyLevelData.csv"
    data = pd.read_csv(data_path, usecols=["SES_Label", "Average_AQI"])
    data["Average_AQI"] = pd.to_numeric(data["Average_AQI"], errors="coerce")
    data["Average_AQI"] = data["Average_AQI"].replace(
        [float("inf"), float("-inf")], float("nan")
    )
    data["SES_Label"] = data["SES_Label"].astype("string").str.strip().replace("", pd.NA)
    valid = data.dropna(subset=["SES_Label", "Average_AQI"])
    summary = valid.groupby("SES_Label")["Average_AQI"].agg(
        Mean_AQI="mean", County_Count="count"
    )

    print("Average county AQI by SES label (each county weighted equally):")
    print(summary.to_string(float_format=lambda value: f"{value:.6f}"))
    print(f"Rows excluded (missing or invalid values): {len(data) - len(valid):,}")


if __name__ == "__main__":
    main()
