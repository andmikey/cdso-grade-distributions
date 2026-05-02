import streamlit as st

st.set_page_config(layout="wide", page_title="UT Grade Distributions")

pg = st.navigation(
    [
        st.Page("pages/1_Course_Statistics.py", title="Course Statistics"),
        st.Page("pages/2_Course_Overview.py", title="Course Overview"),
    ]
)
pg.run()
