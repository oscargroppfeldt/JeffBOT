import datetime

class Logger:
    def __init__(self, log_name, log_file = ""):
        self.log_name = log_name
        self.log_file = log_file
    
    def initialize(self, file_name = "log"):
        file = open(f"{file_name}.log", "w")
        file.write(f"___Log created at {datetime.datetime}___\n")
        file.close()

    def log(self, msg):
        with open(self.log_file) as file:
            file.write(f"{datetime.datetime}: {msg}\n")
        

    