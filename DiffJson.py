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
import re

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
    You can walk the JSON before comparison with select1() and select2(). The
        keys have to be separated with the string defined by the property
        pathDelimiter. With the property useSquareBrackets you decide whether to
        use the array index syntax (that is, key[value] instead of key.value).
    To ignore specific paths (relative to the final root paths after the usages
        of select1() and select2()), add them to the list held by the property
        ignorePaths. The key has to be separated with the string defined by the
        property pathDelimiter.
    You can deserialize specific string values to JSON while walking. To do that
        preceed the key with the deserialize operator. To turn this feature on
        set the property deserializeOperator to a string value; None turns this
        off.
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
        self._ignorePaths = []
        self._dye = self.Dye()
        self._modifiedValueFormatter = lambda v1, v2: v1 + ' > ' + v2
        self._prefix_added    = '> '
        self._prefix_removed  = '< '
        self._prefix_modified = '~ '
        self._pathDelimiter = '.'
        self._deserializeOperator = None
        self._useSquareBrackets = True
        
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
    
    def select1( self, path ):
        sub = DiffJson.getPath( self._json1, path, self._pathDelimiter, self._deserializeOperator, self._useSquareBrackets )
        if sub is not None:
            self._json1 = sub
            return True
        else:
            return False
    
    def select2( self, path ):
        sub = DiffJson.getPath( self._json2, path, self._pathDelimiter, self._deserializeOperator, self._useSquareBrackets )
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
    def ignorePaths( self ):
        """
        @rtype: [basestring]
        """
        return self._ignorePaths

    @ignorePaths.setter
    def ignorePaths( self, value ):
        """
        @type value: [basestring]
        """
        self._ignorePaths = value

    @property
    def colored( self ):
        return self._dye.colored
        
    @colored.setter
    def colored( self, value ):
        self._dye.colored = value
        
    @property
    def modifiedValueFormatter( self ):
        """
        @rtype: (basestring, basestring) -> basestring
        """
        return self._modifiedValueFormatter
    
    @modifiedValueFormatter.setter
    def modifiedValueFormatter( self, value ):
        """
        @type value: (basestring, basestring) -> basestring
        """
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

    @property
    def pathDelimiter( self ):
        return self._pathDelimiter

    @pathDelimiter.setter
    def pathDelimiter( self, value ):
        self._pathDelimiter = value

    @property
    def deserializeOperator( self ):
        """
        @rtype: basestring|None
        """
        return self._deserializeOperator

    @deserializeOperator.setter
    def deserializeOperator( self, value ):
        """
        @type value: basestring|None
        """
        self._deserializeOperator = value

    @property
    def useSquareBrackets( self ):
        return self._useSquareBrackets

    @useSquareBrackets.setter
    def useSquareBrackets( self, value ):
        self._useSquareBrackets = value

    @staticmethod
    def getPath( jsonDictOrList, path, delimiter, deserializeOperator, useSquareBrackets ):
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
            paths = path.strip( delimiter ).split( delimiter )

            if useSquareBrackets:
                # convert key[value] to key.value
                newPaths = []
                for x in paths:
                    if not deserializeOperator:
                        regex = r'^.*\[([0-9]+)\]$'
                    else:
                        regex = r'^.*\[(' + re.escape(deserializeOperator) + r'[0-9]+)\]$'
                    m = re.match( regex, x )
                    if m:
                        indexString = m.group( 1 )
                        newPaths.append( x[:len( x ) - (len( indexString ) + 2)] )
                        newPaths.append( indexString )
                    else:
                        newPaths.append( x )
                paths = newPaths

            for x in paths:
                deserializeValue = False
                if deserializeOperator is not None and not x in elem and len(x) >= len(deserializeOperator) and x[:len(deserializeOperator)] == deserializeOperator:
                    x = x[len(deserializeOperator):]
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
        if self._useSquareBrackets and isinstance( key, int ):
            return path + dyer( '[' + unicode(key) + ']' )
        else:
            if path == '':
                return dyer( unicode(key) )
            else:
                return path + self._pathDelimiter + dyer( unicode( key ) )
    
    def _combinePath( self, path, key ):
        if self._useSquareBrackets and isinstance( key, int ):
            return path + '[' + unicode(key) + ']'
        else:
            if path == '':
                return unicode(key)
            else:
                return path + self._pathDelimiter + unicode( key )

    @staticmethod
    def _prettyValue( value ):
        if isinstance( value, dict ) or isinstance( value, list ):
            return json.dumps( value, sort_keys = sys.version_info < (2, 7) )
        elif isinstance( value, bool ):
            return 'true' if value else 'false'
        elif value is None:
            return 'null'
        elif isinstance( value, int ) or isinstance( value, float ):
            return unicode( value )
        else:
            return '"' + value + '"'

    def __diff( self ):
        self.__diffValue( '', '', self._json1, self._json2 )
    
    def __diffDict( self, path, original, modified ):
        remaining = copy.deepcopy( modified )
        for key, value in original.iteritems():
            if key in modified:
                del remaining[key]
            if self._combinePath( path, key ) in self._ignorePaths:
                continue
            if key in modified:
                self.__diffValue( path, key, value, modified[key] )
            else:
                self.__printer( self.prefix_removed + self._coloredKey( path, key, self._dye.removed ) + ': ' +
                    DiffJson._prettyValue( value )
                    )
        for key, value in remaining.iteritems():
            if self._combinePath( path, key ) in self._ignorePaths:
                continue
            self.__printer( self.prefix_added + self._coloredKey( path, key, self._dye.added ) + ': ' +
                DiffJson._prettyValue( value )
                )
    
    def __diffList( self, path, original, modified ):
        for key, value in enumerate( original ):
            if self._combinePath( path, key ) in self._ignorePaths:
                continue
            if key < len(modified):
                self.__diffValue( path, key, value, modified[key] )
            else:
                self.__printer( self.prefix_removed + self._coloredKey( path, key, self._dye.removed ) + ': ' +
                    DiffJson._prettyValue( value )
                    )
        for key, value in enumerate( modified[len(original):] ):
            if self._combinePath( path, key ) in self._ignorePaths:
                continue
            self.__printer( self.prefix_added + self._coloredKey( path, key + len(original), self._dye.added ) + ': ' +
                DiffJson._prettyValue( value )
                )
    
    def __diffValue( self, path, key, original, modified ):
        if original != modified:
            fullPath = self._combinePath( path, key )
            if fullPath in self._ignorePaths:
                return
            if isinstance( original, dict ) and isinstance( modified, dict ):
                self.__diffDict( fullPath, original, modified )
            elif isinstance( original, list ) and isinstance( modified, list ):
                self.__diffList( fullPath, original, modified )
            else:
                value = self.modifiedValueFormatter(
                    self._dye.removed( DiffJson._prettyValue( original ) ),
                    self._dye.added( DiffJson._prettyValue( modified ) )
                    )
                self.__printer( self.prefix_modified + self._coloredKey( path, key, self._dye.modified ) + ': ' +
                    unicode( value )
                    )
