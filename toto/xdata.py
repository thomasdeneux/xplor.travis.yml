"""xdata module is a module to define data in the form of an ND array
XPLOR dataset is contained in a N dimensional array. The array contains the 
data itself, but the array also has headers. The headers contains this
information about each of the dimensions : names, types, units, scale, ...
This module uses : 
        pandas as pd
        numpy as np
        operator
        abc
There are 3 classes in this module:
    
    - DimensionDescription : for a specific dimension, DimensionDescription 
                        stores a label,a dimension_type ('numeric', 'logical',
                        'string', or 'mixed'), possibly a unit and the 
                        corresponding conversion table.
                        
                        It allows to determine the dimension_type of an
                        element, and access the default value of a given
                        dimension_type.
                        
                        
    - Header : abstract class (subclasses are CategoricalHeader 
               and MeasureHeader). Headers contains information about a
               dimension of the NDimensional data, such as a general label,
               the number of element, the description of the
               dimension/subdimensions, and allows to access the values to
               display on the axis.
               
    - CategoricalHeader : CategoricalHeader is a subclass of Header. It is used
                          to characterize a dimension in which the data has no
                          regular organisation. It usually is a list of
                          elements. However, such elements can have interesting
                          features of different types. That's why such features
                          are stored in columns, each of them described by a
                          DimensionDescription object.
                          
    - MeasureHeader : MeasureHeader is a subclass of Header. It is used for
                      data acquired by equally spaced sample in a continuous
                      dimension such as time or space. In which case, there is
                      only one subdimension (i.e. only one column).
                      
    - Xdata : TODO
    
"""

# Authors: Elodie Ikkache CNRS <elodie.ikkache@student.ecp.fr>
#          Thomas Deneux CNRS <thomas.deneux@unic.cnrs-gif.fr>
#
# version 1.0
# -*- coding: utf-8 -*-

import pandas as pd
import numpy as np
# itemgetter is used to sort a list of dictionaries
from operator import itemgetter
# Header is abstract, subclasses are MeasureHeader and CategoricalHeader
from abc import ABC, abstractmethod
from pprint import pprint


class Color:
    """ Defines colors.

    This class allows defining colors, either as RGB values or using
    predefined strings.

    Parameters
    ----------
    rgb : either a 3-tuple with 3 integers between 0 and 255,
                or a predefined string predefined strings are 'black',
                'white', 'red', 'green', 'purple', 'cyan', 'magenta'

    Attributes
    ----------
    rgb : a 3-tuple with 3 integers between 0 and 255

    """

    def __init__(self, rgb):
        if isinstance(rgb, str):
            if rgb == 'black':
                self.rgb = [0, 0, 0]
            elif rgb == 'white':
                self.rgb = [255, 255, 255]
            elif rgb == 'red':
                self.rgb = [255, 0, 0]
            elif rgb == 'green':
                self.rgb = [0, 255, 0]
            elif rgb == 'blue':
                self.rgb = [0, 0, 255]
            elif rgb == 'purple':
                self.rgb = [255, 255, 0]
            elif rgb == 'cyan':
                self.rgb = [0, 255, 255]
            elif rgb == 'magenta':
                self.rgb = [255, 0, 255]
            else:
                raise Exception("String argument is not a recognized color "
                                "name.")
        else:
            try:
                self.rgb = [int(x) for x in rgb]
                if len(self.rgb) != 3:
                    raise Exception()
                for i in range(3):
                    x = self.rgb[i]
                    if x < 0 or x > 255:
                        raise Exception()
            except:
                raise Exception("Argument must be either a 3-element color "
                                "definition or a string color name.")

    def __eq__(self, other):
        return self.rgb == other.rgb


class DimensionDescription:
    
    """ This class aims at defining a dimension.
    
    This class allows to define a dimension with a name, a type ('numeric,
    'logical', 'string', 'color' or 'mixed'), and possibly a unit for 
    numerical dimensions.
    
    Parameters
    ----------
    - label :
        name for the dimension
        (type str (e.g. 'time'))
    - dimension_type :
        can be 'numeric', 'logical', 'string', 'color' or 'mixed'
    - unit :
        One can define only the unit (e.g. mm) or the conversions as well in
        the form of a list (e.g. ['mm', 10**(-3), 'm', 1]).
        
        (type str or list)
        
        optional (default value = None)
 
    
    Attributes
    ----------
    - label :
        name of the dimension
        (type str)
    - dimension_type :
        'numeric', 'logical', 'string', 'color' or 'mixed'
    - unit :
        currently used unit
        (type str)
    - allunit :
        list of dictionaries for unit conversions

    Methods
    -------
    - set_dimtype_to_mixed :
        changing the dimension_type to 'mixed' if adding values that are not
        of the correct dimension_type (merging lines for instance)
    - copy :
        to copy a DimensionDescription instance
        
    (static methods)
    - infertype(x, getdefaultvalue=False) :
        gives the dimension_type of the x element and possibly the associated
        defaultvalue
    - defaultvalue(dimension_type) :
        gives the default value associated to a certain dimension_type
        
    Examples
    --------
    
     t = DimensionDescription('time','numeric',['s, 1, 'ms', 10**(-3),
     'min', 60, 'hour', 3600])
    
     c = DimensionDescription('condition','string')
     
    Note
    ----
     
    DimensionDescription of dimension type 'color' are Color objects

    """

    def __init__(self, 
                 label,
                 dimension_type,
                 unit=None):
        """Constructor of the class DimensionDescription"""
        
        # Checking arguments and setting properties.

        # label must be a string
        if not isinstance(label, str):
            raise Exception('label must be a string')
        self._label = label

        # dimension_type must be 'numeric', 'logical', 'string, or 'mixed'
        if not (dimension_type in ['numeric', 'logical', 'string', 'color',
                                   'mixed']):
            raise Exception("a dimension_type must be 'numeric', 'logical',"
                            "'string', 'color' or 'mixed'")
        self._dimension_type = dimension_type

        # only 'numeric' dimensions can have a unit, and this is not mandatory
        if unit is None:
            self._unit = None
            self._all_units = None
        elif dimension_type != 'numeric':
            raise Exception("only numeric DimensionDescriptions can have a"
                            " unit")
        # the unit can be given in the form of a string ...
        elif isinstance(unit, str):
            self._unit = unit
            self._all_units = [{'unit': unit, 'value': 1.0}]
        # ...or in the form of a list of linked units and conversion
        # coefficients
        elif not unit:  # pythonic way of checking whether a list is empty,
            # by using the implicit booleanness
            raise Exception("there must be at least one unit")
        elif isinstance(unit, list):
            list_length = len(unit)
            if list_length % 2 != 0:
                raise Exception("unit must be a string with the unit symbol or"
                                " a list of the symbols of the unit followed"
                                "by the conversion indicator"
                                " (e.g. ['mm', 10**(-3), 'm', 1]")
            # One of the units must be the reference.
            # That means that one conversion coefficient must be equal to one.
            reference = False
            self._all_units = []
            for i in range(0, list_length, 2):
                # assign pairs of items to unit (string) and value (float)
                try:
                    d = {'unit': str(unit[i]), 'value': float(unit[i+1])}
                except:
                    raise Exception("unit name must be a string and conversion"
                                    " coefficient must be a numerical scalar")
                self._all_units += [d]
                # take the first unit with value 1 has reference
                if d['value'] == 1 and not reference:
                    reference = True
                    self._unit = d['unit']
            if not reference:
                raise Exception("one of the conversion coefficients must be "
                                "equal to one to define a reference")
            # sort the list of units according conversion coefficients
            self._all_units.sort(key=itemgetter('value'))
        # Checking if the type of unit is either str, list or if it is None.
        else:
            raise Exception("unit must be a string with the unit symbol or a "
                            "list  of the symbols of the unit followed by "
                            "the conversion indicator (e.g. "
                            "['mm', 10**(-3), 'm', 1])")
                
    # Attributes label, dimension_type, unit and all_units can be seen but not
    # modified outside of the class (only get methods, no setters).
    @property
    def label(self):
        """name for the dimension (type str (e.g. 'time'))"""
        return self._label
    
    @property
    def dimension_type(self):
        """'numeric', 'logical', 'string', 'color' or 'mixed'"""
        return self._dimension_type
    
    @property
    def unit(self):
        """currently used unit (type str)"""
        return self._unit
    
    @property
    def all_units(self):
        """conversion table (type list of dict)"""
        return self._all_units
    
    def set_dimtype_to_mixed(self):
        """change the dimension_type to mixed"""
        self._dimension_type = 'mixed'
        
    def copy(self):
        """copy a DimensionDescription instance"""
        obj = DimensionDescription(self.label, self.dimension_type)
        obj._unit = self._unit
        obj._all_units = self._all_units
        return obj

    @staticmethod
    def infertype(x, getdefaultvalue=False):
        """infertype is a static method to access the dimension_type of an
        element x and if required, the associated default value"""
        if isinstance(x, bool):
            dimtype = 'logical'
        elif isinstance(x, str):
            dimtype = 'string'
        elif type(x) in [int, float, complex, np.float64, np.int64]:
            dimtype = 'numeric'
        elif isinstance(x, Color):
            dimtype = 'color'
        else:
            dimtype = 'mixed'
        if getdefaultvalue:
            return dimtype, DimensionDescription.defaultvalue(dimtype)
        else:
            return dimtype

    # Calculating a default value for the differents dimension_types.
    @staticmethod
    def defaultvalue(dimension_type):
        """defaultvalue is a static method to access the default value of a
        given dimension_type"""
        if dimension_type == 'numeric':
            return 0
        elif dimension_type == 'logical':
            return False
        elif dimension_type == 'string':
            return ''
        elif dimension_type == 'color':
            return Color((0, 149, 182))
            # it is a nice color, different from that of the background
        elif dimension_type == 'mixed':
            return None
        else:
            raise Exception("This function only gives the default value for"
                            " the following types: 'numeric', 'logical', "
                            "'string', 'color' or 'mixed'")


class Header(ABC):
    """ This abstract class allows the creation of headers for the different 
    dimensions of a dataset.
    
    Header is an abstract class that has two subclasses: CategoricalHeader and
    MeasureHeader.
    A Header object fully describes a dimension.
    A CategoricalHeader is used for data with  no regular organisation.
    It usually correspond to a list of elements. However,  such elements can
    have interesting features of different types. That's why such features are 
    stored in columns, each of them described by a DimensionDescription object.
    A MeasureHeader is used for data aquired with regular intervals in a
    continuous dimension such as time or space. In which case, there is only
    one subdimension (i.e. only one column witch is not stored).
    
    
    Parameters
    ----------     
     
    Attributes
    ----------
    - label :
        name of the dimension (type str)
    - column_descriptors :
        list of the DimensionDescription of each of the columns of values
    - is_measure :
        true if the header is a MeasureHeader instance, false if it is a
        CategoricalHeader instance
    - is_categorical_with_values :
        true if it is an instance of CategoricalHeader and that values is not
        None. If it is a categorical header but with no column or a measure
        header, it is false.
    - is_undifferentiated :
        true if it is a categorical header with no values
        (not is_categorical_with_values)

    Methods
    -------           
    (abstract methods)
    
    - n_elem :
        number of element in the column(s)/ number of samples
    - is_categorical :
        differentiate measure and categorical headers for the properties
        is_measure, is_categorical_with_values and is_undifferentiated
    - __eq__ :
        compares all the fields of the headers (returns True if all the 
        fields are the same) it can be used by writting header1 == header2
    - get_n_columns :
        gives the number of columns (1 for MeasureHeader, 0 to n for
        CategoricalHeader)
    - get_units :
        gives the list of the unit used for each column ('no unit' is 
        returned for each column with no specified unit)
    - get_all_units :
        gives the list of conversion table for each column ('no unit' is
        returned for each column with no specified unit)
    - disp :
        gives the main attributes of a Header
    - get_value :
        (self, nline, column = None)
        gives the value located at the line nline and at the column column
        (defined by it's label or it's number) or the fist one. Since we use
        pyhton, we have decided that to access the first element of the
        column, nline must be equal to 0.
    - get_itemname : 
        (self, nline)
        nline can here be an integer or a list of integer. The function
        returns the corresponding values of the first column.
    - copy :
        creates a copy of the header
                
    (non abstract method)
    
    - check_header_update:
        (self, flag, ind, newheader)
        flag : 'all', 'chgdim', 'new', 'remove', 'chg', 'perm','chg&new' or
        'chg&rm'  
            
        ind : numpy.array of shape (n,)
        
        basics checks when updating data and giving a new header
        
    Examples
    --------
     CategorialHeader: (with values)
         label : 'fruits'
         column_descriptors : (list of DimensionDescriptors, simplified here)
             1/ label : 'fruits', dimension_type : 'string', no unit
             
             2/ label : 'prices', dimension_type : 'numeric', unit : 'euros/kg'
             
             3/ label : 'color', dimension_type : 'string', no unit
             
         n_elem : 4
         values :
             [['apple', 0.5, 'red' ]
             
             ['pear', 0.75, 'green']
             
             ['banana', 0.66, 'yellow']
             
             ['cherry', 0.89, 'red']]
             
                        
                                   fruits
                                   
                         fruits |  prices  | color
                        ____________________________
                        
                         apple  |    0.5   |  red   
                          
                         pear   |   0.75   |  green
                          
                         banana |   0.66   |  yellow
                         
                         cherry |   0.89   |  red
                         
        
    CategorialHeader: (undifferentiated)
         label : 'fruits'
         
         column_descriptors : (list of DimensionDescriptors) : None
                 
         n_elem : 4
         
         values : None
            
                       'fruits'
                                   
                        fruits 
                         
                        1    
                        
                        2   
                        
                        3   
                        
                        4   
    
    MeasureHeader:
        label : 'x'
        
        column_descriptors : (list of one DimensionDescription)
        
            label : 'x', 
            
            dimension_type : 'numeric',
            
            unit : 'mm',
            
            all_units : [{unit : 'mm', 'value' : 10**(-3)}, {unit : 'm',
            'value' : 1}]
            
        n-elem : 4
        
        start : 1
        
        scale : 2
        
                                   'x'
                                    
                                    x 
    
                                    
                                    1 
                                   
                                    3 
                                   
                                    5 
                                   
                                    7 
     
    """

    # Define an abstract constructor which will not be used, but serves for
    # the the code analyzer to learn the attributes mandatory for a Header
    # class
    @abstractmethod
    def __init__(self):
        self._label = None
        self._column_descriptors = None
        self._n_elem = None

    # Attributes label and column_descriptors can be seen but not modified
    # outside of the class (only get methods, no setters).
    @property
    def label(self):
        """general label of the header"""
        return self._label
    
    @property
    def column_descriptors(self):
        """list of DimensionDescription instances describing each column"""
        return self._column_descriptors
    
    # Properties is_measure, is_undifferentiated, is_categorical_with_values
    #  help to differentiate different types of headers faster in other modules
    @property
    def is_measure(self):
        """fast way to differentiate measure headers from categorical ones"""
        return not self.is_categorical
    
    @property    
    def is_categorical_with_values(self):
        """fast way to test if a header is categorical with values
        (ie list of elements)"""
        return self.is_categorical and self.get_n_columns() > 0

    @property    
    def is_undifferentiated(self):
        """fast way to test if a header is categorical with no values"""
        return self.is_categorical and self.get_n_columns() == 0
                
    # Methods
    def check_header_update(self, flag, ind, new_header):
        """basics checks when updating data and giving a new header"""
        # check types of parameters
        if not isinstance(new_header, Header):
            raise Exception("new_header must be a header")

        # 'chgdim' flag allows any change!
        if flag == 'chgdim':
            return

        # check that the types are coherent
        if self.is_categorical != new_header.is_categorical:
            raise Exception("both headers must be of same type")

        # check that labels are preserved
        if new_header._label != self._label:
            raise Exception("both headers must have the same label")

        # check that column descriptors are preserved (note that there can
        # be additional columns though)
        if new_header._column_descriptors[:len(self._column_descriptors)] !=\
                self._column_descriptors:
            raise Exception("sub-labels are not preserved")

        # only 'all' and 'chgdim' flag allows to change n_elem as we want
        if flag == 'new':
            if new_header.n_elem != self._n_elem + len(ind):
                raise Exception("the new headers has the wrong number of "
                                "elements")
        elif flag in ['chg' 'perm']:
            if new_header.n_elem != self._n_elem:
                raise Exception("both headers must have the same number "
                                "of elements")
        elif flag == 'remove':
            if new_header.n_elem != self._n_elem - len(ind):
                raise Exception("the new headers has the wrong number of "
                                "elements")
        # 'chg&new' and 'chg&rm' flags impose ind to be an array of array
        # with the first element being the array of indices to be changed
        # and the second element being an array of new indices
        elif flag == 'chg&new':
            if new_header.n_elem != self._n_elem + len(ind[1]):
                raise Exception("the new headers has the wrong number of "
                                "elements")
        elif flag == 'chg&rm':
            if new_header.n_elem != self._n_elem + len(ind[0]):
                raise Exception("the new headers has the wrong number of "
                                "elements")
        else:
            raise Exception("Unknown flag")

    # abstract methods
    @abstractmethod
    def n_elem(self):
        """gives the the number of elements/samples in that dimension"""
        pass
   
    @abstractmethod
    def is_categorical(self):
        """used for the properties is_measure, is_categorical_with_values and
        is_undifferentiated, fast way to differenciate categorical and measure
        headers"""
        pass
    
    @abstractmethod
    def __eq__(self, other):
        """Override the default Equals behavior"""
        pass
    
    @abstractmethod
    def get_n_columns(self):
        """returns the number of columns"""
        pass

    @abstractmethod
    def get_units(self):
        """gives a list of the units of all the columns"""
        pass
    
    @abstractmethod
    def get_all_units(self):
        """gives a list of the conversion tables for the units of all the
        columns"""
        pass
            
    @abstractmethod
    def disp(self):
        """display some information about the haeder"""
        pass
    
    @abstractmethod
    def get_value(self, line, column=None):
        """get the value of the line of number line of the column column
        (defined by it's label or number) or the first column"""
        pass
    
    @abstractmethod
    def get_itemname(self, nline):
        """get the value(s) of the line(s) in nline (it can be an int or a list
        of int), of the first column"""
        pass
    
    @abstractmethod
    def copy(self):
        """creates a copy of the Header instance"""
        pass


class CategoricalHeader(Header):
    """ This class allows the creation of a header for a categorical dimension
    of a dataset.
    
    CategoricalHeader is used for categorical dimensions of a dataset. This
    means that this dimension is either not continuous or that the data has not
    been collected regularly in this dimension. Therefore, their is no scale,
    measure for this dimension. It is more a collection of objects.
    
    A CategoricalHeader has a general label as well as one or several
    DimensionDescription objects stored in column_descriptorss to describe each
    of the features. For each feature, values can be given (e.g. for 'fruits'
    values would be 'apple', 'pear', 'blueberry', 'watermelon'...) or be a list
    of numbers. The first case corresponds to 'is_categorical_with_values', the
    second to 'is_undifferentiated'
    
    
    
    Parameters
    ----------     
    - label:
        name of the header
        (type : str)
    - column_descriptors :
        description of the dimension of each feature
        
        (type str, DimensionDescription or a list of such elements)
        
        (optional, the case with no column is possible. The legend would then
        be a list of int [1, 2, ...], it is undifferentiated)
     
    - n_elem :
        number of element in the column(s)
        
        (type int)
        
        (optional if values is specified)
            
    - values :
        content of the various subdimensions
        
        (type DataFrame from pandas (pandas.core.frame.DataFrame) of shape
        (n_elem, len(column_descriptors))
        
        (optional if it is just undifferentiated series of measures and that
        n_elem is given)
            
    
    Attributes
    ----------
    - label :
        name of the dimension
        (type str)
    - column_descriptors :
        list of the DimensionDescription of each of the columns of values
    - values :
        content of the various subdimensions (pandas DataFrame
        (pandas.core.frame.DataFrame)of shape (n_elem, len(column_descriptors))
      
    Methods
    -------  
    (methods imposed by inheritance)
    
    - n_elem :
        number of element in the column(s)/ number of samples number of lines
        of values
    - is_categorical :
        differentiate measure and categorical headers for the properties
        is_measure, is_categorical_with_values and is_undifferentiated
    - is_categorical :
        returns True since it is the class CategoricalHeader
    - __eq__ :
        compares all the fields of the headers (returns True if all the
        fields are the same) it can be used by writting header1 == header2
    - get_n_columns :
        gives the number of columns (1 for MeasureHeader, 0 to n for
        CategoricalHeader)
    - get_units :
        gives the list of the unit used for each column ('no unit' is returned
        for each column with no specified unit)
    - get_all_units :
        gives the list of conversion table for each column ('no unit' is
        returned for each column with no specified unit)
    - disp :
        gives the main attributes of a Header
    - get_value(nline, column = None) : 
        gives the value located at the line nline and at the column column
        (defined by it's label or it's number) or the fist one. Since we use
        pyhton, we have decided that to access the first element of the
        column, nline must be equal to 0.
    - get_itemname(nline) :
        nline can here be an integer or a list of integer. The function
        returns the corresponding values of the first column
    - copy :
        creates a copy of the categorical header
    
    (other methods)
    
    - add_column(column_descriptor, values) :
        column_descriptor must be of type str or DimensionDescription
        values must be of type pandas.core.series.Series this method allows
        to created a new categorical header from the attributes of a previous
        categorical haeder, while adding a new column (it can be usefull for
        selections or to add colors)
    - update_categoricalheader(flag, ind, values) :
        flags can be : 'all', 'new', 'chg', 'chg&new', 'chg&rm', 'remove',
        'perm'
        
        idn indicates were the changes take place
        
        values contains the new values
        
        This method allows filters to create a new categorical header from
        the current one, with some changes in the values
    - mergelines(ind) :
        When merging some data, the corresponding header's lines must be 
        merged as well. Mergelines returns for each column all the
        encountered values with no repetitions in the from of a pandas Serie.
        
    Example
    --------
    
    (with values)
    
         label : 'fruits'
         
         column_descriptors : (list of DimensionDescriptors, simplified here)
         
             1/ label : 'fruits', dimension_type : 'string', no unit
             
             2/ label : 'prices', dimension_type : 'numeric', unit : 'euros/kg'
             
             3/ label : 'color', dimension_type : 'string', no unit
             
         n_elem : 4
         
         values :
             
             [['apple', 0.5, 'red' ]
             
             ['pear', 0.75, 'green']
             
             ['banana', 0.66, 'yellow']
             
             ['cherry', 0.89, 'red']]
             
                        
                                   fruits
                                   
                         fruits |  prices  | color
                        ____________________________
                         apple |    0.5   |  red    
                          
                         pear  |   0.75   |  green
                          
                         banana |   0.66   |  yellow
                         
                         cherry |   0.89   |  red

    (undifferentiated)
    
         label : 'fruits'
         
         column_descriptors : (list of DimensionDescriptors, simplified here) :
         []
         
         n_elem : 4
         
         values : None
         
            
                       'fruits'
                                   
                        fruits 
                         
                        1    
                        
                        2   
                        
                        3   
                        
                        4  
 
    """
    
    def __init__(self,
                 label,
                 column_descriptors=None,
                 n_elem=None,
                 values=None):
        """Constructor of the class CategoricalHeader"""
        # label is not optional and must be of type string
        # label can be different from the labels of the columns
        if not (isinstance(label,str)):
            raise Exception("The header's label must be of type str")
        self._label = label
        # if values is None, so is column_descriptors, but we must have n_elem
        if values is None:
            if n_elem is None:
                raise Exception("if no value is given, n_elem must be given")
            elif not isinstance(n_elem, int):
                raise Exception("n_elem must be of type int")
            if not ((column_descriptors is None) | (column_descriptors == [])):
                raise Exception("if there is no values, there are no columns"
                                " to be described")
            self._values = pd.DataFrame(np.zeros((n_elem, 0)))
            self._column_descriptors = None
        elif not isinstance(values, pd.core.frame.DataFrame):
            raise Exception("values must be a pandas DataFrame")
        else:
            # values is a DataFrame
            # we have to check that it has the correct shape
            # however, labels of the dataframe will not be taken into
            # consideration correspond
            if isinstance(n_elem, int):
                if not n_elem == values.shape[0]:
                    raise Exception("n_elem is not coherent with shape of "
                                    "values")
            elif not n_elem is None:
                raise Exception("n_elem must but of type int")
            # n_elem is either not given or correspond to the number of 
            # lines of the dataframe
            # let's check that values and column_descriptors are size coherent
            if isinstance(column_descriptors, str) | \
                         isinstance(column_descriptors, DimensionDescription):
                column_descriptors = [column_descriptors]
            elif not isinstance(column_descriptors, list):
                raise Exception ("column_descriptors must be of type str, "
                                 "DimensionDescription or a list of such "
                                 "elements")
            # column_descriptors is now a list
            if len(column_descriptors) != values.shape[1]:
                raise Exception ("column_descriptors and values must have the "
                                 "same length")
            self._values = values
            self._column_descriptors = []
            for i in range (len(column_descriptors)):
                if isinstance(column_descriptors[i], str):
                    dimdescription = \
                    createDimensionDescription(column_descriptors[i],
                                               values[i])
                    self._column_descriptors += [dimdescription]
                elif isinstance(column_descriptors[i], DimensionDescription):
                    d = column_descriptors[i].dimension_type
                    if d != 'mixed':
                        for e in range (values.shape[0]):
                            # /!\dataframe[column][line]
                            if DimensionDescription.infertype(values[i][e]) != d:
                                raise Exception("dimension_types of "
                                                "column_descriptors must be "
                                                "coherent with the data in "
                                                "values")
                    self._column_descriptors += [column_descriptors[i]]
                else:
                    raise Exception("all column_descriptors elements must be "
                                    "either of type str or "
                                    "DimensionDescription")
        

    # private property but with get access
    @property
    def n_elem(self):
        """number of elements/samples in that dimension, line number of values
        """
        return self.values.shape[0]
   
    @property
    def is_categorical(self):
        """CategoricalHeader instances are all categorical"""
        return True
    
    @property
    def values(self):
        """values is a pandas DataFrame"""
        return self._values
    
    # methods
    def __eq__(self, other):
        """Override the default Equals behavior"""
        # the two headers must have the same type
        if not isinstance(other, CategoricalHeader):
            return False
        # the label must be the same
        if self._label != other._label:
            return False
        # the column_descriptors must be the same
        if self.is_categorical_with_values != other.is_categorical_with_values:
                return False
        if self.is_categorical_with_values:
            if len(self._column_descriptors) != len(other._column_descriptors):
                    return False
            for i in range (len(self._column_descriptors)) :
                selfdescriptor =  self._column_descriptors[i]
                otherdescriptor = other._column_descriptors[i]
                if selfdescriptor.label != otherdescriptor.label :
                    return False
                if selfdescriptor.dimension_type != \
                otherdescriptor.dimension_type :
                    return False
                if selfdescriptor.unit != otherdescriptor.unit :
                    return False
                if selfdescriptor.all_units != otherdescriptor.all_units :
                    return False
        # the content of values must be the same
        if self._values.shape != other._values.shape :
            return False
        for column in range (self._values.shape[1]):
            for line in range (self._values.shape[0]):
                if self._values[column][line] != other._values[column][line]:
                    return False
        return True
        
    def get_n_columns(self):
        """returns the number of columns"""
        if self._column_descriptors is None:
            return 0
        return (len(self._column_descriptors))

    def get_units(self):
        """gives a list of the units of all the columns"""
        units = []
        if self.get_n_columns() == 0:
            return ([])
        else:
            for dimensiondescription in self._column_descriptors:
                if dimensiondescription.unit == None:
                    units += ['no unit']
                else:
                    units += [dimensiondescription.unit]
            return units
    
    def get_all_units(self):
        """gives a list of the conversion tables for the units of all the
        columns"""
        all_units = []
        if self.get_n_columns() == 0:
            return ([])
        for dimensiondescription in self._column_descriptors:
            if dimensiondescription.unit == None:
                all_units += ['no unit']
            else:
                all_units += [dimensiondescription.all_units]
        return all_units
    
    def disp(self):
        """display some information about the haeder"""
        print("CategoricalHeader : " + self._label)
        print("columns:")
        columns = self._column_descriptors
        for i in range (self.get_n_columns()):
            label = str(columns[i].label)
            if columns[i].unit == None :
                unit = ''
            else:
                unit = ' ('+ columns[i].unit+ ')'
            print(label + unit)
    
    def get_value(self, line, column = None):
        """get the value of the line of number line of the column defined by 
        column"""
        if not isinstance(line, int):
            raise Exception("line must be of type int")
        if line >= self.n_elem| line < 0:
            raise Exception("line must be in [0, n_elem[")
        if column is None :
            column = 0
        if isinstance(column, int):
            if column == 0 and self.get_n_columns() == 0:
                # nline must be 0 to have the first elem of a list in python.
                return (line)
            if column >= self.get_n_columns() | column < 0:
                raise Exception("column is a str or an int in [0, n_col[")
            return (self._values[column][line])
        elif not isinstance(column, str):
            raise Exception ("column is either the label of a column or it's"
            "number (int)")
        # if it is a string
        count = 0
        for dimdescriptor in self._column_descriptors:
            if dimdescriptor.label == column:
                return self._values[count][line]
            count += 1
        raise Exception("column is either the label of a column or it's"
            "number (int)")
    
    def get_itemname(self, line):
        """get the value(s) of the line(s) in nline (it can be an int or a list
        of int), of the first column"""
        # this function is the same for both the headers, but it could be
        # modified to choose witch column we want for categorical headers
        if isinstance(line, int):
            if line >= self.n_elem| line < 0:
                raise Exception("nline must be in [0, n_elem[")
            return (self.get_value(line))
        elif isinstance(line, list):
            itemnames = []
            for n in line:
                if not isinstance(n,int):
                    raise Exception("all line numbers must be integers")
                itemnames += [self.get_value(n)]
            return itemnames
        raise Exception("nline must be an int or a list of int")
    
    def add_column(self, column_descriptor, values):
        """this method allows to add a column to a categorical header"""
        if not isinstance(values, pd.core.series.Series):
            raise Exception ("values must be of type pd.core.series.Series")
        elif values.shape[0] != self._values.shape[0]:
            raise Exception ("values must have the correct amount of lines")
        if isinstance(column_descriptor, str):
            column_descriptor = createDimensionDescription(column_descriptor,
                                                           values)
        elif not isinstance(column_descriptor, DimensionDescription):
            raise Exception("column_descriptor must be of type str or "
                            "DimensionDescription")
        else:
            # if it was a given DimensionDescriptor, let's check that the
            # dimension_type correspond to that of the values
            dimension_type = column_descriptor.dimension_type
            if dimension_type != 'mixed':
                for i in values:
                    if DimensionDescription.infertype(i) != dimension_type:
                        raise Exception ("the dimension_type of the "
                                         "DimensionDescription must correspond"
                                         " to that of the values")
        column_descriptors = self._column_descriptors + [column_descriptor]
        newvalues = self._values.copy()
        newvalues[len(column_descriptors)-1] = values
        return (CategoricalHeader(self._label,
                                  column_descriptors,
                                  values = newvalues))
        
    def update_categoricalheader(self, flag, ind, values):
        """updates the values of a categorical header"""
        # flag 'all' : all the values can change, they are all given
        # in values argument of type pandas DataFrame
        if flag == 'all':
            if (ind is None) | (ind ==[]) | (ind == range(self.n_elem)):
                if not isinstance(values, pd.core.frame.DataFrame):
                    raise Exception("values must be a pandas DataFrame")
                elif values.shape[1] != self._values.shape[1]:
                    raise Exception("values must keep the same number of "
                    "columns")
                column_descriptors = self._column_descriptors
                for j in range(values.shape[1]):
                    if column_descriptors[j].dimension_type != 'mixed':
                        for i in range(values.shape[0]):
                            if column_descriptors[j].dimension_type != \
                            DimensionDescription.infertype (values[j][i]):
                                column_descriptors[j].set_dimtype_to_mixed()
                                i = values.shape[0]
                return CategoricalHeader(self._label,
                                         column_descriptors,
                                         values = values)
            else:
                raise Exception("ind must be empty or the list of all the "
                                "indices that have changed")
        # flag 'new' : adding new lines, some of wich can be the merging of 
        # many lines
        elif flag == 'new':
            if (ind is None) | (isinstance(ind, list)):
                   if not isinstance(values, list):
                       raise Exception("values must be a list of pandas Serie")
                   newvalues = self._values.copy()
                   new_descriptors = self.column_descriptors
                   for s in values:
                       j = self.get_n_columns()
                       if not isinstance(s, pd.core.series.Series):
                           raise Exception("values must be a list of pandas "
                                           "Serie")
                       elif (s.shape[0] != j):
                           raise Exception("all series in values must have the"
                                           " same number of elements that the "
                                           "number of column of the header")
                       for i in range(j):
                           dimtype = new_descriptors[i].dimension_type
                           if  (dimtype != 'mixed') | \
                           (dimtype != DimensionDescription.infertype(s[i])):
                               new_descriptors[i].set_dimtype_to_mixed()    
                       newvalues = newvalues.append(s, ignore_index=True)
                   return CategoricalHeader (self._label,
                                             new_descriptors,
                                             values = newvalues)            
            else :
                raise Exception("ind must be empty or the list of all the "
                                "indices that have changed")
        # flag 'chg' : changing some lines (keep the same number of lines)
        elif flag == 'chg':
            if not isinstance(ind, list):
                raise Exception ("ind must be the list of the indicices of the"
                                 " lines that have changed")
            elif not isinstance(values, list):
                raise Exception ("values must be a list of the new lines "
                                 "(pandas series)")
            elif len(values) != len(ind):
                raise Exception ("values and ind must have the same length")
            newvalues = self._values.copy()
            new_descriptors = self.column_descriptors
            j = self.get_n_columns()
            for i in range(len(ind)):
                if not isinstance (ind[i], int):
                    raise Exception ("ind must be the list of the indicices of"
                                     "the lines that have changed")
                elif (ind[i] < 0) | (ind[i] >= self.n_elem):
                    raise Exception ("for a chg flag, indices must be in range"
                                     " of n_elem")
                elif not isinstance(values[i], pd.core.series.Series):
                    raise Exception ("new lines must be pandas series")
                elif values[i].shape[0]!= j:
                    raise Exception ("all series must have the same number of "
                                     "element as the number of column of the "
                                     "header")
                for c in range(j):
                    dimtype = new_descriptors[c].dimension_type
                    if  (dimtype != 'mixed') | \
                    (dimtype != DimensionDescription.infertype(values[i][c])):
                        new_descriptors[i].set_dimtype_to_mixed()    
                newvalues.iloc[ind[i]] = values[i]
            return CategoricalHeader (self._label,
                                      new_descriptors,
                                      values = newvalues)
        # flag 'remove' : suppress some lines
        elif flag == 'remove':
            if not isinstance(ind, list):
                raise Exception ("ind must be the list of the indicices of the"
                                 " lines that have changed")
            for i in ind:
                if not isinstance(i, int):
                    raise Exception("all indicies must be of type int")
                elif (i < 0) | (i >= self.n_elem):
                    raise Exception ("indices must correspond to an existing"
                                     " line")
            if (not values is None) & (values != []):
                raise Exception ("no new values can be given when only "
                                 "removing lines")
            newvalues = self._values.copy()
            newvalues = newvalues.drop(newvalues.index[ind])
            newvalues = newvalues.reset_index(drop=True)
            return CategoricalHeader (self._label,
                                      self._column_descriptors,
                                      values = newvalues)
        # flag 'perm' : change the lines order
        elif flag == 'perm':
            if (not values is None) & (values != []):
                raise Exception ("no new values can be given when only "
                                 "permutting lines")
            elif not isinstance(ind, list):
                raise Exception ("ind must be the list of the indicices of the"
                                 " lines that have changed")
            elif len(ind) != self.n_elem:
                raise Exception ("ind must be the list of all the indices in "
                                 "the new order")
            newvalues = pd.DataFrame()
            for i in range(len(ind)):
                if not isinstance(ind[i], int):
                    raise Exception ("all indices must be integers")
                newvalues = newvalues.append(self._values.iloc[ind[i]])
                newvalues = newvalues.reset_index(drop=True)
            return CategoricalHeader(self._label,
                                     self._column_descriptors,
                                     values = newvalues)
        # flag 'chg&new' : combination of 'chg' and 'new'
        elif flag == 'chg&new':
            if not isinstance(ind, list):
                raise Exception ("ind must be a list of the list of the "
                                 "indicices that have changed and the list of "
                                 "those to remove")    
            elif not isinstance(values, list):
                raise Exception ("values is of type list")    
            elif len(values) != 2:
                raise Exception ("values must containes the values to change "
                                 "and the values to add")
            elif not (isinstance(values[0], list) & \
                      isinstance(values[1], list)):
                raise Exception ("values must containes the values to change "
                                 "and the values to add in two lists")
            elif isinstance(ind[0], list):
                indchg = ind[0]
            else:
                indchg = ind
            # let's first change the lines that needs to be changed...    
            if len(values[0]) != len(indchg):
                raise Exception ("all the lines to be changed must be given "
                                 "a value")
            newvalues = self._values.copy()
            new_descriptors = self.column_descriptors
            j = self.get_n_columns()
            for i in range(len(indchg)):
                if not isinstance (indchg[i], int):
                    raise Exception ("all indices must be of type int")
                elif (indchg[i] < 0) | (indchg[i] >= self.n_elem):
                    raise Exception ("for a chg action, indices must be in "
                                     "range of n_elem")
                elif not isinstance(values[0][i], pd.core.series.Series):
                    raise Exception ("new lines must be pandas series")
                elif values[0][i].shape[0]!= j:
                    raise Exception ("all series must have the same number of "
                                     "element as the number of column of the "
                                     "header")
                for c in range(j):
                    dimtype = new_descriptors[c].dimension_type
                    if  (dimtype != 'mixed') | \
                    (dimtype != DimensionDescription.infertype(values[0][i][c])):
                        new_descriptors[i].set_dimtype_to_mixed()    
                newvalues.iloc[indchg[i]] = values[0][i]
            # ...now let's add the new lines
            for s in values[1]:
                if not isinstance(s, pd.core.series.Series):
                    raise Exception("values must be a list of pandas Serie")
                elif (s.shape[0] != j):
                    raise Exception("all series in values must have the same "
                                    "number of elements that the number of "
                                    "column of the header")
                for i in range(j):
                    dimtype = new_descriptors[i].dimension_type
                    if  (dimtype != 'mixed') | \
                    (dimtype != DimensionDescription.infertype(s[i])):
                        new_descriptors[i].set_dimtype_to_mixed()    
                newvalues = newvalues.append(s, ignore_index=True)
            return CategoricalHeader (self._label,
                                      new_descriptors,
                                      values = newvalues) 
        # flag 'chg&rm' : combination of 'chg' and 'rm'
        elif flag == 'chg&rm':
            if not isinstance(ind, list):
                raise Exception ("ind must be a list of the list of the "
                                 "indicices that have changed and the list of "
                                 "those to remove")    
            elif not isinstance(values, list):
                raise Exception ("values is of type list")    
            elif len(ind) != 2:
                raise Exception ("ind must containes the lines to change "
                                 "and the lines to remove")
            elif not (isinstance(ind[0], list) & \
                      isinstance(ind[1], list)):
                raise Exception ("values must containes the values to change "
                                 "and the values to add in two lists")
            # let's first change the lines that needs to be changed...    
            if len(values) != len(ind[0]):
                raise Exception ("all the lines to be changed must be given "
                                 "a value")
            newvalues = self._values.copy()
            new_descriptors = self.column_descriptors
            j = self.get_n_columns()
            for i in range(len(ind[0])):
                if not isinstance (ind[0][i], int):
                    raise Exception ("all indices must be of type int")
                elif (ind[0][i] < 0) | (ind[0][i] >= self.n_elem):
                    raise Exception ("for a chg action, indices must be in "
                                     "range of n_elem")
                elif not isinstance(values[i], pd.core.series.Series):
                    raise Exception ("new lines must be pandas series")
                elif values[i].shape[0]!= j:
                    raise Exception ("all series must have the same number of "
                                     "element as the number of column of the "
                                     "header")
                for c in range(j):
                    dimtype = new_descriptors[c].dimension_type
                    if  (dimtype != 'mixed') | \
                    (dimtype != DimensionDescription.infertype(values[i][c])):
                        new_descriptors[i].set_dimtype_to_mixed()    
                newvalues.iloc[ind[0][i]] = values[i]
            # ...now let's remove the unwanted lines
            for i in ind[1]:
                if not isinstance(i, int):
                    raise Exception("all indicies must be of type int")
                elif (i < 0) | (i >= self.n_elem):
                    raise Exception ("indices must correspond to an existing"
                                     " line")
            newvalues = newvalues.drop(newvalues.index[ind[1]])
            newvalues = newvalues.reset_index(drop=True)
            return CategoricalHeader (self._label,
                                      new_descriptors,
                                      values = newvalues)
        # all the accepted flags were listed before, so the argument is not 
        # valid  
        raise Exception("the given flag must be 'all', 'perm', 'chg', 'new'"
                        " 'remove', 'chg&new', or 'chg&rm'")
        
    def mergelines(self, ind):
        """creating the values (pandas Serie) for merged lines"""
        if not isinstance(ind, list):
            raise Exception ("ind must be a list of indices")
        ncol = len(self._column_descriptors)
        merge = []
        for j in range(ncol):
            merge.append([])
        for i in ind:
            if not isinstance(i, int):
                raise Exception ("all indices must be of type int")
            elif i<0 | i>self.n_elem:
                raise Exception ("indices must correspond to an element of "
                                 "values")
            for j in range(ncol):
                if not (self._values[j][i] in merge[j]):
                    merge[j].append(self._values[j][i])
        for j in range(ncol):
            if self._column_descriptors[j].dimension_type == 'color':
                red = 0
                green = 0
                blue = 0
                for i in (merge[j]):
                    red += i.rgb[0]
                    green += i.rgb[1]
                    blue += i.rgb[2]
                n = len(merge[j])
                merge[j]= Color((red/n, green/n, blue/n))
        return pd.Series(merge)
    
    def copy(self):
        """creates a copy of a categoricalHeader"""
        if self.column_descriptors is None:
            column_descriptors = []
        else:
            column_descriptors = []
            for c in self.column_descriptors:
                column_descriptors.append(c.copy())
        values = self._values.copy()
        return CategoricalHeader(self.label,
                                 column_descriptors,
                                 self.n_elem,
                                 values)
            
                
            
        
        
                  
class MeasureHeader(Header):
    """ This class allows the creation of a header for a measureable dimensions
    of a dataset.
    
    MeasureHeader is used for a measurable dimensions of a dataset. This
    means that this dimension is continuous and that the data has been 
    collected regularly in this dimension. Therefore, a scale, a start
    attributes can be defined.
    
    A MeasureHeader has a general label and only one column (there is only one
    feature of interest). This column is described by a single
    DimensionDescription object, but it is still stored in a list
    (column_descriptors) in order to keep the similarity between the different
    types of headers. The values are not stored because they can be calculated
    easily from the start and scale attributes and the n_elem property. 
    
    
    Parameters
    ----------     
    - label:
        name of the header
        (type str)
    - start :
        first value of this dimension
        (type float or int)
    - n_elem :
        number of element in the column
        (type int)
    - scale :
        interval between the values of this dimension
        (type float or int)        
    - unit :
        One can define only the unit (e.g. mm) or the conversions as well in
        the form of a list (e.g. ['mm', 10**(-3), 'm', 1])
            
        (type str or list)
        
        (optional)     
    - checkbank :
        Default value of checkbank is Flase. If is it True, a unit must be
        specified, in order to check in the bank of conversion tables if one
        exists for the given unit.
        
        (optional)
                
    - column_descriptors :
        description of the dimension (it's label must be the same as the
        general label of the header)
            
        (type DimensionDescription)
        
        (optional)
    
    
    Attributes
    ----------
    - label :
        name of the dimension (type str)
    - column_descriptors :
        list of one DimensionDescription instance
    - start :
        first value of this dimension (type float)
    - scale :
        interval between the values of this dimension (type float)
      
    Methods
    -------          
    (methods imposed by inheritance)
    
    - n_elem :
        number of element in the column(s)/ number of samples
    - is_categorical :
        differentiate measure and categorical headers for the properties
        is_measure, is_categorical_with_values and is_undifferentiated    
    - __eq__ :
        compares all the fields of the headers (returns True if all the
        fields are the same) it can be used by writting header1 == header2
    - get_n_columns :
        gives the number of columns (1 for MeasureHeader, 0 to n for
        CategoricalHeader)
    - get_units :
        gives the list of the unit used for each column ('no unit' is
        returned for each column with no specified unit)
    - get_all_units :
        gives the list of conversion table for each column ('no unit' is
        returned for each column with no specified unit)
    - disp :
        gives the main attributes of a Header
    - get_value(nline, column = None) :
        gives the value located at the line nline and at the column column
        (defined by it's label or it's number) or the fist one.Since we use
        pyhton, we have decided that to access the first element of the
        column, nline must be equal to 0.
    - get_itemname(nline) :
        nline can here be an integer or a list of integer. The function
        returns the corresponding values of the first column.
                
    (other methods)
    
    - update_measureheader(start = None, n_elem = None,scale = None):
        creates a new measure header from the attributes of a previous one,
        and the specified changes
    - copy :
        creates a copy of a MeasureHeader instance
        
    
    Example
    --------
        label : 'x'
        
        column_descriptors : (list of one DimensionDescription)
        
            label : 'x', 
            
            dimension_type : 'numeric',
            
            unit : 'mm',
            
            all_units : [{unit : 'mm', 'value' : 10**(-3)}, {unit : 'm',
            'value' : 1}]
    
        n-elem : 4
        
        start : 1
        
        scale : 1
        
        
                                   'x'
                                    
                                    x 
    
                                    
                                    1 
                                   
                                    3 
                                   
                                    5 
                                   
                                    7 
     
     
    """
    
    def __init__(self,
                 label,
                 start,
                 n_elem,
                 scale,
                 unit = None,
                 checkbank = False,
                 column_descriptors = None):
        
        """Constructor of the class MeasureHeader"""
        # label must be of type str
        if  not isinstance(label,str):
            raise Exception("label must be of type str")
        self._label = label
        # start must be of type int or float
        if not (isinstance(start, float) | isinstance(start, int)):
            raise Exception("start must be of type float or int")
        self._start = float(start)
        # n_elem must be of type int
        if not isinstance(n_elem, int):
            raise Exception ("n_elem must be of type int")
        self._n_elem = n_elem
        # scale must be of type int or float
        if not (isinstance(scale, float) | isinstance(scale, int)):
            raise Exception("scale must be of type float or int")
        self._scale = float(scale)
        # case with a column_descriptors parameter
        if isinstance(column_descriptors, DimensionDescription):
            if column_descriptors.label != label:
                raise Exception ("the general label and the label from the"
                "column_descriptors must be the same")
            elif not unit is None:
                raise Exception ("you can either choose to use unit (and"
                "possibly checkbank) or to use column_descriptors, not both ")
            self._column_descriptors = [column_descriptors]
        elif not column_descriptors is None :
            raise Exception ("column_descriptors must be of type"
            " DimensionDescription")
        elif not isinstance(checkbank, bool) :
            raise Exception("checkbank must be a boolean")
        elif unit is None:
            if checkbank:
                raise Exception ("Specify a unit so as to checkout the bank")
            dimdescription = DimensionDescription(label, 'numeric')
            self._column_descriptors = [dimdescription]
        elif isinstance(unit,str) | isinstance(unit,list):
            if checkbank:
                all_units = check_bank(unit)
                if all_units is None:
                    dimdescription = DimensionDescription(label,
                                                      'numeric',
                                                      unit)
                else:
                    units = []
                    for dico in all_units:
                        units += [dico['unit'], dico['value']]
                dimdescription = DimensionDescription(label,
                                                      'numeric',
                                                      units)
            else:
                dimdescription = DimensionDescription(label, 'numeric', unit)
            self._column_descriptors = [dimdescription]
        else :
            raise Exception ("unit must be a str or a list")


    # private property but with get access   
    @property
    def is_categorical(self):
        """MeasureHeader instances are all not categorical"""
        return False
    
    @property
    def start(self):
        """int or float, first value of the dimension"""
        return self._start
    
    @property
    def scale(self):
        """interval between the values of this dimension"""
        return self._scale
    
    @property
    def n_elem(self):
        """number of elements in the dimension"""
        return self._n_elem 

    
    # methods
    def __eq__(self, other):
        """Override the default Equals behavior"""
        # the two headers must have the same type
        if not isinstance(other, MeasureHeader):
            return False
        if self._label != other._label:
            return False
        if self._start != other._start:
            return False
        if self.n_elem != other._n_elem:
            return False
        if self._scale != other._scale:
            return False
        selfdescriptor =  self._column_descriptors[0]
        otherdescriptor = other._column_descriptors[0]
        if selfdescriptor.label != otherdescriptor.label :
            return False
        if selfdescriptor.dimension_type != otherdescriptor.dimension_type :
            return False
        if selfdescriptor.unit != otherdescriptor.unit :
            return False
        if selfdescriptor.all_units != otherdescriptor.all_units :
            return False
        return True
        
    def get_n_columns(self):
        """returns the number of columns"""
        return (1)    
    
    def get_units(self):
        """gives the unit if it exist, in the form of a list to be compatible
        with CategoricalHeaders"""
        if self._column_descriptors[0].unit == None:
            return (['no unit'])
        return ([self._column_descriptors[0].unit])
    
    def get_all_units(self):
        """gives the conversion tables in the form of a list with a single
        element to be compatible with Categorical headers"""
        if self._column_descriptors[0].unit == None:
            return (['no unit'])
        return ([self._column_descriptors[0].all_units])
    
    def disp(self):
        """display some information about the haeder"""
        print ("MeasureHeader : " + self._label)
        print ("unit : " + self.get_units()[0])
        print ("start : " + str(self._start))
        print ("scale : " + str(self._scale))
        print ("n_elem : " + str(self._n_elem))
    
    def get_value(self, line, column = None):
        """get the value of the line of number line of the first column"""
        if not (column is None or column == 0):
            raise Exception ("Measure headers have only one column, column"
            "argument must be None or 0")
        if not isinstance(line, int):
            raise Exception("line must be of type int")
        if line >= self._n_elem or line < 0:
            raise Exception("line must be in [0, n_elem[")
        # Since we use pyhton, we have decided that to access the first element
        # of the column, line must be equal to 0.
        return (self._start + line * self._scale)
    
    def get_itemname(self, nline):
        """get the value(s) of the line(s) in nline (it can be an int or a list
        of int), of the first column"""
        if isinstance(nline, int):
            if nline >= self._n_elem | nline < 0:
                raise Exception("nline must be in [0, n_elem[")
            return (self.get_value(nline))
        elif isinstance(nline, list):
            itemnames = []
            for n in nline:
                if not isinstance(n,int):
                    raise Exception("all line numbers must be integers")
                elif n >= self._n_elem | n < 0:
                    raise Exception("nline must be in [0, n_elem[")
                itemnames += [self.get_value(n)]
            return itemnames
        raise Exception("nline must be an int or a list of int")
        
        
    def update_measureheader(self,
                             start = None,
                             n_elem = None,
                             scale = None):
        """creates a new measure header from the attributes of a previous one,
        and the specified changes"""
        if start is None:
            start = self._start
        elif not (isinstance(start, int) | isinstance(start, float)):
            raise Exception ("start must be of type int or float")
        if n_elem is None:
            n_elem = self._n_elem
        elif not isinstance(n_elem, int):
            raise Exception("n_elem must be of type int")
        if scale is None:
            scale = self._scale
        elif not isinstance(scale, float) | isinstance(scale, int):
            raise Exception("scale must be of type int or float")
        return (MeasureHeader(self._label,
                              start,
                              n_elem,
                              scale,
                              column_descriptors =  \
                              self._column_descriptors[0]))
    def copy(self):
        """creates a copy of a measure header"""
        descriptor = self.column_descriptors[0].copy()
        return MeasureHeader(self.label,
                             self.start,
                             self.n_elem,
                             self.scale,
                             column_descriptors = descriptor)

class Xdata:
    """This class allows the creation of a ND dataset, with headers for each
    dimension and a name.
    
    Xdata is used to store the data. Xdata is a container for an ND
    (N dimensional) array with all the values/data, as well as all of the 
    headers describing each of the N dimensions, stored in a list. Xdata also
    has the name of the whole set of data and a data_descriptor attribute to
    describe the data.
    Xdata includes a handeling of events.
    TODO : explain better the event part
    
    
    Parameters
    ----------     
    - name :
        name of the dataset (type str)
    - data :
        N dimensional numpy array with the data itself
    - headers :
        list of the headers describing each of the N dimensions
    - unit :
        simple unit or list of conversion
    
    Attributes
    ----------
    - data :
        N dimensional numpy.ndarray with the data itself
    - headers :
        list of the headers describing each of the N dimensions
    - name :
        name of the dataset (type str)
    - data_descriptor :
        DimensionDescription instance describing the dataset
    
    Methods
    -------
    - get_n_dimensions :
        gives the number of dimensions of xdata (it corresponds to the
        number of headers)
    - shape :
        gives the shape of the data (it corresponds to the number of elements
        for each dimension)
    - copy :
        creates a copy of a Xdata instance
    - update_data(newdata) :
        Simply changing some values in data by giving a whole new numpy array.
        Thoses changes can change the length of measure headers or categorical
        headers tht are undifferentiated. This method returns a new Xdata
        instance.
    - update_xdata(flag, dim, ind, dataslices, modified_header) :
        - flag
            - 'chgdata' to only chage some data (it can modifie the length of
              measure headers and undifferentiated headers but not
              categoricalwithvalues headers), this flag is not supposed to be
              used: to simply change the data, one must use update_data.
              However, the flag can be 'all' but with no new header, in witch
              case, we transform it to the 'chgdata' flag (this is why it is
              tolerated as an arrgument as well)
        
            - 'all' to change the data and modifie the header (possible
              modifications are given for modified_header)
               
            - 'chg' to change some lines of a header and corresponding data
               
            - 'new' to add lines in a dimension
               
            - 'remove' to remove some lines
               
            - 'chg&new' to change and add some lines
               
            - 'chg&rm' to change and remove some lines
               
            - 'perm' to permute some lines
               
       - dim : (int) number of the modified header
       
       - ind : (list of int) indices of lines that are changing
       
       - dataslices : new values for the modified lines
       
       - modified_header : same header as before but with a few changes
       (adding columns, lines, changing values depending of the type of
       header).
       
       This method allows to update a header and the corresponding data,
       the shape of data migth be modifed but the dimensions are still
       representing the same thing(DimensionDescriptions are not changed,
       (except for dimension_type that migth become 'mixed' if some lines are
       merged)).It returns a new data instance.
    - modify_dimensions(flag, dim, newdata, newheaders):
        - flag
            - 'global' to change everything,
            - 'chgdim' to change one dimension/dimensions,
            - 'insertdim' to insert a dimension/dimensions,
            - 'rmdim' to remove a dimension/dimensions,
            - 'permdim' to permute the dimensions
                                  
        - dim : list of the dimensions to be changed
        
        - newdata : full numpy.array with the whole data (except for flag
        'permdim')
                                    
        - newheaders : list of the new headers
        
        This methods allows to modify the structure of a Xdata instance, i.e.
        to modify the DimensionDescriptions in the list of headers (and
        therefore the data) new headers do not represent the same thing as
        before. This method aslo allows to change the number of dimensions.
        It returns a new Xdata instance.
    
    
    Example
    -------
    Let's take the example of children throwing a ball.
    We are interrested in the hight of the ball over time, for each child, and
    for each throw.
    
    In this example, we have 3 dimensions:
         - time
         - child
         - number of the throw, that we are going to call repetition
         
    Therefore, headers will be a list of the 3 headers given below:
        
        - time is a MeasureHeader:
            
        label : 't'
        
        column_descriptors : (list of one DimensionDescription)
        
            label : 't', 
            
            dimension_type : 'numeric',
            
            unit : 'ms',
            
            all_units : [{unit : 'ms', 'value' : 10**(-3)},
            {unit : 's', 'value' : 1}]
            
        n-elem : 3000
        
        start : 0
        
        scale : 2
        
                                   't'
                                    
                                    t 
                                   
                                    0
                                    
                                    2 
                                    
                                    4 
                                    
                                    6 
                                    
                                   ...
                                   
        - repetition is a CategoricalHeader that is undifferentiated
         label : 'repetitions'
         
         column_descriptors : (list of DimensionDescriptors, simplified here)
         []
         
         n_elem : 8
         
         values : None
         
            
                        'repetitions'
                                   
                        repetitions 
                        
                        0 
                        
                        1  
                        
                        2  
                        
                        3  
                        
                        4 
                        
                        5
                        
                        6  
                        
                        7      
        
        - child is a CategoricalHeader with values (because we can store some
        complementary informatios)
        
         label : 'child'
         
         column_descriptors : (list of DimensionDescriptors, simplified here)
         
             1/ label : 'name', dimension_type : 'string', no unit
             
             2/ label : 'age', dimension_type : 'numeric', unit : 'year old'
             
             3/ label : 'gender', dimension_type : 'string', no unit
             
         n_elem : 5
         
         values :
             
             
             [['Emily', 8, 'female' ]
             ['Paul', 7, 'male']
             
             ['Helen', 9, 'female']
             
             ['Lily', 7, 'female']
             
             ['James', 9, 'male']]
             
             
                        
                                   child
                                   
                          name  |  age  | gender
                         _________________________
                          Emily |   8   |  female  
                          
                          Paul  |   7   |  male
                          
                          Helen |   9   |  female
                          
                          Lily  |   7   |  female
                          
                          James |   9   |  male
                          
        
        Now we have our list of headers, of length 3.
        
        
        The corresponding data is 3D array containing the values of the higth
        of the ball at all time for each of the children's throw. It is
        described (dimension_type and unit) in data_descriptor.
        
        All we miss is the name of this set of data and headers : "higth of
        the throw of a ball"
        
    """
    def __init__(self,
                 name,
                 data,
                 headers,
                 unit):
        """Constructor of the class Xdata"""
        # name must be a string
        if not isinstance(name, str):
            raise Exception ("name must be of type str")
        self._name = name
        # data must be a numpy array and headers a list with the same length
        if not isinstance(data, np.ndarray):
            raise Exception ("data must be of type numpy.ndarray")
        elif not isinstance(headers, list):
            raise Exception ("headers must be of type list")
        elif len(headers) != len(data.shape):
            raise Exception ("each dimension must be described by a header")
        self._data = data
        for h in headers:
            if not isinstance(h, Header):
                raise Exception ("headers must only contain header elements")
        self._headers = headers
        # unit must allow creation of a DimensionDescription instance
        if isinstance(unit, str) | isinstance(unit, list) | (unit is None):
            self._data_descriptor = DimensionDescription(name, 'numeric', unit)
        else:
            raise Exception ("unit must a string or a list of conversion")
    
    @property
    def name(self):
        """name of the data with the complementary informations stored in
        headers and data_descriptor"""
        return self._name
    
    @property
    def headers(self):
        """list of the headers for each dimension"""
        return self._headers
    
    @property
    def data(self):
        """ND numpy.array of numerical data"""
        return self._data
    
    @property
    def data_descriptor(self):
        """DimensionDescription instance to describe the content of data"""
        return self._data_descriptor
            
    def get_n_dimensions(self):
        """gives the number of dimensions of the data"""
        return len(self.headers)
    
    def shape(self):
        """gives the number of element in each dimension"""
        return self.data.shape
    
    def copy(self):
        """gives a copy of a Xdata instance"""
        data = self.data.copy()
        headers = []
        for h in self.headers:
            headers.append(h.copy())
        if self.data_descriptor.all_units is None:
            unit = None
        else:
            unit = []
            for i in self.data_descriptor.all_units:
                unit.append(i['unit'])
                unit.append(i['value'])
        return Xdata(self.name, data, headers, unit)
    
    def update_data(self, newdata):
        """Creating a new Xdata instance, with updated data and the same 
        headers as before (except for the length of some measure headers and
        undiferentiated headers)"""
        #checking the number of dimension
        if len(newdata.shape) != self.get_n_dimensions() :
            raise Exception("update_data method does not allow to change the "
                            "number of dimensions, please use "
                            "modify_dimensions method instead")
        #for each dimension, check if the number of element has chaged
        #if it has changed, make sure this change is allowed
        #if so, update the header
        newxdata = self.copy()
        for dim in range(self.get_n_dimensions()):
            if newdata.shape[dim] != self.headers[dim].n_elem :
                oldh = newxdata.headers[dim]
                if self.headers[dim].is_categorical_with_values:
                    raise Exception ("categorical headers with values can't "
                                     "have new not defined elements")
                elif self.headers[dim].is_undifferentiated:
                    n = newdata.shape[dim] - self.headers[dim].n_elem
                    if n > 0:
                        values = [pd.Series([])] * n
                        h = oldh.update_categoricalheader('new',
                                                          None,
                                                          values)
                        newxdata.headers[dim] = h
                    else : #the number element has decreased
                        ind = range(n)
                        h = oldh.update_categoricalheader('rm',
                                                          ind,
                                                          None)
                        newxdata.headers[dim] = h
                else : #the header is a measure header
                    h = oldh.update_measureheader(n_elem = newdata.shape[dim])
                    newxdata.headers[dim] = h
                    
        #once all headers are updated, update the data itself
        newxdata._data = newdata
        return (newxdata)
        
    def update_xdata(self, flag, dim, ind, dataslices, modified_header):
        """creates a new Xdata instance with the same attributes as the
        previous one, except for lines changed both in the data and the
        corresponding header"""
        if not isinstance(dim, int):
            raise Exception ("dim is of type int")
        elif (dim < 0) | (dim >= self.get_n_dimensions()):
            raise Exception ("dim must correspond to an existing dimension")
        ND = self.get_n_dimensions()
        oldheader = self.headers[dim]
        #for flag 'all' : the whole content of the header has been modified
        #dataslices is a numpy array with all the data
        #check that flag 'all' is not in fact a flag 'chgdata'
        if flag == 'all':
            #checking that ind is coherent
            if not ((ind is None) | (isinstance(ind, list))):
                raise Exception ("ind must be None, an empty list, or the list"
                                 " of all indices")
            #checking that modified_header is a Header
            if not isinstance(modified_header, Header):
                raise Exception("modified_header must be of type Header")
            #checking that flag is not in fact 'chgdata'
            #i.e. that the header has changed
            if oldheader == modified_header:
                flag = 'chgdata'
            #checking that dataslices can replace data
            if not isinstance(dataslices, np.ndarray):
                raise Exception ("dataslices must be a numpy array for a flag "
                "'all'")
            elif len(dataslices.shape)!= ND:         
                raise Exception ("dataslices must have the same number of "
                                 "dimensions as data")
            for n in range(ND):
                # 'all' flag does not change the number of elements in the
                #various dimensions except for the one that is being modified
                if n == dim:
                    if dataslices.shape[dim] != modified_header.n_elem:
                        raise Exception ("the new data and the new header must"
                                         " have the same number of elements in"
                                         " the concerned dimension")
                    elif modified_header.label != oldheader.label:
                        raise Exception ("label of the header can't be changed"
                                         " with this method")
                    elif self.headers[dim].is_measure:
                        if modified_header.unit != oldheader.unit:
                            raise Exception ("flag 'all' can't change the unit"
                            " of the header")
                        elif modified_header.all_units != oldheader.all_units:
                            raise Exception ("flag 'all' can't change the unit"
                            " of the header")
                else:
                    if dataslices.shape[n] != self.shape()[n]:
                        raise Exception ("'all' flag only allows one dimension"
                                         " to change its number of elements")
            newxdata = self.copy()
            newxdata._data = dataslices
            newxdata._headers[dim] = modified_header
            return (newxdata, flag)
        
        if flag == 'chgdata':
            #This flag is not supposed to be used execpt if the given flag was
            #'all' but the header was the same
            
            #header must be None or the same as the old one
            if not ((modified_header is None) | \
                    (modified_header == oldheader)):
                raise Exception ("'chgdata' flag can't change the header")
            if not ((ind is None) | (isinstance(ind, list))):
                raise Exception ("ind must be None, an empty list, or the list"
                                 " of all indices")
            elif not isinstance(dataslices, np.ndarray):
                raise Exception ("dataslices must be a numpy array for a flag "
                "'chgdata'")
            elif dataslices.shape != self.data.shape:
                raise Exception ("flag 'chgdata' can't change the dimensions "
                                 "nor number of elements in the dimensions")
            newxdata = self.copy()
            newxdata._data = dataslices
            return (newxdata, flag)
        
        elif flag == 'chg':
            #lets first check the header
            if not isinstance(modified_header, Header):
                raise Exception("modified_header must be of type Header")
            elif (modified_header.is_measure | \
                 modified_header.is_undifferentiated):
                if modified_header != oldheader:
                    raise Exception ("measure headers and undifferentiated "
                                     "ones can't be modified by a flag 'chg'")
            else: #then it's a categoricalwithvalues header
                if oldheader.n_elem != modified_header.n_elem:
                    raise Exception("'chg' flag can't change the number of "
                                    "elements in the dimension")
                elif oldheader.get_n_columns() != modified_header.get_n_columns():
                    raise Exception ("'chg' flag can't change the number of "
                                     "columns of the header")
                elif oldheader.get_all_units() != modified_header.get_all_units():
                    raise Exception ("'chg' flag can't change the units")
                elif oldheader.label != modified_header.label:
                    raise Exception("'chg' flag can't change labels")
                for i in range(oldheader.get_n_columns()):
                    if oldheader.column_descriptors[i].label != \
                       modified_header.column_descriptors[i].label:
                        raise Exception("'chg' flag can't change labels")
            #note : we didn't check that the values haven't changed for the 
            #lines that are not supposed to be modified in order to fasten the
            #update for huge sets of data. Such changes are usually done by
            #filters, that are tested to do the right thing
            
            #now lets check that ind and dataslices have correct type and same
            #length
            if not isinstance(ind, list):
                raise Exception("ind must be of type list")
            elif not isinstance(dataslices, list):
                raise Exception("dataslices must be of type list")
            elif len(ind) != len(dataslices):
                raise Exception("dataslices must have the same number of "
                                "element as ind")     
            newxdata = self.copy()
            changeslice  = [slice(None,None,None)] * (self.get_n_dimensions())
            for i in range(len(ind)):
                changeslice[dim] = ind[i]
                if not isinstance(ind[i], int):
                    raise Exception("all indices must be of type int")
                elif not isinstance(dataslices[i], np.ndarray):
                    raise Exception("all dataslices must be of type "
                                    "numpy.ndarray")
                elif len(dataslices[i].shape) != (len(self.data.shape) -1):
                    raise Exception ("dataslice doesn't have a correct shape")
                for j in range(len(dataslices[i].shape)):
                    if j<dim:
                        if dataslices[i].shape[j] != self.data.shape[j]:
                            raise Exception ("dataslice doesn't have a correct"
                                             " number of elements")
                    if j>dim:
                        if dataslices[i].shape[j] != self.data.shape[j + 1]:
                            raise Exception ("dataslice doesn't have a correct"
                                             " number of elements")
                #now lets modify the data ...
                newxdata._data[tuple(changeslice)] = dataslices[i]
            #...and replace the header
            newxdata._headers[dim] = modified_header
            return (newxdata, flag)
        
        
        elif flag == 'new':
            #lets first test ind
            if not (isinstance(ind, list) | (ind is None)):
                raise Exception("ind must be None, or an empty list, or the "
                                "list of new indices")
            #now lets check dataslices
            elif not isinstance(dataslices, list):
                raise Exception("dataslices must be of type list")
            for i in range(len(dataslices)):
                if not isinstance(dataslices[i], np.ndarray):
                    raise Exception("all dataslices must be of type "
                                    "numpy.ndarray")
                elif len(dataslices[i].shape) != (len(self.data.shape) -1):
                    raise Exception ("dataslice doesn't have a correct shape")
                for j in range(len(dataslices[i].shape)):
                    if j<dim:
                        if dataslices[i].shape[j] != self.data.shape[j]:
                            raise Exception ("dataslice doesn't have a correct"
                                             " number of elements")
                    if j>dim:
                        if dataslices[i].shape[j] != self.data.shape[j + 1]:
                            raise Exception ("dataslice doesn't have a correct"
                                             " number of elements")
            #now we check the header
            if not isinstance(modified_header, Header):
                raise Exception("modified_header must be of type Header")
            elif modified_header.is_measure != oldheader.is_measure |\
            modified_header.is_undifferentiated != oldheader.is_undifferentiated:
                raise Exception("header can't change its type with flag 'new'")
            if (modified_header.n_elem != oldheader.n_elem + len(dataslices)):
                    raise Exception ("the number of elements added in a "
                                     "dimension must be the same in data and "
                                     "in the header")
            if modified_header.is_categorical_with_values:
                if oldheader.get_n_columns() != modified_header.get_n_columns():
                    raise Exception ("'new' flag can't change the number of "
                                     "columns of the header")
                elif oldheader.get_all_units() != modified_header.get_all_units():
                    raise Exception ("'new' flag can't change the units")
                elif oldheader.label != modified_header.label:
                    raise Exception("'new' flag can't change labels")
                for i in range(oldheader.get_n_columns()):
                    if oldheader.column_descriptors[i].label != \
                       modified_header.column_descriptors[i].label:
                        raise Exception("'new' flag can't change labels")
            #note : we didn't check that the values haven't changed for the 
            #lines that are not supposed to be modified in order to fasten the
            #update for huge sets of data. Such changes are usually done by
            #filters, that are tested to do the right thing
            newxdata = self.copy()
            #Now lets replace the header
            newxdata._headers[dim] = modified_header
            #And recreate the data (can't change the size of a numpy array)
            shape = list(self.shape())
            shape[dim] += len(dataslices)
            newdataarray = np.zeros(tuple(shape))
            olddata = [slice(None, None, None)] * ND
            olddata[dim] = slice(0, self._headers[dim].n_elem, None)
            newxdata._data = newdataarray
            newxdata._data[tuple(olddata)] = self.data
            for i in range(len(dataslices)):
                newdata = olddata
                newdata[dim] = self._headers[dim].n_elem + i
                sliceofdata = np.array([dataslices[i]])
                newxdata._data[tuple(newdata)] = sliceofdata             
            return (newxdata, flag)

        elif flag == 'remove':
            #lets first check that ind and dataslices has correct type
            if not isinstance(ind, list):
                raise Exception("ind must be of type list")
            elif not ((dataslices is None) | (dataslices == [])):
                raise Exception("dataslices must be empty")
            for i in range(len(ind)):
                if not isinstance(ind[i], int):
                    raise Exception("all indices must be of type int")
            #now lets check the header and its number of elements
            if not isinstance(modified_header, Header):
                raise Exception("modified_header must be of type Header")
            elif modified_header.is_measure != oldheader.is_measure |\
            modified_header.is_undifferentiated != oldheader.is_undifferentiated:
                raise Exception("header can't change its type with flag "
                "'remove'")
            if (modified_header.n_elem != oldheader.n_elem - len(ind)):
                    raise Exception ("the number of elements removed in a "
                                     "dimension must be the same in data and "
                                     "in the header")
            if modified_header.is_categorical_with_values:
                if oldheader.get_n_columns() != modified_header.get_n_columns():
                    raise Exception ("'remove' flag can't change the number of"
                                     " columns of the header")
                elif oldheader.get_all_units() != modified_header.get_all_units():
                    raise Exception ("'remove' flag can't change the units")
                elif oldheader.label != modified_header.label:
                    raise Exception("'remove' flag can't change labels")
                for i in range(oldheader.get_n_columns()):
                    if oldheader.column_descriptors[i].label != \
                       modified_header.column_descriptors[i].label:
                        raise Exception("'remove' flag can't change labels")
            #note : we didn't check that the values haven't changed for the 
            #lines that are not supposed to be modified in order to fasten the
            #update for huge sets of data. Such changes are usually done by
            #filters, that are tested to do the right thing
            newxdata = self.copy()
            #Now lets replace the header
            newxdata._headers[dim] = modified_header
            newxdata._data = np.delete(newxdata._data, ind, dim)           
            return (newxdata, flag)
        
        elif flag == 'chg&new':
            #lets first check dataslices
            if not isinstance(dataslices, list):
                raise Exception ("dataslices must be a list of two elements: "
                                 "first the list of the lines that have "
                                 "changed, second the list of new lines")
            elif len(dataslices) != 2:
                raise Exception ("dataslices must be a list of two elements: "
                                 "first the list of the lines that have "
                                 "changed, second the list of new lines")
            elif not (isinstance(dataslices[0], list) & \
                      isinstance(dataslices[1], list)):
                raise Exception ("dataslices must be a list of two elements: "
                                 "first the list of the lines that have "
                                 "changed, second the list of new lines")
            #now lets check ind
            if not isinstance(ind, list):
                raise Exception ("ind must be the list of indices of the lines"
                                 " to be changed")
            elif isinstance(ind[0], list):
                if len(ind) != 2 :
                    raise Exception ("ind must be the list of indices of the "
                                     "lines to be changed")
                elif not ((ind[1] is None) | isinstance(ind[1], list)):
                    raise Exception ("the list of new lines to add must be "
                                     "empty,, None or the list of the indices")
                ind = ind[0]
            #now lets check the modified header and check that the length of 
            #the arguments is coherent
            if not isinstance(modified_header, Header):
                raise Exception("modified_header must be of type Header")
            elif modified_header.is_measure != oldheader.is_measure |\
            modified_header.is_undifferentiated != oldheader.is_undifferentiated:
                raise Exception("header can't change its type with flag "
                "'chg&new'")
            if (modified_header.n_elem != \
                oldheader.n_elem + len(dataslices[1])):
                    raise Exception ("the number of elements added in a "
                                     "dimension must be the same in data and "
                                     "in the header")
            if modified_header.is_categorical_with_values:
                if oldheader.get_n_columns() != modified_header.get_n_columns():
                    raise Exception ("'chg&new' flag can't change the number "
                                     "of columns of the header")
                elif oldheader.get_all_units() != modified_header.get_all_units():
                    raise Exception ("'chg&new' flag can't change the units")
                elif oldheader.label != modified_header.label:
                    raise Exception("'chg&new' flag can't change labels")
                for i in range(oldheader.get_n_columns()):
                    if oldheader.column_descriptors[i].label != \
                       modified_header.column_descriptors[i].label:
                        raise Exception("'chg&new' flag can't change labels")
            #note : we didn't check that the values haven't changed for the 
            #lines that are not supposed to be modified in order to fasten the
            #update for huge sets of data. Such changes are usually done by
            #filters, that are tested to do the right thing
            if len(ind) != len(dataslices[0]):
                raise Exception ("all changed slices must be given new values")
            
            newxdata = self.copy()
            newxdata._headers[dim] = modified_header
            shape = list(self.shape())
            shape[dim] += len(dataslices)
            newdataarray = np.zeros(tuple(shape))
            olddata = [slice(None, None, None)] * ND
            olddata[dim] = slice(0, self._headers[dim].n_elem, None)
            newxdata._data = newdataarray
            #lets copy the 'old' values
            newxdata._data[tuple(olddata)] = self.data
            #and change the lines before adding the new ones
            changeslice  = [slice(None,None,None)] * ND
            for i in range(len(ind)):
                changeslice[dim] = ind[i]
                if not isinstance(ind[i], int):
                    raise Exception("all indices must be of type int")
                elif not isinstance(dataslices[0][i], np.ndarray):
                    raise Exception("all dataslices must be of type "
                                    "numpy.ndarray")
                elif len(dataslices[0][i].shape) != (len(self.data.shape) -1):
                    raise Exception ("dataslice doesn't have a correct shape")
                for j in range(len(dataslices[0][i].shape)):
                    if j<dim:
                        if dataslices[0][i].shape[j] != self.data.shape[j]:
                            raise Exception ("dataslice doesn't have a correct"
                                             " number of elements")
                    if j>dim:
                        if dataslices[0][i].shape[j] != self.data.shape[j + 1]:
                            raise Exception ("dataslice doesn't have a correct"
                                             " number of elements")
                #slices and indices are correct, lets modify the data
                newxdata._data[tuple(changeslice)] = dataslices[0][i]
            #now lets add the new lines
            for i in range(len(dataslices[1])):
                if not isinstance(dataslices[1][i], np.ndarray):
                    raise Exception("all dataslices must be of type "
                                    "numpy.ndarray")
                elif len(dataslices[1][i].shape) != (len(self.data.shape) -1):
                    raise Exception ("dataslice doesn't have a correct shape")
                for j in range(len(dataslices[1][i].shape)):
                    if j<dim:
                        if dataslices[1][i].shape[j] != self.data.shape[j]:
                            raise Exception ("dataslice doesn't have a correct"
                                             " number of elements")
                    if j>dim:
                        if dataslices[1][i].shape[j] != self.data.shape[j + 1]:
                            raise Exception ("dataslice doesn't have a correct"
                                             " number of elements")
                
                newdata = olddata
                newdata[dim] = self._headers[dim].n_elem + i
                sliceofdata = np.array([dataslices[1][i]])
                newxdata._data[tuple(newdata)] = sliceofdata            
            return (newxdata, flag)
            
        elif flag == 'chg&rm':
            #lets first check dataslices
            if not isinstance(dataslices, list):
                raise Exception ("dataslices must be a list of the lines to "
                                 "change")
            #now lets check ind
            if (not isinstance(ind, list)) or \
               len(ind) != 2 or \
               (not isinstance(ind[0], list)) or \
               (not isinstance(ind[1], list)):
                raise Exception ("ind must be the list of the list of indices "
                                 "of the lines to be changed and the list of "
                                 "the lines to be removed")
            #now lets check the modified header and check that the length of 
            #the arguments is coherent
            if not isinstance(modified_header, Header):
                raise Exception("modified_header must be of type Header")
            elif modified_header.is_measure != oldheader.is_measure |\
            modified_header.is_undifferentiated != oldheader.is_undifferentiated:
                raise Exception("header can't change its type with flag "
                "'chg&rm'")
            if (modified_header.n_elem != \
                oldheader.n_elem - len(ind[1])):
                    raise Exception ("the number of elements removed in a "
                                     "dimension must be the same in data and "
                                     "in the header")
            if modified_header.is_categorical_with_values:
                if oldheader.get_n_columns() != modified_header.get_n_columns():
                    raise Exception ("'chg&rm' flag can't change the number "
                                     "of columns of the header")
                elif oldheader.get_all_units() != modified_header.get_all_units():
                    raise Exception ("'chg&rm' flag can't change the units")
                elif oldheader.label != modified_header.label:
                    raise Exception("'chg&rm' flag can't change labels")
                for i in range(oldheader.get_n_columns()):
                    if oldheader.column_descriptors[i].label != \
                       modified_header.column_descriptors[i].label:
                        raise Exception("'chg&rm' flag can't change labels")
            #note : we didn't check that the values haven't changed for the 
            #lines that are not supposed to be modified in order to fasten the
            #update for huge sets of data. Such changes are usually done by
            #filters, that are tested to do the right thing
            if len(ind[0]) != len(dataslices):
                raise Exception ("all changed slices must be given new values")
            
            newxdata = self.copy()
            newxdata._headers[dim] = modified_header
            #let's change the lines before removing some
            changeslice  = [slice(None,None,None)] * ND
            for i in range(len(ind)):
                changeslice[dim] = ind[0][i]
                if not isinstance(ind[0][i], int):
                    raise Exception("all indices must be of type int")
                elif not isinstance(dataslices[i], np.ndarray):
                    raise Exception("all dataslices must be of type "
                                    "numpy.ndarray")
                elif len(dataslices[i].shape) != (len(self.data.shape) -1):
                    raise Exception ("dataslice doesn't have a correct shape")
                for j in range(len(dataslices[i].shape)):
                    if j<dim:
                        if dataslices[i].shape[j] != self.data.shape[j]:
                            raise Exception ("dataslice doesn't have a correct"
                                             " number of elements")
                    if j>dim:
                        if dataslices[i].shape[j] != self.data.shape[j + 1]:
                            raise Exception ("dataslice doesn't have a correct"
                                             " number of elements")
                # slices and indices are correct, lets modify the data
                newxdata._data[tuple(changeslice)] = dataslices[i]
            # now lets remove the lines we don't want to keep
            newxdata._data = np.delete(newxdata._data, ind[1], dim)                
            return (newxdata, flag)
        elif flag == 'perm':
            # dataslices must be None, because all the values will be
            # calculated from the permutation
            if not dataslices is None:
                raise Exception("dataslices must be None for a 'perm' flag")
            # now let's check the Header
            if not isinstance(modified_header, Header):
                raise Exception("modified_header must be of type Header")
            elif (modified_header.is_measure | \
                 modified_header.is_undifferentiated):
                if modified_header != oldheader:
                    raise Exception ("measure headers and undifferentiated "
                                     "ones can't be modified by a flag 'perm'")
            else: #then it's a categoricalwithvalues header
                if oldheader.n_elem != modified_header.n_elem:
                    raise Exception("'perm' flag can't change the number of "
                                    "elements in the dimension")
                elif oldheader.get_n_columns() != modified_header.get_n_columns():
                    raise Exception ("'perm' flag can't change the number of "
                                     "columns of the header")
                elif oldheader.get_all_units() != modified_header.get_all_units():
                    raise Exception ("'perm' flag can't change the units")
                elif oldheader.label != modified_header.label:
                    raise Exception("'perm' flag can't change labels")
                for i in range(oldheader.get_n_columns()):
                    if oldheader.column_descriptors[i].label != \
                       modified_header.column_descriptors[i].label:
                        raise Exception("'perm' flag can't change labels")
            #note : we didn't check that the values haven't changed for the 
            #lines that are not supposed to be modified in order to fasten the
            #update for huge sets of data. Such changes are usually done by
            #filters, that are tested to do the right thing
            
            # now lets check that ind is a permutation of the indices of the
            # lines
            if len(ind) != self.headers[dim].n_elem:
                raise Exception ("ind is not a permutation of the indices")
            for i in range(self.headers[dim].n_elem):
                if not i in ind:
                    raise Exception ("ind is not a permutation of the indices")
            #now lets permute the data and replace the header
            newxdata = self.copy()
            newxdata._headers[dim] = modified_header
            permuteslice  = [slice(None,None,None)] * ND
            oldslice =  [slice(None,None,None)] * ND                 
            for i in range(len(ind)):
                if i != ind[i]:
                    # this test saves some time if not all the lines are
                    # permuted
                    permuteslice[dim]  = ind[i]
                    oldslice[dim] = i
                    newxdata._data[permuteslice] = self.data[oldslice]
            return (newxdata, flag)    
        # all accepted flags with this method are already taken care of
        # flag argument is either not a flag or not one accepted by this method
        raise Exception("flag must be 'all', 'chg', 'new', 'remove', 'perm' "
        "'chg&new' or 'chg&rm'")

        
def createDimensionDescription(label, column = None):
    """the function creates an instance of DimensionDescription.
    
    createDimensionDescription gives an instance of the class
    DimensionDescription from a label and an column of values of type
    pandas.core.series.Series.
    
    If column is None, the DimensionDescription instance will be of
    dimension_type 'mixed' by default.
    
    When using this function, no unit is specified, so
    dimensiondescription.unit will be None.
    
    Parameters
    ----------     
    - label:
        label for the DimensionDescription instance
        (type str)
    - column :
        values to determine the dimension_type of the DimensionDescription
        (type pandas.core.series.Series, shape (n,1))
    """
    if not isinstance(label,str):
        raise Exception("label must be of type str")
    #if no table of value is given:
    if column is None:
        return(DimensionDescription(label, 'mixed'))
    elif not isinstance(column, pd.core.series.Series):
        raise Exception("column must be of type pandas.core.series.Series")
    elif len(column.shape) != 1:
        raise Exception("column must be of shape (n,1)")
    #if a table of value is given, we must determine the dimension_type
    #we must check all the elements to make sure it is not a 'mixed' type
    dimension_type =  DimensionDescription.infertype(column[0])
    notmixed = True
    i = 0
    while notmixed and i < column.shape[0]:
          if dimension_type == DimensionDescription.infertype(column[i]):
              i += 1
          else:
              notmixed = False
    if notmixed:
        return (DimensionDescription(label, dimension_type))
    return (DimensionDescription(label, 'mixed'))


def check_bank(unit):
    """The functions checks if this unit is in one of the conversion tables of
    the bank. If so, it returns the conversion table, else, it returns None"""
    pass
    #TODO
    
    
def disp(obj):
    """generic disp method"""
    try:
        pprint(vars(obj))
    except:
        pprint(obj)
        
if __name__ == '__main__':
    c = MeasureHeader('toto',1,25,3,'s')


    class MyHeader:
        def __init__(self, label):
            self._label = label

        def check_header_update(self, new_header:MyHeader):
            # check that labels are preserved
            if new_header._label != self._label:
                raise Exception("new header must have the same label")