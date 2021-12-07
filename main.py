# -*- coding: utf-8 -*-
"""
Created on Sun Dec  5 02:41:22 2021

@author: Asterisk
"""
import sys; sys.path.insert(0, '../Leviathon')


import sys
import json
import argparse
import regex
import io
from pathlib import Path

from decompilerMain import main as decompiler
from decompilerMain import generateArgParse as decompilerArgs
from compilerMain import main as compiler
from compilerMain import generateArgParse as compilerArgs

def getHelp():
    hlp = io.StringIO("")
    dp = decompilerArgs()
    dp.print_help(hlp)
    hlp.write("\n\n")
    pp = compilerArgs()
    hlp2 = io.StringIO("")
    pp.print_help(hlp2)
    hlp.seek(0)
    hlp2.write(hlp.read())
    hlp2.seek(0)
    return hlp2.read()

class combinedParser(argparse.ArgumentParser):
    def print_help(self,file = sys.stdout):
        hlp = getHelp()
        file.write(hlp)

def generateArgParse():
    parser = combinedParser(description='Leviathon Compiler',add_help = False)
    parser.add_argument('input', nargs = 1, type=str, 
                        help='Project file to compile (.fand)')
    parser.add_argument('-h', '--help',action='help', help="Show this help message and exit", default=argparse.SUPPRESS)
    parser.add_argument('arguments', nargs=argparse.REMAINDER)
    return parser

def jsonParse(args):
    inputFile = args[0]
    argDict = json.read(inputFile)
    args = []
    for key,val in argDict.items():
        if key != "input":
            args.append("-" + key)
            args.append(val)
        else:
            args = [val] + args
    main(args)
    return

def getMode(inputFile):
    extension = Path(inputFile).suffix
    mapping = {".json":jsonParse,
         ".nack":compiler,".fand":compiler,
         ".thklst":decompiler,".thk":decompiler}
    if extension not in mapping:
        raise ValueError("%s is not a .thklst, .thk, .fand, .nack or .json file"%inputFile)
    return mapping[extension]

def main(arglist):
    parser = generateArgParse()    
    args = parser.parse_args(arglist)
    mode = getMode(args.input[0])
    mode(arglist)
    
if __name__ in "__main__":
    main(sys.argv[1:])