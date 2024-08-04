import os

total = len(os.listdir("pages"))
wasted = 0
for i in os.listdir("pages"):
    with open("pages/" + i, encoding="utf8") as f:
        print(f.read(1))
        if f.read(1) == "":
            wasted += 1

print(wasted, total)
