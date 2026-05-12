import generator as gen

def append(text, newline=True):
    codeFile = gen.codeFile

    codeFile.write(f"{text}")
    if newline:
        codeFile.write("\n")