
import pandas as pd

from data_laden import (
    glucose,
    activity,
    basal,
    bolus,
    carbs,
    bmi,
    metadata
)


# General data quality

datasets = {
    "Glucose": (glucose, "bg_ts"),
    "Activity": (activity, "activity_ts"),
    "Basal": (basal, "basal_ts"),
    "Bolus": (bolus, "bolus_ts"),
    "Carbs": (carbs, "meal_ts"),
    "BMI": (bmi, None),
    "Metadata": (metadata, None)
}

print("\nDATA QUALITY OVERVIEW")

for name, (df, timestamp_col) in datasets.items():

    print(f"\n{name}")
    print("Rows:", len(df))
    print("Columns:", len(df.columns))
    print("Missing values:", df.isna().sum().sum())
    print("Duplicate rows:", df.duplicated().sum())

    print("\nMissing values per column:")
    print(df.isna().sum())


# Check participant IDs

for name, (df, timestamp_col) in datasets.items():
    if "participant_id" not in df.columns:
        raise ValueError(
            f"{name} has no participant_id column. "
            "Add participant IDs in data_laden.py first."
        )


# Quality per dataset and participant

quality_tables = []

for name, (df, timestamp_col) in datasets.items():

    for participant, group in df.groupby("participant_id"):

        result = {
            "participant_id": participant,
            f"{name}_rows": len(group),
            f"{name}_missing": group.isna().sum().sum(),
            f"{name}_duplicates": group.duplicated().sum()
        }

        if timestamp_col is not None:

            timestamps = pd.to_datetime(
                group[timestamp_col],
                errors="coerce",
                dayfirst=True
            )

            result[f"{name}_missing_timestamps"] = timestamps.isna().sum()

            result[f"{name}_duplicate_timestamps"] = (
                timestamps.duplicated().sum()
            )

        quality_tables.append(result)


# Combine participant results

quality_summary = pd.DataFrame(quality_tables)

quality_summary = (
    quality_summary
    .groupby("participant_id")
    .first()
    .fillna(0)
    .astype(float)
)


# CGM measurement intervals

glucose_check = glucose.copy()

glucose_check["bg_ts"] = pd.to_datetime(
    glucose_check["bg_ts"],
    errors="coerce",
    dayfirst=True
)

glucose_check["value"] = pd.to_numeric(
    glucose_check["value"],
    errors="coerce"
)

glucose_check = glucose_check.sort_values(
    ["participant_id", "bg_ts"]
)

cgm_results = []

for participant, group in glucose_check.groupby("participant_id"):

    # Use unique timestamps to calculate intervals
    timestamps = (
        group["bg_ts"]
        .dropna()
        .drop_duplicates()
        .sort_values()
    )

    intervals = timestamps.diff().dt.total_seconds() / 60

    valid_intervals = intervals.dropna()

    cgm_results.append({
        "participant_id": participant,
        "CGM_intervals_1_4_min": (
            (valid_intervals > 0) &
            (valid_intervals < 5)
        ).sum(),
        "CGM_intervals_5_min": (
            valid_intervals == 5
        ).sum(),
        "CGM_intervals_over_5_min": (
            valid_intervals > 5
        ).sum(),
        "CGM_gaps_over_10_min": (
            valid_intervals > 10
        ).sum(),
        "CGM_median_interval": valid_intervals.median()
    })

cgm_summary = pd.DataFrame(cgm_results)

quality_summary = quality_summary.join(
    cgm_summary.set_index("participant_id")
)



# General data quality overview

print("\nDATA QUALITY OVERVIEW")

overview = []

for name, (df, timestamp_col) in datasets.items():

    overview.append({
        "Dataset": name,
        "Rows": len(df),
        "Missing": df.isna().sum().sum(),
        "Duplicates": df.duplicated().sum()
    })

overview_df = pd.DataFrame(overview)

print(overview_df.to_string(index=False))


# Quality per participant

print("\nQUALITY PER PARTICIPANT")

columns = [
    "Glucose_rows",
    "Glucose_duplicates",
    "Glucose_duplicate_timestamps",
    "Activity_rows",
    "Activity_duplicates",
    "Basal_rows",
    "Basal_missing",
    "Bolus_rows",
    "Bolus_missing",
    "Carbs_rows",
    "Carbs_missing",
    "CGM_gaps_over_10_min"
]

participant_table = quality_summary[
    [col for col in columns if col in quality_summary.columns]
].reset_index()

print(
    participant_table.to_string(
        index=False,
        float_format=lambda x: f"{x:.0f}"
    )
)


# Best participants for initial testing

print("\nPARTICIPANTS FOR INITIAL TESTING")

candidates = participant_table[
    (participant_table["Glucose_rows"] > 0) &
    (participant_table["Bolus_rows"] > 0) &
    (participant_table["Carbs_rows"] > 0)
].copy()

candidates = candidates.sort_values(
    by=["CGM_gaps_over_10_min", "Glucose_rows"],
    ascending=[True, False]
)

print(
    candidates[
        [
            "participant_id",
            "Glucose_rows",
            "Bolus_rows",
            "Carbs_rows",
            "CGM_gaps_over_10_min"
        ]
    ].head(5).to_string(index=False)
)


# Save results

overview_df.to_csv(
    "data_quality_overview.csv",
    index=False
)

participant_table.to_csv(
    "data_quality_per_participant.csv",
    index=False
)

# Save results

quality_summary.to_csv(
    "data_quality_per_participant.csv"
)

print("\nData quality assessment completed")
