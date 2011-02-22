# -*- coding: utf-8 -*-

'''
Copyright 2010 Simon Potter, Tomáš Heřman
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

import urllib2
import cookielib
import urllib
import StringIO
import re
import os
import sys
import logging
from optparse import OptionParser
from string import Template


class GomParserError(Exception):
    def __init__(self, value):
        self.parameter = value
    def __str__(self):
        return str(self.parameter)


def parseHTML(response, quality):
    # Seeing what we've received from GOMtv
    logging.debug("Response:")
    logging.debug(response)

    # Parsing through the live page for a link to the gox XML file.
    # Quality is simply passed as a URL parameter e.g. HQ, SQ, SQTest
    try:
        patternHTML = r"http://www.gomtv.net/gox[^;]+;"
        urlFromHTML = re.search(patternHTML, response).group(0)
        urlFromHTML = re.sub(r"\" \+ playType \+ \"", quality, urlFromHTML)
        urlFromHTML = re.sub(r"\"[^;]+;", "", urlFromHTML)
    except AttributeError:
        raise GomParserError("Error: Unable to find the majority of the GOMtv XML URL on the Live page.")

    # Finding the title of the stream, probably not necessary but
    # done for completeness
    try:
        patternTitle = r"this\.title[^;]+;"
        titleFromHTML = re.search(patternTitle, response).group(0)
        titleFromHTML = re.search(r"\"(.*)\"", titleFromHTML).group(0)
        titleFromHTML = re.sub(r"\"", "", titleFromHTML)
    except AttributeError:
        raise GomParserError("Error: Unable to find the stream title on the Live page.")

    return (urlFromHTML + titleFromHTML)

def parseStreamURL(response, quality):
    # Observing the GOX XML file containing the stream link
    logging.debug("GOX XML:")
    logging.debug(response)

    # The response for the GOX XML if an incorrect stream quality is chosen is 1002.
    if (response == "1002"):
        raise GomParserError("Error: A premium ticket is required to watch higher quality streams, please choose 'SQTest' instead.")

    # Grabbing the gomcmd URL
    try:
        streamPattern = r'<REF href="([^"]*)"/>'
        regexResult = re.search(streamPattern, response).group(1)
    except AttributeError:
        raise GomParserError("Error: Unable to find the gomcmd URL in the GOX XML file.")

    # If we are using a premium ticket, we don't need to parse the URL further
    # we just need to clean it up a bit
    if quality == 'HQ' or quality == 'SQ':
        regexResult = urllib.unquote(regexResult) # Unquoting URL entities
        regexResult = re.sub(r'&amp;', '&', regexResult) # Removing &amp;
        return regexResult

    # Collected the gomcmd URL, now need to extract the correct HTTP URL
    # from the string, only for 'SQTest'
    try:
        patternHTTP = r"(http%3[Aa].+)&quot;"
        regexResult = re.search(patternHTTP, regexResult).group(0)
        regexResult = urllib.unquote(regexResult) # Unquoting URL entities
        regexResult = re.sub(r'&amp;', '&', regexResult) # Removing &amp;
        regexResult = re.sub(r'&quot;', '', regexResult) # Removing &quot;
    except AttributeError:
        raise GomParserError("Error: Unable to extract the HTTP stream from the gomcmd URL.")

    return regexResult


# Options is a dict that must contain the following:
#  email:     youremail@example.com
#  password:  password
#  quality:   SQTest,SQ,HQ
def retrieveGomURL(email, password, quality):
    gomtvURL = "http://www.gomtv.net"
    gomtvLiveURL = gomtvURL + "/2011gslsponsors2/live/"
    gomtvSignInURL = gomtvURL + "/user/loginProcess.gom"
    values = {
             'cmd': 'login',
             'rememberme': '1',
             'mb_username': email,
             'mb_password': password
             }

    data = urllib.urlencode(values)
    cookiejar = cookielib.LWPCookieJar()
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookiejar))

    # Signing into GOMTV
    request = urllib2.Request(gomtvSignInURL, data)
    urllib2.install_opener(opener)
    response = urllib2.urlopen(request)

    if len(cookiejar) == 0:
        raise GomParserError("Authentification failed. Please check your login and password.")

    # Collecting data on the Live streaming page
    request = urllib2.Request(gomtvLiveURL)
    response = urllib2.urlopen(request)
    url = parseHTML(response.read(), quality)

    if len(url) == 0:
        raise GomParserError("Unable to find URL on the Live streaming page. Is the stream available?")

    logging.debug("Printing URL on Live page:")
    logging.debug(url)
    logging.debug("")

    # Grab the response of the URL listed on the Live page for a stream
    request = urllib2.Request(url)
    response = urllib2.urlopen(request)
    responseData = response.read()

    logging.debug("Response:")
    logging.debug(responseData)
    logging.debug("")

    # Find out the URL found in the response
    url = parseStreamURL(responseData, quality)

    if url == None:
        raise GomParserError("Unable to parse the URL to find the HTTP video stream.")

    return url


def generateVLCCmd(command, url, cache, outputFile):
    # Application locations and parameters for different operating systems.
    # May require changing on OSX, can't test.
    vlcOSX = '/Applications/VLC.app/Contents/MacOS/VLC "--http-caching=$cache" "$url"'
    vlcLinux = 'vlc "--http-caching=$cache" "$url"'

    if not command:
        # Determining which VLC command to use based on the OS that this script is being run on
        if os.name == 'posix' and os.uname()[0] == 'Darwin':
            command = Template(vlcOSX)
        else:
            command = Template(vlcLinux)  # On Windows, assuming VLC is in the PATH, this should work.


    commandArgs = {
                  'cache': cache,
                  'url': url
                  }
    cmd = command.substitute(commandArgs)
    if outputFile:
        cmd = cmd + " :demux=dump :demuxdump-file=\"" + outputFile + "\""
    cmd = cmd + " vlc://quit"

    return cmd


def main():

    # Collecting options parsed in from the command line
    parser = OptionParser()
    parser.add_option("-p", "--password", dest = "password", help = "Password to your GOMtv account")
    parser.add_option("-e", "--email", dest = "email", help = "Email your GOMtv account uses")
    parser.add_option("-q", "--quality", dest = "quality", help = "Stream quality to use: 'HQ', 'SQ' or 'SQTest'. Default is 'SQTest'. This parameter is case sensitive.")
    parser.add_option("-c", "--command", dest = "command", help = "Custom command to run")
    parser.add_option("-d", "--buffer-time", dest = "cache", help = "Cache size in [ms]")
    parser.add_option("-o", "--output", dest = "outputFile", help = "File to save stream to")

    # Setting stream quality default to 'SQTest'. May work for HQ and SQ but can't test.
    parser.set_defaults(quality = "SQTest")

    parser.set_defaults(cache = 30000)  # Caching 30s by default
    (options, args) = parser.parse_args()

    # Printing out parameters
    logging.debug("Email: %s" % options.email)
    logging.debug("Password: %s" % options.password)
    logging.debug("Quality: %s" % options.quality)
    logging.debug("Command: %s" % options.command)

    # Stopping if email and password are defaults found in play.sh/save.sh
    if options.email == "youremail@example.com" and options.password == "PASSWORD":
        print "Enter in your GOMtv email and password into play.sh and save.sh."
        print "This script will not work correctly without a valid account."
        sys.exit(1)

    try:
        # Log in and retrieve Gom stream URL
        url = retrieveGomURL(options.email, options.password, options.quality)

        # Generate VLC commandline
        cmd = generateVLCCmd(options.command, url, options.cache, options.outputFile)
    except GomParserError, (err):
        print err
        exit(1)

    print "Stream URL:", url
    print ""
    print "VLC command:", cmd
    print ""
    print "Starting VLC..."
    os.system(cmd)


# Actually run the script
if __name__ == "__main__":
    main()

