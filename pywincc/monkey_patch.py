"""
This is a monkey patch to fix a WinCCOLEDBPRovider and adodbapi issue.
The WinCC Provider does not provide some information the adodbapi expects.
This patch was accepted by the adodbapi maintainer and is now in the
development branch.
http://sourceforge.net/p/adodbapi/code/ci/fe567730985dd27df1ad8708da96c3d6a75527e9/
Once a new adodbapi version is released this patch may be omitted.
"""
import adodbapi
from adodbapi.adodbapi import make_COM_connecter, getIndexedValue,\
     defaultCursorLocation, defaultIsolationLevel
import adodbapi.apibase as api
import pywintypes


verbose = adodbapi.verbose
version = adodbapi.version


def monkey_connect(self, kwargs, connection_maker=make_COM_connecter):
    if verbose > 9:
        print('kwargs=', repr(kwargs))
    try:
        self.connection_string = kwargs['connection_string'] % kwargs # insert keyword arguments
    except (Exception), e:
        self._raiseConnectionError(KeyError,'Python string format error in connection string->')
    self.timeout = kwargs.get('timeout', 30)
    self.kwargs = kwargs
    if verbose:
        print '%s attempting: "%s"' % (version, self.connection_string)
    self.connector = connection_maker()
    self.connector.ConnectionTimeout = self.timeout
    self.connector.ConnectionString = self.connection_string

    try:
        self.connector.Open()  # Open the ADO connection
    except api.Error:
        self._raiseConnectionError(api.DatabaseError, 'ADO error trying to Open=%s' % self.connection_string)

    try:
        if getIndexedValue(self.connector.Properties,'Transaction DDL').Value != 0:
            self.supportsTransactions=True
    except pywintypes.com_error:
        # print type(e), e
        pass
    self.dbms_name = getIndexedValue(self.connector.Properties,'DBMS Name').Value
    try:
        self.dbms_version = getIndexedValue(self.connector.Properties,'DBMS Version').Value
    except pywintypes.com_error:
        pass
    self.connector.CursorLocation = defaultCursorLocation #v2.1 Rose
    if self.supportsTransactions:
        self.connector.IsolationLevel=defaultIsolationLevel
        self._autocommit = bool(kwargs.get('autocommit', False))
        if not self._autocommit:
            self.transaction_level = self.connector.BeginTrans() #Disables autocommit & inits transaction_level
    else:
        self._autocommit = True
    if 'paramstyle' in kwargs:
        self.paramstyle = kwargs['paramstyle'] # let setattr do the error checking
    self.messages=[]
    if verbose:
        print 'adodbapi New connection at %X' % id(self)

adodbapi.Connection.connect = monkey_connect


def adodbapi_SQLrow__unicode__(self):
    """Extend adodbapi's SQLrow class with an __unicod__ function.
    This is just a copy of the str method where I replaced the two occurences of 'str' by 'unicode'."""    
    return unicode(tuple(unicode(self._getValue(i)) for i in range(self.rows.numberOfColumns)))

def adodbapi_SQLrow__str__(self):
    """Overwrite adodbapi's SQLrow classes __str__ function to fix unicode errors when attempting to print it"""
    return unicode(self).encode('utf-8')

adodbapi.SQLrow.__unicode__ = adodbapi_SQLrow__unicode__
adodbapi.SQLrow.__str__ = adodbapi_SQLrow__str__
