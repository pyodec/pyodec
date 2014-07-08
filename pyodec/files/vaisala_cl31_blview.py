from decoders.core import FileDecoder
from decoders.messages.vaisalacl31 import cl31HisD
import numpy as np
import os
import time
import gzip

msgdecode = cl31HisD()

class VHisCL31D(FileDecoder):
    def on_line(self, line):
        if len(line) < 700:
            return None
        dat = msgdecode.decode(line)
        if dat:
            print dat[0],dat[1].shape
            return dat
        return False
    
    def decode_proc(self, filepath, yieldcount=1000):
        # open the file
        if not os.path.exists(filepath):
            print "NO SUCH FILE"
            return 
        gzfh = gzip.open(filepath,'r')
        for d in self.read_lines_gen(yieldcount, gzfh):
            yield d
        gzfh.close()

decoder = VHisCL31D(inherit=msgdecode)