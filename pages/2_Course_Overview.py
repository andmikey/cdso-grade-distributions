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
for course in courses:
    # Check the course has any data in the selected semesters before aggregating
    mask = (df["Course Name"] == course) & (df["Semester"].isin(selected_semesters))
    if not df[mask].empty:
        _, summary, _, full_total = aggregate(degree, course, semesters_tuple)
        rows.append(
            {
                "Course": course,
                "Total Students": full_total,
                "% A or A-": round(summary["% A or A-"] * 100, 1),
                "% at least B-": round(summary["% at least B-"] * 100, 1),
                "% at least C": round(summary["% at least C"] * 100, 1),
                "% Withdrawal": round(summary["% withdrawal"] * 100, 1),
            }
        )

if not rows:
    st.info("No courses have data for the selected semester(s).")
    st.stop()

overview_df = pd.DataFrame(rows)

st.dataframe(
    overview_df,
    use_container_width=True,
    hide_index=True,
    column_config={
        "Course": st.column_config.TextColumn("Course"),
        "Total Students": st.column_config.NumberColumn("Total Students", format="%d"),
        "% A or A-": st.column_config.NumberColumn("% A or A-", format="%.1f%%"),
        "% at least B-": st.column_config.NumberColumn(
            "% at least B-", format="%.1f%%"
        ),
        "% at least C": st.column_config.NumberColumn("% at least C", format="%.1f%%"),
        "% Withdrawal": st.column_config.NumberColumn("% Withdrawal", format="%.1f%%"),
    },
)
