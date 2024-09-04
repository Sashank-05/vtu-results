import pandas as pd

from helper import dbhandler, extract_table


def neat_marks(sem: int, usn: str, batch=23):
    table = dbhandler.DBHandler()
    table_name = usn[1:5]
    branch = usn[5:7]
    try:
        marks = table.get_student_marks(f"{table_name}{branch}", sem, usn)
        column = table.get_columns(f"BI{batch}CD_SEM_{sem}")
    except:
        print("here")
        return 0


    new_column = []

    for i in column[2:20]:
        if "_" in i:
            new_column.append(i.removesuffix("_internal").removesuffix("_external"))
        else:
            new_column.append(i)

    new_column = list(dict.fromkeys(new_column[0:16]))

    internal_marks = []
    external_marks = []
    total_marks = []
    result = []

    for i in range(2, len(marks[0]) - 3):
        if i % 2 == 0:
            internal_marks.append(marks[0][i])
        else:
            external_marks.append(marks[0][i])

    for i, j in zip(internal_marks, external_marks):
        total_marks.append(int(i) + int(j))
        if int(i) >= 20 and int(j) >= 18 and int(i+j) >= 40:
            result.append("P")
        else:
            result.append("F")

    # print(new_column,internal_marks,external_marks,total_marks,marks[0][18],marks[0][19])

    column_names = ["Subject Code", "internal marks", "external marks", "Total", "Result"]

    df = pd.DataFrame(list(zip(new_column, internal_marks, external_marks, total_marks, result)), columns=column_names)
    # print(df)
    df, extras = extract_table.cal(df, [])
    html_table = df.to_html(index=False)
    if html_table: 
        print("lol")
        return html_table, extras
    
        


if __name__ == "__main__":
    print(neat_marks(2, "1bi23cd055"))