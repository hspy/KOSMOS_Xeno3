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


import time
import wx
import subprocess, ctypes
from threading import Timer, Lock, Thread, Semaphore
import os, sys
if os.name == 'posix':
    from signal import SIGTERM, SIGKILL

    
class outputThread(Thread):
    """
    Thread is used to print the output of a command to the stdout
    """
    def __init__(self, Proc, fd, callback=None, endcallback=None):
        Thread.__init__(self)
        self.killed = False
        self.finished = False
        self.retval = None
        self.Proc = Proc
        self.callback = callback
        self.endcallback = endcallback
        self.fd = fd

    def run(self):
        outchunk = None
        self.retval = None
        while outchunk != '' and not self.killed :
            outchunk = self.fd.readline()
            if self.callback : self.callback(outchunk)
        while self.retval is None and not self.killed :
            self.retval = self.Proc.poll()
            outchunk = self.fd.readline()
            if self.callback : self.callback(outchunk)
        while outchunk != '' and not self.killed :
            outchunk = self.fd.readline()
            if self.callback : self.callback(outchunk)
        if self.endcallback:
            try:
                err = self.Proc.wait()
            except:
                err = self.retval
            self.finished = True
            self.endcallback(self.Proc.pid, err)
        
class ProcessLogger:
    def __init__(self, logger, Command, finish_callback = None, 
                 no_stdout = False, no_stderr = False, no_gui = True, 
                 timeout = None, outlimit = None, errlimit = None,
                 endlog = None, keyword = None, kill_it = False, cwd = None):
        self.logger = logger
        if not isinstance(Command, list):
            self.Command_str = Command
            self.Command = []
            for i,word in enumerate(Command.replace("'",'"').split('"')):
                if i % 2 == 0:
                    word = word.strip()
                    if len(word) > 0:
                        self.Command.extend(word.split())
                else:
                    self.Command.append(word)
        else:
            self.Command = Command
            self.Command_str = subprocess.list2cmdline(self.Command)
        
        self.Command = map(lambda x: x.encode(sys.getfilesystemencoding()),
                           self.Command)
        
        self.finish_callback = finish_callback
        self.no_stdout = no_stdout
        self.no_stderr = no_stderr
        self.startupinfo = None
        self.errlen = 0
        self.outlen = 0
        self.errlimit = errlimit
        self.outlimit = outlimit
        self.exitcode = None
        self.outdata = []
        self.errdata = []
        self.keyword = keyword
        self.kill_it = kill_it
        self.finishsem = Semaphore(0)
        self.endlock = Lock()
        
        popenargs= {
               "cwd":os.getcwd() if cwd is None else cwd,
               "stdin":subprocess.PIPE, 
               "stdout":subprocess.PIPE, 
               "stderr":subprocess.PIPE}
        
        if no_gui == True and wx.Platform == '__WXMSW__':
            self.startupinfo = subprocess.STARTUPINFO()
            self.startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            popenargs["startupinfo"] = self.startupinfo
        elif wx.Platform == '__WXGTK__':
            popenargs["shell"] = False
        
        self.Proc = subprocess.Popen( self.Command, **popenargs )

        self.outt = outputThread(
                      self.Proc,
                      self.Proc.stdout,
                      self.output,
                      self.finish) 
        self.outt.start()

        self.errt = outputThread(
                      self.Proc,
                      self.Proc.stderr,
                      self.errors)
        self.errt.start()

        if timeout:
            self.timeout = Timer(timeout,self.endlog)
            self.timeout.start()
        else:
            self.timeout = None

    def output(self,v):
        self.outdata.append(v)
        self.outlen += 1
        if not self.no_stdout:
            self.logger.write(v)
        if (self.keyword and v.find(self.keyword)!=-1) or (self.outlimit and self.outlen > self.outlimit):
            self.endlog()
            
    def errors(self,v):
        self.errdata.append(v)
        self.errlen += 1
        if not self.no_stderr:
            self.logger.write_warning(v)
        if self.errlimit and self.errlen > self.errlimit:
            self.endlog()

    def log_the_end(self,ecode,pid):
        self.logger.write(self.Command_str + "\n")
        self.logger.write_warning(_("exited with status %s (pid %s)\n")%(str(ecode),str(pid)))

    def finish(self, pid,ecode):
        if self.timeout: self.timeout.cancel()
        self.exitcode = ecode
        if self.exitcode != 0:
            self.log_the_end(ecode,pid)
        if self.finish_callback is not None:
            self.finish_callback(self,ecode,pid)
        self.finishsem.release()

    def kill(self,gently=True):
        self.outt.killed = True
        self.errt.killed = True
        if wx.Platform == '__WXMSW__':
            PROCESS_TERMINATE = 1
            handle = ctypes.windll.kernel32.OpenProcess(PROCESS_TERMINATE, False, self.Proc.pid)
            ctypes.windll.kernel32.TerminateProcess(handle, -1)
            ctypes.windll.kernel32.CloseHandle(handle)
        else:
            if gently:
                sig=SIGTERM
            else:
                sig=SIGKILL
            try:
                os.kill(self.Proc.pid, sig)
            except:
                pass
        self.outt.join()
        self.errt.join()

    def endlog(self):
        if self.endlock.acquire(False):
            self.finishsem.release()
            if not self.outt.finished and self.kill_it:
               self.kill()

        
    def spin(self):
        self.finishsem.acquire()
        return [self.exitcode, "".join(self.outdata), "".join(self.errdata)]

