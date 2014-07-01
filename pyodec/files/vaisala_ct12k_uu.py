from decoders.core import FileDecoder
from decoders.messages.vaisalact12k import decoder as msgdecode
import numpy as np
import os
import time
import gzip

"""
U of Utah CT-12k: epoch times stored *before* the message
"""

class uuct12kD(FileDecoder):
    def on_chunk(self, message):
        # this is an end-spliced message, so we will get the timestamp
        ob = message.split(unichr(002))
        try:
            tmstr = ob[0].split()[-1]
            # don't add extra newlines after the time string if you want to be happy
            otime = float(tmstr)
        except:
            return False
        data = msgdecode.decode(ob[1])
        if data is False:
            return None
        output = (otime,data[0],data[1])
        return output
    
    def decode(self, filepath, yieldcount=1000):
        # open the file
        if not os.path.exists(filepath):
            print "NO SUCH FILE"
            return 
        gzfh = gzip.open(filepath,'r')
        for d in self.read_chunks_gen(yieldcount, gzfh,end=unichr(003)):
            yield d
        gzfh.close()

decoder = uuct12kD(inherit=msgdecode)