import os

import pandas as pd
import streamlit as st

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# When True the denominator for A/B/C proportion buckets excludes "Other"
# (withdrawals).  Set to False to include "Other" in all denominators.
EXCLUDE_OTHER_FROM_DENOM = True

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "grade_data", "parsed_data")

DATA_FILES = {
    "CS": os.path.join(DATA_DIR, "cs_grades.csv"),
    "DS": os.path.join(DATA_DIR, "ds_grades.csv"),
    "AI": os.path.join(DATA_DIR, "ai_grades.csv"),
}

GRADE_ORDER = [
    "A",
    "A-",
    "B+",
    "B",
    "B-",
    "C+",
    "C",
    "C-",
    "D+",
    "D",
    "D-",
    "F",
    "Other",
]

SEASON_ORDER = {"Spring": 0, "Summer": 1, "Fall": 2}

BAR_COLOR = "#BF5700"  # UT Austin burnt orange

# Grade buckets (all use graded denominator unless noted)
BUCKET_A = {"A", "A-"}
BUCKET_B_MINUS = {"A", "A-", "B+", "B", "B-"}
BUCKET_C = {"A", "A-", "B+", "B", "B-", "C+", "C"}


# ---------------------------------------------------------------------------
# Data helpers
# ---------------------------------------------------------------------------


@st.cache_data
def load_data(degree: str) -> pd.DataFrame:
    """Load the parsed CSV for the given degree label (CS / DS / AI)."""
    path = DATA_FILES[degree]
    df = pd.read_csv(path)
    df["Count of letter grade"] = (
        pd.to_numeric(df["Count of letter grade"], errors="coerce")
        .fillna(0)
        .astype(int)
    )
    return df


def get_courses(df: pd.DataFrame) -> list[str]:
    """Return sorted list of unique course names in df."""
    return sorted(df["Course Name"].unique().tolist())


def _semester_sort_key(semester: str) -> tuple:
    parts = semester.split(" ")
    year = int(parts[1])
    season = SEASON_ORDER.get(parts[0], 99)
    return (year, season)


def get_semesters(df: pd.DataFrame, course: str) -> list[str]:
    """Return chronologically sorted semesters available for the given course."""
    semesters = df.loc[df["Course Name"] == course, "Semester"].unique().tolist()
    return sorted(semesters, key=_semester_sort_key)


def get_all_semesters(df: pd.DataFrame) -> list[str]:
    """Return chronologically sorted list of all unique semesters in df."""
    semesters = df["Semester"].unique().tolist()
    return sorted(semesters, key=_semester_sort_key)


@st.cache_data
def aggregate(
    degree: str, course: str, semesters: tuple
) -> tuple[pd.DataFrame, dict, dict, int]:
    """
    Filter data to the chosen course and semesters, sum counts, compute
    proportions, and return (grade_df, summary, summary_counts, full_total).

    `semesters` must be a tuple (hashable) for cache keying.
    """
    df = load_data(degree)
    mask = (df["Course Name"] == course) & (df["Semester"].isin(semesters))
    filtered = df[mask].copy()

    grade_counts = (
        filtered.groupby("Letter Grade", as_index=False)["Count of letter grade"]
        .sum()
        .rename(columns={"Count of letter grade": "Count"})
    )

    full_total = int(grade_counts["Count"].sum())
    other_count = int(
        grade_counts.loc[grade_counts["Letter Grade"] == "Other", "Count"].sum()
    )
    graded_total = full_total - other_count if EXCLUDE_OTHER_FROM_DENOM else full_total

    grade_df = pd.DataFrame({"Letter Grade": GRADE_ORDER})
    grade_df = grade_df.merge(grade_counts, on="Letter Grade", how="left")
    grade_df["Count"] = grade_df["Count"].fillna(0).astype(int)
    grade_df["Proportion"] = grade_df["Count"] / full_total if full_total > 0 else 0.0

    def graded_pct(bucket: set) -> float:
        if graded_total == 0:
            return 0.0
        return (
            float(grade_df.loc[grade_df["Letter Grade"].isin(bucket), "Count"].sum())
            / graded_total
        )

    def full_pct(bucket: set) -> float:
        if full_total == 0:
            return 0.0
        return (
            float(grade_df.loc[grade_df["Letter Grade"].isin(bucket), "Count"].sum())
            / full_total
        )

    summary = {
        "% A or A-": graded_pct(BUCKET_A),
        "% at least B-": graded_pct(BUCKET_B_MINUS),
        "% at least C": graded_pct(BUCKET_C),
        "% withdrawal": full_pct({"Other"}),
    }

    def bucket_count(bucket: set) -> int:
        return int(grade_df.loc[grade_df["Letter Grade"].isin(bucket), "Count"].sum())

    summary_counts = {
        "% A or A-": bucket_count(BUCKET_A),
        "% at least B-": bucket_count(BUCKET_B_MINUS),
        "% at least C": bucket_count(BUCKET_C),
        "% withdrawal": bucket_count({"Other"}),
    }

    return grade_df, summary, summary_counts, full_total
