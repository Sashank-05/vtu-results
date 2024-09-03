import os
def convert(df, lis):
    emp=["","","","","","",""]
    c1=emp.insert(0,lis[2])
    c2=emp.insert(0,lis[3])
    df["Total Marks"] = c1
    df["GPA"] = c2
    print(df)


    directory = 'csv_files'
    file_path = os.path.join(directory, f'{lis[0]}.csv')
    os.makedirs(directory, exist_ok=True)

    df.to_csv(file_path, index=False)

