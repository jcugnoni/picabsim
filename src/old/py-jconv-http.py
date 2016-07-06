#!/usr/bin/python

import time
import BaseHTTPServer
import os
import urlparse
import subprocess

HOST_NAME = '' # leave blank to answer requests on all possible host names
PORT_NUMBER = 9999 # by default http port is 9999, change it as needed
IR_FOLDER = '/home/pi/IR' # directory where custom IR are saved
JACK_START_CMD='/home/pi/jackstart.sh'
JACK_CONNECTIONS=[['system:capture_1','jconvolver:In-1'],['jconvolver:Out-1','system:playback_1'],['jconvolver:Out-2','system:playback_2']]
CURRENT_IR_INDEX=0
JCNV_MAXMEM=3072
JCNV_PART=256
JCNV_GAIN=0.5
JCNV_R_DLY=0
JCNV_L_DLY=1
JCNV_LEN=0

# HTML INTERFACE HEADER, until IR list item
HTML_HEADER = """
<html>
<head>
<meta content="text/html; charset=ISO-8859-1"
http-equiv="content-type">
<title></title>
</head>
<body>
<p> Please select impulse response: </p>
<form method="get" action="IR" name="FormIR">
<select size="8" name="IRList">
"""
# HTML INTERFACE FOOTER
HTML_FOOTER = """
</select>
<br>
<button name="SetIR" value="1">Set IR</button>
<button name="Restart" value="1">(Re)Start Engine</button><br>
</form>
<p> Press OK to set IR from list. 
If needed, restart engine.</p>
<br>
</body>
</html>
"""

def get_IR_list():
    """ return a list of IR (with .wav) extension """
    lst=os.listdir(IR_FOLDER)
    irlst=[]
    for item in lst:
      if item.endswith('.wav'):
        irlst.append(item)
    return irlst

def write_jconv_config():
   lst=get_IR_list()
   print lst
   impulsefile=lst[CURRENT_IR_INDEX]
   print "setting config for %s"%(impulsefile)
   impulsepath=os.path.join(IR_FOLDER,impulsefile)
   print "full path to impulse file: %s"%(impulsepath)
   config_path=impulsepath+'.conf'
   print "full path of config fil: %s"%(config_path)
   if not(os.path.exists(config_path)):
     fid=open(config_path,'w')
     fid.write('/cd %s \n'%(IR_FOLDER))
     fid.write('/convolver/new    1    2         %s      %s          1.0 \n'%(JCNV_PART,JCNV_MAXMEM))
     fid.write('/impulse/read    1   1   %f      %i       0       %i     1    %s \n'%(JCNV_GAIN,JCNV_L_DLY,JCNV_LEN,impulsefile))
     fid.write('/impulse/read    1   2   %f      %i       0       %i     1    %s \n'%(JCNV_GAIN,JCNV_R_DLY,JCNV_LEN,impulsefile))
     fid.close()
   return config_path

def set_impulse():
   print "Jack status & ports"
   out=os.system('jack_lsp')
   # check if jconvolver is running
   try:
     out = subprocess.check_output("ps -C jconvolver | grep -c jconvolver", shell=True).strip()
   except subprocess.CalledProcessError:
     out='0'
   if int(out)==0:
     print "jconvolver is not running"
     jconv_running=False
   elif int(out)>0:
     print "jconvolver is running"
     jconv_running=True
   else:
     print "Error getting jconvolver status"
   if jconv_running==True:
     print "Disconnect jconvolver & kill it"
     for connection in JACK_CONNECTIONS:
       os.system('jack_disconnect %s %s'%(connection[0],connection[1]))
     os.system('killall jconvolver')
   # write config and restart 
   config=write_jconv_config()   
   print "Restart jconvolver with config %s"%(config)
   os.system('jconvolver %s &'%(config))
   time.sleep(5)
   # reconnect jconvolver
   for connection in JACK_CONNECTIONS:
     os.system('jack_connect %s %s'%(connection[0],connection[1]))

def restart_engine():
   """ restart jconvolver or even jack if needed """    
   # get status of jack and start it again if needed
   print "Jack status & ports"
   out=os.system('jack_lsp')
   if out!=0:
     print "Jackd not responding: kill and restart jack"
     os.system('killall jackd')
     os.system(' %s &'%(JACK_START_CMD))
     time.sleep(20)
   # restart jconvolver and set it up
   set_impulse()
   
def process_request(url):
    global CURRENT_IR_INDEX
    urlobj=urlparse.urlsplit(url)
    args=urlparse.parse_qsl(urlobj.query)
    msg=''
    for arg in args:
      if arg[0]=='IRList':
        # set CURRENT_IR_INDEX
        idx=int(arg[1])
        if idx!=CURRENT_IR_INDEX:
          CURRENT_IR_INDEX=idx
          msg+=' IR set to %i; '%(idx)
      if arg[0]=='Restart':
        # restart engine
        msg+=' Restarting engine; '
        restart_engine()
      if arg[0]=='SetIR':
        # set IR to CURRENT_IR_INDEX
        msg+=' Set new impulse to %i; '%(CURRENT_IR_INDEX)
        set_impulse()
    return msg

class MyHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    def do_HEAD(s):
        s.send_response(200)
        s.send_header("Content-type", "text/html")
        s.end_headers()
    def do_GET(s):
        """Respond to a GET request."""
        # first: process GET arguments
        msg=process_request(s.path)
        # second: update interface
        s.send_response(200)
        s.send_header("Content-type", "text/html")
        s.end_headers()
        s.wfile.write(HTML_HEADER)
        # add IR from directory
        irlst=get_IR_list()
        for count in range(len(irlst)):
          s.wfile.write("""<option value="%i">%s</option>"""%(count,irlst[count]))
        s.wfile.write(HTML_FOOTER)
        # If someone went to "http://something.somewhere.net/foo/bar/",
        # then s.path equals "/foo/bar/".
        s.wfile.write("<p>You accessed path: %s</p>" % s.path)
        s.wfile.write("<p>Msg: %s</p>" % msg)
        s.wfile.write("</body></html>")

if __name__ == '__main__':
    restart_engine()    
    server_class = BaseHTTPServer.HTTPServer
    httpd = server_class((HOST_NAME, PORT_NUMBER), MyHandler)
    print time.asctime(), "Server Starts - %s:%s" % (HOST_NAME, PORT_NUMBER)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
    print time.asctime(), "Server Stops - %s:%s" % (HOST_NAME, PORT_NUMBER)
