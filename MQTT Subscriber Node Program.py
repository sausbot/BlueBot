# -*- coding: utf-8 -*-
"""
Created on Wed Mar  4 15:34:00 2020

@author: sausbot
"""

#!/usr/bin/env python3

import paho.mqtt.client as mqtt
import threading
from datetime import datetime

dateTimeObj = datetime.now()
timeStampStr = dateTimeObj.strftime("%d-%b-%Y (%H:%M:%S.%f)")
file = open("Logging.txt","a")
file2 = open("SubLog.txt","a") 

file.write(timeStampStr)
file2.write(timeStampStr)

file.write("\n")
file2.write("\n")

file.flush()
file2.flush()

nut1 = [100,100,100]
nut2 = [100,100,100]
nut3 = [100,100,100]

prevTime = ['00:00:00','00:00:00','00:00:00']
newTime = ['00:00:00','00:00:00','00:00:00']

prevRoom = [0,0,0]
newRoom = [0,0,0]
count = [0,0,0]

incoming = []

# This is the Subscriber
def on_connect(client, userdata, flags, rc):
  print("Connected with result code "+str(rc))
  client.subscribe("testTopic")

def on_message(client, userdata, msg):
#  if msg.payload.decode() == "Hello world!":
#    print("Yes!")
#    client.disconnect()
#  else:
#    print ("what")
   message = msg.payload.decode()
   #print (message)
   incoming = message.split(' ') 
   #file.write(incoming)
   #file.flush()
   
   #t1 = threading.Thread(target=search_nut1, args=(incoming,)) 
   #t2 = threading.Thread(target=search_nut2, args=(incoming,)) 
   #t3 = threading.Thread(target=search_nut3, args=(incoming,))
   
   t1 = threading.Thread(target=search_for_nut, args=(incoming, 0,'NUT1', nut1,))
   t2 = threading.Thread(target=search_for_nut, args=(incoming, 1,'NUT2', nut2,))
   t3 = threading.Thread(target=search_for_nut, args=(incoming, 2,'NUT3', nut3,))

   # starting thread 1 
   t1.start() 
   # starting thread 2 
   t2.start() 
   t3.start()
  
   # wait until thread 1 is completely executed 
   t1.join() 
   # wait until thread 2 is completely executed 
   t2.join()
   t3.join()
  
   # both threads completely executed 
   # print("Done!") 

def search_for_nut (splitStr, index, nutName, nutArray):
   if splitStr[0] == 'ROOM1' and splitStr[1] == nutName:
           nutArray[0] = float (splitStr[5])
   elif splitStr[0] == 'ROOM2' and splitStr[1] == nutName:
           nutArray[1] = float (splitStr[5])
   elif splitStr [0] == 'ROOM3' and splitStr[1] == nutName:
           nutArray[2] = float (splitStr[5])
   
   try:        
       nutRoom = nutArray.index(min(nutArray))+1
       parse = '\nNUT {} {} TIME {}'.format(index+1, nutArray, splitStr[7])
       
       print (parse)
       file2.write(parse)
       file2.flush()
       
       if nutRoom == prevRoom [index] and count[index] > 1:
           count [index]-=1
           msg = "\nJKS WE ARE NOT IN A NEW ROOM for NUT {} {}".format(index+1,count)
           print(msg)
           file2.write(msg)
           file2.flush()
               
       if nutRoom != prevRoom [index] and splitStr[1] == nutName and nutArray[0] != 100 and nutArray[1] != 100 and nutArray[2] != 100:
           count[index] = count[index] + 1
           now = splitStr[7]
           msg = "\nNUT {} WE MAY BE IN A NEW ROOM {}".format(index+1,count[index])
           print(msg)
           file2.write(msg)
           file2.flush()
           
           if count[index] >= 12:
               prevRoom [index] = nutRoom
               prevTime [index] = newTime [index]
               newTime [index] = splitStr[7]
               count[index] = 0
               print ("NEW ROOM INITIALIZED")
           
               print ("\n")
               out = "NUT {} {} in ROOM {} START: {}\n".format(index+1, nutArray, nutRoom, newTime[index])
               print (out)
               file.write(out)
               file.flush()
               
           msg = "\nuofficial NUT {} {} MAY BE in ROOM {} TIME: {} PREVROOM: {}\n".format(index+1, nutArray, nutRoom, now, prevRoom[index])
           print(msg)
           file2.write(msg)
           file2.flush()
   except:
       pass
   
client1 = mqtt.Client()
client2 = mqtt.Client()
client3 = mqtt.Client()

#address of the first Pi
client1.connect("192.168.0.134",1883,60)
#address of the second Pi
client2.connect("192.168.0.124",1883,60)
#address of the third Pi
client3.connect("192.168.0.155",1883,60)

client1.on_connect = on_connect
client1.on_message = on_message

client2.on_connect = on_connect
client2.on_message = on_message

client3.on_connect = on_connect
client3.on_message = on_message

client1.loop_start()
client2.loop_start()
client3.loop_start()