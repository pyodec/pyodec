from pyodec.core import MessageDecoder, VariableList, FixedVariableList
import numpy as np
'''
DEPRECATED - THIS HAS BEEN MOVED INTO THE GENERIC CL-31 decoders!

decoder for Viasala-BL-view produced .his data files from a CL-31
'''
'''
    read a CL31 HIS file, which is just lines of encoded data,
    NO status information is provided with this data format.
'''
class cl31HisD(MessageDecoder):
    init_vars = VariableList()
    init_vars.addvar('DATTIM','seconds since 1970-01-01 00:00 UTC',int,1,'S') 
    init_vars.addvar('BS','Attenuated backscatter coefficient','float32',(480,),'1/(m sr)')

    init_fixed_vars = FixedVariableList()
    init_fixed_vars.addvar('HEIGHT','m AGL','int',np.arange(770)*10)

    def decode(self, message):
        if len(message) < 300:
            return False
        line = message.split(',')
        tm = int(line[1])
        line = line[-1].strip()
        data = np.zeros(480,dtype=np.float32)
        # and grab/decode the data line
        for i in xrange(0,len(line),5):
            ven = line[i:i+5]
            data[i/5] = twos_comp(int(ven,16),20)
        # set negative values to the minimum value of 1
        data[data<=0] = 1.
        # reverse the data! it comes out backwards
        data = data[::-1]
        data = np.log10(data) - 10 #??
        return [tm,data]
        
def twos_comp(val, bits):
    """compute the 2's compliment of int value val"""
    if((val & (1 << (bits - 1))) != 0):
        val = val - (1 << bits)
    return val


decoder = cl31HisD()