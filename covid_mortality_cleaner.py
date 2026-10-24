"""Calculate county mortality and estimated case-fatality statistics."""

from pathlib import Path
import pandas as pd

from CountyLevelDataJoiner import add_join_keys

PROJECT_DIR = Path(__file__).resolve().parent


def build_mortality():
    community = pd.read_csv(
        PROJECT_DIR / "United_States_COVID-19_Community_Levels_by_County_20261023.csv",
        dtype="string",
    )
    for column in ["county_population", "covid_cases_per_100k"]:
        community[column] = pd.to_numeric(
            community[column].str.replace(",", "", regex=False), errors="coerce"
        )
    community["date_updated"] = pd.to_datetime(community["date_updated"])
    if community.duplicated(["county_fips", "date_updated"]).any():
        raise ValueError("Duplicate county-week records in community data")
    community["Estimated_Cases"] = (
        community["covid_cases_per_100k"] * community["county_population"] / 100_000
    )
    cases = community.groupby("county_fips")["Estimated_Cases"].sum(min_count=1)
    latest = community.sort_values("date_updated").drop_duplicates("county_fips", keep="last")
    population = latest.set_index("county_fips")["county_population"]
    deaths = pd.read_csv(
        PROJECT_DIR / "Provisional_COVID-19_Death_Counts_in_the_United_States_by_County_20261023.csv",
        dtype="string",
    ).rename(columns={
        "County name": "County", "Deaths involving COVID-19": "COVID_19_Deaths"
    })
    deaths["county_fips"] = deaths["FIPS County Code"].str.zfill(5)
    deaths["COVID_19_Deaths"] = pd.to_numeric(
        deaths["COVID_19_Deaths"].str.replace(",", "", regex=False), errors="raise"
    )
    deaths["Population"] = deaths["county_fips"].map(population)
    deaths["Estimated_Cases"] = deaths["county_fips"].map(cases)

    deaths["Case_Fatality_Rate_Pct"] = (
        deaths["COVID_19_Deaths"] / deaths["Estimated_Cases"].where(deaths["Estimated_Cases"] > 0) * 100
    )
    deaths["Mortality_Rate_Per_100k"] = (
        deaths["COVID_19_Deaths"] / deaths["Population"].where(deaths["Population"] > 0) * 100_000
    )
    columns = ["State", "County", "Population", "Estimated_Cases", "COVID_19_Deaths",
               "Case_Fatality_Rate_Pct", "Mortality_Rate_Per_100k"]
    result = deaths[columns]
    result.to_csv(PROJECT_DIR / "covid_mortality_cleaner.csv", index=False)
    return result


def main():
    mortality = add_join_keys(build_mortality())
    county = add_join_keys(pd.read_csv(PROJECT_DIR / "countyLevelData.csv"))
    columns = ["Population", "Estimated_Cases", "Case_Fatality_Rate_Pct", "Mortality_Rate_Per_100k"]
    county = county.drop(columns=columns, errors="ignore")
    joined = county.merge(
        mortality[["_state", "_county"] + columns],
        on=["_state", "_county"], how="left", validate="one_to_one",
    ).drop(columns=["_state", "_county"])
    joined.to_csv(PROJECT_DIR / "countyLevelData.csv", index=False)
    print(f"Saved mortality statistics and joined {len(joined):,} county rows.")


if __name__ == "__main__":
    main()
