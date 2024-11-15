import json
import logging
import os
from io import StringIO
import pprint

import pandas as pd
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(module)s - %(message)s')

with open(os.path.join(os.path.dirname(__file__), '../static/data.json'), 'r') as file:
    subject_data = json.load(file)


import pandas as pd
from bs4 import BeautifulSoup
from io import StringIO

def extractor(saved_html):
    with open(saved_html, "r", encoding="utf-8") as file:
        soup = BeautifulSoup(file, "lxml")

    html_string = str(soup)
    tables = pd.read_html(StringIO(html_string))

    rows = soup.find_all("div", class_="divTableRow")
    column_names = ['Subject Code', 'Subject Name', 'Internal Marks', 'External Marks', 'Total', 'Result', 'Announced / Updated on']
    target_string="Semester : "
    sems=[int((x.text).replace(target_string,""))for x in soup.find_all("div",{"style":"text-align:center;padding:5px;"})]
    print(sems)
    table_data = []
    table1_data = []
    dfs = {}
    i=0
    for row in rows:
        cells = [cell.text.strip() for cell in row.find_all("div", class_="divTableCell")]
        table_data.append(cells)

    for row in table_data[:-1]:
        if row == column_names:
            if table1_data:
                dfs[sems[i]]=(pd.DataFrame(table1_data[1:], columns=table1_data[0]).drop('Announced / Updated on', axis=1))
                table1_data = []
                i+=1
            table1_data.append(row)
        else:
            table1_data.append(row)

    if table1_data:
        #i+=1
        dfs[sems[i]]=(pd.DataFrame(table1_data[1:], columns=table1_data[0]).drop('Announced / Updated on', axis=1))
        

    details = [tables[0][1][0].strip(":"), tables[0][1][1].strip(":")]

    return dfs, details



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

        #logging.info(df_marks)
        print(df_marks)
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

    #print("\n \n \n \n ",df_marks,"\n \n \n \n next one")
    return df_marks, details


if __name__=="__main__":
    dfs, details = extractor("C:/Users/Admin/Desktop/New folder/vtu-results/tempwork/pages/1BI22CD004.html")
    pprint.pprint(dfs)