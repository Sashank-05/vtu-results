
def df_to_sql(df,lis:list):

    df = df.drop(columns=["Subject Name", "Grade Points", "Credits Obtained", "Result"], errors='ignore')
    internal_marks=list(df["Internal Marks"])
    external_marks=list(df["External Marks"])
    total_marks=list(df["Total"])
    other=lis
    
    return(internal_marks,external_marks,other)
    


def get_subject_code(df):
    subjects=[]

    for i in list(df["Subject Code"]):
        subjects.append(i+"_internal")
        subjects.append(i+"_external")
    subjects+=["Total","GPA","Result"]

    return(subjects)
