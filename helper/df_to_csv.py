def convert(df, lis):
    df["Total Marks"] = lis[2]
    df["GPA"] = lis[3]
    print(df)

    df.to_csv(fr'csv_files\{lis[0]}.csv')
