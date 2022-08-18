import features

#def GetHmiSockLibClass():
#    from HmiSockClient import HmiSockLibrary
#    return HmiSockLibrary

#features.libraries.append(
#    ('HmiSock', GetHmiSockLibClass))

def GetHmiSockClass():
    from hmisock import RootClass
    return RootClass

features.libraries.append(
    ('hmisock', GetHmiSockClass))

#features.catalog.append(
#    ('hmisock', _('PLCopen HMI SOCK'), _('Map located variables over HMI SOCK'), GetHmiSockClass))

