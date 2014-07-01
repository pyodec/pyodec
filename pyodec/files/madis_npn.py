"""
This decoder is similar to the MADIS MAP network decoder, except it produces
data for stations in the NOAA profiler network. Many things are the same though.
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

class NpnDecoder(FileDecoder):
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
            # loop through the stations we found
            for stnid in map(''.join,src.variables[src.idVariables]):
                data = {}
                data['stnid'] = stnid
                data['loc'] = [src.variables['staLat'][i],
                               src.variables['staLon'][i],
                               src.variables['staElev'][i]]
                data['metacols'] = [
                    'STID',
                    'OWNER',
                    'PROVIDER',
                    'instrument_type',
                    'NETWORK',
                    'name',
                    'VARS',
                ]
                data['metavars'] = [
                    ''.join(stnid),
                    'NOAA',
                    'MADIS',
                    'Radar Wind Profiler', # NNP don't really diffferentiate between units
                    'NPN',
                    '', # this is sad, but true
                    [],
                    
                ]
                # now determine the dataset characteristics as best we can...
                self.vars[stnid] = VariableList()
                self.fixed_vars[stnid] = FixedVariableList()
                # and create the row object, starting with the
                row = [src.variables[src.timeVariables][i]]
                # determine some scope information for this station
                # grab the levels of data for this station. if the length is 0, then move on
                lvls = src.variables['levels'][i]
                if len(lvls[:]) == 0:
                    i+=1
                    continue
                self.fixed_vars[stnid].addvar('HEIGHT','mAGL','float32',lvls[:])
                self.fixed_vars[stnid].addvar('QCTESTS','','|S60',map(''.join,src.variables['QCT']))
                self.fixed_vars[stnid].addvar('ICTESTS','','|S72',map(''.join,src.variables['ICT']))
                self.fixed_vars[stnid].addvar('BEAMNAMES','','|S8', map(''.join,src.variables['beamNames']))
                for v in src.variables:
                    # loop through the variables - please let the variables be fixed!!!!
                    var = src.variables[v]
                    if not var.isrec:
                        # the variable is not record-based, so, move along
                        continue
                    # grab the actual data for this station of this variable
                    vardat = var[i]
                    vardtype = str(vardat.dtype)
                    # but, these datatypes are not really allowed by pytables, so fix
                    if "i" in vardtype:
                        vardtype='int'
                    elif 'f' in vardtype:
                        vardtype='float32'
                    varshp = var.shape[1:] # the first dim is the staion, so, not that
                    varunit = False;
                    try:
                        varunit  = var.units
                        varname = var.long_name
                    except AttributeError:
                        if varunit is False:
                            varunit = ''
                        varname = ''
                    data['metavars'][6].append((v,varname,varunit,varshp))
                    # record the variable
                    row.append(vardat)
                    self.vars[stnid].addvar(v,vardtype,varshp,varunit)
                data['data']=[tuple(row)]
                # save heights as A FIXED VAR
                #FIXME - this is more complicated than this... but I couldn't figure it out
                
                #else:
                #    for i in range(beams):
                #        self.fixed_vars[data['stnid']].addvar('HEIGHT{}'.format(i),src.variables['levels'].units,'float32',src.variables['levels'][i][:levels[i]])
                    
                yield data
                i+=1
                
                
    
decoder = NpnDecoder(vars=True)
if __name__ == '__main__':
    c=0
    for stn in decoder.decode('/data/ASN/RAW/MNPN_201404/a85ca80116c0d367564289b0b8b27e1e.dat.gz'):
        ##print len(decoder.get_dtype(stn['stnid'])),
        c+=1
        print np.array([],dtype=decoder.get_fixed_vars(stn['stnid'])).dtype
        print stn['stnid'], c,
        #print np.array(stn['data'][0],dtype=decoder.get_dtype(stn['stnid']))
        #print decoder.get_fixed_vars(stn['stnid'])
