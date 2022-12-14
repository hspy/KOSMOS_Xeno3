#!/usr/bin/env python
# -*- coding: utf-8 -*-

#This file is part of Beremiz, a Integrated Development Environment for
#programming IEC 61131-3 automates supporting plcopen standard and CanFestival. 
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

import os, sys, getopt
from threading import Thread, currentThread, Semaphore, Lock
from runtime.xenomai import TryPreloadXenomai
def usage():
    print """
Usage of Beremiz PLC execution service :\n
%s {[-n servicename] [-i IP] [-p port] [-x enabletaskbar] [-a autostart]|-h|--help} working_dir
           -n        - zeroconf service name (default:disabled)
           -i        - IP address of interface to bind to (default:localhost)
           -p        - port number default:3000
           -h        - print this help text and quit
           -a        - autostart PLC (0:disable 1:enable) (default:0)
           -x        - enable/disable wxTaskbarIcon (0:disable 1:enable) (default:1)
           -t        - enable/disable Twisted web interface (0:disable 1:enable) (default:1)
           -c        - enable xenomai3 cobalt (preload Xenomai_init)
           working_dir - directory where are stored PLC files
"""%sys.argv[0]

try:
    opts, argv = getopt.getopt(sys.argv[1:], "i:p:n:x:t:a:c:h")
    #opts, argv = getopt.getopt(sys.argv[1:], "i:p:n:x:t:a:h")
except getopt.GetoptError, err:
    # print help information and exit:
    print str(err) # will print something like "option -a not recognized"
    usage()
    sys.exit(2)

# default values
given_ip = None
port = 3000
servicename = None
autostart = False
enablewx = True
havewx = False
enabletwisted = True
havetwisted = False
cobalt = False

for o, a in opts:
    if o == "-h":
        usage()
        sys.exit()
    elif o == "-i":
        if len(a.split(".")) == 4 or a == "localhost":
            given_ip = a
        else:
            usage()
            sys.exit()
    elif o == "-p":
        # port: port that the service runs on
        port = int(a)
    elif o == "-n":
        servicename = a
    elif o == "-x":
        enablewx = int(a)
    elif o == "-t":
        enabletwisted = int(a)
    elif o == "-a":
        autostart = int(a)
    elif o == "-c":
        cobalt = True
    else:
        usage()
        sys.exit()

if len(argv) > 1:
    usage()
    sys.exit()
elif len(argv) == 1:
    WorkingDir = argv[0]
    os.chdir(WorkingDir)
elif len(argv) == 0:
    WorkingDir = os.getcwd()
    argv=[WorkingDir]

if(cobalt ==True):
    TryPreloadXenomai()

import __builtin__
if __name__ == '__main__':
    __builtin__.__dict__['_'] = lambda x: x

if enablewx:
    try:
        import wx, re
        from threading import Thread, currentThread
        from types import *
        havewx = True
    except:
        print "Wx unavailable !"
        havewx = False

    if havewx:
        app=wx.App(redirect=False)
        
        # Import module for internationalization
        import gettext
        
        CWD = os.path.split(os.path.realpath(__file__))[0]
        def Bpath(*args):
            return os.path.join(CWD,*args)
        
        # Get folder containing translation files
        localedir = os.path.join(CWD,"locale")
        # Get the default language
        langid = wx.LANGUAGE_DEFAULT
        # Define translation domain (name of translation files)
        domain = "Beremiz"

        # Define locale for wx
        loc = __builtin__.__dict__.get('loc', None)
        if loc is None:
            loc = wx.Locale(langid)
            __builtin__.__dict__['loc'] = loc
        # Define location for searching translation files
        loc.AddCatalogLookupPathPrefix(localedir)
        # Define locale domain
        loc.AddCatalog(domain)

        def unicode_translation(message):
            return wx.GetTranslation(message).encode("utf-8")

        if __name__ == '__main__':
            __builtin__.__dict__['_'] = wx.GetTranslation#unicode_translation
        
        defaulticon = wx.Image(Bpath("images", "brz.png"))
        starticon = wx.Image(Bpath("images", "icoplay24.png"))
        stopicon = wx.Image(Bpath("images", "icostop24.png"))
        
        class ParamsEntryDialog(wx.TextEntryDialog):
            if wx.VERSION < (2, 6, 0):
                def Bind(self, event, function, id = None):
                    if id is not None:
                        event(self, id, function)
                    else:
                        event(self, function)
            
            
            def __init__(self, parent, message, caption = "Please enter text", defaultValue = "", 
                               style = wx.OK|wx.CANCEL|wx.CENTRE, pos = wx.DefaultPosition):
                wx.TextEntryDialog.__init__(self, parent, message, caption, defaultValue, style, pos)
                
                self.Tests = []
                if wx.VERSION >= (2, 8, 0):
                    self.Bind(wx.EVT_BUTTON, self.OnOK, id=self.GetAffirmativeId())
                elif wx.VERSION >= (2, 6, 0):
                    self.Bind(wx.EVT_BUTTON, self.OnOK, id=self.GetSizer().GetItem(3).GetSizer().GetAffirmativeButton().GetId())
                else:
                    self.Bind(wx.EVT_BUTTON, self.OnOK, id=self.GetSizer().GetItem(3).GetSizer().GetChildren()[0].GetSizer().GetChildren()[0].GetWindow().GetId())
            
            def OnOK(self, event):
                value = self.GetValue()
                texts = {"value" : value}
                for function, message in self.Tests:
                    if not function(value):
                        message = wx.MessageDialog(self, message%texts, _("Error"), wx.OK|wx.ICON_ERROR)
                        message.ShowModal()
                        message.Destroy()
                        return
                self.EndModal(wx.ID_OK)
                event.Skip()
            
            def GetValue(self):
                return self.GetSizer().GetItem(1).GetWindow().GetValue()
            
            def SetTests(self, tests):
                self.Tests = tests
        
        class BeremizTaskBarIcon(wx.TaskBarIcon):
            TBMENU_START = wx.NewId()
            TBMENU_STOP = wx.NewId()
            TBMENU_CHANGE_NAME = wx.NewId()
            TBMENU_CHANGE_PORT = wx.NewId()
            TBMENU_CHANGE_INTERFACE = wx.NewId()
            TBMENU_LIVE_SHELL = wx.NewId()
            TBMENU_WXINSPECTOR = wx.NewId()
            TBMENU_CHANGE_WD = wx.NewId()
            TBMENU_QUIT = wx.NewId()
            
            def __init__(self, pyroserver, level):
                wx.TaskBarIcon.__init__(self)
                self.pyroserver = pyroserver
                # Set the image
                self.UpdateIcon(None)
                self.level = level
                
                # bind some events
                self.Bind(wx.EVT_MENU, self.OnTaskBarStartPLC, id=self.TBMENU_START)
                self.Bind(wx.EVT_MENU, self.OnTaskBarStopPLC, id=self.TBMENU_STOP)
                self.Bind(wx.EVT_MENU, self.OnTaskBarChangeName, id=self.TBMENU_CHANGE_NAME)
                self.Bind(wx.EVT_MENU, self.OnTaskBarChangeInterface, id=self.TBMENU_CHANGE_INTERFACE)
                self.Bind(wx.EVT_MENU, self.OnTaskBarLiveShell, id=self.TBMENU_LIVE_SHELL)
                self.Bind(wx.EVT_MENU, self.OnTaskBarWXInspector, id=self.TBMENU_WXINSPECTOR)
                self.Bind(wx.EVT_MENU, self.OnTaskBarChangePort, id=self.TBMENU_CHANGE_PORT)
                self.Bind(wx.EVT_MENU, self.OnTaskBarChangeWorkingDir, id=self.TBMENU_CHANGE_WD)
                self.Bind(wx.EVT_MENU, self.OnTaskBarQuit, id=self.TBMENU_QUIT)
            
            def CreatePopupMenu(self):
                """
                This method is called by the base class when it needs to popup
                the menu for the default EVT_RIGHT_DOWN event.  Just create
                the menu how you want it and return it from this function,
                the base class takes care of the rest.
                """
                menu = wx.Menu()
                menu.Append(self.TBMENU_START, _("Start PLC"))
                menu.Append(self.TBMENU_STOP, _("Stop PLC"))
                if self.level==1:
                    menu.AppendSeparator()
                    menu.Append(self.TBMENU_CHANGE_NAME, _("Change Name"))
                    menu.Append(self.TBMENU_CHANGE_INTERFACE, _("Change IP of interface to bind"))
                    menu.Append(self.TBMENU_CHANGE_PORT, _("Change Port Number"))
                    menu.Append(self.TBMENU_CHANGE_WD, _("Change working directory"))
                    menu.AppendSeparator()
                    menu.Append(self.TBMENU_LIVE_SHELL, _("Launch a live Python shell"))
                    menu.Append(self.TBMENU_WXINSPECTOR, _("Launch WX GUI inspector"))
                menu.AppendSeparator()
                menu.Append(self.TBMENU_QUIT, _("Quit"))
                return menu
            
            def MakeIcon(self, img):
                """
                The various platforms have different requirements for the
                icon size...
                """
                if "wxMSW" in wx.PlatformInfo:
                    img = img.Scale(16, 16)
                elif "wxGTK" in wx.PlatformInfo:
                    img = img.Scale(22, 22)
                # wxMac can be any size upto 128x128, so leave the source img alone....
                icon = wx.IconFromBitmap(img.ConvertToBitmap() )
                return icon
            
            def OnTaskBarStartPLC(self, evt):
                if self.pyroserver.plcobj is not None: 
                    self.pyroserver.plcobj.StartPLC()
            
            def OnTaskBarStopPLC(self, evt):
                if self.pyroserver.plcobj is not None:
                    Thread(target=self.pyroserver.plcobj.StopPLC).start()
            
            def OnTaskBarChangeInterface(self, evt):
                dlg = ParamsEntryDialog(None, _("Enter the IP of the interface to bind"), defaultValue=self.pyroserver.ip_addr)
                dlg.SetTests([(re.compile('\d{1,3}(?:\.\d{1,3}){3}$').match, _("IP is not valid!")),
                               ( lambda x :len([x for x in x.split(".") if 0 <= int(x) <= 255]) == 4, _("IP is not valid!"))
                               ])
                if dlg.ShowModal() == wx.ID_OK:
                    self.pyroserver.ip_addr = dlg.GetValue()
                    self.pyroserver.Stop()
            
            def OnTaskBarChangePort(self, evt):
                dlg = ParamsEntryDialog(None, _("Enter a port number "), defaultValue=str(self.pyroserver.port))
                dlg.SetTests([(UnicodeType.isdigit, _("Port number must be an integer!")), (lambda port : 0 <= int(port) <= 65535 , _("Port number must be 0 <= port <= 65535!"))])
                if dlg.ShowModal() == wx.ID_OK:
                    self.pyroserver.port = int(dlg.GetValue())
                    self.pyroserver.Stop()
            
            def OnTaskBarChangeWorkingDir(self, evt):
                dlg = wx.DirDialog(None, _("Choose a working directory "), self.pyroserver.workdir, wx.DD_NEW_DIR_BUTTON)
                if dlg.ShowModal() == wx.ID_OK:
                    self.pyroserver.workdir = dlg.GetPath()
                    self.pyroserver.Stop()
            
            def OnTaskBarChangeName(self, evt):
                dlg = ParamsEntryDialog(None, _("Enter a name "), defaultValue=self.pyroserver.name)
                dlg.SetTests([(lambda name : len(name) is not 0 , _("Name must not be null!"))])
                if dlg.ShowModal() == wx.ID_OK:
                    self.pyroserver.name = dlg.GetValue()
                    self.pyroserver.Restart()
            
            def _LiveShellLocals(self):
                if self.pyroserver.plcobj is not None:
                    return {"locals":self.pyroserver.plcobj.python_runtime_vars}
                else:
                    return {}
            
            def OnTaskBarLiveShell(self, evt):
                from wx import py
                frame = py.crust.CrustFrame(**self._LiveShellLocals())
                frame.Show()
            
            def OnTaskBarWXInspector(self, evt):
                # Activate the widget inspection tool
                from wx.lib.inspection import InspectionTool
                if not InspectionTool().initialized:
                    InspectionTool().Init(**self._LiveShellLocals())

                wnd = wx.GetApp()
                InspectionTool().Show(wnd, True)
            
            def OnTaskBarQuit(self, evt):
                if wx.Platform == '__WXMSW__':
                    Thread(target=self.pyroserver.Quit).start()
                self.RemoveIcon()
                wx.CallAfter(wx.GetApp().ExitMainLoop)
            
            def UpdateIcon(self, plcstatus):
                if plcstatus is "Started" :
                    currenticon = self.MakeIcon(starticon)
                elif plcstatus is "Stopped":
                    currenticon = self.MakeIcon(stopicon)
                else:
                    currenticon = self.MakeIcon(defaulticon)
                self.SetIcon(currenticon, "Beremiz Service")

from runtime import PLCObject, PLCprint, ServicePublisher, MainWorker
import Pyro
import Pyro.core as pyro

if not os.path.isdir(WorkingDir):
    os.mkdir(WorkingDir)

def default_evaluator(tocall, *args, **kwargs):
    try:
        res=(tocall(*args,**kwargs), None)
    except Exception:
        res=(None, sys.exc_info())
    return res

class Server():
    def __init__(self, servicename, ip_addr, port, workdir, argv, autostart=False, statuschange=None, evaluator=default_evaluator, website=None):
        self.continueloop = True
        self.daemon = None
        self.servicename = servicename
        self.ip_addr = ip_addr
        self.port = port
        self.workdir = workdir
        self.argv = argv
        self.servicepublisher = None
        self.autostart = autostart
        self.statuschange = statuschange
        self.evaluator = evaluator
        self.website = website
        self.plcobj = PLCObject(self)
    
    def _to_be_published(self):
        return self.servicename is not None and \
               self.ip_addr is not None and \
               self.ip_addr != "localhost" and \
               self.ip_addr != "127.0.0.1"

    def PrintServerInfo(self):
        print(_("Pyro port :"), self.port)

        # Beremiz IDE detects LOCAL:// runtime is ready by looking
        # for self.workdir in the daemon's stdout.
        print(_("Current working directory :"), self.workdir)

        if self._to_be_published():
            print(_("Publishing service on local network"))

        sys.stdout.flush()


    def Loop(self,when_ready):
        while self.continueloop:
            self.Start(when_ready)
        
    def Restart(self):
        self.Stop()

    def Quit(self):
        self.continueloop = False
        if self.plcobj is not None:
            self.plcobj.StopPLC()
            self.plcobj.UnLoadPLC()
        self.Stop()

    def Start(self,when_ready):
        Pyro.config.PYRO_MULTITHREADED = 0
        pyro.initServer()
        self.daemon=pyro.Daemon(host=self.ip_addr, port=self.port)
        self.daemon.setTimeout(60)
        uri = self.daemon.connect(self.plcobj,"PLCObject")
    
        print "Pyro port :",self.port
        print "Pyro object's uri :",uri
        print "Current working directory :",self.workdir
        
        # Configure and publish service
        # Not publish service if localhost in address params
        self.daemon.setTimeout(60)
        self.daemon.connect(self.plcobj, "PLCObject")
        if self._to_be_published():
            self.servicepublisher = ServicePublisher.ServicePublisher()
            self.servicepublisher.RegisterService(self.servicename, self.ip_addr, self.port)
        
        when_ready()
        
        self.daemon.requestLoop()
        self.daemon.sock.close()
    
    def Stop(self):
        if self.plcobj is not None:
            self.plcobj.StopPLC()
        if self.servicepublisher is not None:
            self.servicepublisher.UnRegisterService()
            self.servicepublisher = None
        self.daemon.shutdown(True)

    def AutoLoad(self):
        self.plcobj.AutoLoad()
        if self.plcobj.GetPLCstatus()[0] == "Stopped":
            if autostart:
                self.plcobj.StartPLC()
        self.plcobj.StatusChange()

if enabletwisted:
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        try:
            from threading import Thread, currentThread
            if havewx:
                from twisted.internet import wxreactor
                wxreactor.install()
            from twisted.internet import reactor, task
            from twisted.python import log, util
            from nevow import rend, appserver, inevow, tags, loaders, athena
            from nevow.page import renderer
            
            havetwisted = True
        except:
            print "Twisted unavailable !"
            havetwisted = False

if havetwisted:
    
    xhtml_header = '''<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN"
"http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">
'''

    class PLCHMI(athena.LiveElement):
    
        initialised = False
    
        def HMIinitialised(self, result):
            self.initialised = True
        
        def HMIinitialisation(self):
            self.HMIinitialised(None)
    
    class DefaultPLCStartedHMI(PLCHMI):
        docFactory = loaders.stan(tags.div(render=tags.directive('liveElement'))[                                    
                                             tags.h1["PLC IS NOW STARTED"],
                                             ])
        
    class PLCStoppedHMI(PLCHMI):
        docFactory = loaders.stan(tags.div(render=tags.directive('liveElement'))[
                                             tags.h1["PLC IS STOPPED"],
                                             ])
    
    class MainPage(athena.LiveElement):
        jsClass = u"WebInterface.PLC"
        docFactory = loaders.stan(tags.div(render=tags.directive('liveElement'))[
                                                        tags.div(id='content')[                         
                                                        tags.div(render = tags.directive('PLCElement')),
                                                        ]])
        
        def __init__(self, *a, **kw):
            athena.LiveElement.__init__(self, *a, **kw)
            self.pcl_state = False
            self.HMI = None
            self.resetPLCStartedHMI()
        
        def setPLCState(self, state):
            self.pcl_state = state
            if self.HMI is not None:
                self.callRemote('updateHMI')
        
        def setPLCStartedHMI(self, hmi):
            self.PLCStartedHMIClass = hmi
        
        def resetPLCStartedHMI(self):
            self.PLCStartedHMIClass = DefaultPLCStartedHMI
        
        def getHMI(self):
            return self.HMI
        
        def HMIexec(self, function, *args, **kwargs):
            if self.HMI is not None:
                getattr(self.HMI, function, lambda:None)(*args, **kwargs)
        athena.expose(HMIexec)
        
        def resetHMI(self):
            self.HMI = None
        
        def PLCElement(self, ctx, data):
            return self.getPLCElement()
        renderer(PLCElement)
        
        def getPLCElement(self):
            self.detachFragmentChildren()
            if self.pcl_state:
                f = self.PLCStartedHMIClass()
            else:
                f = PLCStoppedHMI()
            f.setFragmentParent(self)
            self.HMI = f
            return f
        athena.expose(getPLCElement)

        def detachFragmentChildren(self):
            for child in self.liveFragmentChildren[:]:
                child.detach()
    
    class WebInterface(athena.LivePage):

        docFactory = loaders.stan([tags.raw(xhtml_header),
                                   tags.html(xmlns="http://www.w3.org/1999/xhtml")[
                                       tags.head(render=tags.directive('liveglue')),
                                       tags.body[
                                           tags.div[
                                                   tags.div( render = tags.directive( "MainPage" ))
                                                   ]]]])
        MainPage = MainPage()
        PLCHMI = PLCHMI
        
        def __init__(self, plcState=False, *a, **kw):
            super(WebInterface, self).__init__(*a, **kw)
            self.jsModules.mapping[u'WebInterface'] = util.sibpath(__file__, os.path.join('runtime', 'webinterface.js'))
            self.plcState = plcState
            self.MainPage.setPLCState(plcState)

        def getHMI(self):
            return self.MainPage.getHMI()
        
        def LoadHMI(self, hmi, jsmodules):
            for name, path in jsmodules.iteritems():
                self.jsModules.mapping[name] = os.path.join(WorkingDir, path)
            self.MainPage.setPLCStartedHMI(hmi)
        
        def UnLoadHMI(self):
            self.MainPage.resetPLCStartedHMI()
        
        def PLCStarted(self):
            self.plcState = True
            self.MainPage.setPLCState(True)
        
        def PLCStopped(self):
            self.plcState = False
            self.MainPage.setPLCState(False)
            
        def renderHTTP(self, ctx):
            """
            Force content type to fit with SVG
            """
            req = inevow.IRequest(ctx)
            req.setHeader('Content-type', 'application/xhtml+xml')
            return super(WebInterface, self).renderHTTP(ctx)

        def render_MainPage(self, ctx, data):
            f = self.MainPage
            f.setFragmentParent(self)
            return ctx.tag[f]

        def child_(self, ctx):
            self.MainPage.detachFragmentChildren()
            return WebInterface(plcState=self.plcState)
            
        def beforeRender(self, ctx):
            d = self.notifyOnDisconnect()
            d.addErrback(self.disconnected)
        
        def disconnected(self, reason):
            self.MainPage.resetHMI()
            #print reason
            #print "We will be called back when the client disconnects"
        
    if havewx:
        reactor.registerWxApp(app)
    website = WebInterface()
    site = appserver.NevowSite(website)
    
    website_port = 8009
    listening = False
    while not listening:
        try:
            reactor.listenTCP(website_port, site)
            listening = True
        except:
            website_port += 1
    print "Http interface port :",website_port
else:
    website = None

if havewx:
    from threading import Semaphore
    wx_eval_lock = Semaphore(0)
    main_thread = currentThread()

    def statuschange(status):
        wx.CallAfter(taskbar_instance.UpdateIcon,status)
        
    def wx_evaluator(obj, *args, **kwargs):
        tocall,args,kwargs = obj.call
        obj.res = default_evaluator(tocall, *args, **kwargs)
        wx_eval_lock.release()
        
    def evaluator(tocall, *args, **kwargs):
        global main_thread
        if(main_thread == currentThread()):
            # avoid dead lock if called from the wx mainloop 
            return default_evaluator(tocall, *args, **kwargs)
        else:
            o=type('',(object,),dict(call=(tocall, args, kwargs), res=None))
            wx.CallAfter(wx_evaluator,o)
            wx_eval_lock.acquire()
            return o.res
    
    pyroserver = Server(servicename, given_ip, port, WorkingDir, argv, autostart, statuschange, evaluator, website)
    taskbar_instance = BeremizTaskBarIcon(pyroserver, enablewx)
else:
    pyroserver = Server(servicename, given_ip, port, WorkingDir, argv, autostart, website=website)

# Exception hooks s
import threading, traceback
def LogMessageAndException(msg, exp=None):
    if exp is None:
        exp = sys.exc_info()
    if pyroserver.plcobj is not None:
        pyroserver.plcobj.LogMessage(0, msg + '\n'.join(traceback.format_exception(*exp)))
    else:
        print(msg)
        traceback.print_exception(*exp)


def LogException(*exp):
    LogMessageAndException("", exp)

sys.excepthook = LogException
def installThreadExcepthook():
    init_old = threading.Thread.__init__
    def init(self, *args, **kwargs):
        init_old(self, *args, **kwargs)
        run_old = self.run
        def run_with_except_hook(*args, **kw):
            try:
                run_old(*args, **kw)
            except (KeyboardInterrupt, SystemExit):
                raise
            except:
                sys.excepthook(*sys.exc_info())
        self.run = run_with_except_hook
    threading.Thread.__init__ = init
installThreadExcepthook()


#pyro thread position
pyro_thread_started = Lock()
pyro_thread_started.acquire()
pyro_thread = Thread(target=pyroserver.Loop,
                     kwargs=dict(when_ready=pyro_thread_started.release)) #may change to main loop?
pyro_thread.start()

# Wait for pyro thread to be effective
pyro_thread_started.acquire()

pyroserver.PrintServerInfo()


#start pyro thread seperately




if havetwisted or havewx:
    # pyro_thread=Thread(target=pyroserver.Loop)
    # pyro_thread.start()

    if havetwisted:
        reactor.run()
    elif havewx:
        app.MainLoop()
else:
    try :
        MainWorker.runloop(pyroserver.AutoLoad) ## should be changed to mainloop
    except KeyboardInterrupt,e:
        pass
pyroserver.Quit()
sys.exit(0)
