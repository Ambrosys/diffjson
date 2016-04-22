# coding=UTF-8

from __future__ import print_function

""" diff JSON objects """

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
        ~ a.x: 1 > 2
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

    class Dye(object):

        def __init__( self ):
            self._colored = False
            self._c_added    = '\033[92m' # Green
            self._c_removed  = '\033[91m' # Red
            self._c_modified = '\033[94m' # Blue
            self.__c_end     = '\033[0m'  # Default shell color

        @property
        def colored( self ):
            return self._colored

        @colored.setter
        def colored( self, value ):
            self._colored = value

        def setColors( self, added, removed, modified ):
            self._c_added = added
            self._c_removed = removed
            self._c_modified = modified

        def added( self, text ): return self._coloredText( text, self._c_added )
        def removed( self, text ): return self._coloredText( text, self._c_removed )
        def modified( self, text ): return self._coloredText( text, self._c_modified )

        def _coloredText( self, text, color ):
            return color + text + self.__c_end if self.colored and sys.stdout.isatty() else text
    
    def __init__( self, json1, json2 ):
        self._json1 = json1
        self._json2 = json2
        self._dye = self.Dye()
        self._modifiedValueFormatter = lambda v1, v2: v1 + ' > ' + v2
        self._prefix_added    = '> '
        self._prefix_removed  = '< '
        self._prefix_modified = '~ '
        
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
    
    def select1( self, path, delimiter, deserializeOperator = None ):
        sub = DiffJson.getPath( self._json1, path, delimiter, deserializeOperator )
        if sub is not None:
            self._json1 = sub
            return True
        else:
            return False
    
    def select2( self, path, delimiter, deserializeOperator = None ):
        sub = DiffJson.getPath( self._json2, path, delimiter, deserializeOperator )
        if sub is not None:
            self._json2 = sub
            return True
        else:
            return False
        
    def __call__( self, printer ):
        self.__printer = printer
        self.__diff()
        
    def printDiff( self, indentation = 0 ):
        self( lambda item: print( ' ' * indentation + item ) )
        
    @property
    def colored( self ):
        return self._dye.colored
        
    @colored.setter
    def colored( self, value ):
        self._dye.colored = value
        
    @property
    def modifiedValueFormatter( self ):
        """
        @rtype: (str, str) -> str
        """
        return self._modifiedValueFormatter
    
    @modifiedValueFormatter.setter
    def modifiedValueFormatter( self, value ):
        self._modifiedValueFormatter = value
    
    def setPrefixes( self, added, removed, modified ):
        self._prefix_added = added
        self._prefix_removed = removed
        self._prefix_modified = modified
        
    def setColors( self, added, removed, modified ):
        self._dye.setColors( added, removed, modified )
        
    @property
    def prefix_added( self ):
        return self._prefix_added
        
    @property
    def prefix_removed( self ):
        return self._prefix_removed
        
    @property
    def prefix_modified( self ):
        return self._prefix_modified

    @staticmethod
    def getPath( jsonDictOrList, path, delimiter, deserializeOperator ):
        """
        @type deserializeOperator: basestring|None
        @param deserializeOperator: If not None, a path item with preceeding
            deserializeOperator will cause the string value getting deserialized
            into a json value. But only, if the path item is not an existing
            key. Because then, we assume, that the user do not want to
            deserialize but just navigate the key. If he intends to actually
            deserialize, he must give another deserializeOperator, that does not
            conflict with existing keys.
        """
        elem = jsonDictOrList
        try:
            for x in path.strip( delimiter ).split( delimiter ):
                deserializeValue = False
                if deserializeOperator is not None and isinstance( x, basestring ) and not x in elem and len(x) >= 1 and x[0] == deserializeOperator:
                    x = x[1:]
                    deserializeValue = True

                if isinstance( elem, dict ):
                    elem = elem[x]
                elif isinstance( elem, list ):
                    elem = elem[int(x)]

                if deserializeValue:
                    if sys.version_info >= (2, 7):
                        elem = json.loads( elem, object_pairs_hook=OrderedDict )
                    else:
                        elem = json.loads( elem )
        except (KeyError, IndexError):
            return None
        return elem
        
    def _coloredKey( self, path, key, dyer ):
        if isinstance( key, int ):
            return path + dyer( '[' + str(key) + ']' )
        else:
            if path == '':
                return dyer( key )
            else:
                return path + '.' + dyer( key )
    
    @staticmethod
    def _combinePath( path, key ):
        if isinstance( key, int ):
            return path + '[' + str(key) + ']'
        else:
            if path == '':
                return key
            else:
                return path + '.' + key

    @staticmethod
    def _prettyValue( value ):
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
        self.__diffValue( '', '', self._json1, self._json2 )
    
    def __diffDict( self, path, original, modified ):
        remaining = copy.deepcopy( modified )
        for key, value in original.iteritems():
            if key in modified:
                self.__diffValue( path, key, value, modified[key] )
                del remaining[key]
            else:
                self.__printer( self.prefix_removed + self._coloredKey( path, key, self._dye.removed ) + ': ' +
                    DiffJson._prettyValue( value )
                    )
        for key, value in remaining.iteritems():
            self.__printer( self.prefix_added + self._coloredKey( path, key, self._dye.added ) + ': ' +
                DiffJson._prettyValue( value )
                )
    
    def __diffList( self, path, original, modified ):
        for key, value in enumerate( original ):
            if key < len(modified):
                self.__diffValue( path, key, value, modified[key] )
            else:
                self.__printer( self.prefix_removed + self._coloredKey( path, key, self._dye.removed ) + ': ' +
                    DiffJson._prettyValue( value )
                    )
        for key, value in enumerate( modified[len(original):] ):
            self.__printer( self.prefix_added + self._coloredKey( path, key + len(original), self._dye.added ) + ': ' +
                DiffJson._prettyValue( value )
                )
    
    def __diffValue( self, path, key, original, modified ):
        if original != modified:
            if isinstance( original, dict ) and isinstance( modified, dict ):
                self.__diffDict( DiffJson._combinePath( path, key ), original, modified )
            elif isinstance( original, list ) and isinstance( modified, list ):
                self.__diffList( DiffJson._combinePath( path, key ), original, modified )
            else:
                value = self.modifiedValueFormatter(
                    self._dye.removed( DiffJson._prettyValue( original ) ),
                    self._dye.added( DiffJson._prettyValue( modified ) )
                    )
                self.__printer( self.prefix_modified + self._coloredKey( path, key, self._dye.modified ) + ': ' +
                    str( value )
                    )
