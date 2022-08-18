import os
import re
from types import TupleType

import wx
import wx.grid
import wx.gizmos
import wx.lib.buttons

from plcopen.structures import IEC_KEYWORDS, TestIdentifier
from controls import CustomGrid, CustomTable, FolderTree
from editors.ConfTreeNodeEditor import ConfTreeNodeEditor, SCROLLBAR_UNIT
from util.BitmapLibrary import GetBitmap
from controls.CustomStyledTextCtrl import NAVIGATION_KEYS

# ------------ for SDO Management --------------------
import string
import wx.grid as gridlib
#-------------------------------------------------------------

[ETHERCAT_VENDOR, ETHERCAT_GROUP, ETHERCAT_DEVICE] = range(3)

def AppendMenu(parent, help, id, kind, text):
    if wx.VERSION >= (2, 6, 0):
        parent.Append(help=help, id=id, kind=kind, text=text)
    else:
        parent.Append(helpString=help, id=id, kind=kind, item=text)

def GetVariablesTableColnames(position=False):
    _ = lambda x : x
    colname = ["#"]
    if position:
        colname.append(_("Position"))
    return colname + [_("Name"), _("Index"), _("SubIndex"), _("Type"), _("Access")]

ACCESS_TYPES = {
    'ro': 'R',
    'wo': 'W',
    'rw': 'R/W'}

def GetAccessValue(access, pdo_mapping):
    value = "SDO: %s" % ACCESS_TYPES.get(access, "")
    if pdo_mapping != "":
        value += ", PDO: %s" % pdo_mapping
    return value

VARIABLES_FILTERS = [
    (_("All"), (0x0000, 0xffff)),
    (_("Communication Parameters"), (0x1000, 0x1fff)),
    (_("Manufacturer Specific"), (0x2000, 0x5fff)),
    (_("Standardized Device Profile"), (0x6000, 0x9fff))]

VARIABLE_INDEX_FILTER_FORMAT = _("Variable Index: #x%4.4X")

ETHERCAT_INDEX_MODEL = re.compile("#x([0-9a-fA-F]{0,4})$")
ETHERCAT_SUBINDEX_MODEL = re.compile("#x([0-9a-fA-F]{0,2})$")
LOCATION_MODEL = re.compile("(?:%[IQM](?:[XBWLD]?([0-9]+(?:\.[0-9]+)*)))$")

# ----------------------------- For Sync Manager Table -----------------------------------
def GetSyncManagersTableColnames():
    _ = lambda x : x
    return ["#", _("Name"), _("Start Address"), _("Default Size"), _("Control Byte"), _("Enable")]

class SyncManagersTable(CustomTable):
    
    def GetValue(self, row, col):
        if row < self.GetNumberRows():
            if col == 0:
                return row
            return self.data[row].get(self.GetColLabelValue(col, False), "")       
#------------------------------------------------------------------------------------

class NodeVariablesSizer(wx.FlexGridSizer):
    
    def __init__(self, parent, controler, position_column=False):
        wx.FlexGridSizer.__init__(self, cols=1, hgap=0, rows=2, vgap=5)
        self.AddGrowableCol(0)
        self.AddGrowableRow(1)
        
        self.Controler = controler
        self.PositionColumn = position_column
        
        self.VariablesFilter = wx.ComboBox(parent, style=wx.TE_PROCESS_ENTER)
        self.VariablesFilter.Bind(wx.EVT_COMBOBOX, self.OnVariablesFilterChanged)
        self.VariablesFilter.Bind(wx.EVT_TEXT_ENTER, self.OnVariablesFilterChanged)
        self.VariablesFilter.Bind(wx.EVT_CHAR, self.OnVariablesFilterKeyDown)
        self.AddWindow(self.VariablesFilter, flag=wx.GROW)
        
        self.VariablesGrid = wx.gizmos.TreeListCtrl(parent, 
                style=wx.TR_DEFAULT_STYLE |
                      wx.TR_ROW_LINES |
                      wx.TR_COLUMN_LINES |
                      wx.TR_HIDE_ROOT |
                      wx.TR_FULL_ROW_HIGHLIGHT)
        self.VariablesGrid.GetMainWindow().Bind(wx.EVT_LEFT_DOWN,
            self.OnVariablesGridLeftClick)
        self.AddWindow(self.VariablesGrid, flag=wx.GROW)
        
        self.Filters = []
        for desc, value in VARIABLES_FILTERS:
            self.VariablesFilter.Append(desc)
            self.Filters.append(value)
        
        self.VariablesFilter.SetSelection(0)
        self.CurrentFilter = self.Filters[0]
        self.VariablesFilterFirstCharacter = True
        
        if position_column:
            for colname, colsize, colalign in zip(GetVariablesTableColnames(position_column),
                                                  [40, 80, 350, 80, 100, 80, 150],
                                                  [wx.ALIGN_RIGHT, wx.ALIGN_RIGHT, wx.ALIGN_LEFT, 
                                                   wx.ALIGN_RIGHT, wx.ALIGN_RIGHT, wx.ALIGN_LEFT, 
                                                   wx.ALIGN_LEFT]):
                self.VariablesGrid.AddColumn(_(colname), colsize, colalign)
            self.VariablesGrid.SetMainColumn(2)
        else:
            for colname, colsize, colalign in zip(GetVariablesTableColnames(),
                                                  [40, 350, 80, 100, 80, 150],
                                                  [wx.ALIGN_RIGHT, wx.ALIGN_LEFT, wx.ALIGN_RIGHT, 
                                                   wx.ALIGN_RIGHT, wx.ALIGN_LEFT, wx.ALIGN_LEFT]):
                self.VariablesGrid.AddColumn(_(colname), colsize, colalign)
            self.VariablesGrid.SetMainColumn(1)
    
    def RefreshView(self):
        entries = self.Controler.GetSlaveVariables(self.CurrentFilter)
        self.RefreshVariablesGrid(entries)
    
    def RefreshVariablesGrid(self, entries):
        root = self.VariablesGrid.GetRootItem()
        if not root.IsOk():
            root = self.VariablesGrid.AddRoot(_("Slave entries"))
        self.GenerateVariablesGridBranch(root, entries, GetVariablesTableColnames(self.PositionColumn))
        self.VariablesGrid.Expand(root)
        
    def GenerateVariablesGridBranch(self, root, entries, colnames, idx=0):
        item, root_cookie = self.VariablesGrid.GetFirstChild(root)
        
        no_more_items = not item.IsOk()
        for entry in entries:
            idx += 1
            if no_more_items:
                item = self.VariablesGrid.AppendItem(root, "")
            for col, colname in enumerate(colnames):
                if col == 0:
                    self.VariablesGrid.SetItemText(item, str(idx), 0)
                else:
                    value = entry.get(colname, "")
                    if colname == "Access":
                        value = GetAccessValue(value, entry.get("PDOMapping", ""))
                    self.VariablesGrid.SetItemText(item, value, col)
            if entry["PDOMapping"] == "":
                self.VariablesGrid.SetItemBackgroundColour(item, wx.LIGHT_GREY)
            else:
                self.VariablesGrid.SetItemBackgroundColour(item, wx.WHITE)
            self.VariablesGrid.SetItemPyData(item, entry)
            idx = self.GenerateVariablesGridBranch(item, entry["children"], colnames, idx)
            if not no_more_items:
                item, root_cookie = self.VariablesGrid.GetNextChild(root, root_cookie)
                no_more_items = not item.IsOk()
        
        if not no_more_items:
            to_delete = []
            while item.IsOk():
                to_delete.append(item)
                item, root_cookie = self.VariablesGrid.GetNextChild(root, root_cookie)
            for item in to_delete:
                self.VariablesGrid.Delete(item)
        
        return idx
    
    def OnVariablesFilterChanged(self, event):
        filter = self.VariablesFilter.GetSelection()
        if filter != -1:
            self.CurrentFilter = self.Filters[filter]
            self.RefreshView()
        else:
            try:
                value = self.VariablesFilter.GetValue()
                if value == "":
                    self.CurrentFilter = self.Filters[0]
                    self.VariablesFilter.SetSelection(0)
                else:
                    result = ETHERCAT_INDEX_MODEL.match(value)
                    if result is not None:
                        value = result.group(1)
                    index = int(value, 16)
                    self.CurrentFilter = (index, index)
                    self.VariablesFilter.SetValue(VARIABLE_INDEX_FILTER_FORMAT % index)
                self.RefreshView()
            except:
                if self.CurrentFilter in self.Filters:
                    self.VariablesFilter.SetSelection(self.Filters.index(self.CurrentFilter))
                else:
                    self.VariablesFilter.SetValue(VARIABLE_INDEX_FILTER_FORMAT % self.CurrentFilter[0])
        self.VariablesFilterFirstCharacter = True
        event.Skip()
    
    def OnVariablesFilterKeyDown(self, event):
        if self.VariablesFilterFirstCharacter:
            keycode = event.GetKeyCode()
            if keycode not in [wx.WXK_RETURN, 
                               wx.WXK_NUMPAD_ENTER]:
                self.VariablesFilterFirstCharacter = False
                if keycode not in NAVIGATION_KEYS:
                    self.VariablesFilter.SetValue("")
            if keycode not in [wx.WXK_DELETE, 
                               wx.WXK_NUMPAD_DELETE, 
                               wx.WXK_BACK]:
                event.Skip()
        else:
            event.Skip()
    
    def OnVariablesGridLeftClick(self, event):
        item, flags, col = self.VariablesGrid.HitTest(event.GetPosition())
        if item.IsOk():
            entry = self.VariablesGrid.GetItemPyData(item)
            data_type = entry.get("Type", "")
            data_size = self.Controler.GetSizeOfType(data_type)
            
            if col == -1 and data_size is not None:
                pdo_mapping = entry.get("PDOMapping", "")
                access = entry.get("Access", "")
                entry_index = self.Controler.ExtractHexDecValue(entry.get("Index", "0"))
                entry_subindex = self.Controler.ExtractHexDecValue(entry.get("SubIndex", "0"))
                location = self.Controler.GetCurrentLocation()
                if self.PositionColumn:
                    slave_pos = self.Controler.ExtractHexDecValue(entry.get("Position", "0"))
                    location += (slave_pos,)
                    node_name = self.Controler.GetSlaveName(slave_pos)
                else:
                    node_name = self.Controler.CTNName()
                
                if pdo_mapping != "":
                    var_name = "%s_%4.4x_%2.2x" % (node_name, entry_index, entry_subindex)
                    if pdo_mapping == "T":
                        dir = "%I"
                    else:
                        dir = "%Q"
                    location = "%s%s" % (dir, data_size) + \
                               ".".join(map(lambda x:str(x), location + (entry_index, entry_subindex)))
                    
                    data = wx.TextDataObject(str((location, "location", data_type, var_name, "", access)))
                    dragSource = wx.DropSource(self.VariablesGrid)
                    dragSource.SetData(data)
                    dragSource.DoDragDrop()
                    return
                
                elif self.PositionColumn:
                    location = self.Controler.GetCurrentLocation() +\
                               (slave_pos, entry_index, entry_subindex)
                    data = wx.TextDataObject(str((location, "variable", access)))
                    dragSource = wx.DropSource(self.VariablesGrid)
                    dragSource.SetData(data)
                    dragSource.DoDragDrop()
                    return
        
        event.Skip()

class NodeEditor(ConfTreeNodeEditor):
    
    CONFNODEEDITOR_TABS = [
        (_("Ethercat node"), "_create_EthercatNodeEditor"),
        # Add Notebook Tab for EtherCAT Management Treebook
        (_("EtherCAT Management"), "_create_EtherCATManagementEditor")
        ]
    
    def _create_EthercatNodeEditor(self, prnt):
        self.EthercatNodeEditor = wx.Panel(prnt, style=wx.TAB_TRAVERSAL)
        
        main_sizer = wx.FlexGridSizer(cols=1, hgap=0, rows=2, vgap=5)
        main_sizer.AddGrowableCol(0)
        main_sizer.AddGrowableRow(1)
        
        variables_label = wx.StaticText(self.EthercatNodeEditor,
              label=_('Variable entries:'))
        main_sizer.AddWindow(variables_label, border=10, flag=wx.TOP|wx.LEFT|wx.RIGHT)
        
        self.NodeVariables = NodeVariablesSizer(self.EthercatNodeEditor, self.Controler)
        main_sizer.AddSizer(self.NodeVariables, border=10, 
            flag=wx.GROW|wx.BOTTOM|wx.LEFT|wx.RIGHT)
                
        self.EthercatNodeEditor.SetSizer(main_sizer)

        return self.EthercatNodeEditor
    
    def __init__(self, parent, controler, window):
        ConfTreeNodeEditor.__init__(self, parent, controler, window)
        
        # add Contoler for use EthercatSlave.py Method
        self.Controler=controler
        
    def GetBufferState(self):
        return False, False
        
    def RefreshView(self):
        ConfTreeNodeEditor.RefreshView(self)
    
        self.NodeVariables.RefreshView()

    # -------------------For EtherCAT Management ----------------------------------------------    
    def _create_EtherCATManagementEditor(self, prnt):
        self.EtherCATManagementEditor = wx.ScrolledWindow(prnt,
            style=wx.TAB_TRAVERSAL|wx.HSCROLL|wx.VSCROLL)
        self.EtherCATManagementEditor.Bind(wx.EVT_SIZE, self.OnResize)

        self.EtherCATManagermentEditor_Main_Sizer = wx.FlexGridSizer(cols=1, hgap=0, rows=2, vgap=5)
        self.EtherCATManagermentEditor_Main_Sizer.AddGrowableCol(0)
        self.EtherCATManagermentEditor_Main_Sizer.AddGrowableRow(0)
        
        self.EtherCATManagementTreebook = EtherCATManagementTreebook(self.EtherCATManagementEditor, self.Controler, self)
          
        self.EtherCATManagermentEditor_Main_Sizer.AddSizer(self.EtherCATManagementTreebook, border=10, flag=wx.GROW)

        self.EtherCATManagementEditor.SetSizer(self.EtherCATManagermentEditor_Main_Sizer)
        return self.EtherCATManagementEditor
    
    def OnResize(self, event):
        self.EtherCATManagementEditor.GetBestSize()
        xstart, ystart = self.EtherCATManagementEditor.GetViewStart()
        window_size = self.EtherCATManagementEditor.GetClientSize()
        maxx, maxy = self.EtherCATManagementEditor.GetMinSize()
        posx = max(0, min(xstart, (maxx - window_size[0]) / SCROLLBAR_UNIT))
        posy = max(0, min(ystart, (maxy - window_size[1]) / SCROLLBAR_UNIT))
        self.EtherCATManagementEditor.Scroll(posx, posy)
        self.EtherCATManagementEditor.SetScrollbars(SCROLLBAR_UNIT, SCROLLBAR_UNIT, 
                maxx / SCROLLBAR_UNIT, maxy / SCROLLBAR_UNIT, posx, posy)
        event.Skip()

CIA402NodeEditor = NodeEditor

#--------------------------- For total Editor (Treebook) ---------------------------------------------
class EtherCATManagementTreebook(wx.Treebook):
    def __init__(self, parent, controler, node_editor):
        wx.Treebook.__init__(self, parent, -1, size=wx.DefaultSize, style=wx.BK_DEFAULT)
        self.parent = parent
        self.Controler = controler
        self.node_editor = node_editor
        
        self.row = 8
        self.col = 17 # Chaerin 130228
        
        self.SlaveStatePanel = SlaveStatePanelClass(self, self.Controler)
        self.SDOManagementPanel = SDOPanelClass(self, self.Controler)
        self.PDOMonitoringPanel = PDOPanelClass(self, self.Controler)
        self.ESCManagementPanel = EEPROMAccessPanel(self)
        self.SmartView = SlaveSiiSmartView(self, self.Controler)
        self.HexEditor = HexEditor(self, self.Controler, self.row, self.col)
        self.RegisterAccess = RegisterAccessPanel(self, self.Controler)
        
        self.AddPage(self.SlaveStatePanel, "Slave State")
        self.AddPage(self.SDOManagementPanel, "SDO Management")
        self.AddPage(self.PDOMonitoringPanel, "PDO Monitoring")
        self.AddPage(self.ESCManagementPanel, "ESC Management")
        self.AddSubPage(self.SmartView, "Smart View")
        self.AddSubPage(self.HexEditor, "Hex View") 
        self.AddPage(self.RegisterAccess, "Register Access")

        
        self.Bind(wx.EVT_TREEBOOK_PAGE_CHANGED, self.OnPageChanged)
        self.Bind(wx.EVT_TREEBOOK_PAGE_CHANGING, self.OnPageChanging)
        
    def OnPageChanged(self, event):
        old = event.GetOldSelection()
        new = event.GetSelection()
        sel = event.GetSelection()
        event.Skip()
        
    def OnPageChanging(self, event):
        old = event.GetOldSelection()
        new = event.GetSelection()
        sel = event.GetSelection()
        event.Skip()    
        
    def LoadData(self):
        error, returnVal = self.Controler.GetSlaveStateFromSlave()
        # if error != 0, Beremiz do not connect 
        if error != 0  :
            #run = False
            return None
            
        # if returnVal == "", Beremiz is connect but slave is not connect on master
        elif returnVal == "" :
            #run = False
            return None
            
        # returnVal is not None, Request of the state   
        elif returnVal is not None:
            # xml's Smart View Information Load
            rootClass = self.Controler.GetRootClass()
            self.SmartViewInfosFromXML = rootClass.GetSmartViewInfos()              
            
            # EEPROM's SII data Load
            returnVal = self.Controler.Sii_Read()
            self.binaryCode = returnVal
            self.Controler.SiiData = self.binaryCode # by Chaerin 130529

            # by Chaerin 130212
            # fill padding to binaryCode
            for index in range(self.SmartViewInfosFromXML["eeprom_size"] - len(self.binaryCode)):
                self.binaryCode = self.binaryCode +'ff'.decode('hex')
            
            self.HexRead(self.binaryCode)
              
            return self.binaryCode
            
        #return run
        return None
        
    def GetByteAddressData(self, offset, endBit, startBit, format):
        #get binary data from word address
        list = []
        binary = []
        data = ''
        
        for index in range(2):           
            list.append(self.binaryCode[offset*2 + index])
            
        list.reverse()
        data = list   #word address data
        
        binary.append(bin(ord(data[0]))[2:].zfill(8))
        binary.append(bin(ord(data[1]))[2:].zfill(8))
        
        binary = ''.join(binary)
        
        #bit 
        length = endBit - startBit
        if length < 0:
            return -1
        
        binaryList = []
        for index in range(length+1):
            binaryList.append(binary[15 - endBit + index])        
        binaryList = ''.join(binaryList)
        
        if format == 10:
            return int(binaryList,2)
        elif format == 16:
            return hex(int(binaryList,2))
        elif format == 2:
            return binaryList     
        
    def GetWordAddressData(self, dictTuple, format):
        offset = int(str(dictTuple[0]), 16) * 2
        length = int(str(dictTuple[1]), 16) * 2
        list = []
        data = ''
        for index in range(length):
            hexData = hex(ord(self.binaryCode[offset + index]))[2:]
            list.append(hexData.zfill(2))
            
        list.reverse()
        data = list[0:length]

        if format == 16:
            return '0x' + ''.join(data) 
        elif format == 10:
            return str(int(str(''.join(data)), 16))
        elif format == 2: 
            ''.join(data)           
        
    def HexRead(self, binary):
        rowCode = []
        rowText = ""
        row = 0
        self.hexCode = [] # by Chaerin 130121
        
        for index in range(0, len(binary)) :
            if len(binary[index]) != 1:
                break #goto continue statement below.
            else:
                digithexstr = hex(ord(binary[index])) #get one hex value in string format "0x%N", %N being the hex pair. Automatically goes to next byte after each cycle.

                tempvar2 = digithexstr[2:4]
                if len(tempvar2) == 1:        #if the display num consists of 1 digit
                    tempvar2 = "0" + tempvar2 #append a 0 to front if there is none.
                rowCode.append(tempvar2) 
                
                # convert from hex data to ASCII data
                if int(digithexstr, 16)>=32 and int(digithexstr, 16)<=126:
                    rowText = rowText + chr(int(digithexstr, 16))
                else:
                    rowText = rowText + "."
                
                if index != 0 : 
                    if len(rowCode) == (self.col - 1):
                        rowCode.append(rowText)
                        self.hexCode.append(rowCode)
                        rowText = ""
                        rowCode = []
                        row = row + 1                        
        self.row = row
        
        return self.hexCode # by Chaerin 130529


# --------------------------- For SlaveState Class --------------------------------------
class SlaveStatePanelClass(wx.Panel):
    def __init__(self, parent, controler):
        wx.Panel.__init__(self, parent, -1, (0, 0), size=wx.DefaultSize, style = wx.SUNKEN_BORDER)
        self.Controler = controler
        self.parent = parent
        
        self.SlaveState_main_sizer = wx.BoxSizer(wx.VERTICAL)
        self.SlaveState_inner_main_sizer = wx.FlexGridSizer(cols=1, hgap=50, rows=3, vgap=10)
        
        # --------------------------- for Slave Information -----------------------------------------------------
        self.SlaveInfosDetailsBox = wx.StaticBox(self, label=_('Slave Informations'))
        self.SlaveInfosDetailsBoxSizer = wx.StaticBoxSizer(self.SlaveInfosDetailsBox, wx.VERTICAL)
        self.SlaveInfosDetailsInnerSizer = wx.FlexGridSizer(cols=4, hgap=10, rows=2, vgap=10)
        
        self.VendorLabel = wx.StaticText(self, label=_('Vendor:'), size=wx.DefaultSize)
        self.Vendor = wx.TextCtrl(self, size=wx.Size(150, 24), style=wx.TE_READONLY)
        self.ProductcodeLabel = wx.StaticText(self, label=_('Product code:'), size=wx.DefaultSize)
        self.ProductCode = wx.TextCtrl(self, size=wx.Size(150, 24), style=wx.TE_READONLY)
        self.RevisionnumberLabel = wx.StaticText(self, label=_('Revision number:'), size=wx.DefaultSize)
        self.RevisionNumber = wx.TextCtrl(self, size=wx.Size(150, 24), style=wx.TE_READONLY)
        self.PhysicsLabel = wx.StaticText(self, label=_('Physics:'), size=wx.DefaultSize)
        self.Physics = wx.TextCtrl(self, size=wx.Size(150, 24), style=wx.TE_READONLY)
        
        self.SlaveInfosDetailsInnerSizer.AddMany([self.VendorLabel, self.Vendor, self.ProductcodeLabel, self.ProductCode,
                                       self.RevisionnumberLabel, self.RevisionNumber, self.PhysicsLabel, self.Physics])
        
        self.SlaveInfosDetailsBoxSizer.Add(self.SlaveInfosDetailsInnerSizer)
         
        #--------------------------- for Sync Manager --------------------------------------------------------    
        self.SyncManagerBox = wx.StaticBox(self, label=_('Sync Manager'))
        self.SyncManagerBoxSizer = wx.StaticBoxSizer(self.SyncManagerBox, wx.VERTICAL)
        self.SyncManagerInnerSizer = wx.FlexGridSizer(cols=1, hgap=5, rows=1, vgap=5)
               
        self.SyncManagersGrid = CustomGrid(self, size=wx.Size(605,155), style=wx.VSCROLL)      
               
        self.SyncManagerInnerSizer.Add(self.SyncManagersGrid)    
        self.SyncManagerBoxSizer.Add(self.SyncManagerInnerSizer)
               
        # --------------------------- for Slave State ----------------------------------------------------------
        self.SlaveStateBox = wx.StaticBox(self, label=_('Slave State Transition && Monitoring'))
        self.SlaveStateBoxBoxSizer = wx.StaticBoxSizer(self.SlaveStateBox, wx.VERTICAL)      
        self.SlaveState_sizer = wx.FlexGridSizer(cols=4, hgap=10, rows=4, vgap=10)
        
        self.InitButton = wx.Button(self, label=_('INIT'), size=wx.Size(130, 30), id=0)
        self.PreOPButton = wx.Button(self, label=_('PREOP'), size=wx.Size(130, 30), id=1)
        self.SafeOPButton = wx.Button(self, label=_('SAFEOP'), size=wx.Size(130, 30), id=2)
        self.OPButton = wx.Button(self, label=_('OP'), size=wx.Size(130, 30), id=3)
        self.StartTimerButton = wx.Button(self, label=_('Start State Monitoring'))
        self.StopTimerButton = wx.Button(self, label=_('Stop State Monitoring'))
        
        self.InitButton.Bind(wx.EVT_BUTTON, self.OnButtonClick)
        self.PreOPButton.Bind(wx.EVT_BUTTON, self.OnButtonClick)
        self.SafeOPButton.Bind(wx.EVT_BUTTON, self.OnButtonClick)
        self.OPButton.Bind(wx.EVT_BUTTON, self.OnButtonClick)
        self.StartTimerButton.Bind(wx.EVT_BUTTON, self.StartTimer)
        self.StopTimerButton.Bind(wx.EVT_BUTTON, self.CurrentStateThreadStop)
        
        self.TargetStateLabel = wx.StaticText(self, label=_('Target State:'))
        self.TargetState = wx.TextCtrl(self, style=wx.TE_READONLY)
        
        self.CurrentStateLabel = wx.StaticText(self, label=_('Current State:'))
        self.CurrentState = wx.TextCtrl(self, style=wx.TE_READONLY)        
        
        self.SlaveState_sizer.AddMany([self.InitButton, self.PreOPButton, self.TargetStateLabel, self.TargetState, 
                                       self.SafeOPButton, self.OPButton, self.CurrentStateLabel, self.CurrentState,
                                       self.StartTimerButton, self.StopTimerButton])
        
        self.SlaveStateBoxBoxSizer.Add(self.SlaveState_sizer)
         
        #---------------------------------- Add Sizer --------------------------------------------------------- 
        self.SlaveState_inner_main_sizer.AddSizer(self.SlaveInfosDetailsBoxSizer)
        self.SlaveState_inner_main_sizer.AddSizer(self.SyncManagerBoxSizer)
        self.SlaveState_inner_main_sizer.AddSizer(self.SlaveStateBoxBoxSizer)
        
        self.SlaveState_main_sizer.Add(self.SlaveState_inner_main_sizer)
        
        self.SetSizer(self.SlaveState_main_sizer)
        
        # by andrew for Timer ---------------------------
        self.Bind(wx.EVT_TIMER, self.GetCurrentState)
        self.t1 = wx.Timer(self)
        # timer period 1 second
        self.t1.Start(1000)
        self.Create_SyncManager_Table()
        
        self.Centre()
    
    def Create_SyncManager_Table(self):
        self.SyncManagersTable = SyncManagersTable(self, [], GetSyncManagersTableColnames())
        self.SyncManagersGrid.SetTable(self.SyncManagersTable)
        self.SyncManagersGridColAlignements = [wx.ALIGN_RIGHT, wx.ALIGN_LEFT, wx.ALIGN_RIGHT, 
                                               wx.ALIGN_RIGHT, wx.ALIGN_RIGHT, wx.ALIGN_RIGHT]
        self.SyncManagersGridColSizes = [40, 150, 100, 100, 100, 100]
        self.SyncManagersGrid.SetRowLabelSize(0)
        for col in range(self.SyncManagersTable.GetNumberCols()):
            attr = wx.grid.GridCellAttr()
            attr.SetAlignment(self.SyncManagersGridColAlignements[col], wx.ALIGN_CENTRE)
            self.SyncManagersGrid.SetColAttr(col, attr)
            self.SyncManagersGrid.SetColMinimalWidth(col, self.SyncManagersGridColSizes[col])
            self.SyncManagersGrid.AutoSizeColumn(col, False) 
        
        self.RefreshSlaveInfos()
        
    # ----------- called by EthercatSlave SetParamsAttribute Method ------------------
    def RefreshSlaveInfos(self):
        slave_infos = self.Controler.GetSlaveInfos()
        if slave_infos is not None:
            self.Vendor.SetValue(slave_infos["vendor"])
            self.ProductCode.SetValue(slave_infos["product_code"])
            self.RevisionNumber.SetValue(slave_infos["revision_number"])
            self.Physics.SetValue(slave_infos["physics"])
            self.SyncManagersTable.SetData(slave_infos["sync_managers"])
            self.SyncManagersTable.ResetView(self.SyncManagersGrid)
        else:
            self.Vendor.SetValue("")
            self.ProductCode.SetValue("")
            self.RevisionNumber.SetValue("")
            self.Physics.SetValue("")
            self.SyncManagersTable.SetData([])
            self.SyncManagersTable.ResetView(self.SyncManagersGrid)   
        
    # Event Mapping Slave State Button, Request Slave State for RemoteExec
    def OnButtonClick(self, event):
        error, returnVal = self.Controler.GetSlaveStateFromSlave()
        # if error != 0, Beremiz do not connect 
        if error != 0  : 
            self.TargetState.SetValue("")
            pass
        # if returnVal == "", Beremiz is connect but slave is not connect on master
        elif returnVal == "" :
            self.TargetState.SetValue("")
            pass
        # returnVal is not None, Request of the state   
        elif returnVal is not None:
            id = event.GetId()    
            if id == 0:
                self.Controler.RequestSlaveState("init")
                self.TargetState.SetValue("INIT")
            elif id == 1:
                self.Controler.RequestSlaveState("preop")
                self.TargetState.SetValue("PREOP")
            elif id == 2:
                self.Controler.RequestSlaveState("safeop")
                self.TargetState.SetValue("SAFEOP")
            elif id == 3:
                # User can transfer op state after PLC start
                status = self.Controler.GetCTRoot()._connector.GetPLCstatus()
                if status == "Started" :
                    self.Controler.RequestSlaveState("op")
                    self.TargetState.SetValue("OP")
                # if PLC is not started, can not transfer op state
                else :
                    pass
            else :
                pass

    # Start Current State Thread, Mapping Start State Monitoring button 
    def StartTimer(self, event):
        self.t1 = wx.Timer(self)
        # 1 sec period timer 
        self.t1.Start(1000)
        
    # Stop Current State Thread, Mapping Stop State Monitoring button 
    def CurrentStateThreadStop(self, event):
        self.t1.Stop()
        self.TargetState.SetValue(" ")     

    #Thread for slave state update         
    def GetCurrentState(self, event):
        # request to current slave state
        error, returnVal = self.Controler.GetSlaveStateFromSlave()
        
        # if error != 0, Beremiz do not connect 
        if error != 0  :
            #self.CurrentState.SetValue("")
            self.TargetState.SetValue("")
            pass
        # if returnVal == "", Beremiz is connect but slave is not connect on master
        elif returnVal == "":
            #self.CurrentState.SetValue("")
            self.TargetState.SetValue("")
            pass
        # returnVal is not None, Parsing of the return value
        elif returnVal is not None:
            line = returnVal.split("\n")
            try :
                self.SetCurrentState(line[self.Controler.GetSlavePos()])
            except :
                pass        
            
    # String Parsing result of "ethercat slaves"
    def SetCurrentState(self, line):
        try :
            token = line.split("  ")
            if token[2] == "INIT" :
                self.CurrentState.SetValue("INIT")
                self.Controler.SetSlaveState("INIT")
            elif token[2] == "PREOP" :
                self.CurrentState.SetValue("PREOP")
                self.Controler.SetSlaveState("PREOP")
            elif token[2] == "SAFEOP" :
                self.CurrentState.SetValue("SAFEOP")
                self.Controler.SetSlaveState("SAFEOP")    
            elif token[2] == "OP" :
                self.CurrentState.SetValue("OP")
                self.Controler.SetSlaveState("OP") 
            else :  
                self.CurrentState.SetValue(token[3])
        except :
            pass   

# -------------------------- For SDO class ------------------------------------------------
class SDOPanelClass(wx.Panel):
    def __init__(self, parent, controler):
        wx.Panel.__init__(self, parent, -1)
        self.Controler = controler
        
        self.SDOManagement_main_sizer = wx.BoxSizer(wx.VERTICAL)
        self.SDOManagement_inner_main_sizer = wx.FlexGridSizer(cols=1, hgap=10, rows=2, vgap=10)
             
        self.SDO_update = wx.Button(self, label=_('update'))          
        self.SDO_update.Bind(wx.EVT_BUTTON, self.SDOInfoUpdate)
        
        self.callSDONoteBook = SDONoteBook(self, controler=self.Controler)
        self.SDOManagement_inner_main_sizer.Add(self.SDO_update)
        self.SDOManagement_inner_main_sizer.Add(self.callSDONoteBook, wx.ALL | wx.EXPAND)           

        self.SDOManagement_main_sizer.Add(self.SDOManagement_inner_main_sizer)
        
        self.SetSizer(self.SDOManagement_main_sizer)
         
    def SDOInfoUpdate(self, evt):     
        self.sdo_title = []
        self.run = True
        self.SDOFlag = True
        
        # Divide save parsing data
        self.sdos_all = []
        self.sdos_0 = []
        self.sdos_1 = []
        self.sdos_2 = []
        self.sdos_6 = []
        self.sdos_a = []
                
        # GetSlaveXML Method is checking whether slave is connected to master
        # if return is error, Beremiz is not connected
        # if only 1 line return, Beremiz is connected but slave is not connected to master
        error, returnVal = self.Controler.GetSlaveXML()
        line = returnVal.split("\n")
        
        # if return is error, return error message and destroy SDO dialog
        # and run flag turn false
        if error != 0 :
            self.NotConnectedDialog()
            self.run = False
            pass
        
        # if slave is not connected, return error message and destroy SDO dialog
        # and run flag turn false
        elif len(line) == 1 : # if it's windows, it's not 1 but 2.
            self.NoSlaveDialog()
            self.run = False
            pass
        
        # if slave is connected, request to SlaveSDO data
        elif len(line) > 1 :            
            # User is firstly click to 'SlaveSDO' Button
            # Then, it is request to SlaveSDO data from slave and parsing SDO data 
            # Then, SDOLoadingFlag changes true
            # request new SlaveSDO data from slave
            self.SDOs = self.Controler.GetSlaveSDOFromSlave()
            # SDOFlag is check to cancel during SDO data loading
            # if False, press cancel button
            self.SDOFlag = self.SdoParser() 
            # save the result of parsing data
            self.Controler.SDOData_0 = self.sdos_0
            self.Controler.SDOData_1 = self.sdos_1
            self.Controler.SDOData_2 = self.sdos_2
            self.Controler.SDOData_6 = self.sdos_6
            self.Controler.SDOData_a = self.sdos_a
            self.Controler.SDOData_all = self.sdos_all
            self.Controler.Loading_SDO_Flag = True

            # fill the cell new parsing data
            self.callSDONoteBook.CreateNoteBook()      
            # UI refresh
            self.Refresh()
                            
    # parsing SlaveSDO data                         
    def SdoParser(self):     
        # for progress bar UI
        slaveSDO_progress = wx.ProgressDialog("Slave SDO Monitoring", "Now Uploading...",
                               maximum = len(self.SDOs.splitlines()), parent=self,
                               style = wx.PD_CAN_ABORT | wx.PD_APP_MODAL | wx.PD_ELAPSED_TIME | wx.PD_ESTIMATED_TIME | 
                                       wx.PD_REMAINING_TIME | wx.PD_AUTO_HIDE | wx.PD_SMOOTH)        
        
        # if KeepGoing Flag is false, loop is stop and this method return false
        keepGoing = True
        # for progress bar count
        count = 0
             
        # SlaveSDO data split line by line 
        for details_line in self.SDOs.splitlines():
            count += 1
                        
            # If start of line is "SDO", this line is not having value
            # Then, that line is not parsing         
            if details_line[:3] == "SDO":
                details_line = details_line.strip()
                token = details_line[11:]
                tmp = self.StringTest(token.strip())
                title_name = tmp[1:len(tmp)-1]            
                continue
            details_line = details_line.strip()

            # each token is separated by ','
            first_divide = details_line.split("\"")
            # SDO information tracking..disabled in.
#            fulIdx, access, type, size, name = details_line.split(",")
            if len(first_divide)>2:
                token1 = first_divide[0].split(",")
                fulIdx = token1[0]
                access = token1[1]
                type = token1[2]                 
                size = token1[3]
                
                name = first_divide[1]
                # this remove " and "  (first and last)
                # StringTest is Test that value 'name' is alphanumeric  
                name_after_check = self.StringTest(name)
                
                tail_token = first_divide[2].split(",")

                idx, subIdx = fulIdx.split(":")

                # error line handing
                if type == "octet_string":
                    hexVal = ' ---- '
                elif len(tail_token) == 1 :
                    #hexVal = "TT"
                    hexVal = self.Controler.GetSDOValue_Slow(idx, subIdx)
                else :
                    hexVal = tail_token[1]
                       
                # decVal is not used currently, but maintain data structure  
                if len(token) == 6 :
                    decVal = '0'
                elif len(token) == 7 :
                    decVal = tail_token[2]
            
                # result of parsing SlaveSDO data, datatype is dictionary
                self.data = {'idx':idx.strip(), 'subIdx':subIdx.strip(), 'access':access.strip(), 
                             'type':type.strip(), 'size':size.strip(),  'name':name_after_check.strip(), 
                             'value':hexVal.strip(), "category":title_name.strip()}
                
                # append self.sdos data structure
                if int(idx, 0) < 0x1000 :
                    self.sdos_0.append(self.data)
                elif int(idx, 0) < 0x2000 :
                    self.sdos_1.append(self.data)
                elif int(idx, 0) < 0x6000 :
                    self.sdos_2.append(self.data)
                elif int(idx, 0) < 0xa000 :
                    self.sdos_6.append(self.data)  
                else :
                    self.sdos_a.append(self.data)
                  
                self.sdos_all.append(self.data)
            
            # about Progress bar UI Message
            if count >= len(self.SDOs.splitlines()) / 2:
                (keepGoing, skip) = slaveSDO_progress.Update(count, "Please Waiting a moment!!")
            else:
                (keepGoing, skip) = slaveSDO_progress.Update(count)
                
            # if Cancle button was pressed, slaveSDO_progress.Update will 
            # will be return 
            # Fasle by andrew. 
            if (keepGoing == False):
                break
            
        slaveSDO_progress.Destroy()      
        return keepGoing 

    # StringTest is Test that value 'name' is alphanumeric  
    def StringTest(self, check_string):
        allow_range = string.printable
        result = check_string
        for i in range(0, len(check_string)):
            # string.isalnum() is check whether string is alphanumeric and is not
            if check_string[len(check_string)-1-i:len(check_string)-i] in allow_range :
                result = check_string[:len(check_string) - i]
                break
            else :
                pass   
        return result
    
    # ------------------------- For notify error state -----------------------
    def NotConnectedDialog (self):
        dlg = wx.MessageDialog (self, 'It is not connected!!',
                             ' Warning...', wx.OK | wx.ICON_INFORMATION)
        dlg.ShowModal()
        dlg.Destroy()
        
    def NoSlaveDialog (self):
        dlg = wx.MessageDialog (self, 'There is no slave!!',
                             ' Warning...', wx.OK | wx.ICON_INFORMATION)
        dlg.ShowModal()
        dlg.Destroy()
     
class SDONoteBook(wx.Notebook):
    def __init__(self, parent, controler):
        wx.Notebook.__init__(self, parent, id = -1, size=(1130,680))    
        self.Controler = controler
        self.CreateNoteBook()
        
        self.Bind(wx.EVT_CHOICEBOOK_PAGE_CHANGED, self.OnPageChanged)
        self.Bind(wx.EVT_CHOICEBOOK_PAGE_CHANGING, self.OnPageChanging)
        
    def CreateNoteBook(self):    
        self.data = []
        count = 1
        
        # accroding to EtherCAT Communication(03/2011), 158p
        if wx.Platform == '__WXMSW__':
            pageTexts = [ "All",
                         "0x0000 - 0x0fff : Data Type Description",
                         "0x1000 - 0x1fff : Communication object",
                         "0x2000 - 0x5fff : Manufacturer specific",
                         "0x6000 - 0x9fff : Profile specific",
                         "0xa000 - 0xffff : reserved"]
        else :
            pageTexts = [ "All",
                         "0x0000 - 0x0fff : \n Data Type Description",
                         "0x1000 - 0x1fff : \n Communication object",
                         "0x2000 - 0x5fff : \n Manufacturer specific",
                         "0x6000 - 0x9fff : \n Profile specific",
                         "0xa000 - 0xffff : \n reserved"]              
        
        # update_flag means user click update button
        # if not add DeleteAllpages, UI not update but repetition same category
        self.DeleteAllPages()
        
        # add data set according to pageText
        for txt in pageTexts:
            if count == 1:
                self.data = self.Controler.SDOData_all
            elif count == 2:
                self.data = self.Controler.SDOData_0 
            elif count == 3:
                self.data = self.Controler.SDOData_1
            elif count == 4:
                self.data = self.Controler.SDOData_2
            elif count == 5:
                self.data = self.Controler.SDOData_6
            else :
                self.data = self.Controler.SDOData_a
            
            self.win = SlaveSDOTable(self, self.data) 
            self.AddPage(self.win, txt)
            count += 1
        
    def OnPageChanged(self, event):
        old = event.GetOldSelection()
        new = event.GetSelection()
        sel = self.GetSelection()
        event.Skip()

    def OnPageChanging(self, event):
        old = event.GetOldSelection()
        new = event.GetSelection()
        sel = self.GetSelection()
        event.Skip()

# -------------------- Create Grid For SDO Management ---------------------------------------
class SlaveSDOTable(wx.grid.Grid):  
    def __init__(self, parent, data):
        wx.grid.Grid.__init__(self, parent, -1, size=(1130,665), 
                              style=wx.EXPAND|wx.ALIGN_CENTRE_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL)
        
        self.Controler = parent.Controler
        self.parent = parent
        self.run = True
        self.SDOFlag = True
        if data is None :
            self.sdos = []
        else :
            self.sdos = data
        
        self.CreateGrid(len(self.sdos), 8)
        self.SetColLabelSize(30)
        self.SetColSize(3, 100)
        self.SetColSize(5, 250)
        self.SetColSize(6, 300)
        self.SetColSize(7, 120)
        self.SetRowLabelSize(0)
        
        self.SetColLabelValue(0, "Index")
        self.SetColLabelValue(1, "Subindex")
        self.SetColLabelValue(2, "Access")
        self.SetColLabelValue(3, "Type")
        self.SetColLabelValue(4, "Size")
        self.SetColLabelValue(5, "Category")
        self.SetColLabelValue(6, "Name")
        self.SetColLabelValue(7, "Value")
                
        attr = wx.grid.GridCellAttr()

        # ------- for SDO download  -----------------        
        self.Bind(gridlib.EVT_GRID_CELL_LEFT_DCLICK, self.SDOModifyDialog)

        for i in range(7): 
            self.SetColAttr(i,attr)                   
            
        self.SetColLabelAlignment(wx.ALIGN_CENTER, wx.ALIGN_BOTTOM)
        # ------------------------------------------------------------
            
        # fill the cell new parsing data
        self.SetTableValue()  

    # fill the cell new parsing data              
    def SetTableValue(self):
        # sdoList is a basis of classification about dictionary, self.sdos
        sdoList = ['idx', 'subIdx', 'access', 'type', 'size', 'category', 'name', 'value']
        for rowIdx in range(len(self.sdos)):
            for colIdx in range(len(self.sdos[rowIdx])):          
                self.SetCellValue(rowIdx, colIdx, self.sdos[rowIdx][sdoList[colIdx]])
                self.SetReadOnly(rowIdx, colIdx, True)
    
    # ------------------------- For notify error state -----------------------
    def InputErrorDialog (self):
        dlg = wx.MessageDialog (self, 'You can input only hex, dec value',
                             ' Warning...', wx.OK | wx.ICON_INFORMATION)
        dlg.ShowModal()
        dlg.Destroy()           
        
    def StateErrorDialog (self):
        dlg = wx.MessageDialog (self, 'You cannot SDO download this state',
                             ' Warning...', wx.OK | wx.ICON_INFORMATION)
        dlg.ShowModal()
        dlg.Destroy()             
        
    # ------------------------ For SDO modify dialog ------------------------   
    # CheckSDODataAccess is checking that access data has "w" 
    def CheckSDODataAccess(self, row):
        Write_flag = False
        check = self.sdos[row]['access']
        if check[1:2] == 'w' :
            self.Controler.Check_PREOP = True
            Write_flag = True
        if check[3:4] == 'w' : 
            self.Controler.Check_SAFEOP = True
            Write_flag = True
        if check[5:] =='w' :
            self.Controler.Check_OP = True
            Write_flag = True
            
        return Write_flag
    
    # DecideSDODownload is check StateFlag and decide which data can write current slave state
    def DecideSDODownload(self, state):
        if state == "PREOP" and self.Controler.Check_PREOP == True :
            return True
        elif state == "SAFEOP" and self.Controler.Check_SAFEOP == True :
            return True
        elif state == "OP" and self.Controler.Check_OP == True :
            return True
        
        return False
    
    # ClearStateFlag is initialize StateFlag
    def ClearStateFlag(self):
        self.Controler.Check_PREOP = False
        self.Controler.Check_SAFEOP = False
        self.Controler.Check_OP = False
    
    def SDOModifyDialog (self, event):
        # StateFlag is notice SDOData access each slave state
        self.ClearStateFlag()
        # if this line 'access' data has 'w', this line value may write
        # access data has not 'w', can readonly
        # CheckSDODataAccess is checking that access data has "w" 
        if event.GetCol() == 7 and self.CheckSDODataAccess(event.GetRow()) == True: 
            # declare TextEntryDialog for Modify SDO download data        
            dlg = wx.TextEntryDialog (self, "Enter hex or dec value (if enter dec value, it automatically conversed hex value)",
                                      "SDOModifyDialog", style = wx.OK | wx.CANCEL)

            startValue = self.GetCellValue(event.GetRow(), event.GetCol()) 
            dlg.SetValue(startValue)
            
            if dlg.ShowModal() == wx.ID_OK:
                try :
                    # try int(variable) if success, user input dec or hex value
                    int(dlg.GetValue(), 0)
                                
                    # DecideSDODownload is check StateFlag and decide which data can write current slave state
                    if self.DecideSDODownload(self.Controler.GetSlaveState()) == True :
                        # finally, request SDDODownload have modify value
                        self.Controler.SdoDownload(self.sdos[event.GetRow()]['type'], self.sdos[event.GetRow()]['idx'], 
                                                   self.sdos[event.GetRow()]['subIdx'], dlg.GetValue())
                        # and read modify value and set cell modified value 
                        self.SetCellValue(event.GetRow(), event.GetCol(), dlg.GetValue())
                    else :
                        self.StateErrorDialog()                  
                # try int(variable) if occur error, user input deference value not dec or hex
                except ValueError:
                    # Then, notify error state
                    self.InputErrorDialog()    

# --------------------------------- For PDO Class ----------------------------------------------
# PDO Class UI  : Panel -> Choicebook (RxPDO, TxPDO) -> Notebook (PDO Index) -> Grid (PDO entry)
class PDOPanelClass(wx.Panel):
    def __init__(self, parent, controler):
        wx.Panel.__init__(self, parent, -1)
        self.Controler = controler

        self.PDOMonitoringEditor_main_sizer = wx.BoxSizer(wx.VERTICAL)
        self.PDOMonitoringEditor_inner_main_sizer = wx.FlexGridSizer(cols=1, hgap=10, rows=2, vgap=10)
        
        self.callPDOChoicebook = PDOChoicebook(self, controler=self.Controler)   
        self.PDOMonitoringEditor_inner_main_sizer.Add(self.callPDOChoicebook, wx.ALL) #| wx.EXPAND)    
        
        self.PDOMonitoringEditor_main_sizer.Add(self.PDOMonitoringEditor_inner_main_sizer)
        
        self.SetSizer(self.PDOMonitoringEditor_main_sizer)

    def PDOInfoUpdate(self):
        # SetAddxmlflag define EthercatSlave(EthercatCIA402Slave).py
        # this method change Addxmlflag true
        # if Addxmlflag is true, PDOChoiceBook request PDO information
        self.Controler.SetAddxmlflag()
        # RequestPDOInfo get PDO information from import xml data 
        self.Controler.RequestPDOInfo()
        self.callPDOChoicebook.Destroy()
        self.callPDOChoicebook = PDOChoicebook(self, controler=self.Controler)
        # Recreate choicebook has update PDO information
        self.Refresh()
            
class PDOChoicebook(wx.Choicebook):
    def __init__(self, parent, controler):
        wx.Choicebook.__init__(self, parent, id=-1, size=(640, 500), style=wx.CHB_DEFAULT)
        self.Controler = controler
        
        RxWin = PDONoteBook(self, id=-1, controler=self.Controler, name="Rx")
        TxWin = PDONoteBook(self, id=-1, controler=self.Controler, name="Tx")
        self.AddPage(RxWin, "RxPDO")
        self.AddPage(TxWin, "TxPDO")
        
        # bind event for page change   
        self.Bind(wx.EVT_CHOICEBOOK_PAGE_CHANGED, self.OnPageChanged)
        self.Bind(wx.EVT_CHOICEBOOK_PAGE_CHANGING, self.OnPageChanging)
        
    def OnPageChanged(self, event):
        old = event.GetOldSelection()
        new = event.GetSelection()
        sel = self.GetSelection()
        event.Skip()

    def OnPageChanging(self, event):
        old = event.GetOldSelection()
        new = event.GetSelection()
        sel = self.GetSelection()
        event.Skip()     
        
class PDONoteBook(wx.Notebook):
    def __init__(self, parent, id, name, controler):
        wx.Notebook.__init__(self, parent, id=-1, size=(640, 400))
        self.Controler = controler
        
        count = 0
        pageTexts = []
        
        self.Controler.RequestPDOInfo()
        
        # PDOChoiceBook is devided by name field ('Tx' or 'Rx') and check Addxmlflag
        if name == "Tx" and self.Controler.Addxmlflag == True :
            # get pdo_info and pdo_entry
            # pdo_info has PDO index, name, number of entry at slave that is placed in combobox
            # (upper grid, device pdo category)
            pdo_info =  self.Controler.GetTxPDOCategory()
            pdo_entry = self.Controler.GetTxPDOInfo()
            for tmp in pdo_info :
                title = str(hex(tmp['pdo_index']))
                pageTexts.append(title)
        elif name == "Rx" and self.Controler.Addxmlflag == True :
            # Same process of Tx
            pdo_info =  self.Controler.GetRxPDOCategory()
            pdo_entry = self.Controler.GetRxPDOInfo()
            for tmp in pdo_info :
                title = str(hex(tmp['pdo_index']))
                pageTexts.append(title)
        
        # add page according to the number of pdo_info
        for txt in pageTexts:
            win = PDOEntryTable(self, pdo_info, pdo_entry, count)
            self.AddPage(win, txt)
            count += 1  

        self.Bind(wx.EVT_CHOICEBOOK_PAGE_CHANGED, self.OnPageChanged)
        self.Bind(wx.EVT_CHOICEBOOK_PAGE_CHANGING, self.OnPageChanging)
        
    def OnPageChanged(self, event):
        old = event.GetOldSelection()
        new = event.GetSelection()
        sel = self.GetSelection()
        event.Skip()

    def OnPageChanging(self, event):
        old = event.GetOldSelection()
        new = event.GetSelection()
        sel = self.GetSelection()
        event.Skip()     

# for grid        
class PDOEntryTable(wx.grid.Grid):
    def __init__(self, parent, info, entry, count):
        wx.grid.Grid.__init__(self, parent, -1, size=(700, 400), pos=wx.Point(0,0), style=wx.EXPAND|wx.ALIGN_CENTRE_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL)
        self.Controler = parent.Controler
        
        self.pdo_info = info
        self.pdo_entry = entry
        self.count = count
        
        # ------------------- for UI(number, position, size, etc) -------------------------------
        self.CreateGrid(self.pdo_info[self.count]['number_of_entry'], 5)
        self.SetColLabelSize(25)
        
        self.SetColLabelValue(0, "Index")
        self.SetColLabelValue(1, "Subindex")
        self.SetColLabelValue(2, "Length")     
        self.SetColLabelValue(3, "Type")
        self.SetColLabelValue(4, "Name")
        self.SetRowLabelSize(0)
        self.SetColSize(3, 50)
        self.SetColSize(4, 300)
        
        attr = wx.grid.GridCellAttr()
        
        for i in range(5):
            self.SetColAttr(i, attr)
         
        # fill PDO information before parsing etherlab.py   
        self.SetTableValue()   
            
    def SetTableValue(self):
        list_index = 0
        # decision loop range (for the same number_of_entry)
        for i in range(self.count + 1) :
            list_index += self.pdo_info[i]['number_of_entry']

        start_value = list_index - self.pdo_info[self.count]['number_of_entry']
        
        pdoList = ['entry_index', 'subindex', 'bitlen', 'type', 'name']
        for rowIdx in range(self.pdo_info[self.count]['number_of_entry']):
            for colIdx in range(len(self.pdo_entry[rowIdx])):
                # (colIdx == 0) means that data is index, it change hex -> str before fill the cell
                if colIdx == 0 :
                    self.SetCellValue(rowIdx, colIdx, str(hex(self.pdo_entry[start_value][pdoList[colIdx]])))
                else :
                    self.SetCellValue(rowIdx, colIdx, str(self.pdo_entry[start_value][pdoList[colIdx]]))
                self.SetReadOnly(rowIdx, colIdx, True)
                #self.SetCellAlignment(rowIdx, colIdx, wx.ALIGN_CENTRE, wx.ALIGN_CENTRE)
                self.SetRowSize(rowIdx, 25)
            start_value += 1

# ----------------------------- For EEPROM Class ----------------------------------------------------
# by Chaerin 130227
# This class explain EEPROM Access.

[ID_SMARTVIEWSTATICBOX] = [wx.NewId() for _init_ctrls in range(1)]
[ID_EEPROMSIZE, ID_PDITYPE, ID_COMBOX_DEVICEEMULATION] = [wx.NewId() for _init_config_data in range(3)]
[ID_COMBOX_COE, ID_COMBOX_SOE, ID_COMBOX_EOE, ID_COMBOX_FOE, ID_COMBOX_AOE] = [wx.NewId() for _init_mailbox_protocol in range(5)]

class EEPROMAccessPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, -1)
        sizer = wx.FlexGridSizer(cols=1, hgap=20,rows=3, vgap=5)
        
        line1 = wx.StaticText(self, -1, "  EEPROM Access is composed to SmartView and HexView.")
        line2 = wx.StaticText(self, -1, "    - SmartView shows Config Data, Device Identity, Mailbox settings, etc.")
        line3 = wx.StaticText(self, -1, "    - HexView shows EEPROM's contents.")
        
        
        sizer.Add(line1, 0, wx.TOP, 15)
        sizer.Add(line2, 0, wx.TOP, 10)
        sizer.Add(line3, 0, wx.TOP, 0)
        
        self.SetSizer(sizer)

class SlaveSiiSmartView(wx.Panel):
        
    def __init__(self, parent, controler):
        self.panel = wx.Panel.__init__(self, parent, -1)
        self.prnt = parent
        self.Controler = controler

        Sizer = wx.FlexGridSizer(cols=2, hgap=9, rows=1, vgap=9)
        LeftSizer = wx.FlexGridSizer(cols=1, hgap=9, rows=2, vgap=9)
        RightSizer = wx.FlexGridSizer(cols=1, hgap=9, rows=2, vgap=9)
        self.otherPdiType = 0  # by Chaerin 130121

        eepromSize = []
        self.pdiType = {0  :['none', '00000000'], 
                   4  :['Digital I/O', '00000100'],
                   5  :['SPI Slave', '00000101'],
                   7  :['EtherCAT Bridge (port3)', '00000111'],
                   8  :['uC async. 16bit', '00001000'],
                   9  :['uC async. 8bit', '00001001'],
                   10 :['uC sync. 16bit', '00001010'],
                   11 :['uC sync. 8bit', '00001011'],
                   16 :['32 Digtal Input and 0 Digital Output', '00010000'],
                   17 :['24 Digtal Input and 8 Digital Output', '00010001'],
                   18 :['16 Digtal Input and 16 Digital Output','00010010'],
                   19 :['8 Digtal Input and 24 Digital Output', '00010011'],
                   20 :['0 Digtal Input and 32 Digital Output', '00010100'],
                   128:['On-chip bus', '11111111']
        }

        pdiComboValue = []
        for i in sorted(self.pdiType.keys()):
            pdiComboValue.append(self.pdiType[i][0])

        # config data ----------------------------------------------------------------------------
        self.confSizer = self.MakeStaticBoxSizer("Config Data (evaluated from ESC)")       
        
        # for ComboBox
        self.confFlxSizer = wx.FlexGridSizer(cols=1, hgap=9, rows=4, vgap=6) 
        
        self.txt_eepromsize = wx.StaticText(self,-1,"EEPROM Size (Byte)", size = (160, 20))
        self.ctl_combobox_confEEPRomSize = wx.ComboBox(self, ID_EEPROMSIZE, choices=eepromSize, size=(360, -1), style=wx.CB_READONLY | wx.CB_SIMPLE) # size=(240, -1) -> size=(320, -1)
        
        self.txt_pditype = wx.StaticText(self,-1,"PDI Type:", size = (160, 20))
        self.ctl_combobox_confPDIType = wx.ComboBox(self, ID_PDITYPE, choices=pdiComboValue, size=(360, -1), style=wx.CB_READONLY | wx.CB_SIMPLE) # size=(240, -1) -> size=(320, -1) 

        self.ctl_checkbox_deviceEmulation = wx.CheckBox(self, ID_COMBOX_DEVICEEMULATION, """Device Emulation (state machine emulation)""") # add readonly Chaerin 130117
        
        # add UI
        self.confFlxSizer.Add(self.txt_eepromsize, border=2, flag=wx.ALL)
        self.confFlxSizer.Add(self.ctl_combobox_confEEPRomSize, border=2, flag=wx.ALL)
        self.confFlxSizer.Add(self.txt_pditype, border=2, flag=wx.ALL)
        self.confFlxSizer.Add(self.ctl_combobox_confPDIType, border=2, flag=wx.ALL)
        self.confSizer.Add(self.confFlxSizer, border=2, flag=wx.ALL)
        self.confSizer.Add(self.ctl_checkbox_deviceEmulation, border=6, flag=wx.TOP|wx.BOTTOM) 
         
        # device identity -----------------------------------------------------------------------
        self.deviceIdSizer = self.MakeStaticBoxSizer("Device Identity")
        
        self.deviceFlxSizer = wx.FlexGridSizer(cols=2, hgap=9, rows=4, vgap=5) # rows=5 -> rows=4  by Chaerin 130214
        
        self.txt_vendorId = wx.StaticText(self,-1,"Vendor Id:")
        self.txtctrl_vendorId = wx.TextCtrl(self, -1,"", size=(180, 28), style=wx.TE_READONLY) # size=(90, 28) -> size=(155, 28)
        
        self.txt_productCode = wx.StaticText(self,-1,"Product Code:")
        self.txtctrl_productCode = wx.TextCtrl(self, -1,"", size=(180, 28), style=wx.TE_READONLY)
        
        self.txt_revNo = wx.StaticText(self,-1,"Reversion No")
        self.txtctrl_revNo = wx.TextCtrl(self, -1,"", size=(180, 28), style=wx.TE_READONLY)        
        
        self.txt_serialNo = wx.StaticText(self,-1,"Serial No:")
        self.txtctrl_serialNo= wx.TextCtrl(self, -1,"", size=(180, 28), style=wx.TE_READONLY)       
        
        # add UI       
        self.deviceFlxSizer.Add(self.txt_vendorId, border=75, flag=wx.RIGHT)
        self.deviceFlxSizer.Add(self.txtctrl_vendorId, border=5, flag=wx.TOP|wx.BOTTOM)
        self.deviceFlxSizer.Add(self.txt_productCode, border=75, flag=wx.RIGHT)
        self.deviceFlxSizer.Add(self.txtctrl_productCode, border=5, flag=wx.TOP|wx.BOTTOM)
        self.deviceFlxSizer.Add(self.txt_revNo, border=75, flag=wx.RIGHT)
        self.deviceFlxSizer.Add(self.txtctrl_revNo, border=5, flag=wx.TOP|wx.BOTTOM)
        self.deviceFlxSizer.Add(self.txt_serialNo, border=75, flag=wx.RIGHT)
        self.deviceFlxSizer.Add(self.txtctrl_serialNo, border=5, flag=wx.TOP|wx.BOTTOM)
        
        self.deviceIdSizer.Add(self.deviceFlxSizer, border=2, flag=wx.ALL)
        
        #mailbox -----------------------------------------------------------------------------
        self.mailboxSizer = self.MakeStaticBoxSizer("Mailbox")
        
        #protocol
        self.mailboxProtocolSizer = wx.FlexGridSizer(cols=5, hgap=9, rows=1, vgap=9)
        self.checkbox_coe = wx.CheckBox(self, -1, "CoE")
        self.checkbox_soe = wx.CheckBox(self, -1, "SoE")
        self.checkbox_eoe = wx.CheckBox(self, -1, "EoE")
        self.checkbox_foe = wx.CheckBox(self, -1, "FoE")
        self.checkbox_aoe = wx.CheckBox(self, -1, "AoE")
        
        self.mailboxProtocolSizer.Add(self.checkbox_coe, border=3, flag=wx.TOP|wx.BOTTOM)
        self.mailboxProtocolSizer.Add(self.checkbox_soe, border=3, flag=wx.TOP|wx.BOTTOM)
        self.mailboxProtocolSizer.Add(self.checkbox_eoe, border=3, flag=wx.TOP|wx.BOTTOM)
        self.mailboxProtocolSizer.Add(self.checkbox_foe, border=3, flag=wx.TOP|wx.BOTTOM)
        self.mailboxProtocolSizer.Add(self.checkbox_aoe, border=3, flag=wx.TOP|wx.BOTTOM)
        
        #bootstrap
        self.bootstarpSizer = self.MakeStaticBoxSizer("Bootstrap Configuration")
        self.bootFlexSizer = wx.FlexGridSizer(cols=3, hgap=9, rows=2, vgap=9)
        
        self.txt_bootRcvOffset = wx.StaticText(self,-1,"Receive Offset/Size:")
        self.txt_bootSendOffset = wx.StaticText(self,-1,"Send Offset/Size:")
        
        self.txtctrl_bootRcvOffset = wx.TextCtrl(self, -1,"", style=wx.TE_READONLY, size=(100, 30))
        self.txtctrl_bootRcvSize = wx.TextCtrl(self, -1,"", style=wx.TE_READONLY, size=(100, 30))
        self.txtctrl_bootSendOffset = wx.TextCtrl(self, -1,"", style=wx.TE_READONLY, size=(100, 30))
        self.txtctrl_bootSendSize = wx.TextCtrl(self, -1,"", style=wx.TE_READONLY, size=(100, 30))
        
        self.bootFlexSizer.Add(self.txt_bootRcvOffset, border=20, flag=wx.RIGHT)
        self.bootFlexSizer.Add(self.txtctrl_bootRcvOffset, border=5, flag=wx.TOP|wx.BOTTOM)
        self.bootFlexSizer.Add(self.txtctrl_bootRcvSize, border=5, flag=wx.TOP|wx.BOTTOM)
        self.bootFlexSizer.Add(self.txt_bootSendOffset, border=20, flag=wx.RIGHT)
        self.bootFlexSizer.Add(self.txtctrl_bootSendOffset, border=5, flag=wx.TOP|wx.BOTTOM)
        self.bootFlexSizer.Add(self.txtctrl_bootSendSize, border=5, flag=wx.TOP|wx.BOTTOM)
        
        self.bootstarpSizer.Add(self.bootFlexSizer, border=2, flag=wx.ALL)
        
        #standard
        self.stdConfSizer = self.MakeStaticBoxSizer("Standard Configuration")
        self.stdConfFlexSizer = wx.FlexGridSizer(cols=3, hgap=9, rows=2, vgap=9)
        
        self.txt_stdRcvOffset = wx.StaticText(self,-1,"Receive Offset/Size:")
        self.txt_stdSendOffsets = wx.StaticText(self,-1,"Send Offset/Size:")
        
        self.txtctrl_stdRcvOffset = wx.TextCtrl(self, -1,"", style=wx.TE_READONLY, size=(100, 30))
        self.txtctrl_stdRcvSize = wx.TextCtrl(self, -1,"", style=wx.TE_READONLY, size=(100, 30))
        self.txtctrl_stdSendOffset = wx.TextCtrl(self, -1,"", style=wx.TE_READONLY, size=(100, 30))
        self.txtctrl_stdSendSize = wx.TextCtrl(self, -1,"", style=wx.TE_READONLY, size=(100, 30))
        
        self.stdConfFlexSizer.Add(self.txt_stdRcvOffset, border=20, flag=wx.RIGHT)
        self.stdConfFlexSizer.Add(self.txtctrl_stdRcvOffset, border=5, flag=wx.TOP|wx.BOTTOM)
        self.stdConfFlexSizer.Add(self.txtctrl_stdRcvSize, border=5, flag=wx.TOP|wx.BOTTOM)
        self.stdConfFlexSizer.Add(self.txt_stdSendOffsets, border=20, flag=wx.RIGHT)
        self.stdConfFlexSizer.Add(self.txtctrl_stdSendOffset, border=5, flag=wx.TOP|wx.BOTTOM)
        self.stdConfFlexSizer.Add(self.txtctrl_stdSendSize, border=5, flag=wx.TOP|wx.BOTTOM)        
        
        self.stdConfSizer.Add(self.stdConfFlexSizer, border=2, flag=wx.ALL)
        
        self.mailboxSizer.Add(self.mailboxProtocolSizer, border=10, flag=wx.TOP|wx.BOTTOM)
        self.mailboxSizer.Add(self.bootstarpSizer, border=7, flag=wx.TOP|wx.BOTTOM)
        self.mailboxSizer.Add(self.stdConfSizer, border=7, flag=wx.TOP|wx.BOTTOM)

        #button   by Chaerin 130214
        self.buttonSizer = wx.FlexGridSizer(cols=2, hgap=9, rows=1, vgap=6) 
        self.button_writeEeprom = wx.Button(self, -1, "Write EEPROM", size=(150, 40))
        self.button_readEeprom = wx.Button(self, -1, "Read EEPROM", size=(150, 40))
        
        self.buttonSizer.Add(self.button_writeEeprom, border=10, flag=wx.ALL)
        self.buttonSizer.Add(self.button_readEeprom, border=10, flag=wx.ALL)

        # mod by Chaerin 130214
        LeftSizer.Add(self.confSizer, border=15, flag=wx.EXPAND|wx.ALIGN_CENTER|wx.LEFT|wx.TOP)
        LeftSizer.Add(self.deviceIdSizer, border=15, flag=wx.EXPAND|wx.ALIGN_CENTER|wx.LEFT|wx.TOP)
        RightSizer.Add(self.buttonSizer)
        RightSizer.Add(self.mailboxSizer, border=15, flag=wx.EXPAND|wx.ALIGN_CENTER|wx.LEFT|wx.TOP)
        Sizer.Add(LeftSizer)
        Sizer.Add(RightSizer)
        
        self.SetSizer(Sizer)
        
        #event mapping ----------------------------------------------------------
        self.ctl_combobox_confEEPRomSize.Bind(wx.EVT_COMBOBOX, self.ChangeData)
        self.ctl_combobox_confPDIType.Bind(wx.EVT_COMBOBOX, self.ChangeData)
        self.ctl_checkbox_deviceEmulation.Bind(wx.EVT_CHECKBOX, self.ChangeData)

        self.txtctrl_vendorId.Bind(wx.EVT_TEXT, self.ChangeData)
        self.txtctrl_revNo.Bind(wx.EVT_TEXT, self.ChangeData)
        self.txtctrl_serialNo.Bind(wx.EVT_TEXT, self.ChangeData)
        self.txtctrl_productCode.Bind(wx.EVT_TEXT, self.ChangeData)
        
        self.checkbox_coe.Bind(wx.EVT_CHECKBOX, self.ChangeData) # by Chaerin 130212
        self.checkbox_soe.Bind(wx.EVT_CHECKBOX, self.ChangeData) # by Chaerin 130212
        self.checkbox_eoe.Bind(wx.EVT_CHECKBOX, self.ChangeData) # by Chaerin 130212
        self.checkbox_foe.Bind(wx.EVT_CHECKBOX, self.ChangeData) # by Chaerin 130212
        self.checkbox_aoe.Bind(wx.EVT_CHECKBOX, self.ChangeData) # by Chaerin 130212
        
        self.txtctrl_bootRcvOffset.Bind(wx.EVT_TEXT, self.ChangeData)
        self.txtctrl_bootRcvSize.Bind(wx.EVT_TEXT, self.ChangeData)
        self.txtctrl_bootSendOffset.Bind(wx.EVT_TEXT, self.ChangeData)
        self.txtctrl_bootSendSize.Bind(wx.EVT_TEXT, self.ChangeData)

        self.txtctrl_stdRcvOffset.Bind(wx.EVT_TEXT, self.ChangeData)
        self.txtctrl_stdRcvSize.Bind(wx.EVT_TEXT, self.ChangeData)
        self.txtctrl_stdSendOffset.Bind(wx.EVT_TEXT, self.ChangeData)
        self.txtctrl_stdSendSize.Bind(wx.EVT_TEXT, self.ChangeData)
        
        self.button_writeEeprom.Bind(wx.EVT_BUTTON, self.WriteToEEPROM)
        self.button_readEeprom.Bind(wx.EVT_BUTTON, self.ReadFromEEPROM)
        
        self.Create_SmartView()
        
    def Create_SmartView(self):  
        self.SmartViewInfosFromXML = self.Controler.GetRootClass().GetSmartViewInfos()
        self.SetXMLData()
        
    def ChangeData(self, evt):
        if self.ctl_combobox_confEEPRomSize.GetId() == evt.GetId():
            self.ctl_combobox_confEEPRomSize.Select(self.EEPROMSizeSelected)
            
        elif self.ctl_combobox_confPDIType.GetId() == evt.GetId():           
            self.ctl_combobox_confPDIType.Select(self.pdiTypeSelected)

        elif self.ctl_checkbox_deviceEmulation.GetId() == evt.GetId():
            deviceEmulation_chk = evt.GetEventObject() # by Chaerin 130119
            deviceEmulation_chk.SetValue(not deviceEmulation_chk.GetValue()) # by Chaerin 130119 
        
        elif self.txtctrl_vendorId.GetId() == evt.GetId():
            pass
        
        elif self.txtctrl_revNo.GetId() == evt.GetId():            
            pass
        
        elif self.txtctrl_serialNo.GetId() == evt.GetId():            
            pass
        
        elif self.txtctrl_productCode.GetId() == evt.GetId():            
            pass
        
        elif self.checkbox_coe.GetId() == evt.GetId():
            coe_chk = evt.GetEventObject() 
            coe_chk.SetValue(not coe_chk.GetValue())

        elif self.checkbox_soe.GetId() == evt.GetId():
            soe_chk = evt.GetEventObject()
            soe_chk.SetValue(not soe_chk.GetValue())

        elif self.checkbox_eoe.GetId() == evt.GetId():
            eoe_chk = evt.GetEventObject()
            eoe_chk.SetValue(not eoe_chk.GetValue())

        elif self.checkbox_foe.GetId() == evt.GetId():
            foe_chk = evt.GetEventObject()
            foe_chk.SetValue(not foe_chk.GetValue())

        elif self.checkbox_aoe.GetId() == evt.GetId():
            aoe_chk = evt.GetEventObject()
            aoe_chk.SetValue(not aoe_chk.GetValue())

        elif self.txtctrl_bootRcvOffset.GetId() == evt.GetId():            
            pass
        
        elif self.txtctrl_bootRcvSize.GetId() == evt.GetId():            
            pass
        
        elif self.txtctrl_bootSendOffset.GetId() == evt.GetId():            
            pass
        
        elif self.txtctrl_bootSendSize.GetId() == evt.GetId():            
            pass
                
        elif self.txtctrl_stdRcvOffset.GetId() == evt.GetId():            
            pass
        
        elif self.txtctrl_stdRcvSize.GetId() == evt.GetId():            
            pass
        
        elif self.txtctrl_stdSendOffset.GetId() == evt.GetId():            
            pass
        
        elif self.txtctrl_stdSendSize.GetId() == evt.GetId():            
            pass
        
    def WriteToEEPROM(self, event):
        
        error, returnVal = self.Controler.GetSlaveXML()
        line = returnVal.split("\n")
        # if error != 0, Beremiz do not connect 
        if error != 0  : 
            self.NotConnectedDialog()
        # if len(line) == 1, Beremiz is connect but slave is not connect on master
        elif len(line) == 1 : # if it's windows, it's not 1 but 2.
            self.NoSlaveDialog()
        # returnVal is not None, Request of the state   
        elif len(line) > 1 :
        
            dialog = wx.FileDialog(self, _("Choose a binary file"), os.getcwd(), "",  _("bin files (*.bin)|*.bin"), wx.OPEN)
            tmpflag = 0
            
            if dialog.ShowModal() == wx.ID_OK:
                filepath = dialog.GetPath()
                try:
                    binfile = open(filepath,"rb")
                    self.siiBinary = binfile.read()
                    tmpflag = 1
                except:
                    self.InvalidFileDialog()
                    pass

            dialog.Destroy()
            
            # sii_write
            if tmpflag == 1:
                error, returnVal = self.Controler.Sii_Write(self.siiBinary)
                self.Controler.Rescan()
                #self.prnt.binaryCode = self.siiBinary
                self.Controler.SiiData = self.siiBinary
                self.SetEEPROMData()
                tmpflag = 0
    
    def ReadFromEEPROM(self, event):
        error, returnVal = self.Controler.GetSlaveXML()
        line = returnVal.split("\n")
        # if error != 0, Beremiz do not connect 
        if error != 0  : 
            self.NotConnectedDialog()
        # if len(line) == 1, Beremiz is connect but slave is not connect on master
        elif len(line) == 1 : # if it's windows, it's not 1 but 2.
            self.NoSlaveDialog()
        # returnVal is not None, Request of the state   
        elif len(line) > 1 :
            self.siiBinary = self.prnt.LoadData()
            self.SetEEPROMData()
            dialog = wx.FileDialog(self, _("Save as..."), os.getcwd(), "slave0.bin",  _("bin files (*.bin)|*.bin|All files|*.*"), wx.SAVE|wx.OVERWRITE_PROMPT)
        
            if dialog.ShowModal() == wx.ID_OK:
                filepath = dialog.GetPath()
                binfile = open(filepath,"wb")
                binfile.write(self.siiBinary)
                binfile.close()
    
            dialog.Destroy()
    
    def SetXMLData(self): #by Chaerin 130212
        
        #Config Data : EEPROM size
        self.ctl_combobox_confEEPRomSize.Clear()
        self.ctl_combobox_confEEPRomSize.Append(str(self.SmartViewInfosFromXML["eeprom_size"]))
        self.ctl_combobox_confEEPRomSize.Select(0)
        self.EEPROMSizeSelected = 0
        
        #Config Data : PDI Type
        cntPdiType = self.SmartViewInfosFromXML["pdi_type"]
        self.ctl_combobox_confPDIType.Clear()
        
        self.pdiTypeSelected = -1
        ##The case that PDI Type is defined in EtherCAT Slave Controller Register Description
        for i in self.pdiType.keys():
            if cntPdiType == i:
                self.ctl_combobox_confPDIType.Append(self.pdiType[i][0])
                self.ctl_combobox_confPDIType.Select(0)
                self.pdiTypeSelected = 0
        ##Other case of PDI Types
        if self.pdiTypeSelected != 0:
            self.ctl_combobox_confPDIType.Append(str(cntPdiType))
            self.ctl_combobox_confPDIType.Select(0)
            self.pdiTypeSelected = 0
        
        #Config Data : Device Emulation
        self.ctl_checkbox_deviceEmulation.SetValue(self.SmartViewInfosFromXML["device_emulation"])
        
        #Device Identity : Vendor ID
        self.txtctrl_vendorId.SetValue(self.SmartViewInfosFromXML["vendor_id"])
        
        #Device Identity : Product Code
        self.txtctrl_productCode.SetValue(self.SmartViewInfosFromXML["product_code"])

        #Device Identity : Revision No.
        self.txtctrl_revNo.SetValue(self.SmartViewInfosFromXML["revision_no"])
     
        #Device Identity : Serial No.
        self.txtctrl_serialNo.SetValue(self.SmartViewInfosFromXML["serial_no"])           
        
        #Mailbox : checkbox
        self.checkbox_coe.SetValue(self.SmartViewInfosFromXML["mailbox_coe"])
        self.checkbox_soe.SetValue(self.SmartViewInfosFromXML["mailbox_soe"])
        self.checkbox_eoe.SetValue(self.SmartViewInfosFromXML["mailbox_eoe"])
        self.checkbox_foe.SetValue(self.SmartViewInfosFromXML["mailbox_foe"])
        self.checkbox_aoe.SetValue(self.SmartViewInfosFromXML["mailbox_aoe"])
        
        #Mailbox : Bootstrap Configuration
        self.txtctrl_bootRcvOffset.SetValue(self.SmartViewInfosFromXML["mailbox_bootstrapconf_outstart"])
        self.txtctrl_bootRcvSize.SetValue(self.SmartViewInfosFromXML["mailbox_bootstrapconf_outlength"])
        self.txtctrl_bootSendOffset.SetValue(self.SmartViewInfosFromXML["mailbox_bootstrapconf_instart"])
        self.txtctrl_bootSendSize.SetValue(self.SmartViewInfosFromXML["mailbox_bootstrapconf_inlength"])
        
        #Mailbox : Standard Configuration
        self.txtctrl_stdRcvOffset.SetValue(self.SmartViewInfosFromXML["mailbox_standardconf_outstart"])
        self.txtctrl_stdRcvSize.SetValue(self.SmartViewInfosFromXML["mailbox_standardconf_outlength"])
        self.txtctrl_stdSendOffset.SetValue(self.SmartViewInfosFromXML["mailbox_standardconf_instart"])
        self.txtctrl_stdSendSize.SetValue(self.SmartViewInfosFromXML["mailbox_standardconf_inlength"])  
        
        
    def SetEEPROMData(self):
        #SII_DICT = { Parameter : (WordAddress, WordSize) }
        SII_Dict= { 'PDIControl' :                          ( '0', 1),
                    'PDIConfiguration' :                    ( '1', 1),
                    'PulseLengthOfSYNCSignals' :            ( '2', 1),
                    'ExtendedPDIConfiguration' :            ( '3', 1),
                    'ConfiguredStationAlias' :              ( '4', 1),
                    'Checksum' :                            ( '7', 1),
                    'VendorID' :                            ( '8', 2),
                    'ProductCode' :                         ( 'a', 2),
                    'RevisionNumber' :                      ( 'c', 2),
                    'SerialNumber' :                        ( 'e', 2),
                    'Execution Delay' :                     ('10', 1),
                    'Port0Delay' :                          ('11', 1),
                    'Port1Delay' :                          ('12', 1),
                    'BootstrapReceiveMailboxOffset' :       ('14', 1),
                    'BootstrapReceiveMailboxSize' :         ('15', 1),
                    'BootstrapSendMailboxOffset' :          ('16', 1),
                    'BootstrapSendMailboxSize' :            ('17', 1),
                    'StandardReceiveMailboxOffset' :        ('18', 1),
                    'StandardReceiveMailboxSize' :          ('19', 1),
                    'StandardSendMailboxOffset' :           ('1a', 1),
                    'StandardSendMailboxSize' :             ('1b', 1),
                    'MailboxProtocol' :                     ('1c', 1),
                    'Size' :                                ('3e', 1),
                    'Version' :                             ('3f', 1),
                    'First Category Type/Vendor Specific' : ('40', 1),
                    'Following Category Word Size' :        ('41', 1),
                    'Category Data' :                       ('42', 1),
                }
        
        #Config Data : EEPROM Size
        ##EEPROM's data in address '0x003f' is Size of EEPROM in KBit-1
        eeprom_size = (int(self.prnt.GetWordAddressData( SII_Dict.get('Size'),10 ))+1)/8*1024
        self.ctl_combobox_confEEPRomSize.Clear()
        self.ctl_combobox_confEEPRomSize.Append(str(eeprom_size))
        self.ctl_combobox_confEEPRomSize.Select(0)
        self.EEPROMSizeSelected = 0
        
        #Config Data : PDI Type
        cntPdiType = int(self.prnt.GetWordAddressData( SII_Dict.get('PDIControl'),16 ).split('x')[1][2:4], 16)
        
        self.ctl_combobox_confPDIType.Clear()
        
        self.pdiTypeSelected = -1
        ##The case that PDI Type is defined in EtherCAT Slave Controller Register Description
        for i in self.pdiType.keys():
            if cntPdiType == i:
                self.ctl_combobox_confPDIType.Append(self.pdiType[i][0])
                self.ctl_combobox_confPDIType.Select(0)
                self.pdiTypeSelected = 0
        ##Other case of PDI Types
        if self.pdiTypeSelected != 0:
            self.ctl_combobox_confPDIType.Append(str(cntPdiType))
            self.ctl_combobox_confPDIType.Select(0)
            self.pdiTypeSelected = 0
        
        #Config Data : Device Emulation
        ## Device Emulation is 8th bit of EEPROM's address '0x0000'
        deviceEmulation = bool(int(bin(int(self.prnt.GetWordAddressData( SII_Dict.get('PDIControl'),16 ).split('x')[1], 16)).split('b')[1].zfill(16)[7]))
        self.ctl_checkbox_deviceEmulation.SetValue(deviceEmulation)

        #device identity
        self.txtctrl_vendorId.SetValue      (self.prnt.GetWordAddressData( SII_Dict.get('VendorID'),16 ))
        self.txtctrl_productCode.SetValue   (self.prnt.GetWordAddressData( SII_Dict.get('ProductCode'),16 ))
        self.txtctrl_revNo.SetValue         (self.prnt.GetWordAddressData( SII_Dict.get('RevisionNumber'),16 ))
        self.txtctrl_serialNo.SetValue      (self.prnt.GetWordAddressData( SII_Dict.get('SerialNumber'),16 ))
        
        #mailbox
        self.txtctrl_bootRcvOffset.SetValue (self.prnt.GetWordAddressData( SII_Dict.get('BootstrapReceiveMailboxOffset'),10 ))
        self.txtctrl_bootRcvSize.SetValue   (self.prnt.GetWordAddressData( SII_Dict.get('BootstrapReceiveMailboxSize'),10 ))
        self.txtctrl_bootSendOffset.SetValue(self.prnt.GetWordAddressData( SII_Dict.get('BootstrapSendMailboxOffset'),10 ))
        self.txtctrl_bootSendSize.SetValue  (self.prnt.GetWordAddressData( SII_Dict.get('BootstrapSendMailboxSize'),10 ))
        
        self.txtctrl_stdRcvOffset.SetValue  (self.prnt.GetWordAddressData( SII_Dict.get('StandardReceiveMailboxOffset'),10 ))
        self.txtctrl_stdRcvSize.SetValue    (self.prnt.GetWordAddressData( SII_Dict.get('StandardReceiveMailboxSize'),10 ))
        self.txtctrl_stdSendOffset.SetValue (self.prnt.GetWordAddressData( SII_Dict.get('StandardSendMailboxOffset'),10 ))
        self.txtctrl_stdSendSize.SetValue   (self.prnt.GetWordAddressData( SII_Dict.get('StandardSendMailboxSize'),10 ))
     
    # Use this method avoid repeat declare 
    def MakeStaticBoxSizer(self, boxlabel):
        box = wx.StaticBox(self, -1, boxlabel)
        sizer = wx.StaticBoxSizer(box, wx.VERTICAL)

        return sizer
    
    # ------------------------- For notify error state -----------------------
    def NotConnectedDialog (self):
        dlg = wx.MessageDialog (self, 'It is not connected!!',
                             ' Warning...', wx.OK | wx.ICON_INFORMATION)
        dlg.ShowModal()
        dlg.Destroy()
        
    def NoSlaveDialog (self):
        dlg = wx.MessageDialog (self, 'There is no slave!!',
                             ' Warning...', wx.OK | wx.ICON_INFORMATION)
        dlg.ShowModal()
        dlg.Destroy()
        
    def InvalidFileDialog (self): # by Chaerin 130625
        dlg = wx.MessageDialog (self, 'The file does not exist!',
                             ' Warning...', wx.OK | wx.ICON_INFORMATION)
        dlg.ShowModal()
        dlg.Destroy()
        
        
class HexEditor(wx.Panel):
    def __init__(self, parent, controler, row, col):
        self.panel = wx.Panel.__init__(self, parent, -1)
        self.parent = parent
        self.Controler = controler
        self.row = row
        self.col = col
        
        # ui
        self.viewSizer =wx.FlexGridSizer(cols=1, hgap=10, rows=2, vgap=10)
        
        self.siiButtonSizer = wx.BoxSizer()
        self.siiUpload = wx.Button(self, -1, "Sii Upload")
        self.siiDownload = wx.Button(self, -1, "Sii Download")
        self.writeToBinFile = wx.Button(self, -1, "write to a binary file") # add by Chaerin 130108
        self.readFromBinFile = wx.Button(self, -1, "read from a binary file") # add by Chaerin 130108
        self.xmlToEEPROM = wx.Button(self, -1, "XML to EEPROM") # add by Chaerin 130509

        #self.siiView = SiiGridPanel(self, self.Controler, self.row, self.col)
        self.siiGrid = SiiGridTable(self, self.Controler, row, col) # by Chaerin 130529
        
        self.siiButtonSizer.Add(self.siiUpload)
        self.siiButtonSizer.Add(self.siiDownload)
        self.siiButtonSizer.Add(self.writeToBinFile) # add by Chaerin 130108
        self.siiButtonSizer.Add(self.readFromBinFile) # add by Chaerin 130108
        self.siiButtonSizer.Add(self.xmlToEEPROM) # add by Chaerin 130509
        
        self.viewSizer.Add(self.siiButtonSizer)
        #self.viewSizer.Add(self.siiView)    
        self.viewSizer.Add(self.siiGrid)  # by Chaerin 130529  
        
        # bind event
        self.siiUpload.Bind(wx.EVT_BUTTON, self.OnButtonSiiUpload)
        self.siiDownload.Bind(wx.EVT_BUTTON, self.OnButtonSiiDownload)
        self.writeToBinFile.Bind(wx.EVT_BUTTON, self.OnButtonWriteToBinFile) # add by Chaerin 130108
        self.readFromBinFile.Bind(wx.EVT_BUTTON, self.OnButtonReadFromBinFile) # add by Chaerin 130108    
        self.xmlToEEPROM.Bind(wx.EVT_BUTTON, self.OnButtonXmlToEEPROM) # add by Chaerin 130509
        
        self.SetSizer(self.viewSizer)     
        
        rootClass = self.Controler.GetRootClass()
        self.siiBinary = rootClass.XmlToEeprom()
        self.parent.HexRead(self.siiBinary)
        self.CreateSiiGridTable(self.parent.row, self.parent.col)
        self.siiGrid.SetValue(self.parent, self.siiBinary)
        self.siiGrid.Update()

        
    def CreateSiiGridTable(self, row, col):
        #self.siiView.UpdateTable(row, col)
        self.viewSizer.Detach(self.siiGrid)
        self.siiGrid.Destroy()
        self.siiGrid = SiiGridTable(self, self.Controler, row, col)
        self.viewSizer.Add(self.siiGrid)
        self.siiGrid.CreateGrid(row, col)
        self.SetSizer(self.viewSizer)
        self.viewSizer.FitInside(self.parent.parent) # by Chaerin 130625
        self.parent.parent.FitInside() # by Chaerin 130715

        
        
    def OnButtonSiiUpload(self, evt):  # by Chaerin 130121
        error, returnVal = self.Controler.GetSlaveXML()
        line = returnVal.split("\n")
        # if error != 0, Beremiz do not connect 
        if error != 0  : 
            self.NotConnectedDialog()
        # if len(line) == 1, Beremiz is connect but slave is not connect on master
        elif len(line) == 1 : # if it's windows, it's not 1 but 2.
            self.NoSlaveDialog()
        # returnVal is not None, Request of the state   
        elif len(line) > 1 :
            self.siiBinary = self.parent.LoadData()
            #self.siiBinary = self.parent.binaryCode # by Chaerin 130625
            self.CreateSiiGridTable(self.parent.row, self.parent.col)
            #self.siiView.siiGrid.SetValue(self.parent, self.parent.binaryCode)
            self.siiGrid.SetValue(self.parent, self.siiBinary) # by Chaerin 130529
            #self.siiView.siiGrid.Update() 
            self.siiGrid.Update()
            
    
    def OnButtonSiiDownload(self, evt):  # by Chaerin 130121
        error, returnVal = self.Controler.GetSlaveXML()
        line = returnVal.split("\n")
        # if error != 0, Beremiz do not connect 
        if error != 0  : 
            self.NotConnectedDialog()
        # if len(line) == 1, Beremiz is connect but slave is not connect on master
        elif len(line) == 1 : # if it's windows, it's not 1 but 2.
            self.NoSlaveDialog()
        # returnVal is not None, Request of the state   
        elif len(line) > 1 :
            error, returnVal = self.Controler.Sii_Write(self.siiBinary)
            self.Controler.Rescan()
            #self.parent.binaryCode = self.siiBinary
        
    def OnButtonWriteToBinFile(self, evt): # add by Chaerin 130108
        error, returnVal = self.Controler.GetSlaveXML()
        line = returnVal.split("\n")
        # if error != 0, Beremiz do not connect 
        if error != 0  : 
            self.NotConnectedDialog()
        # if len(line) == 1, Beremiz is connect but slave is not connect on master
        elif len(line) == 1 : # if it's windows, it's not 1 but 2.
            self.NoSlaveDialog()
        # returnVal is not None, Request of the state   
        elif len(line) > 1 :
        
            dialog = wx.FileDialog(self, _("Save as..."), os.getcwd(), "slave0.bin",  _("bin files (*.bin)|*.bin|All files|*.*"), wx.SAVE|wx.OVERWRITE_PROMPT)
        
            if dialog.ShowModal() == wx.ID_OK:
                filepath = dialog.GetPath()
                binfile = open(filepath,"wb")
                binfile.write(self.siiBinary)
                binfile.close()
    
            dialog.Destroy()  
    
    def OnButtonReadFromBinFile(self, evt): # # by Chaerin 130121
            
        dialog = wx.FileDialog(self, _("Choose a binary file"), os.getcwd(), "",  _("bin files (*.bin)|*.bin"), wx.OPEN)
        
        if dialog.ShowModal() == wx.ID_OK:
            filepath = dialog.GetPath()
            
            try:
                binfile = open(filepath, "rb")
                self.siiBinary = binfile.read()
                self.parent.HexRead(self.siiBinary)
                self.CreateSiiGridTable(self.parent.row, self.parent.col)
                #self.siiView.siiGrid.SetValue(self.parent, self.siiBinary)
                self.siiGrid.SetValue(self.parent, self.siiBinary) # by Chaerin 130529
                #self.siiView.siiGrid.Update()
                self.siiGrid.Update()
                #self.siiDownload.Enable() #Enable siiDownload button
            except:
                self.InvalidFileDialog()
            
        dialog.Destroy()            
            
    def OnButtonXmlToEEPROM(self, evt): # by Chaerin 130509
        rootClass = self.Controler.GetRootClass()
        self.siiBinary = rootClass.XmlToEeprom() # by Chaerin 130625
        self.parent.HexRead(self.siiBinary) # by Chaerin 130625
        
        self.CreateSiiGridTable(self.parent.row, self.parent.col)
        self.siiGrid.SetValue(self.parent, self.siiBinary) # by Chaerin 130625
        
        self.siiGrid.Update()
            #self.siiDownload.Enable()
        
    def NotConnectedDialog (self):
        dlg = wx.MessageDialog (self, 'It is not connected!!',
                             ' Warning...', wx.OK | wx.ICON_INFORMATION)
        dlg.ShowModal()
        dlg.Destroy()
        
    def NoSlaveDialog (self):
        dlg = wx.MessageDialog (self, 'There is no slave!!',
                             ' Warning...', wx.OK | wx.ICON_INFORMATION)
        dlg.ShowModal()
        dlg.Destroy()
    
    def InvalidFileDialog (self): # by Chaerin 130625
        dlg = wx.MessageDialog (self, 'The file does not exist!',
                             ' Warning...', wx.OK | wx.ICON_INFORMATION)
        dlg.ShowModal()
        dlg.Destroy()
        
        
class SiiGridPanel(wx.Panel):
    def __init__(self, parent, controler, row, col):
        self.parent = parent
        self.controler = controler
        
        wx.Panel.__init__(self, parent, -1)
        sizer = wx.FlexGridSizer(cols=1, hgap=0, rows=1, vgap=0)     
        self.siiGrid = SiiGridTable(self, self.controler, row, col)
        sizer.Add(self.siiGrid)
        self.SetSizer(sizer)
        
    def UpdateTable(self, row, col):
        self.siiGrid.Destroy()
        self.siiGrid = SiiGridTable(self, self.controler, row, col)
        self.siiGrid.CreateGrid(row, col)
        
        
class SiiGridTable(wx.grid.Grid):  
    def __init__(self, parent, controler, row, col):        
        self.prnt = parent
        self.controler = controler
        self.data = {}
        self.row = row
        self.col = col    
        
        wx.grid.Grid.__init__(self, parent, -1, size=(830,450), style=wx.ALIGN_CENTRE_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL)        

    def SetValue(self, parent, value):
        self.SetRowLabelSize(100)
        for col in range(self.col):
            if col == 16: # by Chaerin 130305
                self.SetColLabelValue(16, "Text View")
                self.SetColSize(16, (self.GetSize().x-120)*4/20)
            else:
                self.SetColLabelValue(col, '%s'%col)
                self.SetColSize(col, (self.GetSize().x-120)/20)
            
        row = col = 0
        
        for rowIndex in parent.hexCode: 
            col = 0
            self.SetRowLabelValue(row, '%s'%self.GetAddress(row*(self.col-1)))
            for hex in rowIndex:
                self.SetCellValue(row, col, '%s'%hex)
                
                if col == 16: 
                    self.SetCellAlignment(row, col, wx.ALIGN_LEFT, wx.ALIGN_CENTER)
                else:
                    self.SetCellAlignment(row, col, wx.ALIGN_CENTRE, wx.ALIGN_CENTER)
                    
                self.SetReadOnly(row, col, True)  # by Chaerin 110119
                col = col + 1
            row = row + 1
                
    def GetAddress(self, index):
        hexAddress = hex(index)
        preAddress = hexAddress[0:2]
        postAddress = hexAddress[2:len(hexAddress)]

        if len(postAddress) == 1 :
            postAddress = "000" + postAddress
            hexAddress = preAddress + postAddress
        elif len(postAddress) == 2 :
            postAddress = "00" + postAddress
            hexAddress = preAddress + postAddress
        else:
            postAddress = "0" + postAddress
            hexAddress = preAddress + postAddress
        
        return hexAddress
        
class RegisterAccessPanel(wx.Panel):
    def __init__(self, parent, controler):
        
        self.parent = parent
        self.controler = controler
        self.__init_data()
        
        # Previous value of register data for register description configuration
        self.pre_escType = ""
        self.pre_fmmuNumber = ""
        self.pre_smNumber = ""
        self.pre_pdiType = ""
        
        wx.Panel.__init__(self, parent, -1)
        
        # sizer
        sizer = wx.FlexGridSizer(cols=1, hgap=20, rows=2, vgap=5)
        button_sizer = wx.FlexGridSizer(cols=2, hgap=10, rows=1, vgap=10)
        
        # item
        self.reload_button = wx.Button(self, -1, "Reload")
        self.compactView_checkbox = wx.CheckBox(self, -1, "Compact View")        
        self.register_notebook = RegisterNotebook(self, self.controler)
        
        # add item in sizer
        button_sizer.Add(self.reload_button)
        button_sizer.Add(self.compactView_checkbox)
        sizer.Add(button_sizer)
        sizer.Add(self.register_notebook)
        self.SetSizer(sizer)  
        
        # event mapping
        self.reload_button.Bind(wx.EVT_BUTTON, self.OnReloadButton)
        self.compactView_checkbox.Bind(wx.EVT_CHECKBOX, self.ToggleCompactViewCheckbox)
        
        # default setting of data
        self.BasicSetData()
        if self.controler.RegData is not "":
            self.ParseData()
            #data setting in grid
            self.register_notebook.win0.mainTablePanel.registerMainTable.CreateGrid(self.win0_mainRow, self.mainCol)
            self.register_notebook.win0.mainTablePanel.registerMainTable.SetValue(self, self.regMonitorData, 0, 512)
            self.register_notebook.win1.mainTablePanel.registerMainTable.CreateGrid(self.win0_mainRow, self.mainCol)
            self.register_notebook.win1.mainTablePanel.registerMainTable.SetValue(self, self.regMonitorData, 512, 1024)
            self.register_notebook.win2.mainTablePanel.registerMainTable.CreateGrid(self.win0_mainRow, self.mainCol)
            self.register_notebook.win2.mainTablePanel.registerMainTable.SetValue(self, self.regMonitorData, 1024, 1536)
            self.register_notebook.win3.mainTablePanel.registerMainTable.CreateGrid(self.win0_mainRow, self.mainCol)
            self.register_notebook.win3.mainTablePanel.registerMainTable.SetValue(self, self.regMonitorData, 1536, 2048)
        else:
            self.compactView_checkbox.Disable()
        
        if 1 == 0 : #error check about connection, etc.
            self.LoadData()
            self.BasigSetData()
            self.ParseData()
        
            #data setting in grid
            self.register_notebook.win0.mainTablePanel.registerMainTable.CreateGrid(self.win0_mainRow, self.mainCol)
            self.register_notebook.win0.mainTablePanel.registerMainTable.SetValue(self, self.regMonitorData, 0, 512)
            self.register_notebook.win1.mainTablePanel.registerMainTable.CreateGrid(self.win0_mainRow, self.mainCol)
            self.register_notebook.win1.mainTablePanel.registerMainTable.SetValue(self, self.regMonitorData, 512, 1024)
            self.register_notebook.win2.mainTablePanel.registerMainTable.CreateGrid(self.win0_mainRow, self.mainCol)
            self.register_notebook.win2.mainTablePanel.registerMainTable.SetValue(self, self.regMonitorData, 1024, 1536)
            self.register_notebook.win3.mainTablePanel.registerMainTable.CreateGrid(self.win0_mainRow, self.mainCol)
            self.register_notebook.win3.mainTablePanel.registerMainTable.SetValue(self, self.regMonitorData, 1536, 2048)
        
    
    def __init_data(self):
        
        self.compactFlag = False
        
        #main grids' rows and cols
        self.win0_mainRow = 512
        self.win1_mainRow = 512
        self.win2_mainRow = 512
        self.win3_mainRow = 512
        self.mainCol = 4
        
        #main grids' data range
        self.win0_range = [0, 512]
        self.win1_range = [512, 1024]
        self.win2_range = [1024, 1536]
        self.win3_range = [1536, 2048]
        
        # Register Description Dictionary for main grid; It contains description of Register's each offset.
        # without FMMU(0x0600:0x06FF), SM(0x0800:0x08FF), PowerOn(0x0e00:0x0eff) and User Ram(0x0f80:0x0ffe)
        self.registerDescription_Dict= {'0000': "ESC Rev/Type",
                                        '0002': "ESC Build",
                                        '0004': "SM/FMMU Cnt",
                                        '0006': "Ports/DPRAM",
                                        '0008': "Features",
                                        '0010': "Phys Addr",
                                        '0012': "Configured Station Alias",
                                        '0020': "Register Protect",
                                        '0030': "Access Protect",
                                        '0040': "ESC Reset",
                                        '0100': "ESC Ctrl",
                                        '0102': "ESC Ctrl Ext",
                                        '0108': "Phys. RW Offset",
                                        '0110': "ESC Status",
                                        '0120': "AL Ctrl",
                                        '0130': "AL Status",
                                        '0134': "AL Status Code",
                                        '0138': "RUN/ERR LED Override",
                                        '0140': "PDI Ctrl",
                                        '014e': "PDI Information",
                                        '0150': "PDI Cfg",
                                        '0152': "PDI Cfg Ext",
                                        '0200': "ECAT IRQ Mask",
                                        '0204': "PDI IRQ Mask L",
                                        '0206': "PDI IRQ Mask H",
                                        '0210': "ECAT IRQ",
                                        '0220': "PDI IRQ 1",
                                        '0222': "PDI IRQ 2",
                                        '0300': "CRC A",
                                        '0302': "CRC B",
                                        '0304': "CRC C",
                                        '0306': "CRC D",
                                        '0308': "Forw. CRC A/B",
                                        '030a': "Forw. CRC C/D",
                                        '030c': "Proc. CRC/PDI Err",
                                        '030e': "PDI Error Code",
                                        '0310': "Link Lost A/B",
                                        '0312': "Link Lost C/D",
                                        '0400': "WD Divisor",
                                        '0410': "WD Time PDI",
                                        '0420': "WD Time SM",
                                        '0440': "WD Status",
                                        '0442': "WD PDI/SM Counter",
                                        '0500': "EEPROM Assign",
                                        '0502': "EEPROM Ctrl/Status",
                                        '0504': "EEPROM Address L",
                                        '0506': "EEPROM Address H",
                                        '0508': "EEPROM Data 0",
                                        '050a': "EEPROM Data 1",
                                        '050c': "EEPROM Data 2",
                                        '050e': "EEPROM Data 3",
                                        '0510': "Phy MIO Ctrl/Status",
                                        '0512': "Phy MIO Address",
                                        '0514': "Phy MIO Data",
                                        '0516': "MIO Access",
                                        '0518': "MIO Port Status A/B",
                                        '051a': "MIO Port Status C/D",
                                        '0900': "DC RecvTimeL_A",
                                        '0902': "DC RecvTimeH_A",
                                        '0904': "DC RecvTimeL_B",
                                        '0906': "DC RecvTimeH_B",
                                        '0908': "DC RecvTimeL_C",
                                        '090a': "DC RecvTimeH_C",
                                        '090c': "DC RecvTimeL_D",
                                        '090e': "DC RecvTimeH_D",
                                        '0910': "DC SysTimeLL",
                                        '0912': "DC SysTimeLH",
                                        '0914': "DC SysTimeHL",
                                        '0916': "DC SysTimeHH",
                                        '0918': "DC RecvTimeLL_A",
                                        '091a': "DC RecvTimeLH_A",
                                        '091c': "DC RecvTimeHL_A",
                                        '091e': "DC RecvTimeHH_A",
                                        '0920': "DC SysTimeOffsLL",
                                        '0922': "DC SysTimeOffsLH",
                                        '0924': "DC SysTimeOffsHL",
                                        '0926': "DC SysTimeOffsHH",
                                        '0928': "DC SysTimeDelayL",
                                        '092a': "DC SysTimeDelayH",
                                        '092c': "DC CtrlErrorL",
                                        '092e': "DC CtrlErrorH",
                                        '0930': "DC SpeedStart",
                                        '0932': "DC SpeedDiff",
                                        '0934': "DC FiltExp",
                                        '0936': "Receive Time Latch Mode",
                                        '0980': "DC Assign/Activ",
                                        '0982': "DC CycImpulse",
                                        '0984': "DC Activation Status",
                                        '098e': "DC CycSync State",
                                        '0990': "DC StartTime0 LL",
                                        '0992': "DC StartTime0 LH",
                                        '0994': "DC StartTime0 HL",
                                        '0996': "DC StartTime0 HH",
                                        '0998': "DC StartTime1 LL",
                                        '099a': "DC StartTime1 LH",
                                        '099c': "DC StartTime1 HL",
                                        '099e': "DC StartTime1 HH",
                                        '09a0': "DC CycTime0 L",
                                        '09a2': "DC CycTime0 H",
                                        '09a4': "DC CycTime1 L",
                                        '09a6': "DC CycTime1 H",
                                        '09a8': "DC Latch Ctrl",
                                        '09ae': "DC Latch Status",
                                        '09b0': "DC Latch0 Pos LL",
                                        '09b2': "DC Latch0 Pos LH",
                                        '09b4': "DC Latch0 Pos HL",
                                        '09b6': "DC Latch0 Pos HH",
                                        '09b8': "DC Latch0 Neg LL",
                                        '09ba': "DC Latch0 Neg LH",
                                        '09bc': "DC Latch0 Neg HL",
                                        '09be': "DC Latch0 Neg HH",
                                        '09c0': "DC Latch1 Pos LL",
                                        '09c2': "DC Latch1 Pos LH",
                                        '09c4': "DC Latch1 Pos HL",
                                        '09c6': "DC Latch1 Pos HH",
                                        '09c8': "DC Latch1 Neg LL",
                                        '09ca': "DC Latch1 Neg LH",
                                        '09cc': "DC Latch1 Neg HL",
                                        '09ce': "DC Latch1 Neg HH",
                                        '09f0': "DC RecvSMChange L",
                                        '09f2': "DC RecvSMChange H",
                                        '09f8': "DC PDISMStart L",
                                        '09fa': "DC PDISMStart H",
                                        '09fc': "DC PDISMChange L",
                                        '09fe': "DC PDISMChange H",
                                        '0f00': "Digital Out L",
                                        '0f02': "Digital Out H",
                                        '0f10': "GPO LL",
                                        '0f12': "GPO LH",
                                        '0f14': "GPO HL",
                                        '0f16': "GPO HH",
                                        '0f18': "GPI LL",
                                        '0f1a': "GPI LH",
                                        '0f1c': "GPI HL",
                                        '0f1e': "GPI HH",
                                        }
        
        # add User Ram label into register description dictionary
        # This range is 0x0f80:0x0fff
        for index in range(64):
            userRam_key = hex(int(0x0f80) + index*2).split('x')[1].zfill(4)
            self.registerDescription_Dict[str(userRam_key)] = "User Ram"
        
        # Register Description Dictionary for sub grid; It contains description of Register's each bits.
        # It is just general values. values depended on other value are added later.
        self.registerSubGrid_Dict = {'0000': [['0-7', 'Type', {'00000010':'ESC10/ESC20', '00000100':'IP Core', '00010001':'ET1100', '00010010':'ET1200'}], ['8-15', 'Revision', {}]],
                                     '0004': [['0-7', 'FMMU cnt', {}], ['8-15', 'SM cnt', {}]],
                                     '0006': [['0-7', 'DPRAM (Kbyte)', {}], ['8-9', 'Port A', {'00':'Not implemented', '01':'Not configured(EEPROM)', '10':'EBUS', '11':'MII/RMII'}], ['10-11', 'Port B', {'00':'Not implemented', '01':'Not configured(EEPROM)', '10':'EBUS', '11':'MII/RMII'}], ['12-13', 'Port C', {'00':'Not implemented', '01':'Not configured(EEPROM)', '10':'EBUS', '11':'MII/RMII'}], ['14-15', 'Port D', {'00':'Not implemented', '01':'Not configured(EEPROM)', '10':'EBUS', '11':'MII/RMII'}]],
                                     '0008': [['0', 'FMMU Operation', {'0':'Bit oriented', '1':'Byte oriented'}], ['2', 'DC support', {'0':'FALSE', '1':'TRUE'}], ['3', 'DC 64 bit support', {'0':'FALSE', '1':'TRUE'}], ['4', 'E-Bus low jitter', {'0':'FALSE', '1':'TRUE'}], ['5', 'E-Bus ext. link detection', {'0':'FALSE', '1':'TRUE'}], ['6', 'MII ext. link detection', {'0':'FALSE', '1':'TRUE'}], ['7', 'Separate Handling of FCS Errors', {'0':'FALSE', '1':'TRUE'}], ['8', 'DC SYNC ext. Activation', {'0':'FALSE', '1':'TRUE'}], ['9', 'EtherCAT LRW cmd. support', {'0':'FALSE', '1':'TRUE'}], ['10', 'EtherCAT R/W cmd. support', {'0':'FALSE', '1':'TRUE'}], ['11', 'Fixed FMMU/SM Cfg.', {'0':'FALSE', '1':'TRUE'}]],
                                     '0040': [['0-7', 'ESC reset ECAT', {}], ['8-15', 'ESC reset PDI', {}]],
                                     '0102': [['0-2', 'FIFO size', {}], ['3', 'Low E-Bus jitter', {'0':'Deactive', '1':'Active'}], ['8', 'Second address', {'0':'Deactive', '1':'Active'}]],
                                     '0110': [['0', 'Operation', {'0':'FALSE', '1':'TRUE'}], ['1', 'PDI watchdog', {'0':'expired', '1':'reloaded'}], ['2', 'Enh. Link Detection', {'0':'Deactive', '1':'Active'}], ['4', 'Physical link Port A', {'0':'FALSE', '1':'TRUE'}], ['5', 'Physical link Port B', {'0':'FALSE', '1':'TRUE'}], ['6', 'Physical link Port C', {'0':'FALSE', '1':'TRUE'}], ['7', 'Physical link Port D', {'0':'FALSE', '1':'TRUE'}], ['8-9', 'Port A', {'00':'Loop Open, no link', '01':'Loop closed, no link', '10':'Loop open, with link', '11':'Loop closed, with link'}], ['10-11', 'Port B', {'00':'Loop Open, no link', '01':'Loop closed, no link', '10':'Loop open, with link', '11':'Loop closed, with link'}], ['12-13', 'Port C', {'00':'Loop Open, no link', '01':'Loop closed, no link', '10':'Loop open, with link', '11':'Loop closed, with link'}], ['14-15', 'Port D', {'00':'Loop Open, no link', '01':'Loop closed, no link', '10':'Loop open, with link', '11':'Loop closed, with link'}]],
                                     '0120': [['0-3', 'AL Ctrl', {'0000':'INIT', '0011':'Bootstrap', '0010':'PREOP', '0100':'SAFEOP', '1000':'OP'}], ['4', 'Error Ack', {}], ['5', 'Device Identification', {'0':'No request', '1':'Device Identification request'}]],
                                     '0130': [['0-3', 'AL Status', {'0000':'INIT', '0011':'Bootstrap', '0010':'PREOP', '0100':'SAFEOP', '1000':'OP'}], ['4', 'Error', {}], ['5', 'Device Identification', {'0':'not valid', '1':'loaded'}]],
                                     '0140': [['0-7', 'PDI', {'00000000':'none', '00000001':'4 Digital Input', '00000010':'4 Digital Output', '00000011':'2 DI and 2 DO', '00000100':'Digital I/O', '00000101':'SPI Slave', '00000110':'Oversampling I/O', '00000111':'EtherCAT Bridge (port3)', '00001000':'uC async. 16bit', '00001001':'uC async. 8bit', '00001010':'uC sync. 16bit', '00001011':'uC sync. 8bit', '00010000':'32 Digtal Input and 0 Digital Output', '00010001':'24 Digtal Input and 8 Digital Output', '00010010':'16 Digtal Input and 16 Digital Output', '00010011':'8 Digtal Input and 24 Digital Output', '00010100':'0 Digtal Input and 32 Digital Output', '11111111':'On-chip bus'}], ['8', 'Device emulation', {'0':'FALSE', '1':'TRUE'}], ['9', 'Enhanced link detection all ports', {'0':'Disabled', '1':'Enabled'}], ['10', 'DC SYNC Out Unit', {'0':'Disabled', '1':'Enabled'}], ['11', 'DC Latch In Unit', {'0':'Disabled', '1':'Enabled'}], ['12', 'Enhanced link port 0', {'0':'Disabled', '1':'Enabled'}], ['13', 'Enhanced link port 1', {'0':'Disabled', '1':'Enabled'}], ['14', 'Enhanced link port 2', {'0':'Disabled', '1':'Enabled'}], ['15', 'Enhanced link port 3', {'0':'Disabled', '1':'Enabled'}]],
                                     '0200': [['0', 'Latch event', {'0':'FALSE', '1':'TRUE'}], ['2', 'ESC Status event', {'0':'FALSE', '1':'TRUE'}], ['3', 'AL Status event', {'0':'FALSE', '1':'TRUE'}]],
                                     '0204': [['0', 'AL Ctrl', {'0':'FALSE', '1':'TRUE'}], ['1', 'Latch input', {'0':'FALSE', '1':'TRUE'}], ['2', 'SYNC 0', {'0':'FALSE', '1':'TRUE'}], ['3', 'SYNC 1', {'0':'FALSE', '1':'TRUE'}], ['5', 'EEPROM command pending', {'0':'FALSE', '1':'TRUE'}]],
                                     '0210': [['0', 'Latch event', {'0':'FALSE', '1':'TRUE'}], ['2', 'ESC Status event', {'0':'FALSE', '1':'TRUE'}], ['3', 'AL Status event', {'0':'FALSE', '1':'TRUE'}]],
                                     '0220': [['0', 'AL Ctrl', {'0':'FALSE', '1':'TRUE'}], ['1', 'Latch input', {'0':'FALSE', '1':'TRUE'}], ['2', 'DC SYNC 0', {'0':'FALSE', '1':'TRUE'}], ['3', 'DC SYNC 1', {'0':'FALSE', '1':'TRUE'}], ['4', 'SM activation reg. changed', {'0':'FALSE', '1':'TRUE'}], ['5', 'EEPROM command pending', {'0':'FALSE', '1':'TRUE'}], ['6', 'Watchdog Process Data expired', {'0':'FALSE', '1':'TRUE'}]],
                                     '0300': [['0-7', 'Invalid frame', {}], ['8-15', 'RX error', {}]],
                                     '0302': [['0-7', 'Invalid frame', {}], ['8-15', 'RX error', {}]],
                                     '0304': [['0-7', 'Invalid frame', {}], ['8-15', 'RX error', {}]],
                                     '0306': [['0-7', 'Invalid frame', {}], ['8-15', 'RX error', {}]],
                                     '0308': [['0-7', 'Port A', {}], ['8-15', 'Port B', {}]],
                                     '030a': [['0-7', 'Port C', {}], ['8-15', 'Port D', {}]],
                                     '030c': [['0-7', 'Process unit error', {}], ['8-15', 'PDI error', {}]],
                                     '0310': [['0-7', 'Port A', {}], ['8-15', 'Port B', {}]],
                                     '0312': [['0-7', 'Port C', {}], ['8-15', 'Port D', {}]],
                                     '0440': [['0', 'PD watchdog', {'0':'expired', '1':'active or disabled'}]],
                                     '0442': [['0-7', 'SM watchdog cnt', {}], ['8-15', 'PDI watchdog cnt', {}]],
                                     '0500': [['0', 'EEPROM access ctrl', {'0':'ECAT', '1':'PDI'}], ['1', 'Reset PDI access', {'0':'Do not change Bit 501.0', '1':'Reset Bit 501.0 to 0'}], ['8', 'EEPROM access status', {'0':'ECAT', '1':'PDI'}]],
                                     '0510': [['0', 'Write enable', {'0':'FALSE', '1':'TRUE'}], ['1', 'PDI control possible', {'0':'FALSE', '1':'TRUE'}], ['2', 'link detection active', {'0':'FALSE', '1':'TRUE'}], ['3-7', 'Phy address offset', {}], ['8', 'Read access', {'0':'FALSE', '1':'TRUE'}], ['9', 'Write access', {'0':'FALSE', '1':'TRUE'}], ['13', 'Read error occured', {'0':'FALSE', '1':'TRUE'}], ['14', 'Write error occured', {'0':'FALSE', '1':'TRUE'}], ['15', 'Busy', {'0':'FALSE', '1':'TRUE'}]],
                                     '0512': [['0-4', 'Phy address', {}], ['8-11', 'MIO address', {}]],
                                     '0516': [['0', 'ECAT claims exclusive access', {'0':'FALSE', '1':'TRUE'}], ['8', 'PDI has access to MII management', {'0':'FALSE', '1':'TRUE'}], ['9', 'Force PDI to reset 517.0', {'0':'FALSE', '1':'TRUE'}]],
                                     '0518': [['0', 'Port A: Physical link detected', {'0':'FALSE', '1':'TRUE'}], ['1', 'Port A: Link detected', {'0':'FALSE', '1':'TRUE'}], ['2', 'Port A: Link status error', {'0':'FALSE', '1':'TRUE'}], ['3', 'Port A: Read error', {'0':'FALSE', '1':'TRUE'}], ['4', 'Port A: Link partner error', {'0':'FALSE', '1':'TRUE'}], ['5', 'Port A: Phy config updated', {'0':'FALSE', '1':'TRUE'}], ['8', 'Port B: Physical link detected', {'0':'FALSE', '1':'TRUE'}], ['9', 'Port B: Link detected', {'0':'FALSE', '1':'TRUE'}], ['10', 'Port B: Link status error', {'0':'FALSE', '1':'TRUE'}], ['11', 'Port B: Read error', {'0':'FALSE', '1':'TRUE'}], ['12', 'Port B: Link partner error', {'0':'FALSE', '1':'TRUE'}], ['13', 'Port B: Phy config updated', {'0':'FALSE', '1':'TRUE'}]],
                                     '051a': [['0', 'Port C: Physical link detected', {'0':'FALSE', '1':'TRUE'}], ['1', 'Port C: Link detected', {'0':'FALSE', '1':'TRUE'}], ['2', 'Port C: Link status error', {'0':'FALSE', '1':'TRUE'}], ['3', 'Port C: Read error', {'0':'FALSE', '1':'TRUE'}], ['4', 'Port C: Link partner error', {'0':'FALSE', '1':'TRUE'}], ['5', 'Port C: Phy config updated', {'0':'FALSE', '1':'TRUE'}], ['8', 'Port D: Physical link detected', {'0':'FALSE', '1':'TRUE'}], ['9', 'Port D: Link detected', {'0':'FALSE', '1':'TRUE'}], ['10', 'Port D: Link status error', {'0':'FALSE', '1':'TRUE'}], ['11', 'Port D: Read error', {'0':'FALSE', '1':'TRUE'}], ['12', 'Port D: Link partner error', {'0':'FALSE', '1':'TRUE'}], ['13', 'Port D: Phy config updated', {'0':'FALSE', '1':'TRUE'}]],
                                     '0934': [['0-7', 'System time diff', {}], ['8-15', 'Speed counter', {}]],
                                     '0980': [['0', 'Write access cyclic', {'0':'ECAT', '1':'PDI'}], ['4', 'Write access Latch 0', {'0':'ECAT', '1':'PDI'}], ['5', 'Write access Latch 1', {'0':'ECAT', '1':'PDI'}], ['8', 'Sync Out Unit activation', {'0':'Deactivated', '1':'Activated'}], ['9', 'Generate SYNC 0', {'0':'FALSE', '1':'TRUE'}], ['10', 'Generate SYNC 1', {'0':'FALSE', '1':'TRUE'}], ['11', 'Auto activation', {'0':'FALSE', '1':'TRUE'}], ['12', 'Start time extension 32->64', {'0':'FALSE', '1':'TRUE'}], ['13', 'Start time check', {'0':'FALSE', '1':'TRUE'}], ['14', 'Half range', {'0':'FALSE', '1':'TRUE'}], ['15', 'Debug pulse', {'0':'FALSE', '1':'TRUE'}]],
                                     '098e': [['0', 'SYNC 0 triggered', {'0':'FALSE', '1':'TRUE'}], ['8', 'SYNC 1 triggered', {'0':'FALSE', '1':'TRUE'}]],
                                     '09a8': [['0', 'Latch 0 pos', {'0':'Continuous', '1':'Single event'}], ['1', 'Latch 0 neg', {'0':'Continuous', '1':'Single event'}], ['8', 'Latch 1 pos', {'0':'Continuous', '1':'Single event'}], ['9', 'Latch 1 neg', {'0':'Continuous', '1':'Single event'}]]
                                     }
        
    def LoadData(self):
        self.register_data = ""
        #reg_read
        #ex : reg_read -p 0 0x0000 0x0001
        #return value : 0x11
        self.register_data = self.register_data + self.controler.Reg_Read("0x0000", "0x0400")
        self.register_data = self.register_data + " " + self.controler.Reg_Read("0x0400", "0x0400")
        self.register_data = self.register_data + " " + self.controler.Reg_Read("0x0800", "0x0400")
        self.register_data = self.register_data + " " + self.controler.Reg_Read("0x0c00", "0x0400")
        self.controler.RegData = self.register_data
        
        # store previous value (ESC type, port number of FMMU, port number of SM, and PDI type)
        self.pre_escType = self.controler.Reg_EscType
        self.pre_fmmuNumber = self.controler.Reg_FmmuNumber
        self.pre_smNumber = self.controler.Reg_SmNumber
        self.pre_pdiType = self.controler.Reg_PdiType
        
        # update value (ESC type, port number of FMMU, port number of SM, and PDI type)
        self.controler.Reg_EscType = self.controler.Reg_Read("0x0000", "0x0001")
        self.controler.Reg_FmmuNumber = self.controler.Reg_Read("0x0004", "0x0001")
        #self.smNumber = self.controler.Reg_Read("0x0005", "0x0001")
        self.controler.Reg_SmNumber = self.controler.Reg_Read("0x0005", "0x0001")
        #self.pdiType = self.controler.Reg_Read("0x0140", "0x0001")
        self.controler.Reg_PdiType = self.controler.Reg_Read("0x0140", "0x0001")
        
        #Enable compactView checkbox
        self.compactView_checkbox.Enable()
    
        
    def BasicSetData(self):
        
        # update Power On label into register description dictionary
        if self.pre_escType is not self.controler.Reg_EscType:
            # delete previous Power On label
            for index in range(128):
                powerOn_key = hex(int(0x0e00) + index*2).split('x')[1].zfill(4)
                if self.registerDescription_Dict.has_key(powerOn_key):
                    del self.registerDescription_Dict[powerOn_key]
                if self.registerSubGrid_Dict.has_key(powerOn_key):
                    del self.registerSubGrid_Dict[powerOn_key]
            
            # delete previous subgrid label
            if self.registerSubGrid_Dict.has_key('0002'): # Register Build (0x0002:0x0003)
                del self.registerSubGrid_Dict['0002']
            if self.registerSubGrid_Dict.has_key('0100'): # Part of Register ESC DL Control (0x0100:0x0101)
                del self.registerSubGrid_Dict['0100']
            if self.registerSubGrid_Dict.has_key('0140'): # PDI Control (0x0140:0x0141)
                del self.registerSubGrid_Dict['0140']
            if self.registerSubGrid_Dict.has_key('0502'): # Register EEPROM Control/Status (0x0502:0x0503)
                del self.registerSubGrid_Dict['0502']
            if self.registerSubGrid_Dict.has_key('0510'): # MII Management Control/Status (0x0510:0x0511)
                del self.registerSubGrid_Dict['0510']
            if self.registerSubGrid_Dict.has_key('09ae'): # Latch0/1 Status (0x09ae:0x09af)
                del self.registerSubGrid_Dict['09ae']
            
            # add new Power On label and add new subgrid label
            ## The case that ESC Type is ESC10 or ESC20
            if self.controler.Reg_EscType == '0x02': # Power On value is FPGA Update(ESC10/20 and TwinCAT only); from "EtherCAT Slave Controller SectionII - Register Description" document
                # Add new Sub Grid Label
                ## PDI Control (0x0140:0x0141)
                self.registerSubGrid_Dict['0140'] = [['0-7', 'PDI', {'00000000':'none', '00000100':'Digital I/O', '00000101':'SPI Slave', '00000111':'EtherCAT Bridge (port3)', '00001000':'uC async. 16bit', '00001001':'uC async. 8bit', '00001010':'uC sync. 16bit', '00001011':'uC sync. 8bit', '00010000':'32 Digtal Input and 0 Digital Output', '00010001':'24 Digtal Input and 8 Digital Output', '00010010':'16 Digtal Input and 16 Digital Output', '00010011':'8 Digtal Input and 24 Digital Output', '00010100':'0 Digtal Input and 32 Digital Output', '11111111':'On-chip bus'}], ['8', 'Device emulation', {'0':'FALSE', '1':'TRUE'}]]
                ## Register EEPROM Control/Status (0x0502:0x0503)
                self.registerSubGrid_Dict['0502'] = [['0', 'Write access', {'0':'FALSE', '1':'TRUE'}], ['5', 'EEPROM emulation', {'0':'Notmal operation', '1':'PDI emulates EEPROM'}], ['6', '8 byte access', {'0':'FALSE', '1':'TRUE'}], ['8', 'Read access', {'0':'FALSE', '1':'TRUE'}], ['9', 'Write access', {'0':'FALSE', '1':'TRUE'}], ['10', 'Reload access', {'0':'FALSE', '1':'TRUE'}], ['11', 'CRC error', {'0':'FALSE', '1':'TRUE'}], ['12', 'Load error', {'0':'FALSE', '1':'TRUE'}], ['13', 'Cmd error', {'0':'FALSE', '1':'TRUE'}], ['14', 'Write error', {'0':'FALSE', '1':'TRUE'}], ['15', 'Busy', {'0':'FALSE', '1':'TRUE'}]]
                ## Register Receive Time Latch Mode (0x0936)
                self.registerSubGrid_Dict['0936'] = [['0', 'Receive Time Latch Mode', {'0':'Forwarding mode', '1':'Reverse mode'}]]
                ## Register AL Event Request and Mask
                self.registerSubGrid_Dict['0204'].append(['4', 'SM changed', {'0':'FALSE', '1':'TRUE'}])
                self.registerSubGrid_Dict['0220'].append(['4', 'SM changed', {'0':'FALSE', '1':'TRUE'}])
                
            ## The case that ESC Type is IP Core
            if self.controler.Reg_EscType == '0x04':
                self.registerDescription_Dict['0e00'] = "Product ID"
                self.registerDescription_Dict['0e02'] = "Product ID"
                self.registerDescription_Dict['0e04'] = "Product ID"
                self.registerDescription_Dict['0e06'] = "Product ID"
                self.registerDescription_Dict['0e08'] = "Vendor ID"
                self.registerDescription_Dict['0e0a'] = "Vendor ID"
                self.registerDescription_Dict['0e0c'] = "Vendor ID"
                self.registerDescription_Dict['0e0e'] = "Vendor ID"
                
                # Add new Sub Grid Label
                ## Register Build (0x0002:0x0003)
                self.registerSubGrid_Dict['0002'] = [['0-3', 'maintenance version', {}], ['4-7', 'minor version', {}]]
                ## Part of Register ESC DL Control (0x0100:0x0103)
                self.registerSubGrid_Dict['0100'] = [['0', 'kill non EtherCAT frames', {}], ['1', 'Temporary loop control', {'0':'Permanent use', '1':'Use for about 1 sec.'}], ['8-9', 'Port A', {'00':'Auto loop', '01':'Auto close', '10':'Loop open', '11':'Loop closed'}], ['10-11', 'Port B', {'00':'Auto loop', '01':'Auto close', '10':'Loop open', '11':'Loop closed'}], ['12-13', 'Port C', {'00':'Auto loop', '01':'Auto close', '10':'Loop open', '11':'Loop closed'}], ['14-15', 'Port D', {'00':'Auto loop', '01':'Auto close', '10':'Loop open', '11':'Loop closed'}]]
                self.registerSubGrid_Dict['0102'] = [['0-2', 'RX FIFO Size', {}], ['3', 'EBUS Low Jitter', {'0':'Normal jitter', '1':'Reduced jitter'}], ['6', 'EBUS remode link down signaling time', {'0':'Default', '1':'Reduced'}], ['9', 'Station alias', {'0':'Ignore', '1':'Available'}]]
                ## RUN/ERR LED Override (0x0138:0x0139)
                self.registerSubGrid_Dict['0138'] = [['0-3', 'RUN LED Code', {'0000':'Off', '0001':'Flash 1x', '0010':'Flash 2x', '0011':'Flash 3x', '0100':'Flash 4x', '0101':'Flash 5x', '0110':'Flash 6x', '0111':'Flash 7x', '1000':'Flash 8x', '1001':'Flash 9x', '1010':'Flash 10x', '1011':'Flash 11x', '1100':'Flash 12x', '1101':'Blinking', '1110':'Flickering', '1111':'On'}], ['4', 'Enable RUN LED Override', {'0':'Disabled', '1':'Enabled'}], ['8-11', 'ERR LED Code', {'0000':'Off', '0001':'Flash 1x', '0010':'Flash 2x', '0011':'Flash 3x', '0100':'Flash 4x', '0101':'Flash 5x', '0110':'Flash 6x', '0111':'Flash 7x', '1000':'Flash 8x', '1001':'Flash 9x', '1010':'Flash 10x', '1011':'Flash 11x', '1100':'Flash 12x', '1101':'Blinking', '1110':'Flickering', '1111':'On'}], ['12', 'Enable ERR LED Override', {'0':'Disabled', '1':'Enabled'}]]
                ## PDI Information (0x014e:0x014f)
                self.registerSubGrid_Dict['014e'] = [['0', 'PDI reg.func. acknowledge by write', {'0':'Disabled', '1':'Enabled'}], ['1', 'PDI configured', {'0':'FALSE', '1':'TRUE'}],['2', 'PDI Active', {'0':'FALSE', '1':'TRUE'}], ['3', 'PDI config. invalid', {'0':'FALSE', '1':'TRUE'}]]
                ## Register EEPROM Control/Status (0x0502:0x0503)
                self.registerSubGrid_Dict['0502'] = [['0', 'Write access', {'0':'FALSE', '1':'TRUE'}], ['5', 'EEPROM emulation', {'0':'Notmal operation', '1':'PDI emulates EEPROM'}], ['6', '8 byte access', {'0':'FALSE', '1':'TRUE'}], ['7', '2 byte address', {'0':'FALSE', '1':'TRUE'}], ['8', 'Read access', {'0':'FALSE', '1':'TRUE'}], ['9', 'Write access', {'0':'FALSE', '1':'TRUE'}], ['10', 'Reload access', {'0':'FALSE', '1':'TRUE'}], ['11', 'CRC error', {'0':'FALSE', '1':'TRUE'}], ['12', 'Load error', {'0':'FALSE', '1':'TRUE'}], ['13', 'Cmd error', {'0':'FALSE', '1':'TRUE'}], ['14', 'Write error', {'0':'FALSE', '1':'TRUE'}], ['15', 'Busy', {'0':'FALSE', '1':'TRUE'}]]
                ## DC Activation Status (0x0984)
                self.registerSubGrid_Dict['0984'] = [['0', 'SYNC0 pending', {'0':'FALSE', '1':'TRUE'}], ['1', 'SYNC1 pending', {'0':'FALSE', '1':'TRUE'}], ['2', 'Start Time', {'0':'within near future', '1':'out of near future'}]]
                ## Latch0/1 Status (0x09ae:0x09af)
                self.registerSubGrid_Dict['09ae'] = [['0', 'Event Latch 0 pos', {'0':'FALSE', '1':'TRUE'}], ['1', 'Event Latch 0 neg', {'0':'FALSE', '1':'TRUE'}], ['2', 'Latch 0 pin state', {'0':'FALSE', '1':'TRUE'}], ['8', 'Event Latch 1 pos', {'0':'FALSE', '1':'TRUE'}], ['9', 'Event Latch 1 neg', {'0':'FALSE', '1':'TRUE'}], ['10', 'Latch 1 pin state', {'0':'FALSE', '1':'TRUE'}]]
                
            ## The case that ESC Type is ET1100
            if self.controler.Reg_EscType == '0x11':
                self.registerDescription_Dict['0e00'] = "Power On"
                # Add new Sub Grid Label
                ## Part of Register ESC DL Control (0x0100:0x0103)
                self.registerSubGrid_Dict['0100'] = [['0', 'kill non EtherCAT frames', {}], ['1', 'Temporary loop control', {'0':'Permanent use', '1':'Use for about 1 sec.'}], ['8-9', 'Port A', {'00':'Auto loop', '01':'Auto close', '10':'Loop open', '11':'Loop closed'}], ['10-11', 'Port B', {'00':'Auto loop', '01':'Auto close', '10':'Loop open', '11':'Loop closed'}], ['12-13', 'Port C', {'00':'Auto loop', '01':'Auto close', '10':'Loop open', '11':'Loop closed'}], ['14-15', 'Port D', {'00':'Auto loop', '01':'Auto close', '10':'Loop open', '11':'Loop closed'}]]
                self.registerSubGrid_Dict['0102'] = [['0-2', 'RX FIFO Size', {}], ['3', 'EBUS Low Jitter', {'0':'Normal jitter', '1':'Reduced jitter'}], ['6', 'EBUS remode link down signaling time', {'0':'Default', '1':'Reduced'}], ['9', 'Station alias', {'0':'Ignore', '1':'Available'}]]
                ## Register EEPROM Control/Status (0x0502:0x0503)
                self.registerSubGrid_Dict['0502'] = [['0', 'Write access', {'0':'FALSE', '1':'TRUE'}], ['5', 'EEPROM emulation', {'0':'Notmal operation', '1':'PDI emulates EEPROM'}], ['6', '8 byte access', {'0':'FALSE', '1':'TRUE'}], ['7', '2 byte address', {'0':'FALSE', '1':'TRUE'}], ['8', 'Read access', {'0':'FALSE', '1':'TRUE'}], ['9', 'Write access', {'0':'FALSE', '1':'TRUE'}], ['10', 'Reload access', {'0':'FALSE', '1':'TRUE'}], ['11', 'CRC error', {'0':'FALSE', '1':'TRUE'}], ['12', 'Load error', {'0':'FALSE', '1':'TRUE'}], ['13', 'Cmd error', {'0':'FALSE', '1':'TRUE'}], ['14', 'Write error', {'0':'FALSE', '1':'TRUE'}], ['15', 'Busy', {'0':'FALSE', '1':'TRUE'}]]
                ## MII Management Control/Status (0x0510:0x0511)
                self.registerSubGrid_Dict['0510'] = [['0', 'Write access', {'0':'FALSE', '1':'TRUE'}], ['3-7', 'Phy address offset', {}], ['8', 'Read access', {'0':'FALSE', '1':'TRUE'}], ['9', 'Write access', {'0':'FALSE', '1':'TRUE'}], ['14', 'Write error', {'0':'FALSE', '1':'TRUE'}], ['15', 'Busy', {'0':'FALSE', '1':'TRUE'}]]
                ## Latch0/1 Status (0x09ae:0x09af)
                self.registerSubGrid_Dict['09ae'] = [['0', 'Event Latch 0 pos', {'0':'FALSE', '1':'TRUE'}], ['1', 'Event Latch 0 neg', {'0':'FALSE', '1':'TRUE'}], ['2', 'Latch 0 pin state', {'0':'FALSE', '1':'TRUE'}], ['8', 'Event Latch 1 pos', {'0':'FALSE', '1':'TRUE'}], ['9', 'Event Latch 1 neg', {'0':'FALSE', '1':'TRUE'}], ['10', 'Latch 1 pin state', {'0':'FALSE', '1':'TRUE'}]]
                ## Power On (0x0e00:0x0e01)
                self.registerSubGrid_Dict['0e00'] = [['0-1', 'Port mode', {'00':'Port 0 and 1', '01':'Port 0, 1 and 2', '10':'Port 0, 1 and 3', '11':'Port 0, 1, 2 and 3'}], ['2', 'Logical port 0', {'0':'EBUS', '1':'MII'}], ['3', 'Logical port 1', {'0':'EBUS', '1':'MII'}], ['4', 'Logical port 2', {'0':'EBUS', '1':'MII'}], ['5', 'Logical port 3', {'0':'EBUS', '1':'MII'}], ['6-7', 'CPU clock output', {'00':'Off - PDI[7] available', '01':'PDI[7]=25MHz', '10':'PDI[7]=20MHz', '11':'PDI[7]=10MHz'}], ['8-9', 'TX signal shift', {'00':'MII TX shifted 0', '01':'MII TX shifted 90', '10':'MII TX shifted 180', '11':'MII TX shifted 270'}], ['10', 'Clock 25 output', {'0':'Disable', '1':'Enable'}], ['11', 'Transparent mode MII', {'0':'Disable', '1':'Enable'}], ['12', 'Digital Ctrl/Status move', {'0':'PDI[39:32]', '1':'the highest available PDI Byte'}], ['13', 'Phy offset', {'0':'No offset', '1':'16 offset'}], ['14', 'Phy link polarity', {'0':'Active low', '1':'Active high'}]]
                ## Register AL Event Request and Mask
                self.registerSubGrid_Dict['0204'].append(['4', 'SM changed', {'0':'FALSE', '1':'TRUE'}])
                self.registerSubGrid_Dict['0220'].append(['4', 'SM changed', {'0':'FALSE', '1':'TRUE'}])
                
            ## The case that ESC Type is ET1200
            if self.controler.Reg_EscType == '0x12':
                self.registerDescription_Dict['0e00'] = "Power On"
                # Add new Sub Grid Label
                ## Part of Register ESC DL Control (0x0100:0x0103)
                self.registerSubGrid_Dict['0100'] = [['0', 'kill non EtherCAT frames', {}], ['1', 'Temporary loop control', {'0':'Permanent use', '1':'Use for about 1 sec.'}], ['8-9', 'Port A', {'00':'Auto loop', '01':'Auto close', '10':'Loop open', '11':'Loop closed'}], ['10-11', 'Port B', {'00':'Auto loop', '01':'Auto close', '10':'Loop open', '11':'Loop closed'}], ['12-13', 'Port C', {'00':'Auto loop', '01':'Auto close', '10':'Loop open', '11':'Loop closed'}], ['14-15', 'Port D', {'00':'Auto loop', '01':'Auto close', '10':'Loop open', '11':'Loop closed'}]]
                self.registerSubGrid_Dict['0102'] = [['0-2', 'RX FIFO Size', {}], ['3', 'EBUS Low Jitter', {'0':'Normal jitter', '1':'Reduced jitter'}], ['6', 'EBUS remode link down signaling time', {'0':'Default', '1':'Reduced'}], ['9', 'Station alias', {'0':'Ignore', '1':'Available'}]]
                ## Register EEPROM Control/Status (0x0502:0x0503)
                self.registerSubGrid_Dict['0502'] = [['0', 'Write access', {'0':'FALSE', '1':'TRUE'}], ['5', 'EEPROM emulation', {'0':'Notmal operation', '1':'PDI emulates EEPROM'}], ['6', '8 byte access', {'0':'FALSE', '1':'TRUE'}], ['7', '2 byte address', {'0':'FALSE', '1':'TRUE'}], ['8', 'Read access', {'0':'FALSE', '1':'TRUE'}], ['9', 'Write access', {'0':'FALSE', '1':'TRUE'}], ['10', 'Reload access', {'0':'FALSE', '1':'TRUE'}], ['11', 'CRC error', {'0':'FALSE', '1':'TRUE'}], ['12', 'Load error', {'0':'FALSE', '1':'TRUE'}], ['13', 'Cmd error', {'0':'FALSE', '1':'TRUE'}], ['14', 'Write error', {'0':'FALSE', '1':'TRUE'}], ['15', 'Busy', {'0':'FALSE', '1':'TRUE'}]]
                ## MII Management Control/Status (0x0510:0x0511)
                self.registerSubGrid_Dict['0510'] = [['0', 'Write access', {'0':'FALSE', '1':'TRUE'}], ['3-7', 'Phy address offset', {}], ['8', 'Read access', {'0':'FALSE', '1':'TRUE'}], ['9', 'Write access', {'0':'FALSE', '1':'TRUE'}], ['14', 'Write error', {'0':'FALSE', '1':'TRUE'}], ['15', 'Busy', {'0':'FALSE', '1':'TRUE'}]]
                ## Register AL Event Request and Mask
                self.registerSubGrid_Dict['0204'].append(['4', 'SM changed', {'0':'FALSE', '1':'TRUE'}])
                self.registerSubGrid_Dict['0220'].append(['4', 'SM changed', {'0':'FALSE', '1':'TRUE'}])
                ## Power On (0x0e00)
                self.registerSubGrid_Dict['0e00'] = [['0-1', 'Chip mode', {'00':'Port0:EBUS, Port1:EBUS, 18bit PDI', '10':'Port0:MII, Port1:EBUS, 8bit PDI', '11':'Port0:EBUS, Port1:MII, 8bit PDI'}], ['2-3', 'CPU clock output', {'00':'Off - PDI[7] available as PDI port', '01':'PDI[7]=25MHz', '10':'PDI[7]=20MHz', '11':'PDI[7]=10MHz'}], ['4-5', 'TX signal shift', {'00':'MII TX signals shifted by 0', '01':'MII TX signals shifted by 90', '10':'MII TX signals shifted by 180', '11':'MII TX signals shifted by 270'}], ['6', 'CLK25 Output Enable', {'0':'Disabled', '1':'Enabled'}], ['7', 'Phy address offset', {'0':'No offset', '1':'16 offset'}]]
                ## Register Receive Time Latch Mode (0x0936)
                self.registerSubGrid_Dict['0936'] = [['0', 'Receive Time Latch Mode', {'0':'Forwarding mode', '1':'Reverse mode'}]]
                
        # update FMMU label into register description dictionary
        if self.pre_fmmuNumber is not self.controler.Reg_FmmuNumber:
            for index in range(int(self.controler.Reg_FmmuNumber, 16)):
                self.registerDescription_Dict['06'+str(hex(index).split('x')[1])+'0'] = "F"+str(index)+" lstart L"
                self.registerDescription_Dict['06'+str(hex(index).split('x')[1])+'2'] = "F"+str(index)+" lstart H"
                self.registerDescription_Dict['06'+str(hex(index).split('x')[1])+'4'] = "F"+str(index)+" lLength"
                self.registerDescription_Dict['06'+str(hex(index).split('x')[1])+'6'] = "F"+str(index)+" lStartEndBit"
                self.registerDescription_Dict['06'+str(hex(index).split('x')[1])+'8'] = "F"+str(index)+" pStart"
                self.registerDescription_Dict['06'+str(hex(index).split('x')[1])+'a'] = "F"+str(index)+" pStartBit/Dir"
                self.registerDescription_Dict['06'+str(hex(index).split('x')[1])+'c'] = "F"+str(index)+" Enable"
                ## sub grid label
                self.registerSubGrid_Dict['06'+str(hex(index).split('x')[1])+'6'] = [['0-2', 'Logical start bit', {}], ['8-10', 'Logical end bit', {}]]
                self.registerSubGrid_Dict['06'+str(hex(index).split('x')[1])+'a'] = [['0-2', 'Physical start bit', {}], ['8', 'Read access', {'0':'Deactive', '1':'Active'}], ['9', 'Write access', {'0':'Deactive', '1':'Active'}]]
        
        # update SM label into register description dictionary
        if self.pre_smNumber is not self.controler.Reg_SmNumber:
            for index in range(int(self.controler.Reg_SmNumber, 16)):
                if index % 2 == 0: # index is even
                    self.registerDescription_Dict['08'+str(hex(index/2).split('x')[1])+'0'] = "SM"+str(index)+" Start"
                    self.registerDescription_Dict['08'+str(hex(index/2).split('x')[1])+'2'] = "SM"+str(index)+" Length"
                    self.registerDescription_Dict['08'+str(hex(index/2).split('x')[1])+'4'] = "SM"+str(index)+" Ctrl/Status"
                    self.registerDescription_Dict['08'+str(hex(index/2).split('x')[1])+'6'] = "SM"+str(index)+" Enable"
                    ## sub grid label
                    self.registerSubGrid_Dict['08'+str(hex(index/2).split('x')[1])+'4'] = [['0-1', 'OpMode', {'00':'3 buffer', '10':'1 buffer'}], ['2-3', 'Access', {'00':'Read', '01':'Write'}], ['4', 'ECAT IRQ', {'0':'FALSE', '1':'TRUE'}], ['5', 'PDI IRQ', {'0':'FALSE', '1':'TRUE'}], ['6', 'Watchdog trigger', {'0':'FALSE', '1':'TRUE'}], ['8', 'IRQ write', {'0':'FALSE', '1':'TRUE'}], ['9', 'IRQ read', {'0':'FALSE', '1':'TRUE'}], ['11', '1 buffer state', {'0':'Read', '1':'Write'}], ['12-13', '3 buffer state', {'00':'1 buffer', '01':'2 buffer', '10':'3 buffer', '11':'no buffer written'}]]
                    if self.controler.Reg_EscType == '0x11':
                        self.registerSubGrid_Dict['08'+str(hex(index/2).split('x')[1])+'6'] = [['0', 'Enable', {'0':'FALSE', '1':'TRUE'}], ['1', 'Repeat request', {'0':'FALSE', '1':'TRUE'}], ['6', 'Latch SyncMan Change ECAT', {'0':'FALSE', '1':'TRUE'}], ['7', 'Latch SyncMan Change PDI', {'0':'FALSE', '1':'TRUE'}], ['8', 'Deactivate', {'0':'FALSE', '1':'TRUE'}], ['9', 'Repeat acknowledge', {'0':'FALSE', '1':'TRUE'}]]
                    else:
                        self.registerSubGrid_Dict['08'+str(hex(index/2).split('x')[1])+'6'] = [['0', 'Enable', {'0':'FALSE', '1':'TRUE'}], ['1', 'Repeat request', {'0':'FALSE', '1':'TRUE'}], ['8', 'Deactivate', {'0':'FALSE', '1':'TRUE'}], ['9', 'Repeat acknowledge', {'0':'FALSE', '1':'TRUE'}]]
                    
                else: # index is odd
                    self.registerDescription_Dict['08'+str(hex(index/2).split('x')[1])+'8'] = "SM"+str(index)+" Start"
                    self.registerDescription_Dict['08'+str(hex(index/2).split('x')[1])+'a'] = "SM"+str(index)+" Length"
                    self.registerDescription_Dict['08'+str(hex(index/2).split('x')[1])+'c'] = "SM"+str(index)+" Ctrl/Status"
                    self.registerDescription_Dict['08'+str(hex(index/2).split('x')[1])+'e'] = "SM"+str(index)+" Enable"
                    ## sub grid label
                    self.registerSubGrid_Dict['08'+str(hex(index/2).split('x')[1])+'c'] = [['0-1', 'OpMode', {'00':'3 buffer', '10':'1 buffer'}], ['2-3', 'Access', {'00':'Read', '01':'Write'}], ['4', 'ECAT IRQ', {'0':'FALSE', '1':'TRUE'}], ['5', 'PDI IRQ', {'0':'FALSE', '1':'TRUE'}], ['6', 'Watchdog trigger', {'0':'FALSE', '1':'TRUE'}], ['8', 'IRQ write', {'0':'FALSE', '1':'TRUE'}], ['9', 'IRQ read', {'0':'FALSE', '1':'TRUE'}], ['11', '1 buffer state', {'0':'Read', '1':'Write'}], ['12-13', '3 buffer state', {'00':'1 buffer', '01':'2 buffer', '10':'3 buffer', '11':'no buffer written'}]]
                    if self.controler.Reg_EscType == '0x11':
                        self.registerSubGrid_Dict['08'+str(hex(index/2).split('x')[1])+'e'] = [['0', 'Enable', {'0':'FALSE', '1':'TRUE'}], ['1', 'Repeat request', {'0':'FALSE', '1':'TRUE'}], ['6', 'Latch SyncMan Change ECAT', {'0':'FALSE', '1':'TRUE'}], ['7', 'Latch SyncMan Change PDI', {'0':'FALSE', '1':'TRUE'}], ['8', 'Deactivate', {'0':'FALSE', '1':'TRUE'}], ['9', 'Repeat acknowledge', {'0':'FALSE', '1':'TRUE'}]]
                    else:
                        self.registerSubGrid_Dict['08'+str(hex(index/2).split('x')[1])+'e'] = [['0', 'Enable', {'0':'FALSE', '1':'TRUE'}], ['1', 'Repeat request', {'0':'FALSE', '1':'TRUE'}], ['8', 'Deactivate', {'0':'FALSE', '1':'TRUE'}], ['9', 'Repeat acknowledge', {'0':'FALSE', '1':'TRUE'}]]
        
                ## sub grid label
                self.registerSubGrid_Dict['0200'].append([str(4+index), 'SM '+str(index)+' IRQ', {'0':'FALSE', '1':'TRUE'}])
                self.registerSubGrid_Dict['0210'].append([str(4+index), 'SM '+str(index)+' IRQ', {'0':'FALSE', '1':'TRUE'}])
                self.registerSubGrid_Dict['0204'].append([str(8+index), 'SM '+str(index), {'0':'FALSE', '1':'TRUE'}])
                self.registerSubGrid_Dict['0220'].append([str(8+index), 'SM '+str(index), {'0':'FALSE', '1':'TRUE'}])
                
        # update PDI Type dependent subgrid label; PDI Configuration (0x0150:0x0153), PDI Error Code (0x030e)
        if self.pre_pdiType is not self.controler.Reg_PdiType:
            if self.controler.Reg_PdiType == '0x04':
                self.registerSubGrid_Dict['0150'] = [['0', 'OUTVALID polarity', {'0':'Active high', '1':'Active low'}], ['1', 'OUTVALID mode', {'0':'Output event signaling', '1':'WD_TRIG signaling'}], ['2', 'mode of direction', {'0':'Unidirectional', '1':'Bidirectional'}], ['3', 'Watchdog behavior', {'0':'immediately output reset', '1':'wait output reset'}], ['4-5', 'Input data is sampled at', {'00':'Start of Frame', '01':'Rising edge of LATCH_IN', '10':'DC SYNC0 event', '11':'DC SYNC1 event'}], ['6-7', 'Output Data is updated at', {'00':'End of Frame', '10':'DC SYNC0 event', '11':'DC SYNC1 event'}]]
                self.registerSubGrid_Dict['0152'] = [['0', 'Direction of I/O[1:0]', {'0':'Input', '1':'Output'}], ['1', 'Direction of I/O[3:2]', {'0':'Input', '1':'Output'}], ['2', 'Direction of I/O[5:4]', {'0':'Input', '1':'Output'}], ['3', 'Direction of I/O[7:6]', {'0':'Input', '1':'Output'}], ['4', 'Direction of I/O[9:8]', {'0':'Input', '1':'Output'}], ['5', 'Direction of I/O[11:10]', {'0':'Input', '1':'Output'}], ['6', 'Direction of I/O[13:12]', {'0':'Input', '1':'Output'}], ['7', 'Direction of I/O[15:14]', {'0':'Input', '1':'Output'}], ['8', 'Direction of I/O[17:16]', {'0':'Input', '1':'Output'}], ['9', 'Direction of I/O[19:18]', {'0':'Input', '1':'Output'}], ['10', 'Direction of I/O[21:20]', {'0':'Input', '1':'Output'}], ['11', 'Direction of I/O[23:22]', {'0':'Input', '1':'Output'}], ['12', 'Direction of I/O[25:24]', {'0':'Input', '1':'Output'}], ['13', 'Direction of I/O[27:26]', {'0':'Input', '1':'Output'}], ['14', 'Direction of I/O[29:28]', {'0':'Input', '1':'Output'}], ['15', 'Direction of I/O[31:30]', {'0':'Input', '1':'Output'}]]
            elif self.controler.Reg_PdiType == '0x05':
                self.registerSubGrid_Dict['0150'] = [['0-1', 'SPI mode', {}], ['2', 'SPI IRQ output driver', {'0':'Push-Pull', '1':'Open'}], ['3', 'SPI IRQ polarity', {'0':'Active low', '1':'Active high'}], ['4', 'SPI SEL polarity', {'0':'Active low', '1':'Active high'}], ['5', 'Data output sample mode', {'0':'Normal', '1':'Late'}], ['8', 'SYNC output', {'0':'Push pull', '1':'Open'}], ['9', 'SYNC0 polarity', {'0':'Active low', '1':'Active high'}], ['10', 'SYNC0 output', {'0':'Disable', '1':'Enable'}], ['11', 'SYNC0 to AL event', {'0':'Disable', '1':'Enable'}], ['12', 'SYNC1 output', {'0':'Push pull', '1':'Open'}], ['13', 'SYNC1 polarity', {'0':'Active low', '1':'Active high'}], ['14', 'SYNC1 output', {'0':'Disable', '1':'Enable'}], ['15', 'SYNC1 to AL event', {'0':'Disable', '1':'Enable'}]]
                self.registerSubGrid_Dict['030e'] = [['0-2', 'Number of SPI CLK cycles of whole access', {}], ['3', 'Busy violation during read access', {}], ['4', 'Read termination missing', {}], ['5', 'Access continued', {}], ['6-7', 'SPI command', {}]]
            elif self.controler.Reg_PdiType == '0x08' or self.controler.Reg_PdiType == '0x09':
                self.registerSubGrid_Dict['0150'] = [['0-1', 'BUSY output driver/polarity', {'00':'Push-Pull active low', '01':'Open Drain (Active low)', '10':'Push-Pull active high', '11':'Open Source (Active high)'}], ['2-3', 'IRQ output driver/polarity', {'00':'Push-Pull active low', '01':'Open Drain (Active low)', '10':'Push-Pull active high', '11':'Open Source (Active high)'}], ['4', 'BHE polarity', {'0':'Active low', '1':'Active high'}], ['7', 'RD polarity', {'0':'Active low', '1':'Active high'}], ['8', 'SYNC output', {'0':'Push pull', '1':'Open'}], ['9', 'SYNC0 polarity', {'0':'Active low', '1':'Active high'}], ['10', 'SYNC0 output', {'0':'Disable', '1':'Enable'}], ['11', 'SYNC0 to AL event', {'0':'Disable', '1':'Enable'}], ['12', 'SYNC1 output', {'0':'Push pull', '1':'Open'}], ['13', 'SYNC1 polarity', {'0':'Active low', '1':'Active high'}], ['14', 'SYNC1 output', {'0':'Disable', '1':'Enable'}], ['15', 'SYNC1 to AL event', {'0':'Disable', '1':'Enable'}]]
                self.registerSubGrid_Dict['0152'] = [['0', 'Read BUSY delay', {'0':'Normal read', '1':'Delayed read'}]]
                if self.controler.Reg_EscType == '0x04':
                    self.registerSubGrid_Dict['030e'] = [['0', 'Busy violation during read access', {}], ['1', 'Busy violation during write access'], ['2', 'Addressing error for a read access', {}], ['3', 'Addressing error for a write access', {}]]
            elif self.controler.Reg_PdiType == '0x0a' or self.controler.Reg_PdiType == '0x0b':
                self.registerSubGrid_Dict['0150'] = [['0-1', 'TA output driver/polarity', {'00':'Push-Pull active low', '01':'Open Drain (Active low)', '10':'Push-Pull active high', '11':'Open Source (Active high)'}], ['2-3', 'IRQ output driver/polarity', {'00':'Push-Pull active low', '01':'Open Drain (Active low)', '10':'Push-Pull active high', '11':'Open Source (Active high)'}], ['4', 'BHE polarity', {'0':'Active low', '1':'Active high'}], ['5', 'ADR(0) polarity', {'0':'Active low', '1':'Active high'}], ['6', 'Byte access mode', {'0':'BHE or Byte Select mode', '1':'Transfer Size mode'}], ['7', 'TS polarity', {'0':'Active low', '1':'Active high'}], ['8', 'SYNC output', {'0':'Push pull', '1':'Open'}], ['9', 'SYNC0 polarity', {'0':'Active low', '1':'Active high'}], ['10', 'SYNC0 output', {'0':'Disable', '1':'Enable'}], ['11', 'SYNC0 to AL event', {'0':'Disable', '1':'Enable'}], ['12', 'SYNC1 output', {'0':'Push pull', '1':'Open'}], ['13', 'SYNC1 polarity', {'0':'Active low', '1':'Active high'}], ['14', 'SYNC1 output', {'0':'Disable', '1':'Enable'}], ['15', 'SYNC1 to AL event', {'0':'Disable', '1':'Enable'}]]
                self.registerSubGrid_Dict['0152'] = [['8', 'Write data valid', {'0':'One clock cycle after CS', '1':'Together with CS'}], ['9', 'Read mode', {'0':'Use Byte Select', '1':'Always read 16 bit'}], ['10', 'CS mode', {'0':'Sample with riging edge', '1':'Sample with falling edge'}], ['11', 'TA/IRQ mode', {'0':'Update with riging edge', '1':'Update with falling edge'}]]
                if self.controler.Reg_EscType == '0x04':
                    self.registerSubGrid_Dict['030e'] = [['0', 'Busy violation during read access', {}], ['1', 'Busy violation during write access'], ['2', 'Addressing error for a read access', {}], ['3', 'Addressing error for a write access', {}]]
            elif self.controler.Reg_PdiType == '0x07':
                self.registerSubGrid_Dict['0150'] = [['0', 'Bridge port physical layer', {'0':'EBUS', '1':'MII'}], ['8', 'SYNC output', {'0':'Push pull', '1':'Open'}], ['9', 'SYNC0 polarity', {'0':'Active low', '1':'Active high'}], ['10', 'SYNC0 output', {'0':'Disable', '1':'Enable'}], ['11', 'SYNC0 to AL event', {'0':'Disable', '1':'Enable'}], ['12', 'SYNC1 output', {'0':'Push pull', '1':'Open'}], ['13', 'SYNC1 polarity', {'0':'Active low', '1':'Active high'}], ['14', 'SYNC1 output', {'0':'Disable', '1':'Enable'}], ['15', 'SYNC1 to AL event', {'0':'Disable', '1':'Enable'}]]
            elif self.controler.Reg_PdiType == '0xff':
                self.registerSubGrid_Dict['0150'] = [['0-6', 'Bus clock multiplication factor', {}], ['7', 'On-chip bus', {'0':'Altera Avalon', '1':'Xilinx OPB'}], ['8', 'SYNC output', {'0':'Push pull', '1':'Open'}], ['9', 'SYNC0 polarity', {'0':'Active low', '1':'Active high'}], ['10', 'SYNC0 output', {'0':'Disable', '1':'Enable'}], ['11', 'SYNC0 to AL event', {'0':'Disable', '1':'Enable'}], ['12', 'SYNC1 output', {'0':'Push pull', '1':'Open'}], ['13', 'SYNC1 polarity', {'0':'Active low', '1':'Active high'}], ['14', 'SYNC1 output', {'0':'Disable', '1':'Enable'}], ['15', 'SYNC1 to AL event', {'0':'Disable', '1':'Enable'}]] 
                self.registerSubGrid_Dict['0152'] = [['0-1', 'Data Bus Width', {'00':'4Byte', '01':'1Byte', '10':'2Byte'}]]

    
    def ParseData(self):
        rowData = []
        self.regMonitorData = []
        regWord = ""
        
        regData = self.controler.RegData.split() # split each register data
        
        # loop for register(0x0000:0x0fff)
        for address in range(0x1000):
        #for address in range(0x0010):
            #arrange 2Bytes of register data 
            regWord = regData[address].split('x')[1] + regWord
            if (address%2) == 1:
                # append address
                hexAddress = hex(address-1).split('x')[1].zfill(4)
                rowData.append(hexAddress)
                
                # append description
                if self.registerDescription_Dict.has_key(hexAddress):
                    rowData.append(self.registerDescription_Dict[hexAddress])
                else:
                    rowData.append("")
                    
                # append Decimal value
                rowData.append(str(int(regWord, 16)))
                
                # append Hex value
                rowData.append('0x'+regWord)
                
                # append ASCII value
                charData = ""
                if int(regWord[0:2], 16)>=32 and int(regWord[0:2], 16)<=126:
                    charData = charData + chr(int(regWord[0:2], 16))
                else:
                    charData = charData + "."
                if int(regWord[2:4], 16)>=32 and int(regWord[2:4], 16)<=126:
                    charData = charData + chr(int(regWord[2:4], 16))
                else:
                    charData = charData + "."
                rowData.append(charData)
                
                self.regMonitorData.append(rowData)
                regWord = "" # initialize regWord
                rowData = []
    
    
    def OnReloadButton(self, event):
        
        error, returnVal = self.controler.GetSlaveXML()
        line = returnVal.split("\n")
        # if error != 0, Beremiz do not connect 
        if error != 0  : 
            self.NotConnectedDialog()
        # if len(line) == 1, Beremiz is connect but slave is not connect on master
        elif len(line) == 1 : # if it's windows, it's not 1 but 2.
            self.NoSlaveDialog()
        # returnVal is not None, Request of the state   
        elif len(line) > 1 :
            self.LoadData()
            self.BasicSetData()
            self.ParseData()
            if self.compactFlag == True:
                self.ToggleCompactViewCheckbox(True)
            else: 
                self.register_notebook.win0.mainTablePanel.UpdateTable(self.win0_mainRow, self.mainCol, self.win0_range[0], self.win0_range[1], self.regMonitorData)
                self.register_notebook.win1.mainTablePanel.UpdateTable(self.win1_mainRow, self.mainCol, self.win1_range[0], self.win1_range[1], self.regMonitorData)
                self.register_notebook.win2.mainTablePanel.UpdateTable(self.win2_mainRow, self.mainCol, self.win2_range[0], self.win2_range[1], self.regMonitorData)
                self.register_notebook.win3.mainTablePanel.UpdateTable(self.win3_mainRow, self.mainCol, self.win3_range[0], self.win3_range[1], self.regMonitorData)

        else:
            pass

        
    def ToggleCompactViewCheckbox(self, event):     
        # Compact View Checkbox is True
        if (event == True) or (event.GetEventObject().GetValue() == True):
            self.compactFlag = True
            
            regCompactData = []
            win0_row = 0
            win1_row = 0
            win2_row = 0
            win3_row = 0
            
            for regRowData in self.regMonitorData:
                if regRowData[1] is not "":
                    # data structure for register compact view
                    regCompactData.append(regRowData)

                    # count for each register notebooks' row
                    # It compare with register's address.
                    if int('0x'+regRowData[0], 16)>=0 and int('0x'+regRowData[0], 16)<1024 :
                        win0_row += 1
                    elif int('0x'+regRowData[0], 16)>=1024 and int('0x'+regRowData[0], 16)<2048 :
                        win1_row += 1
                    elif int('0x'+regRowData[0], 16)>=2048 and int('0x'+regRowData[0], 16)<3072 :
                        win2_row += 1
                    elif int('0x'+regRowData[0], 16)>=3072 and int('0x'+regRowData[0], 16)<4096 :
                        win3_row += 1
                    else : 
                        pass

                else:
                    pass

            # Setting tables' rows and cols, range for compact view
            self.win0_mainRow = win0_row
            self.win1_mainRow = win1_row
            self.win2_mainRow = win2_row
            self.win3_mainRow = win3_row
            self.win0_range = [0, win0_row]
            self.win1_range = [win0_row, win0_row + win1_row]
            self.win2_range = [win0_row + win1_row, win0_row + win1_row + win2_row]
            self.win3_range = [win0_row + win1_row + win2_row, win0_row + win1_row + win2_row + win3_row]
            
            # Update table
            self.register_notebook.win0.mainTablePanel.UpdateTable(self.win0_mainRow, self.mainCol, self.win0_range[0], self.win0_range[1], regCompactData)
            self.register_notebook.win1.mainTablePanel.UpdateTable(self.win1_mainRow, self.mainCol, self.win1_range[0], self.win1_range[1], regCompactData)
            self.register_notebook.win2.mainTablePanel.UpdateTable(self.win2_mainRow, self.mainCol, self.win2_range[0], self.win2_range[1], regCompactData)
            self.register_notebook.win3.mainTablePanel.UpdateTable(self.win3_mainRow, self.mainCol, self.win3_range[0], self.win3_range[1], regCompactData)
            
        # Compact View Checkbox is False    
        else:
            self.compactFlag = False
            # Setting original rows, cols and range
            self.win0_mainRow = 512
            self.win1_mainRow = 512
            self.win2_mainRow = 512
            self.win3_mainRow = 512
            
            self.win0_range = [0, 512]
            self.win1_range = [512, 1024]
            self.win2_range = [1024, 1536]
            self.win3_range = [1536, 2048]
            
            # Update table 
            self.register_notebook.win0.mainTablePanel.UpdateTable(self.win0_mainRow, self.mainCol, self.win0_range[0], self.win0_range[1], self.regMonitorData)
            self.register_notebook.win1.mainTablePanel.UpdateTable(self.win1_mainRow, self.mainCol, self.win1_range[0], self.win1_range[1], self.regMonitorData)
            self.register_notebook.win2.mainTablePanel.UpdateTable(self.win2_mainRow, self.mainCol, self.win2_range[0], self.win2_range[1], self.regMonitorData)
            self.register_notebook.win3.mainTablePanel.UpdateTable(self.win3_mainRow, self.mainCol, self.win3_range[0], self.win3_range[1], self.regMonitorData)
            
    def NotConnectedDialog (self):
        dlg = wx.MessageDialog (self, 'It is not connected!!',
                             ' Warning...', wx.OK | wx.ICON_INFORMATION)
        dlg.ShowModal()
        dlg.Destroy()
        
    def NoSlaveDialog (self):
        dlg = wx.MessageDialog (self, 'There is no slave!!',
                             ' Warning...', wx.OK | wx.ICON_INFORMATION)
        dlg.ShowModal()
        dlg.Destroy()


class RegisterNotebook(wx.Notebook):
    def __init__(self, parent, controler):
        wx.Notebook.__init__(self, parent, id = -1)
        
        self.parent = parent
        self.controler = controler
        
        for index in range(4):
            if index == 0:
                self.win0 = RegisterNotebookPanel(self, parent.win0_mainRow, parent.mainCol, parent.win0_range[0], parent.win0_range[1])
                self.AddPage(self.win0, "0x0000 - 0x03FF")
            elif index == 1:
                self.win1 = RegisterNotebookPanel(self, parent.win1_mainRow, parent.mainCol, parent.win1_range[0], parent.win1_range[1])
                self.AddPage(self.win1, "0x0400 - 0x07FF")
            elif index == 2:
                self.win2 = RegisterNotebookPanel(self, parent.win2_mainRow, parent.mainCol, parent.win2_range[0], parent.win2_range[1])
                self.AddPage(self.win2, "0x0800 - 0x0BFF")
            elif index == 3:
                self.win3 = RegisterNotebookPanel(self, parent.win3_mainRow, parent.mainCol, parent.win3_range[0], parent.win3_range[1])
                self.AddPage(self.win3, "0x0C00 - 0x0FFF")
            else:
                pass
        
        self.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.OnPageChanged)
        self.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGING, self.OnPageChanging)


    def OnPageChanged(self, event):
        old = event.GetOldSelection()
        new = event.GetSelection()
        sel = self.GetSelection()
        event.Skip()

    def OnPageChanging(self, event):
        old = event.GetOldSelection()
        new = event.GetSelection()
        sel = self.GetSelection()
        event.Skip()


class RegisterNotebookPanel(wx.Panel):
    def __init__(self, parent, row, col, lowIndex, highIndex):
        wx.Panel.__init__(self, parent, -1)
        
        self.parent = parent
        subRow = 0
        subCol = 4
        
        sizer = wx.FlexGridSizer(cols=1, hgap=10, rows=2, vgap=30)
        
        self.mainTablePanel = RegisterMainTablePanel(self, row, col)
        self.subTablePanel = RegisterSubTablePanel(self, subRow, subCol)
        
        sizer.Add(self.mainTablePanel)
        sizer.Add(self.subTablePanel)
        
        self.SetSizer(sizer)


class RegisterMainTablePanel(wx.Panel):
    def __init__(self, parent, row, col):
        wx.Panel.__init__(self, parent, -1)
        
        self.parent = parent
        self.row = row
        self.col = col
        
        self.sizer = wx.FlexGridSizer(cols=1, hgap=0, rows=1, vgap=0)
        self.registerMainTable = RegisterMainTable(self, self.row, self.col)
        
        self.sizer.Add(self.registerMainTable)
        self.SetSizer(self.sizer)
        
        
    def UpdateTable(self, row, col, lowIndex, highIndex, data):
        self.registerMainTable.Destroy()
        self.registerMainTable = RegisterMainTable(self, row, col)
        self.sizer.Add(self.registerMainTable)
        self.SetSizer(self.sizer)
        self.registerMainTable.CreateGrid(row, col)
        self.registerMainTable.SetValue(self, data, lowIndex, highIndex)
        self.registerMainTable.Update()
    

class RegisterSubTablePanel(wx.Panel):
    def __init__(self, parent, row, col):
        wx.Panel.__init__(self, parent, -1)
        
        self.parent = parent
        self.row = row
        self.col = col
        
        self.sizer = wx.FlexGridSizer(cols=1, hgap=0, rows=1, vgap=0)
        self.registerSubTable = RegisterSubTable(self, self.row, self.col)
        self.registerSubTable.CreateGrid(row, col)
        self.registerSubTable.SetValue(self, [])
        self.sizer.Add(self.registerSubTable)
        self.SetSizer(self.sizer)


    def UpdateTable(self, row, col, data):
        self.registerSubTable.Destroy()
        self.registerSubTable = RegisterSubTable(self, row, col)
        self.sizer.Add(self.registerSubTable)
        self.SetSizer(self.sizer)
        self.registerSubTable.CreateGrid(row, col)
        self.registerSubTable.SetValue(self, data)
        self.registerSubTable.Update()

        
class RegisterMainTable(wx.grid.Grid):
    def __init__(self, parent, row, col):        
        self.prnt = parent
        self.data = {}
        self.row = row
        self.col = col
        
        wx.grid.Grid.__init__(self, parent, -1, size=(680,300), style=wx.EXPAND|wx.ALIGN_CENTRE_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL)        
        
        #event mapping
        self.Bind(gridlib.EVT_GRID_CELL_LEFT_CLICK, self.OnSelectCell)
        self.Bind(gridlib.EVT_GRID_SELECT_CELL, self.OnSelectCell)
        self.Bind(gridlib.EVT_GRID_CELL_LEFT_DCLICK, self.OnRegModifyDialog)
       
    def SetValue(self, parent, regMonitorData, lowIndex, highIndex):
        self.SetColLabelValue(0, "Description")
        self.SetColLabelValue(1, "Dec")
        self.SetColLabelValue(2, "Hex")
        self.SetColLabelValue(3, "Char")
        self.SetColSize(0, 200)
    
        row = col = 0
        for rowIndex in regMonitorData[lowIndex:highIndex]:
             
            col = 0
            self.SetRowLabelValue(row, rowIndex[0])
            
            for dataIndex in range(4):
                self.SetCellValue(row, col, rowIndex[dataIndex+1])
                self.SetCellAlignment(row, col, wx.ALIGN_CENTRE, wx.ALIGN_CENTER)
                self.SetReadOnly(row, col, True)  # by Chaerin 110119
                col = col + 1
            row = row + 1
    
    def OnSelectCell(self, event): # for description in sub grid
        subRow = 0
        subCol = 4
        
        address = self.GetRowLabelValue(event.GetRow())
        
        # data structure of table for register's detail description.
        regSubGridData = []
        
        # Check if this register's detail description is exist or not, and create data structure for the detail description table;sub grid
        if address in self.prnt.parent.parent.parent.registerSubGrid_Dict:
            
            for element in self.prnt.parent.parent.parent.registerSubGrid_Dict[address]:
                rowData =[]
                # append bits
                rowData.append(element[0])
                # append name
                rowData.append(element[1])
                # append value
                binData = bin(int(str(self.GetCellValue(event.GetRow(), 1)))).split('b')[1].zfill(16)
                #print binData
                value = (binData[8:16][::-1]+binData[0:8][::-1])[int(element[0].split('-')[0]):(int(element[0].split('-')[-1])+1)][::-1]
                #binValue = int(('0b'+str(value)), 2)
                rowData.append(str(int(('0b'+str(value)), 2)))
                # append Enum
                if value in element[2]:
                    rowData.append(element[2][value])
                else:
                    rowData.append('')
                # append rowData in regSubGridData
                regSubGridData.append(rowData)
                subRow = subRow + 1
                
        else:
            pass
        
        self.prnt.parent.subTablePanel.UpdateTable(subRow, subCol, regSubGridData)
        event.Skip()
    
    def OnRegModifyDialog(self, event): # for modifing register's value
        # user can enter a value in case that user double-clicked 'Dec' or 'Hex' value.
        if event.GetCol()==1 or event.GetCol()==2:
            dlg = wx.TextEntryDialog(self, "Enter hex(0xnnnn) or dec(n) value", "Register Modify Dialog", style = wx.OK|wx.CANCEL)
            
            # Setting value in initial dialog value
            startValue = self.GetCellValue(event.GetRow(), event.GetCol())
            dlg.SetValue(startValue)
        
            if dlg.ShowModal() == wx.ID_OK:
                try:
                    # It int(input) success, this input is dev or hex value. Otherwise, it's error, so it goes except.
                    int(dlg.GetValue(), 0)

                    # reg_write
                    # ex) ethercat reg_write -p 0 -t uint16 0x0000 0x0000
                    returnVal = self.prnt.parent.parent.controler.Reg_Write('0x'+self.GetRowLabelValue(event.GetRow()), dlg.GetValue())

                    if len(returnVal)==0:
                        # set dec
                        self.SetCellValue(event.GetRow(), 1, str(int(dlg.GetValue(), 0))) 
                        # set hex
                        hexData = '0x'+str(hex(int(dlg.GetValue(), 0)).split('x')[1].zfill(4))
                        self.SetCellValue(event.GetRow(), 2, hexData)
                        # set char
                        charData = ""
                        if int(hexData[2:4], 16)>=32 and int(hexData[2:4], 16)<=126:
                            charData = charData + chr(int(hexData[2:4], 16))
                        else:
                            charData = charData + "."
                        if int(hexData[4:6], 16)>=32 and int(hexData[4:6], 16)<=126:
                            charData = charData + chr(int(hexData[4:6], 16))
                        else:
                            charData = charData + "."
                        self.SetCellValue(event.GetRow(), 3, charData) 
                    
                    else:
                        self.PermissionErrorDialog()
                
                except ValueError:
                    self.InputErrorDialog()
        else:
            pass
        
        event.Skip()
    
    def PermissionErrorDialog(self):
        dlg = wx.MessageDialog(self, 'You can\'t modify it. This register is read-only or it\'s not connected.', 
                               ' Warning...', wx.OK|wx.ICON_INFORMATION)
        dlg.ShowModal()
        dlg.Destroy()
        
        
    def InputErrorDialog(self):
        dlg = wx.MessageDialog(self, 'You entered wrong value. You can enter dec or hex value only.', 
                               ' Warning...', wx.OK|wx.ICON_INFORMATION)
        dlg.ShowModal()
        dlg.Destroy()
    
    
class RegisterSubTable(wx.grid.Grid):
    def __init__(self, parent, row, col):        
        self.prnt = parent
        self.data = {}
        self.row = row
        self.col = col    
        
        wx.grid.Grid.__init__(self, parent, -1, size=(680,150), style=wx.EXPAND|wx.ALIGN_CENTRE_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL)        

    def SetValue(self, parent, data):
        self.SetColLabelValue(0, "Bits")
        self.SetColLabelValue(1, "Name")
        self.SetColLabelValue(2, "Value")
        self.SetColLabelValue(3, "Enum")
        self.SetColSize(1, 200)
        self.SetColSize(3, 200)
            
        row = col = 0
        for rowData in data: 
            col = 0
            
            for element in rowData:
                self.SetCellValue(row, col, element)
                self.SetCellAlignment(row, col, wx.ALIGN_CENTRE, wx.ALIGN_CENTER)
                self.SetReadOnly(row, col, True)  # by Chaerin 110119
                col = col + 1
            row = row + 1
                
#---------------------------------End ---------------------------------------------------------------

def GetProcessVariablesTableColnames():
    _ = lambda x : x
    return ["#", _("Name"), 
            _("Read from (nodeid, index, subindex)"), 
            _("Write to (nodeid, index, subindex)"),
            _("Description")]

class ProcessVariablesTable(CustomTable):
    
    def GetValue(self, row, col):
        if row < self.GetNumberRows():
            if col == 0:
                return row + 1
            colname = self.GetColLabelValue(col, False)
            if colname.startswith("Read from"):
                value = self.data[row].get("ReadFrom", "")
                if value == "":
                    return value
                return "%d, #x%0.4X, #x%0.2X" % value
            elif colname.startswith("Write to"):
                value = self.data[row].get("WriteTo", "")
                if value == "":
                    return value
                return "%d, #x%0.4X, #x%0.2X" % value
            return self.data[row].get(colname, "")
    
    def SetValue(self, row, col, value):
        if col < len(self.colnames):
            colname = self.GetColLabelValue(col, False)
            if colname.startswith("Read from"):
                self.data[row]["ReadFrom"] = value
            elif colname.startswith("Write to"):
                self.data[row]["WriteTo"] = value
            else:
                self.data[row][colname] = value
    
    def _updateColAttrs(self, grid):
        """
        wx.grid.Grid -> update the column attributes to add the
        appropriate renderer given the column name.

        Otherwise default to the default renderer.
        """
        for row in range(self.GetNumberRows()):
            for col in range(self.GetNumberCols()):
                editor = None
                renderer = None
                colname = self.GetColLabelValue(col, False)
                if colname in ["Name", "Description"]:
                    editor = wx.grid.GridCellTextEditor()
                    renderer = wx.grid.GridCellStringRenderer()
                    grid.SetReadOnly(row, col, False)
                else:
                    grid.SetReadOnly(row, col, True)
                
                grid.SetCellEditor(row, col, editor)
                grid.SetCellRenderer(row, col, renderer)
                
            self.ResizeRow(grid, row)

class ProcessVariableDropTarget(wx.TextDropTarget):
    
    def __init__(self, parent):
        wx.TextDropTarget.__init__(self)
        self.ParentWindow = parent
    
    def OnDropText(self, x, y, data):
        self.ParentWindow.Select()
        x, y = self.ParentWindow.ProcessVariablesGrid.CalcUnscrolledPosition(x, y)
        col = self.ParentWindow.ProcessVariablesGrid.XToCol(x)
        row = self.ParentWindow.ProcessVariablesGrid.YToRow(y - self.ParentWindow.ProcessVariablesGrid.GetColLabelSize())
        message = None
        try:
            values = eval(data)
        except:
            message = _("Invalid value \"%s\" for process variable")%data
            values = None
        if not isinstance(values, TupleType):
            message = _("Invalid value \"%s\" for process variable")%data
            values = None
        if values is not None and col != wx.NOT_FOUND and row != wx.NOT_FOUND and 2 <= col <= 3:
            location = None
            if values[1] == "location":
                result = LOCATION_MODEL.match(values[0])
                if result is not None:
                    location = map(int, result.group(1).split('.'))
                master_location = self.ParentWindow.GetMasterLocation()
                if (master_location == tuple(location[:len(master_location)]) and 
                    len(location) - len(master_location) == 3):
                    values = tuple(location[len(master_location):])
                    var_type = self.ParentWindow.Controler.GetSlaveVariableDataType(*values)
                    if col == 2:
                        other_values = self.ParentWindow.ProcessVariablesTable.GetValueByName(row, "WriteTo")
                    else:
                        other_values = self.ParentWindow.ProcessVariablesTable.GetValueByName(row, "ReadFrom")
                    if other_values != "":
                        other_type = self.ParentWindow.Controler.GetSlaveVariableDataType(*other_values)
                    else:
                        other_type = None
                    if other_type is None or var_type == other_type:
                        if col == 2:
                            self.ParentWindow.ProcessVariablesTable.SetValueByName(row, "ReadFrom", values)
                        else:
                            self.ParentWindow.ProcessVariablesTable.SetValueByName(row, "WriteTo", values)
                        self.ParentWindow.SaveProcessVariables()
                        self.ParentWindow.RefreshProcessVariables()
                    else:
                        message = _("'Read from' and 'Write to' variables types are not compatible")
                else:
                    message = _("Invalid value \"%s\" for process variable")%data
                    
        if message is not None:
            wx.CallAfter(self.ShowMessage, message)
    
    def ShowMessage(self, message):
        message = wx.MessageDialog(self.ParentWindow, message, _("Error"), wx.OK|wx.ICON_ERROR)
        message.ShowModal()
        message.Destroy()

def GetStartupCommandsTableColnames():
    _ = lambda x : x
    return [_("Position"), _("Index"), _("Subindex"), _("Value"), _("Description")]

class StartupCommandDropTarget(wx.TextDropTarget):
    
    def __init__(self, parent):
        wx.TextDropTarget.__init__(self)
        self.ParentWindow = parent
    
    def OnDropText(self, x, y, data):
        self.ParentWindow.Select()
        message = None
        try:
            values = eval(data)
        except:
            message = _("Invalid value \"%s\" for startup command")%data
            values = None
        if not isinstance(values, TupleType):
            message = _("Invalid value \"%s\" for startup command")%data
            values = None
        if values is not None:
            location = None
            if values[1] == "location":
                result = LOCATION_MODEL.match(values[0])
                if result is not None and len(values) > 5:
                    location = map(int, result.group(1).split('.'))
                    access = values[5]
            elif values[1] == "variable":
                location = values[0]
                access = values[2]
            if location is not None:
                master_location = self.ParentWindow.GetMasterLocation()
                if (master_location == tuple(location[:len(master_location)]) and 
                    len(location) - len(master_location) == 3):
                    if access in ["wo", "rw"]:
                        self.ParentWindow.AddStartupCommand(*location[len(master_location):])
                    else:
                        message = _("Entry can't be write through SDO")
                else:
                    message = _("Invalid value \"%s\" for startup command")%data
                    
        if message is not None:
            wx.CallAfter(self.ShowMessage, message)
    
    def ShowMessage(self, message):
        message = wx.MessageDialog(self.ParentWindow, message, _("Error"), wx.OK|wx.ICON_ERROR)
        message.ShowModal()
        message.Destroy()

class StartupCommandsTable(CustomTable):

    """
    A custom wx.grid.Grid Table using user supplied data
    """
    def __init__(self, parent, data, colnames):
        # The base class must be initialized *first*
        CustomTable.__init__(self, parent, data, colnames)
        self.old_value = None

    def GetValue(self, row, col):
        if row < self.GetNumberRows():
            colname = self.GetColLabelValue(col, False)
            value = self.data[row].get(colname, "")
            if colname == "Index":
                return "#x%0.4X" % value
            elif colname == "Subindex":
                return "#x%0.2X" % value
            return value
    
    def SetValue(self, row, col, value):
        if col < len(self.colnames):
            colname = self.GetColLabelValue(col, False)
            if colname in ["Index", "Subindex"]:
                if colname == "Index":
                    result = ETHERCAT_INDEX_MODEL.match(value)
                else:
                    result = ETHERCAT_SUBINDEX_MODEL.match(value)
                if result is None:
                    return
                value = int(result.group(1), 16)
            elif colname == "Value":
                value = int(value)
            elif colname == "Position":
                self.old_value = self.data[row][colname]
                value = int(value)
            self.data[row][colname] = value
    
    def GetOldValue(self):
        return self.old_value
    
    def _updateColAttrs(self, grid):
        """
        wx.grid.Grid -> update the column attributes to add the
        appropriate renderer given the column name.

        Otherwise default to the default renderer.
        """
        for row in range(self.GetNumberRows()):
            for col in range(self.GetNumberCols()):
                editor = None
                renderer = None
                colname = self.GetColLabelValue(col, False)
                if colname in ["Position", "Value"]:
                    editor = wx.grid.GridCellNumberEditor()
                    renderer = wx.grid.GridCellNumberRenderer()
                else:
                    editor = wx.grid.GridCellTextEditor()
                    renderer = wx.grid.GridCellStringRenderer()
                
                grid.SetCellEditor(row, col, editor)
                grid.SetCellRenderer(row, col, renderer)
                grid.SetReadOnly(row, col, False)
                
            self.ResizeRow(grid, row)
    
    def GetCommandIndex(self, position, command_idx):
        for row, command in enumerate(self.data):
            if command["Position"] == position and command["command_idx"] == command_idx:
                return row
        return None

class MasterNodesVariablesSizer(NodeVariablesSizer):
    
    def __init__(self, parent, controler):
        NodeVariablesSizer.__init__(self, parent, controler, True)
        
        self.CurrentNodesFilter = {}
    
    def SetCurrentNodesFilter(self, nodes_filter):
        self.CurrentNodesFilter = nodes_filter
        
    def RefreshView(self):
        if self.CurrentNodesFilter is not None:
            args = self.CurrentNodesFilter.copy()
            args["limits"] = self.CurrentFilter
            entries = self.Controler.GetNodesVariables(**args)
            self.RefreshVariablesGrid(entries)

NODE_POSITION_FILTER_FORMAT = _("Node Position: %d")

class MasterEditor(ConfTreeNodeEditor):
    
    CONFNODEEDITOR_TABS = [
        (_("Network"), "_create_EthercatMasterEditor"),
        (_("Master State"), "_create_MasterStateEditor")
        ]
    
    def _create_MasterStateEditor(self, prnt):
        self.MasterStateEditor = wx.ScrolledWindow(prnt, style=wx.TAB_TRAVERSAL|wx.HSCROLL|wx.VSCROLL)
        self.MasterStateEditor.Bind(wx.EVT_SIZE, self.OnResize)
        
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        inner_main_sizer = wx.FlexGridSizer(cols=1, hgap=10, rows=2, vgap=10)
        inner_tophalf_sizer = wx.FlexGridSizer(cols=2, hgap=10, rows=1, vgap=10)
        inner_bottomhalf_sizer = wx.FlexGridSizer(cols=2, hgap=10, rows=1, vgap=10)
        
        self.UpdateButton = wx.Button(self.MasterStateEditor, label=_('Update'))
        self.UpdateButton.Bind(wx.EVT_BUTTON, self.OnButtonClick)
        
        self.MasterStateBox = wx.StaticBox(self.MasterStateEditor, label=_('EtherCAT Master State'))
        self.MasterStateSizer = wx.StaticBoxSizer(self.MasterStateBox)
        self.InnerMasterStateSizer = wx.FlexGridSizer(cols=2, hgap=10, rows=3, vgap=10)
        
        self.DeviceInfoBox = wx.StaticBox(self.MasterStateEditor, label=_('Ethernet Network Card Information'))
        self.DeviceInfoSizer = wx.StaticBoxSizer(self.DeviceInfoBox)
        self.InnerDeviceInfoSizer = wx.FlexGridSizer(cols=4, hgap=10, rows=3, vgap=10)
        
        self.FrameInfoBox = wx.StaticBox(self.MasterStateEditor, label=_('Network Frame Information'))
        self.FrameInfoSizer = wx.StaticBoxSizer(self.FrameInfoBox)
        self.InnerFrameInfoSizer = wx.FlexGridSizer(cols=4, hgap=10, rows=5, vgap=10)
        
        # ----------------------- Master State -----------------------------------------------------------
        self.PhaseLabel = wx.StaticText(self.MasterStateEditor, label=_('Phase:'))      
        self.Phase = wx.TextCtrl(self.MasterStateEditor)
        self.ActiveLabel = wx.StaticText(self.MasterStateEditor, label=_('Active:'))      
        self.Active = wx.TextCtrl(self.MasterStateEditor)
        self.SlaveCountLabel = wx.StaticText(self.MasterStateEditor, label=_('Slave Count:'))      
        self.SlaveCount = wx.TextCtrl(self.MasterStateEditor)
        
        self.InnerMasterStateSizer.AddMany([self.PhaseLabel, self.Phase, self.ActiveLabel, self.Active,
                                           self.SlaveCountLabel, self.SlaveCount])
        self.MasterStateSizer.AddSizer(self.InnerMasterStateSizer)
        
        # ----------------------- Ethernet Network Card Information --------------------------------------- 
        self.MacAddressLabel = wx.StaticText(self.MasterStateEditor, label=_('MAC address:'))      
        self.MacAddress = wx.TextCtrl(self.MasterStateEditor, size=wx.Size(130, 24))
        self.LinkStateLabel = wx.StaticText(self.MasterStateEditor, label=_('Link State:'))      
        self.LinkState = wx.TextCtrl(self.MasterStateEditor, size=wx.Size(130, 24))
        self.TxFramesLabel = wx.StaticText(self.MasterStateEditor, label=_('Tx Frames:'))      
        self.TxFrames = wx.TextCtrl(self.MasterStateEditor, size=wx.Size(130, 24))
        self.RxFramesLabel = wx.StaticText(self.MasterStateEditor, label=_('Rx Frames:'))      
        self.RxFrames = wx.TextCtrl(self.MasterStateEditor, size=wx.Size(130, 24))
        self.LostFramesLabel = wx.StaticText(self.MasterStateEditor, label=_('Lost Frames:'))      
        self.LostFrames = wx.TextCtrl(self.MasterStateEditor, size=wx.Size(130, 24))
     
        self.InnerDeviceInfoSizer.AddMany([self.MacAddressLabel, self.MacAddress, self.LinkStateLabel, self.LinkState,
                                           self.TxFramesLabel, self.TxFrames, self.RxFramesLabel, self.RxFrames,
                                           self.LostFramesLabel, self.LostFrames])
        self.DeviceInfoSizer.AddSizer(self.InnerDeviceInfoSizer)      
          
        # ----------------------- Network Frame Information -----------------------------------------------
        #self.TxByteLabel = wx.StaticText(self.MasterStateEditor, label=_('Tx Bytes:'))      
        #self.TxByte = wx.TextCtrl(self.MasterStateEditor)
        #self.TxErrorLabel = wx.StaticText(self.MasterStateEditor, label=_('Tx Error:'))      
        #self.TxError = wx.TextCtrl(self.MasterStateEditor)
        self.TxFrameRateLabel = wx.StaticText(self.MasterStateEditor, label=_('Tx Frame Rate [1/s]:'))      
        self.TxFrameRate1 = wx.TextCtrl(self.MasterStateEditor)
        self.TxFrameRate2 = wx.TextCtrl(self.MasterStateEditor)
        self.TxFrameRate3 = wx.TextCtrl(self.MasterStateEditor)    
        self.TxRateLabel = wx.StaticText(self.MasterStateEditor, label=_('Tx Rate [kByte/s]:'))      
        self.TxRate1 = wx.TextCtrl(self.MasterStateEditor)
        self.TxRate2 = wx.TextCtrl(self.MasterStateEditor)
        self.TxRate3 = wx.TextCtrl(self.MasterStateEditor)
        self.LossRateLabel = wx.StaticText(self.MasterStateEditor, label=_('Loss Rate [1/s]:'))      
        self.LossRate1 = wx.TextCtrl(self.MasterStateEditor)
        self.LossRate2 = wx.TextCtrl(self.MasterStateEditor)
        self.LossRate3 = wx.TextCtrl(self.MasterStateEditor) 
        self.FrameLossLabel = wx.StaticText(self.MasterStateEditor, label=_('Frame loss [%]:'))      
        self.FrameLoss1 = wx.TextCtrl(self.MasterStateEditor)
        self.FrameLoss2 = wx.TextCtrl(self.MasterStateEditor)
        self.FrameLoss3 = wx.TextCtrl(self.MasterStateEditor) 
        
        self.InnerFrameInfoSizer.AddMany([#self.TxByteLabel, self.TxByte, self.TxErrorLabel, self.TxError,
                                          self.TxFrameRateLabel, self.TxFrameRate1, self.TxFrameRate2, self.TxFrameRate3,
                                          self.TxRateLabel, self.TxRate1, self.TxRate2, self.TxRate3,
                                          self.LossRateLabel, self.LossRate1, self.LossRate2, self.LossRate3,
                                          self.FrameLossLabel, self.FrameLoss1, self.FrameLoss2, self.FrameLoss3])
        self.FrameInfoSizer.AddSizer(self.InnerFrameInfoSizer)      
        
        # --------------------------------- Main Sizer ----------------------------------------------------
        
        inner_tophalf_sizer.AddSizer(self.MasterStateSizer)
        inner_tophalf_sizer.AddSizer(self.DeviceInfoSizer)
        
        inner_bottomhalf_sizer.AddSizer(self.FrameInfoSizer)
        
        inner_main_sizer.AddSizer(inner_tophalf_sizer)
        inner_main_sizer.AddSizer(inner_bottomhalf_sizer)
      
        main_sizer.AddSizer(self.UpdateButton)
        main_sizer.AddSizer(inner_main_sizer)
 
        self.MasterStateEditor.SetSizer(main_sizer)
        return self.MasterStateEditor
    
    def _create_EthercatMasterEditor(self, prnt):
        self.EthercatMasterEditor = wx.ScrolledWindow(prnt, 
            style=wx.TAB_TRAVERSAL|wx.HSCROLL|wx.VSCROLL)
        self.EthercatMasterEditor.Bind(wx.EVT_SIZE, self.OnResize)
        
        self.EthercatMasterEditorSizer = wx.BoxSizer(wx.VERTICAL)
        
        self.NodesFilter = wx.ComboBox(self.EthercatMasterEditor,
            style=wx.TE_PROCESS_ENTER)
        self.Bind(wx.EVT_COMBOBOX, self.OnNodesFilterChanged, self.NodesFilter)
        self.Bind(wx.EVT_TEXT_ENTER, self.OnNodesFilterChanged, self.NodesFilter)
        self.NodesFilter.Bind(wx.EVT_CHAR, self.OnNodesFilterKeyDown)
        
        process_variables_header = wx.BoxSizer(wx.HORIZONTAL)
        
        process_variables_label = wx.StaticText(self.EthercatMasterEditor,
              label=_("Process variables mapped between nodes:"))
        process_variables_header.AddWindow(process_variables_label, 1,
              flag=wx.ALIGN_CENTER_VERTICAL)
        
        for name, bitmap, help in [
                ("AddVariableButton", "add_element", _("Add process variable")),
                ("DeleteVariableButton", "remove_element", _("Remove process variable")),
                ("UpVariableButton", "up", _("Move process variable up")),
                ("DownVariableButton", "down", _("Move process variable down"))]:
            button = wx.lib.buttons.GenBitmapButton(self.EthercatMasterEditor, bitmap=GetBitmap(bitmap), 
                  size=wx.Size(28, 28), style=wx.NO_BORDER)
            button.SetToolTipString(help)
            setattr(self, name, button)
            process_variables_header.AddWindow(button, border=5, flag=wx.LEFT)
        
        self.ProcessVariablesGrid = CustomGrid(self.EthercatMasterEditor, style=wx.VSCROLL)
        self.ProcessVariablesGrid.SetMinSize(wx.Size(0, 150))
        self.ProcessVariablesGrid.SetDropTarget(ProcessVariableDropTarget(self))
        self.ProcessVariablesGrid.Bind(wx.grid.EVT_GRID_CELL_CHANGE, 
              self.OnProcessVariablesGridCellChange)
        self.ProcessVariablesGrid.Bind(wx.grid.EVT_GRID_CELL_LEFT_CLICK, 
              self.OnProcessVariablesGridCellLeftClick)
        self.ProcessVariablesGrid.Bind(wx.EVT_KEY_DOWN, self.OnProcessVariablesGridKeyDown)
        
        startup_commands_header = wx.BoxSizer(wx.HORIZONTAL)
        
        startup_commands_label = wx.StaticText(self.EthercatMasterEditor,
              label=_("Startup service variables assignments:"))
        startup_commands_header.AddWindow(startup_commands_label, 1,
              flag=wx.ALIGN_CENTER_VERTICAL)
        
        for name, bitmap, help in [
                ("AddCommandButton", "add_element", _("Add startup service variable")),
                ("DeleteCommandButton", "remove_element", _("Remove startup service variable"))]:
            button = wx.lib.buttons.GenBitmapButton(self.EthercatMasterEditor, bitmap=GetBitmap(bitmap), 
                  size=wx.Size(28, 28), style=wx.NO_BORDER)
            button.SetToolTipString(help)
            setattr(self, name, button)
            startup_commands_header.AddWindow(button, border=5, flag=wx.LEFT)
        
        self.StartupCommandsGrid = CustomGrid(self.EthercatMasterEditor, style=wx.VSCROLL)
        self.StartupCommandsGrid.SetDropTarget(StartupCommandDropTarget(self))
        self.StartupCommandsGrid.SetMinSize(wx.Size(0, 150))
        self.StartupCommandsGrid.Bind(wx.grid.EVT_GRID_CELL_CHANGE, 
              self.OnStartupCommandsGridCellChange)
        self.StartupCommandsGrid.Bind(wx.grid.EVT_GRID_EDITOR_SHOWN, 
              self.OnStartupCommandsGridEditorShow)
        
        self.NodesVariables = MasterNodesVariablesSizer(self.EthercatMasterEditor, self.Controler)
        
        main_staticbox = wx.StaticBox(self.EthercatMasterEditor, label=_("Node filter:"))
        staticbox_sizer = wx.StaticBoxSizer(main_staticbox, wx.VERTICAL)
        self.EthercatMasterEditorSizer.AddSizer(staticbox_sizer, 0, border=10, flag=wx.GROW|wx.ALL)
        
        main_staticbox_sizer = wx.FlexGridSizer(cols=1, hgap=0, rows=6, vgap=0)
        main_staticbox_sizer.AddGrowableCol(0)
        main_staticbox_sizer.AddGrowableRow(2)
        main_staticbox_sizer.AddGrowableRow(4)
        main_staticbox_sizer.AddGrowableRow(5)
        staticbox_sizer.AddSizer(main_staticbox_sizer, 1, flag=wx.GROW)
        main_staticbox_sizer.AddWindow(self.NodesFilter, border=5, flag=wx.GROW|wx.ALL)
        main_staticbox_sizer.AddSizer(process_variables_header, border=5, 
              flag=wx.GROW|wx.LEFT|wx.RIGHT|wx.BOTTOM)
        main_staticbox_sizer.AddWindow(self.ProcessVariablesGrid, 1, 
              border=5, flag=wx.GROW|wx.LEFT|wx.RIGHT|wx.BOTTOM)
        main_staticbox_sizer.AddSizer(startup_commands_header, 
              border=5, flag=wx.GROW|wx.LEFT|wx.RIGHT|wx.BOTTOM)
        main_staticbox_sizer.AddWindow(self.StartupCommandsGrid, 1, 
              border=5, flag=wx.GROW|wx.LEFT|wx.RIGHT|wx.BOTTOM)
        
        second_staticbox = wx.StaticBox(self.EthercatMasterEditor, label=_("Nodes variables filter:"))
        second_staticbox_sizer = wx.StaticBoxSizer(second_staticbox, wx.VERTICAL)
        second_staticbox_sizer.AddSizer(self.NodesVariables, 1, border=5, flag=wx.GROW|wx.ALL)
        
        main_staticbox_sizer.AddSizer(second_staticbox_sizer, 1, 
            border=5, flag=wx.GROW|wx.LEFT|wx.RIGHT|wx.BOTTOM)
        
        self.EthercatMasterEditor.SetSizer(self.EthercatMasterEditorSizer)
        
        return self.EthercatMasterEditor

    def __init__(self, parent, controler, window):
        ConfTreeNodeEditor.__init__(self, parent, controler, window)
        
        # ------------------------------------------------------------------
        self.Controler = controler
        # ------------------------------------------------------------------
        
        self.ProcessVariables = []
        self.CellShown = None
        self.NodesFilterFirstCharacter = True
        
        self.ProcessVariablesDefaultValue = {"Name": "", "ReadFrom": "", "WriteTo": "", "Description": ""}
        self.ProcessVariablesTable = ProcessVariablesTable(self, [], GetProcessVariablesTableColnames())
        self.ProcessVariablesColSizes = [40, 100, 150, 150, 200]
        self.ProcessVariablesColAlignements = [wx.ALIGN_CENTER, wx.ALIGN_LEFT, wx.ALIGN_LEFT, wx.ALIGN_LEFT, wx.ALIGN_LEFT]
        
        self.ProcessVariablesGrid.SetTable(self.ProcessVariablesTable)
        self.ProcessVariablesGrid.SetButtons({"Add": self.AddVariableButton,
                                              "Delete": self.DeleteVariableButton,
                                              "Up": self.UpVariableButton,
                                              "Down": self.DownVariableButton})
        
        def _AddVariablesElement(new_row):
            self.ProcessVariablesTable.InsertRow(new_row, self.ProcessVariablesDefaultValue.copy())
            self.SaveProcessVariables()
            self.ProcessVariablesTable.ResetView(self.ProcessVariablesGrid)
            return new_row
        setattr(self.ProcessVariablesGrid, "_AddRow", _AddVariablesElement)
        
        def _DeleteVariablesElement(row):
            self.ProcessVariablesTable.RemoveRow(row)
            self.SaveProcessVariables()
            self.ProcessVariablesTable.ResetView(self.ProcessVariablesGrid)
        setattr(self.ProcessVariablesGrid, "_DeleteRow", _DeleteVariablesElement)
            
        def _MoveVariablesElement(row, move):
            new_row = self.ProcessVariablesTable.MoveRow(row, move)
            if new_row != row:
                self.SaveProcessVariables()
                self.ProcessVariablesTable.ResetView(self.ProcessVariablesGrid)
            return new_row
        setattr(self.ProcessVariablesGrid, "_MoveRow", _MoveVariablesElement)
        
        _refresh_buttons = getattr(self.ProcessVariablesGrid, "RefreshButtons")
        def _RefreshButtons():
            if self.NodesFilter.GetSelection() == 0:
                _refresh_buttons()
            else:
                self.AddVariableButton.Enable(False)
                self.DeleteVariableButton.Enable(False)
                self.UpVariableButton.Enable(False)
                self.DownVariableButton.Enable(False)
        setattr(self.ProcessVariablesGrid, "RefreshButtons", _RefreshButtons)
        
        self.ProcessVariablesGrid.SetRowLabelSize(0)
        for col in range(self.ProcessVariablesTable.GetNumberCols()):
            attr = wx.grid.GridCellAttr()
            attr.SetAlignment(self.ProcessVariablesColAlignements[col], wx.ALIGN_CENTRE)
            self.ProcessVariablesGrid.SetColAttr(col, attr)
            self.ProcessVariablesGrid.SetColMinimalWidth(col, self.ProcessVariablesColSizes[col])
            self.ProcessVariablesGrid.AutoSizeColumn(col, False)
        self.ProcessVariablesGrid.RefreshButtons()
    
        self.StartupCommandsDefaultValue = {"Position": 0, "Index": 0, "Subindex": 0, "Value": 0, "Description": ""}
        self.StartupCommandsTable = StartupCommandsTable(self, [], GetStartupCommandsTableColnames())
        self.StartupCommandsColSizes = [100, 100, 50, 100, 200]
        self.StartupCommandsColAlignements = [wx.ALIGN_CENTER, wx.ALIGN_RIGHT, wx.ALIGN_RIGHT, wx.ALIGN_RIGHT, wx.ALIGN_LEFT]
        
        self.StartupCommandsGrid.SetTable(self.StartupCommandsTable)
        self.StartupCommandsGrid.SetButtons({"Add": self.AddCommandButton,
                                             "Delete": self.DeleteCommandButton})
        
        def _AddCommandsElement(new_row):
            command = self.StartupCommandsDefaultValue.copy()
            command_idx = self.Controler.AppendStartupCommand(command)
            self.RefreshStartupCommands()
            self.RefreshBuffer()
            return self.StartupCommandsTable.GetCommandIndex(command["Position"], command_idx)
        setattr(self.StartupCommandsGrid, "_AddRow", _AddCommandsElement)
        
        def _DeleteCommandsElement(row):
            command = self.StartupCommandsTable.GetRow(row)
            self.Controler.RemoveStartupCommand(command["Position"], command["command_idx"])
            self.RefreshStartupCommands()
            self.RefreshBuffer()
        setattr(self.StartupCommandsGrid, "_DeleteRow", _DeleteCommandsElement)
        
        self.StartupCommandsGrid.SetRowLabelSize(0)
        for col in range(self.StartupCommandsTable.GetNumberCols()):
            attr = wx.grid.GridCellAttr()
            attr.SetAlignment(self.StartupCommandsColAlignements[col], wx.ALIGN_CENTRE)
            self.StartupCommandsGrid.SetColAttr(col, attr)
            self.StartupCommandsGrid.SetColMinimalWidth(col, self.StartupCommandsColSizes[col])
            self.StartupCommandsGrid.AutoSizeColumn(col, False)
        self.StartupCommandsGrid.RefreshButtons()
    
    def RefreshBuffer(self):
        self.ParentWindow.RefreshTitle()
        self.ParentWindow.RefreshFileMenu()
        self.ParentWindow.RefreshEditMenu()
        self.ParentWindow.RefreshPageTitles()
    
    def GetBufferState(self):
        return self.Controler.GetBufferState()
    
    def Undo(self):
        self.Controler.LoadPrevious()
        self.RefreshView()
            
    def Redo(self):
        self.Controler.LoadNext()
        self.RefreshView()
    
    def RefreshView(self):
        ConfTreeNodeEditor.RefreshView(self)
        
        self.RefreshNodesFilter()
        self.RefreshProcessVariables()
        self.RefreshStartupCommands()
        self.NodesVariables.RefreshView()
    
    def RefreshNodesFilter(self):
        value = self.NodesFilter.GetValue()
        self.NodesFilter.Clear()
        self.NodesFilter.Append(_("All"))
        self.NodesFilterValues = [{}]
        for vendor_id, vendor_name in self.Controler.GetLibraryVendors():
            self.NodesFilter.Append(_("%s's nodes") % vendor_name)
            self.NodesFilterValues.append({"vendor": vendor_id})
        self.NodesFilter.Append(_("CIA402 nodes"))
        self.NodesFilterValues.append({"slave_profile": 402})
        if value in self.NodesFilter.GetStrings():
            self.NodesFilter.SetStringSelection(value)
        else:
            try:
                int(value)
                self.NodesFilter.SetValue(value)
            except:
                self.NodesFilter.SetSelection(0)
        self.RefreshCurrentNodesFilter()
    
    def RefreshCurrentNodesFilter(self):
        filter = self.NodesFilter.GetSelection()
        if filter != -1:
            self.CurrentNodesFilter = self.NodesFilterValues[filter]
        else:
            try:
                value = self.NodesFilter.GetValue()
                if value == "":
                    self.CurrentNodesFilter = self.NodesFilterValues[0]
                    self.NodesFilter.SetSelection(0)
                else:
                    position = int(self.NodesFilter.GetValue())
                    self.CurrentNodesFilter = {"slave_pos": position}
                    self.NodesFilter.SetValue(NODE_POSITION_FILTER_FORMAT % position)
            except:
                if self.CurrentNodesFilter in self.NodesFilterValues:
                    self.NodesFilter.SetSelection(self.NodesFilterValues.index(self.CurrentNodesFilter))
                else:
                    self.NodesFilter.SetValue(NODE_POSITION_FILTER_FORMAT % self.CurrentNodesFilter["slave_pos"])
        self.NodesFilterFirstCharacter = True
        self.NodesVariables.SetCurrentNodesFilter(self.CurrentNodesFilter)
    
    def RefreshProcessVariables(self):
        if self.CurrentNodesFilter is not None:
            self.ProcessVariables = self.Controler.GetProcessVariables()
            slaves = self.Controler.GetSlaves(**self.CurrentNodesFilter)
            data = []
            for variable in self.ProcessVariables:
                if (variable["ReadFrom"] == "" or variable["ReadFrom"][0] in slaves or
                    variable["WriteTo"] == "" or variable["WriteTo"][0] in slaves):
                    data.append(variable)
            self.ProcessVariablesTable.SetData(data)
            self.ProcessVariablesTable.ResetView(self.ProcessVariablesGrid)
            self.ProcessVariablesGrid.RefreshButtons()
    
    def SaveProcessVariables(self):
        if self.CurrentNodesFilter is not None:
            if len(self.CurrentNodesFilter) > 0:
                self.Controler.SetProcessVariables(self.ProcessVariables)
            else:
                self.Controler.SetProcessVariables(self.ProcessVariablesTable.GetData())
            self.RefreshBuffer()
    
    def RefreshStartupCommands(self, position=None, command_idx=None):
        if self.CurrentNodesFilter is not None:
            col = max(self.StartupCommandsGrid.GetGridCursorCol(), 0)
            self.StartupCommandsTable.SetData(
                self.Controler.GetStartupCommands(**self.CurrentNodesFilter))
            self.StartupCommandsTable.ResetView(self.StartupCommandsGrid)
            if position is not None and command_idx is not None:
                self.SelectStartupCommand(position, command_idx, col)
    
    def SelectStartupCommand(self, position, command_idx, col):
        self.StartupCommandsGrid.SetSelectedCell(
            self.StartupCommandsTable.GetCommandIndex(position, command_idx),
            col)
    
    def GetMasterLocation(self):
        return self.Controler.GetCurrentLocation()
    
    def AddStartupCommand(self, position, index, subindex):
        col = max(self.StartupCommandsGrid.GetGridCursorCol(), 0)
        command = self.StartupCommandsDefaultValue.copy()
        command["Position"] = position
        command["Index"] = index
        command["Subindex"] = subindex
        command_idx = self.Controler.AppendStartupCommand(command)
        self.RefreshStartupCommands()
        self.RefreshBuffer()
        self.SelectStartupCommand(position, command_idx, col)
    
    def OnNodesFilterChanged(self, event):
        self.RefreshCurrentNodesFilter()
        if self.CurrentNodesFilter is not None:
            self.RefreshProcessVariables()
            self.RefreshStartupCommands()
            self.NodesVariables.RefreshView()
        event.Skip()
    
    def OnNodesFilterKeyDown(self, event):
        if self.NodesFilterFirstCharacter:
            keycode = event.GetKeyCode()
            if keycode not in [wx.WXK_RETURN, 
                               wx.WXK_NUMPAD_ENTER]:
                self.NodesFilterFirstCharacter = False
                if keycode not in NAVIGATION_KEYS:
                    self.NodesFilter.SetValue("")
            if keycode not in [wx.WXK_DELETE, 
                               wx.WXK_NUMPAD_DELETE, 
                               wx.WXK_BACK]:
                event.Skip()
        else:
            event.Skip()
    
    def OnProcessVariablesGridCellChange(self, event):
        row, col = event.GetRow(), event.GetCol()
        colname = self.ProcessVariablesTable.GetColLabelValue(col, False)
        value = self.ProcessVariablesTable.GetValue(row, col)
        message = None
        if colname == "Name":
            if not TestIdentifier(value):
                message = _("\"%s\" is not a valid identifier!") % value
            elif value.upper() in IEC_KEYWORDS:
                message = _("\"%s\" is a keyword. It can't be used!") % value
            elif value.upper() in [var["Name"].upper() for idx, var in enumerate(self.ProcessVariablesTable.GetData()) if idx != row]:
                message = _("An variable named \"%s\" already exists!") % value
        if message is None:
            self.SaveProcessVariables()
            wx.CallAfter(self.ProcessVariablesTable.ResetView, self.ProcessVariablesGrid)
            event.Skip()
        else:
            dialog = wx.MessageDialog(self, message, _("Error"), wx.OK|wx.ICON_ERROR)
            dialog.ShowModal()
            dialog.Destroy()
            event.Veto()
    
    def OnProcessVariablesGridCellLeftClick(self, event):
        row = event.GetRow()
        if event.GetCol() == 0:
            var_name = self.ProcessVariablesTable.GetValueByName(row, "Name")
            var_type = self.Controler.GetSlaveVariableDataType(
                *self.ProcessVariablesTable.GetValueByName(row, "ReadFrom"))
            data_size = self.Controler.GetSizeOfType(var_type)
            number = self.ProcessVariablesTable.GetValueByName(row, "Number")
            location = "%%M%s" % data_size + \
                       ".".join(map(lambda x:str(x), self.Controler.GetCurrentLocation() + (number,)))
            
            data = wx.TextDataObject(str((location, "location", var_type, var_name, "")))
            dragSource = wx.DropSource(self.ProcessVariablesGrid)
            dragSource.SetData(data)
            dragSource.DoDragDrop()
        event.Skip()
    
    def OnProcessVariablesGridKeyDown(self, event):
        keycode = event.GetKeyCode()
        col = self.ProcessVariablesGrid.GetGridCursorCol()
        row = self.ProcessVariablesGrid.GetGridCursorRow()
        colname = self.ProcessVariablesTable.GetColLabelValue(col, False)
        if (keycode in (wx.WXK_DELETE, wx.WXK_NUMPAD_DELETE) and 
            (colname.startswith("Read from") or colname.startswith("Write to"))):
            self.ProcessVariablesTable.SetValue(row, col, "")
            self.SaveProcessVariables()
            wx.CallAfter(self.ProcessVariablesTable.ResetView, self.ProcessVariablesGrid)
        else:
            event.Skip()
    
    def OnStartupCommandsGridEditorShow(self, event):
        self.CellShown = event.GetRow(), event.GetCol()
        event.Skip()
    
    def OnStartupCommandsGridCellChange(self, event):
        row, col = event.GetRow(), event.GetCol()
        if self.CellShown == (row, col):
            self.CellShown = None
            colname = self.StartupCommandsTable.GetColLabelValue(col, False)
            value = self.StartupCommandsTable.GetValue(row, col)
            message = None
            if colname == "Position":
                if value not in self.Controler.GetSlaves():
                    message = _("No slave defined at position %d!") % value
                old_value = self.StartupCommandsTable.GetOldValue()
                command = self.StartupCommandsTable.GetRow(row)
                if message is None and old_value != command["Position"]:
                    self.Controler.RemoveStartupCommand(
                        self.StartupCommandsTable.GetOldValue(),
                        command["command_idx"], False)
                    command_idx = self.Controler.AppendStartupCommand(command)
                    wx.CallAfter(self.RefreshStartupCommands, command["Position"], command_idx)
            else:
                command = self.StartupCommandsTable.GetRow(row)
                self.Controler.SetStartupCommandInfos(command)
                if colname in ["Index", "SubIndex"]: 
                    wx.CallAfter(self.RefreshStartupCommands, command["Position"], command["command_idx"])
            if message is None:
                self.RefreshBuffer()
                event.Skip()
            else:
                dialog = wx.MessageDialog(self, message, _("Error"), wx.OK|wx.ICON_ERROR)
                dialog.ShowModal()
                dialog.Destroy()
                event.Veto()
        else:
            event.Veto()
    
    def OnResize(self, event):
        self.EthercatMasterEditor.GetBestSize()
        xstart, ystart = self.EthercatMasterEditor.GetViewStart()
        window_size = self.EthercatMasterEditor.GetClientSize()
        maxx, maxy = self.EthercatMasterEditorSizer.GetMinSize()
        posx = max(0, min(xstart, (maxx - window_size[0]) / SCROLLBAR_UNIT))
        posy = max(0, min(ystart, (maxy - window_size[1]) / SCROLLBAR_UNIT))
        self.EthercatMasterEditor.Scroll(posx, posy)
        self.EthercatMasterEditor.SetScrollbars(SCROLLBAR_UNIT, SCROLLBAR_UNIT, 
                maxx / SCROLLBAR_UNIT, maxy / SCROLLBAR_UNIT, posx, posy)
        event.Skip()
        
    def OnButtonClick(self, event):
        self.MasterState = self.Controler.getMasterState()
        if self.MasterState:
            self.Phase.SetValue(self.MasterState["phase"])
            self.Active.SetValue(self.MasterState["active"])
            self.SlaveCount.SetValue(self.MasterState["slave"])
            self.MacAddress.SetValue(self.MasterState["MAC"])
            self.LinkState.SetValue(self.MasterState["link"])
            self.TxFrames.SetValue(self.MasterState["TXframe"])
            self.RxFrames.SetValue(self.MasterState["RXframe"])
            self.LostFrames.SetValue(self.MasterState["lost"])
            
            self.TxFrameRate1.SetValue(self.MasterState["TXframerate1"])
            self.TxFrameRate2.SetValue(self.MasterState["TXframerate2"])
            self.TxFrameRate3.SetValue(self.MasterState["TXframerate3"])
            self.TxRate1.SetValue(self.MasterState["TXrate1"])
            self.TxRate2.SetValue(self.MasterState["TXrate2"])
            self.TxRate3.SetValue(self.MasterState["TXrate3"])
            self.LossRate1.SetValue(self.MasterState["loss1"])
            self.LossRate2.SetValue(self.MasterState["loss2"])
            self.LossRate3.SetValue(self.MasterState["loss3"])
            self.FrameLoss1.SetValue(self.MasterState["frameloss1"])
            self.FrameLoss2.SetValue(self.MasterState["frameloss2"])
            self.FrameLoss3.SetValue(self.MasterState["frameloss3"])
    
class LibraryEditorSizer(wx.FlexGridSizer):
    
    def __init__(self, parent, module_library, buttons):
        wx.FlexGridSizer.__init__(self, cols=1, hgap=0, rows=4, vgap=5)
        
        self.ModuleLibrary = module_library
        self.ParentWindow = parent
        
        self.AddGrowableCol(0)
        self.AddGrowableRow(1)
        self.AddGrowableRow(3)
        
        ESI_files_label = wx.StaticText(parent, 
            label=_("ESI Files:"))
        self.AddWindow(ESI_files_label, border=10, 
            flag=wx.TOP|wx.LEFT|wx.RIGHT)
        
        folder_tree_sizer = wx.FlexGridSizer(cols=2, hgap=5, rows=1, vgap=0)
        folder_tree_sizer.AddGrowableCol(0)
        folder_tree_sizer.AddGrowableRow(0)
        self.AddSizer(folder_tree_sizer, border=10, 
            flag=wx.GROW|wx.LEFT|wx.RIGHT)
        
        self.ESIFiles = FolderTree(parent, self.GetPath(), editable=False)
        self.ESIFiles.SetFilter(".xml")
        folder_tree_sizer.AddWindow(self.ESIFiles, flag=wx.GROW)
        
        buttons_sizer = wx.BoxSizer(wx.VERTICAL)
        folder_tree_sizer.AddSizer(buttons_sizer, 
            flag=wx.ALIGN_CENTER_VERTICAL)
        
        for idx, (name, bitmap, help, callback) in enumerate(buttons):
            button = wx.lib.buttons.GenBitmapButton(parent, 
                  bitmap=GetBitmap(bitmap), 
                  size=wx.Size(28, 28), style=wx.NO_BORDER)
            button.SetToolTipString(help)
            setattr(self, name, button)
            if idx > 0:
                flag = wx.TOP
            else:
                flag = 0
            if callback is None:
                callback = getattr(self, "On" + name, None)
            if callback is not None:
                parent.Bind(wx.EVT_BUTTON, callback, button)
            buttons_sizer.AddWindow(button, border=10, flag=flag)
        
        modules_label = wx.StaticText(parent, 
            label=_("Modules library:"))
        self.AddSizer(modules_label, border=10, 
            flag=wx.LEFT|wx.RIGHT)
        
        self.ModulesGrid = wx.gizmos.TreeListCtrl(parent,
              style=wx.TR_DEFAULT_STYLE |
                    wx.TR_ROW_LINES |
                    wx.TR_COLUMN_LINES |
                    wx.TR_HIDE_ROOT |
                    wx.TR_FULL_ROW_HIGHLIGHT)
        self.ModulesGrid.GetMainWindow().Bind(wx.EVT_LEFT_DOWN,
            self.OnModulesGridLeftDown)
        self.ModulesGrid.Bind(wx.EVT_TREE_BEGIN_LABEL_EDIT,
            self.OnModulesGridBeginLabelEdit)
        self.ModulesGrid.Bind(wx.EVT_TREE_END_LABEL_EDIT,
            self.OnModulesGridEndLabelEdit)
        self.ModulesGrid.GetHeaderWindow().Bind(wx.EVT_MOTION, 
            self.OnModulesGridHeaderMotion)
        self.AddWindow(self.ModulesGrid, border=10, 
            flag=wx.GROW|wx.BOTTOM|wx.LEFT|wx.RIGHT)
        
        for colname, colsize, colalign in zip(
                [_("Name")] + [param_infos["column_label"] 
                               for param, param_infos in 
                               self.ModuleLibrary.MODULES_EXTRA_PARAMS],
                [400] + [param_infos["column_size"] 
                         for param, param_infos in 
                         self.ModuleLibrary.MODULES_EXTRA_PARAMS],
                [wx.ALIGN_LEFT] + [wx.ALIGN_RIGHT] * len(self.ModuleLibrary.MODULES_EXTRA_PARAMS)):
            self.ModulesGrid.AddColumn(_(colname), colsize, colalign, edit=True)
        self.ModulesGrid.SetMainColumn(0)
        
        self.CurrentSelectedCol = None
        self.LastToolTipCol = None
    
    def GetPath(self):
        return self.ModuleLibrary.GetPath()
    
    def SetControlMinSize(self, size):
        self.ESIFiles.SetMinSize(size)
        self.ModulesGrid.SetMinSize(size)
        
    def GetSelectedFilePath(self):
        return self.ESIFiles.GetPath()
    
    def RefreshView(self):
        self.ESIFiles.RefreshTree()
        self.RefreshModulesGrid()
    
    def RefreshModulesGrid(self):
        root = self.ModulesGrid.GetRootItem()
        if not root.IsOk():
            root = self.ModulesGrid.AddRoot("Modules")
        self.GenerateModulesGridBranch(root, 
            self.ModuleLibrary.GetModulesLibrary(), 
            GetVariablesTableColnames())
        self.ModulesGrid.Expand(root)
            
    def GenerateModulesGridBranch(self, root, modules, colnames):
        item, root_cookie = self.ModulesGrid.GetFirstChild(root)
        
        no_more_items = not item.IsOk()
        for module in modules:
            if no_more_items:
                item = self.ModulesGrid.AppendItem(root, "")
            self.ModulesGrid.SetItemText(item, module["name"], 0)
            if module["infos"] is not None:
                for param_idx, (param, param_infos) in enumerate(self.ModuleLibrary.MODULES_EXTRA_PARAMS):
                    self.ModulesGrid.SetItemText(item, 
                                                 str(module["infos"][param]), 
                                                 param_idx + 1)
            else:
                self.ModulesGrid.SetItemBackgroundColour(item, wx.LIGHT_GREY)
            self.ModulesGrid.SetItemPyData(item, module["infos"])
            self.GenerateModulesGridBranch(item, module["children"], colnames)
            if not no_more_items:
                item, root_cookie = self.ModulesGrid.GetNextChild(root, root_cookie)
                no_more_items = not item.IsOk()
        
        if not no_more_items:
            to_delete = []
            while item.IsOk():
                to_delete.append(item)
                item, root_cookie = self.ModulesGrid.GetNextChild(root, root_cookie)
            for item in to_delete:
                self.ModulesGrid.Delete(item)
    
    def OnImportButton(self, event):
        dialog = wx.FileDialog(self.ParentWindow,
             _("Choose an XML file"), 
             os.getcwd(), "",  
             _("XML files (*.xml)|*.xml|All files|*.*"), wx.OPEN)
        
        if dialog.ShowModal() == wx.ID_OK:
            filepath = dialog.GetPath()
            if self.ModuleLibrary.ImportModuleLibrary(filepath):
                wx.CallAfter(self.RefreshView)
            else:
                message = wx.MessageDialog(self, 
                    _("No such XML file: %s\n") % filepath, 
                    _("Error"), wx.OK|wx.ICON_ERROR)
                message.ShowModal()
                message.Destroy()
        dialog.Destroy()
        
        event.Skip()
    
    def OnDeleteButton(self, event):
        filepath = self.GetSelectedFilePath()
        if os.path.isfile(filepath):
            folder, filename = os.path.split(filepath)
            
            dialog = wx.MessageDialog(self.ParentWindow, 
                  _("Do you really want to delete the file '%s'?") % filename, 
                  _("Delete File"), wx.YES_NO|wx.ICON_QUESTION)
            remove = dialog.ShowModal() == wx.ID_YES
            dialog.Destroy()
            
            if remove:
                os.remove(filepath)
                self.ModuleLibrary.LoadModules()
                wx.CallAfter(self.RefreshView)
        event.Skip()
    
    def OnModulesGridLeftDown(self, event):
        item, flags, col = self.ModulesGrid.HitTest(event.GetPosition())
        if item.IsOk():
            entry_infos = self.ModulesGrid.GetItemPyData(item)
            if entry_infos is not None and col > 0:
                self.CurrentSelectedCol = col
            else:
                self.CurrentSelectedCol = None
        else:
            self.CurrentSelectedCol = None
        event.Skip()

    def OnModulesGridBeginLabelEdit(self, event):
        item = event.GetItem()
        if item.IsOk():
            entry_infos = self.ModulesGrid.GetItemPyData(item)
            if entry_infos is not None:
                event.Skip()
            else:
                event.Veto()
        else:
            event.Veto()

    def OnModulesGridEndLabelEdit(self, event):
        item = event.GetItem()
        if item.IsOk() and self.CurrentSelectedCol is not None:
            entry_infos = self.ModulesGrid.GetItemPyData(item)
            if entry_infos is not None and self.CurrentSelectedCol > 0:
                param, param_infos = self.ModuleLibrary.MODULES_EXTRA_PARAMS[self.CurrentSelectedCol - 1]
                stripped_column_label = param_infos["column_label"].split('(')[0].strip()
                try:
                    self.ModuleLibrary.SetModuleExtraParam(
                        entry_infos["vendor"],
                        entry_infos["product_code"],
                        entry_infos["revision_number"],
                        param,
                        int(event.GetLabel()))
                    wx.CallAfter(self.RefreshModulesGrid)
                    event.Skip()
                except ValueError:
                    message = wx.MessageDialog(self, 
                        _("Module %s must be an integer!") % stripped_column_label, 
                        _("Error"), wx.OK|wx.ICON_ERROR)
                    message.ShowModal()
                    message.Destroy()
                    event.Veto()
            else:
                event.Veto()
        else:
            event.Veto()
                
    def OnModulesGridHeaderMotion(self, event):
        item, flags, col = self.ModulesGrid.HitTest(event.GetPosition())
        if col != self.LastToolTipCol and self.LastToolTipCol is not None:
            self.ModulesGrid.GetHeaderWindow().SetToolTip(None)
            self.LastToolTipCol = None
        if col > 0 and self.LastToolTipCol != col:
            self.LastToolTipCol = col
            param, param_infos = self.ModuleLibrary.MODULES_EXTRA_PARAMS[col - 1]
            wx.CallAfter(self.ModulesGrid.GetHeaderWindow().SetToolTipString, 
                         param_infos["description"])
        event.Skip()

class DatabaseManagementDialog(wx.Dialog):
    
    def __init__(self, parent, database):
        wx.Dialog.__init__(self, parent,
              size=wx.Size(700, 500), title=_('ESI Files Database management'),
              style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)
        
        main_sizer = wx.FlexGridSizer(cols=1, hgap=0, rows=2, vgap=10)
        main_sizer.AddGrowableCol(0)
        main_sizer.AddGrowableRow(0)
        
        self.DatabaseSizer = LibraryEditorSizer(self, database,
            [("ImportButton", "ImportESI", _("Import file to ESI files database"), None),
             ("DeleteButton", "remove_element", _("Remove file from database"), None)])
        self.DatabaseSizer.SetControlMinSize(wx.Size(0, 0))
        main_sizer.AddSizer(self.DatabaseSizer, border=10,
            flag=wx.GROW|wx.TOP|wx.LEFT|wx.RIGHT)
        
        button_sizer = self.CreateButtonSizer(wx.OK|wx.CANCEL|wx.CENTRE)
        button_sizer.GetAffirmativeButton().SetLabel(_("Add file to project"))
        button_sizer.GetCancelButton().SetLabel(_("Close"))
        main_sizer.AddSizer(button_sizer, border=10, 
              flag=wx.ALIGN_RIGHT|wx.BOTTOM|wx.LEFT|wx.RIGHT)
        
        self.SetSizer(main_sizer)
        
        self.DatabaseSizer.RefreshView()
        
    def GetValue(self):
        return self.DatabaseSizer.GetSelectedFilePath()

class LibraryEditor(ConfTreeNodeEditor):
    
    CONFNODEEDITOR_TABS = [
        (_("Modules Library"), "_create_ModuleLibraryEditor")]
    
    def _create_ModuleLibraryEditor(self, prnt):
        self.ModuleLibraryEditor = wx.ScrolledWindow(prnt,
            style=wx.TAB_TRAVERSAL|wx.HSCROLL|wx.VSCROLL)
        self.ModuleLibraryEditor.Bind(wx.EVT_SIZE, self.OnResize)
        
        self.ModuleLibrarySizer = LibraryEditorSizer(self.ModuleLibraryEditor,
            self.Controler.GetModulesLibraryInstance(),
            [("ImportButton", "ImportESI", _("Import ESI file"), None),
             ("AddButton", "ImportDatabase", _("Add file from ESI files database"), self.OnAddButton),
             ("DeleteButton", "remove_element", _("Remove file from library"), None)])
        self.ModuleLibrarySizer.SetControlMinSize(wx.Size(0, 200))
        self.ModuleLibraryEditor.SetSizer(self.ModuleLibrarySizer)
        
        return self.ModuleLibraryEditor

    def __init__(self, parent, controler, window):
        ConfTreeNodeEditor.__init__(self, parent, controler, window)
    
        self.RefreshView()
    
    def RefreshView(self):
        ConfTreeNodeEditor.RefreshView(self)
        self.ModuleLibrarySizer.RefreshView()

    def OnAddButton(self, event):
        dialog = DatabaseManagementDialog(self, 
            self.Controler.GetModulesDatabaseInstance())
        
        if dialog.ShowModal() == wx.ID_OK:
            module_library = self.Controler.GetModulesLibraryInstance()
            module_library.ImportModuleLibrary(dialog.GetValue())
            
        dialog.Destroy()
        
        wx.CallAfter(self.ModuleLibrarySizer.RefreshView)
        
        event.Skip()

    def OnResize(self, event):
        self.ModuleLibraryEditor.GetBestSize()
        xstart, ystart = self.ModuleLibraryEditor.GetViewStart()
        window_size = self.ModuleLibraryEditor.GetClientSize()
        maxx, maxy = self.ModuleLibraryEditor.GetMinSize()
        posx = max(0, min(xstart, (maxx - window_size[0]) / SCROLLBAR_UNIT))
        posy = max(0, min(ystart, (maxy - window_size[1]) / SCROLLBAR_UNIT))
        self.ModuleLibraryEditor.Scroll(posx, posy)
        self.ModuleLibraryEditor.SetScrollbars(SCROLLBAR_UNIT, SCROLLBAR_UNIT, 
                maxx / SCROLLBAR_UNIT, maxy / SCROLLBAR_UNIT, posx, posy)
        event.Skip()
        

