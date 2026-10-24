"""Combine 2020–2023 daily AQI observations and average them by county."""

from pathlib import Path

import pandas as pd


PROJECT_DIR = Path(__file__).resolve().parent
aqi_data = pd.concat(
    [
        pd.read_csv(
            PROJECT_DIR / f"daily_aqi_by_county_{year}.csv",
            dtype={"State Code": "string", "County Code": "string"},
        )
        for year in range(2020, 2024)
    ],
    ignore_index=True,
)
aqi_data["AQI"] = pd.to_numeric(aqi_data["AQI"], errors="raise")

# Each available daily observation has equal weight across all four years.
# Include state so counties with the same name remain separate.
county_aqi = (
    aqi_data.groupby(["State Name", "county Name"], as_index=False)["AQI"]
    .mean()
    .rename(columns={"State Name": "State", "county Name": "County", "AQI": "Average_AQI"})
)
county_aqi.to_csv(PROJECT_DIR / "countyAQI.csv", index=False)


if __name__ == "__main__":
    print(f"Combined {len(aqi_data):,} daily observations from 2020–2023.")
    print(f"Saved average AQI for {len(county_aqi):,} counties to countyAQI.csv.")
