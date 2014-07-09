from pyodec.core import MessageDecoder, VariableList, FixedVariableList, FileDecoder
import numpy as np

"""
decode message 006 from a Campbell Scientific CS135
"""

class cs135Dm6(MessageDecoder):
    # set decoder parameters for this type of message.

    vars = VariableList()
    # line 1
    vars.addvar('INSTRID','Instrument self-identification character','str',1,'')
    vars.addvar('OPS','CS135 Operating System',str,1,'')
    vars.addvar('MSG','CS135 Message format number',str,3,'')
    # line 2
    vars.addvar('CLSTAT','Cloud detection status',str,1,'')
    vars.addvar('TRANS','CS135 window transmission',int,1,'%')
    vars.addvar('VVIS','Vertical visibility',int,1,'m or ft')
    vars.addvar('FIRST_CLOUD','Lowest cloud height',int,1,'m or ft')
    vars.addvar('SECOND_CLOUD','second cloud level height',int,1,'m or ft')
    vars.addvar('HIGHEST_SIG','Highest received bacskcatter signal',int,1,'m or ft')
    vars.addvar('THIRD_CLOUD','Lowest cloud height',int,1,'m or ft')
    vars.addvar('FOURTH_CLOUD','Lowest cloud height',int,1,'m or ft')
    vars.addvar('ALARMS','ALARMS and WARNINGS',bool,(48,),'boolean')
    # line 3
    for i in range(5):
        vars.addvar('COVERAGE_CLD{}'.format(i+1),
                    'Cloud coverage for layer {}'.format(i+1),int,1,'oktas')
        vars.addvar('CLDHT_'+str(i+1),
                    'Height of cloud level {} in 10s of m or 100s of ft'.format(i+1),
                    int,1,'10s of m or 100s of  ft')
    # line 4
    vars.addvar('SCALE','Scale Parameter',int,1,'%')
    vars.addvar('RESOLUTION','Backscatter profile resolution',int,1,'m')
    vars.addvar('LENGTH','Profile length (number of bins)',int,1,'')
    vars.addvar('PULSE_ENERGY','Laser pulse energy',int,1,'%')
    vars.addvar('LASERTEMP','Laser temperature',int,1,'C') # includes +/-
    vars.addvar('TILT','Total tilt angle',int,1,'degrees')
    vars.addvar('BACKGROUND_RAD','Background light at internal ADC',int,1,'mv',mn=0,mx=2500)
    vars.addvar('PULSEQ','Pulse quantitiy x 1000',int,1,'',mx=9999,mn=0)
    vars.addvar('RATE','Pulse rate',int,1,'MHz',mx=99,mn=0)
    vars.addvar('SUM','Sum of detected, normalized backscatter multiplied by scale*10^4',int,1,'srad^-1',mn=0,mx=999)
    for i in range(3):
        ist = str(i+1)
        vars.addvar('MLH'+ist,'Mixing layer height # '+ist,int,1,'m')
        vars.addvar('MLH_QUAL'+ist,'MLH Quality parameter for layer #'+ist,
                    str, 5, '')
    # line 5
    vars.addvar('BS','Attenuated, Normalized, Backscatter coefficient','float32',(2048,),'1/(m sr)')

    # for now we are going to assume height is fixed, and return it as such
    fixed_vars = FixedVariableList()
    fixed_vars.addvar('HEIGHT','m AGL','int',np.arange(2048)*5)
    
    def decode(self, message):
        OB_LENGTH = 2048 # appears tho be fixed in this format
        SCALING_FACTOR = 1.0e9 # also appears to be fixed
        'break the full ob text into it\'s constituent parts'
        p1 = message.split(unichr(2))
        p2 = p1[1].split(unichr(3))
        code = p1[0].strip()
        # ensure that this is a type 006 message.
        if code[-3:] != "006":
            raise IOError('Wrong Decoder')
        # grab the rest of the possible values
        ob = p2[0].strip()  # just contents between B and C
        # unused currently checksum = p2[1].strip()
        data = ob.split("\n")  # split into lines
        # the final line is the profile line
        prof = list(data[-1].strip())
        #grab status lines
        sl1 = data[0].strip().replace("/",'0').split()
        sl2 = data[1].strip().replace("/",'0').split()
        sl3 = data[2].strip().split()
        sl4 = data[3].strip().replace("/","0").split()
        # and decode them! This could be ugly
        # initialize the data row - start by grabbing useful information
        meters = sl1[6][0] # first flag 1=meters, 0=ft
        resolution= sl3[1]
        length = sl3[2]
        
        row = []
        row.append(code[2]) # self-ID
        row.append(code[3:6]) # operating system
        row.append(code[6:9]) # message number (006)
        # actual status variables
        row.append(sl1[0][0]) # message status
        row.append(sl1[1]) # transmission, %
        if sl1[0][0] == 5:
            # first value is vertical vis
            row.append(sl1[2]) # vertical vis
            row.append(0) # lowest cloud
        else:
            # first value is lowest cloud
            row.append(0) # vertical vis
            row.append(sl1[2]) # lowest cloud
        if sl1[0][0] == 5:
            row.append(0) # second cloud base
            row.append(sl1[3]) # highest signal received
        else:
            row.append(sl1[3]) # second cloud base
            row.append(0) # highest signal received
        row.append(sl1[4]) # third height
        row.append(sl1[5]) # fourth height
        # flags & alarms
        alarms = []
        for v in list(sl1[6]):
            val = '{:04b}'.format(int(v,16))
            alarms += list(val)
        row.append(alarms)
        #row += list(sl1[6]) # 12 flags
       
        ## LINE 2
        row += sl2 # cloud coverage/condition & heights (cover/height/cover/height 5 times)
        # line 3 - super awesome info line!!
        row += sl3
        # scale %, resolution, prof length, pulse energy %, laser temperature C,
        # tilt angle, background light MV, pulse quantity x 1000, sample rate MHz,
        # backscatter sum.
        
        # line 5 -- mixed layer height info
        row += sl4
        # first MLH height meters, quality of mlh, height of 2nd mlh, quality
        # of 2nd mlh, third height, third quality

        values = np.zeros(2048, dtype=np.float32)
        ky = 0
        for i in xrange(0, len(prof), 5):
            ven = prof[i:i + 5]
            values[ky] = twos_comp(int(ven, 16), 20)  # scaled to 100000sr/km (x1e9 sr/m)FYI
            ky += 1  # keep the key up to date
        # then the storage will be log10'd values
        values[values <= 0] = 1.
        row.append(np.log10(values / SCALING_FACTOR))
        return row

# I thanks Travc at stack overflow for this method of converting values
# See here: http://stackoverflow.com/questions/1604464/twos-complement-in-python
def twos_comp(val, bits):
    """compute the 2's compliment of int value val"""
    if((val & (1 << (bits - 1))) != 0):
        val = val - (1 << bits)
    return val

decoder = cs135Dm6()

