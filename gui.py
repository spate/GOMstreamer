# -*- coding: utf-8 -*-

'''
Copyright 2011 James Helferty

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

 http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
'''

import sys, os
import wx
import ConfigParser
import gomparser
import subprocess
import logging
import re
from wx import xrc

CONFIG_FILENAME = "config"
GUI_XRC_FILENAME = "gui.xrc"
CACHE = 30000

DEFAULT_CONFIG = {
    'email':"youremail@example.com",
    'password':"PASSWORD",
    'vlcloc':"",
    'ogmloc':"",
    'quality':"SQTest" }


class GOMApp(wx.App):
    def OnInit(self):
        # load xml resources
        self.res = xrc.XmlResource(GUI_XRC_FILENAME)  # TODO: platform-specific resources, if need be
        self.frame = self.res.LoadFrame(None, 'GOMFrame')

        self.email = xrc.XRCCTRL(self.frame, "email")
        self.pwd = xrc.XRCCTRL(self.frame, "password")
        self.vlcLoc = xrc.XRCCTRL(self.frame, "vlcLocation")
        self.ogmLoc = xrc.XRCCTRL(self.frame, "ogmLocation")
        self.strmUrl = xrc.XRCCTRL(self.frame, "streamUrl")
        self.strmQ = xrc.XRCCTRL(self.frame, "streamQuality")
        self.status = xrc.XRCCTRL(self.frame, "statusLog")

        # setup callbacks
        self.frame.Bind(wx.EVT_TEXT, self.OnTextChange, id=xrc.XRCID('email'))
        self.frame.Bind(wx.EVT_TEXT, self.OnTextChange, id=xrc.XRCID('password'))
        self.frame.Bind(wx.EVT_TEXT, self.OnTextChange, id=xrc.XRCID('vlcLocation'))
        self.frame.Bind(wx.EVT_TEXT, self.OnTextChange, id=xrc.XRCID('ogmLocation'))
        self.frame.Bind(wx.EVT_CHOICE, self.OnQualityChange, id=xrc.XRCID('streamQuality'))
        self.frame.Bind(wx.EVT_BUTTON, self.OnVlcLocOpen, id=xrc.XRCID('vlcButton'))
        self.frame.Bind(wx.EVT_BUTTON, self.OnOgmLocOpen, id=xrc.XRCID('ogmButton'))
        self.frame.Bind(wx.EVT_BUTTON, self.OnSaveStream, id=xrc.XRCID('saveButton'))
        self.frame.Bind(wx.EVT_BUTTON, self.OnPlayStream, id=xrc.XRCID('playButton'))

        # load config
        self.config = ConfigParser.SafeConfigParser(defaults=DEFAULT_CONFIG)
        self.config.read(CONFIG_FILENAME)
        self.cfg = dict(self.config.items("DEFAULT"))
        self.email.SetValue(self.cfg["email"])
        self.pwd.SetValue(self.cfg["password"])
        self.vlcLoc.SetValue(self.cfg["vlcloc"])
        self.ogmLoc.SetValue(self.cfg["ogmloc"])
        cfg_quality = self.cfg["quality"]
        i = 0
        for s in self.strmQ.GetStrings():
            if s == cfg_quality:
                self.strmQ.SetSelection(i)
            i += 1

        self.status.SetValue("Ready")

        # show window
        self.frame.Fit()
        self.frame.Show(True)
        self.SetTopWindow(self.frame)
        return True

    def OnExit(self):
        # save config
        self.config.set("DEFAULT", "email", self.cfg["email"])
        self.config.set("DEFAULT", "password", self.cfg["password"])
        self.config.set("DEFAULT", "vlcloc", self.cfg["vlcloc"])
        self.config.set("DEFAULT", "ogmloc", self.cfg["ogmloc"])
        self.config.set("DEFAULT", "quality", self.cfg["quality"])
        self.config.write(open(CONFIG_FILENAME, 'wb'))

    def OnVlcLocOpen(self, event):
        name = wx.FileSelector("VLC Location ...", parent=self.frame)
        if name:
            self.vlcLoc.SetValue(name)
            self.cfg["vlcloc"] = name

    def OnOgmLocOpen(self, event):
        name = wx.SaveFileSelector("Stream", ".ogm", "dump.ogm", parent=self.frame)
        if name:
            self.ogmLoc.SetValue(name)
            self.cfg["ogmloc"] = name

    def OnTextChange(self, event):
        tb = {
            xrc.XRCID('email') : "email",
            xrc.XRCID('password') : "password",
            xrc.XRCID('vlcLocation') : "vlcloc",
            xrc.XRCID('ogmLocation') : "ogmloc" }
        config_entry = tb[event.GetId()]
        self.cfg[config_entry] = event.GetEventObject().GetValue()

    def OnQualityChange(self, event):
        self.cfg["quality"] = self.strmQ.GetStringSelection()

    def OnSaveStream(self, event):
        try:
            url = gomparser.retrieveGomURL(self.cfg["email"], self.cfg["password"], self.cfg["quality"])
        except gomparser.GomParserError, (err):
            self.status.SetValue(str(err))
            return
        self.strmUrl.SetValue(url)

        # FIXME: Actually use user-specified VLC!
        cmd = gomparser.generateVLCCmd(None, url, CACHE, self.cfg["ogmloc"])
        self.status.SetValue("Executing %s" % cmd)
        subprocess.Popen(cmd, shell=True)

    def OnPlayStream(self, event):
        try:
            url = gomparser.retrieveGomURL(self.cfg["email"], self.cfg["password"], self.cfg["quality"])
        except gomparser.GomParserError, (err):
            self.status.SetValue(str(err))
            return
        self.strmUrl.SetValue(url)

        # FIXME: Actually use user-specified VLC!
        cmd = gomparser.generateVLCCmd(None, url, CACHE, None)
        self.status.SetValue("Executing %s" % cmd)
        subprocess.Popen(cmd, shell=True)


if __name__ == "__main__":
    # Uncomment the following line to enable debug output:
    #logging.getLogger().setLevel(logging.DEBUG)

    if os.name == 'posix' and os.uname()[0] == 'Darwin':
        is_mac = True
    else:
        is_mac = False

    # platform directories
    script_dir = os.path.dirname(os.path.abspath(__file__))

    if is_mac:
        # On the Mac, this is the preferred place to put config files:
        config_dir = os.path.expandvars('$HOME/Library/Application Support/GOMstreamer')
    elif os.name == 'posix':
        # On Linux, this is standard:
        config_dir = os.path.expandvars('$HOME/.GOMstreamer')

    # create config directory
    if not os.path.exists(config_dir):
        os.mkdir(config_dir, 0700)

    # set the config filename.
    CONFIG_FILENAME = config_dir + "/config"


    # On the mac, check if we're in a .app bundle, and if so,
    # pull our resources from the appropriate directory.
    if is_mac:
        if re.search(r'.*\.app/Contents/MacOS$', script_dir):
            GUI_XRC_FILENAME = script_dir + "/../Resources/" + GUI_XRC_FILENAME

    logging.debug("path: %s" % os.getcwd())
    logging.debug("scriptdir: %s" % script_dir)
    logging.debug("CONFIG_FILENAME: %s" % CONFIG_FILENAME)
    logging.debug("GUI_XRC_FILENAME: %s" % GUI_XRC_FILENAME)

    app = GOMApp(redirect=False)
    app.MainLoop()


