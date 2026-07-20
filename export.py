import communication as comms

def send(text):
    text = text + "\nM400"
    append(text)
    if comms.sendSerial:
        sendGcode(text)

def append(text):
    codeFile = comms.codeFile

    codeFile.write(f"{text}\n")

def sendGcode(text):
    text = text.strip()  # Strip all EOL characters for streaming

    for line in text.splitlines():
        if (line.isspace() == False and len(line) > 0 and line.lstrip()[0] != ";"):
            line = line + "\n"
            comms.s.write(line.encode())  # Send g-code block
            response = comms.s.readline().decode().strip()
            while not response.startswith("ok") and response != "":
                response = comms.s.readline().decode().strip()