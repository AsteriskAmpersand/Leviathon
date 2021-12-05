# -*- coding: utf-8 -*-
"""
Created on Mon Sep 20 22:33:38 2021

@author: Asterisk
"""
import construct as c
from pathlib import Path

Header = c.Struct(
        "signature" / c.Int64ul,
        "count" / c.Int32sl,
        )

Entry = c.Struct(
        "thinkTableDataHash" / c.Int32ul,
        "rThinkTableHash" / c.Int32ul,
        "path" / c.IfThenElse(lambda this: this.rThinkTableHash,c.CString("utf8"),c.Computed(lambda this: ""))        
        )

signature = 86302593025
thinkTableDataHash = 1598592894 
thinkTableHash = 1655080001

ThkList = c.Struct(
    "header" / Header,
    "entries" / Entry[c.this.header.count],
    "data" / c.Int32ul[c.this.header.count],
    )

