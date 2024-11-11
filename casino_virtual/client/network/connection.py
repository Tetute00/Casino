"""Network connection handler"""

class Connection:
    def __init__(self, host="localhost", port=5000):
        self.host = host
        self.port = port

    def connect(self):
        """Establish connection to server"""
        pass