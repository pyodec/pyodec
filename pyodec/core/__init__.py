import gzip
import os
import traceback
from numpy import array

class Decoder(object):
    """
    The root decoer object, primarily controls and standardizes interaction
    between 
    """
    vars = None
    """
        Holds the decoder class' ``VariableList`` object. 
        
        VariableLists are a **class** attribute, which allows the developer to define the ``vars`` value without rewriting the ``__init__()`` method. Variables should be either a constant for all uses of the decoder, or a variable that changes in the process of decoding. Thus, this may limit the ability to execute multiple decoders in a thread.
    """
    fixed_vars = None
    """
    the location of the ``FixedVariableList`` object within a ``Decoder``
    """
    inherit = None
    """
        Predefine another ``Decoder`` descendant to inherit variables from on ``__init__()``
    """
    state = {'identifier':False,
            'index':False,
            } # some unique identifier for the current state of the return
    def __init__(self, vars=False, inherit=False, fixed_vars=False):
        """
        Create a MessageDecoder object, which has methods for opening, and looping
        through files. The _line_read method and the _chunk_read methods
        should be altered for a specific reader.
        
        The initialization will add information about the variables, and their
        shapes which are returned by any specific decoder.
        
        Variable dictionary returns the maximum shape, and name of the
        variables which will be returned by the decoder (per ob, it will
        return an array of these arrays)
        
        vars = 5
        
        fixed_vars = 10
        
        state = dict
        """
        # this attribute indicates if the decoder will produce data for multiple stations
        # if yes, then there is a specific format to use (and a special format for get_dtype)
        # those decoders also have the op
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
        Return the integer array index of the variable column named ``varname``. This value can be used in conjunction
        with a returned array of data to extract a single known column (if you do not wish to compile the data int a recarray)
        
        alias of :func:`VariableList.get_index()` for the ``Decoder`` object's contained ``VariableList`` object.
        """
        return self.vars.get_index(varname)
    def getvars(self, stnid=False):
        """
        Get all the variables in a list of dictionaries describing them.
        
        alias of :func:`VariableList.getvars()` for the ``Decoder`` object's contained ``VariableList`` object.
        """
        return self.vars.getvars()
    def get_fixed_vars(self, stnid=False):
        """
        Get all the variables in a list of dictionaries describing them and containing their data.
        
        alias of :func:`FixedVariableList.getvars()` for the ``Decoder`` object's contained ``FixedVariableList`` object.
        """
        return self.fixed_vars.getvars()
    def get_dtype(self, stnid=False):
        """
        Get a numpy-recarray-compliant datatype statement which can be 
        used to create a recarray from any single observation.
        """
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
    def __line_read(self, gfhandle):
        """
        This method lets you define the behavior for reading every line
        """
        for line in gfhandle:
            if line[:2] == '::': continue
            yield line
            
    def __chunk_read(self, gfhandle, begin=False, end=False):
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
    
    def read_lines(self, limit, gfhandle):
        """
        Handle reading a file line-by-line, throwing each received line in a file (split by ``for line in file:``) to the ``self.on_line`` string decoder.
        
        If ``self.on_line`` returns something falsey, then it is skipped, otherwise it is appended to a ``list``, and once the length of that list is equal to that of ``limit``, it is yielded to the decode_proc which called it, and thus to the decoding process.
        
        """
        data = []
        try:
            for line in self.__line_read(gfhandle):
                ob = self.on_line(line)
                if ob:
                    # if ob data was retunred for this instance, then save it
                    data.append(ob)
                    if len(data) >= limit:
                        #yield np.rec.fromrecords(data,dtype=self.get_dtype())
                        yield data
                        data = []
        except KeyboardInterrupt:
            exit()
        except:
            print "COULD NOT READ FILE"
            traceback.print_exc()
            return
        # yield remaining obs
        #yield np.rec.fromrecords(data,dtype=self.get_dtype())
        yield data

    
    def read_chunks(self, yieldcount, gfhandle, begin=False, end=False):
        """
        generator form of chunk reading
        """
        data = []
        try:
            for chunk in self.__chunk_read(gfhandle, begin, end):
                try:
                    ob = self.on_chunk(chunk)
                except:
                    traceback.print_exc()
                if ob:
                    data.append(ob)
                    if len(data) >= yieldcount:
                        #yield np.rec.fromrecords(data,dtype=self.get_dtype())
                        yield data
                        data = []
        except KeyboardInterrupt:
            exit()
        except:
            print "COULD NOT READ FILE"
            traceback.print_exc()
            return
        # yield remaining obs
        # yield np.rec.fromrecords(data,dtype=self.get_dtype())
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
    def decode_chunks(self, filepath, limit, begin=None, end=None, **kwargs):
        """
        A predefined version of the ``decode_proc`` function that can be used 
        for instances where decoding only requires opening the file and passing
        it to the ``self.read_chunks(...)`` method.
        
        .. code-block:: python

            class MyDecoder(FileDecoder):
                ...
                def decode_proc(self, path, limit=1000, *kwargs):
                    return self.decode_chunks(path, limit, begin=chr(2), **kwargs)
        """
        if os.path.exists(filepath):
            with self.open_ascii(filepath) as fil:
                for data in self.read_chunks(limit, filehandle, end=end, begin=begin):
                    yield data
                    
    def decode_lines(self, filepath, limit, **kwargs):
        """
        A precompiled generator-based decoder allowing line-decoding without having
        to write the standard modules - if the default options are all that are needed.
        
        .. code-block:: python

            class MyDecoder(FileDecoder):
                ...
                def decode_proc(self, *args, *kwargs):
                    return self.decode_lines(*args, **kwargs)
        
        """
        if os.path.exists(filepath):
            with self.open_ascii(filepath) as fil:
                for data in self.read_lines(limit, filehandle):
                    yield data
    def decode_proc(self, filepath, limit, **kwargs):
        """
        **mandatory developer defined function**
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
        
        args:
            name (str): short, space-free name which should be thought of the "column name" 
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
        """
            return a dictionary of values for a specific variable identified by the variable name given.
        """
        return self.getvar_by_id(self.get_index(varname))
    
    def getvar_by_id(self, i):
        """
            return a dictionary of values for a variable identified by index ``i``
        """
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
        """
        Return a list of dictionaries describing all the variables in the set.
        """
        data = []
        for i in range(len(self.varnames)):
            data.append(self.getvar_by_id(i))
        return data
    
    def get_index(self, varname):
        """
        return the index of the variable with the name ``varname``
        """
        if varname in self.indices:
            return self.indices[varname]
        else:
            raise ValueError('Variable {} not found'.format(varname))
            
    def tables_desc(self):
        """
        .. deprecated:: 0.0
            Use :func:`dtype()` instead.
        """
        return self.dtype()
    
    def dtype(self):
        """
        This utility will produce the numpy recarray dtype entry
        for the pytable which will hold the data contained within.
        
        This description could be used to create a recarray of the returned data.
        
        To insert into pytables as a description, create the array with
        
        .. code-block:: python
        
            np.array([],dtype=decoder.vars.dtype())
        
        """
        dtype = []
        i=0
        for v in self.varnames:
            if self.shapes[i]:
                dtype.append( (v, self.dtypes[i], self.shapes[i]) )
            else:
                dtype.append( (v, self.dtypes[i]) )
            i+=1
        return dtype
    
class FixedVariableList(object):
    """
        A holder for storing, manipluating and interacting with variables which are fixed with relation
        to the returned dataset. These inlude the AGL heights of a fixed-gate remote sensor, beam names,
        elevation angles, etc.
    """
    def __init__(self, ):
        """
            init
        """
        self.names  = []
        self.units  = []
        self.data   = []
    def addvar(self, name, unit, dtype, data):
        """
            Append a fixed variable to the set of variables. Provide a name, unit, data type and the value 
            of the fixed variable (an array of heights, angles, whatever)
            
            :todo: Remove dtype, add long-description
        """
        self.names.append(name)
        self.units.append(unit)
        self.data.append(array(data,dtype=dtype))
        # data is a recarray
    def getvars(self, ):
        """
            Get all the fixed variables from the set as a list of dictionaries with keys of 
            
            * ``name``
            * ``unit``
            * ``data``
        """
        data=[]
        for i in range(len(self.names)):
            data.append({
                'name':self.names[i],
                'unit':self.units[i],
                'data':self.data[i]
                })
        return data


    

    
    
    
    
