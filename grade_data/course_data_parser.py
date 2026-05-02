import os
import glob
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
COURSE_LISTING_DIR = os.path.join(BASE_DIR, "course_listing")
GRADE_CSV_DIR = os.path.join(BASE_DIR, "csvs")
OUTPUT_DIR = os.path.join(BASE_DIR, "parsed_data")

# (course listing file, Course Prefix in grade CSVs, output file)
DEGREES = [
    ("cs_courses.csv", "C S", "cs_grades.csv"),
    ("ai_courses.csv", "A I", "ai_grades.csv"),
    ("ds_courses.csv", "DSC", "ds_grades.csv"),
]


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Load and combine all grade distribution CSVs
    grade_files = sorted(glob.glob(os.path.join(GRADE_CSV_DIR, "*.csv")))
    grades = pd.concat(
        [pd.read_csv(f, encoding="utf-8-sig") for f in grade_files],
        ignore_index=True,
    )
    grades["Course Prefix"] = grades["Course Prefix"].str.strip()

    for listing_file, prefix, output_file in DEGREES:
        courses = pd.read_csv(os.path.join(COURSE_LISTING_DIR, listing_file), sep=";")

        # Filter grade data to this degree's prefix and known courses
        filtered = grades[
            (grades["Course Prefix"] == prefix)
            & (grades["Course Title"].isin(courses["Course Title"]))
        ].copy()

        # Attach Course Name from the listing
        result = filtered.merge(
            courses[["Course Title", "Course Name"]],
            on="Course Title",
        )

        # Select just the columns we want
        result = result[
            ["Semester", "Course Name", "Letter Grade", "Count of letter grade"]
        ]

        # Sort chronologically, then by course name, then by grade
        season_order = {"Spring": 0, "Summer": 1, "Fall": 2}
        grade_order = {
            "A+": 0,
            "A": 1,
            "A-": 2,
            "B+": 3,
            "B": 4,
            "B-": 5,
            "C+": 6,
            "C": 7,
            "C-": 8,
            "D+": 9,
            "D": 10,
            "D-": 11,
            "F": 12,
            "Other": 13,
        }
        result[["Season", "Year"]] = result["Semester"].str.split(" ", expand=True)
        result["Year"] = result["Year"].astype(int)
        result["SeasonOrder"] = result["Season"].map(season_order)
        result["GradeOrder"] = result["Letter Grade"].map(grade_order)
        result = result.sort_values(
            ["Year", "SeasonOrder", "Course Name", "GradeOrder"]
        ).drop(columns=["Season", "Year", "SeasonOrder", "GradeOrder"])

        output_path = os.path.join(OUTPUT_DIR, output_file)
        result.to_csv(output_path, index=False)
        print(f"Written {output_path} ({len(result)} rows)")


if __name__ == "__main__":
    main()
