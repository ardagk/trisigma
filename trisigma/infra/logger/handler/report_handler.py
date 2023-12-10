import os
import logging
from datetime import datetime
import time
import json
import pickle

class ReportHandler(logging.Handler):
    def __init__(self, log_dir, agent_name):
        super().__init__()
        assert ' ' not in agent_name, 'agent_name cannot contain spaces'
        self.log_dir = log_dir
        self.agent_name = agent_name

    def emit(self, record):
        title = record.name
        filepath = self.get_filename(title)
        # Create the log directory if it doesn't exist
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        #format the log message
        msg = self.format(record)
        # Write the log message to the appropriate file
        with open(filepath, 'a') as file:
            file.write(f'{msg}\n')

    def format(self, record):
        try:
            data = 'json::' + json.dumps(record.msg)
        except:
            try:
                data = 'pickle::' + pickle.dumps(record.msg).hex()
            except:
                try:
                    data = 'str::' + str(record.msg)
                except Exception as e:
                    data = 'err::' + str(e)
        return f'{time.time()},\"{self.agent_name}\",{data}'

    def get_filename(self, title):
        return os.path.join(
            self.log_dir,
            title.split('.')[-1],
            f'{datetime.now().strftime("%Y-%m")}.log')
