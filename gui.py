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
import urllib2
import ConfigParser
import gomparser
import subprocess
import logging
import re
import time
from wx import xrc
from string import Template

CONFIG_PIPE = "vlcpipe"
CONFIG_FILENAME = "config"
GUI_XRC_FILENAME = "gui.xrc"
CACHE = 30000

DEFAULT_CONFIG = {
    'id_email':"",
    'id_password':"",
    'id_save':"True",
    'stream_season':"2011gslsponsors2",
    'stream_quality':"SQTest",
    'stream_http_auth':"KPeerClient",
    'player_location':"",
    'now_record_and_play':"False",
    'later_record':"False",
    'later_record_time':"18:10",
    'later_record_timezone':"KST",
    'later_record_date_use':"False",
    'later_record_date':"",
    'later_record_and_play':"False",
    'record_save_location':"",
    'record_save_filename_scheme':"GSL-$d-$t.ogm" }


class GOMApp(wx.App):
    def OnInit(self):
        # load xml resources
        self.res = xrc.XmlResource(GUI_XRC_FILENAME)  # TODO: platform-specific resources, if need be
        self.frame = self.res.LoadFrame(None, 'GOMFrame')

        self.emailTxt = xrc.XRCCTRL(self.frame, "emailTxt")
        self.passTxt = xrc.XRCCTRL(self.frame, "passTxt")
        self.saveIdBox = xrc.XRCCTRL(self.frame, "saveIdBox")
        self.nowWatchBtn = xrc.XRCCTRL(self.frame, "nowWatchBtn")
        self.nowRecordBtn = xrc.XRCCTRL(self.frame, "nowRecordBtn")
        self.nowRecordWatchBox = xrc.XRCCTRL(self.frame, "nowRecordWatchBox")
        self.laterRecordBox = xrc.XRCCTRL(self.frame, "laterRecordBox")
        self.laterHourCho = xrc.XRCCTRL(self.frame, "laterHourCho")
        self.laterMinuteCho = xrc.XRCCTRL(self.frame, "laterMinuteCho")
        self.laterTZCho = xrc.XRCCTRL(self.frame, "laterTZCho")
        self.laterRecordDateBox = xrc.XRCCTRL(self.frame, "laterRecordDateBox")
        self.laterRecordDatePkr = xrc.XRCCTRL(self.frame, "laterRecordDatePkr")
        self.laterRecordWatchBox = xrc.XRCCTRL(self.frame, "laterRecordWatchBox")
        self.statusTxt = xrc.XRCCTRL(self.frame, "statusTxt")

        self.qualityCho = xrc.XRCCTRL(self.frame, "qualityCho")
        self.seasonIdTxt = xrc.XRCCTRL(self.frame, "seasonIdTxt")
        self.httpAuthTxt = xrc.XRCCTRL(self.frame, "httpAuthTxt")
        self.playerLocTxt = xrc.XRCCTRL(self.frame, "playerLocTxt")
        self.saveLocTxt = xrc.XRCCTRL(self.frame, "saveLocTxt")
        self.filenameSchemeTxt = xrc.XRCCTRL(self.frame, "filenameSchemeTxt")

        # setup callbacks
        self.frame.Bind(wx.EVT_TEXT, self.OnTextChange, id=xrc.XRCID('emailTxt'))
        self.frame.Bind(wx.EVT_TEXT, self.OnTextChange, id=xrc.XRCID('passTxt'))
        self.frame.Bind(wx.EVT_CHECKBOX, self.OnCheckboxChange, id=xrc.XRCID('saveIdBox'))
        self.frame.Bind(wx.EVT_BUTTON, self.OnPlayStream, id=xrc.XRCID('nowWatchBtn'))
        self.frame.Bind(wx.EVT_BUTTON, self.OnSaveStream, id=xrc.XRCID('nowRecordBtn'))
        self.frame.Bind(wx.EVT_CHECKBOX, self.OnCheckboxChange, id=xrc.XRCID('nowRecordWatchBox'))
        self.frame.Bind(wx.EVT_CHECKBOX, self.OnCheckboxChange, id=xrc.XRCID('laterRecordBox'))
        self.frame.Bind(wx.EVT_CHOICE, self.OnRecordTimeChange, id=xrc.XRCID('laterHourCho'))
        self.frame.Bind(wx.EVT_CHOICE, self.OnRecordTimeChange, id=xrc.XRCID('laterMinuteCho'))
        self.frame.Bind(wx.EVT_CHOICE, self.OnRecordTimeChange, id=xrc.XRCID('laterTZCho'))
        self.frame.Bind(wx.EVT_CHECKBOX, self.OnCheckboxChange, id=xrc.XRCID('laterRecordDateBox'))
        ### date picker watcher
        self.frame.Bind(wx.EVT_CHECKBOX, self.OnCheckboxChange, id=xrc.XRCID('laterRecordWatchBox'))

        self.frame.Bind(wx.EVT_CHOICE, self.OnQualityChange, id=xrc.XRCID('qualityCho'))
        self.frame.Bind(wx.EVT_TEXT, self.OnTextChange, id=xrc.XRCID('seasonIdTxt'))
        self.frame.Bind(wx.EVT_TEXT, self.OnTextChange, id=xrc.XRCID('httpAuthTxt'))
        self.frame.Bind(wx.EVT_TEXT, self.OnTextChange, id=xrc.XRCID('playerLocTxt'))
        self.frame.Bind(wx.EVT_BUTTON, self.OnPlayerLocOpen, id=xrc.XRCID('playerLocBtn'))
        self.frame.Bind(wx.EVT_TEXT, self.OnTextChange, id=xrc.XRCID('saveLocTxt'))
        self.frame.Bind(wx.EVT_BUTTON, self.OnSaveLocOpen, id=xrc.XRCID('saveLocBtn'))
        self.frame.Bind(wx.EVT_TEXT, self.OnTextChange, id=xrc.XRCID('filenameSchemeTxt'))

        # load config
        def find_choice(control, val):
          i = 0
          for s in control.GetStrings():
            if s == val:
              return i
            i += 1
          return 0
        self.config = ConfigParser.RawConfigParser(defaults=DEFAULT_CONFIG)
        self.config.read(CONFIG_FILENAME)
        self.cfg = dict(self.config.items("DEFAULT"))
        self.emailTxt.SetValue(self.cfg["id_email"])
        self.passTxt.SetValue(self.cfg["id_password"])
        self.saveIdBox.SetValue("True" == self.cfg["id_save"])
        self.nowRecordWatchBox.SetValue("True" == self.cfg["now_record_and_play"])
        self.laterRecordBox.SetValue("True" == self.cfg["later_record"])
        time_list = self.cfg["later_record_time"].split(':')
        if len(time_list) == 2:
          self.laterHourCho.SetSelection(find_choice(self.laterHourCho, time_list[0]))
          self.laterMinuteCho.SetSelection(find_choice(self.laterMinuteCho, time_list[1]))
        self.laterTZCho.SetSelection(find_choice(self.laterTZCho, self.cfg["later_record_timezone"]))
        self.laterRecordDateBox.SetValue("True" == self.cfg["later_record_date_use"])
        self.laterRecordWatchBox.SetValue("True" == self.cfg["later_record_and_play"])

        ### recDateEn, recDate

        self.qualityCho.SetSelection(find_choice(self.qualityCho, self.cfg["stream_quality"]))
        self.seasonIdTxt.SetValue(self.cfg["stream_season"])
        self.httpAuthTxt.SetValue(self.cfg["stream_http_auth"])
        self.playerLocTxt.SetValue(self.cfg["player_location"])
        self.saveLocTxt.SetValue(self.cfg["record_save_location"])
        self.filenameSchemeTxt.SetValue(self.cfg["record_save_filename_scheme"])

        self.statusTxt.SetValue("Ready")

        ## GOM url
        self.gomStreamUrl = ""
        self.gomStreamTS = None

        ## Subprocesses
        self.process_curl = None
        self.process_vlc = None

        # show window
        self.frame.Fit()
        self.frame.Show(True)
        self.SetTopWindow(self.frame)
        return True

    def OnExit(self):
        # save config
        if self.cfg["id_save"] == "False":
            self.cfg["id_email"] = ""
            self.cfg["id_password"] = ""
        keys = self.cfg.keys()
        keys.sort()
        for key in keys:
          self.config.set("DEFAULT", key, self.cfg[key])
        self.config.write(open(CONFIG_FILENAME, 'wb'))

        self.TerminateSubprocesses()

    def OnCheckboxChange(self, event):
        tb = {
            xrc.XRCID('saveIdBox') : "id_save",
            xrc.XRCID('nowRecordWatchBox') : "now_record_and_play",
            xrc.XRCID('laterRecordBox') : "later_record",
            xrc.XRCID('laterRecordDateBox') : "later_record_date_use",
            xrc.XRCID('laterRecordWatchBox') : "later_record_and_play" }
        config_entry = tb[event.GetId()]
        self.cfg[config_entry] = str(event.GetEventObject().GetValue())

    def OnPlayerLocOpen(self, event):
        def_path = ""
        def_file = self.cfg["player_location"]
        if def_file and len(def_file)>0:
            def_path = os.path.dirname(os.path.abspath(def_file))
        name = wx.FileSelector("Player Location ...", default_path=def_path, default_filename=def_file, parent=self.frame)
        if name:
            self.playerLocTxt.SetValue(name)
            self.cfg["player_location"] = name

    def OnSaveLocOpen(self, event):
        def_path = self.cfg["record_save_location"]
        name = wx.DirSelector("Select stream save location ...", def_path, parent=self.frame)
        if name:
            self.saveLocTxt.SetValue(name)
            self.cfg["record_save_location"] = name

    def OnTextChange(self, event):
        tb = {
            xrc.XRCID('emailTxt') : "id_email",
            xrc.XRCID('passTxt') : "id_password",
            xrc.XRCID('seasonIdTxt') : "stream_season",
            xrc.XRCID('httpAuthTxt') : "stream_http_auth",
            xrc.XRCID('playerLocTxt') : "player_location",
            xrc.XRCID('saveLocTxt') : "record_save_location",
            xrc.XRCID('filenameSchemeTxt') : "record_save_filename_scheme" }
        config_entry = tb[event.GetId()]
        self.cfg[config_entry] = event.GetEventObject().GetValue()

    def OnQualityChange(self, event):
        self.cfg["stream_quality"] = self.qualityCho.GetStringSelection()

    def OnRecordTimeChange(self, event):
        self.cfg["later_record_time"] = (self.laterHourCho.GetStringSelection() + ":" +
                                         self.laterMinuteCho.GetStringSelection())
        self.cfg["later_record_timezone"] = self.laterTZCho.GetStringSelection()


    def GetStreamURL(self):
        now = time.time()
        if self.gomStreamTS and self.gomStreamTS + (5*60) > now:
          return self.gomStreamURL

        try:
            self.gomStreamURL = gomparser.retrieveGomURL(self.cfg["id_email"], self.cfg["id_password"],
                                                         self.cfg["stream_season"], self.cfg["stream_quality"])
        except gomparser.GomParserError, (err):
            self.statusTxt.SetValue(str(err))
            return None
        except urllib2.URLError, (err):
            self.statusTxt.SetValue(str(err))
            return None
        logging.debug("url=%s" % self.gomStreamURL)

        self.gomStreamTS = now
        return self.gomStreamURL

    def GetPlayerBinary(self):
        player = self.cfg["player_location"]
        if os.name == 'posix' and os.uname()[0] == 'Darwin' and player.endswith("VLC.app"):
            player += "/Contents/MacOS/VLC"
        return player

    def TerminateSubprocesses(self):
        if self.process_curl and self.process_curl.poll() == None:
          self.process_curl.kill()
        self.process_curl = None
        if self.process_vlc and self.process_vlc.poll() == None:
          self.process_vlc.terminate()
        self.process_vlc = None

    def OnSaveStream(self, event):
        # cleanup!
        self.TerminateSubprocesses()

        url = self.GetStreamURL()
        if url == None:
          return

        # Generate filename
        now = time.localtime(time.time())
        subs = { "d":time.strftime("%Y%m%d", now), "t":time.strftime("%H%M%S"), "s":self.cfg["stream_season"] }
        filename = Template(self.cfg["record_save_filename_scheme"]).substitute(subs)
        filename = self.cfg["record_save_location"] + "/" + filename

        # Generate the curl command
        subs = { "h":self.cfg["stream_http_auth"], "u":url, "f":filename }
        cmd = Template("curl -A '$h' \"$u\" > \"$f\"").substitute(subs)

        logging.debug("Executing curl: %s" % cmd)
        self.process_curl = subprocess.Popen(cmd, shell=True)

        time.sleep(2)
        if self.process_curl.poll() != None:
          logging.debug("curl quit pretty quick.. bailing.")

        # Generate player command
        player = self.GetPlayerBinary()
        subs = { "p":player, "f":filename }
        cmd = Template("$p \"stream://$f\"").substitute(subs)

        logging.debug("Executing VLC: %s" % cmd)
        self.process_vlc = subprocess.Popen(cmd, shell=True)


    def OnPlayStream(self, event):
        # cleanup!
        self.TerminateSubprocesses()

        url = self.GetStreamURL()
        if url == None:
          return

        # Generate the curl command
        subs = { "h":self.cfg["stream_http_auth"], "u":url, "f":CONFIG_PIPE }
        cmd = Template("curl -A '$h' \"$u\" > \"$f\"").substitute(subs)

        logging.debug("Executing curl: %s" % cmd)
        self.process_curl = subprocess.Popen(cmd, shell=True)

        # Generate player command
        player = self.GetPlayerBinary()
        subs = { "p":player, "f":CONFIG_PIPE }
        cmd = Template("$p \"stream://$f\"").substitute(subs)

        logging.debug("Executing VLC %s" % cmd)
        self.process_vlc = subprocess.Popen(cmd, shell=True)




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
    CONFIG_PIPE = config_dir + "/vlcpipe"

    # create the pipe
    if not os.path.exists(CONFIG_PIPE):
      os.mkfifo(CONFIG_PIPE)

    # Set appropriate config file defaults for the platform
    if is_mac:
        DEFAULT_CONFIG['player_location'] = "/Applications/VLC.app"
        DEFAULT_CONFIG['record_save_location'] = os.path.expandvars("$HOME/Downloads")
    elif os.name == 'posix':
        DEFAULT_CONFIG['player_location'] = "/usr/bin/vlc"
        DEFAULT_CONFIG['record_save_location'] = os.path.expandvars("$HOME")

    # On the mac, check if we're in a .app bundle, and if so,
    # pull our resources from the appropriate directory.
    if is_mac:
        if re.search(r'.*\.app/Contents/MacOS$', script_dir):
            GUI_XRC_FILENAME = script_dir + "/../Resources/" + GUI_XRC_FILENAME

    logging.debug("path: %s" % os.getcwd())
    logging.debug("scriptdir: %s" % script_dir)
    logging.debug("CONFIG_PIPE: %s" % CONFIG_PIPE)
    logging.debug("CONFIG_FILENAME: %s" % CONFIG_FILENAME)
    logging.debug("GUI_XRC_FILENAME: %s" % GUI_XRC_FILENAME)

    app = GOMApp(redirect=False)
    app.MainLoop()


