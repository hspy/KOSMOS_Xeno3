import os

import wx

from PLCControler import LOCATION_CONFNODE, LOCATION_MODULE, LOCATION_GROUP, \
    LOCATION_VAR_INPUT, LOCATION_VAR_OUTPUT, LOCATION_VAR_MEMORY

from MotionLibrary import Headers, AxisXSD
from EthercatSlave import _EthercatSlaveCTN
from ConfigEditor import CIA402NodeEditor

# Definition of node variables that have to be mapped in PDO
# [(name, index, subindex, type, 
#   direction for master ('I': input, 'Q': output)),...]
NODE_VARIABLES = [
    ("ControlWord",             0x6040, 0x00, "UINT", "Q"),
    ("TargetPosition",          0x607a, 0x00, "DINT", "Q"),
    ("TargetVelocity",          0x60ff, 0x00, "DINT", "Q"),
    ("TargetTorque",            0x6071, 0x00, "INT",  "Q"),
    ("ModesOfOperation",        0x6060, 0x00, "SINT", "Q"),
    ("StatusWord",              0x6041, 0x00, "UINT", "I"),
    ("ModesOfOperationDisplay", 0x6061, 0x00, "SINT", "I"),
    ("ActualPosition",          0x6064, 0x00, "DINT", "I"),
    ("ActualVelocity",          0x606c, 0x00, "DINT", "I"),
    ("ActualTorque",            0x6077, 0x00, "INT",  "I"),
]

# Definition of optional node variables that can be added to PDO mapping.
# A checkbox will be displayed for each section in node configuration panel to
# enable them
# [(section_name, 
#   [{'description', (name, index, subindex, type, 
#                     direction for master ('I': input, 'Q': output)),
#     'retrieve', string_template_for_retrieve_variable (None: not retrieved, 
#                                 default string template if not defined),
#     'publish', string_template_for_publish_variable (None: not published, 
#                                 default string template if not defined),
#    },...]
EXTRA_NODE_VARIABLES = [
    ("ErrorCode", [
        {"description": ("ErrorCode", 0x603F, 0x00, "UINT", "I"),
         "publish": None}
        ]),
    ("DigitalInputs", [
        {"description": ("DigitalInputs", 0x60FD, 0x00, "UDINT", "I"),
         "publish": None}
        ]),
    ("DigitalOutputs", [
        {"description": ("DigitalOutputs", 0x60FE, 0x00, "UDINT", "Q"),
         "retrieve": None}
        ]),
    ("TouchProbe", [
        {"description": ("TouchProbeFunction", 0x60B8, 0x00, "UINT", "Q"),
         "retrieve": None},
        {"description": ("TouchProbeStatus", 0x60B9, 0x00, "UINT", "I"),
         "publish": None},
        {"description": ("TouchProbePos1PosValue", 0x60BA, 0x00, "DINT", "I"),
         "publish": None},
        {"description": ("TouchProbePos1NegValue", 0x60BB, 0x00, "DINT", "I"),
         "publish": None},
        ]),
]

# List of parameters name in no configuration panel for optional variable
# sections
EXTRA_NODE_VARIABLES_DICT = {
    "Enable" + name: params 
    for name, params in EXTRA_NODE_VARIABLES}

# List of block to define to interface MCL to fieldbus for specific functions
FIELDBUS_INTERFACE_GLOBAL_INSTANCES = [
    {"blocktype": "GetTorqueLimit", 
     "inputs": [],
     "outputs": [{"name": "TorqueLimitPos", "type": "UINT"},
                 {"name": "TorqueLimitNeg", "type": "UINT"}]},
    {"blocktype": "SetTorqueLimit", 
     "inputs": [{"name": "TorqueLimitPos", "type": "UINT"},
                {"name": "TorqueLimitNeg", "type": "UINT"}],
     "outputs": []},
]

#--------------------------------------------------
#         Remote Exec Etherlab Commands
#--------------------------------------------------

SLAVE_STATE = """
import commands
result = commands.getoutput("ethercat state -p %d %s")
returnVal =result 
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
#                 Ethercat CIA402 Node
#--------------------------------------------------

# --------- Add by jblee for pdo monitoring ---------

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

# ----------------------- end --------------------------

class _EthercatCIA402SlaveCTN(_EthercatSlaveCTN):
    XSD = """<?xml version="1.0" encoding="ISO-8859-1" ?>
    <xsd:schema xmlns:xsd="http://www.w3.org/2001/XMLSchema">
      <xsd:element name="CIA402SlaveParams">
        <xsd:complexType>
          %s
        </xsd:complexType>
      </xsd:element>
    </xsd:schema>
    """ % ("\n".join(["""\
          <xsd:attribute name="Enable%s" type="xsd:boolean"
                         use="optional" default="false"/>""" % category 
                for category, variables in EXTRA_NODE_VARIABLES]) + AxisXSD)
    
    NODE_PROFILE = 402
    EditorType = CIA402NodeEditor
    
    ConfNodeMethods = [
        {"bitmap" : "CIA402AxisRef",
         "name" : _("Axis Ref"),
         "tooltip" : _("Initiate Drag'n drop of Axis ref located variable"),
         "method" : "_getCIA402AxisRef",
         "push": True},
        {"bitmap" : "CIA402NetPos",
         "name" : _("Axis Pos"),
         "tooltip" : _("Initiate Drag'n drop of Network position located variable"),
         "method" : "_getCIA402NetworkPosition",
         "push": True},
    ]
    
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
    
    def GetIconName(self):
        return "CIA402Slave"
    
    def SetParamsAttribute(self, path, value):
        if path == "CIA402SlaveParams.Type":
            path = "SlaveParams.Type"
        elif path == "CIA402SlaveParams.Alias":
            path = "SlaveParams.Alias"
        return _EthercatSlaveCTN.SetParamsAttribute(self, path, value)
    
    def GetVariableLocationTree(self):
        axis_name = self.CTNName()
        current_location = self.GetCurrentLocation()
        children = [{"name": name_frmt % (axis_name),
                     "type": LOCATION_VAR_INPUT,
                     "size": "W",
                     "IEC_type": iec_type,
                     "var_name": var_name_frmt % axis_name,
                     "location": location_frmt % (
                            ".".join(map(str, current_location))),
                     "description": "",
                     "children": []}
                    for name_frmt, iec_type, var_name_frmt, location_frmt in
                        [("%s Network Position", "UINT", "%s_pos", "%%IW%s"),
                         ("%s Axis Ref", "AXIS_REF", "%s", "%%IW%s.402")]]
        children.extend(self.CTNParent.GetDeviceLocationTree(
                            self.GetSlavePos(), current_location, axis_name))
        return  {"name": axis_name,
                 "type": LOCATION_CONFNODE,
                 "location": self.GetFullIEC_Channel(),
                 "children": children,
        }
    
    def CTNGlobalInstances(self):
        current_location = self.GetCurrentLocation()
        return [("%s_%s" % (block_infos["blocktype"], 
                            "_".join(map(str, current_location))),
                 "EtherLab%s" % block_infos["blocktype"], "") 
                for block_infos in FIELDBUS_INTERFACE_GLOBAL_INSTANCES]
    
    def StartDragNDrop(self, data):
        data_obj = wx.TextDataObject(str(data))
        dragSource = wx.DropSource(self.GetCTRoot().AppFrame)
        dragSource.SetData(data_obj)
        dragSource.DoDragDrop()
    
    def _getCIA402NetworkPosition(self):
        self.StartDragNDrop(
            ("%%IW%s" % ".".join(map(str, self.GetCurrentLocation())), 
             "location", "UINT", self.CTNName() + "_Pos", ""))
        
    def _getCIA402AxisRef(self):
        self.StartDragNDrop(
            ("%%IW%s.402" % ".".join(map(str, self.GetCurrentLocation())), 
             "location", "AXIS_REF", self.CTNName(), ""))
        
    def CTNGenerate_C(self, buildpath, locations):
        current_location = self.GetCurrentLocation()
        
        location_str = "_".join(map(lambda x:str(x), current_location))
        slave_pos = self.GetSlavePos()
        MCL_headers = Headers
        
        # Open CIA402 node code template file 
        plc_cia402node_filepath = os.path.join(os.path.split(__file__)[0], 
                                               "plc_cia402node.c")
        plc_cia402node_file = open(plc_cia402node_filepath, 'r')
        plc_cia402node_code = plc_cia402node_file.read()
        plc_cia402node_file.close()
        
        # Init list of generated strings for each code template file section
        fieldbus_interface_declaration = []
        fieldbus_interface_definition = []
        init_axis_params = []
        extra_variables_retrieve = []
        extra_variables_publish = []
        extern_located_variables_declaration = []
        entry_variables = []
        init_entry_variables = []
        
        # Fieldbus interface code sections
        for blocktype_infos in FIELDBUS_INTERFACE_GLOBAL_INSTANCES:
            blocktype = blocktype_infos["blocktype"]
            ucase_blocktype = blocktype.upper()
            blockname = "_".join([ucase_blocktype, location_str])
            
            extract_inputs = "\n".join(["""\
    __SET_VAR(%s->, %s, %s);""" % (blockname, input_name, input_value)
                for (input_name, input_value) in [
                    ("EXECUTE", "__GET_VAR(data__->EXECUTE)")] + [
                    (input["name"].upper(), 
                     "__GET_VAR(data__->%s)" % input["name"].upper())
                    for input in blocktype_infos["inputs"]]
                ])
            
            
            return_outputs = "\n".join(["""\
    __SET_VAR(data__->,%(output_name)s, 
              __GET_VAR(%(blockname)s->%(output_name)s));""" % locals()
                    for output_name in ["DONE", "BUSY", "ERROR"] + [
                        output["name"].upper()
                        for output in blocktype_infos["outputs"]]
                ])
                        
            fieldbus_interface_declaration.append("""
extern void ETHERLAB%(ucase_blocktype)s_body__(ETHERLAB%(ucase_blocktype)s* data__);
void __%(blocktype)s_%(location_str)s(MC_%(ucase_blocktype)s *data__) {
__DECLARE_GLOBAL_PROTOTYPE(ETHERLAB%(ucase_blocktype)s, %(blockname)s);
ETHERLAB%(ucase_blocktype)s* %(blockname)s = __GET_GLOBAL_%(blockname)s();
__SET_VAR(%(blockname)s->, POS, AxsPub.axis->NetworkPosition);
%(extract_inputs)s
ETHERLAB%(ucase_blocktype)s_body__(%(blockname)s);
%(return_outputs)s
}""" % locals())
            
            fieldbus_interface_definition.append("""\
        AxsPub.axis->__mcl_func_MC_%(blocktype)s = __%(blocktype)s_%(location_str)s;\
""" % locals())
        
        # Get a copy list of default variables to map
        variables = NODE_VARIABLES[:]
        
        # Set AxisRef public struct members value
        node_params = self.CTNParams[1].getElementInfos(self.CTNParams[0])
        for param in node_params["children"]:
            param_name = param["name"]
            
            # Param is optional variables section enable flag
            extra_node_variable_infos = EXTRA_NODE_VARIABLES_DICT.get(param_name)
            if extra_node_variable_infos is not None:
                param_name = param_name.replace("Enable", "") + "Enabled"
                
                if not param["value"]:
                    continue
                
                # Optional variables section is enabled
                for variable_infos in extra_node_variable_infos:
                    var_name = variable_infos["description"][0]
                    
                    # Add each variables defined in section description to the
                    # list of variables to map
                    variables.append(variable_infos["description"])
                    
                    # Add code to publish or retrive variable
                    for var_exchange_dir, str_list, default_template in [
                         ("retrieve", extra_variables_retrieve,
                          "    AxsPub.axis->%(var_name)s = *(AxsPub.%(var_name)s);"),
                         ("publish", extra_variables_publish,
                          "    *(AxsPub.%(var_name)s) = AxsPub.axis->%(var_name)s;")]:
                        
                        template = variable_infos.get(var_exchange_dir, 
                                                      default_template)
                        if template is not None:
                            extra_variables_publish.append(template % locals())
            
            # Set AxisRef public struct member value if defined
            if param["value"] is not None:
                param_value = ({True: "1", False: "0"}[param["value"]]
                               if param["type"] == "boolean"
                               else str(param["value"]))
                
                init_axis_params.append("""\
        AxsPub.axis->%(param_name)s = %(param_value)s;""" % locals())
        
        # Add each variable in list of variables to map to master list of
        # variables to add to network configuration
        for name, index, subindex, var_type, dir in variables:
            var_size = self.GetSizeOfType(var_type)
            var_name = """\
__%(dir)s%(var_size)s%(location_str)s_%(index)d_%(subindex)d""" % locals()
            
            extern_located_variables_declaration.append(
                    "IEC_%(var_type)s *%(var_name)s;" % locals())
            entry_variables.append(
                    "    IEC_%(var_type)s *%(name)s;" % locals())
            init_entry_variables.append(
                    "    AxsPub.%(name)s = %(var_name)s;" % locals())
            
            self.CTNParent.FileGenerator.DeclareVariable(
                    slave_pos, index, subindex, var_type, dir, var_name)
        
        # Add newline between string in list of generated strings for sections
        [fieldbus_interface_declaration, fieldbus_interface_definition,
         init_axis_params, extra_variables_retrieve, extra_variables_publish,
         extern_located_variables_declaration, entry_variables, 
         init_entry_variables] = map(lambda l: "\n".join(l), [
            fieldbus_interface_declaration, fieldbus_interface_definition,
            init_axis_params, extra_variables_retrieve, extra_variables_publish,
            extern_located_variables_declaration, entry_variables, 
            init_entry_variables])
        
        # Write generated content to CIA402 node file
        Gen_CIA402Nodefile_path = os.path.join(buildpath, 
                                "cia402node_%s.c"%location_str)
        cia402nodefile = open(Gen_CIA402Nodefile_path, 'w')
        cia402nodefile.write(plc_cia402node_code % locals())
        cia402nodefile.close()
        
        return [(Gen_CIA402Nodefile_path, '"-I%s"'%os.path.abspath(self.GetCTRoot().GetIECLibPath()))],"",True
    
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
