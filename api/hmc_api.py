# # -*- coding:UTF-8 -*-
# import xmltodict
# import urllib2
# import ssl
#
# ssl._create_default_https_context = ssl._create_unverified_context
#
# url = 'https://200.31.147.83:12443'
# username = 'hscroot'
# password = 'abc123'
# data = '''
# <LogonRequest xmlns="http://www.ibm.com/xmlns/systems/power/firmware/web/mc/2012_10/"
# schemaVersion="V1_3_0">
#     <Metadata>
#         <Atom/>
#     </Metadata>
#     <UserID kb="CUR" kxe="false">%s</UserID>
#     <Password kb="CUR" kxe="false">%s</Password>
# </LogonRequest>
# ''' % (username, password)
#
#
# class HMCAPI(object):
#     def __init__(self):
#         self.opener = urllib2.build_opener(urllib2.HTTPCookieProcessor)
#
#     def get_token(self, url=url, data=data):
#         try:
#             headers = {
#                 'Content-Type': 'application/vnd.ibm.powervm.web+xml'
#             }
#             req = urllib2.Request(url + '/rest/api/web/Logon', headers=headers)
#             req.get_method = lambda: 'PUT'
#             x_session = xmltodict.parse(self.opener.open(req, data).read())
#             return x_session['LogonResponse']['X-API-Session']['#text']
#         except Exception, e:
#             print e
#             return False
#
#     def get_class(self, x_session):
#         try:
#             headers = {
#                 'Content-Type': 'application/atom+xml,application/vnd.ibm.powervm.uom+xml;Type=ManagedSystem',
#                 'X-API-Session': x_session}
#             req = urllib2.Request(url + '/rest/api/uom/ManagedSystem', headers=headers)
#             self.response = self.opener.open(req).read()
#             return self.response
#         except urllib2.HTTPError, e:
#             print e
#
#     def __del__(self):
#         self.opener.close()
#
#
# hmcapi = HMCAPI()
# x_session = hmcapi.get_token()
# print x_session
# manage = hmcapi.get_class(x_session)
# print manage
#
#
# !D:\Virtualenv\AutomateVirtualenv\Scripts\python.exe
# EASY-INSTALL-ENTRY-SCRIPT: 'HmcRestClient==1.0','console_scripts','HmcRestClient'

__requires__ = 'HmcRestClient==1.0'
import sys
from pkg_resources import load_entry_point

if __name__ == '__main__':
    sys.exit(
        load_entry_point('HmcRestClient==1.0', 'console_scripts', 'HmcRestClient')()
    )
