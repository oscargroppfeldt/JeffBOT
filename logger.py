from datetime import datetime

class Logger:
    def __init__(self, log_file = ""):

        self.log_file = log_file

    def initialize(self, file_name = "log"):
        self.log_file = file_name
        file = open(f"{file_name}.log", "w")
        file.write(f"___Log created at {str(datetime.now())}___\n")
        file.close()

    def init(self, file_name = "log"):
        self.log_file = file_name
        try:
            with open(f"{file_name}.log", 'x') as file:
                file.write(f"\t___Log created at {str(datetime.now())}___")
        except FileExistsError:
            with open(f"{file_name}.log", 'a') as file:
                file.write(f"\n\t___Log continued at {str(datetime.now())}___")

    def log(self, msg):
        with open(f"{self.log_file}.log",'a') as file:
            file.write(f"{datetime.now()}: {msg}\n")

