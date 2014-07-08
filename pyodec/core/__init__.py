import gzip
import os
import traceback
from numpy import array

class Decoder(object):
    vars = False
    fixed_vars = False
    inherit = False
    state = {'identifier':False,
            'index':False,
            } # some unique identifier for the current state of the return
    def __init__(self, vars=False, inherit=False, fixed_vars=False):
        """
        create a MessageDecoder object, which has methods for opening, and looping
        through files. The _line_read method and the _chunk_read methods
        should be altered for a specific reader.
        
        The initialization will add information about the variables, and their
        shapes which are returned by any specific decoder.
        
        Variable dictionary returns the maximum shape, and name of the
        variables which will be returned by the decoder (per ob, it will
        return an array of these arrays)
        """
        # this attribute indicates if the decoder will produce data for multiple stations
        # if yes, then there is a specific format to use (and a special format for get_dtype)
        # those decoders also have the op
        self.station_collection=False
        if inherit:
            self.vars = inherit.vars
            self.fixed_vars = inherit.fixed_vars
            #inheritance be darned
        if self.inherit:
            # internally inherit a metadat set
            self.vars = self.inherit.vars
            self.fixed_vars = self.inherit.fixed_vars
        # or, on init, you can further redefine what the variables are.
        if vars:
            self.vars = vars
        if fixed_vars:
            self.fixed_vars = fixed_vars
        else:
            self.fixed_vars = FixedVariableList()
        # then, at the end, if vars still has not been set, then we sortof fail.
        # though this sadly still initialized the object.
        if self.vars is False:
            # they never defined vars anywhere, so, fail
            raise IOError("You need to pass variable information to this!")
            
    def varpos(self, varname):
        """
        return the index of the variable with the name varname
        """
        return self.vars.get_index(varname)
    def getvars(self, stnid=False):
        if stnid and type(self.vars) == dict:
            return self.vars[stnid].getvars()
        return self.vars.getvars()
    def get_fixed_vars(self, stnid=False):
        if stnid and type(self.fixed_vars) == dict:
            return self.fixed_vars[stnid].getvars()
        return self.fixed_vars.getvars()
    def get_dtype(self, stnid=False):
        """
        Get a numpy-recarray-compliant datatype statement which can be 
        used to create a recarray from any single observation.
        """
        if stnid and type(self.vars) == dict:
            return self.vars[stnid].tables_desc()
        return self.vars.tables_desc()

class FileDecoder(Decoder):
    """
    The inheritable class for a decoder of files.
    """
    def decode(self, filepath, generator=False, limit=1000, **kwargs):
        """
        run the contained decode_proc as either a generator or a procedural decoder. 
        If run as a generator, generator=True.
        """
        if generator:
            # offload directly to the generator
            return self.decode_proc(filepath, limit, **kwargs)
        else:
            # accumulate the data, since decode_proc is always a generator!
            data = []
            for d in self.decode_proc(filepath, limit, **kwargs):
                data+=d
            return d
    def _line_read(self, gfhandle):
        """
        This method lets you define the behavior for reading every line
        """
        for line in gfhandle:
            if line[:2] == '::': continue
            yield line
            
    def _chunk_read(self, gfhandle, begin=False, end=False):
        """
        this method lets you define the behavior for reading the file by chunks
        (which actually simply redefines the _line_read for chunking)
        """
        # NOTE this assumes lines are strings...
        MAX_CHUNK_LEN = 200
        chunk = ['']*MAX_CHUNK_LEN
        chunk_linenum = 0
        for line in gfhandle:
            if line[:2] == '::': continue
            if begin is False or chunk_linenum > 0 or begin in line:
                if end is False and begin in line:
                    # yield the chunk now, then begin again
                    data = ''.join(chunk)
                    if not data == '':
                        yield data
                    chunk_linenum = 0
                    chunk = ['']*MAX_CHUNK_LEN
                # then we are in a chunk
                chunk[chunk_linenum] = line
                chunk_linenum+=1
                if end and end in line:
                    yield ''.join(chunk)
                    # and reset the values
                    chunk_linenum=0
                    chunk = ['']*MAX_CHUNK_LEN
        endstr = ''.join(chunk)
        if endstr:
            yield endstr
    
    def read_lines(self, yieldcount, gfhandle):
        """
        Read the file, and yield the # of obs as a generator
        """
        data = []
        try:
            for line in self._line_read(gfhandle):
                ob = self.on_line(line)
                if ob:
                    # if ob data was retunred for this instance, then save it
                    data.append(ob)
                    if len(data) >= yieldcount:
                        yield data
                        data = []
        except KeyboardInterrupt:
            exit()
        except:
            print "COULD NOT READ FILE"
            traceback.print_exc()
            return
        # yield remaining obs
        yield data

    
    def read_chunks(self, yieldcount, gfhandle, begin=False, end=False):
        """
        generator form of chunk reading
        """
        data = []
        try:
            for chunk in self._chunk_read(gfhandle, begin, end):
                ob = self.on_chunk(chunk)
                if ob:
                    data.append(ob)
                    if len(data) >= yieldcount:
                        yield data
                        data = []
        except KeyboardInterrupt:
            exit()
        except:
            print "COULD NOT READ FILE"
            traceback.print_exc()
            return
        # yield remaining obs
        yield data
    
    @classmethod
    def open_ascii(cls, filepath):
        if not os.path.exists(filepath):
            raise NameError('File Not Found')
        if os.path.splitext(filepath)[1] == '.gz':
            return gzip.open(filepath,'r')
        else:
            return open(filepath,'r')

    _throw_updates = False
    def yield_update(self, update):
        """
        A reading process can throw updates if it wishes. The
        default self._throw_updates must be set to true.
        """
        if self._throw_updates:
            return {'UPDATE':update}
        return False
    def allow_updates(self):
        self._throw_updates = True
        
    def on_chunk(self, chunk):
        """
        return a tuple from an observation -- defined by the specific decoder.
        return False if the ob should be skipped
        """
        return 'undefined function'
    
    def on_line(self, line):
        """
        return a tuple whose indices correspond to those of varlist.
        return False if the ob should be skipped
        """
        return 'undefined function'
    def decode_chunks(self, filepath, limit, begin=None, end=None):
        """
        A "precompiled" generator-based decoder, to allow you to skip
        having to write the standard lines.
        """
        if os.path.exists(filepath):
            with self.open_ascii(filepath) as fil:
                for data in self.read_chunks(limit, filehandle, end=end, begin=begin):
                    yield data
    def decode_lines(self, filepath, limit):
        """
        A precompiled generator-based decoder allowing line-decoding without having
        to write the standard modules - if the default options are all that are needed.
        """
        if os.path.exists(filepath):
            with self.open_ascii(filepath) as fil:
                for data in self.read_lines(limit, filehandle):
                    yield data
    def decode_proc(self, filepath, limit, **kwargs):
        """
        this should be a standardized function - defined by the decoder
        which takes a file path, and opens it, and calls read_lines or read_chunks
        and then returns the data those two functions produce.

        Alternatively, you can not decode it, and use the default. But, it really won't
        work for most applications. Sorry.
        """
        if self.on_chunk('') != 'undefined':
            func = self.on_chunk
        else:
            func = self.on_line
        with self.open_ascii(filepath) as fil:
            for data in func(limit, fil, **kwargs):
                yield data
 

class MessageDecoder(Decoder):
    """
    Just a wrapper for the decoder class, because message decoders can (and should)
    contain a varlist just as the main decoders
    """
    def decode(self, message):
        """
        the decode method should be refactored, and used to decode a string message
        """
        pass    
    
    
class VariableList(object):
    """
    the requrements of the varaible list are somewhat strict, it must provide information
    regarding the names of the variables, their ranges, data conversions and units. 
    """
    def __init__(self, ):
        self.varnames   = []
        self.longnames  = []
        self.dtypes     = []
        self.shapes     = []
        self.offsets    = []
        self.scales     = []
        self.units      = []
        self.mins       = []
        self.maxs       = []
        self.indices    = {}
    
    def addvar(self, name, longname, dtype, shape, unit, index=None, scale=1, offset=0, mn=0, mx=1):
        """
        Add a variable to the variable list. 
        """
        if index == None:
            self._append(name,longname,dtype,shape,unit,scale,offset,mn,mx)
        else:
            # they specified an index. 
            if len(self.varnames) == index:
                # then this is a simple append operation
                self._append(name,longname,dtype,shape,unit,scale,offset,mn,mx)
            elif index < len(self.varnames):
                # overwrite
                self._overwrite(index, name, longname, dtype, 
                                shape, unit, scale, offset, 
                                mn, mx)
            else:
                # they are writing one beyoned where we are currently,
                # so we should add null values until we can append
                while len(self.varnames) < index:
                    self._append(None,None,None,None,None,None,None,None,None)
                self._append(name,longname,dtype,shape,unit,scale,offset,mn,mx)
                
    def _append(self, name, longname, dtype, shape, unit, scale, offset, mn, mx):
        """
        simply append the values
        """
        self.varnames.append(name)
        self.longnames.append(longname)
        self.dtypes.append(dtype)
        self.shapes.append(shape)
        self.scales.append(scale)
        self.offsets.append(offset)
        self.units.append(unit)
        self.mins.append(mn)
        self.maxs.append(mx)
        self.indices[name] = len(self.varnames)-1
        
    def _overwrite(self, index, name, longname, dtype, shape,
                   unit, scale, offset, mn, mx):
        """
        overwrite a certain index
        """
        self.varnames[index] = name
        self.longnames[index] = longname
        self.dtypes[index] = dtype
        self.shapes[index] = shape
        self.scales[index] = scale
        self.offsets[index] = offset
        self.units[index] = unit
        self.mins[index] = mn
        self.maxs[index] = mx
        self.indiecs[name] = index
    
    def __add__(self, additional):
        """
        you can say vars1+vars2 = vars3
        """
        new = VariableList()
        new.varnames = self.varnames + additional.varnames
        new.longnames = self.longnames + additional.longnames
        new.dtypes = self.dtypes + additional.dtypes
        new.shapes = self.shapes + additional.shapes
        new.scales = self.scales + additional.scales
        new.offsets = self.offsets + additional.offsets
        new.units = self.units + additional.units
        new.mins = self.mins + additional.mins
        new.maxs = self.maxs + additional.maxs
        for k in range(len(new.varnames)):
            new.indices[new.varnames[k]] = k
        return new
    
    def __repr__(self):
        """
        print representation of this variable
        """
        rstr = "VariableList Object with {} Values\n".format(len(self.varnames))
        i=0
        for var in self.varnames:
            rstr+="{:<20s}{:<20}{:<20}\n".format(var, self.dtypes[i],self.shapes[i])
            i+=1
        return rstr[:-1]
    
    def __len__(self):
        """
        the 'len()' function
        """
        return len(self.varnames)
    
    def getvar(self, varname):
        # lazy function for grabbing the info about a specific variable
        i=0
        for v in self.varnames:
            if varname==v:
                break
            i+=1
        return self.getvar_by_id(i)
    
    def getvar_by_id(self, i):
        if i >= len(self.varnames):
            # bad index
            return
        return {'name':self.varnames[i],
                'longname':self.longnames[i],
                'dtype':self.dtypes[i],
                'shape':self.shapes[i],
                'scale':self.scales[i],
                'offset':self.offsets[i],
                'unit':self.units[i],
                'min':self.mins[i],
                'max':self.maxs[i] }
    
    def getvars(self, ):
        data = []
        for i in range(len(self.varnames)):
            data.append(self.getvar_by_id(i))
        return data
    
    def get_index(self, varname):
        """
        return the index of the variable with the name 'varname'
        """
        if varname in self.indices:
            return self.indices[varname]
        else:
            raise ValueError('Variable {} not found'.format(varname))
            
    def tables_desc(self):
        """
        DEPRECATED: alias for self.dtype()
        """
        return self.dtype()
    
    def dtype(self):
        """
        This utility will produce the numpy recarray dtype entry
        for the pytable which will hold the data contained within.
        
        This description could be used to create a recarray of the returned data.
        
        To insert into pytables as a description, create the array with
        np.array([],dtype=decoder.tables_desc())
        """
        dtype = []
        i=0
        for v in self.varnames:
            if self.shapes[i]:
                dtype.append( (v,self.dtypes[i],self.shapes[i]) )
            else:
                dtype.append( (v,self.dtypes[i]) )
            i+=1
        return dtype
    
class FixedVariableList(object):
    """
    Similar to a variable list, but much simpler, with fewer functions
    """
    def __init__(self, ):
        self.names  = []
        self.units  = []
        self.data   = []
    def addvar(self, name, unit, dtype, data):
        self.names.append(name)
        self.units.append(unit)
        self.data.append(array(data,dtype=dtype))
        # data is a recarray
    def getvars(self, ):
        data=[]
        for i in range(len(self.names)):
            data.append({
                'name':self.names[i],
                'unit':self.units[i],
                'data':self.data[i]
                })
        return data


    

    
    
    
    
