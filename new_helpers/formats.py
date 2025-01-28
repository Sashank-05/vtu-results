import logging
import os

import pandas as pd

if os.getcwd().endswith('new_helpers'):
    import dbhandler, extract
else:
    from new_helpers import dbhandler, extract

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(module)s - %(message)s')


def neat_marks(sem: int, usn: str, batch=23):  # fixed this function
    table = dbhandler.DBHandler()
    table_name = usn[1:5]
    branch = usn[5:7]

    try:
        marks = table.get_student_marks(f"{table_name}{branch}", sem, usn)
        column = table.get_columns(f"BI{batch}CD_SEM_{sem}")
    except Exception as e:
        logging.error(f"Error fetching marks or columns: {e}")
        return 0

    new_column = []
    for col in column[2:20]:
        if "_" in col:
            new_column.append(col.removesuffix("_internal").removesuffix("_external"))
        else:
            new_column.append(col)
    new_column = list(dict.fromkeys(new_column[0:16]))

    internal_marks, external_marks, total_marks, result = [], [], [], []
    for i in range(2, len(marks[0]) - 3):
        if i % 2 == 0:
            internal_marks.append(marks[0][i])
        else:
            external_marks.append(marks[0][i])

    for internal, external in zip(internal_marks, external_marks):
        total = int(internal) + int(external)
        total_marks.append(total)
        result.append("P" if int(internal) >= 20 and int(external) >= 18 and total >= 40 else "F")

    column_names = ["Subject Code", "Internal Marks", "External Marks", "Total", "Result"]
    df = pd.DataFrame(list(zip(new_column, internal_marks, external_marks, total_marks, result)), columns=column_names)
    extractor = extract.Extract()
    df_ = extractor.calculate(df)
    print(df_)
    df = df_[0]
    extras = df_[1]
    html_table = df.to_html(index=False)

    if html_table:
        logging.info("Successfully generated HTML table.")
        return html_table, extras
    else:
        logging.error("Failed to generate HTML table.")
        return [0], [0]


def dataframe_to_sql(df: pd.DataFrame) -> tuple:
    df = df.drop(columns=["Subject Name", "Grade Points", "Credits Obtained", "Result"], errors='ignore')
    internal_marks = list(df["Internal Marks"])
    external_marks = list(df["External Marks"])

    return internal_marks, external_marks


def df_to_csv(df, data):
    emp = ["", "", "", "", "", "", ""]
    emp.insert(0, data[2])
    emp.insert(0, data[3])
    df["Total Marks"] = emp[0]
    df["GPA"] = emp[1]
    directory = 'csv_files'
    file_path = os.path.join(directory, f'{data[0]}.csv')
    os.makedirs(directory, exist_ok=True)
    df.to_csv(file_path, index=False)


def get_subject_code(df):
    subjects = []

    for i in list(df["Subject Code"]):
        subjects.append(i + "_internal")
        subjects.append(i + "_external")
    subjects += ["Total", "GPA", "Result"]

    return subjects


if __name__ == "__main__":
    logging.info(neat_marks(1, "1bi23cd055"))
