import json
import logging
import os
from io import StringIO

import pandas as pd
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(module)s - %(message)s')

with open(os.path.join(os.path.dirname(__file__), '../static/data.json'), 'r') as file:
    subject_data = json.load(file)


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

    details: list = list()
    details.append(tables[0][1][0].strip(":"))
    details.append(tables[0][1][1].strip(":"))

    return df_marks, details


def cal(df_marks, details):
    sub_status = list(df_marks["Result"])
    grade: list = []
    total_credits = 0

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

        try:
            df_marks.insert(6, "Grade Points", grade)
        except:
            df_marks["Grade Points"] = grade

        credit_obtained: list = []
        for i, j in zip(list(df_marks["Grade Points"]), list(df_marks["Subject Code"])):
            credits = subject_data.get(j.strip(), {}).get("Credits", 0)
            credit_obtained.append(credits * i)
            total_credits += credits

        try:
            df_marks.insert(7, "Credits Obtained", credit_obtained)
        except:
            df_marks["Credits Obtained"] = credit_obtained

        logging.info(df_marks)
        details.append(sum([int(x) for x in list(df_marks["Total"])]))
        total_credits_obtained = sum([int(x) for x in list(df_marks["Credits Obtained"])])

        details.append(total_credits_obtained / total_credits)
        details.append("PASS")

    else:
        try:
            details.append(sum([int(x) for x in list(df_marks["Total"])]))
        except:
            details.append(" ")

        details.append("NAN")
        count = sub_status.count("F")
        details.append(f"{count} Fail")

    return df_marks, details
