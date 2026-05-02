import pandas as pd
import streamlit as st

from data_utils import (
    DATA_FILES,
    load_data,
    get_courses,
    get_all_semesters,
    aggregate,
)

st.title("Course Overview")
st.caption(
    "Compare all courses for a given degree and semester. "
    "Click any column header to sort."
)

degree = st.selectbox("Degree", options=list(DATA_FILES.keys()), key="overview_degree")

df = load_data(degree)
all_semesters = get_all_semesters(df)
default_semester = [all_semesters[-1]] if all_semesters else []

selected_semesters = st.multiselect(
    "Semester(s)",
    options=all_semesters,
    default=default_semester,
    key="overview_semesters",
)

if not selected_semesters:
    st.info("Select at least one semester to view the course overview.")
    st.stop()

semesters_tuple = tuple(sorted(selected_semesters))

# Build one row per course that has data in the selected semesters
courses = get_courses(df)
rows = []
cdf_keys: list[str] = []
for course in courses:
    # Check the course has any data in the selected semesters before aggregating
    mask = (df["Course Name"] == course) & (df["Semester"].isin(selected_semesters))
    if not df[mask].empty:
        _, summary, summary_counts, full_total = aggregate(
            degree, course, semesters_tuple
        )
        if not cdf_keys:
            cdf_keys = list(summary.keys())
        row: dict = {"Course": course, "Total Students": full_total}
        for key in summary:
            row[key] = round(summary[key] * 100, 1)
            row[key.replace("% ", "# ")] = summary_counts[key]
        rows.append(row)

if not rows:
    st.info("No courses have data for the selected semester(s).")
    st.stop()

full_df = pd.DataFrame(rows)

show_counts = st.toggle("Show counts", value=False, key="overview_display_mode")

if not show_counts:
    pct_cols = ["Course", "Total Students"] + cdf_keys
    overview_df = full_df[pct_cols]
    column_config: dict = {
        "Course": st.column_config.TextColumn("Course"),
        "Total Students": st.column_config.NumberColumn("Total Students", format="%d"),
    }
    for key in cdf_keys:
        column_config[key] = st.column_config.NumberColumn(key, format="%.1f%%")
else:
    count_keys = [k.replace("% ", "# ") for k in cdf_keys]
    cnt_cols = ["Course", "Total Students"] + count_keys
    overview_df = full_df[cnt_cols]
    column_config = {
        "Course": st.column_config.TextColumn("Course"),
        "Total Students": st.column_config.NumberColumn("Total Students", format="%d"),
    }
    for key in count_keys:
        column_config[key] = st.column_config.NumberColumn(key, format="%d")

st.dataframe(
    overview_df,
    width="stretch",
    hide_index=True,
    column_config=column_config,
)
