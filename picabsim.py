#!/usr/bin/python

# -*- coding: utf-8 -*-
"""
@author: jcugnoni
"""


import os, sys, time
import urlparse
import subprocess
from pipes import quote
from flask import Flask, url_for, render_template,  request
import makeIR

## configuration and default variables, edit as needed

DEBUG=True

HOST_NAME = '' # leave blank to answer requests on all possible host names
PORT_NUMBER = 9999 # by default http port is 9999, change it as needed
#IR_FOLDER = '/home/pi/IR' # directory where custom IR are saved
IR_FOLDER = '/home/jcugnoni/Documents/Perso/piguitarix/picabsim/home/pi/IR' # directory where custom IR are saved
JACK_START_CMD='jackstart.sh' # script used to start jack if needed, should be in picabsim/script
# JACK connections: depends on your hardware, but with a 2 input, 2 output, this should work 
# format: list of pairs of ports. use jack_lsp to list active ports.
JACK_CONNECTIONS_MONO=[['system:capture_1','jconvolver:In-1'],
['system:capture_1','jconvolver:In-2'],
['jconvolver:Out-1','system:playback_1'],
['jconvolver:Out-2','system:playback_2']]
JACK_CONNECTIONS_STEREO=[['system:capture_1','jconvolver:In-1'],
['system:capture_2','jconvolver:In-2'],
['jconvolver:Out-1','system:playback_1'],
['jconvolver:Out-2','system:playback_2']]
JACK_CONNECTIONS=JACK_CONNECTIONS_MONO # default config is mono
JCONV_CONF='/tmp/picabsim-jconv.conf' # path to temporary convolver config file (write access needed)

# default values of main variables, stored as dictionnary "patch"
patch={
'STEREO':False,  # stereo mode (uses JACK CONNECTION STEREO if true else uses MONO connections)
'IR_INDEX_L':0,   # id of left IR
'IR_INDEX_R':0,   # id of right IR
'IR_FOLDER_R':IR_FOLDER,  # folder for right IR
'IR_FOLDER_L':IR_FOLDER,  # folder for right IR
'JCNV_MAXMEM':3072,  # max length of IR used in jconvolver => defines CPU load (lower=faster)
'JCNV_PART':256,  # jconvolver partition size, can be optimized for higher perf
'JCNV_GAIN_R':0.5, # IR gain R
'JCNV_GAIN_L':0.5, # IR gain L
'JCNV_DLY_R':0,  # IR Delay R
'JCNV_DLY_L':1  # IR Delay L
}
# store state variables for the IR manager
editor={
'IR_FOLDER':IR_FOLDER,
'IR_INDEX':0,
'IR_SELECT1':'',
'IR_SELECT2':'',
'LOWPASS':0,
'HIGHPASS':20000,
'DECAY_TIME':1000,
'MIX':0.5,
'NEW_IR':'NewIR.wav'
}

## main app code

### Main functions

def get_script_path():
    """ return the path to the scripts sub directory (wrt to application root path) """
    return os.path.join(os.path.dirname(os.path.realpath(sys.argv[0])),'scripts')

def chdir_str(oldpath,relpath):
	""" apply a relative directory change to an input path """
	if relpath.strip()=='..':
		return os.path.join(os.path.split(oldpath)[0:-1])[0]
	else:
		return os.path.join(oldpath,relpath)

def shellquote(s):
    """ escapes file names used in shell commands """
    return "'" + s.replace("'", "'\\''") + "'"

def get_dir_list(path):
    """ return subdirs of current folder"""
    lst=os.listdir(path)
    dirlst=[]
    for item in lst:
        if os.path.isdir(os.path.join(path,item)):
            dirlst.append(item)
    dirlst.sort()
    dirlst.insert(0,'..')
    return dirlst

def get_IR_list(path):
    """ return a list of IR (with .wav) extension """
    lst=os.listdir(path)
    irlst=[]
    for item in lst:
      if item.endswith('.wav'):
        irlst.append(item)
    irlst.sort()
    return irlst

def write_jconv_config(patch):
   """ write jconvolver config file with selected options"""
   if DEBUG:
      print "DEBUG: in write_jconv_config()"
   lstL=get_IR_list(patch['IR_FOLDER_L'])
   lstR=get_IR_list(patch['IR_FOLDER_R'])
   #print lst
   impulsefileL=lstL[patch['IR_INDEX_L']]
   impulsefileR=lstR[patch['IR_INDEX_R']]
   impulsepathL=shellquote(os.path.join(patch['IR_FOLDER_L'],impulsefileL))
   impulsepathR=shellquote(os.path.join(patch['IR_FOLDER_R'],impulsefileR))
   print "full path to impulse file R: %s"%(impulsepathR)
   print "full path to impulse file L: %s"%(impulsepathL)
   config_path=JCONV_CONF
   print "full path of config file: %s"%(config_path)
   fid=open(config_path,'w')
   #fid.write('/cd %s \n'%(IR_FOLDER)) not needed
   fid.write('/convolver/new    2    2         %s      %s          1.0 \n'% \
            (patch['JCNV_PART'],patch['JCNV_MAXMEM']))
   fid.write('/impulse/read    1   1   %f      %i       0       %i     1    %s \n'%(patch['JCNV_GAIN_L'],
             patch['JCNV_DLY_L'],0,impulsepathL))
   fid.write('/impulse/read    2   2   %f      %i       0       %i     1    %s \n'%(patch['JCNV_GAIN_R'],
             patch['JCNV_DLY_R'],0,impulsepathR))
   fid.close()
   return config_path

def set_impulse():
   """ set selected impulses and options. takes time as it restarts jconvolver"""
   if DEBUG:
       print "DEBUG: in restart_engine()"
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
   config=write_jconv_config(patch)   
   print "Restart jconvolver with config %s"%(config)
   os.system('jconvolver %s &'%(shellquote(config)))
   time.sleep(5)
   # reconnect jconvolver
   for connection in JACK_CONNECTIONS:
     os.system('jack_connect %s %s'%(connection[0],connection[1]))

def restart_engine():
   """ restart jconvolver or even jack if needed """    
   # get status of jack and start it again if needed
   if DEBUG:
      print "DEBUG: in restart_engine()"
   print "Jack status & ports"
   out=os.system('jack_lsp')
   if out!=0:
     print "Jackd not responding: kill and restart jack"
     os.system('killall jackd')
     script=os.path.join(get_script_path(),JACK_START_CMD.strip())
     os.system(' %s &'%(shellquote(script)))
     time.sleep(20)
   # restart jconvolver and set it up
   set_impulse()

def process_main(request):
   """ processes an http request, and trigger appropriate functions """
   global patch  # uses global dictionnary patch to store current settings
   msg=''
   if DEBUG:
       print "DEBUG in process_request()"
       print "Output: request.form"
       print request
       print request.form
   # app data update
   if 'SetDir1' in request.form:
      dirlst=get_dir_list(patch['IR_FOLDER_L'])
      relpath=dirlst[int(request.form['DirList1'])]
      newpath=chdir_str(patch['IR_FOLDER_L'],relpath)
      if DEBUG: 
		  print "Change IR path R to : "
		  print newpath
      patch['IR_FOLDER_L']=newpath
   if 'SetDir2' in request.form:
      dirlst=get_dir_list(patch['IR_FOLDER_R'])
      relpath=dirlst[int(request.form['DirList2'])]
      newpath=chdir_str(patch['IR_FOLDER_R'],relpath)
      if DEBUG: 
		  print "Change IR path R to : "
		  print newpath
      patch['IR_FOLDER_R']=newpath
   if ('SetIR1' in request.form) | ('SetIR2' in request.form) :
      patch['JCNV_DLY_L']=int(request.form['predelay1'])
      patch['JCNV_GAIN_L']=float(request.form['gain1'])
      patch['IR_INDEX_L']=int(request.form['IRList1'])
      patch['JCNV_DLY_R']=int(request.form['predelay2'])
      patch['JCNV_GAIN_R']=float(request.form['gain2'])
      patch['IR_INDEX_R']=int(request.form['IRList2'])
      set_impulse()
   if 'CopyIR1' in request.form:
      patch['JCNV_DLY_L']=int(request.form['predelay1'])
      patch['JCNV_GAIN_L']=float(request.form['gain1'])
      patch['IR_INDEX_L']=int(request.form['IRList1'])
      patch['JCNV_DLY_R']=patch['JCNV_DLY_L']
      patch['JCNV_GAIN_R']=patch['JCNV_GAIN_L']
      patch['IR_INDEX_R']=patch['IR_INDEX_L']
      patch['IR_FOLDER_R']=patch['IR_FOLDER_L']
      set_impulse()
   if 'CopyIR2' in request.form:
      patch['JCNV_DLY_R']=int(request.form['predelay2'])
      patch['JCNV_GAIN_R']=float(request.form['gain2'])
      patch['IR_INDEX_R']=int(request.form['IRList2'])
      patch['JCNV_DLY_L']=patch['JCNV_DLY_R']
      patch['JCNV_GAIN_L']=patch['JCNV_GAIN_R']
      patch['IR_INDEX_L']=patch['IR_INDEX_R']
      patch['IR_FOLDER_L']=patch['IR_FOLDER_R']
      set_impulse()
   if 'restart' in request.form:
      if request.form['monostereo']=='2':
         patch['STEREO']=True
         JACK_CONNECTIONS=JACK_CONNECTIONS_STEREO
      else:
         patch['STEREO']=False
         JACK_CONNECTIONS=JACK_CONNECTIONS_MONO
      restart_engine()
   return msg


def process_editor(request):
   """ processes an http request, and trigger appropriate functions """
   global editor  # uses global dictionnary patch to store current settings
   msg=''
   if DEBUG:
       print "DEBUG in process_editor()"
       print "Output: request.form"
       print request
       print request.form
   # app data update
   if 'SetDir' in request.form:
      dirlst=get_dir_list(editor['IR_FOLDER'])
      relpath=dirlst[int(request.form['DirList'])]
      newpath=chdir_str(editor['IR_FOLDER'],relpath)
      if DEBUG: 
		  print "Change IR path R to : "
		  print newpath
      editor['IR_FOLDER']=newpath
   if ('SelectIR1' in request.form):
      dirlst=get_dir_list(editor['IR_FOLDER'])
      editor['IR_INDEX']=int(request.form['IRList'])
      editor['IR_SELECT1']=dirlst[editor['IR_INDEX']]
   if ('SelectIR2' in request.form):
      dirlst=get_dir_list(editor['IR_FOLDER'])
      editor['IR_SELECT1']=dirlst[int(request.form['IRList'])]
   return msg


### FLASK WEB APP

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def mainGui():
    msg=''
    if request.method == 'POST':
        msg=process_main(request)
    pathL=patch['IR_FOLDER_L']
    pathR=patch['IR_FOLDER_R']
    dirlstL=get_dir_list(pathL)
    dirlstR=get_dir_list(pathR)
    irlstL=get_IR_list(pathL)
    irlstR=get_IR_list(pathR)
    idL=patch['IR_INDEX_L']
    idR=patch['IR_INDEX_R']
    if DEBUG:
        print "DEBUG: in mainGui()"
        print "Output: irlstR/L,dirlstR/L,idL/R,pathL/R,patch"
        print irlstR
        print irlstL
        print dirlstR
        print dirlstL
        print idL
        print idR
        print pathL
        print pathR
        print patch
        print "--------------------"
    return render_template('mainGUI.html',dirlstR=dirlstR,dirlstL=dirlstL,irlstR=irlstR,irlstL=irlstL,
                           gainR=patch['JCNV_GAIN_R'],gainL=patch['JCNV_GAIN_L'], 
                           dlyR=patch['JCNV_DLY_R'],dlyL=patch['JCNV_DLY_L'],
                           stereo=patch['STEREO'],idL=idL,idR=idR,msg=msg)
                           

@app.route('/edit', methods=['GET', 'POST'])
def editorGUI():
    msg=''    
    if request.method == 'POST':
        msg=process_editor(request)
    path=editor['IR_FOLDER']
    dirlst=get_dir_list(path)
    irlst=get_IR_list(path)
    id1=editor['IR_INDEX']
    if DEBUG:
        print "DEBUG: in editorGui()"
        print irlst
        print dirlst
        print id1
        print path
        print editor
        print "--------------------"
    return render_template('editorGUI.html',dirlst=dirlst,irlst=irlst,
                           id1=id1,msg=msg)

@app.route('/hello')
def hello_world():
    return 'Hello World!'

if __name__ == '__main__':
    app.run(host='0.0.0.0',port=PORT_NUMBER,debug=DEBUG)
