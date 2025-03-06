import openpyxl
import os
import shutil
import new_helpers.dbhandler as dbhandler
import pandas as pd


class export:
    def __init__(self, table_name):
        self.table_name = table_name
        self.template = 'static/template.xlsx'
        self.dbhandler = dbhandler.DBHandler(db_path='database.db')

    def export_as_excel(self):
        shutil.copy(self.template, self.table_name + '.xlsx')

        wb = openpyxl.load_workbook(self.table_name + '.xlsx')
        sheet = wb['OverallResult']

        df = self.dbhandler.get_semester_marks(self.table_name[:8],self.table_name[-1] )
        idx = 8

        for i in df:
            # Convert elements to integers where applicable and maintain the structure
            #i = list(i)[:2] + [int(x) for x in i[3:-2]] + list(i)[-2:]
            i = list(i)
            new_list = []

            for index in range(2):
                new_list.append(i[index])

            for index in range(3, len(i) - 2):
                try:
                    new_list.append(int(i[index]))
                except:
                    new_list.append(i[index])

            for index in range(len(i) - 2, len(i)):
                new_list.append(i[index])

            i = new_list
            print(str(idx))

            # Fill Excel sheet with extracted data
            sheet['B' + str(idx)] = i[0]
            sheet['C' + str(idx)] = i[1]

            sheet['E' + str(idx)] = i[2]
            sheet['F' + str(idx)] = i[3]

            sheet['N' + str(idx)] = i[4]
            sheet['O' + str(idx)] = i[5]

            sheet['W' + str(idx)] = i[6]
            sheet['X' + str(idx)] = i[7]

            sheet['AF' + str(idx)] = i[8]
            sheet['AG' + str(idx)] = i[9]

            sheet['AO' + str(idx)] = i[10]
            sheet['AP' + str(idx)] = i[11]

            sheet['AX' + str(idx)] = i[12]
            sheet['AY' + str(idx)] = i[13]

            sheet['BG' + str(idx)] = i[14]
            sheet['BH' + str(idx)] = i[15]

            sheet['BP' + str(idx)] = i[16]
            sheet['BQ' + str(idx)] = i[17]

            idx += 1  # Move to the next row

        wb.save(self.table_name + '.xlsx')


if __name__ == '__main__':
    export('X1BI23CD_SEM_2').export_as_excel()
