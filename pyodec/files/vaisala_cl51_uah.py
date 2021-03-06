from pyodec.core import FileDecoder
from pyodec.messages.vaisalacl51 import decoder as msgdecode
import numpy as np
import os
import time
import gzip

"""
UAH CL-51 format... funky, is all i'll say
"""

import os

os.environ['TZ']='UTC'
time.tzset()

class UAHcl51D(FileDecoder):
    def on_chunk(self, message):
        # this is an end-spliced message, so we will get the timestamp
        data = msgdecode.decode(message)
        if data is False:
            return None
        return data
    
    def decode_proc(self, filepath, yieldcount=1000):
        # open the file
        fil = self.open_ascii(filepath)
        if fil is False:
            print "File not found"
            return
        for d in self.read_chunks_gen(yieldcount, fil,end='$'):
            yield d
        fil.close()

decoder = UAHcl51D(inherit=msgdecode)