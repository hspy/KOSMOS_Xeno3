import os, shutil, csv, StringIO
#from xml.dom import minidom

from POULibrary import POULibrary
#from OpcFileTreeNode import OPCFile

import xml.etree.ElementTree as etree
from datetime import datetime

# OPC UA default id number addition
OpcUaId = 10000

# OPC UA Server Configuration
VpiName = '/usr/lib/opcua/libVpis'

opcAliasDict = {
                    "Boolean" : "i=1", "SByte" : "i=2", "Byte" : "i=3", "Int16" : "i=4",
                    "UInt16" : "i=5", "Int32" : "i=6", "UInt32" : "i=7", "Int64" : "i=8",
                    "UInt64" : "i=9", "Float" : "i=10", "Double" : "i=11", 
                    "DateTime" : "i=13", "String" : "i=12", "ByteString" : "i=15", 
                    "Guid" : "i=14", "XmlElement" : "i=16", "NodeId" : "i=17", 
                    "ExpandedNodeId" : "i=18", "QualifiedName" : "i=20", 
                    "LocalizedText" : "i=21", "StatusCode" : "i=19",
                    "Structure" : "i=22", "Number" : "i=26", "Integer" : "i=27",
                    "UInteger" : "i=28", "HasComponent" : "i=47", "HasProperty" : "i=46",
                    "Organizes" : "i=35", "HasEventSource" : "i=36", 
                    "HasNotifier" : "i=48", "HasSubtype" : "i=45", 
                    "HasTypeDefinition" : "i=40", "HasModellingRule" : "i=37", 
                    "HasEncoding" : "i=38", "HasDescription" : "i=39", 
                    "HasInputVar" : "ns=2;i=4001", "HasOutputVar" : "ns=2;i=4002", 
                    "HasInOutVar" : "ns=2;i=4003", "HasLocalVar" : "ns=2;i=4004", 
                    "HasExternalVar" : "ns=2;i=4005", "With" : "ns=2;i=4006",
                    "CtrlConfigurationType" : "ns=2;i=1001", "ConfigurableObjectType" : "ns=1;i=1004",
                    "Mandatory" : "i=78", "FolderType" : "i=61", "FunctionalGroupType" : "ns=1;i=1005",
                    "CtrlResourceType":"ns=2;i=1002", "Optional":"i=80",
                    "DeviceSet":"ns=1;i=5001", "Objects":"i=85",
                    "CtrlTaskType":"ns=2;i=1006", "PropertyType":"i=68",
                    "CtrlProgramType":"ns=2;i=1004", "OptionalPlaceholder":"i=11508",
                    "CtrlFunctionBlockType":"ns=2;i=1005",
                    }
    
plcOpcTypeDict = {
                  "BOOL":"Boolean", "SINT":"SByte", "USINT":"Byte", "INT":"Int16",
                  "UINT":"UInt16", "DINT":"Int32", "UDINT":"UInt32", "LINT":"Int64",
                  "ULINT":"UInt64", "BYTE":"Byte", "WORD":"UInt16", "DWORD":"UInt32",
                  "LWORD":"UInt64", "REAL":"Float", "LREAL":"Double", "string":"String", 
                  "CHAR":"Byte", "WSTRING":"String", "CHAR":"Byte", "WSTRING":"String",
                  "WCHAR":"UInt16", "DT":"DateTime", "DATE":"DateTime", "TOD":"DateTime",
                  "TIME":"Double"
                  }

plcInterfaceDict = {
                'inputVars':'HasInputVar', 'outputVars':'HasOutputVar',  'inOutVars':'HasInOutVar', 
                'localVars':'HasLocalVar', 'externalVars':'HasExternalVar'
                }

def tagName(tag, ns):
    return "{%s}%s" % (ns, tag)

def addReference(element, refType, val, isForward=True):
    
    ref = etree.SubElement(
                           element.find('References'), 
                           'Reference', 
                           {'ReferenceType':refType})
    ref.text = val
    if not isForward:
        ref.set('IsForward', 'false')

class plcOpcXmlGenerator():
    
    def __init__(self, plcXml, buildPath):

        self.objectTypeIdx = 1001
        self.objectIdx = 5001
        self.variableIdx = 9001
        
        self.opcObjDict = {}
        self.opcObjTypeDict = {}
        self.opcVarDict = {}
        self.varIdxDict = {}
        self.instanceDict = {}
        self.programPouTypeDict = {}
        self.fbPouTypeDict = {}
        
        self.plcXml = plcXml
        self.buildPath = buildPath

        self.derivedVarList = []
        self.vpiVarList = []

        self.genOpcObjList = []

        ############ get variable numbers ##########
        
        varCsv = open(os.path.join(self.buildPath, "VARIABLES.csv"))
        varRawStr = ""
        
        for line in varCsv:
            if line.strip() == '// Variables':
                break
        
        for line in varCsv:
            if line.strip() == '// Ticktime':
                varRawStr = varRawStr[:len(varRawStr)-2]
                break
            else:
                varRawStr += line
        
        varCsv.close()
        
        varRawStrStm = StringIO.StringIO(varRawStr)
        varStr = csv.reader(varRawStrStm, delimiter=';')
        testPath = os.path.join(self.buildPath, "test.txt")
 
        for row in varStr:
            key = row[2]
            if key in self.varIdxDict:
                pass
            self.varIdxDict[key] = row[0]
        
        testPath = os.path.join(self.buildPath, "test.txt")

        with file(testPath, 'w') as test:
            for item in self.varIdxDict.items():
                test.write(str("key: " + item[0] + ", val: " + item[1] + "\n")) 
 
        ############ default beremiz opc objects ################
        
        self.opcBeremizDefaultObjList = [
            self.getUaObjectType('BeremizConfigurationType',
                [
                 ['HasComponent', 'Resources', True],
                 ['HasComponent', 'GlobalVars', True],
                 ['HasComponent', 'AccessVars', True],
                 ['HasComponent', 'ConfigVars', True],
                 ['HasSubtype', 'CtrlConfigurationType', False],
                 ]
                         ),
            self.getUaObject('Resources', 'BeremizConfigurationType', 
                [
                 ['HasComponent', 'SupportedTypes', True],
                 ['HasTypeDefinition', 'ConfigurableObjectType', True],
                 ['HasModellingRule', 'Mandatory', True],
                 ['HasComponent', 'BeremizConfigurationType', False],
                 ]
                        ),
            self.getUaObject('SupportedTypes', 'Resources', 
                [
                 ['HasTypeDefinition', 'FolderType', True],
                 ['HasModellingRule', 'Mandatory', True],
                 ['HasComponent', 'Resources', False],
                 ]
                        ),
            self.getUaObject('GlobalVars', 'BeremizConfigurationType', 
                [
                 ['HasTypeDefinition', 'FunctionalGroupType', True],
                 ['HasModellingRule', 'Mandatory', True],
                 ['HasComponent', 'BeremizConfigurationType', False],
                 ]
                        ),
            self.getUaObject('AccessVars', 'BeremizConfigurationType', 
                [
                 ['HasTypeDefinition', 'FunctionalGroupType', True],
                 ['HasModellingRule', 'Mandatory', True],
                 ['HasComponent', 'BeremizConfigurationType', False],
                 ]
                        ),
            self.getUaObject('ConfigVars', 'BeremizConfigurationType', 
                [
                 ['HasTypeDefinition', 'FunctionalGroupType', True],
                 ['HasModellingRule', 'Mandatory', True],
                 ['HasComponent', 'BeremizConfigurationType', False],
                 ]
                        ),
            self.getUaObjectType('BeremizResourceType',
                [
                 ['HasComponent', 'Tasks', True],
                 ['HasComponent', 'Programs', True],
                 ['HasComponent', 'GlobalVars', True],
                 ['HasSubtype', 'CtrlResourceType', False],
                 ]
                         ),
            self.getUaObject('Tasks', 'BeremizResourceType', 
                [
                 ['HasComponent', 'SupportedTypes', True],
                 ['HasTypeDefinition', 'ConfigurableObjectType', True],
                 ['HasModellingRule', 'Mandatory', True],
                 ['HasComponent', 'BeremizResourceType', False],
                 ]
                        ),
            self.getUaObject('SupportedTypes', 'Tasks', 
                [
                 ['HasTypeDefinition', 'FolderType', True],
                 ['HasModellingRule', 'Mandatory', True],
                 ['HasComponent', 'Tasks', False],
                 ]
                        ),
            self.getUaObject('Programs', 'BeremizResourceType', 
                [
                 ['HasComponent', 'SupportedTypes', True],
                 ['HasTypeDefinition', 'ConfigurableObjectType', True],
                 ['HasModellingRule', 'Mandatory', True],
                 ['HasComponent', 'BeremizResourceType', False],
                 ]
                        ),
            self.getUaObject('SupportedTypes', 'Programs', 
                [
                 ['HasTypeDefinition', 'FolderType', True],
                 ['HasModellingRule', 'Mandatory', True],
                 ['HasComponent', 'Programs', False],
                 ]
                        ),
            self.getUaObject('GlobalVars', 'BeremizResourceType', 
                [
                 ['HasTypeDefinition', 'FolderType', True],
                 ['HasModellingRule', 'Optional', True],
                 ['HasComponent', 'BeremizResourceType', False],
                 ]
                        ),
            self.getUaObjectType('BeremizTaskType',
                [
                 ['HasProperty', 'Priority', True],
                 ['HasProperty', 'Interval', True],
                 ['HasProperty', 'Single', True],
                 ['HasSubtype', 'CtrlTaskType', False],
                 ]
                         ),
            self.getUaVariable('Priority', 
                False, 
                'UDINT', 
                'BeremizTaskType', 
                [
                 ['HasTypeDefinition', 'PropertyType', True],
                 ['HasModellingRule', 'Mandatory', True],
                 ['HasProperty', 'Priority', False]
                ]),
            self.getUaVariable('Interval', 
                False, 
                'string', 
                'BeremizTaskType', 
                [
                 ['HasTypeDefinition', 'PropertyType', True],
                 ['HasModellingRule', 'Optional', True],
                 ['HasProperty', 'Interval', False]
                ]),
            self.getUaVariable('Single', 
                False, 
                'string', 
                'BeremizTaskType', 
                [
                 ['HasTypeDefinition', 'PropertyType', True],
                 ['HasModellingRule', 'Optional', True],
                 ['HasProperty', 'Single', False]
                ])
        ]
         
        ############ initialize parsing ############
            
        self.tree = etree.parse(plcXml)
        
        self.root = self.tree.getroot()
        self.ns = self.root.get('{http://www.w3.org/2001/XMLSchema-instance}schemaLocation')
       
        ############ initialize xml generation ############
        
        self.rootGen = etree.Element('UANodeSet')
        
        self.rootGen.set('xmlns', "http://opcfoundation.org/UA/2011/03/UANodeSet.xsd")
        self.rootGen.set('xmlns:xsd', "http://www.w3.org/2001/XMLSchema")
        self.rootGen.set('xmlns:xsi', "http://www.w3.org/2001/XMLSchema-instance")
        self.rootGen.set('LastModified', datetime.now().isoformat())
        
        etree.SubElement(etree.SubElement(self.rootGen, 'NamespaceUris'), 'Uri'
                         ).text = "http://opcfoundation.org/Beremiz/" 
                         
       
        ################### generate parts ##########
                        
        # add alias elements
        self.setAlias()
        
        for item in self.opcBeremizDefaultObjList:
            self.setOpcXmlElements(item)
                
        self.setNodeNameToNodeId()
        
        self.parseProject()
        
        for item in self.genOpcObjList:
            self.setOpcXmlElements(item)

    def getNewIdx(self, idx):
            val = idx + 1
            for key in self.varIdxDict.keys():
                if key == val:
                    return self.getNewIdx(val)
            return val
    
    class DefUaObject():
        
        def setRefList(self, refList):
            self.refList = refList
            
        def addRefList(self, obj):
            self.refList.append(obj)
    
    class UaObject(DefUaObject):
        
        def __init__(self, genObj, objName, parentNodeId, refList):
            self.genObj = genObj
            self.browseName = "3:" + objName
            self.setObjTag()
            self.parentNodeId = parentNodeId
            self.displayName = objName
            self.setNodeId()
            self.refList = refList
            self.genObj.opcObjDict[self.nodeId] = self
        
        def setObjTag(self):
            self.nodeTag = "UAObject"
            
        def setNodeId(self):
            self.nodeId = "ns=3;i=" + str(self.genObj.objectIdx)
            self.genObj.objectIdx = self.genObj.getNewIdx(self.genObj.objectIdx)
            
    class UaObjectType(DefUaObject):
        
        def __init__(self, genObj, objName, refList):
            self.genObj = genObj
            self.browseName = "3:" + objName
            self.setObjTag()
            self.displayName = objName
            self.setNodeId()
            self.refList = refList
            self.genObj.opcObjTypeDict[self.displayName] = self
        
        def setObjTag(self):
            self.nodeTag = "UAObjectType"
            
        def setNodeId(self):
            self.nodeId = "ns=3;i=" + str(self.genObj.objectTypeIdx)
            self.genObj.objectTypeIdx = self.genObj.getNewIdx(self.genObj.objectTypeIdx)
			
    class UaVariable(DefUaObject):
        
        def __init__(self, genObj, objName, isObjVar, objType, parentNodeId, refList):
            self.genObj = genObj
            self.browseName = "3:" + objName
            self.isObjVar = isObjVar
            self.setObjTag()
            self.parentNodeId = parentNodeId
            self.objType = objType
            self.displayName = objName
            self.nodeId = None
            self.setNodeId()
            self.refList = refList
            self.genObj.opcVarDict[self.nodeId] = self
        
        def setObjTag(self):
            self.nodeTag = "UAVariable"
            
        def setNodeId(self):
            if self.isObjVar:
                if str(self.displayName).upper() in self.genObj.varIdxDict :
                    id = self.genObj.varIdxDict[str(self.displayName).upper()]
                    id = int(id) + OpcUaId
                    if id == 0 :
                        id = 20
                 #   self.nodeId = "ns=3;i=" + self.genObj.varIdxDict[str(self.displayName).upper()]
                    self.nodeId = "ns=3;i=" + str(id)
                 #   print self.displayName + ' : ' + self.nodeId
                    self.genObj.vpiVarList.append(self)
                        
            if self.nodeId is None:
                self.nodeId = "ns=3;i=" + str(self.genObj.variableIdx)
                self.genObj.variableIdx = self.genObj.getNewIdx(self.genObj.variableIdx)   

        def setVal(self, value):
            self.value = value
            
    def getUaObject(self, objName, parentNodeId, refList):
        return self.UaObject(self, objName, parentNodeId, refList)
    
    def getUaObjectType(self, objName, refList):
        return self.UaObjectType(self, objName, refList)
    
    def getUaVariable(self, objName, isObjVar, objType, parentNodeId, refList):
        return self.UaVariable(self, objName, isObjVar, objType, parentNodeId, refList)
    
    def setAlias(self):
        
        aliases = etree.SubElement(self.rootGen, 'Aliases')
        
        for item in opcAliasDict.items():
            alias = etree.Element('Alias', {'Alias':item[0]})
            alias.text = item[1]
            aliases.append(alias)
        
    def setOpcXmlElements(self, nodeObj):
    
        newObj = etree.SubElement(self.rootGen, nodeObj.nodeTag, {"BrowseName":nodeObj.browseName})
        newObj.set('NodeId', nodeObj.nodeId)
    
        if isinstance(nodeObj, self.UaObject) or isinstance(nodeObj, self.UaVariable):
            if nodeObj.parentNodeId != '':
                newObj.set("ParentNodeId", nodeObj.parentNodeId)
        
        etree.SubElement(newObj, 'DisplayName').text = nodeObj.displayName
        etree.SubElement(newObj, 'References')
        
        for item in nodeObj.refList:
            addReference(newObj, item[0], item[1], item[2])
        
        if isinstance(nodeObj, self.UaVariable):
            newObj.set("DataType", plcOpcTypeDict[nodeObj.objType])
            # UAVariable access level - read/write permission (0x3)
            newObj.set("AccessLevel", "3")
            if hasattr(nodeObj, 'value'):
                etree.SubElement(
                                 etree.SubElement(newObj, 'Value'), 
                                 nodeObj.objType,
                                 {'xmlns':'http://opcfoundation.org/UA/2008/02/Types.xsd'}
                                 ).text = nodeObj.value    
            
    def setNodeNameToNodeId(self):
    
        nodeIdDict = {}
        for obj in self.opcBeremizDefaultObjList:
            if not nodeIdDict.has_key(obj.displayName):
                nodeIdDict[obj.displayName] = [obj.nodeId]
            else:
                nodeIdDict[obj.displayName].append(obj.nodeId)
        for rootObj in self.rootGen.iter():
            if 'ParentNodeId' in rootObj.attrib.keys():
                parentText = rootObj.get('ParentNodeId')
                if opcAliasDict.has_key(parentText):
                    rootObj.set('ParentNodeId', opcAliasDict[parentText])
                else:
                    rootObj.set('ParentNodeId', nodeIdDict[parentText][0])
                    if len(nodeIdDict[parentText]) > 1:
                        nodeIdDict[parentText] = nodeIdDict[parentText][1:]
            elif rootObj.tag == 'Reference':
                refText = rootObj.text
                if opcAliasDict.has_key(refText):
                    rootObj.text = opcAliasDict[refText]
                else:
                    rootObj.text = nodeIdDict[refText][0]
                    if len(nodeIdDict[refText]) > 1:
                        nodeIdDict[refText] = nodeIdDict[refText][1:]
                        
    def parseProject(self):
        
        # TODO: configVar, globalVar, accessVar in the project scope
        #       should be parsed from 'root' elementtree object.

        root = self.root
        ns = self.ns
        
        for proj in root.iter(tagName('configuration',ns)) :
            
            self.projName = proj.get('name')
        
            projObj = self.getUaObject(
                               self.projName,
                               opcAliasDict['DeviceSet'],
                               [
                                ['HasTypeDefinition', self.opcObjTypeDict['BeremizConfigurationType'].nodeId, True],
                                ['HasComponent', opcAliasDict['DeviceSet'], False],
                                ]
                               )
            self.genOpcObjList.append(projObj)
            
            resourceObj = self.getUaObject('Resources', projObj.nodeId, 
                [
                 ['HasTypeDefinition', opcAliasDict['ConfigurableObjectType'], True],
                 ['HasModellingRule', opcAliasDict['Mandatory'], True],
                 ['HasComponent', projObj.nodeId, False],
                 ]
                        )
            projObj.addRefList(['HasComponent', resourceObj.nodeId, True])
            self.genOpcObjList.append(resourceObj)
            
            supportedTypeObj = self.getUaObject('SupportedTypes', resourceObj.nodeId, 
                [
                 ['HasTypeDefinition', opcAliasDict['FolderType'], True],
                 ['HasModellingRule', opcAliasDict['Mandatory'], True],
                 ['HasComponent', resourceObj.nodeId, False],
                 ]
                        )
            resourceObj.addRefList(['HasComponent', supportedTypeObj.nodeId, True])
            self.genOpcObjList.append(supportedTypeObj)
            
            globalVarObj = self.getUaObject('GlobalVars', projObj.nodeId, 
                [
                 ['HasTypeDefinition', opcAliasDict['FunctionalGroupType'], True],
                 ['HasModellingRule', 'Mandatory', True],
                 ['HasComponent', projObj.nodeId, False],
                 ]
                        )
            projObj.addRefList(['HasComponent', globalVarObj.nodeId, True])
            self.genOpcObjList.append(globalVarObj)
            
            accessVarObj = self.getUaObject('AccessVars', projObj.nodeId, 
                [
                 ['HasTypeDefinition', opcAliasDict['FunctionalGroupType'], True],
                 ['HasModellingRule', 'Mandatory', True],
                 ['HasComponent', projObj.nodeId, False],
                 ]
                        )
            projObj.addRefList(['HasComponent', accessVarObj.nodeId, True])
            self.genOpcObjList.append(accessVarObj)
            
            configVarObj = self.getUaObject('ConfigVars', projObj.nodeId, 
                [
                 ['HasTypeDefinition', opcAliasDict['FunctionalGroupType'], True],
                 ['HasModellingRule', 'Mandatory', True],
                 ['HasComponent', projObj.nodeId, False],
                 ]
                        )
            projObj.addRefList(['HasComponent', configVarObj.nodeId, True])
            self.genOpcObjList.append(configVarObj)
           
            for config in root.iter(tagName('configuration', ns)):
                self.parseGlobalVars(config, globalVarObj)
                self.parseResources(resourceObj, config)                         
                   
    def parseGlobalVars(self, configuration, globalVarsObj):

        root = self.root
        ns = self.ns
        objVarList = []
                
        # parse global variable list

        try :                   
            for globalVars in configuration.find(tagName('globalVars', ns)):
                for variable in globalVars.iter(tagName('variable', ns)):
                    # parse global variable type
                    typelist = list(variable.find(tagName('type', ns)))[0]
                    objType = typelist.tag[len(ns)+2:]
                    if not objType in plcOpcTypeDict:
                        continue
                    # write to plcvpi.xml by using getUaVariable function
                    objVarObj = self.getUaVariable(
                                    configuration.get('name') + '.' + variable.get('name'), 
                                    True, 
                                    objType, 
                                    globalVarsObj.nodeId, 
                                        [
                                        ["HasTypeDefinition", opcAliasDict[plcOpcTypeDict[objType]], True],
        #                                ["HasModellingRule", opcAliasDict['OptionalPlaceholder'], True],  
                                        ["HasComponent", globalVarsObj.nodeId, False],
                                        ]
                                    )
                    globalVarsObj.addRefList(['HasComponent', objVarObj.nodeId, True])
                    objVarList.append(objVarObj)
        except TypeError: # if configuration has no globalVars, 
          for item in objVarList: self.genOpcObjList.append(item) 
            
        for item in objVarList: self.genOpcObjList.append(item) 
                             
    def parseResources(self, resources, configuration):
        
        #TODO: variable handling needeed.
        
        root = self.root
        ns = self.ns 
        
        for rsc in root.iter(tagName('resource', ns)):
            resourceObj_ = self.getUaObject(
                                rsc.get('name'),
                                self.opcBeremizDefaultObjList[1].nodeId,
                                [
                                    ['HasTypeDefinition',
                                        self.opcObjTypeDict['BeremizResourceType'].nodeId,True],
                                    ['HasComponent', self.opcBeremizDefaultObjList[1].nodeId,
                                        False],
                                    ['HasModellingRule',opcAliasDict['Optional'],True]
                                ]
                                )
            self.opcBeremizDefaultObjList[1].addRefList(['HasComponent', resourceObj_.nodeId, True])
            self.genOpcObjList.append(resourceObj_)
            resourceObj = self.getUaObject(
                                 rsc.get('name'),
                                 resources.nodeId,
                                 [
                                  ['Organizes', opcAliasDict['Objects'], False],
                                  ['HasTypeDefinition', self.opcObjTypeDict['BeremizResourceType'].nodeId, True],
                                  ['HasComponent', resources.nodeId, False]
                                  ]
                                 )
            resources.addRefList(['HasComponent', resourceObj.nodeId, True])
            self.genOpcObjList.append(resourceObj)
            
            tasksObj = self.getUaObject('Tasks', resourceObj.nodeId,
                [
                 ['HasTypeDefinition', opcAliasDict['ConfigurableObjectType'], True],
                 ['HasModellingRule', opcAliasDict['Mandatory'], True],
                 ['HasComponent', resourceObj.nodeId, False],
                 ]
                        )
            resourceObj.addRefList(['HasComponent', tasksObj.nodeId, True])
            self.genOpcObjList.append(tasksObj)
            
            supportedTypesObj = self.getUaObject('SupportedTypes', tasksObj.nodeId, 
                [
                 ['HasTypeDefinition', opcAliasDict['FolderType'], True],
                 ['HasModellingRule', opcAliasDict['Mandatory'], True],
                 ['HasComponent', tasksObj.nodeId, False],
                 ]
                        )
            tasksObj.addRefList(['HasComponent', supportedTypesObj.nodeId, True])
            self.genOpcObjList.append(supportedTypesObj)
            
            programsObj = self.getUaObject('Programs', resourceObj.nodeId,
                [
                 ['HasTypeDefinition', opcAliasDict['ConfigurableObjectType'], True],
                 ['HasModellingRule', opcAliasDict['Mandatory'], True],
                 ['HasComponent', resourceObj.nodeId, False],
                 ]
                        )
            resourceObj.addRefList(['HasComponent', programsObj.nodeId, True])
            self.genOpcObjList.append(programsObj)
            
            progSupTypesObj = self.getUaObject('SupportedTypes', programsObj.nodeId, 
                [
                 ['HasTypeDefinition', opcAliasDict['FolderType'], True],
                 ['HasModellingRule', opcAliasDict['Mandatory'], True],
                 ['HasComponent', programsObj.nodeId, False],
                 ]
                        )
            programsObj.addRefList(['HasComponent', 'SupportedTypes', True])
            self.genOpcObjList.append(progSupTypesObj)
            
            globalVarsObj = self.getUaObject('GlobalVars', resourceObj.nodeId, 
                [
                 ['HasTypeDefinition', opcAliasDict['FolderType'], True],
                 ['HasModellingRule', opcAliasDict['Optional'], True],
                 ['HasComponent', resourceObj.nodeId, False],
                 ]
            )
            resourceObj.addRefList(['HasComponent', globalVarsObj.nodeId, True])
            self.genOpcObjList.append(globalVarsObj)      
            self.parseGlobalVarsOfResource(rsc, globalVarsObj, configuration)      # parse GlovalVars of resource
            self.parseTasks(rsc, tasksObj, configuration)    
            #sefl.parseFBTypes(rsc, 
            self.parsePOUs(rsc, programsObj, configuration)
                    
    def parseGlobalVarsOfResource(self, resource, globalVarsObj, configuration):  # parse GlovalVars of resource
        
        root = self.root
        ns = self.ns
        objVarList = []
        
        # parse global variable list
        for globalVars in resource.iter(tagName('globalVars', ns)):
            for variable in globalVars.iter(tagName('variable', ns)):
                # parse global variable type
                typelist = list(variable.find(tagName('type', ns)))[0]
                objType = typelist.tag[len(ns)+2:]
                if not objType in plcOpcTypeDict:
                    continue
                # write to plcvpi.xml by using getUaVariable function
                objVarObj = self.getUaVariable(
                                               configuration.get('name') + '.' + 
                                               resource.get('name') + '.' +
                                               variable.get('name'), 
                                               True, 
                                               objType, 
                                               globalVarsObj.nodeId, 
                                               [
                                                ["HasTypeDefinition", opcAliasDict[plcOpcTypeDict[objType]], True],
                #                               ["HasModellingRule", opcAliasDict['OptionalPlaceholder'], True],  
                                                ["HasComponent", globalVarsObj.nodeId, False],
                                                ]
                                )
                globalVarsObj.addRefList(['HasComponent', objVarObj.nodeId, True])
                objVarList.append(objVarObj)
                                
        for item in objVarList: self.genOpcObjList.append(item) 
        
    def parseTasks(self, resource, tasks, configuration):
    
        ns = self.ns
        
        for task in resource.iter(tagName('task', ns)):
            taskObj = self.getUaObject(
                               task.get('name'),
                               tasks.nodeId,
                               [
                                ['HasTypeDefinition', self.opcObjTypeDict['BeremizTaskType'].nodeId, True],
                                ['HasComponent', tasks.nodeId, False]
                                ]
                               )
            self.genOpcObjList.append(taskObj)
            tasks.addRefList(['HasComponent', taskObj.nodeId, True])
            
            priorityVar = self.getUaVariable(
                                    'Priority',
                                     False,
                                     'UDINT',
                                     taskObj.nodeId,
                                     [
                                      ['HasTypeDefinition', opcAliasDict['PropertyType'], True],
                                      ['HasModellingRule', opcAliasDict['Mandatory'], True],
                                      ['HasProperty', taskObj.nodeId, False]
                                      ]
                                     )
            priorityVar.setVal(task.get('priority'))
            taskObj.addRefList(['HasProperty', priorityVar.nodeId, True])
            self.genOpcObjList.append(priorityVar)
             
            intervalVar = self.getUaVariable(
                                     'Interval',
                                     False,
                                     'string',
                                     taskObj.nodeId,
                                     [
                                      ['HasTypeDefinition', opcAliasDict['PropertyType'], True],
                                      ['HasModellingRule', opcAliasDict['Optional'], True],
                                      ['HasProperty', taskObj.nodeId, False]
                                      ]
                                     )
            intervalVar.setVal(task.get('interval'))
            taskObj.addRefList(['HasProperty', intervalVar.nodeId, True])
            self.genOpcObjList.append(intervalVar)
          
            for inst in task.findall(tagName('pouInstance', ns)):
                self.instanceDict[
                                  configuration.get('name') + '.' + resource.get('name')
                                  + '.' + inst.get('name')
                                  ] = (inst.get('typeName'), taskObj)
                                  
    def parseInterfaceVars(self, pou, parentPouObj, isObjVar, objName):
        
        ns = self.ns
        derivedVarList = self.derivedVarList
        
        for interface in plcInterfaceDict.keys():
            for vars in pou.iter(tagName(interface, ns)):
                for variable in vars.iter(tagName('variable', ns)):
                    typelist = list(variable.find(tagName('type', ns)))[0]
                    objType = typelist.tag[len(ns)+2:]
                    if objType == 'derived':
                        derivedType = typelist.get('name')
                        derivedVarList.append((derivedType, variable.get('name'), parentPouObj, plcInterfaceDict[interface]))
                    elif not objType in plcOpcTypeDict:
                        continue
                    else:
                        varObj = self.getUaVariable(
                                        objName + '.' + variable.get('name'),
                                        isObjVar,
                                        objType,
                                        parentPouObj.nodeId,
                                        [
                                         ["HasTypeDefinition", opcAliasDict[plcOpcTypeDict[objType]], True],
                                         ["HasModellingRule", opcAliasDict['OptionalPlaceholder'], True],
                                         [plcInterfaceDict[interface], parentPouObj.nodeId, False]
                                         ]
                                        )
                        parentPouObj.addRefList([plcInterfaceDict[interface], varObj.nodeId, True])
                        self.genOpcObjList.append(varObj)
    
    def parsePOUs(self, resource, programsObj, configuration):
        
        root = self.root
        ns = self.ns 
        derivedVarList = self.derivedVarList
        
        for pou in root.iter(tagName('pou', ns)):
            if pou.get('pouType') == 'program':

                ##### For program object type #####
                objName = pou.get('name')
                
                pouObjType = self.getUaObjectType(
                    'Beremiz'+ objName + 'ProgramType', 
                    [
                     ['HasSubtype', opcAliasDict["CtrlProgramType"], False],
                     ]
                                                  )
                self.genOpcObjList.append(pouObjType)
                self.programPouTypeDict[pouObjType.displayName] = (pouObjType, pou)
                self.parseInterfaceVars(pou, pouObjType, False, objName)
                
                # Add reference with tasks to program object type
                for item in self.instanceDict.values():
                    if item[0] == pouObjType.displayName:
                        pouObjType.addRefList(['With', item[1].nodeId, True])
                        item[1].addRefList(['With', pouObjType.nodeId, False])

            elif pou.get('pouType') == 'functionBlock':
                ##### For FB object type #####
                objName = pou.get('name')
                
                pouObjType = self.getUaObjectType(
                    'Beremiz'+ objName + 'FBType', 
                    [
                     ['HasSubtype', opcAliasDict["CtrlFunctionBlockType"], False],
                     ]
                                                  )
                self.genOpcObjList.append(pouObjType)
                self.fbPouTypeDict[pouObjType.displayName] = (pouObjType, pou)
                self.parseInterfaceVars(pou, pouObjType, False, objName)
                
                ##### For program object #####
        for item in list(self.instanceDict.items()):
            programTypeName = "Beremiz" + item[1][0] + "ProgramType"
            programPouTypeTuple = self.programPouTypeDict.get(programTypeName) 
            if programPouTypeTuple is not None: 
                pouObj = self.getUaObject(
                              item[0], programsObj.nodeId, 
                              [
                               ['HasTypeDefinition', programPouTypeTuple[0].nodeId, True],
                               ])
                self.genOpcObjList.append(pouObj)
                pouObj.addRefList(['HasComponent', programsObj.nodeId, False])
                programsObj.addRefList(['HasComponent', pouObj.nodeId, True])

                self.parseInterfaceVars(programPouTypeTuple[1], pouObj, True, item[0])
                    
                # Add reference with task to program object
                pouObj.addRefList(['With', item[1][1].nodeId, True]) 
                item[1][1].addRefList(['With', pouObj.nodeId, False])
                
        for item in self.derivedVarList:
            fbTypeName = "Beremiz" + item[0] + "FBType"
            fbPouTypeTuple = self.fbPouTypeDict.get(fbTypeName)
            if fbPouTypeTuple is not None:
                fbInstanceName = item[2].displayName+'.'+item[1]
                pouObj = self.getUaObject(
                              fbInstanceName, item[2].nodeId, 
                              [
                               ['HasTypeDefinition', fbPouTypeTuple[0].nodeId, True],
                               ])
                self.genOpcObjList.append(pouObj)
                pouObj.addRefList([item[3], item[2].nodeId, False])
                item[2].addRefList([item[3], pouObj.nodeId, True])

                self.parseInterfaceVars(fbPouTypeTuple[1], pouObj, True, fbInstanceName)
        
                                            
    def generateOpcXml(self):

        ##### if all implementation is done, use this statement to make output file. #####
        genPath = os.path.join(self.buildPath, "plcOpc.xml") 
        outputTree = etree.ElementTree(self.rootGen)
        outputTree.write(genPath, 
                         encoding="UTF-8", 
                         xml_declaration=True,
                         method="xml")
        
        return genPath

    def getNodeId(self, item):	
		nodeIdInformation = item.nodeId.split(';')[1]
		nodeId = int(nodeIdInformation.split('=')[1])
		return nodeId
	
    def generateVpiXml(self):
        genPath = os.path.join(self.buildPath, "plcVpi.xml")
        self.rootVpi = etree.Element('SubSystems')
        self.rootVpi.set('xmlns', "http://scheme.beremiz.org/UABeremiz.xsd")
        self.rootVpi.set('xmlns:xsd', "http://www.w3.org/2001/XMLSchema")
        self.rootVpi.set('xmlns:xsi', "http://www.w3.org/2001/XMLSchema-instance")
        self.rootVpi.set('LastModified', datetime.now().isoformat())
        
        etree.SubElement(etree.SubElement(self.rootVpi, 'NamespaceUris'), 'Uri'
                         ).text = "http://opcfoundation.org/Beremiz/"

        subSys = etree.SubElement(self.rootVpi, 'SubSystem')
        subSys.set('VpiName', VpiName)
        subSys.set('SubSystemName', self.projName)
        subSys.set('SubSystemId', 'ns=3;i=1000')
        subSys.set('AccessMode', 'Both')
		
        self.vpiVarList.sort(key=self.getNodeId)
					  
        for item in self.vpiVarList:
            itemTag = etree.SubElement(subSys, 'Tag')
            itemTag.set('Id', item.nodeId)
            itemTag.set('Name', item.displayName)
            itemTag.set('Type', plcOpcTypeDict[item.objType])
            itemTag.set('NbElement', '0')
            itemTag.set('AccessType', 'Input_Output')
       
        outputTree = etree.ElementTree(self.rootVpi)
        outputTree.write(genPath, 
                         encoding="UTF-8", 
                         xml_declaration=True,
                         method="xml")
        
        return genPath

def GetLocalPath(filename):
    return os.path.join(os.path.split(__file__)[0], filename) 

class RootClass(POULibrary):
    def GetLibraryPath(self):
        return GetLocalPath("pous.xml")

    def Generate_C(self, buildpath, varlist, IECCFLAGS):
        c_file_path = os.path.join(os.path.split(__file__)[0], "opcua_part1.c")
        c_file = open(c_file_path, 'r')
        part1_c_code = c_file.read()
        c_file.close()
		
        c_file_path = os.path.join(os.path.split(__file__)[0], "opcua_part2.c")
        c_file = open(c_file_path, 'r')
        part2_c_code = c_file.read()
        c_file.close()
		
        UA_client_fb_count = 0
        UA_client_list = ["UA_CONNECT", "UA_DISCONNECT", "UA_NAMESPACEGETINDEXLIST", "UA_NODEGETHANDLELIST", 
							"UA_NODERELEASEHANDLELIST", "UA_NODEGETINFORMATION", "UA_SUBSCRIPTIONCREATE", "UA_SUBSCRIPTIONDELETE",
							"UA_SUBSCRIPTIONPROCESSED","UA_MONITOREDITEMADDLIST", "UA_MONITOREDITEMREMOVELIST", "UA_MONITOREDITEMOPERATELIST",
							"UA_READLIST", "UA_WRITELIST", "UA_METHODGETHANDLELIST", "UA_METHODRELEASEHANDLELIST", "UA_METHODCALL", "UA_CONNECTIONGETSTATUS",
							"_UA_GETMONITOREDITEMVARIABLEVALUE"]
		
        for v in varlist:
			if v["vartype"] == "FB" and v["type"] in UA_client_list :
				UA_client_fb_count = UA_client_fb_count + 1;
				
        UA_client_fb_count = max(1, UA_client_fb_count)
				
		# prepare UAClientFB code
        part2_c_code = part2_c_code % {
            "UAClientFBCounts": UA_client_fb_count }
		
        gen_c_file_path = os.path.join(buildpath, "opcua.c")
        gen_c_file = open(gen_c_file_path,'w')
        gen_c_file.write(part1_c_code + '\n' + part2_c_code)
        gen_c_file.close()
           
        plcXmlGen = plcOpcXmlGenerator(os.path.join(self.GetCTR().CTNPath(), "plc.xml"), buildpath)

        return ((["opcua"], [(gen_c_file_path, IECCFLAGS)], True),"",
                ("plcOpc.xml", file(plcXmlGen.generateOpcXml())),
                ("plcVpi.xml", file(plcXmlGen.generateVpiXml()))
                )
