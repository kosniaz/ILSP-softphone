# $Id: registration.py 2171 2008-07-24 09:01:33Z bennylp $
#
# SIP account and registration sample. In this sample, the program
# will block to wait until registration is complete
#
# Copyright (C) 2003-2008 Benny Prijono <benny@prijono.org>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA 
#
import sys
import pjsua as pj
import os
import threading
import time

#from dotenv import load_dotenv
#load_dotenv(dotenv_path='.env')
SERVER= os.environ.get('SIP_PROXY_HOST','<host>')
PORT = os.environ.get('SIP_PROXY_PORT','<port>')
USER= os.environ.get('SIP_USER','<user>')
PASS= os.environ.get('SIP_PASS','<pass>')

def log_cb(level, str, len):
    
    print(str, end=' ')

current_call=None

class MyAccountCallback(pj.AccountCallback):
    sem = None

    def __init__(self, account):
        pj.AccountCallback.__init__(self, account)

    def on_incoming_call(self, call):
        global current_call 
        if current_call:
            call.answer(486, "Busy")
            return
            
        print("Incoming call from ", call.info().remote_uri)

        my_current_call = call

        call_cb = MyCallCallback(my_current_call)
        my_current_call.set_callback(call_cb)

        my_current_call.answer(180)
        answer="" 
        while answer!="a" and answer!="h":
            answer = input("enter a to answer, or h to reject")
            if answer=="a":
                my_current_call.answer(200)
                break
            elif answer=="h":
                my_current_call.answer(486,"Busy")
                break

           

    def wait(self):
        self.sem = threading.Semaphore(0)
        self.sem.acquire()

    def on_reg_state(self):
        if self.sem:
            if self.account.info().reg_status >= 200:
                self.sem.release()

class MyCallCallback(pj.CallCallback):

    def __init__(self, call=None):
        pj.CallCallback.__init__(self, call)

    # Notification when call state has changed
    def on_state(self):
        global current_call
        print("Call with", self.call.info().remote_uri, end=' ')
        print("is", self.call.info().state_text, end=' ')
        print("last code =", self.call.info().last_code, end=' ') 
        print("(" + self.call.info().last_reason + ")")
        
        if self.call.info().state == pj.CallState.DISCONNECTED:
            current_call = None
            print('Current call is', current_call)

    # Notification when call's media state has changed.
    def on_media_state(self):
        if self.call.info().media_state == pj.MediaState.ACTIVE:
            # Connect the call to sound device
            call_slot = self.call.info().conf_slot
            pj.Lib.instance().conf_connect(call_slot, 0)
            pj.Lib.instance().conf_connect(0, call_slot)
            print("Media is now active")
        else:
            print("Media is inactive")

lib = pj.Lib()

try:
    lib.init(log_cfg = pj.LogConfig(level=4, callback=log_cb))
    lib.create_transport(pj.TransportType.UDP, pj.TransportConfig(5080))
    lib.start()

    domain=SERVER+":"+PORT
    acc = lib.create_account(pj.AccountConfig(domain=SERVER+":"+PORT, username=USER, password=PASS ))

    acc_cb = MyAccountCallback(acc)
    acc.set_callback(acc_cb)
    acc_cb.wait()

    print("\n")
    print("Registration complete, status=", acc.info().reg_status, \
          "(" + acc.info().reg_reason + ")")
    print("\nPress ENTER to make a call")
    sys.stdin.readline()
    if len(sys.argv)>1:
        current_call=acc.make_call(sys.argv[1], cb=MyCallCallback())
    else:
        print("no arguments passed, not making the call - going to passive mode instead.")
        print("waiting for a call")
    

    time.sleep(300)

    lib.destroy()
    lib = None

except pj.Error as e:
    print("Exception: " + str(e))
    lib.destroy()



