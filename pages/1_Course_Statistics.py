import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from data_utils import (
    DATA_FILES,
    GRADE_ORDER,
    BAR_COLOR,
    load_data,
    get_courses,
    get_semesters,
    aggregate,
)


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
