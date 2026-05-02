import os
import pandas as pd
import plotly.graph_objects as go
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

# Grade buckets for summary table (all use graded denominator unless noted)
BUCKET_A = {"A", "A-"}  # spec: A or A-
BUCKET_B_MINUS = {"A", "A-", "B+", "B", "B-"}
BUCKET_C = {"A", "A-", "B+", "B", "B-", "C+", "C"}


# ---------------------------------------------------------------------------
# Data layer
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


@st.cache_data
def aggregate(degree: str, course: str, semesters: tuple) -> tuple[pd.DataFrame, dict]:
    """
    Filter data to the chosen course and semesters, sum counts, compute
    proportions, and return (grade_df, summary_dict).

    `semesters` must be a tuple (hashable) for cache keying.
    """
    df = load_data(degree)
    mask = (df["Course Name"] == course) & (df["Semester"].isin(semesters))
    filtered = df[mask].copy()

    # Sum counts by letter grade
    grade_counts = (
        filtered.groupby("Letter Grade", as_index=False)["Count of letter grade"]
        .sum()
        .rename(columns={"Count of letter grade": "Count"})
    )

    full_total = grade_counts["Count"].sum()
    other_count = grade_counts.loc[
        grade_counts["Letter Grade"] == "Other", "Count"
    ].sum()
    graded_total = full_total - other_count if EXCLUDE_OTHER_FROM_DENOM else full_total

    # Build a complete frame in canonical grade order (zeros for missing grades)
    grade_df = pd.DataFrame({"Letter Grade": GRADE_ORDER})
    grade_df = grade_df.merge(grade_counts, on="Letter Grade", how="left")
    grade_df["Count"] = grade_df["Count"].fillna(0).astype(int)
    grade_df["Proportion"] = grade_df["Count"] / full_total if full_total > 0 else 0.0

    # Summary stats
    def graded_pct(bucket: set) -> float:
        if graded_total == 0:
            return 0.0
        total_in_bucket = grade_df.loc[
            grade_df["Letter Grade"].isin(bucket), "Count"
        ].sum()
        return total_in_bucket / graded_total

    def full_pct(bucket: set) -> float:
        if full_total == 0:
            return 0.0
        total_in_bucket = grade_df.loc[
            grade_df["Letter Grade"].isin(bucket), "Count"
        ].sum()
        return total_in_bucket / full_total

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


# ---------------------------------------------------------------------------
# Panel renderer
# ---------------------------------------------------------------------------


def render_panel(ctx, key_prefix: str = "") -> None:
    """
    Render one complete panel (controls + chart + table) inside the given
    Streamlit context object (a column or st itself).
    """
    degree = ctx.selectbox(
        "Degree",
        options=list(DATA_FILES.keys()),
        key=f"{key_prefix}_degree",
    )

    df = load_data(degree)
    courses = get_courses(df)

    course = ctx.selectbox(
        "Course",
        options=courses,
        key=f"{key_prefix}_course",
    )

    available_semesters = get_semesters(df, course)
    default_semester = [available_semesters[-1]] if available_semesters else []

    selected_semesters = ctx.multiselect(
        "Semester(s)",
        options=available_semesters,
        default=default_semester,
        key=f"{key_prefix}_semesters",
    )

    if not selected_semesters:
        ctx.info("Select at least one semester to view the grade distribution.")
        return

    grade_df, summary, summary_counts, full_total = aggregate(
        degree, course, tuple(sorted(selected_semesters))
    )

    # --- Bar chart ---
    semester_label = (
        ", ".join(selected_semesters)
        if len(selected_semesters) == 1
        else f"{len(selected_semesters)} semesters"
    )
    chart_title = f"{course} ({degree}) — {semester_label}"

    fig = go.Figure(
        go.Bar(
            x=grade_df["Letter Grade"],
            y=(grade_df["Proportion"] * 100).round(1),
            customdata=grade_df["Count"],
            marker_color=BAR_COLOR,
            hovertemplate="%{x}: %{customdata} students (%{y:.1f}%)<extra></extra>",
        )
    )
    fig.update_layout(
        title=chart_title,
        xaxis_title="Letter Grade",
        yaxis_title="Proportion of students (%)",
        xaxis=dict(categoryorder="array", categoryarray=GRADE_ORDER),
        yaxis=dict(range=[0, 100]),
        margin=dict(t=50, b=40, l=50, r=20),
        plot_bgcolor="white",
        paper_bgcolor="white",
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(showgrid=True, gridcolor="#e0e0e0")

    ctx.plotly_chart(fig, width="stretch", key=f"{key_prefix}_chart")

    ctx.caption(f"Total students: {full_total:,}")

    # --- Summary table ---
    summary_df = pd.DataFrame(
        {
            "Metric": list(summary.keys()),
            "%": [f"{v * 100:.1f}%" for v in summary.values()],
            "Count": [summary_counts[k] for k in summary.keys()],
        }
    )
    ctx.table(summary_df.set_index("Metric"))


# ---------------------------------------------------------------------------
# App shell
# ---------------------------------------------------------------------------

st.set_page_config(layout="wide", page_title="UT Grade Distributions")

st.title("UT Austin CDSO Course Grade Distributions")
st.caption(
    "Explore grade distributions for MSCS, MSDS, and MSAI courses. "
    "Data is aggregated across the selected semesters."
)

compare_mode = st.toggle("Compare two courses")

if compare_mode:
    col_left, col_right = st.columns(2)
    render_panel(col_left, key_prefix="left")
    render_panel(col_right, key_prefix="right")
else:
    render_panel(st, key_prefix="main")
