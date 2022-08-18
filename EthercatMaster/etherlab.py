import os, shutil
from xml.dom import minidom

import wx
import csv

from xmlclass import *

from ConfigTreeNode import ConfigTreeNode
from PLCControler import UndoBuffer, LOCATION_CONFNODE, LOCATION_MODULE, LOCATION_GROUP, LOCATION_VAR_INPUT, LOCATION_VAR_OUTPUT, LOCATION_VAR_MEMORY

from EthercatSlave import ExtractHexDecValue, ExtractName
from EthercatMaster import _EthercatCTN
from ConfigEditor import LibraryEditor, ETHERCAT_VENDOR, ETHERCAT_GROUP, ETHERCAT_DEVICE

#--------------------------------------------------
#                 Ethercat ConfNode
#--------------------------------------------------

EtherCATInfoClasses = GenerateClassesFromXSD(os.path.join(os.path.dirname(__file__), "EtherCATInfo.xsd")) 

cls = EtherCATInfoClasses["EtherCATBase.xsd"].get("DictionaryType", None)
if cls:
    cls.loadXMLTreeArgs = None
    
    setattr(cls, "_loadXMLTree", getattr(cls, "loadXMLTree"))
    
    def loadXMLTree(self, *args):
        self.loadXMLTreeArgs = args
    setattr(cls, "loadXMLTree", loadXMLTree)

    def load(self):
        if self.loadXMLTreeArgs is not None:
            self._loadXMLTree(*self.loadXMLTreeArgs)
            self.loadXMLTreeArgs = None
    setattr(cls, "load", load)

cls = EtherCATInfoClasses["EtherCATInfo.xsd"].get("DeviceType", None)
if cls:
    cls.DataTypes = None
    
    def GetProfileNumbers(self):
        profiles = []
        
        for profile in self.getProfile():
            profile_content = profile.getcontent()
            if profile_content is None:
                continue
            
            for content_element in profile_content["value"]:
                if content_element["name"] == "ProfileNo":
                    profiles.append(content_element["value"])
        
        return profiles
    setattr(cls, "GetProfileNumbers", GetProfileNumbers)
    
    def GetProfileDictionaries(self):
        dictionaries = []
        
        for profile in self.getProfile():
        
            profile_content = profile.getcontent()
            if profile_content is None:
                continue
            
            for content_element in profile_content["value"]:
                if content_element["name"] == "Dictionary":
                    dictionaries.append(content_element["value"])
                elif content_element["name"] == "DictionaryFile":
                    raise ValueError, "DictionaryFile for defining Device Profile is not yet supported!"
                
        return dictionaries
    setattr(cls, "GetProfileDictionaries", GetProfileDictionaries)
    
    def ExtractDataTypes(self):
        self.DataTypes = {}
        
        for dictionary in self.GetProfileDictionaries():
            dictionary.load()
            
            datatypes = dictionary.getDataTypes()
            if datatypes is not None:
                
                for datatype in datatypes.getDataType():
                    content = datatype.getcontent()
                    if content is not None and content["name"] == "SubItem":
                        self.DataTypes[datatype.getName()] = datatype
    
    setattr(cls, "ExtractDataTypes", ExtractDataTypes)
    
    def getCoE(self):
        mailbox = self.getMailbox()
        if mailbox is not None:
            return mailbox.getCoE()
        return None
    setattr(cls, "getCoE", getCoE)

    def GetEntriesList(self, limits=None):
        if self.DataTypes is None:
            self.ExtractDataTypes()
        
        entries = {}
        
        for dictionary in self.GetProfileDictionaries():
            dictionary.load()
            
            for object in dictionary.getObjects().getObject():
                entry_index = object.getIndex().getcontent()
                index = ExtractHexDecValue(entry_index)
                if limits is None or limits[0] <= index <= limits[1]:
                    entry_type = object.getType()
                    entry_name = ExtractName(object.getName())
                    
                    entry_type_infos = self.DataTypes.get(entry_type, None)
                    if entry_type_infos is not None:
                        content = entry_type_infos.getcontent()
                        for subitem in content["value"]:
                            entry_subidx = subitem.getSubIdx()
                            if entry_subidx is None:
                                entry_subidx = "0"
                            subidx = ExtractHexDecValue(entry_subidx)
                            subitem_access = ""
                            subitem_pdomapping = ""
                            subitem_flags = subitem.getFlags()
                            if subitem_flags is not None:
                                access = subitem_flags.getAccess()
                                if access is not None:
                                    subitem_access = access.getcontent()
                                pdomapping = subitem_flags.getPdoMapping()
                                if pdomapping is not None:
                                    subitem_pdomapping = pdomapping.upper()
                            entries[(index, subidx)] = {
                                "Index": entry_index,
                                "SubIndex": entry_subidx,
                                "Name": "%s - %s" % 
                                        (entry_name.decode("utf-8"),
                                         ExtractName(subitem.getDisplayName(), 
                                                     subitem.getName()).decode("utf-8")),
                                "Type": subitem.getType(),
                                "BitSize": subitem.getBitSize(),
                                "Access": subitem_access, 
                                "PDOMapping": subitem_pdomapping}
                    else:
                        entry_access = ""
                        entry_pdomapping = ""
                        entry_flags = object.getFlags()
                        if entry_flags is not None:
                            access = entry_flags.getAccess()
                            if access is not None:
                                entry_access = access.getcontent()
                            pdomapping = entry_flags.getPdoMapping()
                            if pdomapping is not None:
                                entry_pdomapping = pdomapping.upper()
                        entries[(index, 0)] = {
                             "Index": entry_index,
                             "SubIndex": "0",
                             "Name": entry_name,
                             "Type": entry_type,
                             "BitSize": object.getBitSize(),
                             "Access": entry_access,
                             "PDOMapping": entry_pdomapping}
        
        for TxPdo in self.getTxPdo():
            ExtractPdoInfos(TxPdo, "Transmit", entries, limits)
        for RxPdo in self.getRxPdo():
            ExtractPdoInfos(RxPdo, "Receive", entries, limits)
        
        return entries
    setattr(cls, "GetEntriesList", GetEntriesList)

    def GetSyncManagers(self):
        sync_managers = []
        for sync_manager in self.getSm():
            sync_manager_infos = {}
            for name, value in [("Name", sync_manager.getcontent()),
                                ("Start Address", sync_manager.getStartAddress()),
                                ("Default Size", sync_manager.getDefaultSize()),
                                ("Control Byte", sync_manager.getControlByte()),
                                ("Enable", sync_manager.getEnable())]:
                if value is None:
                    value =""
                sync_manager_infos[name] = value
            sync_managers.append(sync_manager_infos)
        return sync_managers
    setattr(cls, "GetSyncManagers", GetSyncManagers)

def GroupItemCompare(x, y):
    if x["type"] == y["type"]:
        if x["type"] == ETHERCAT_GROUP:
            return cmp(x["order"], y["order"])
        else:
            return cmp(x["name"], y["name"])
    elif x["type"] == ETHERCAT_GROUP:
        return -1
    return 1

def SortGroupItems(group):
    for item in group["children"]:
        if item["type"] == ETHERCAT_GROUP:
            SortGroupItems(item)
    group["children"].sort(GroupItemCompare)

def ExtractPdoInfos(pdo, pdo_type, entries, limits=None):
    pdo_index = pdo.getIndex().getcontent()
    pdo_name = ExtractName(pdo.getName())
    for pdo_entry in pdo.getEntry():
        entry_index = pdo_entry.getIndex().getcontent()
        entry_subindex = pdo_entry.getSubIndex()
        index = ExtractHexDecValue(entry_index)
        subindex = ExtractHexDecValue(entry_subindex)
        
        if limits is None or limits[0] <= index <= limits[1]:
            entry = entries.get((index, subindex), None)
            if entry is not None:
                entry["PDO index"] = pdo_index
                entry["PDO name"] = pdo_name
                entry["PDO type"] = pdo_type
            else:
                entry_type = pdo_entry.getDataType()
                if entry_type is not None:
                    if pdo_type == "Transmit":
                        access = "ro"
                        pdomapping = "T"
                    else:
                        access = "wo"
                        pdomapping = "R"
                    entries[(index, subindex)] = {
                        "Index": entry_index,
                        "SubIndex": entry_subindex,
                        "Name": ExtractName(pdo_entry.getName()),
                        "Type": entry_type.getcontent(),
                        "Access": access,
                        "PDOMapping": pdomapping}

class ModulesLibrary:

    MODULES_EXTRA_PARAMS = [
        ("pdo_alignment", {
            "column_label": _("PDO alignment"), 
            "column_size": 150,
            "default": 8,
            "description": _(
"Minimal size in bits between 2 pdo entries")}),
        ("max_pdo_size", {
            "column_label": _("Max entries by PDO"),
            "column_size": 150,
            "default": 255,
            "description": _(
"""Maximal number of entries mapped in a PDO
including empty entries used for PDO alignment""")}),
        ("add_pdo", {
            "column_label": _("Creating new PDO"), 
            "column_size": 150,
            "default": 0,
            "description": _(
"""Adding a PDO not defined in default configuration
for mapping needed location variables
(1 if possible)""")})
    ]
    
    def __init__(self, path, parent_library=None):
        self.Path = path
        if not os.path.exists(self.Path):
            os.makedirs(self.Path)
        self.ParentLibrary = parent_library
        
        if parent_library is not None:
            self.LoadModules()
        else:
            self.Library = None
        self.LoadModulesExtraParams()
    
    def GetPath(self):
        return self.Path
    
    def GetModulesExtraParamsFilePath(self):
        return os.path.join(self.Path, "modules_extra_params.cfg")
    
    def LoadModules(self):
        self.Library = {}
        
        files = os.listdir(self.Path)
        for file in files:
            filepath = os.path.join(self.Path, file)
            if os.path.isfile(filepath) and os.path.splitext(filepath)[-1] == ".xml":
                xmlfile = open(filepath, 'r')
                xml_tree = minidom.parse(xmlfile)
                xmlfile.close()
                
                self.modules_infos = None
                for child in xml_tree.childNodes:
                    if child.nodeType == xml_tree.ELEMENT_NODE and child.nodeName == "EtherCATInfo":
                        self.modules_infos = EtherCATInfoClasses["EtherCATInfo.xsd"]["EtherCATInfo"]()
                        self.modules_infos.loadXMLTree(child)
                
                if self.modules_infos is not None:
                    vendor = self.modules_infos.getVendor()
                    
                    vendor_category = self.Library.setdefault(ExtractHexDecValue(vendor.getId()), 
                                                              {"name": ExtractName(vendor.getName(), _("Miscellaneous")), 
                                                               "groups": {}})
                    
                    for group in self.modules_infos.getDescriptions().getGroups().getGroup():
                        group_type = group.getType()
                        
                        vendor_category["groups"].setdefault(group_type, {"name": ExtractName(group.getName(), group_type), 
                                                                          "parent": group.getParentGroup(),
                                                                          "order": group.getSortOrder(), 
                                                                          "devices": []})
                    
                    for device in self.modules_infos.getDescriptions().getDevices().getDevice():
                        device_group = device.getGroupType()
                        if not vendor_category["groups"].has_key(device_group):
                            raise ValueError, "Not such group \"%\"" % device_group
                        vendor_category["groups"][device_group]["devices"].append((device.getType().getcontent(), device))

        return self.Library ## add by hwang 13.05.01

    def GetModulesLibrary(self, profile_filter=None):
        if self.Library is None:
            self.LoadModules()
        library = []
        for vendor_id, vendor in self.Library.iteritems():
            groups = []
            children_dict = {}
            for group_type, group in vendor["groups"].iteritems():
                group_infos = {"name": group["name"],
                               "order": group["order"],
                               "type": ETHERCAT_GROUP,
                               "infos": None,
                               "children": children_dict.setdefault(group_type, [])}
                device_dict = {}
                for device_type, device in group["devices"]:
                    if profile_filter is None or profile_filter in device.GetProfileNumbers():
                        product_code = device.getType().getProductCode()
                        revision_number = device.getType().getRevisionNo()
                        module_infos = {"device_type": device_type,
                                        "vendor": vendor_id,
                                        "product_code": product_code,
                                        "revision_number": revision_number}
                        module_infos.update(self.GetModuleExtraParams(vendor_id, product_code, revision_number))
                        device_infos = {"name": ExtractName(device.getName()),
                                        "type": ETHERCAT_DEVICE,
                                        "infos": module_infos,
                                        "children": []}
                        group_infos["children"].append(device_infos)
                        device_type_occurrences = device_dict.setdefault(device_type, [])
                        device_type_occurrences.append(device_infos)
                for device_type_occurrences in device_dict.itervalues():
                    if len(device_type_occurrences) > 1:
                        for occurrence in device_type_occurrences:
                            occurrence["name"] += _(" (rev. %s)") % occurrence["infos"]["revision_number"]
                if len(group_infos["children"]) > 0:
                    if group["parent"] is not None:
                        parent_children = children_dict.setdefault(group["parent"], [])
                        parent_children.append(group_infos)
                    else:
                        groups.append(group_infos)
            if len(groups) > 0:
                library.append({"name": vendor["name"],
                                "type": ETHERCAT_VENDOR,
                                "infos": None,
                                "children": groups})
        library.sort(lambda x, y: cmp(x["name"], y["name"]))
        return library

    def GetVendors(self):
        return [(vendor_id, vendor["name"]) for vendor_id, vendor in self.Library.items()]
    
    def GetModuleInfos(self, module_infos):
        vendor = ExtractHexDecValue(module_infos["vendor"])
        vendor_infos = self.Library.get(vendor)
        if vendor_infos is not None:
            for group_name, group_infos in vendor_infos["groups"].iteritems():
                for device_type, device_infos in group_infos["devices"]:
                    product_code = ExtractHexDecValue(device_infos.getType().getProductCode())
                    revision_number = ExtractHexDecValue(device_infos.getType().getRevisionNo())
                    if (product_code == ExtractHexDecValue(module_infos["product_code"]) and
                        revision_number == ExtractHexDecValue(module_infos["revision_number"])):
			self.cntdevice = device_infos ## add by hwang 13.05.01.
                        self.cntdeviceType = device_type  ## add by hwang 13.05.01.
                        return device_infos, self.GetModuleExtraParams(vendor, product_code, revision_number)
        return None, None
    
    def ImportModuleLibrary(self, filepath):
        if os.path.isfile(filepath):
            shutil.copy(filepath, self.Path)
            self.LoadModules()
            return True
        return False
    
    def LoadModulesExtraParams(self):
        self.ModulesExtraParams = {}
        
        csvfile_path = self.GetModulesExtraParamsFilePath()
        if os.path.exists(csvfile_path):
            csvfile = open(csvfile_path, "rb")
            sample = csvfile.read(1024)
            csvfile.seek(0)
            dialect = csv.Sniffer().sniff(sample)
            has_header = csv.Sniffer().has_header(sample)
            reader = csv.reader(csvfile, dialect)
            for row in reader:
                if has_header:
                    has_header = False
                else:
                    params_values = {}
                    for (param, param_infos), value in zip(
                        self.MODULES_EXTRA_PARAMS, row[3:]):
                        if value != "":
                            params_values[param] = int(value)
                    self.ModulesExtraParams[
                        tuple(map(int, row[:3]))] = params_values
            csvfile.close()
    
    def SaveModulesExtraParams(self):
        csvfile = open(self.GetModulesExtraParamsFilePath(), "wb")
        extra_params = [param for param, params_infos in self.MODULES_EXTRA_PARAMS]
        writer = csv.writer(csvfile, delimiter=';')
        writer.writerow(['Vendor', 'product_code', 'revision_number'] + extra_params)
        for (vendor, product_code, revision_number), module_extra_params in self.ModulesExtraParams.iteritems():
            writer.writerow([vendor, product_code, revision_number] + 
                            [module_extra_params.get(param, '') 
                             for param in extra_params])
        csvfile.close()
    
    def SetModuleExtraParam(self, vendor, product_code, revision_number, param, value):
        vendor = ExtractHexDecValue(vendor)
        product_code = ExtractHexDecValue(product_code)
        revision_number = ExtractHexDecValue(revision_number)
        
        module_infos = (vendor, product_code, revision_number)
        self.ModulesExtraParams.setdefault(module_infos, {})
        self.ModulesExtraParams[module_infos][param] = value
        
        self.SaveModulesExtraParams()
    
    def GetModuleExtraParams(self, vendor, product_code, revision_number):
        vendor = ExtractHexDecValue(vendor)
        product_code = ExtractHexDecValue(product_code)
        revision_number = ExtractHexDecValue(revision_number)
        
        if self.ParentLibrary is not None:
            extra_params = self.ParentLibrary.GetModuleExtraParams(vendor, product_code, revision_number)
        else:
            extra_params = {}
        
        extra_params.update(self.ModulesExtraParams.get((vendor, product_code, revision_number), {}))
        
        for param, param_infos in self.MODULES_EXTRA_PARAMS:
            extra_params.setdefault(param, param_infos["default"])
        
        return extra_params

USERDATA_DIR = wx.StandardPaths.Get().GetUserDataDir()
if wx.Platform != '__WXMSW__':
    USERDATA_DIR += '_files'

ModulesDatabase = ModulesLibrary(
    os.path.join(USERDATA_DIR, "ethercat_modules"))

class RootClass:
    
    CTNChildrenTypes = [("EthercatNode",_EthercatCTN,"Ethercat Master")]
    EditorType = LibraryEditor
    
    def __init__(self):
        self.ModulesLibrary = None
        self.LoadModulesLibrary()
    
    def GetIconName(self):
        return "Ethercat"
    
    def GetModulesLibraryPath(self, project_path=None):
        if project_path is None:
            project_path = self.CTNPath()
        return os.path.join(project_path, "modules") 
    
    def OnCTNSave(self, from_project_path=None):
        if from_project_path is not None:
            shutil.copytree(self.GetModulesLibraryPath(from_project_path),
                            self.GetModulesLibraryPath())
        return True
    
    def CTNGenerate_C(self, buildpath, locations):
        return [],"",False
    
    def LoadModulesLibrary(self):
        if self.ModulesLibrary is None:
            self.ModulesLibrary = ModulesLibrary(self.GetModulesLibraryPath(), ModulesDatabase)
        else:
            self.ModulesLibrary.LoadModulesLibrary()
    
    def GetModulesDatabaseInstance(self):
        return ModulesDatabase
    
    def GetModulesLibraryInstance(self):
        return self.ModulesLibrary
    
    def GetModulesLibrary(self, profile_filter=None):
        return self.ModulesLibrary.GetModulesLibrary(profile_filter)
    
    def GetVendors(self):
        return self.ModulesLibrary.GetVendors()
    
    def GetModuleInfos(self, module_infos):
        return self.ModulesLibrary.GetModuleInfos(module_infos)

# ---------- placed by hwang ----------------- #

    # by Chaerin 130212        
    def GetSmartViewInfos(self):
        
        # smart view elements' initial value
        eeprom_size = 128
        pdi_type = 0
        device_emulation = False
        vendor_id = '0x00000000'
        product_code = '0x00000000'
        revision_no = '0x00000000'
        serial_no = '0x00000000'
        mailbox_coe = False
        mailbox_soe = False
        mailbox_eoe = False
        mailbox_foe = False
        mailbox_aoe = False
        mailbox_bootstrapconf_outstart = '0'
        mailbox_bootstrapconf_outlength = '0'
        mailbox_bootstrapconf_instart = '0'
        mailbox_bootstrapconf_inlength = '0'
        mailbox_standardconf_outstart = '0'
        mailbox_standardconf_outlength = '0'
        mailbox_standardconf_instart = '0'
        mailbox_standardconf_inlength = '0'
        
        # self.cntdevice -> self.ModulesLibrary.cntdevice by hwang 13.05.01    
        # node of current device which is selected by user at ethercat slave node
        if self.ModulesLibrary.cntdevice is not None:

            for eeprom_element in self.ModulesLibrary.cntdevice.getEeprom().getcontent()["value"]:
                # get EEPROM Size; <Device>-<Eeprom>-<ByteSize>
                if eeprom_element["name"] == "ByteSize":
                    eeprom_size = eeprom_element["value"]
                        
                elif eeprom_element["name"] == "ConfigData":
                    configData_data = self.DecimalToHex(eeprom_element["value"]).split('x')[1]
                    # get PDI Type; <Device>-<Eeprom>-<ConfigData> address 0x00
                    pdi_type = int(str(configData_data)[0:2], 16)
                    # get state of Device Emulation; <Device>-<Eeprom>-<ConfigData> address 0x01
                    if len(configData_data) > 2 and (bin(int(str(configData_data[2:4]), 16)).split('b')[1].zfill(8))[7] == '1':
                        device_emulation = True

                elif eeprom_element["name"] == "BootStrap":
                    bootStrap_data = self.DecimalToHex(eeprom_element["value"]).split('x')[1].zfill(16)
                    # get Mailbox's Bootstrap Configuration; <Device>-<Eeprom>-<BootStrap>
                    mailbox_bootstrapconf_outstart = str(int(str(bootStrap_data[2:4]+bootStrap_data[0:2]), 16))
                    mailbox_bootstrapconf_outlength = str(int(str(bootStrap_data[6:8]+bootStrap_data[4:6]), 16))
                    mailbox_bootstrapconf_instart = str(int(str(bootStrap_data[10:12]+bootStrap_data[8:10]), 16))
                    mailbox_bootstrapconf_inlength = str(int(str(bootStrap_data[14:16]+bootStrap_data[12:14]), 16))
                                  
                
            # get supportable protocol types of Mailbox; <Device>-<Mailbox>
            mb=self.ModulesLibrary.cntdevice.getMailbox()
            if mb is not None:
                if mb.getAoE() is not None:
                    mailbox_aoe = True
                if mb.getEoE() is not None:
                    mailbox_eoe = True
                if mb.getCoE() is not None:
                    mailbox_coe = True
                if mb.getFoE() is not None:
                    mailbox_foe = True
                if mb.getSoE() is not None:
                    mailbox_soe = True
                
            # get Mailbox's Standard Configuration; <Device>-<sm>
            for sm_element in self.ModulesLibrary.cntdevice.getSm():
                if sm_element.getcontent() == "MBoxOut":
                    mailbox_standardconf_outstart = str(int(str(sm_element.getStartAddress()).split('x')[1].zfill(4), 16))
                    if str(sm_element.getDefaultSize())[0:2] == '#x':
                        mailbox_standardconf_outlength = str(int(str(sm_element.getDefaultSize()).split('x')[1], 16))
                    else:
                        mailbox_standardconf_outlength = str(sm_element.getDefaultSize())
                if sm_element.getcontent() == "MBoxIn":
                    mailbox_standardconf_instart = str(int(str(sm_element.getStartAddress()).split('x')[1].zfill(4), 16))
                    if str(sm_element.getDefaultSize())[0:2] == '#x':
                        mailbox_standardconf_inlength = str(int(str(sm_element.getDefaultSize()).split('x')[1], 16))
                    else:
                        mailbox_standardconf_inlength = str(sm_element.getDefaultSize())
                
            # device Identity
            ## vendor ID; It uses self.ModulesLibrary that was made already.
            ##            It checks device type. If device types are same each other, it takes vendor ID.
            for vendorId, vendor in self.ModulesLibrary.Library.iteritems(): # self.ModulesLibrary -> self.MoudulesLibrary.Library by hwang 13.05.01.
                for available_device in vendor["groups"][vendor["groups"].keys()[0]]["devices"]:
                    if available_device[0] == self.ModulesLibrary.cntdeviceType: # self.cntdeviceType -> self.ModulesLibrary.cntdeviceType by hwnag 13.05.01.
                        vendor_id = "0x" + self.DecimalToHex(vendorId).split('x')[1].zfill(8)
                        
            ## product code; <Device>-<Type>
            if self.ModulesLibrary.cntdevice.getType().getProductCode() is not None:
                product_code = self.ModulesLibrary.cntdevice.getType().getProductCode()
                if product_code[0:2] == '#x':
                    product_code = "0x" + product_code.split('x')[1].zfill(8)
                else:
                    product_code = "0x" + hex(product_code).split('x')[1].zfill(8)
                
            ## revision number; <Device>-<Type>
            if self.ModulesLibrary.cntdevice.getType().getRevisionNo() is not None:
                revision_no = self.ModulesLibrary.cntdevice.getType().getRevisionNo()
                if revision_no[0:2] == '#x':
                    revision_no = "0x" + revision_no.split('x')[1].zfill(8)
                else:
                    revision_no = "0x" + hex(revision_no).split('x')[1].zfill(8)
                
            ## serial number; <Device>-<Type>
            if self.ModulesLibrary.cntdevice.getType().getSerialNo() is not None:
                serial_no = self.ModulesLibrary.cntdevice.getType().getSerialNo()
                if serial_no[0:2] == '#x':
                    serial_no = "0x" + serial_no.split('x')[1].zfill(8)
                else:
                    serial_no = "0x" + hex(serial_no).split('x')[1].zfill(8)                        
            
                # smart view elements' dictionary
            smartview_infos = {"eeprom_size": eeprom_size,
                               "pdi_type": pdi_type,
                               "device_emulation": device_emulation,
                               "vendor_id": vendor_id,
                               "product_code": product_code,
                               "revision_no": revision_no,
                               "serial_no": serial_no,
                               "mailbox_coe": mailbox_coe,
                               "mailbox_soe": mailbox_soe,
                               "mailbox_eoe": mailbox_eoe,
                               "mailbox_foe": mailbox_foe,
                               "mailbox_aoe": mailbox_aoe,
                               "mailbox_bootstrapconf_outstart": mailbox_bootstrapconf_outstart,
                               "mailbox_bootstrapconf_outlength": mailbox_bootstrapconf_outlength,
                               "mailbox_bootstrapconf_instart": mailbox_bootstrapconf_instart,
                               "mailbox_bootstrapconf_inlength": mailbox_bootstrapconf_inlength,
                               "mailbox_standardconf_outstart": mailbox_standardconf_outstart,
                               "mailbox_standardconf_outlength": mailbox_standardconf_outlength,
                               "mailbox_standardconf_instart": mailbox_standardconf_instart,
                               "mailbox_standardconf_inlength": mailbox_standardconf_inlength}
                
            #test harnessprin
            #print smartview_infos
            
            return smartview_infos
        
        else:
            return None
        
    def DecimalToHex(self, decnum):
        velue_len = len(hex(decnum).split('x')[1].rstrip('L'))
        if (velue_len % 2) == 0:
            hex_len = velue_len
        else:
            hex_len = (velue_len / 2) * 2 + 2
        
        hex_data = hex(decnum).split('x')[1].rstrip('L').zfill(hex_len)
        data = "0x" + str(hex_data)
        
        return data
# ---------- end (placed by hwang) ---------------#

    # by Chaerin 20130509    
    # EEPROM binary creation using slave xml file
    def XmlToEeprom(self):
        
        eeprom = []
        data = ""
        eeprom_size = 0
        eeprom_binary = ""
        
        # node of current device which is selected by user at ethercat slave node
        if self.ModulesLibrary.cntdevice is not None:
            # get ConfigData for EEPROM 0x0000-0x000d; <Device>-<Eeprom>-<ConfigData>
            for eeprom_element in self.ModulesLibrary.cntdevice.getEeprom().getcontent()["value"]:
                if eeprom_element["name"] == "ConfigData":
                    data = self.DecimalToHex(eeprom_element["value"]).split('x')[1]
            # append eeprom contents
            for i in range(14):
                if data == "":
                    eeprom.append("00")
                else:
                    eeprom.append(data[0:2])
                data = data[2:len(data)]
            
            # calculate CRC for EEPROM 0x000e-0x000f
            crc = 0x48
            for segment in eeprom:
                for i in range(8):
                    bit = crc & 0x80
                    crc = (crc << 1) | ((int(segment, 16) >> (7 - i)) & 0x01)
                    if bit:
                        crc ^= 0x07   
            for k in range(8):
                bit = crc & 0x80
                crc <<= 1
                if bit:
                    crc ^= 0x07
            # append eeprom contents        
            eeprom.append(hex(crc)[len(hex(crc))-3:len(hex(crc))-1])
            eeprom.append("00")
            
            # get VendorID for EEPROM 0x0010-0x0013;
            for vendorID, vendor in self.ModulesLibrary.Library.iteritems():
                for available_device in vendor["groups"][vendor["groups"].keys()[0]]["devices"]:
                    if available_device[0] == self.ModulesLibrary.cntdeviceType:
                        data = self.DecimalToHex(vendorID).split('x')[1].zfill(8)
            # append eeprom cotents
            for i in range(4):
                if data == "":
                    eeprom.append("00")
                else:
                    eeprom.append(data[len(data)-2:len(data)])
                data = data[0:len(data)-2]
            
            # get Product Code for EEPROM 0x0014-0x0017;
            if self.ModulesLibrary.cntdevice.getType().getProductCode() is not None:
                data = self.ModulesLibrary.cntdevice.getType().getProductCode()
                if data[0:2] == '#x':
                    data = str(data.split('x')[1].zfill(8))
                else:
                    data = str(hex(data).split('x')[1].zfill(8))
            # append eeprom cotents
            for i in range(4):
                if data == "":
                    eeprom.append("00")
                else:
                    eeprom.append(data[len(data)-2:len(data)])
                data = data[0:len(data)-2]
            
            # get Revision Number for EEPROM 0x0018-0x001b;
            if self.ModulesLibrary.cntdevice.getType().getRevisionNo() is not None:
                data = self.ModulesLibrary.cntdevice.getType().getRevisionNo()
                if data[0:2] == '#x':
                    data = str(data.split('x')[1].zfill(8))
                else:
                    data = str(hex(data).split('x')[1].zfill(8))
            # append eeprom cotents
            for i in range(4):
                if data == "":
                    eeprom.append("00")
                else:
                    eeprom.append(data[len(data)-2:len(data)])
                data = data[0:len(data)-2]        
            
            # get Serial Number for EEPROM 0x001c-0x001f;
            if self.ModulesLibrary.cntdevice.getType().getSerialNo() is not None:
                serial_no = self.ModulesLibrary.cntdevice.getType().getSerialNo()
                if serial_no[0:2] == '#x':
                    serial_no = str(serial_no.split('x')[1].zfill(8))
                else:
                    serial_no = str(hex(serial_no).split('x')[1].zfill(8))      
            # append eeprom cotents
            for i in range(4):
                if data == "":
                    eeprom.append("00")
                else:
                    eeprom.append(data[len(data)-2:len(data)])
                data = data[0:len(data)-2] 
                
            # get Execution Delay for EEPROM 0x0020-0x0021; couldn't analyze yet
            eeprom.append("00")
            eeprom.append("00")
            
            # get Port0/1 Delay for EEPROM 0x0022-0x0025; couldn't analyze yet
            eeprom.append("00")
            eeprom.append("00")
            eeprom.append("00")
            eeprom.append("00")
            
            # Resereved for EEPROM 0x0026-0x0027;
            eeprom.append("00")
            eeprom.append("00")

            # get BootStrap for EEPROM 0x0028-0x002e; <Device>-<Eeprom>-<BootStrap>
            for eeprom_element in self.ModulesLibrary.cntdevice.getEeprom().getcontent()["value"]:
                if eeprom_element["name"] == "BootStrap":
                    data = self.DecimalToHex(eeprom_element["value"]).split('x')[1].zfill(16)
            # append eeprom contents
            for i in range(8):
                if data == "":
                    eeprom.append("00")
                else:
                    eeprom.append(data[0:2])
                data = data[2:len(data)]
            
            # get Standard Mailbox for EEPROM 0x0030-0x0037; <Device>-<sm>
            standard_receive_mailbox_offset = None
            standard_receive_mailbox_size = None
            standard_send_mailbox_offset = None
            standard_send_mailbox_size = None
            for sm_element in self.ModulesLibrary.cntdevice.getSm():
                if sm_element.getcontent() == "MBoxOut":
                    standard_receive_mailbox_offset = str(sm_element.getStartAddress()).split('x')[1].zfill(4)
                    if str(sm_element.getDefaultSize())[0:2] == '#x':
                        standard_receive_mailbox_size = str(sm_element.getDefaultSize()).split('x')[1].zfill(4)
                    else:
                        standard_receive_mailbox_size = self.DecimalToHex(int(str(sm_element.getDefaultSize()))).split('x')[1].zfill(4)
                if sm_element.getcontent() == "MBoxIn":
                    standard_send_mailbox_offset = str(sm_element.getStartAddress()).split('x')[1].zfill(4)
                    if str(sm_element.getDefaultSize())[0:2] == '#x':
                        standard_send_mailbox_size = str(sm_element.getDefaultSize()).split('x')[1].zfill(4)
                    else:
                        standard_send_mailbox_size = self.DecimalToHex(int(str(sm_element.getDefaultSize()))).split('x')[1].zfill(4)
            # append eeprom contents
            if standard_receive_mailbox_offset is None:
                eeprom.append("00")
                eeprom.append("00")
            else:
                eeprom.append(standard_receive_mailbox_offset[2:4])
                eeprom.append(standard_receive_mailbox_offset[0:2])
            if standard_receive_mailbox_size is None:
                eeprom.append("00")
                eeprom.append("00")
            else:
                eeprom.append(standard_receive_mailbox_size[2:4])
                eeprom.append(standard_receive_mailbox_size[0:2])
            if standard_send_mailbox_offset is None:
                eeprom.append("00")
                eeprom.append("00")
            else:
                eeprom.append(standard_send_mailbox_offset[2:4])
                eeprom.append(standard_send_mailbox_offset[0:2])
            if standard_send_mailbox_size is None:
                eeprom.append("00")
                eeprom.append("00")
            else:
                eeprom.append(standard_send_mailbox_size[2:4])
                eeprom.append(standard_send_mailbox_size[0:2])
            
            # get Mailbox Protocol for EEPROM 0x0038-0x0039;
            data = 0
            mb = self.ModulesLibrary.cntdevice.getMailbox()
            if mb is not None:
                if mb.getAoE() is not None:
                    data = data + 1
                if mb.getEoE() is not None:
                    data = data + 2
                if mb.getCoE() is not None:
                    data = data + 4
                if mb.getFoE() is not None:
                    data = data + 8
                if mb.getSoE() is not None:
                    data = data + 16 
                if mb.getVoE() is not None:
                    data = data + 32 
            data = hex(data).split('x')[1].zfill(4)
            # append eeprom contents
            eeprom.append(data[2:4])
            eeprom.append(data[0:2])
            
            # Resereved for EEPROM 0x003a-0x007b;
            for i in range(0x007b-0x003a+0x0001):
                eeprom.append("00")
            
            # get EEPROM size for EEPROM 0x007c-0x007d;
            data = ""
            for eeprom_element in self.ModulesLibrary.cntdevice.getEeprom().getcontent()["value"]:
                if eeprom_element["name"] == "ByteSize":
                    eeprom_size = int(str(eeprom_element["value"]))
                    data = self.DecimalToHex(int(str(eeprom_element["value"]))/1024*8-1).split('x')[1].zfill(4)
            # append eeprom contents
            if data == "":
                eeprom.append("00")
                eeprom.append("00")
            else:
                eeprom.append(data[2:4])
                eeprom.append(data[0:2])
                
            # Version for EEPROM 0x007e-0x007f; This Version is 1
            eeprom.append("01")
            eeprom.append("00")
            
            
            # append String Category data
            for data in self.ExportStringEeprom():
                eeprom.append(data)
                
            # append General Category data
            for data in self.ExportGeneralEeprom():
                eeprom.append(data)
                
            # append FMMU Category data
            for data in self.ExportFMMUEeprom():
                eeprom.append(data)
            
            # append SyncM Category data
            for data in self.ExportSyncMEeprom():
                eeprom.append(data)
                
            # append TxPDO Category data
            for data in self.ExportTxPDOEeprom():
                eeprom.append(data)
                
            # append RxPDO Category data
            for data in self.ExportRxPDOEeprom():
                eeprom.append(data)
                
            # append DC Category data
            for data in self.ExportDCEeprom():
                eeprom.append(data)
            
            # append padding
            padding = eeprom_size-len(eeprom)
            for i in range(padding):
                eeprom.append("ff")
            
            # convert binary code
            for index in range(eeprom_size):
                eeprom_binary = eeprom_binary +eeprom[index].decode('hex')
            #print eeprom_binary
            return eeprom_binary
    
    def ExportStringEeprom(self):
        eeprom = []
        self.strings = []
        data = "" 
        count = 0 # string counter
        padflag = False # padding if category length is odd
        #index information for General Category in EEPROM
        self.groupIdx = 0
        self.imgIdx = 0
        self.orderIdx = 0
        self.nameIdx = 0
        
        elementflag1 = False
        elementflag2 = False
        elementflag3 = False
        elementflag4 = False
        elementflag5 = False
        
        # vendor specific data
        ## element1; <EtherCATInfo>-<Descriptions>-<Devices>-<Device>-<Type>
        vendor_specific_data = ""
        for element in self.ModulesLibrary.cntdevice.getType().getcontent():
            data += element
        if data is not "" and type(data) == unicode:
            count += 1
            self.strings.append(data)
            elementflag1 = True
            self.orderIdx = count
            deviceType = data
            vendor_specific_data += hex(len(data)).split('x')[1].zfill(2)
            for character in range(len(data)):
                vendor_specific_data += hex(ord(data[character])).split('x')[1].zfill(2)
        data = ""
        ## element2-1; <EtherCATInfo>-<Descriptions>-<Devices>-<Device>-<GroupType>
        data = self.ModulesLibrary.cntdevice.getGroupType()
        if data is not None and type(data) == unicode:
            grouptype = data
            count += 1
            self.strings.append(data)
            elementflag2 = True
            self.groupIdx = count
            vendor_specific_data += hex(len(data)).split('x')[1].zfill(2)
            for character in range(len(data)):
                vendor_specific_data += hex(ord(data[character])).split('x')[1].zfill(2)
        if elementflag2 is False: ## element2-2; <EtherCATInfo>-<Groups>-<Group>-<Type>
            if self.ModulesLibrary.modules_infos is not None:
                for group in self.ModulesLibrary.modules_infos.getDescriptions().getGroups().getGroup():
                    data = group.getType()
                if data is not None and type(data) == unicode:
                    grouptype = data
                    count += 1
                    self.strings.append(data)
                    elementflag2 = True
                    self.groupIdx = count
                    vendor_specific_data += hex(len(data)).split('x')[1].zfill(2)
                    for character in range(len(data)):
                        vendor_specific_data += hex(ord(data[character])).split('x')[1].zfill(2)
        data = ""
        ## element3; <EtherCATInfo>-<Descriptions>-<Groups>-<Group>-<Name(LcId is "1033")>
        if self.ModulesLibrary.modules_infos is not None:
            for group in self.ModulesLibrary.modules_infos.getDescriptions().getGroups().getGroup():
                print 
                for name in group.getName():
                    if name.getLcId() == 1033:
                        data = name.getcontent()
        if data is not "" and type(data) == unicode:
            count += 1
            self.strings.append(data)
            elementflag3 = True
            vendor_specific_data += hex(len(data)).split('x')[1].zfill(2)
            for character in range(len(data)):
                vendor_specific_data += hex(ord(data[character])).split('x')[1].zfill(2)
        data = ""
        ## element4; <EtherCATInfo>-<Descriptions>-<Devices>-<Device>-<Name(LcId is "1033" or "1"?)>
        for element in self.ModulesLibrary.cntdevice.getName():
            if element.getLcId() == 1 or element.getLcId()==1033:
                data = element.getcontent()
        if data is not "" and type(data) == unicode:
            count += 1
            self.strings.append(data)
            elementflag4 = True
            self.nameIdx = count
            vendor_specific_data += hex(len(data)).split('x')[1].zfill(2)
            for character in range(len(data)):
                vendor_specific_data += hex(ord(data[character])).split('x')[1].zfill(2)
        data = ""
        ## element5-1; <EtherCATInfo>-<Descriptions>-<Devices>-<Device>-<Image16x14>
        if self.ModulesLibrary.cntdevice.getcontent() is not None:
            data = self.ModulesLibrary.cntdevice.getcontent()["value"]
            if data is not None and type(data) == unicode:
                count += 1
                self.strings.append(data)
                elementflag5 = True
                self.imgIdx = count
                vendor_specific_data += hex(len(data)).split('x')[1].zfill(2)
                for character in range(len(data)):
                    vendor_specific_data += hex(ord(data[character])).split('x')[1].zfill(2)
        ## element5-2; <EtherCATInfo>-<Descriptions>-<Groups>-<Group>-<Image 16x14>
        if elementflag5 is False:
            if self.ModulesLibrary.modules_infos is not None: 
                for group in self.ModulesLibrary.modules_infos.getDescriptions().getGroups().getGroup():
                    data = group.getcontent()["value"]
                    #print data
                if data is not None and type(data) == unicode:
                    count += 1
                    self.strings.append(data)
                    elementflag5 = True
                    self.imgIdx = count
                    vendor_specific_data += hex(len(data)).split('x')[1].zfill(2)
                    for character in range(len(data)):
                        vendor_specific_data += hex(ord(data[character])).split('x')[1].zfill(2)
        data = ""
        
        # DC related elements
        ## <EtherCATInfo>-<Descriptions>-<Devices>-<Device>-<Dc>-<OpMode>-<Name>
        dc_related_elements = ""
        if self.ModulesLibrary.cntdevice.getDc() is not None:
            for element in self.ModulesLibrary.cntdevice.getDc().getOpMode():
                data = element.getName()
                if data is not "":
                    count += 1
                    self.strings.append(data)
                    dc_related_elements += hex(len(data)).split('x')[1].zfill(2)
                    for character in range(len(data)):
                        dc_related_elements += hex(ord(data[character])).split('x')[1].zfill(2)
                    data = ""
        
        # Input elements(TxPDO)
        ## <EtherCATInfo>-<Descriptions>-<Devices>-<Device>-<TxPdo> ... Name
        input_elements = ""
        inputs = []
        for element in self.ModulesLibrary.cntdevice.getTxPdo():
            for name in element.getName():
                data = name.getcontent()
            #for pfl in self.cntdevice.getProfile():
            #    for pfl_element in pfl.getcontent()["value"]:
            #        if pfl_element["name"] == "Dictionary":
            #            for obj in pfl_element["value"].getObjects().getObject():
            #                if obj.getIndex().getcontent() == element.getIndex().getcontent():
            #                    for name in obj.getName():
            #                        data = name.getcontent()
            #                        print data
            for input in inputs: #for eliminating duplicated name
                if data == input: 
                    data = ""
            if data is not "":
                count += 1
                self.strings.append(data)
                inputs.append(data)
                input_elements += hex(len(data)).split('x')[1].zfill(2)
                for character in range(len(data)):
                    input_elements += hex(ord(data[character])).split('x')[1].zfill(2)
                data = ""            
            for entry in element.getEntry(): #in entry
                #for pfl in self.cntdevice.getProfile():
                #    for pfl_element in pfl.getcontent()["value"]:
                #        if pfl_element["name"] == "Dictionary":
                #            for obj in pfl_element["value"].getObjects().getObject():
                #                if obj.getIndex().getcontent() == entry.getIndex().getcontent():
                #                    for name in obj.getName():
                #                        data = name.getcontent()
                for name in entry.getName():
                    data = name.getcontent()
                for input in inputs: #for eliminating duplicated name
                    if data == input: 
                        data = ""
                if data is not "":
                    count += 1
                    self.strings.append(data)
                    inputs.append(data)
                    input_elements += hex(len(data)).split('x')[1].zfill(2)
                    for character in range(len(data)):
                        input_elements += hex(ord(data[character])).split('x')[1].zfill(2)
                    data = ""
        
        # Output elements(RxPDO)
        ## <EtherCATInfo>-<Descriptions>-<Devices>-<Device>-<RxPdo> ... Name
        output_elements = ""
        outputs = []
        for element in self.ModulesLibrary.cntdevice.getRxPdo():
            for name in element.getName():
                data = name.getcontent()
            for output in outputs: #for eliminating duplicated name
                if data == output: 
                    data = ""
            if data is not "":
                count += 1
                self.strings.append(data)
                outputs.append(data)
                output_elements += hex(len(data)).split('x')[1].zfill(2)
                for character in range(len(data)):
                    output_elements += hex(ord(data[character])).split('x')[1].zfill(2)
                data = ""            
            for entry in element.getEntry(): #in entry
                for name in entry.getName():
                    data = name.getcontent()
                for output in outputs: #for eliminating duplicated name
                    if data == output: 
                        data = ""
                if data is not "":
                    count += 1
                    self.strings.append(data)
                    outputs.append(data)
                    output_elements += hex(len(data)).split('x')[1].zfill(2)
                    for character in range(len(data)):
                        output_elements += hex(ord(data[character])).split('x')[1].zfill(2)
                    data = ""     
        
        # form eeprom data
        ## category header
        eeprom.append("0a")
        eeprom.append("00")
        ## category length (word); "+2" is the length of string's total number
        length = len(vendor_specific_data + dc_related_elements + input_elements + output_elements)+2
        if length%4 == 0:
            pass
        else:
            length +=length%4
            padflag = True
        eeprom.append(hex(length/4).split('x')[1].zfill(4)[2:4])
        eeprom.append(hex(length/4).split('x')[1].zfill(4)[0:2])
        ## total numbers of strings
        eeprom.append(hex(count).split('x')[1].zfill(2))
        ## vendor specific data
        for i in range(len(vendor_specific_data)/2):
            if vendor_specific_data == "":
                eeprom.append("00")
            else:
                eeprom.append(vendor_specific_data[0:2])
            vendor_specific_data = vendor_specific_data[2:len(vendor_specific_data)]        
        ## dc related elements
        for i in range(len(dc_related_elements)/2):
            if dc_related_elements == "":
                eeprom.append("00")
            else:
                eeprom.append(dc_related_elements[0:2])
            dc_related_elements = dc_related_elements[2:len(dc_related_elements)]   
        
        ## input elements
        for i in range(len(input_elements)/2):
            if input_elements == "":
                eeprom.append("00")
            else:
                eeprom.append(input_elements[0:2])
            input_elements = input_elements[2:len(input_elements)]
                    
        ## output elements
        for i in range(len(output_elements)/2):
            if output_elements == "":
                eeprom.append("00")
            else:
                eeprom.append(output_elements[0:2])
            output_elements = output_elements[2:len(output_elements)]
                    
        ## padding for odd bytes length
        if padflag is True:
            eeprom.append("ff")
        
        return eeprom
    
    def ExportGeneralEeprom(self):
        eeprom = []
        data = ""
        
        # category header
        eeprom.append("1e")
        eeprom.append("00")
        # category length
        eeprom.append("10")
        eeprom.append("00")
        # word 1 ... Group Type index and Image index in STRINGS Category
        eeprom.append(hex(self.groupIdx).split('x')[1].zfill(2))
        eeprom.append(hex(self.imgIdx).split('x')[1].zfill(2))
        # word 2 ... Device Type index and Device Name index in STRINGS Category
        eeprom.append(hex(self.orderIdx).split('x')[1].zfill(2))
        eeprom.append(hex(self.nameIdx).split('x')[1].zfill(2))
        # word 3 ... Physical Layer Port info. and CoE Details
        eeprom.append("01") #Physical Layer Port info... assume 01
        ## CoE Details; <EtherCATInfo>-<Descriptions>-<Devices>-<Device>-<Mailbox>-<CoE>
        enSdo = False # for bit 0
        enSdoInfo = False # for bit 1
        enPdoAssign = False # for bit 2
        enPdoConfig = False # for bit 3
        enUpload = False # for bit 4
        enSdoCompAcs = False # for bit 5
        mb = self.ModulesLibrary.cntdevice.getMailbox()
        if mb is not None :
            if mb.getCoE() is not None:
                enSdo = True 
                if mb.getCoE().getSdoInfo() == 1 or mb.getCoE().getSdoInfo() == True:
                    enSdoInfo = True
                if mb.getCoE().getPdoAssign() == 1 or mb.getCoE().getPdoAssign() == True:
                    enPdoAssign = True
                if mb.getCoE().getPdoConfig() == 1 or mb.getCoE().getPdoConfig() == True:
                    enPdoConfig = True
                if mb.getCoE().getPdoUpload() == 1 or mb.getCoE().getPdoUpload() == True:
                    enUpload = True
                if mb.getCoE().getCompleteAccess() == 1 or mb.getCoE().getCompleteAccess() == True:
                    enSdoCompAcs = True
        coe_details = "0b"+"00"+str(int(enSdoCompAcs))+str(int(enUpload))+str(int(enPdoConfig))+str(int(enPdoAssign))+str(int(enSdoInfo))+str(int(enSdo))
        eeprom.append(hex(int(coe_details, 2)).split('x')[1].zfill(2))
        # word 4 ... FoE Datails and EoE Details
        ## FoE Details; <EtherCATInfo>-<Descriptions>-<Devices>-<Device>-<Mailbox>-<FoE>
        if mb is not None and mb.getFoE() is not None:
            eeprom.append("01")
        else:
            eeprom.append("00")
        ## EoE Details; <EtherCATInfo>-<Descriptions>-<Devices>-<Device>-<Mailbox>-<EoE>
        if mb is not None and mb.getEoE() is not None:
            eeprom.append("01")
        else:
            eeprom.append("00")
        # word 5 ... SoE Channels(reserved) and DS402 Channels
        ## SoE Details; <EtherCATInfo>-<Descriptions>-<Devices>-<Device>-<Mailbox>-<SoE>
        if mb is not None and mb.getSoE() is not None:
            eeprom.append("01")
        else:
            eeprom.append("00")
        ## DS402Channels; <EtherCATInfo>-<Descriptions>-<Devices>-<Device>-<Mailbox>-<CoE>: DS402Channels
        if mb is not None and (mb.getCoE().getDS402Channels() == 1 or 
                               mb.getCoE().getDS402Channels() == True):
            eeprom.append("01")
        else:
            eeprom.append("00")
        # word 6 ... SysmanClass(reserved) and Flags
        eeprom.append("00") # reserved
        ## Flags ...
        enSafeOp = False
        enLrw = False
        if self.ModulesLibrary.cntdevice.getType().getTcCfgModeSafeOp() == 1 or self.ModulesLibrary.cntdevice.getType().getTcCfgModeSafeOp() == True:
            enSafeOp = True
        if self.ModulesLibrary.cntdevice.getType().getUseLrdLwr() == 1 or self.ModulesLibrary.cntdevice.getType().getUseLrdLwr() == True:
            enLrw = True
        if enSafeOp is False and enLrw is False: #assume...
            eeprom.append("04")
        else:
            flags = "0b"+"000000"+str(int(enLrw))+str(int(enSafeOp))
            eeprom.append(hex(int(flags, 2)).split('x')[1].zfill(2)) 
        # word 7 ... Current On EBus (assume 0x0000)
        eeprom.append("00")
        eeprom.append("00")
        # after word 7; couldn't analyze yet
        eeprom.append("03")
        eeprom.append("00")
        eeprom.append("11")
        eeprom.append("00")
        eeprom.append("00")
        eeprom.append("00")
        eeprom.append("00")
        eeprom.append("00")
        eeprom.append("00")
        eeprom.append("00")
        eeprom.append("00")
        eeprom.append("00")
        eeprom.append("00")
        eeprom.append("00")
        eeprom.append("00")
        eeprom.append("00")
        eeprom.append("00")
        eeprom.append("00")
        
        return eeprom
    
    def ExportFMMUEeprom(self):
        eeprom = []
        data = ""
        count = 0 # The number of Fmmu
        padflag = False
        
        # get data
        for fmmu in self.ModulesLibrary.cntdevice.getFmmu():
            count += 1
            if fmmu.getcontent() == "Outputs":
                data += "01"
            if fmmu.getcontent() == "Inputs":
                data += "02"
            if fmmu.getcontent() == "MBoxState":
                data += "03"
        
        # form eeprom data
        if data is not "":
            ## category header
            eeprom.append("28")
            eeprom.append("00")
            ## category length
            if count%2 == 1:
                padflag = True
                eeprom.append(hex((count+1)/2).split('x')[1].zfill(4)[2:4])
                eeprom.append(hex((count+1)/2).split('x')[1].zfill(4)[0:2])
            else: 
                eeprom.append(hex((count)/2).split('x')[1].zfill(4)[2:4])
                eeprom.append(hex((count)/2).split('x')[1].zfill(4)[0:2])
            ## append data
            for i in range(count):
                if data == "":
                    eeprom.append("00")
                else:
                    eeprom.append(data[0:2])
                data = data[2:len(data)]
            ## padding for odd bytes length
            if padflag is True:
                eeprom.append("ff")       
            
        return eeprom
    
    def ExportSyncMEeprom(self):
        eeprom = []
        data = ""
        number = {"MBoxOut":"01", "MBoxIn":"02", "Outputs":"03", "Inputs":"04"}
        
        # get data
        for sm in self.ModulesLibrary.cntdevice.getSm():
            if sm.getStartAddress() is not None:
                if sm.getStartAddress()[0:2] == "#x":
                    data += str(sm.getStartAddress()).split('x')[1].zfill(4)[2:4]
                    data += str(sm.getStartAddress()).split('x')[1].zfill(4)[0:2]
                else:
                    data += hex(sm.getStartAddress()).split('x')[1].zfill(4)[2:4]
                    data += hex(sm.getStartAddress()).split('x')[1].zfill(4)[0:2]
            else:
                data += "0000"
            if sm.getDefaultSize() is not None:
                if sm.getDefaultSize()[0:2] == "#x":
                    data += str(sm.getDefaultSize()).split('x')[1].zfill(4)[2:4]
                    data += str(sm.getDefaultSize()).split('x')[1].zfill(4)[0:2]
                else:
                    data += hex(int(sm.getDefaultSize())).split('x')[1].zfill(4)[2:4]
                    data += hex(int(sm.getDefaultSize())).split('x')[1].zfill(4)[0:2]
            else:
                data += "0000"
            if sm.getControlByte() is not None:
                if sm.getControlByte()[0:2] == "#x":
                    data += str(sm.getControlByte()).split('x')[1].zfill(4)[2:4]
                    data += str(sm.getControlByte()).split('x')[1].zfill(4)[0:2]
                else:
                    data += hex(int(sm.getControlByte())).split('x')[1].zfill(4)[2:4]
                    data += hex(int(sm.getControlByte())).split('x')[1].zfill(4)[0:2]
            else:
                data += "0000"               
            if sm.getEnable() == "1" or sm.getEnable() == True:
                data += "01"
            else:
                data += "00"
            data += number[sm.getcontent()]
            
        # form eeprom data
        if data is not "":
            ## category header
            eeprom.append("29")
            eeprom.append("00")
            ## category length 
            eeprom.append(hex(len(data)/4).split('x')[1].zfill(4)[2:4])
            eeprom.append(hex(len(data)/4).split('x')[1].zfill(4)[0:2])
            ## append data
            for i in range(len(data)/2):
                if data == "":
                    eeprom.append("00")
                else:
                    eeprom.append(data[0:2])
                data = data[2:len(data)]

        return eeprom
    
    def ExportTxPDOEeprom(self):
        eeprom = []
        data = ""
        count = 0
        enFixed = False
        enMandatory = False
        enVirtual = False
        
        # get data
        for element in self.ModulesLibrary.cntdevice.getTxPdo():
            ## PDO Index
            if element.getIndex().getcontent()[0:2] == "#x":
                data += element.getIndex().getcontent().split('x')[1].zfill(4)[2:4]
                data += element.getIndex().getcontent().split('x')[1].zfill(4)[0:2]
            else:
                data += hex(element.getIndex().getcontent()).split('x')[1].zfill(4)[2:4]
                data += hex(element.getIndex().getcontent()).split('x')[1].zfill(4)[0:2]
            ## Number of Entries
            data += hex(len(element.getEntry())).split('x')[1].zfill(2)
            ## Related Sync Manager
            if element.getSm() is not None:
                data += hex(element.getSm()).split('x')[1].zfill(2)
            else:
                data += "ff"
            ## Reference to DC Synch ... assume 0
            data += "00"
            ## Name Index
            objname = ""
            for name in element.getName():
                objname = name.getcontent()
            for name in self.strings:
                count += 1
                if objname == name:
                    break
            if len(self.strings) == count:
                data += "00"
            else:
                data += hex(count).split('x')[1].zfill(2)
            count = 0
            ## Flags; by Fixed, Mandatory, Virtual attributes ?
            if element.getFixed() == True or element.getFixed() == 1:
                enFixed = True
            if element.getMandatory() == True or element.getMandatory() == 1:
                enMandatory = True
            if element.getVirtual() == True or element.getVirtual():
                enVirtual = True
            data += str(int(enFixed)) + str(int(enMandatory)) + str(int(enVirtual)) + "0"
            ## in Entry
            for entry in element.getEntry():
                ### Entry Index
                if entry.getIndex().getcontent()[0:2] == "#x":
                    data += entry.getIndex().getcontent().split('x')[1].zfill(4)[2:4]
                    data += entry.getIndex().getcontent().split('x')[1].zfill(4)[0:2]
                else:
                    data += hex(int(entry.getIndex().getcontent())).split('x')[1].zfill(4)[2:4]
                    data += hex(int(entry.getIndex().getcontent())).split('x')[1].zfill(4)[0:2]
                ### Subindex
                data += hex(int(entry.getSubIndex())).split('x')[1].zfill(2)
                ### Entry Name Index
                objname = ""
                for name in entry.getName():
                    objname = name.getcontent()
                for name in self.strings:
                    count += 1
                    if objname == name:
                        break
                if len(self.strings) == count:
                    data += "00"
                else:
                    data += hex(count).split('x')[1].zfill(2)
                count = 0
                ### DataType ... 
                if entry.getDataType() is not None:
                    if entry.getDataType().getcontent() == "BOOL":
                        data += "01"
                    elif entry.getDataType().getcontent() == "SINT":
                        data += "02"
                    elif entry.getDataType().getcontent() == "INT":
                        data += "03"
                    elif entry.getDataType().getcontent() == "DINT":
                        data += "04"
                    elif entry.getDataType().getcontent() == "USINT":
                        data += "05"
                    elif entry.getDataType().getcontent() == "UINT":
                        data += "06"
                    elif entry.getDataType().getcontent() == "UDINT":
                        data += "07"
                    elif entry.getDataType().getcontent() == "ULINT":
                        data += "1b"
                    elif entry.getDataType().getcontent() == "BIT2":
                        data += "31"
                else:
                    data += "00"
                ### BitLen
                if entry.getBitLen() is not None:
                    data += hex(int(entry.getBitLen())).split('x')[1].zfill(2)
                else:
                    data += "00"
                ### Flags; by Fixed attributes ?
                enFixed = False
                if entry.getFixed() == True or entry.getFixed() == 1:
                    enFixed = True
                data += str(int(enFixed)) + "000"
        
        # form eeprom data
        if data is not "":
            ## category header
            eeprom.append("32")
            eeprom.append("00")
            ## category length 
            eeprom.append(hex(len(data)/4).split('x')[1].zfill(4)[2:4])
            eeprom.append(hex(len(data)/4).split('x')[1].zfill(4)[0:2])
            ## append data
            data = str(data.lower())
            for i in range(len(data)/2):
                if data == "":
                    eeprom.append("00")
                else:
                    eeprom.append(data[0:2])
                data = data[2:len(data)]
        
        return eeprom
    
    def ExportRxPDOEeprom(self):
        eeprom = []
        data = ""
        count = 0
        enFixed = False
        enMandatory = False
        enVirtual = False
        
        # get data
        for element in self.ModulesLibrary.cntdevice.getRxPdo():
            ## PDO Index
            if element.getIndex().getcontent()[0:2] == "#x":
                data += element.getIndex().getcontent().split('x')[1].zfill(4)[2:4]
                data += element.getIndex().getcontent().split('x')[1].zfill(4)[0:2]
            else:
                data += hex(element.getIndex().getcontent()).split('x')[1].zfill(4)[2:4]
                data += hex(element.getIndex().getcontent()).split('x')[1].zfill(4)[0:2]
            ## Number of Entries
            data += hex(len(element.getEntry())).split('x')[1].zfill(2)
            ## Related Sync Manager
            if element.getSm() is not None:
                data += hex(element.getSm()).split('x')[1].zfill(2)
            else:
                data += "ff"
            ## Reference to DC Synch ... assume 0
            data += "00"
            ## Name Index
            objname = ""
            for name in element.getName():
                objname = name.getcontent()
            for name in self.strings:
                count += 1
                if objname == name:
                    break
            if len(self.strings) == count:
                data += "00"
            else:
                data += hex(count).split('x')[1].zfill(2)
            count = 0
            ## Flags; by Fixed, Mandatory, Virtual attributes ?
            if element.getFixed() == True or element.getFixed() == 1:
                enFixed = True
            if element.getMandatory() == True or element.getMandatory() == 1:
                enMandatory = True
            if element.getVirtual() == True or element.getVirtual():
                enVirtual = True
            data += str(int(enFixed)) + str(int(enMandatory)) + str(int(enVirtual)) + "0"
            ## in Entry
            for entry in element.getEntry():
                ### Entry Index
                if entry.getIndex().getcontent()[0:2] == "#x":
                    data += entry.getIndex().getcontent().split('x')[1].zfill(4)[2:4]
                    data += entry.getIndex().getcontent().split('x')[1].zfill(4)[0:2]
                else:
                    data += hex(int(entry.getIndex().getcontent())).split('x')[1].zfill(4)[2:4]
                    data += hex(int(entry.getIndex().getcontent())).split('x')[1].zfill(4)[0:2]
                ### Subindex
                data += hex(int(entry.getSubIndex())).split('x')[1].zfill(2)
                ### Entry Name Index
                objname = ""
                for name in entry.getName():
                    objname = name.getcontent()
                for name in self.strings:

                    count += 1
                    if objname == name:
                        break
                if len(self.strings) == count:
                    data += "00"
                else:
                    data += hex(count).split('x')[1].zfill(2)
                count = 0
                ### DataType ... 
                if entry.getDataType() is not None:
                    if entry.getDataType().getcontent() == "BOOL":
                        data += "01"
                    elif entry.getDataType().getcontent() == "SINT":
                        data += "02"
                    elif entry.getDataType().getcontent() == "INT":
                        data += "03"
                    elif entry.getDataType().getcontent() == "DINT":
                        data += "04"
                    elif entry.getDataType().getcontent() == "USINT":
                        data += "05"
                    elif entry.getDataType().getcontent() == "UINT":
                        data += "06"
                    elif entry.getDataType().getcontent() == "UDINT":
                        data += "07"
                    elif entry.getDataType().getcontent() == "ULINT":
                        data += "1b"
                    elif entry.getDataType().getcontent() == "BIT2":
                        data += "31"
                    else:
                        data += "00"
                else:
                    data += "00"
                ### BitLen
                if entry.getBitLen() is not None:
                    data += hex(int(entry.getBitLen())).split('x')[1].zfill(2)
                else:
                    data += "00"
                ### Flags; by Fixed attributes ?
                enFixed = False
                if entry.getFixed() == True or entry.getFixed() == 1:
                    enFixed = True
                data += str(int(enFixed)) + "000"
        
        # form eeprom data
        if data is not "":
            ## category header
            eeprom.append("33")
            eeprom.append("00")
            ## category length 
            eeprom.append(hex(len(data)/4).split('x')[1].zfill(4)[2:4])
            eeprom.append(hex(len(data)/4).split('x')[1].zfill(4)[0:2])
            ## append data
            data = str(data.lower())
            for i in range(len(data)/2):
                if data == "":
                    eeprom.append("00")
                else:
                    eeprom.append(data[0:2])
                data = data[2:len(data)]
        
        return eeprom
    
    def ExportDCEeprom(self):
        eeprom = []
        data = ""
        count = 0
        namecount = 0
        
        # get data
        if self.ModulesLibrary.cntdevice.getDc() is not None:
            for element in self.ModulesLibrary.cntdevice.getDc().getOpMode():
                count += 1
                ## assume that word 1-7 are 0x0000
                data += "0000"
                data += "0000"
                data += "0000"
                data += "0000"
                data += "0000"
                data += "0000"
                data += "0000"
                ## word 8-10
                ### AssignActivate
                if element.getAssignActivate() is not None:
                    if element.getAssignActivate()[0:2] == "#x":
                        data += element.getAssignActivate().split('x')[1].zfill(4)[2:4]
                        data += element.getAssignActivate().split('x')[1].zfill(4)[0:2]
                    else:
                        data += hex(int(element.getAssignActivate())).split('x')[1].zfill(4)[2:4]
                        data += hex(int(element.getAssignActivate())).split('x')[1].zfill(4)[0:2]
                else:
                    data += "0000"
                ### Factor of CycleTimeSync0 ? and default is 1?
                if element.getCycleTimeSync0() is not None:
                    if element.getCycleTimeSync0().getFactor() is not None:
                        data += hex(int(element.getCycleTimeSync0().getFactor())).split('x')[1].zfill(2)
                        data += "00"
                    else:
                        data += "0100"
                else:
                    data += "0100"
                ### Index of Name in STRINGS Category
                ## Name Index
                objname = ""
                for name in element.getName():
                    objname += name
                #print objname
                for name in self.strings:
                    namecount += 1
                    if objname == name:
                        break
                if len(self.strings) == namecount:
                    data += "00"
                else:
                    data += hex(namecount).split('x')[1].zfill(2)
                namecount = 0
                data += "00"
                ## assume that word 11-12 are 0x0000
                data += "0000"
                data += "0000"
                
        # form eeprom data
        if data is not "":
            ## category header
            eeprom.append("3c")
            eeprom.append("00")
            ## category length 
            eeprom.append(hex(len(data)/4).split('x')[1].zfill(4)[2:4])
            eeprom.append(hex(len(data)/4).split('x')[1].zfill(4)[0:2])
            ## append data
            data = str(data.lower())
            for i in range(len(data)/2):
                if data == "":
                    eeprom.append("00")
                else:
                    eeprom.append(data[0:2])
                data = data[2:len(data)]
    
        return eeprom                    
