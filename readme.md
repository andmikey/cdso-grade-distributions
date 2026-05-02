# UT CDSO grade distribution dashboard

## Getting the grade distributions

Open the [grade distribution dashboard](https://iq-analytics.austin.utexas.edu/views/Gradedistributiondashboard/Externaldashboard-Crosstab?%3Aembed=y&%3AisGuestRedirectFromVizportal=n), go to the "bar graph view" and filter:
- Academic year: of your choice
- Course prefix: AI, CS, DSC
- Semesters: all
- Grade level of detail: expanded

Go to Download -> Data and put the CSV in grade_data/csvs. 

Run the CSV parsing script in grade_data/course_data_parser.py to generate the per-degree data tables in grade_data/parsed_csvs.

Future work: [UT Grade Parser](https://github.com/doprz/UT_Grade_Parser/tree/main) should in theory automate this but I couldn't get it to work. 