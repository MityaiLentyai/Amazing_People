

def parse_output(file_name: str):

    with open(file_name, "a") as file:
        file.write("Now the file has more content!\n")