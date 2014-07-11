"""
Pyodec root functionality
"""
import importlib

def decode(source, decoder, *args, **kwargs):
    """
    import and execute a file or string decoder on a certain class
    """
    print "importing", decoder
    decoder = importlib.import_module("."+decoder,'pyodec.files')
    return decoder.decoder.decode(source, *args, **kwargs)




def detect(source):
    """
    **Currently non-functional**
    
    run every decoder we have on some amount of the source file, 
    and return every decoder identifier which successfully read data from the chunk.
    """
    pass

def download(decoder):
    """
    **NON FUNCTIONAL**
    
    Download a decoder and install it on the local ``Pyodec`` installation
    """
