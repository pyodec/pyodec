from pyodec.core import MessageDecoder, VariableList, FixedVariableList
import numpy as np


class cl31Dm2(MessageDecoder):
    init_vars = VariableList()
    init_vars.addvar('BS','Attenuated Backscatter coefficient','float32',(770,),'1/(m sr)')
    init_vars.addvar('STATUS','CL-31 Status information','float32',(13,),'Null')

    # for now we are going to assume height is fixed, and return it as such
    init_fixed_vars = FixedVariableList()
    init_fixed_vars.addvar('HEIGHT','m AGL','int',np.arange(770)*10)
    
    def decode(self, message):
        OB_LENGTH = 770  # FIXME - the current return length is limited to 770
        SCALING_FACTOR = 1.0e9
        
        #break the full ob text into it's constituent parts
        p1 = message.split(unichr(002))
        p2 = p1[1].split(unichr(003))
        code = p1[0].strip()
        ob = p2[0].strip()  # just contents between B and C
        # unused currently checksum = p2[1].strip()
    
        data = ob.split("\n")  # split into lines
    
        #the last line of the profile should be the data line'
        prof = list(data[-1].strip()) # list of the characters
        #grab status lines'
        sl1 = data[0].strip()
        sl2 = data[-2].strip()  # I will skip any intermediate data lines...
    
        status = np.array([sl1[0].replace('/', '0'),
                        sl1[1].replace('A', '2').replace('W', '1')] +
                        sl1[2:-13].replace('/', '0').split() + sl2[:-14].split(),
                        dtype=np.float32)
        #status should have a length of 13... we shall see...'
        # determine height difference by reading the last digit of the code
        height_codes = [0, 10, 20, 5, 5]  # '0' is not a valid key, and will not happen
        data_lengths = [0, 770, 385, 1500, 770]
        #length between 770 and 1500'
        datLen = data_lengths[int(code[-1])]
        htMult = height_codes[int(code[-1])]
        values = np.zeros(datLen, dtype=np.float32)
        ky = 0
        for i in xrange(0, len(prof), 5):
    
            ven = prof[i:i + 5]
    
            values[ky] = twos_comp(int(ven, 16), 20)  # scaled to 100000sr/km (x1e9 sr/m)FYI
            ky += 1  # keep the key up to date
    
        # then the storage will be log10'd values
        values[values <= 0] = 1.
        out = (np.log10(values[:OB_LENGTH] / SCALING_FACTOR),status)
        return out

decoder = cl31Dm2() 


'''
decoder for Viasala-BL-view produced .his data files from a CL-31

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


# I thank Travc at stack overflow for this method of converting values
# See here: http://stackoverflow.com/questions/1604464/twos-complement-in-python
def twos_comp(val, bits):
    """compute the 2's compliment of int value val"""
    if((val & (1 << (bits - 1))) != 0):
        val = val - (1 << bits)
    return val
