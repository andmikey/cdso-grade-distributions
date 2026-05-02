# UT CDSO grade distribution dashboard

This is a simple Streamlit app to view historical grade distributions for CDSO degrees (MSCSO, MSDSO, MSAIO).

You can view the running app [here](https://cdso-grade-distributions.streamlit.app/), using Streamlit Cloud. 

## Adding new courses 

Update the relevant file in [this folder](grade_data/course_listing). The "Course Title" is used for matching against grade distributions and the "Course Name" is used for display. The "Course Code" is currently ignored but may be used in the future.

## Adding new grade distributions

This needs to be done once a semester. Open the [grade distribution dashboard](https://iq-analytics.austin.utexas.edu/views/Gradedistributiondashboard/Externaldashboard-Crosstab?%3Aembed=y&%3AisGuestRedirectFromVizportal=n), go to the "bar graph view" and filter:
- Academic year: of your choice
- Course prefix: AI, CS, DSC
- Semesters: all
- Grade level of detail: expanded

Go to Download -> Data and put the CSV in [this folder](grade_data/csvs). 

Run the CSV parsing script in `grade_data/course_data_parser.py` to generate the per-degree data tables in [this folder](grade_data/parsed_csvs).

Future work: [UT Grade Parser](https://github.com/doprz/UT_Grade_Parser/tree/main) should in theory automate this but I couldn't get it to work so it was faster to just do manually. 