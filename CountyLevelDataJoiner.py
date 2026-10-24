"""Join county AQI, SES, and COVID-19 deaths using normalized locations."""

from pathlib import Path
import re
import unicodedata

import pandas as pd


PROJECT_DIR = Path(__file__).resolve().parent
STATE_NAMES = """Alabama|Alaska|Arizona|Arkansas|California|Colorado|Connecticut|Delaware|District of Columbia|Florida|Georgia|Hawaii|Idaho|Illinois|Indiana|Iowa|Kansas|Kentucky|Louisiana|Maine|Maryland|Massachusetts|Michigan|Minnesota|Mississippi|Missouri|Montana|Nebraska|Nevada|New Hampshire|New Jersey|New Mexico|New York|North Carolina|North Dakota|Ohio|Oklahoma|Oregon|Pennsylvania|Rhode Island|South Carolina|South Dakota|Tennessee|Texas|Utah|Vermont|Virginia|Washington|West Virginia|Wisconsin|Wyoming|Puerto Rico|Virgin Islands|Guam""".split("|")
STATE_CODES = "AL AK AZ AR CA CO CT DE DC FL GA HI ID IL IN IA KS KY LA ME MD MA MI MN MS MO MT NE NV NH NJ NM NY NC ND OH OK OR PA RI SC SD TN TX UT VT VA WA WV WI WY PR VI GU".split()
STATE_LOOKUP = {name.casefold(): code for name, code in zip(STATE_NAMES, STATE_CODES)}
STATE_LOOKUP.update({code.casefold(): code for code in STATE_CODES})
STATE_LOOKUP["country of mexico"] = "MX"


def normalize_county(value):
    """Remove county-equivalent suffixes while preserving independent cities."""
    value = unicodedata.normalize("NFKD", value.casefold().strip())
    value = "".join(char for char in value if not unicodedata.combining(char))
    value = value.replace("(city)", "city")
    value = re.sub(r"\s+(city and borough|census area|municipality|borough|county|parish|municipio)$", "", value)
    value = re.sub(r"^st[.]?\s+", "saint ", value)
    value = re.sub(r"^ste[.]?\s+", "sainte ", value)
    return re.sub(r"[^a-z0-9]", "", value)


def add_join_keys(frame):
    frame = frame.copy()
    frame["_state"] = frame["State"].str.strip().str.casefold().map(STATE_LOOKUP)
    if frame["_state"].isna().any():
        raise ValueError(f"Unknown states: {frame.loc[frame['_state'].isna(), 'State'].unique()}")
    frame["_county"] = frame["County"].map(normalize_county)
    # EPA spellings that differ from the Census county names.
    aliases = {("VA", "charles"): "charlescity", ("PR", "mayagnez"): "mayaguez"}
    frame["_county"] = [
        aliases.get((state, county), county)
        for state, county in zip(frame["_state"], frame["_county"])
    ]
    return frame


def main():
    aqi = add_join_keys(pd.read_csv(PROJECT_DIR / "countyAQI.csv"))
    ses = add_join_keys(pd.read_csv(PROJECT_DIR / "countySES.csv"))
    covid_path = PROJECT_DIR / "Provisional_COVID-19_Death_Counts_in_the_United_States_by_County_20261023.csv"
    covid = pd.read_csv(
        covid_path,
        usecols=["State", "County name", "Deaths involving COVID-19"],
        dtype="string",
    ).rename(columns={"County name": "County", "Deaths involving COVID-19": "COVID_19_Deaths"})
    # Suppressed or unavailable counts remain missing, rather than becoming zero.
    covid["COVID_19_Deaths"] = pd.to_numeric(
        covid["COVID_19_Deaths"].str.replace(",", "", regex=False), errors="raise"
    ).astype("Int64")
    covid = add_join_keys(covid)
    keys = ["_state", "_county"]
    # Retain every county with AQI data, even when another source lacks a match.
    joined = aqi.merge(
        ses[keys + ["SES_Label"]], on=keys, how="left", validate="one_to_one", indicator="_ses_match"
    ).merge(
        covid[keys + ["COVID_19_Deaths"]], on=keys, how="left", validate="one_to_one", indicator="_covid_match"
    )
    print(f"Joined {len(joined):,} counties with AQI data.")
    for source in ["ses", "covid"]:
        missing = joined.loc[joined[f"_{source}_match"] == "left_only", ["State", "County"]]
        print(f"Counties without a {source.upper()} match: {len(missing)}")
        if not missing.empty:
            print(missing.to_string(index=False))
    joined[["State", "County", "Average_AQI", "SES_Label", "COVID_19_Deaths"]].to_csv(
        PROJECT_DIR / "countyLevelData.csv", index=False
    )
    from covid_mortality_cleaner import main as join_mortality
    join_mortality()


if __name__ == "__main__":
    main()
