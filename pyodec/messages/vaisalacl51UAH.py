"""
Decoder for one type of CL51 message, I don't know which type though, it is pretty
wierd. This is the format of data from UAH.

Maybe someday we will see another station with this reporting format...
"""

from pyodec.core import MessageDecoder, VariableList, FixedVariableList
import calendar
import numpy as np
import time
import datetime

# this is a sneaky little trick I came up with *pat on back*
x = np.arange(1637)%17 # 1540 obs with 97 indices, with 16 obs per line :)

class VCl51UAHD(MessageDecoder):
    # Decode CL51 (UAH) ob sets - ends with an $
    def decode(self, message):
        if "$" in message:
            ls = message.strip().split('\n')[:-1]
            # remove the last line
        else:
            ls = message.strip().split("\n")
        # grab the time of the ob
        try:
            
            tm = calendar.timegm(datetime.datetime.strptime(ls[0],'%H:%M:%S %m/%d/%Y').timetuple())
            # and construct the obset, hopefully
            obset = [
                tm,
                ls[1], # cloud status line
                ls[2], # instrument status line
                np.fromstring(' '.join(ls[3:]),sep=' ')[x!=0],
                ]
        except:
            # can't read this ob
            print 'couldnt decode time',ls[0]
            return False
        
        return obset
        
V=VariableList()
V..addvar('DATTIM','seconds since 1970-01-01 00:00 UTC',int,1,'S') 
V.addvar('CLDSTATUS',str,50,'')
V.addvar('INSSTATUS',str,50,'')
V.addvar('BS','int32',(1540,),'W?')

FV = FixedVariableList()
FV.addvar('HEIGHT','m AGL',int,np.arange(1540)*9.7)

decoder=VCl51UAHD(vars=V,fixed_vars=FV)


if __name__ == '__main__':
    pass


