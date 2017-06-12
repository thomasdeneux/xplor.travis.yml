"""xdata module is a module to define data in the form of an ND array
XPLOR dataset is contained in a N dimensional array. The array contains the 
data itself, but the array also has headers. The headers contains this
informations about each of the dimensions : names, types, units, scale, ...
This module uses : 
        pandas as pd
        numpy as np
        operator
        abc
There are 3 classes in this module:
    
    - DimensionDescription : for a specific dimension, DimensionDescription 
                        stores a label,a dimensiontype ('numeric', 'logical',
                        'string', or 'mixed'), possibly a unit and the 
                        corresponding conversion table.
                        
                        It allows to determine the dimensiontype of an element,
                        and access the default value of a given dimensiontype.
                        
                        
    - Header : abstract class (subclasses are CategoricalHeader 
               and MeasureHeader). Headers contains informations about a
               dimension of the NDimensional data, such as a general label,
               the number of element, the description of the
               dimension/subdimensions, and allows to access the values to
               display on the axis.
               
    - CategoricalHeader : CategoricalHeader is a subclass of Header. It is used
                          to caracterize a dimension in which the data has no
                          regular organisation. It usually is a list of
                          elements. However, such elements can have interesting
                          features of different types. That's why such features
                          are stored in columns, each of them described by a
                          DimensionDescription object.
                          
    - MeasureHeader : MeasureHeader is a subclass of Header. It is used for
                      data aquired by equally spaced sample in a continous
                      dimension such as time or space. In wich case, their is
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
#itemgetter is used to sort a list of dictionary
from operator import itemgetter
#Header is abstract, subclasses are MeasureHeader and CategoricalHeader
from abc import ABC, abstractmethod
from pprint import pprint

        
class DimensionDescription:
    
    """ This class aims at defining a dimension.
    
    This class allows to define a dimension with a name, a type ('numeric,
    'logical', 'string', 'color' or 'mixed'), and possibly a unit for numerical 
    dimensions.
    
    Parameters
    ----------
    label : type : string (e.g. 'time')
            name for the dimension
    
     dimensiontype : values : 'numeric', 'logical', 'string', 'color' or 
                     'mixed'
     
     unit : type : string or list, optional (default value = None)
            One can define only the unit (e.g. mm) or the conversions as well
            in the form of a list (e.g. ['mm', 10**(-3), 'm', 1])
     
     
    Attributes
    ----------
    label : name of the dimension
    dimensiontype : 'numeric', 'logical', 'string', 'color' or 'mixed'
    unit : currently used unit
    allunit : list for unit conversions
      
    Methods
    -------
    infertype (x, getdefaultvalue=False) : static
              gives the dimensiontype of the x element and possibly the
              associated defaultvalue
    defaultvalue (dimensiontype) : gives the default value associated to 
              a certain dimensiontype
    Examples
    --------
     DimensionDescription(label,type,unit)
    
     tlabel = DimensionDescription('time','numeric',['s, 1, 'ms', 10**(-3),
                                               'min', 60, 'hour', 3600])
     clabel = DimensionDescription('condition','string')
     
     Note : 'color' DimensionDescription are using RGB 3-tupple
     
    """
    
    
    def __init__(self, 
                 label,
                 dimensiontype,
                 unit = None):
        """Constructor of the class DimensionDescription"""
        
        #Checking the arguments'types, raise an exception if it's not correct.
        #The label must be a string.
        if (not isinstance(label,str)):
            raise Exception('label must be a string')
        self._label = label
        #The dimensiontype must be 'numeric', 'logical', 'string, or 'mixed'.
        if not (dimensiontype in ['numeric', 'logical', 'string', 'color',
        'mixed']):
            raise Exception("a dimensiontype must be 'numeric', 'logical',"
            "'string', 'color' or 'mixed'")
        self._dimensiontype = dimensiontype
        #The unit is not compulsary (None for no unit).
        #However, only 'numeric' dimensions can have a unit.
        if (unit != None) & (dimensiontype != 'numeric'):
            raise Exception("only numeric DimensionDescriptions can have a"
            " unit")
        #The unit can be given in the form of a string ...
        elif (isinstance(unit,str)):
            self._unit = unit
            self._allunits = [{'unit' : unit, 'value' : 1.0}]
        #..or in the form of a list of linked units and conversion coefficients
        elif unit==[]:
            raise Exception("there must be at least one unit")
        elif (isinstance(unit,list)):
            lengthlist = len(unit)
            if lengthlist%2 != 0:
                raise Exception("unit must be a string with the unit symbol or"
                                " a list of the symbols of the unit followed"
                                "by the conversion indicator"
                                " (e.g. ['mm', 10**(-3), 'm', 1]")
            #One of the units must be the reference.
            #That means that one conversion coefficient must be equal to one.
            Reference = False
            self._allunits = []
            for i in range (0,lengthlist,2):
                #The name of the unit is always a string.
                if not isinstance(unit[i],str):
                    raise Exception("unit names must be strings")
                #The coefficient for conversion must be int or float.
                if not (isinstance(unit[i+1],float)) | \
                       (isinstance(unit[i+1],int)):
                    raise Exception("conversion coeffs must be of type float "
                    "or int")
                d = {'unit' : unit[i], 'value' : float(unit[i+1])}
                self._allunits += [d]
                if unit[i+1] == 1:
                    #A reference unit has been defined.
                    Reference = True
                    self._unit = unit[i]
            if not Reference:
                raise Exception("one of the conversion coefficients must be "
                "equal to one to define a reference")
            #The list of units with conversion coefficients is sorted.
            self._allunits.sort(key=itemgetter('value'))
        #Checking if the type of unit is either str, list or if it is None.
        elif (unit != None):
            raise Exception("unit must be a string with the unit symbol or a "
            "list  of the symbols of the unit followed by the conversion "
            "indicator (e.g. ['mm', 10**(-3), 'm', 1]")
        else:
            self._unit = None
            self._allunits = None
                
                
    #Attributes label, dimensiontype, unit and allunits can be seen but not 
    #modified outside of the class (only get methods, no setters).
    @property
    def label(self):
        return self._label
    
    @property
    def dimensiontype(self):
        return self._dimensiontype
    
    @property
    def unit(self):
        return self._unit
    
    @property
    def allunits(self):
        return self._allunits
    
    #Determining the dimension type from some data.
    @staticmethod
    def infertype(x, getdefaultvalue=False):
        """infertype is a static method to access the dimensiontype of an
        element x and if required, the associated default value"""
        dimtype = 'mixed'
        if isinstance(x,bool):
            dimtype = 'logical'
        elif isinstance(x,str):
            dimtype = 'string'
        elif type(x) in [int, float, complex]:
            dimtype = 'numeric'
        elif isinstance(x, tuple):
            if len(x)==3 :
                if ((type(x[0]) == type(x[1]) == type(x[2]) == int) & \
                x[0] < 256 & x[1] < 256 & x[2] < 256 & \
                (x[0] > 0) & (x[1] > 0) & (x[2] > 0)):
                    dimtype = 'color'               
        if getdefaultvalue:
            return (dimtype,DimensionDescription.defaultvalue(dimtype))
        else:
            return dimtype
    
    #Calculating a default value for the differents dimensiontypes.
    @staticmethod
    def defaultvalue(dimensiontype):
        """defaultvalue is a static method to access the default value of a
        given dimensiontype"""
        if dimensiontype == 'numeric':
            return 0
        elif dimensiontype == 'logical':
            return False
        elif dimensiontype == 'string':
            return ''
        elif dimensiontype == 'color':
            return (0, 149, 182)
            #it is a nice color, different from that of the background
        elif dimensiontype == 'mixed':
            return None
        else:
            raise Exception("This function only gives the default value for"
            " the following types: 'numeric', 'logical', 'string', 'color' or"
            " 'mixed'")






    
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
    continous dimension such as time or space. In wich case, there is only one
    subdimension (i.e. only one column witch is not stored).
    
    
    Parameters
    ----------     
     
    Attributes
    ----------
    - label : name of the dimension
    - column_descriptors : list of the DimensionDescription of each of the 
                           columns of values
    
    Properties
    ----------
    - ismeasure : true if the header is a MeasureHeader instance, false if it
                  is a CategoricalHeader instance
    - iscategoricalwithvalues : true if it is an instance of CategoricalHeader
                                and that values is not None. If it is a
                                categorical header but with no column or a
                                measure header, it is false.
    - isundifferentiated : true if it is a categorical header with no values
                      (not iscategoricalwithvalues)
      
    Methods
    -------           
    (abstract methods)    
    - n_elem : number of element in the column(s)/ number of samples
    - iscategorical : differentiate measure and categorical headers for the
                      properties ismeasure, iscategoricalwithvalues and
                      isundifferentiated
    - __eq__ : compares all the fields of the headers
               (returns True if all the fields are the same)
               it can be used by writting header1 == header2
    - getncolumns : gives the number of columns
                    (1 for MeasureHeader, 0 to n for CategoricalHeader)
    - getunits : gives the list of the unit used for each column
                 ('no unit' is returned for each column with no specified unit)
    - getallunits : gives the list of conversion table for each column
                ('no unit' is returned for each column with no specified unit)
    - disp : gives the main attributes of a Header
    - getvalue : (self, nline, column = None)
                 gives the value located at the line nline and at the column
                 column (defined by it's label or it's number) or the fist one.
                 Since we use pyhton, we have decided that to access the first
                 element of the column, nline must be equal to 0.
    - get_itemname :  (self, nline)
                nline can here be an integer or a list of integer.
                the function returns the corresponding values of the first
                column
                
    (non abstract method)
    - check_header_update: (self, flag, ind, newheader)
                            flag : 'all', 'chgdim', 'new', 'remove', 'chg',
                                   'chg&new' or 'chg&rm'
                            ind : numpy.array of shape (n,)
                            basics checks when updating data and giving a new
                            header
        
    Examples
    --------
     CategorialHeader: (with values)
         label : 'fruits'
         column_descriptors : (list of DimensionDescriptors, simplified here)
             1/ label : 'fruits', dimensiontype : 'string', no unit
             2/ label : 'prices', dimensiontype : 'numeric', unit : 'euros/kg'
             3/ label : 'color', dimensiontype : 'string', no unit
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
        
    CategorialHeader: (undifferentiated)
         label : 'fruits'
         column_descriptors : (list of DimensionDescriptors)
                 None
         n_elem : 4
         values : None
            
                         fruits
                                   
                        |fruits |
                        |_______|
                        |   1   |    
                        |   2   |
                        |   3   |
                        |   4   |
        
    MeasureHeader:
        label : 'x'
        column_descriptors : (list of one DimensionDescription)
            label : 'x', 
            dimensiontype : 'numeric',
            unit : 'mm',
            allunits : [{unit : 'mm', 'value' : 10**(-3)},
                         {unit : 'm', 'value' : 1}]
        n-elem : 4
        start : 1
        scale : 2
        
                                     x
                                    
                                   | x |
                                   |___|
                                   | 1 |
                                   | 3 |
                                   | 5 |
                                   | 7 |
     
    """
    #Attributes label and column_descriptors can be seen but not modified
    #outside of the class (only get methods, no setters).
    @property
    def label(self):
        """general label of the header"""
        return self._label
    
    @property
    def column_descriptors(self):
        """list of DimensionDescription instances describing each column"""
        return self._column_descriptors
    
    #Properties ismeasure, isundifferentiated, iscategoricalwithvalues help to
    #differenciate different types of headers faster in other modules
    @property
    def ismeasure(self):
        """fast way to differenciate measure headers from categorical ones"""
        return not self.iscategorical
    
    @property    
    def iscategoricalwithvalues(self):
        """fast way to test if a header is categorical with values
        (ie list of elements)"""
        return self.iscategorical and self.getncolumns>0

    @property    
    def isundifferentiated(self):
        """fast way to test if a header is categorical with no values"""
        return self.iscategorical and self.getncolumns==0
                
    #method
    def check_header_update(self, flag, ind, newheader):
        """basics checks when updating data and giving a new header"""
        #check types of parameters
        if not isinstance(newheader, Header):
            raise Exception("newheader must be a header")
        elif not flag in ['all', 'chgdim', 'new', 'remove', 'chg', 'chg&new',
                          'chg&rrm']:
            raise Exception("flags can be : 'all', 'chgdim', 'new', 'remove', "
            "'chg', 'chg&new' or 'chg&rm'")
        elif not isinstance(ind, np.array):
            raise Exception ("ind must be of type numpy.array")
        elif len(ind.shape) != 1:
            raise Exception("ind must be of shape (n,)")
        if flag != 'chgdim':
            #only 'chgdim' flags allow to change the type of the header
            # and/or change the various labels
            
            #check that the types are coherent
            if self.iscategorical != newheader.iscategorical:
                raise Exception("both headers must be of same type")
            #check that labels are preserved
            if self._label != newheader._label:
                raise Exception ("both headers must have the same label")
            for column in range (len(self._column_descriptors)):
                if self._column_descriptors[column].label != \
                    newheader._column_descriptores[column].label:
                        raise Exception ("sublabels are not preserved")
            #only 'all' and 'chgdim' flag allows to change n_elem as we want
            if flag == 'new':
                if newheader.n_elem != self._n_elem + ind.size:
                    raise Exception ("the new headers has the wrong number of "
                                     "elements")
            elif flag == 'chg':
                if newheader.n_elem != self._n_elem:
                    raise Exception ("both headers must have the same number "
                                         "of elements")
            elif flag == 'remove':
                if newheader.n_elem != self._n_elem - ind.size:
                    raise Exception ("the new headers has the wrong number of "
                                     "elements")
            #'chg&new' and 'chg&rm' flags impose ind to be an array of array
            #with the first element being the array of indices to be changed
            #and the second element being an array of new indices
            elif flag == 'chg&new':
                if newheader.n_elem != self._n_elem + ind[0][1].size:
                    raise Exception ("the new headers has the wrong number of "
                                     "elements")
            elif flag == 'chg&rm':
                if newheader.n_elem != self._n_elem + ind[0][1].size:
                    raise Exception ("the new headers has the wrong number of "
                                     "elements")
    
    
    
    
    #abstract methods
    @abstractmethod
    def n_elem(self):
        """gives the the number of elements/samples in that dimension"""
        pass
   
    @abstractmethod
    def iscategorical(self):
        """used for the properties ismeasure, iscategoricalwithvalues and
        isundifferentiated, fast way to differenciate categorical and measure
        headers"""
        pass
    
    @abstractmethod
    def __eq__(self, other):
        """Override the default Equals behavior"""
        pass
    
    @abstractmethod
    def getncolumns(self):
        """returns the number of columns"""
        pass

    @abstractmethod
    def getunits(self):
        """gives a list of the units of all the columns"""
        pass
    
    @abstractmethod
    def getallunits(self):
        """gives a list of the conversion tables for the units of all the
        columns"""
        pass
            
    @abstractmethod
    def disp(self):
        """display some information about the haeder"""
        pass
    
    @abstractmethod
    def getvalue(self, line, column = None):
        """get the value of the line of number line of the column column
        (defined by it's label or number) or the first column"""
        pass
    
    @abstractmethod
    def get_itemname(self, nline):
        """get the value(s) of the line(s) in nline (it can be an int or a list
        of int), of the first column"""
        pass



class CategoricalHeader(Header):
    """ This class allows the creation of a header for a categorical dimensions
    of a dataset.
    
    CategoricalHeader is used for categorical dimensions of a dataset. This
    means that this dimension is either not continuous or that the data has not
    been collected regularly in this dimension. Therefore, their is no scale,
    measure for this dimension. It is more a collection of objects.
    
    A CategoricalHeader has a general label as well as one or several
    DimensionDescription objects stored in column_descriptorss to describe each
    of the features. For each feature, values can be given (e.g. for 'fruits'
    values would be 'apple', 'pear', 'blueberry', 'watermelon'...) or be a list
    of numbers. The first case corresponds to 'iscategoricalwithvalues', the
    second to 'isundifferentiated'
    
    
    
    Parameters
    ----------     
    - label: name of the header
            type : str
    - column_descriptors : (optional,
                            the case with no column is possible.
                            the legend would then be a list of int [1, 2, ...]
                            it is undifferentiated)
            type : str, DimensionDescription or a list of such elements
            description of the dimension of each feature
    - n_elem : (optional if values is specified)
            type : int
            number of element in the column(s)
    - values : (otional if it is just undifferentiated series of measures and
                that n_elem is given)
            type : DataFrame from pandas (pandas.core.frame.DataFrame) of shape
            (n_elem, len(column_descriptors))
            content of the various subdimensions
    
    Attributes
    ----------
    - label : name of the dimension (str)
    - column_descriptors : list of the DimensionDescription of each of the 
            columns of values
    - values : content of the various subdimensions (pandas DataFrame
            (pandas.core.frame.DataFrame)of shape
            (n_elem, len(column_descriptors))
      
    Methods
    -------  
    (methods imposed by inheritance)
    - n_elem : number of element in the column(s)/ number of samples
               number of lines of values
    - iscategorical : differentiate measure and categorical headers for the
                      properties ismeasure, iscategoricalwithvalues and
                      isundifferentiated
    - iscategorical : returns True since it is the class CategoricalHeader
    - __eq__ : compares all the fields of the headers
               (returns True if all the fields are the same)
               it can be used by writting header1 == header2
    - getncolumns : gives the number of columns
                    (1 for MeasureHeader, 0 to n for CategoricalHeader)
    - getunits : gives the list of the unit used for each column
                 ('no unit' is returned for each column with no specified unit)
    - getallunits : gives the list of conversion table for each column
                ('no unit' is returned for each column with no specified unit)
    - disp : gives the main attributes of a Header
    - getvalue : (self, nline, column = None)
                 gives the value located at the line nline and at the column
                 column (defined by it's label or it's number) or the fist one.
                 Since we use pyhton, we have decided that to access the first
                 element of the column, nline must be equal to 0.
    - get_itemname :  (self, nline)
                nline can here be an integer or a list of integer.
                the function returns the corresponding values of the first
                column
    
    (other methods)
    - updatefromselection : TODO
                
    Example
    --------
    (with values)
         label : 'fruits'
         column_descriptors : (list of DimensionDescriptors, simplified here)
             1/ label : 'fruits', dimensiontype : 'string', no unit
             2/ label : 'prices', dimensiontype : 'numeric', unit : 'euros/kg'
             3/ label : 'color', dimensiontype : 'string', no unit
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
         column_descriptors : (list of DimensionDescriptors, simplified here)
                              []
         n_elem : 4
         values : None
            
                         fruits
                                   
                        |fruits |
                        |_______|
                        |   1   |    
                        |   2   |
                        |   3   |
                        |   4   |
 
    """
    
    def __init__(self,
                 label,
                 column_descriptors = None,
                 n_elem = None,
                 values = None):
        
        """Constructor of the class CategoricalHeader"""
        #label is not optional and must be of type string
        #label can be different from the labels of the columns
        if not (isinstance(label,str)):
            raise Exception("The header's label must be of type str")
        self._label = label
        #if values is None, so is column_descriptors, but we must have n_elem
        if values is None:
            if n_elem is None:
                raise Exception("if no value is given, n_elem must be given")
            elif not isinstance(n_elem, int):
                raise Exception("n_elem must be of type int")
            if (not column_descriptors is None) | column_descriptors == []:
                raise Exception("if there is no values, there are no columns"
                                " to be described")
            self._values = pd.DataFrame(np.zeros((n_elem, 0)))
            self._column_descriptors = None
        elif not isinstance(values, pd.core.frame.DataFrame):
            raise Exception("values must be a pandas DataFrame")
        else :
            #values is a DataFrame
            #we have to check that it has the correct shape
            #however, labels of the dataframe will not be taken into
            #consideration correspond
            if isinstance(n_elem, int):
                if not n_elem == values.shape[0]:
                    raise Exception("n_elem is not coherent with shape of values")
            elif not n_elem is None:
                raise Exception("n_elem must but of type int")
            #n_elem is either not given or correspond to the number of lines of the
            #dataframe
            #now let's check that values and column_descriptors are size coherent
            if isinstance(column_descriptors, str) | \
                         isinstance(column_descriptors, DimensionDescription):
                column_descriptors = [column_descriptors]
            elif not isinstance(column_descriptors, list):
                raise Exception ("column_descriptors must be of type str, "
                                 "DimensionDescription or a list of such elements")
            #column_descriptors is now a list
            if len(column_descriptors) != values.shape[1]:
                raise Exception ("column_descriptors and values must have the same"
                                 " length")
            self._values = values
            self._column_descriptors = []
            for i in range (len(column_descriptors)):
                if isinstance(column_descriptors[i], str):
                    dimdescription = \
                    createDimensionDescription(column_descriptors[i], values[i])
                    self._column_descriptors += [dimdescription]
                elif isinstance(column_descriptors[i], DimensionDescription):
                    for e in range (values.shape[0]):
                        #/!\dataframe[column][line]
                        if DimensionDescription.infertype(values[i][e]) != \
                        column_descriptors.dimensiontype :
                            raise Exception("dimensiontypes of column_descriptors "
                                            "must be coherent with the data in "
                                            "values")
                    self._column_descriptors += [column_descriptors[i]]
                else:
                    raise Exception("all column_descriptors elements must be "
                                    "either of type str or DimensionDescription")
        

    #private property but with get access
    @property
    def n_elem(self):
        """number of elements/samples in that dimension, line number of values
        """
        return self.values.shape[0]
   
    @property
    def iscategorical(self):
        """CategoricalHeader instances are all categorical"""
        return True
    
    @property
    def values(self):
        """values is a pandas DataFrame"""
        return self._values
    
    #methods
    def __eq__(self, other):
        """Override the default Equals behavior"""
        #the two headers must have the same type
        if not isinstance(other, CategoricalHeader):
            return False
        #the label must be the same
        if self._label != other._label:
            return False
        #the column_descriptors must be the same
        if len(self._column_descriptors) != len(other._column_descriptors):
            return False
        for i in range (len(self._column_descriptors)) :
            selfdescriptor =  self._column_descriptors[i]
            otherdescriptor = other._column_descriptors[i]
            if selfdescriptor.label != otherdescriptor.label :
                return False
            if selfdescriptor.dimensiontype != otherdescriptor.dimensiontype :
                return False
            if selfdescriptor.unit != otherdescriptor.unit :
                return False
            if selfdescriptor.allunits != otherdescriptor.allunits :
                return False
        #the content of values must be the same
        if self._values.shape != other._values.shape :
            return False
        for column in range (self._values.shape[1]):
            for line in range (self._values.shape[0]):
                if self._values[column][line] != other._values[column][line]:
                    return False
        return True
        
    def getncolumns(self):
        """returns the number of columns"""
        if self._colum_descriptors is None:
            return 0
        return (len(self._column_descriptors))

    def getunits(self):
        """gives a list of the units of all the columns"""
        units = []
        for dimensiondescription in self._column_descriptors:
            if dimensiondescription.unit == None:
                units += 'no unit'
            else:
                units += dimensiondescription.unit
        return units
    
    def getallunits(self):
        """gives a list of the conversion tables for the units of all the
        columns"""
        allunits = []
        for dimensiondescription in self._column_descriptors:
            if dimensiondescription.unit == None:
                allunits += 'no unit'
            else:
                allunits += dimensiondescription.allunits
        return allunits
    
    def disp(self):
        """display some information about the haeder"""
        print ("CategoricalHeader : " + self._label)
        print ("columns:")
        columns = self._column_descriptors
        for i in range (self.getncolumns()):
            label = str(columns[i].label)
            if columns[i].unit == None :
                unit = ''
            else:
                unit = ' ('+ columns[i].unit+ ')'
            print (label + unit)
    
    def getvalue(self, line, column = None):
        """get the value of the line of number line of the column defined by 
        column"""
        if not isinstance(line, int):
            raise Exception("line must be of type int")
        if line >= self.n_elem() | line < 0:
            raise Exception("line must be in [0, n_elem[")
        if column is None :
            column = 1
        if isinstance(column, int):
            if column == 1 and self.getncolumns() == 0:
                #nline must be 0 to have the first elem of a list in python.
                #but if there is no column, we want to strat counting from 1
                return (line + 1)
            if column >= self.getncolumns() | column < 0:
                raise Exception("column is a str or an int in [0, n_col[")
            return (self._values[column][line])
        elif not isinstance(column, str):
            raise Exception ("column is either the label of a column or it's"
            "number (int)")
        #if it is a string
        count = 0
        for dimdescriptor in self._column_descriptors:
            if dimdescriptor.label == column:
                return self._value[count][line]
            count += 1
        raise Exception("column is either the label of a column or it's"
            "number (int)")
    
    def get_itemname(self, line):
        """get the value(s) of the line(s) in nline (it can be an int or a list
        of int), of the first column"""
        #this function is the same for both the headers, but it could be
        #modified to choose witch column we want for categorical headers
        if isinstance(line, int):
            if line >= self.n_elem() | line < 0:
                raise Exception("nline must be in [0, n_elem[")
            return (self.getvalue(line))
        elif isinstance(line, list):
            itemnames = []
            for n in line:
                if not isinstance(n,int):
                    raise Exception("all line numbers must be integers")
                itemnames += [self.getvalue(n)]
            return itemnames
        raise Exception("nline must be an int or a list of int")

        
                  
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
            type : str
    - start : 
            type : float or int
            first value of this dimension
    - n_elem :
            type : int
            number of element in the column
    - scale :
            type : float or int
            interval between the values of this dimension
    - unit : (optional)
            type : str or list
            One can define only the unit (e.g. mm) or the conversions as well
            in the form of a list (e.g. ['mm', 10**(-3), 'm', 1])
    - checkbank : (optional)
                Default value of checkbank is Flase. If is it True, a unit must
                be specified, in order to check in the bank of conversion
                tables if one exists for the given unit.
    - column_descriptors : (optional)
            type : DimensionDescription
            description of the dimension
            it's label must be the same as the general label
    
    
    Attributes
    ----------
    - label : name of the dimension (str)
    - column_descriptors : list of one DimensionDescription instance
    - start : first value of this dimension (float)
    - scale : interval between the values of this dimension (float)
      
    Methods
    -------          
    (methods imposed by inheritance)
    - n_elem : number of element in the column(s)/ number of samples
    - iscategorical : differentiate measure and categorical headers for the
                      properties ismeasure, iscategoricalwithvalues and
                      isundifferentiated    
    - __eq__ : compares all the fields of the headers
               (returns True if all the fields are the same)
               it can be used by writting header1 == header2
    - getncolumns : gives the number of columns
                    (1 for MeasureHeader, 0 to n for CategoricalHeader)
    - getunits : gives the list of the unit used for each column
                 ('no unit' is returned for each column with no specified unit)
    - getallunits : gives the list of conversion table for each column
                ('no unit' is returned for each column with no specified unit)
    - disp : gives the main attributes of a Header
    - getvalue : (self, nline, column = None)
                 gives the value located at the line nline and at the column
                 column (defined by it's label or it's number) or the fist one.
                 Since we use pyhton, we have decided that to access the first
                 element of the column, nline must be equal to 0.
    - get_itemname :  (self, nline)
                nline can here be an integer or a list of integer.
                the function returns the corresponding values of the first
                column
                
    (other methods)
    - update_measureheader : (start = None, n_elem = None,scale = None)
                             creates a new measure header from the attributes
                             of a previous one, and the specified changes
        
    
    Example
    --------
        label : 'x'
        column_descriptors : (list of one DimensionDescription)
            label : 'x', 
            dimensiontype : 'numeric',
            unit : 'mm',
            allunits : [{unit : 'mm', 'value' : 10**(-3)},
                         {unit : 'm', 'value' : 1}]
        n-elem : 4
        start : 1
        scale : 1
        
                                     x
                                    
                                   | x |
                                   |___|
                                   | 1 |
                                   | 2 |
                                   | 3 |
                                   | 4 |
     
     
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
        #label must be of type str
        if  not isinstance(label,str):
            raise Exception("label must be of type str")
        self._label = label
        #start must be of type int or float
        if not (isinstance(start, float) | isinstance(start, int)):
            raise Exception("start must be of type float or int")
        self._start = float(start)
        #n_elem must be of type int
        if not isinstance(n_elem, int):
            raise Exception ("n_elem must be of type int")
        self._n_elem = n_elem
        #scale must be of type int or float
        if not (isinstance(scale, float) | isinstance(scale, int)):
            raise Exception("scale must be of type float or int")
        self._scale = float(scale)
        #case with a column_descriptors parameter
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
            "DimensionDescription")
        elif not isinstance(checkbank, bool) :
            raise Exception("checkbank must be a boolean")
        elif unit is None:
            if checkbank:
                raise Exception ("Specify a unit so as to checkout the bank")
            dimdescription = DimensionDescription(label, 'numeric')
            self._column_descriptors = [dimdescription]
        elif isinstance(unit,str) | isinstance(unit,list):
            if checkbank:
                allunits = check_bank(unit)
                if allunits is None:
                    dimdescription = DimensionDescription(label,
                                                      'numeric',
                                                      unit)
                else:
                    units = []
                    for dico in allunits:
                        units += [dico['unit'], dico['value']]
                dimdescription = DimensionDescription(label,
                                                      'numeric',
                                                      units)
            else:
                dimdescription = DimensionDescription(label, 'numeric', unit)
            self._column_descriptors = [dimdescription]
        else :
            raise Exception ("unit must be a str or a list")


    #private property but with get access   
    @property
    def iscategorical(self):
        return False
    
    @property
    def start(self):
        return self._start
    
    @property
    def scale(self):
        return self._scale
    
    @property
    def n_elem(self):
        return self._n_elem 

    
    #methods
    def __eq__(self, other):
        """Override the default Equals behavior"""
        #the two headers must have the same type
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
        if selfdescriptor.dimensiontype != otherdescriptor.dimensiontype :
            return False
        if selfdescriptor.unit != otherdescriptor.unit :
            return False
        if selfdescriptor.allunits != otherdescriptor.allunits :
            return False
        return True
        
    def getncolumns(self):
        """returns the number of columns"""
        return (1)    
    
    def getunits(self):
        """gives the unit if it exist, in the form of a list to be compatible
        with CategoricalHeaders"""
        if self._column_descriptors[0].unit == None:
            return (['no unit'])
        return ([self._column_descriptors[0].unit])
    
    def getallunits(self):
        """gives the conversion tables in the form of a list with a single
        element to be compatible with Categorical headers"""
        if self._column_descriptors[0].unit == None:
            return (['no unit'])
        return ([self._column_descriptors[0].allunits])
    
    def disp(self):
        """display some information about the haeder"""
        print ("MeasureHeader : " + self._label)
        print ("unit : " + self.getunits()[0])
        print ("start : " + str(self._start))
        print ("scale : " + str(self._scale))
        print ("n_elem : " + str(self._n_elem))
    
    def getvalue(self, line, column = None):
        """get the value of the line of number line of the first column"""
        if not (column is None or column == 1):
            raise Exception ("Measure headers have only one column, column"
            "argument must be None or 1")
        if not isinstance(line, int):
            raise Exception("line must be of type int")
        if line >= self._n_elem or line < 0:
            raise Exception("line must be in [0, n_elem[")
        #Since we use pyhton, we have decided that to access the first element
        #of the column, line must be equal to 0.
        return (self._start + line * self._scale)
    
    def get_itemname(self, nline):
        """get the value(s) of the line(s) in nline (it can be an int or a list
        of int), of the first column"""
        if isinstance(nline, int):
            if nline >= self._n_elem | nline < 0:
                raise Exception("nline must be in [0, n_elem[")
            return (self.getvalue(nline))
        elif isinstance(nline, list):
            itemnames = []
            for n in nline:
                if not isinstance(n,int):
                    raise Exception("all line numbers must be integers")
                elif n >= self._n_elem | n < 0:
                    raise Exception("nline must be in [0, n_elem[")
                itemnames += [self.getvalue(n)]
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

##class Xdata:
#    """This class allows the creation of a ND dataset, with headers for each
#    dimension and a name.
#    
#    Xdata is used to store the data. This means an ND (N dimensional) array
#    with all the values, as well as a list of headers describing each of the N
#    dimensions and a name for the whole set of data.
#    It also includes a handeling of event.
#    TODO : explain better the event part
#    
#    
#    Parameters
#    ----------     
#    - data : N dimensional array with the data itself
#    - headers : list of the headers describing each of the N dimensions
#            (list of Header or ???????)
#    - name : name of the dataset (str)
#    
#    Attributes
#    ----------
#    - data : N dimensional array with the data itself
#    - headers : list of the headers describing each of the N dimensions
#            (list of Header)
#    - name : name of the dataset (str)
#    
#    Methods
#    -------
#    TODO
#    
#    Examples
#    --------
#    TODO
#    """
#"""    def __init__(self,
#                 data,
#                 headers,
#                 name)"""
#    """Constructor of the class Xdata"""
    

                
def createDimensionDescription(label, column = None):
    """the function creates an instance of DimensionDescription.
    
    createDimensionDescription gives an instance of the class
    DimensionDescription from a label and an column of values of type
    pandas.core.series.Series.
    
    If column is None, the DimensionDescription instance will be of
    dimensiontype 'mixed' by default.
    
    When using this function, no unit is specified, so
    dimensiondescription.unit will be None.
    
    Parameters
    ----------     
    - label: type str
    - column : type pandas.core.series.Series, shape (n,1)
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
    #if a table of value is given, we must determine the dimensiontype
    #we must check all the elements to make sure it is not a 'mixed' type
    dimensiontype =  DimensionDescription.infertype(column[0])
    notmixed = True
    i = 0
    while notmixed and i < column.shape[0]:
          if dimensiontype == DimensionDescription.infertype(column[i]):
              i += 1
          else:
              notmixed = False
    if notmixed:
        return (DimensionDescription(label, dimensiontype))
    return (DimensionDescription(label, 'mixed'))


def check_bank(unit):
    """The functions checks if this unit is in one of the conversion tables of
    the bank. If so, it returns the conversion table, else, it returns None"""
    pass
    #TODO
    
    
def disp(obj):
    try:
        pprint(vars(obj))
    except:
        pprint(obj)