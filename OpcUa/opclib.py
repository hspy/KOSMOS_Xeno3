
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
