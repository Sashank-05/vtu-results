from helper import extract_table
import os 

l=os.listdir("pages")

for i in l:
    print(extract_table.extractor(fr"pages\{i}"))


