# -*- coding: utf-8 -*-
"""
Created on Sat Oct 16 02:48:44 2021

@author: Asterisk
"""

ACTION = "action"
FUNCTION = "function"
CALL = "call"
UNSAFE = "unsafe"

REGISTER = "register"
IMPORTACT = "importActions".lower()
IMPORTLIB = "importLibrary".lower()
AS = "as"
RETURN = "return"
RESET = "reset"
REPEAT = "repeat"

DEF = "def"
ENDF = "endF".lower()
ENDF2 = "endDef".lower()
ENDF3 = "endFunction".lower()

CHANCE = "chance"
ELSEC2 = "elseChance".lower()
ELSEC = "elseC".lower()
ENDC = "endC".lower()
ENDCW = "endCWith".lower()
ENDCW2 = "endChanceWith".lower()
ENDC2 = "endChance".lower()

IF = "if"
ELSE = "else"
ELIF = "elif"
ENDIF = "endIf".lower()
ENDIFW = "endWith".lower()

ENDALL = "conclude"

DO_ACTION = "->"
DO_CALL = ">>"
DO_DIRECTIVE = "=>"
DO_NOTHING = r"\*&"
META = "@"

INDENT_REMOVE_ADD = [ELSE,ELIF,ELSEC,ELSEC2]
INDENT_ADD = [DEF, IF, CHANCE] + INDENT_REMOVE_ADD
INDENT_REMOVE = [ENDF,ENDF2,ENDF3, ENDC,ENDC2,ENDCW,ENDCW2, ENDIF,ENDIFW, ENDALL] + INDENT_REMOVE_ADD