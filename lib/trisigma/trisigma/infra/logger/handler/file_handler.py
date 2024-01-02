import logging

class CustomFileHandler(logging.FileHandler):
    def __init__ (self, path):
        self.path = path
        super().__init__(path)
