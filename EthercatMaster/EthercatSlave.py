import wx

from PLCControler import LOCATION_CONFNODE, LOCATION_MODULE, LOCATION_GROUP, LOCATION_VAR_INPUT, LOCATION_VAR_OUTPUT, LOCATION_VAR_MEMORY
from ConfigTreeNode import ConfigTreeNode

from ConfigEditor import NodeEditor

TYPECONVERSION = {"BOOL" : "X", "SINT" : "B", "INT" : "W", "DINT" : "D", "LINT" : "L",
    "USINT" : "B", "UINT" : "W", "UDINT" : "D", "ULINT" : "L", 
    "BYTE" : "B", "WORD" : "W", "DWORD" : "D", "LWORD" : "L"}

DATATYPECONVERSION = {"BOOL" : "BIT", "SINT" : "S8", "INT" : "S16", "DINT" : "S32", "LINT" : "S64",
    "USINT" : "U8", "UINT" : "U16", "UDINT" : "U32", "ULINT" : "U64", 
    "BYTE" : "U8", "WORD" : "U16", "DWORD" : "U32", "LWORD" : "U64"}

VARCLASSCONVERSION = {"T": LOCATION_VAR_INPUT, "R": LOCATION_VAR_OUTPUT, "RT": LOCATION_VAR_MEMORY}

def ExtractHexDecValue(value):
    try:
        return int(value)
    except:
        pass
    try:
        return int(value.replace("#", "0"), 16)
    except:
        raise ValueError, "Invalid value for HexDecValue \"%s\"" % value

def GenerateHexDecValue(value, base=10):
    if base == 10:
        return str(value)
    elif base == 16:
        return "#x%.8x" % value
    else:
        raise ValueError, "Not supported base"

def ExtractName(names, default=None):
    if len(names) == 1:
        return names[0].getcontent()
    else:
        for name in names:
            if name.getLcId() == 1033:
                return name.getcontent()
    return default

#--------------------------------------------------
#         Remote Exec Etherlab Commands
#--------------------------------------------------

SLAVE_STATE = """
import commands
result = commands.getoutput("ethercat state -p %d %s")
returnVal = result 
"""

GET_SLAVE = """
import commands
result = commands.getoutput("ethercat slave")
returnVal =result 
"""

# ethercat xml -p (Slave Position)
SLAVE_XML = """
import commands
result = commands.getoutput("ethercat xml -p %d")
returnVal =result 
"""

# ethercat sdos -p (Slave Position)
SLAVE_SDO = """
import commands
result = commands.getoutput("ethercat sdos -p %d")
returnVal =result 
"""

GET_SLOW_SDO = """
import commands
result = commands.getoutput("ethercat upload -p %d %s %s")
returnVal =result 
"""

# ethercat download -p (Slave Position) (Main Index) (Sub Index) (Value)
SDO_DOWNLOAD = """
import commands
result = commands.getoutput("ethercat download --type %s -p %d %s %s %s")
returnVal =result 
"""

# ethercat sii_read -p (Slave Position)
SII_READ = """
import commands
result = commands.getoutput("ethercat sii_read -p %d")
returnVal =result 
"""

# later..
REG_READ = """
import commands
result = commands.getoutput("ethercat reg_read -p %d %s %s")
returnVal =result 
"""

SII_WRITE = """ 
import subprocess 
process = subprocess.Popen(
    ["ethercat", "-f", "sii_write", "-p", "%d", "-"],
    stdin=subprocess.PIPE)
process.communicate(sii_data)
returnVal = process.returncode 
"""

# by Chaerin 130324
REG_WRITE = """ 
import commands
result = commands.getoutput("ethercat reg_write -p %d -t uint16 %s %s")
returnVal =result 
""" 

# by Chaerin 130116
FILE_ERASE = """ 
import commands
result = commands.getoutput("rm %s")
returnVal =result 
"""

# by Chaerin 130121
RESCAN = """ 
import commands
result = commands.getoutput("ethercat rescan -p %d")
returnVal =result 
"""

#--------------------------------------------------
#                    Ethercat Node
#--------------------------------------------------

class _EthercatSlaveCTN:

#--------------------------------------------------
#    Data Structure for ethercat management
#--------------------------------------------------

    # Save SlaveSDO data
    SDOData_0 = None
    SDOData_1 = None
    SDOData_2 = None
    SDOData_6 = None
    SDOData_a = None
    SDOData_all = None
    Loading_SDO_Flag = False
    
    # This flag For SlaveSDO Write Access
    Check_PREOP = False
    Check_SAFEOP = False
    Check_OP = False

    # Save PDO Data
    TxPDOInfos = []
    TxPDOCategorys = []
    RxPDOInfos = []
    RxPDOCategorys = []
    Addxmlflag = False
    
    # Save EEPROM Data
    SiiData = ""

    # Save Register Data
    RegData = ""
    Reg_EscType = ""
    Reg_FmmuNumber = ""
    Reg_SmNumber = ""
    Reg_PdiType = ""

#--------------------------------------------------
#    class code
#--------------------------------------------------
  
    NODE_PROFILE = None
    EditorType = NodeEditor
    
    def GetIconName(self):
        return "Slave"
    
    def ExtractHexDecValue(self, value):
        return ExtractHexDecValue(value)
    
    def GetSizeOfType(self, type):
        return TYPECONVERSION.get(self.GetCTRoot().GetBaseType(type), None)
    
    def GetSlavePos(self):
        return self.BaseParams.getIEC_Channel()
    
    def GetParamsAttributes(self, path = None):
        if path:
            parts = path.split(".", 1)
            if self.MandatoryParams and parts[0] == self.MandatoryParams[0]:
                return self.MandatoryParams[1].getElementInfos(parts[0], parts[1])
            elif self.CTNParams and parts[0] == self.CTNParams[0]:
                return self.CTNParams[1].getElementInfos(parts[0], parts[1])
        else:
            params = []
            if self.CTNParams:
                params.append(self.CTNParams[1].getElementInfos(self.CTNParams[0]))
            else:
                params.append({
                    'use': 'required', 
                    'type': 'element', 
                    'name': 'SlaveParams', 
                    'value': None, 
                    'children': []
                })
            
            slave_type = self.CTNParent.GetSlaveType(self.GetSlavePos())
            params[0]['children'].insert(0,
                   {'use': 'optional', 
                    'type': self.CTNParent.GetSlaveTypesLibrary(self.NODE_PROFILE), 
                    'name': 'Type', 
                    'value': (slave_type["device_type"], slave_type)}) 
            params[0]['children'].insert(1,
                   {'use': 'optional', 
                    'type': 'unsignedLong', 
                    'name': 'Alias', 
                    'value': self.CTNParent.GetSlaveAlias(self.GetSlavePos())})
            return params
        
    def SetParamsAttribute(self, path, value):
        position = self.BaseParams.getIEC_Channel()
        
        if path == "SlaveParams.Type":
            self.CTNParent.SetSlaveType(position, value)
            slave_type = self.CTNParent.GetSlaveType(self.GetSlavePos())
            value = (slave_type["device_type"], slave_type)
            if self._View is not None:
                #wx.CallAfter(self._View.EtherCATManagementTreebook.SlaveStatePanel.RefreshSlaveInfos())
                self._View.EtherCATManagementTreebook.SlaveStatePanel.RefreshSlaveInfos()
                self._View.EtherCATManagementTreebook.PDOMonitoringPanel.PDOInfoUpdate()
                self._View.EtherCATManagementTreebook.SmartView.Create_SmartView()
            return value, True
        elif path == "SlaveParams.Alias":
            self.CTNParent.SetSlaveAlias(position, value)
            return value, True
        
        value, refresh = ConfigTreeNode.SetParamsAttribute(self, path, value)
        
        # Filter IEC_Channel, Slave_Type and Alias that have specific behavior
        if path == "BaseParams.IEC_Channel" and value != position:
            self.CTNParent.SetSlavePosition(position, value)
        
        return value, refresh
        
    def GetSlaveInfos(self):
        return self.CTNParent.GetSlaveInfos(self.GetSlavePos())
    
    def GetSlaveVariables(self, limits):
        return self.CTNParent.GetSlaveVariables(self.GetSlavePos(), limits)
    
    def GetVariableLocationTree(self):
        return  {"name": self.BaseParams.getName(),
                 "type": LOCATION_CONFNODE,
                 "location": self.GetFullIEC_Channel(),
                 "children": self.CTNParent.GetDeviceLocationTree(self.GetSlavePos(), self.GetCurrentLocation(), self.BaseParams.getName())
        }

    def CTNGenerate_C(self, buildpath, locations):
        return [],"",False
    
    #--------------------------- For EtherCAT Management -------------------------------------------------
    # used for set Slave State   
    def RequestSlaveState(self, command):
        error, returnVal = self.RemoteExec(SLAVE_STATE%(self.GetSlavePos(), command), returnVal = None)
        return returnVal
    
    # return Slave Current State  
    def GetSlaveStateFromSlave(self):   
        error, returnVal = self.RemoteExec(GET_SLAVE, returnVal = None)
        return error, returnVal
    
    # used for error check
    def GetSlaveXML(self):   # add by Chaerin 121229
        error, returnVal = self.RemoteExec(SLAVE_XML%(self.GetSlavePos()), returnVal = None)
        return error, returnVal    

    # Directly Access Slave, get Slave SDO information
    def GetSlaveSDOFromSlave(self):
        error, returnVal = self.RemoteExec(SLAVE_SDO%(self.GetSlavePos()), returnVal = None)
        return returnVal   
    
    def RequestPDOInfo(self):
        slave = self.CTNParent.GetSlave(self.GetSlavePos())
        type_infos = slave.getType()
        device, alignment = self.CTNParent.GetModuleInfos(type_infos)
        self.ClearDataSet()
        
        if device is not None :
            self.Addxmlflag = True
            self.SavePDOData(device)
        else : 
            pass
        
    def SavePDOData(self, device):
        for pdo, pdo_info in ([(pdo, "Inputs") for pdo in device.getTxPdo()]):
                     
            pdo_index = ExtractHexDecValue(pdo.getIndex().getcontent())
            entries = pdo.getEntry()
            pdo_name = ExtractName(pdo.getName())
            
            count = 0          
            for entry in entries:
                index = ExtractHexDecValue(entry.getIndex().getcontent())
                subindex = ExtractHexDecValue(entry.getSubIndex())
                if ExtractName(entry.getName()) is not None :
                    entry_infos = {
                                "entry_index" : index,
                                "subindex" : subindex,
                                "name" : ExtractName(entry.getName()),
                                "bitlen" : entry.getBitLen(),
                                "type" : entry.getDataType().getcontent()
                                    }
                    self.TxPDOInfos.append(entry_infos)
                    count += 1
              
            categorys = {"pdo_index" : pdo_index, "name" : pdo_name, "number_of_entry" : count}  
            self.TxPDOCategorys.append(categorys)

        for pdo, pdo_info in ([(pdo, "Outputs") for pdo in device.getRxPdo()]):
                      
            pdo_index = ExtractHexDecValue(pdo.getIndex().getcontent())
            entries = pdo.getEntry()
            pdo_name = ExtractName(pdo.getName())
                        
            count = 0          
            for entry in entries:
                index = ExtractHexDecValue(entry.getIndex().getcontent())
                subindex = ExtractHexDecValue(entry.getSubIndex())
                if ExtractName(entry.getName()) is not None :
                    entry_infos = {
                                "entry_index" : index,
                                "subindex" : subindex,
                                "name" : ExtractName(entry.getName()),
                                "bitlen" : str(entry.getBitLen()),
                                "type" : entry.getDataType().getcontent()
                                    }
                    self.RxPDOInfos.append(entry_infos)
                    count += 1
    
            categorys = {"pdo_index" : pdo_index, "name" : pdo_name, "number_of_entry" : count}  
            self.RxPDOCategorys.append(categorys) 

    def GetTxPDOCategory(self):
        if self.Addxmlflag == True :
            return self.TxPDOCategorys
        
    def GetRxPDOCategory(self):
        if self.Addxmlflag == True :
            return self.RxPDOCategorys
        
    def GetTxPDOInfo(self):
        if self.Addxmlflag == True :
            return self.TxPDOInfos
        
    def GetRxPDOInfo(self):
        if self.Addxmlflag == True :
            return self.RxPDOInfos
        
    def SetAddxmlflag(self):
        if self.Addxmlflag == False :
            self.Addxmlflag = True

    def ClearDataSet(self):
        self.TxPDOInfos = []
        self.TxPDOCategorys = []
        self.RxPDOInfos = []
        self.RxPDOCategorys = []
    
    # for SDO download 
    def SdoDownload(self, dataType, idx, subIdx, value):
        error, returnVal = self.RemoteExec(SDO_DOWNLOAD%(dataType, self.GetSlavePos(), idx, subIdx, value), returnVal = None)
        return returnVal
    
    def BackupSDODataSet(self):
        self.Backup_0 = self.SDOData_0
        self.Backup_1 = self.SDOData_1
        self.Backup_2 = self.SDOData_2
        self.Backup_6 = self.SDOData_6
        self.Backup_a = self.SDOData_a
        self.Backup_all = self.SDOData_all
        
    def ReturnBackupDataSet(self):
        self.SDOData_0 = self.Backup_0
        self.SDOData_1 = self.Backup_1
        self.SDOData_2 = self.Backup_2
        self.SDOData_6 = self.Backup_6
        self.SDOData_a = self.Backup_a
        self.SDOData_all = self.Backup_all
    
    def ClearSDODataSet(self):
        self.SDOData_0 = None
        self.SDOData_1 = None
        self.SDOData_2 = None
        self.SDOData_6 = None
        self.SDOData_a = None
        self.SDOData_all = None           

    # for title SDO Management, ESC Memory dialog 
    def GetSlaveName(self):
        # get slave info from xml include name
        tmp = self.CTNParent.GetSlaveInfos(self.GetSlavePos())
        # if xml is imported, get slave name
        if tmp is not None :
            name = tmp['device_type']
            return name
        # xml is not imported, slave name is unknown
        else :
            return "Unknown"

    # used for ESC memory for Binary View
    def Sii_Read(self):
        error, returnVal = self.RemoteExec(SII_READ%(self.GetSlavePos()), returnVal = None)
        self.SiiData = returnVal
        return returnVal
    
    # used for ESC memory for Slave Information
    def Reg_Read(self, offset, length):
        error, returnVal = self.RemoteExec(REG_READ%(self.GetSlavePos(), offset, length), returnVal = None)
        return returnVal   
    
    def Sii_Write(self, binary): # by Chaerin 130116
        error, returnVal = self.RemoteExec(SII_WRITE%(self.GetSlavePos()), returnVal = None, sii_data = binary)
        self.RemoteExec(FILE_ERASE%("./eeprom_bianryfile.bin"), returnVal = None)
        return error, returnVal
    
    # used for register write
    def Reg_Write(self, address, data):
        error, returnVal = self.RemoteExec(REG_WRITE%(self.GetSlavePos(), address, data), returnVal = None)
        return returnVal 
    
    def Rescan(self): # by Chaerin 130121
        error, returnVal = self.RemoteExec(RESCAN%(self.GetSlavePos()), returnVal = None)
        return returnVal
    
    def GetRootClass(self):
        return self.CTNParent.CTNParent
    
    def GetSDOValue_Slow(self, idx, subIdx):
        error, returnVal = self.RemoteExec(GET_SLOW_SDO%(self.GetSlavePos(), idx, subIdx), returnVal = None)
        return returnVal
 
    def SetSlaveState(self, state):
        self.SlaveStateFlag = False
        self.SlaveState = state
        self.SlaveStateFlag = True
        
    def GetSlaveState(self):
        if(self.SlaveStateFlag == False) :
            while True :
                pass
                if self.SlaveStateFlag == True :
                    break
        
        return self.SlaveState
