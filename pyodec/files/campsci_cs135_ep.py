from pyodec.core import FileDecoder, VariableList
from pyodec.messages.campscics135 import decoder as msgdecode
import numpy as np
import os
import time
import gzip

"""
Campbell Scienfitic CS-135 with message 006 and epoch timestamps
"""
class Epcs135D(FileDecoder):
    vars = VariableList()
    vars.addvar('DATTIM','Observation time',int,1,'seconds since 1970-01-01 00:00 UTC') 
    vars += msgdecode.vars
    fixed_vars = msgdecode.fixed_vars
    
    def on_chunk(self, message):
        """
        Read a chunk of data from the file, the chunk being spliced from read_chunks.
        """
        # this is an end-spliced message, so we will get the timestamp
        ob = message.split(unichr(001))
        try:
            tmstr = ob[0].strip().split()[-1]
            # don't add extra newlines after the time string if you want to be happy
            otime = float(tmstr)
        except:
            return False
        try:
            data = msgdecode.decode(ob[1])
        except:
            # there was something ugly in this data... serial hiccups.
            data=False
        if data is False:
            return None
        output = [otime]+data
        return output
    
    def decode_proc(self, filepath, yieldcount=1000, **kwargs):
        # open the file
        #return self.read_chunks(yieldcount, self.open_ascii(filepath), end=unichr(004))
        # problem with above: who closes the file handle??
        with self.open_ascii(filepath) as filehandle:
            for d in self.read_chunks(yieldcount, filehandle, end=unichr(004)):
                yield d
        

decoder = Epcs135D()