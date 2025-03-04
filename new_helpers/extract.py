import json
import logging
import os
from io import StringIO
import pprint

import pandas
import pandas as pd
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(module)s - %(message)s')

with open(os.path.join(os.path.dirname(__file__), '../static/data.json'), 'r') as file:
    subject_data = json.load(file)


class Extract:
    def __init__(self, saved_html="C:/Users/visha/Desktop/vtu_extracter/vtu-results/tempwork/pages"):
        self.saved_html = saved_html

    def get_dfs(self) -> dict:
        """
        Extracts all the tables with sem from the HTML file
        returns
        {
            "Name" : XX,
            "USN" : XX,
            "1": df1,
            "2": df2,
            ...
            "8": None
        }
        :return: dict of name, USN and dataframes of each semester
        """

        with open(self.saved_html, "r", encoding="utf-8") as f:
            soup = BeautifulSoup(f, "lxml")

        html_string = str(soup)
        tables = pd.read_html(StringIO(html_string))

        rows = soup.find_all("div", class_="divTableRow")

        column_names = ['Subject Code',
                        'Subject Name',
                        'Internal Marks',
                        'External Marks',
                        'Total',
                        'Result',
                        'Announced / Updated on']

        target_string = "Semester : "

        sems = [int(x.text.replace(target_string, "")) for x in
                soup.find_all("div", {"style": "text-align:center;padding:5px;"})]

        table_data = []

        table1_data = []
        dfs = {}
        i = 0
        for row in rows:
            cells = [cell.text.strip() for cell in row.find_all("div", class_="divTableCell")]
            table_data.append(cells)

        for row in table_data[:-1]:
            if row == column_names:
                if table1_data:
                    dfs[sems[i]] = (
                        pd.DataFrame(table1_data[1:], columns=table1_data[0]).drop('Announced / Updated on', axis=1))
                    table1_data = []
                    i += 1
                table1_data.append(row)
            else:
                table1_data.append(row)

        if table1_data:
            # i+=1
            dfs[sems[i]] = (
                pd.DataFrame(table1_data[1:], columns=table1_data[0]).drop('Announced / Updated on', axis=1))

        details = [tables[0][1][0].strip(":"), tables[0][1][1].strip(":")]

        original = {"Name": details[0], "USN": details[1], **dfs}
        for sem in range(1, 9):
            if original.get(sem, None) is None:
                original[sem] = None

        return original

    @staticmethod
    def calculate(df: pandas.DataFrame) -> list:
        """
        Calculate the GPA and other details from the dataframe

        Example Input:
        pd.DataFrame
        0       BCS301        MATHEMATICS FOR COMPUTER SCIENCE  ...    56      P
        1       BCS302  DIGITAL DESIGN & COMPUTER ORGANIZATION  ...    77      P
        2       BCS303                       OPERATING SYSTEMS  ...    64      P
        3       BCS304        DATA STRUCTURES AND APPLICATIONS  ...    63      P
        4      BCSL305                     DATA STRUCTURES LAB  ...    90      P
        5      BSCK307       SOCIAL CONNECT AND RESPONSIBILITY  ...    97      P
        6      BPEK359                      PHYSICAL EDUCATION  ...    83      P
        7      BCS358A               DATA ANALYTICS WITH EXCEL  ...   100      P
        8      BCS306A   OBJECT ORIENTED PROGRAMMING WITH JAVA  ...    62      P


        Example of the return value:
        list =
                    [
                        df,
                        [total, gpa, count of pass/fail, count of absent]
                    ]

        :param df:
        :return: list of DataFrame GPA, total marks, credits, result
        """
        if df is None:
            return []
        df = df.drop(columns=["Subject Name"], errors='ignore')

        internal_marks = list(df["Internal Marks"])
        external_marks = list(df["External Marks"])
        codes = list(df["Subject Code"])
        total_marks = list(df["Total"])
        result = list(df["Result"])
        print(result)

        for i in range(len(internal_marks)):
            internal_marks[i] = int(internal_marks[i])
            external_marks[i] = int(external_marks[i])
            total_marks[i] = int(total_marks[i])

        grade = []
        for i in range(len(result)):
            if result[i] != "F" and result[i] != "A":
                if int(total_marks[i]) >= 90:
                    grade.append(10)
                elif int(total_marks[i]) >= 80:
                    grade.append(9)
                elif int(total_marks[i]) >= 70:
                    grade.append(8)
                elif int(total_marks[i]) >= 60:
                    grade.append(7)
                elif int(total_marks[i]) >= 50:
                    grade.append(6)
                elif int(total_marks[i]) >= 40:
                    grade.append(5)
            elif result[i] == "F":
                grade.append(0)
            else:
                grade.append(-1)

        total_credits = 0
        credit = []
        obtained = []
        for i in range(len(result)):
            credit.append(subject_data.get(codes[i].strip(), {}).get("Credits", 0))
            # print(credits[i])
            # print(grade[i])
            if grade[i] == -1:
                obtained.append("A")
            elif grade[i] == 0:
                    obtained.append(0)

            else:
                obtained.append(grade[i] * credit[i])
            total_credits += subject_data.get(codes[i].strip(), {}).get("Credits", 0)


        print(len(grade), len(credit),len(obtained))
        df["Grade Points"] = grade
        df["Credits"] = credit
        df["Credits Obtained"] = obtained

        print("I'm here inside extract")
        if result.count("A") > 0 or result.count("F") > 0:
            gpa = "NAN"
        else:
            gpa = sum(obtained) / total_credits

        mainlist = [df, [sum(total_marks), gpa, result.count("P"),result.count("A")]]
        return mainlist


if __name__=="__main__":
    print("Running")
    e = Extract()
    data = e.get_dfs()
    pprint.pprint(data)
    for sem in range(1, 9):
        if data[sem] is not None:
            print(Extract.calculate(data[sem][0]))
    print("Done")