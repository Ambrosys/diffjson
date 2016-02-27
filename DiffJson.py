
""" diff JSON objects """

from __future__ import print_function

__date__ = "2016-02-26"
__author__ = "Fabian Sandoval Saldias"
__email__ = "fabianvss@gmail.com"

import json
import copy
from collections import OrderedDict
import sys
import contextlib

"""
Note: JSON files are loaded with OrderedDict when supported (Python >= 2.7).

Two examples resulting in the following output (but colored).
    Output (when initialized with OrderedDict instead of regular dict):
        * a.x: 1 <> 2
        < a.y: true
        > b: null
    Initialization (with regular dict for simplicity in this example):
        diffJson = DiffJson( {'a':{'x':1,'y':True}}, {'a':{'x':2},'b':None} )
        diffJson.colored = True
    Option 1: Simple use case:
        diffJson.printDiff( 4 )
    Option 2: With a user defined printer:
        def diffPrinter( item ):
            diffPrinter.result.append( item )
        diffPrinter.result = []
        diffJson( diffPrinter )
        print( '    ' + '\n    '.join( diffPrinter.result ) )
    The API supports to change furthermore:
        - how to print modified values via property modifiedValueFormatter
        - the prefixes via setPrefixes()
        - the colors used via setColors()
"""

class DiffJson(object):
    
    def __init__( self, json1, json2 ):
        self._json1 = json1
        self._json2 = json2
        self._colored = False
        self._modifiedValueFormatter = lambda v1, v2: v1 + ' > ' + v2
        self._prefix_added    = '> '
        self._prefix_removed  = '< '
        self._prefix_modified = '~ '
        self._color_added    = '\033[92m' # Green
        self._color_removed  = '\033[91m' # Red
        self._color_modified = '\033[94m' # Blue
        self.__color_end = '\033[0m' # Default shell color
        
    @classmethod
    def fromPaths( cls, path1, path2 ):
        with contextlib.nested( open( path1, 'r' ), open( path2, 'r' ) ) as (file1, file2):
            return cls.fromFiles( file1, file2 )
        
    @classmethod
    def fromFiles( cls, file1, file2 ):
        if sys.version_info >= (2, 7):
            json1 = json.load( file1, object_pairs_hook=OrderedDict )
            json2 = json.load( file2, object_pairs_hook=OrderedDict )
        else:
            json1 = json.load( file1 )
            json2 = json.load( file2 )
        return cls( json1, json2 )
        
    def __call__( self, printer ):
        self.__printer = printer
        self.__diff()
        
    def printDiff( self, indentation = 0 ):
        self( lambda item: print( ' ' * indentation + item ) )
        
    @property
    def colored( self ):
        return self._colored
        
    @colored.setter
    def colored( self, value ):
        self._colored = value
        
    @property
    def modifiedValueFormatter( self ):
        return self._modifiedValueFormatter
    
    @modifiedValueFormatter.setter
    def modifiedValueFormatter( self, value ):
        self._modifiedValueFormatter = value
    
    def setPrefixes( self, added, removed, modified ):
        self._prefix_added = added
        self._prefix_removed = removed
        self._prefix_modified = modified
        
    def setColors( self, added, removed, modified ):
        self._color_added = added
        self._color_removed = removed
        self._color_modified = modified
        
    @property
    def prefix_added( self ):
        return self._prefix_added
        
    @property
    def prefix_removed( self ):
        return self._prefix_removed
        
    @property
    def prefix_modified( self ):
        return self._prefix_modified
        
    @property
    def color_added( self ):
        return self._color_added if self._colored else ''
        
    @property
    def color_removed( self ):
        return self._color_removed if self._colored else ''
        
    @property
    def color_modified( self ):
        return self._color_modified if self._colored else ''
        
    @property
    def color_end( self ):
        return self.__color_end if self._colored else ''
        
    def _coloredKey( self, path, key, color ):
        if isinstance( key, int ):
            return path + color + '[' + str(key) + ']' + self.color_end
        else:
            if( path == '' ):
                return color + key + self.color_end
            else:
                return path + '.' + color + key + self.color_end
    
    def _combinePath( self, path, key ):
        if isinstance( key, int ):
            return path + '[' + str(key) + ']'
        else:
            if( path == '' ):
                return key
            else:
                return path + '.' + key
    
    def _prettyValue( self, value ):
        if isinstance( value, dict ) or isinstance( value, list ):
            return json.dumps( value, sort_keys = sys.version_info < (2, 7) )
        elif isinstance( value, bool ):
            return 'true' if value else 'false'
        elif value is None:
            return 'null'
        elif isinstance( value, int ) or isinstance( value, float ):
            return str( value )
        else:
            return '"' + value + '"'

    def __diff( self ):
        self.__diffDict( '', self._json1, self._json2 )
    
    def __diffDict( self, path, original, modified ):
        remaining = copy.deepcopy( modified )
        for key, value in original.iteritems():
            if key in modified:
                self.__diffValue( path, key, value, modified[key] )
                del remaining[key]
            else:
                self.__printer( self.prefix_removed + self._coloredKey( path, key, self.color_removed ) + ': ' +
                    self._prettyValue( value )
                    )
        for key, value in remaining.iteritems():
            self.__printer( self.prefix_added + self._coloredKey( path, key, self.color_added ) + ': ' +
                self._prettyValue( value )
                )
    
    def __diffList( self, path, original, modified ):
        for key, value in enumerate( original ):
            if key < len(modified):
                self.__diffValue( path, key, value, modified[key] )
            else:
                self.__printer( self.prefix_removed + self._coloredKey( path, key, self.color_removed ) + ': ' +
                    self._prettyValue( value )
                    )
        for key, value in enumerate( modified[len(original):] ):
            self.__printer( self.prefix_added + self._coloredKey( path, key + len(original), self.color_added ) + ': ' +
                self._prettyValue( value )
                )
    
    def __diffValue( self, path, key, original, modified ):
        if original != modified:
            if isinstance( original, dict ) and isinstance( modified, dict ):
                self.__diffDict( self._combinePath( path, key ), original, modified )
            elif isinstance( original, list ) and isinstance( modified, list ):
                self.__diffList( self._combinePath( path, key ), original, modified )
            else:
                self.__printer( self.prefix_modified + self._coloredKey( path, key, self.color_modified ) + ': ' +
                    self.modifiedValueFormatter(
                        self.color_removed + self._prettyValue( original ) + self.color_end,
                        self.color_added + self._prettyValue( modified ) + self.color_end
                        )
                    )
