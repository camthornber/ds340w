"""Import county economic data from the 2023 ACS five-year estimates."""

from pathlib import Path

import pandas as pd


ACS_DATA_PATH = (
    Path(__file__).resolve().parent
    / "ACSST5Y2023.S1903_2026-10-23T211042"
    / "ACSST5Y2023.S1903-Data.csv"
)

# The second CSV row contains descriptive labels, rather than observations.
# Preserve Census identifiers and special estimate symbols as strings.
acs_data = pd.read_csv(
    ACS_DATA_PATH,
    encoding="utf-8-sig",
    skiprows=[1],
    dtype="string",
).dropna(axis="columns", how="all")

# Calculate quartiles from valid median household incomes only.
median_household_income = pd.to_numeric(acs_data["S1903_C03_001E"], errors="coerce")
lower_quartile, upper_quartile = median_household_income.quantile([0.25, 0.75])
acs_data["SES_Label"] = pd.Series("M", index=acs_data.index, dtype="string")
acs_data.loc[median_household_income <= lower_quartile, "SES_Label"] = "L"
acs_data.loc[median_household_income >= upper_quartile, "SES_Label"] = "H"
# Leave counties with unavailable income unclassified.
acs_data.loc[median_household_income.isna(), "SES_Label"] = pd.NA

location = acs_data["NAME"].str.rsplit(", ", n=1, expand=True)
county_ses = pd.DataFrame({
    "State": location[1],
    "County": location[0].str.replace(r"\s+County$", "", regex=True),
    "SES_Label": acs_data["SES_Label"],
})
county_ses.to_csv(Path(__file__).resolve().parent / "countySES.csv", index=False)


if __name__ == "__main__":
    print(f"Imported {len(acs_data):,} rows and {len(acs_data.columns):,} columns.")
    print(acs_data[["GEO_ID", "NAME"]].head().to_string(index=False))
