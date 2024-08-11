from io import StringIO
import pandas as pd
from bs4 import BeautifulSoup

credit_4 = ["BMATS101", "BPHYS102"]
credit_3 = ["BPOPS103", "BESCK104B", "BETCK105H"]
credit_2 = []
credit_1 = ["BENGK106", "BKSKK107", "BIDTK158", "BKBKK107"]


def extractor(saved_html):
    with open(saved_html, "r", encoding="utf-8") as file:
        soup = BeautifulSoup(file, "lxml")

    rows = soup.find_all("div", class_="divTableRow")
    html_string = str(soup)
    tables = pd.read_html(StringIO(html_string))

    table_data = []
    for row in rows:
        cells = row.find_all("div", class_="divTableCell")
        row_data = [cell.text.strip() for cell in cells]
        table_data.append(row_data)

    df_marks = pd.DataFrame(table_data[1:9], columns=table_data[0])
    df_marks = df_marks.drop('Announced / Updated on', axis=1)

    sub_status = list(df_marks["Result"])
    grade = []
    total_credits = 0
    details = []
    details.append(tables[0][1][0].strip(":"))
    details.append(tables[0][1][1].strip(":"))

    if "F" not in sub_status:
        for i in list(df_marks["Total"]):
            if int(i) >= 90:
                grade.append(10)
            elif int(i) >= 80:
                grade.append(9)
            elif int(i) >= 70:
                grade.append(8)
            elif int(i) >= 60:
                grade.append(7)
            elif int(i) >= 50:
                grade.append(6)
            elif int(i) >= 40:
                grade.append(5)

        # print(grade)

        df_marks.insert(6, "Grade Points", grade)

        credit_obtained = []
        for i, j in zip(list(df_marks["Grade Points"]), list(df_marks["Subject Code"])):
            if j in credit_4:
                credit_obtained.append(4 * i)
                total_credits += 4 * 1
            elif j in credit_3:
                credit_obtained.append(3 * i)
                total_credits += 3 * 1
            elif j in credit_2:
                credit_obtained.append(2 * i)
                total_credits += 2 * 1
            if j in credit_1:
                credit_obtained.append(1 * i)
                total_credits += 1 * 1

        df_marks.insert(7, "Credits Obtained", credit_obtained)

        details.append(sum([int(x) for x in list(df_marks["Total"])]))
        total_credits_obtained = sum([int(x) for x in list(df_marks["Credits Obtained"])])

        details.append(total_credits_obtained / total_credits)
        details.append("PASS")

    else:
        details.append(sum([int(x) for x in list(df_marks["Total"])]))
        details.append("NAN")
        count = sub_status.count("F")
        details.append(f"{count} Fail")

    return df_marks, details

    # list return usn ,name,total,gpa,res
