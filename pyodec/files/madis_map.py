"""
This is the first NetCDF-based decoder. This will produce any number of the
120+ stations within the MADIS Multi-Agency Profiler network... Many of these
variables are currently foreign to me...

This decoder is going to be much more sophistocated than previous attempts.
It will need to produce a dict of values in self.vars and self.fixed_vars,
which update automatically with the data format.....? That might actually
be unnecessary
"""
from decoders.core import FileDecoder, VariableList, FixedVariableList
from decoders.messages.vaisalacl31 import decoder as msgdecode
import numpy as np
import os
import time
import gzip
import scipy.io.netcdf
# and make that prettier
nc = scipy.io.netcdf.netcdf_file

class MapDecoder(FileDecoder):
    def decode(self, fpath):
        # each file contains only a single observation from a number of stations.
        # gather metadata and data for each station, and yield it as a dictionary
        # of the proper format.
        self.station_collection=True
        # define the variables as dictionaries
        self.vars = {}
        self.fixed_vars = {}
        with gzip.open(fpath,'r') as g:
            # and open the netcdf
            src = nc(g)
            i=0
            for stnid in map(''.join,src.variables[src.idVariables]):
                data = {}
                data['stnid'] = stnid
                data['loc'] = [src.variables['latitude'][i],
                               src.variables['longitude'][i],
                               src.variables['elevation'][i]]
                data['metacols'] = [
                    'STID',
                    'OWNER',
                    'PROVIDER',
                    'instrument_type',
                    'NETWORK',
                    'name',
                ]
                data['metavars'] = [
                    ''.join(stnid),
                    ''.join(src.variables['dataProvider'][i]),
                    'MADIS',
                    src.variables['stationType'][i], # some friggin number
                    'MAP',
                    '', # this is sad, but true
                    
                ]
                # now determine the dataset characteristics as best we can...
                self.vars[data['stnid']] = VariableList()
                self.fixed_vars[data['stnid']] = FixedVariableList()
                row = [src.variables[src.timeVariables][i]]
                # save some profile information
                row.append(src.variables['mixingLayer'][i])
                self.vars[data['stnid']].addvar('MixingLayer','float32',1,src.variables['mixingLayer'].units)
                # determine some scope information for this station
                levels = max(src.variables['numLevels'][i]) #DANGEROUS!!!!
                if levels == 0:
                    #um, no levels of data? goodbye.
                    i+=1
                    continue
                # grab the SNR - vertical beam
                row.append(src.variables['signalNoiseRatio'][i,2,:levels])
                self.vars[data['stnid']].addvar('SNR','float32',(levels,),'')
                beams = src.variables['numBeamsUsed'][i]
                rass = src.variables['numRASSModesUsed'][i]
                if True: #rass > 0:
                    # grab temperature?!
                    row.append(src.variables['temperature'][i,:levels])
                    self.vars[data['stnid']].addvar('TEMP','float32',(levels,),src.variables['temperature'].units)
                wind = src.variables['numWindModesUsed'][i]
                if True: #wind > 0:
                    row.append(src.variables['uComponent'][i,:levels])
                    self.vars[data['stnid']].addvar('U','float32',(levels,),src.variables['uComponent'].units)
                    row.append(src.variables['uStdDevComponent'][i,:levels])
                    self.vars[data['stnid']].addvar('UDEV','float32',(levels,),src.variables['uStdDevComponent'])
                    row.append(src.variables['vComponent'][i,:levels])
                    self.vars[data['stnid']].addvar('V','float32',(levels,),src.variables['vComponent'].units)
                    row.append(src.variables['vStdDevComponent'][i,:levels])
                    self.vars[data['stnid']].addvar('VDEV','float32',(levels,),src.variables['vStdDevComponent'])
                    row.append(src.variables['wComponent'][i,:levels])
                    self.vars[data['stnid']].addvar('W','float32',(levels,),src.variables['wComponent'].units)
                    row.append(src.variables['wStdDevComponent'][i,:levels])
                    self.vars[data['stnid']].addvar('WDEV','float32',(levels,),src.variables['wStdDevComponent'])
                data['data']=[tuple(row)]
                # save heights as A FIXED VAR
                #FIXME - this is more complicated than this... but I couldn't figure it out
                self.fixed_vars[data['stnid']].addvar('HEIGHT','mAGL','float32',src.variables['levels'][i][:levels])
                #else:
                #    for i in range(beams):
                #        self.fixed_vars[data['stnid']].addvar('HEIGHT{}'.format(i),src.variables['levels'].units,'float32',src.variables['levels'][i][:levels[i]])
                    
                yield data
                i+=1
                
                
    
decoder = MapDecoder(vars=True)
if __name__ == '__main__':
    c=0
    for stn in decoder.decode('/data/ASN/RAW/MMAP_201404/71fc2aa1d86a260e4d7891ecef506131.dat.gz'):
        ##print len(decoder.get_dtype(stn['stnid'])),
        c+=1
        print stn['stnid'], c, stn['metavars']
        #print np.array(stn['data'][0],dtype=decoder.get_dtype(stn['stnid']))
        #print decoder.get_fixed_vars(stn['stnid'])
