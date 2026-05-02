import os

import pandas as pd
import streamlit as st

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

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

    grade_df = pd.DataFrame({"Letter Grade": GRADE_ORDER})
    grade_df = grade_df.merge(grade_counts, on="Letter Grade", how="left")
    grade_df["Count"] = grade_df["Count"].fillna(0).astype(int)
    grade_df["Proportion"] = grade_df["Count"] / full_total if full_total > 0 else 0.0

    other_count = int(grade_df.loc[grade_df["Letter Grade"] == "Other", "Count"].sum())

    # Build CDF: each entry is the cumulative proportion from A down to that grade
    letter_grades = [g for g in GRADE_ORDER if g != "Other"]
    cumulative_set: set = set()
    summary: dict = {}
    summary_counts: dict = {}
    for i, grade in enumerate(letter_grades):
        cumulative_set.add(grade)
        label = f"% {grade}" if i == 0 else f"% {grade} or better"
        count = int(
            grade_df.loc[grade_df["Letter Grade"].isin(cumulative_set), "Count"].sum()
        )
        summary[label] = count / full_total if full_total > 0 else 0.0
        summary_counts[label] = count

    summary["% Withdrawals"] = other_count / full_total if full_total > 0 else 0.0
    summary_counts["% Withdrawals"] = other_count

    return grade_df, summary, summary_counts, full_total
