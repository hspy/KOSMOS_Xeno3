import features

#def GetOpcUaLibClass():
#    from OpcUaClient import OpcUaLibrary
#    return OpcUaLibrary

#features.libraries.append(
#    ('OpcUa', GetOpcUaLibClass))

def GetOpcUaClass():
    from opcua import RootClass
    return RootClass

features.libraries.append(
    ('opcua', GetOpcUaClass))

#features.catalog.append(
#    ('opcua', _('PLCopen OPC UA'), _('Map located variables over OPC UA'), GetOpcUaClass))

