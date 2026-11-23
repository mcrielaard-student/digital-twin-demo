
import pandas as pd
from pathlib import Path

# Project paths
project_dir = Path(__file__).resolve().parent.parent
raw_dir = project_dir / "data" / "raw" / "T1D-UOM"


# Load participant data
bmi = pd.read_csv(raw_dir / "Demographics" / "UoMBMI.csv")

metadata = pd.read_csv(
    raw_dir / "Article Metadata" / "participant_metadata.csv"
)


# Load activity data
activity_list = []

for file in (raw_dir / "Activity Data").glob("*.csv"):
    df = pd.read_csv(file)
    df["participant_id"] = file.stem.replace("UoMActivity", "UoM")
    activity_list.append(df)

activity = pd.concat(activity_list, ignore_index=True)


# Load glucose data
glucose_list = []

for file in (raw_dir / "Glucose Data").glob("*.csv"):
    df = pd.read_csv(file)
    df["participant_id"] = file.stem.replace("UoMGlucose", "UoM")
    glucose_list.append(df)

glucose = pd.concat(glucose_list, ignore_index=True)


# Load basal insulin data
basal_list = []

for file in (raw_dir / "Insulin Data" / "Basal Data").glob("*.csv"):
    df = pd.read_csv(file)
    df["participant_id"] = file.stem.replace("UoMBasal", "UoM")
    basal_list.append(df)

basal = pd.concat(basal_list, ignore_index=True)


# Load bolus insulin data
bolus_list = []

for file in (raw_dir / "Insulin Data" / "Bolus Data").glob("*.csv"):
    df = pd.read_csv(file)
    df["participant_id"] = file.stem.replace("UoMBolus", "UoM")
    bolus_list.append(df)

bolus = pd.concat(bolus_list, ignore_index=True)


# Load carbohydrate data
carbs_list = []

for file in (raw_dir / "Nutrition Data").glob("*.csv"):
    df = pd.read_csv(file)
    df["participant_id"] = file.stem.replace("UoMCarbs", "UoM")
    carbs_list.append(df)

carbs = pd.concat(carbs_list, ignore_index=True)

# Standardize participant IDs

def clean_participant_id(df):

    if "participant_id" in df.columns:

        ids = df["participant_id"].astype(str).str.extract(
            r"(\d{4})"
        )[0]

        df["participant_id"] = ids.apply(
            lambda x: f"UoM{x}" if pd.notna(x) else pd.NA
        )

    return df


glucose = clean_participant_id(glucose)
activity = clean_participant_id(activity)
basal = clean_participant_id(basal)
bolus = clean_participant_id(bolus)
carbs = clean_participant_id(carbs)
bmi = clean_participant_id(bmi)
metadata = clean_participant_id(metadata)

print("Data laden succesvol")
