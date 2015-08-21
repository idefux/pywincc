WinCC MS SQL Connection
=======================

This python module provides access to the Microsoft SQL Server 2005 database underlying Siemens WinCC.

## Functions

1. Read any data from WinCC configuration and WinCC runtime database (using SQLOLEDB.1 provider)
2. Read data from WinCC TagLogging and AlarmLogging archives (using WINCCOLEDB provider)


## Prerequisites

### Local
1. python 2.7
2. python modules
	* adodbapi
	* win32com

### Remote machine
1. WinCC 7.0 (previous or newer versions may also work)
2. VPN connection to remote machine (e.g. OpenVPN)
3. Firewall settings to allow connection from remote machine