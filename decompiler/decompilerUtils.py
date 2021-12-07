# -*- coding: utf-8 -*-
"""
Created on Tue Dec  7 06:17:46 2021

@author: Asterisk
"""

from decompiler.decompilerSettings import DecompilerSettings

ENC_COND = "endif"
ENC_RNG = "endr"
ENC_NODE = "endf"

class Decompiler():
    def __init__(self,settings = None):
        if settings is None:
            settings = DecompilerSettings()
        self.settings = settings