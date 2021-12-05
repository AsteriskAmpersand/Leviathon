# -*- coding: utf-8 -*-
"""
Created on Sun Dec  5 02:41:22 2021

@author: Asterisk
"""
import sys; sys.path.insert(0, '../Leviathon')


import sys
import json
import argparse
from pathlib import Path

from decompilerMain import main as decompiler
from compilerMain import main as compiler


def generateArgParse():
    parser = argparse.ArgumentParser(description='Leviathon Compiler')
    parser.add_argument('input', nargs = 1, type=str, 
                        help='Project file to compile (.fand)')
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
         ".thklist":decompiler,".thk":decompiler}
    if extension not in mapping:
        raise ValueError("%s is not a .thklst, .thk, .fand, .nack or .json file"%inputFile)
    return mapping[extension]

def main(arglist):
    parser = generateArgParse()    
    args = parser.parse_args(arglist)
    mode = getMode(args.input[0])
    mode(arglist)
    
if __name__ in "__main__":
    #main(["D:\Games SSD\MHW-AI-Analysis\InlineTest\em001.fand", "-verbose"])
    main(sys.argv[1:])