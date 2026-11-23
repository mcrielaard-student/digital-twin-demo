
import pandas as pd

from data_laden import glucose


# Clean glucose data

glucose_clean = glucose.copy()

# Convert datatypes
glucose_clean["bg_ts"] = pd.to_datetime(
    glucose_clean["bg_ts"],
    dayfirst=True,
    errors="coerce"
)

glucose_clean["value"] = pd.to_numeric(
    glucose_clean["value"],
    errors="coerce"
)

# Remove exact duplicate measurements
before = len(glucose_clean)

glucose_clean = glucose_clean.drop_duplicates(
    subset=["participant_id", "bg_ts", "value"]
)

print("Exact duplicate rows removed:", before - len(glucose_clean))


# Identify conflicting measurements
conflicting_glucose = glucose_clean[
    glucose_clean.duplicated(
        subset=["participant_id", "bg_ts"],
        keep=False
    )
].copy()

print(
    "Rows with conflicting timestamps:",
    len(conflicting_glucose)
)


# Sort glucose data
glucose_clean = glucose_clean.sort_values(
    ["participant_id", "bg_ts"]
).reset_index(drop=True)


# Save results
glucose_clean.to_csv(
    "glucose_clean.csv",
    index=False
)

conflicting_glucose.to_csv(
    "conflicting_glucose.csv",
    index=False
)

print("\nGlucose cleaning completed!")
print("Original measurements:", len(glucose))
print("Remaining measurements:", len(glucose_clean))
