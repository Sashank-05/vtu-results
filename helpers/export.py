import os

import openpyxl

if os.getcwd().endswith('helpers'):
    import dbhandler
else:
    from helpers import dbhandler


class export:
    def __init__(self, table_name):
        self.table_name = table_name
        self.template = '../static/template.xlsx' if os.getcwd().endswith('helpers') else 'static/template.xlsx'
        self.dbhandler = dbhandler.DBHandler(
            db_path='../database.db' if os.getcwd().endswith('helpers') else 'database.db')

    def export_as_excel(self):
        x = os.system('copy template.xlsx ' + self.table_name + '.xlsx')
        wb = openpyxl.load_workbook(self.table_name + '.xlsx')
        sheet = wb.get_sheet_by_name('OverallResult')
        df = self.dbhandler.get_semester_marks(self.table_name[:6], self.table_name[-1])
        idx = 8
        for i in df:
            # print(df)
            # first line starts at 8
            i = list(i)[:2] + [int(x) for x in i[3:-2]] + list(i)[-2:]
            print(i)
            print(str(idx))
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

            idx += 1
        wb.save(self.table_name + '.xlsx')




if __name__ == '__main__':
    export('BI23CD_SEM_1').export_as_excel()
