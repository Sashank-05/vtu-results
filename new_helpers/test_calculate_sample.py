import pandas as pd
from new_helpers.extract import Extract

# Create a DataFrame similar to the log entry with 9 subjects
data = {
    'Subject Code': ['BCS501', 'BCS502', 'BCS503', 'BAIL504', 'BCD586', 'BRMK557', 'BCS508', 'BNSK559', 'BAD515B'],
    'Subject Name': ['']*9,
    'Internal Marks': [40, 46, 41, 42, 95, 47, 45, 92, 40],
    'External Marks': [0]*9,
    'Total': [40, 46, 41, 42, 95, 47, 45, 92, 40],
    'Result': ['P','P','P','P','P','P','P','P','P'],
    'Announced / Updated on': ['']*9
}

# drop the last column as extract.calculate drops it too
df = pd.DataFrame(data)
df = df.drop(columns=['Announced / Updated on'])

res = Extract.calculate(df)
print(res[1])
print(res[0])

