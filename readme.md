GOMstreamer Readme
=================

Introduction
------------
GOMstreamer is a Python utility allowing OSX and other Unix based OS users to watch and save GOMtv GSL streams. Note, when saving you are able to watch the streams in VLC as they are downloading, though this may require another instance of VLC to be loaded.

Requirements
------------
- Python 2.x.x
  with following libraries:
  - urllib2
  - cookielib
  - urllib
  - re
  - os
  - optparse
  - wx (for GUI)
- Media player capable of playing HTTP stream whose URL is passed through command line. (For example VLC player, MPlayer)

Usage
-----
### Getting Started ###
On Mac OS X or Linux:
    Run gui.sh

On Mac OS X, you have the option of bundling the GUI up so you no longer have to use the command line to start it. This will create a GOMstreamer.app that you can then drag into your /Applications directory if you so desire. To bundle up GOMstreamer:
    Run bundleapp.sh

### Standard Usage ###
Start the GOMstreamer GUI, and enter your GOMtv email and password into the appropriate fields. Then click either the "Play stream" or "Save stream" buttons to eiher play or save the current stream. To play a saved stream, open the file (default = `dump.ogm`) in any decent media player, like VLC.

### Advanced Usage ###
This version of GOMstreamer is a fork of the command-line version, and retains most of the same commandline options. Instead of having separate streamer and saver scripts, the two have been merged into a single gomparser.py:

### GOMparser parameters ###
    -h, --help            show this help message and exit
    -p PASSWORD, --password=PASSWORD
                          Password to your GOMtv account
    -e EMAIL, --email=EMAIL
                          Email your GOMtv account uses
    -q QUALITY, --quality=QUALITY
                          Stream quality to use: 'HQ', 'SQ' or 'SQTest'. Default
                          is 'SQTest'. This parameter is case sensitive.
    -c COMMAND, --command=COMMAND
                          Custom command to run
    -d CACHE, --buffer-time=CACHE
                          Cache size in [ms]
    -o OUTPUTFILE, --output=OUTPUTFILE
                          File to save stream to. If unspecified, the stream will
			  be shown instead of saved

### Usage with VLC player ###
GOMstreamer uses VLC player by default. In OSX, it requires VLC to be located in the `/Applications` folder while on other Unix based systems it requires it to be in your shell path (try to type `vlc --version` in terminal). When using the GUI, the option to specify VLC's location is currently ignored.

### Advanced usage with custom commands ###
One can also define a specific command for GOMstreamer to run. There are variables which will be filled in by the GOMstreamer one can utilize in his command. The variables are:

- `$url` = url of the stream retrieved by GOMstreamer
- `$cache` = cache size requested by the user to be used by media player

For example, the default VLC command used by GOMstreamer is:
`vlc "--http-caching=$cache" "$url"`  

Note that this functionality is currently unavailable when using the GUI.

Security
--------
GOMstreamer requires one's login information in order to retrieve the stream url. This information is sent to the GOMtv website over the insecure HTTP protocol, just like it would be if one used browser to start up the GOM Player.

WARNING: By entering your login and password into the GUI, these will be stored in plaintext on your hard drive, in locations that you may wish to confirm are not accessible by others. On Mac OS X, this is ~/Library/Application Support/GOMstreamer, and on Linux this is in ~/.GOMstreamer. Securing these directories is YOUR responsibility. Please take any necessary precautions! The authors of this program disclaim all liability for lost and stolen GOMtv accounts.

(We disclaim liability for everything else, too, while we're at it..)

