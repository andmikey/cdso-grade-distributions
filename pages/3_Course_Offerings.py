import pandas as pd
import streamlit as st

from data_utils import DATA_FILES, SEASON_ORDER, load_data


def _semester_sort_key(semester: str) -> tuple:
    parts = semester.split(" ")
    year = int(parts[1])
    season = SEASON_ORDER.get(parts[0], 99)
    return (year, season)


st.title("Course Offerings Over Time")
st.caption("See which semesters each course has been offered for a given degree.")

degree = st.selectbox("Degree", options=list(DATA_FILES.keys()), key="offerings_degree")

SEASONS = ["Spring", "Summer", "Fall"]

season_filter = st.selectbox(
    "Semester",
    options=["All"] + SEASONS,
    key="offerings_season",
)

df = load_data(degree)

# All semesters across the whole dataset, sorted chronologically
all_sems: list[str] = sorted(df["Semester"].unique().tolist(), key=_semester_sort_key)

# Apply season filter
if season_filter != "All":
    all_sems = [s for s in all_sems if s.startswith(season_filter)]

all_sems_recent_first = list(reversed(all_sems))

# All courses for this degree
all_courses: list[str] = sorted(df["Course Name"].unique().tolist())

# Set of (course, semester) pairs where the course was offered
offered_set: set[tuple[str, str]] = set(zip(df["Course Name"], df["Semester"]))

# -------------------------------------------------------------------------
# Table 1: Detailed offerings
# -------------------------------------------------------------------------
st.subheader("Detailed Offerings")
st.caption("Whether each course was offered in each semester (most recent first).")

detail_rows = []
for course in all_courses:
    row: dict = {"Course": course}
    for sem in all_sems_recent_first:
        row[sem] = "✅" if (course, sem) in offered_set else ""
    detail_rows.append(row)

detail_df = pd.DataFrame(detail_rows).set_index("Course")
st.dataframe(detail_df, use_container_width=True)

# -------------------------------------------------------------------------
# Table 2: Availability summary
# -------------------------------------------------------------------------
st.subheader("Availability Summary")
st.caption(
    "Percentage of eligible past semesters in which each course was offered, "
    "broken down by semester. The denominator starts from the semester the course first appeared."
)

# Pre-compute each course's first semester using all semesters (unfiltered by season)
# so the "first offered" baseline is always accurate.
all_sems_unfiltered: list[str] = sorted(
    df["Semester"].unique().tolist(), key=_semester_sort_key
)

course_first_key: dict[str, tuple] = {}
for course in all_courses:
    course_sems = [s for s in all_sems_unfiltered if (course, s) in offered_set]
    if course_sems:
        course_first_key[course] = _semester_sort_key(course_sems[0])

# Which seasons to show columns for
seasons_to_show = [season_filter] if season_filter != "All" else SEASONS

summary_rows = []
for course in all_courses:
    first_key = course_first_key.get(course)
    if first_key is None:
        continue
    row: dict = {"Course": course}
    for season in seasons_to_show:
        # Eligible = semesters of this season that are >= course's first semester
        # and are within the filtered set
        eligible = [
            s
            for s in all_sems_unfiltered
            if s.startswith(season) and _semester_sort_key(s) >= first_key
        ]
        # When a season filter is active, restrict eligible to only filtered sems
        if season_filter != "All":
            eligible = [s for s in eligible if s in all_sems]
        if not eligible:
            row[season] = "N/A"
        else:
            offered_count = sum(1 for s in eligible if (course, s) in offered_set)
            pct = offered_count / len(eligible) * 100
            row[season] = f"{pct:.0f}%"
    summary_rows.append(row)

summary_df = pd.DataFrame(summary_rows).set_index("Course")
st.dataframe(summary_df, use_container_width=True)
