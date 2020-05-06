from datetime import datetime

class ConsoleLogger(applicationRunningQuiet):
    """Logs messages to console"""

    def show(text, display = False):
        if display:
            curr_time = datetime.now().strftime("%d %B %Y %I:%M:%S%p")
            print (curr_time + ": " + text)

    def critical(message):
        print(message, True)
    
    def log(message):
        print(message, not applicationRunningQuiet)

    def trace(message):
        print(message, not applicationRunningQuiet)

