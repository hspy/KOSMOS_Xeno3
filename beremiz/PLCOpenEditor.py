#!/usr/bin/env python
# -*- coding: utf-8 -*-

#This file is part of PLCOpenEditor, a library implementing an IEC 61131-3 editor
#based on the plcopen standard. 
#
#Copyright (C) 2007: Edouard TISSERANT and Laurent BESSARD
#
#See COPYING file for copyrights details.
#
#This library is free software; you can redistribute it and/or
#modify it under the terms of the GNU General Public
#License as published by the Free Software Foundation; either
#version 2.1 of the License, or (at your option) any later version.
#
#This library is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#General Public License for more details.
#
#You should have received a copy of the GNU General Public
#License along with this library; if not, write to the Free Software
#Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

import wx
import os, sys, platform, time, traceback, getopt

CWD = os.path.split(os.path.realpath(__file__))[0]

__version__ = "$Revision: 1.130 $"

if __name__ == '__main__':
    # Usage message displayed when help request or when error detected in 
    # command line
    def usage():
        print "\nUsage of PLCOpenEditor.py :"
        print "\n   %s [Filepath]\n"%sys.argv[0]

    # Parse options given to PLCOpenEditor in command line
    try:
        opts, args = getopt.getopt(sys.argv[1:], "h", ["help"])
    except getopt.GetoptError:
        # print help information and exit:
        usage()
        sys.exit(2)
    
    # Extract if help has been requested
    for o, a in opts:
        if o in ("-h", "--help"):
            usage()
            sys.exit()
    
    # Extract the optional filename to open
    fileOpen = None
    if len(args) > 1:
        usage()
        sys.exit()
    elif len(args) == 1:
        fileOpen = args[0]
    
    # Create wxApp (Need to create App before internationalization because of
    # Windows) 
    app = wx.PySimpleApp()

from docutil import *

from util.TranslationCatalogs import AddCatalog
from util.BitmapLibrary import AddBitmapFolder, GetBitmap

AddCatalog(os.path.join(CWD, "locale"))
AddBitmapFolder(os.path.join(CWD, "images"))

if __name__ == '__main__':
    # Import module for internationalization
    import gettext
    import __builtin__
    
    __builtin__.__dict__['_'] = wx.GetTranslation

from IDEFrame import IDEFrame, AppendMenu
from IDEFrame import TITLE, EDITORTOOLBAR, FILEMENU, EDITMENU, DISPLAYMENU, PROJECTTREE, POUINSTANCEVARIABLESPANEL, LIBRARYTREE, PAGETITLES
from IDEFrame import EncodeFileSystemPath, DecodeFileSystemPath
from editors.Viewer import Viewer
from PLCControler import PLCControler
from dialogs import ProjectDialog

#-------------------------------------------------------------------------------
#                            PLCOpenEditor Main Class
#-------------------------------------------------------------------------------

# Define PLCOpenEditor FileMenu extra items id
[ID_PLCOPENEDITORFILEMENUGENERATE, 
] = [wx.NewId() for _init_coll_FileMenu_Items in range(1)]

class PLCOpenEditor(IDEFrame):

    # Compatibility function for wx versions < 2.6
    if wx.VERSION < (2, 6, 0):
        def Bind(self, event, function, id = None):
            if id is not None:
                event(self, id, function)
            else:
                event(self, function)

    def _init_coll_FileMenu_Items(self, parent):
        AppendMenu(parent, help='', id=wx.ID_NEW,
              kind=wx.ITEM_NORMAL, text=_(u'New') +'\tCTRL+N')
        AppendMenu(parent, help='', id=wx.ID_OPEN,
              kind=wx.ITEM_NORMAL, text=_(u'Open') + '\tCTRL+O')
        AppendMenu(parent, help='', id=wx.ID_CLOSE,
              kind=wx.ITEM_NORMAL, text=_(u'Close Tab') + '\tCTRL+W')
        AppendMenu(parent, help='', id=wx.ID_CLOSE_ALL,
              kind=wx.ITEM_NORMAL, text=_(u'Close Project') + '\tCTRL+SHIFT+W')
        parent.AppendSeparator()
        AppendMenu(parent, help='', id=wx.ID_SAVE,
              kind=wx.ITEM_NORMAL, text=_(u'Save') + '\tCTRL+S')
        AppendMenu(parent, help='', id=wx.ID_SAVEAS,
              kind=wx.ITEM_NORMAL, text=_(u'Save As...') + '\tCTRL+SHIFT+S')
        AppendMenu(parent, help='', id=ID_PLCOPENEDITORFILEMENUGENERATE,
              kind=wx.ITEM_NORMAL, text=_(u'Generate Program') + '\tCTRL+G')
        parent.AppendSeparator()
        AppendMenu(parent, help='', id=wx.ID_PAGE_SETUP,
              kind=wx.ITEM_NORMAL, text=_(u'Page Setup') + '\tCTRL+ALT+P')
        AppendMenu(parent, help='', id=wx.ID_PREVIEW,
              kind=wx.ITEM_NORMAL, text=_(u'Preview') + '\tCTRL+SHIFT+P')
        AppendMenu(parent, help='', id=wx.ID_PRINT,
              kind=wx.ITEM_NORMAL, text=_(u'Print') + '\tCTRL+P')
        parent.AppendSeparator()
        AppendMenu(parent, help='', id=wx.ID_PROPERTIES,
              kind=wx.ITEM_NORMAL, text=_(u'&Properties'))
        parent.AppendSeparator()
        AppendMenu(parent, help='', id=wx.ID_EXIT,
              kind=wx.ITEM_NORMAL, text=_(u'Quit') + '\tCTRL+Q')
        
        self.Bind(wx.EVT_MENU, self.OnNewProjectMenu, id=wx.ID_NEW)
        self.Bind(wx.EVT_MENU, self.OnOpenProjectMenu, id=wx.ID_OPEN)
        self.Bind(wx.EVT_MENU, self.OnCloseTabMenu, id=wx.ID_CLOSE)
        self.Bind(wx.EVT_MENU, self.OnCloseProjectMenu, id=wx.ID_CLOSE_ALL)
        self.Bind(wx.EVT_MENU, self.OnSaveProjectMenu, id=wx.ID_SAVE)
        self.Bind(wx.EVT_MENU, self.OnSaveProjectAsMenu, id=wx.ID_SAVEAS)
        self.Bind(wx.EVT_MENU, self.OnGenerateProgramMenu,
              id=ID_PLCOPENEDITORFILEMENUGENERATE)
        self.Bind(wx.EVT_MENU, self.OnPageSetupMenu, id=wx.ID_PAGE_SETUP)
        self.Bind(wx.EVT_MENU, self.OnPreviewMenu, id=wx.ID_PREVIEW)
        self.Bind(wx.EVT_MENU, self.OnPrintMenu, id=wx.ID_PRINT)
        self.Bind(wx.EVT_MENU, self.OnPropertiesMenu, id=wx.ID_PROPERTIES)
        self.Bind(wx.EVT_MENU, self.OnQuitMenu, id=wx.ID_EXIT)
        
        self.AddToMenuToolBar([(wx.ID_NEW, "new", _(u'New'), None),
                               (wx.ID_OPEN, "open", _(u'Open'), None),
                               (wx.ID_SAVE, "save", _(u'Save'), None),
                               (wx.ID_SAVEAS, "saveas", _(u'Save As...'), None),
                               (wx.ID_PRINT, "print", _(u'Print'), None)])
            
    def _init_coll_HelpMenu_Items(self, parent):
        AppendMenu(parent, help='', id=wx.ID_HELP, 
            kind=wx.ITEM_NORMAL, text=_(u'PLCOpenEditor') + '\tF1')
        #AppendMenu(parent, help='', id=wx.ID_HELP_CONTENTS,
        #      kind=wx.ITEM_NORMAL, text=u'PLCOpen\tF2')
        #AppendMenu(parent, help='', id=wx.ID_HELP_CONTEXT,
        #      kind=wx.ITEM_NORMAL, text=u'IEC 61131-3\tF3')
        AppendMenu(parent, help='', id=wx.ID_ABOUT,
            kind=wx.ITEM_NORMAL, text=_(u'About'))
        self.Bind(wx.EVT_MENU, self.OnPLCOpenEditorMenu, id=wx.ID_HELP)
        #self.Bind(wx.EVT_MENU, self.OnPLCOpenMenu, id=wx.ID_HELP_CONTENTS)
        self.Bind(wx.EVT_MENU, self.OnAboutMenu, id=wx.ID_ABOUT)

    ## Constructor of the PLCOpenEditor class.
    #  @param parent The parent window.
    #  @param controler The controler been used by PLCOpenEditor (default: None).
    #  @param fileOpen The filepath to open if no controler defined (default: None).
    #  @param debug The filepath to open if no controler defined (default: False).
    def __init__(self, parent, fileOpen = None):
        IDEFrame.__init__(self, parent)
        
        result = None
        
        # Open the filepath if defined
        if fileOpen is not None:
            fileOpen = DecodeFileSystemPath(fileOpen, False)
            if os.path.isfile(fileOpen):
                # Create a new controller
                controler = PLCControler()
                result = controler.OpenXMLFile(fileOpen)
                if result is None:
                    self.Controler = controler
                    self.LibraryPanel.SetController(controler)
                    self.ProjectTree.Enable(True)
                    self.PouInstanceVariablesPanel.SetController(controler)
                    self._Refresh(PROJECTTREE, POUINSTANCEVARIABLESPANEL, LIBRARYTREE)
        
        # Define PLCOpenEditor icon
        self.SetIcon(wx.Icon(os.path.join(CWD, "images", "poe.ico"),wx.BITMAP_TYPE_ICO))

        self.Bind(wx.EVT_CLOSE, self.OnCloseFrame)
        
        self._Refresh(TITLE, EDITORTOOLBAR, FILEMENU, EDITMENU, DISPLAYMENU)
        
        if result is not None:
            self.ShowErrorMessage(result)

    def OnCloseFrame(self, event):
        if self.Controler is None or self.CheckSaveBeforeClosing(_("Close Application")):
            self.AUIManager.UnInit()
            
            self.SaveLastState()
            
            event.Skip()
        else:
            event.Veto()

    def RefreshTitle(self):
        name = _("PLCOpenEditor")
        if self.Controler is not None:
            self.SetTitle("%s - %s"%(name, self.Controler.GetFilename()))
        else:
            self.SetTitle(name)

#-------------------------------------------------------------------------------
#                            File Menu Functions
#-------------------------------------------------------------------------------

    def RefreshFileMenu(self):
        MenuToolBar = self.Panes["MenuToolBar"]
        if self.Controler is not None:
            selected = self.TabsOpened.GetSelection()
            if selected >= 0:
                graphic_viewer = isinstance(self.TabsOpened.GetPage(selected), Viewer)
            else:
                graphic_viewer = False
            if self.TabsOpened.GetPageCount() > 0:
                self.FileMenu.Enable(wx.ID_CLOSE, True)
                if graphic_viewer:
                    self.FileMenu.Enable(wx.ID_PREVIEW, True)
                    self.FileMenu.Enable(wx.ID_PRINT, True)
                    MenuToolBar.EnableTool(wx.ID_PRINT, True)
                else:
                    self.FileMenu.Enable(wx.ID_PREVIEW, False)
                    self.FileMenu.Enable(wx.ID_PRINT, False)
                    MenuToolBar.EnableTool(wx.ID_PRINT, False)
            else:
                self.FileMenu.Enable(wx.ID_CLOSE, False)
                self.FileMenu.Enable(wx.ID_PREVIEW, False)
                self.FileMenu.Enable(wx.ID_PRINT, False)
                MenuToolBar.EnableTool(wx.ID_PRINT, False)
            self.FileMenu.Enable(wx.ID_PAGE_SETUP, True)
            project_modified = not self.Controler.ProjectIsSaved()
            self.FileMenu.Enable(wx.ID_SAVE, project_modified)
            MenuToolBar.EnableTool(wx.ID_SAVE, project_modified)
            self.FileMenu.Enable(wx.ID_PROPERTIES, True)
            self.FileMenu.Enable(wx.ID_CLOSE_ALL, True)
            self.FileMenu.Enable(wx.ID_SAVEAS, True)
            MenuToolBar.EnableTool(wx.ID_SAVEAS, True)
            self.FileMenu.Enable(ID_PLCOPENEDITORFILEMENUGENERATE, True)
        else:
            self.FileMenu.Enable(wx.ID_CLOSE, False)
            self.FileMenu.Enable(wx.ID_PAGE_SETUP, False)
            self.FileMenu.Enable(wx.ID_PREVIEW, False)
            self.FileMenu.Enable(wx.ID_PRINT, False)
            MenuToolBar.EnableTool(wx.ID_PRINT, False)
            self.FileMenu.Enable(wx.ID_SAVE, False)
            MenuToolBar.EnableTool(wx.ID_SAVE, False)
            self.FileMenu.Enable(wx.ID_PROPERTIES, False)
            self.FileMenu.Enable(wx.ID_CLOSE_ALL, False)
            self.FileMenu.Enable(wx.ID_SAVEAS, False)
            MenuToolBar.EnableTool(wx.ID_SAVEAS, False)
            self.FileMenu.Enable(ID_PLCOPENEDITORFILEMENUGENERATE, False)

    def OnNewProjectMenu(self, event):
        if self.Controler is not None and not self.CheckSaveBeforeClosing():
            return
        dialog = ProjectDialog(self)
        if dialog.ShowModal() == wx.ID_OK:
            properties = dialog.GetValues()
            self.ResetView()
            self.Controler = PLCControler()
            self.Controler.CreateNewProject(properties)
            self.LibraryPanel.SetController(self.Controler)
            self._Refresh(TITLE, FILEMENU, EDITMENU, PROJECTTREE, POUINSTANCEVARIABLESPANEL, 
                          LIBRARYTREE)

    def OnOpenProjectMenu(self, event):
        if self.Controler is not None and not self.CheckSaveBeforeClosing():
            return
        filepath = ""
        if self.Controler is not None:
            filepath = self.Controler.GetFilePath()
        if filepath != "":
            directory = os.path.dirname(filepath)
        else:
            directory = os.getcwd()
        
        result = None
        
        dialog = wx.FileDialog(self, _("Choose a file"), directory, "",  _("PLCOpen files (*.xml)|*.xml|All files|*.*"), wx.OPEN)
        if dialog.ShowModal() == wx.ID_OK:
            filepath = dialog.GetPath()
            if os.path.isfile(filepath):
                self.ResetView()
                controler = PLCControler()
                result = controler.OpenXMLFile(filepath)
                if result is None:
                    self.Controler = controler
                    self.LibraryPanel.SetController(controler)
                    self.ProjectTree.Enable(True)
                    self.PouInstanceVariablesPanel.SetController(controler)
                    self._Refresh(PROJECTTREE, LIBRARYTREE)
            self._Refresh(TITLE, EDITORTOOLBAR, FILEMENU, EDITMENU)
        dialog.Destroy()
        
        if result is not None:
            self.ShowErrorMessage(result)
    
    def OnCloseProjectMenu(self, event):
        if not self.CheckSaveBeforeClosing():
            return
        self.ResetView()
        self._Refresh(TITLE, EDITORTOOLBAR, FILEMENU, EDITMENU)

    def OnSaveProjectMenu(self, event):
        self.SaveProject()

    def OnSaveProjectAsMenu(self, event):
        self.SaveProjectAs()

    def OnGenerateProgramMenu(self, event):
        dialog = wx.FileDialog(self, _("Choose a file"), os.getcwd(), self.Controler.GetProgramFilePath(),  _("ST files (*.st)|*.st|All files|*.*"), wx.SAVE|wx.CHANGE_DIR)
        if dialog.ShowModal() == wx.ID_OK:
            filepath = dialog.GetPath()
            message_text = ""
            header, icon = _("Done"), wx.ICON_INFORMATION
            if os.path.isdir(os.path.dirname(filepath)):
                program, errors, warnings = self.Controler.GenerateProgram(filepath)
                message_text += "".join([_("warning: %s\n") for warning in warnings])
                if len(errors) > 0:
                    message_text += "".join([_("error: %s\n") for error in errors])
                    message_text += _("Can't generate program to file %s!")%filepath
                    header, icon = _("Error"), wx.ICON_ERROR
                else:
                    message_text += _("Program was successfully generated!")
            else:
                message_text += _("\"%s\" is not a valid folder!")%os.path.dirname(filepath)
                header, icon = _("Error"), wx.ICON_ERROR
            message = wx.MessageDialog(self, message_text, header, wx.OK|icon)
            message.ShowModal()
            message.Destroy()
        dialog.Destroy()

    def OnPLCOpenEditorMenu(self, event):
        wx.MessageBox(_("No documentation available.\nComing soon."))
        
    def OnPLCOpenMenu(self, event):
        open_pdf(os.path.join(CWD, "plcopen", "TC6_XML_V101.pdf"))
    
    def OnAboutMenu(self, event):
        OpenHtmlFrame(self,_("About PLCOpenEditor"), os.path.join(CWD, "doc", "plcopen_about.html"), wx.Size(350, 350))

    def SaveProject(self):
        result = self.Controler.SaveXMLFile()
        if not result:
            self.SaveProjectAs()
        else:
            self._Refresh(TITLE, FILEMENU, PAGETITLES)
        
    def SaveProjectAs(self):
        filepath = self.Controler.GetFilePath()
        if filepath != "":
            directory, filename = os.path.split(filepath)
        else:
            directory, filename = os.getcwd(), "%(projectName)s.xml"%self.Controler.GetProjectProperties()
        dialog = wx.FileDialog(self, _("Choose a file"), directory, filename,  _("PLCOpen files (*.xml)|*.xml|All files|*.*"), wx.SAVE|wx.OVERWRITE_PROMPT)
        if dialog.ShowModal() == wx.ID_OK:
            filepath = dialog.GetPath()
            if os.path.isdir(os.path.dirname(filepath)):
                result = self.Controler.SaveXMLFile(filepath)
                if not result:
                    self.ShowErrorMessage(_("Can't save project to file %s!")%filepath)
            else:
                self.ShowErrorMessage(_("\"%s\" is not a valid folder!")%os.path.dirname(filepath))
            self._Refresh(TITLE, FILEMENU, PAGETITLES)
        dialog.Destroy()

#-------------------------------------------------------------------------------
#                               Exception Handler
#-------------------------------------------------------------------------------

Max_Traceback_List_Size = 20

def Display_Exception_Dialog(e_type,e_value,e_tb):
    trcbck_lst = []
    for i,line in enumerate(traceback.extract_tb(e_tb)):
        trcbck = " " + str(i+1) + _(". ")
        if line[0].find(os.getcwd()) == -1:
            trcbck += _("file : ") + str(line[0]) + _(",   ")
        else:
            trcbck += _("file : ") + str(line[0][len(os.getcwd()):]) + _(",   ")
        trcbck += _("line : ") + str(line[1]) + _(",   ") + _("function : ") + str(line[2])
        trcbck_lst.append(trcbck)
        
    # Allow clicking....
    cap = wx.Window_GetCapture()
    if cap:
        cap.ReleaseMouse()

    dlg = wx.SingleChoiceDialog(None, 
        _("""
An error has occurred.

Click OK to save an error report.

Please be kind enough to send this file to:
edouard.tisserant@gmail.com

Error:
""") +
        str(e_type) + _(" : ") + str(e_value), 
        _("Error"),
        trcbck_lst)
    try:
        res = (dlg.ShowModal() == wx.ID_OK)
    finally:
        dlg.Destroy()

    return res

def Display_Error_Dialog(e_value):
    message = wx.MessageDialog(None, str(e_value), _("Error"), wx.OK|wx.ICON_ERROR)
    message.ShowModal()
    message.Destroy()

def get_last_traceback(tb):
    while tb.tb_next:
        tb = tb.tb_next
    return tb


def format_namespace(d, indent='    '):
    return '\n'.join(['%s%s: %s' % (indent, k, repr(v)[:10000]) for k, v in d.iteritems()])


ignored_exceptions = [] # a problem with a line in a module is only reported once per session

def AddExceptHook(path, app_version='[No version]'):#, ignored_exceptions=[]):
    
    def handle_exception(e_type, e_value, e_traceback):
        traceback.print_exception(e_type, e_value, e_traceback) # this is very helpful when there's an exception in the rest of this func
        last_tb = get_last_traceback(e_traceback)
        ex = (last_tb.tb_frame.f_code.co_filename, last_tb.tb_frame.f_lineno)
        if str(e_value).startswith("!!!"):
            Display_Error_Dialog(e_value)
        elif ex not in ignored_exceptions:
            result = Display_Exception_Dialog(e_type,e_value,e_traceback)
            if result:
                ignored_exceptions.append(ex)
                info = {
                    'app-title' : wx.GetApp().GetAppName(), # app_title
                    'app-version' : app_version,
                    'wx-version' : wx.VERSION_STRING,
                    'wx-platform' : wx.Platform,
                    'python-version' : platform.python_version(), #sys.version.split()[0],
                    'platform' : platform.platform(),
                    'e-type' : e_type,
                    'e-value' : e_value,
                    'date' : time.ctime(),
                    'cwd' : os.getcwd(),
                    }
                if e_traceback:
                    info['traceback'] = ''.join(traceback.format_tb(e_traceback)) + '%s: %s' % (e_type, e_value)
                    last_tb = get_last_traceback(e_traceback)
                    exception_locals = last_tb.tb_frame.f_locals # the locals at the level of the stack trace where the exception actually occurred
                    info['locals'] = format_namespace(exception_locals)
                    if 'self' in exception_locals:
                        info['self'] = format_namespace(exception_locals['self'].__dict__)
                
                output = open(path+os.sep+"bug_report_"+info['date'].replace(':','-').replace(' ','_')+".txt",'w')
                lst = info.keys()
                lst.sort()
                for a in lst:
                    output.write(a+":\n"+str(info[a])+"\n\n")

    #sys.excepthook = lambda *args: wx.CallAfter(handle_exception, *args)
    sys.excepthook = handle_exception

if __name__ == '__main__':
    wx.InitAllImageHandlers()
    
    # Install a exception handle for bug reports
    AddExceptHook(os.getcwd(),__version__)
    
    frame = PLCOpenEditor(None, fileOpen=fileOpen)

    frame.Show()
    app.MainLoop()
    
