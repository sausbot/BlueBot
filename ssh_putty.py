# -*- coding: utf-8 -*-
"""
Created on Sun Mar 22 16:22:19 2020

@author: Sausen Jessa
"""
from subprocess import Popen

Popen("powershell putty.exe pi@rpi1 -pw raspberry")
Popen("powershell putty.exe pi@rpi2 -pw raspberry")
Popen("powershell putty.exe pi@rpi3 -pw raspberry")
