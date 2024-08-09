from bs4 import BeautifulSoup
import pandas as pd

credit_4 = ["BMATS101", "BPHYS102"]
credit_3 = ["BPOPS103", "BESCK104B", "BETCK105H"]
credit_2 = []
credit_1 = ["BENGK106", "BKSKK107", "BIDTK158"]


def extractor(saved_html):
    with open(saved_html, "r", encoding="utf-8") as file:
        soup = BeautifulSoup(file, "lxml")

    rows = soup.find_all("div", class_="divTableRow")
    tables = pd.read_html(str(soup))

    table_data = []
    for row in rows:
        cells = row.find_all("div", class_="divTableCell")
        row_data = [cell.text.strip() for cell in cells]
        table_data.append(row_data)

    df_marks = pd.DataFrame(table_data[1:9], columns=table_data[0])

    return df_marks
