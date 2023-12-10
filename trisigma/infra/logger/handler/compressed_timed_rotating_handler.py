import gzip
import logging
import logging.handlers
import os
import shutil

class CompressedTimedRotatingFileHandler(
        logging.handlers.TimedRotatingFileHandler):

    def namer(self, name):
        return name + '.gz'

    def rotator(self, source, dest):
        print(source.split('/')[-1],'\t', dest.split('/')[-1])
        with open(source, 'rb') as f_in:
            with gzip.open(dest, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out) #type: ignore
        os.remove(source)

