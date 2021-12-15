# -*- coding: utf-8 -*-
"""
Created on Sun Dec  5 02:41:22 2021

@author: Asterisk
"""
from compilerMain import generateArgParse as compilerArgs
from compilerMain import main as compiler
from decompilerMain import generateArgParse as decompilerArgs
from decompilerMain import main as decompiler
from pathlib import Path
import io
import regex
import argparse
import json
import sys
import traceback
sys.path.insert(0, '../Leviathon')


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
    def print_help(self, file=sys.stdout):
        hlp = getHelp()
        file.write(hlp)


def generateArgParse():
    parser = combinedParser(description='Leviathon Compiler', add_help=False)
    parser.add_argument('input', nargs=1, type=str,
                        help='Project file to compile (.fand)')
    parser.add_argument('-h', '--help', action='help',
                        help="Show this help message and exit", default=argparse.SUPPRESS)
    parser.add_argument('arguments', nargs=argparse.REMAINDER)
    return parser


def jsonParse(args):
    inputFile = args[0]
    with open(inputFile) as inf:
        argDict = json.load(inf)
    args = []
    for key, val in argDict.items():
        if key != "input":
            args.append("-" + key)
            args.append(val)
        else:
            args = [val] + args
    main(args, False)
    return


def getMode(inputFile):
    extension = Path(inputFile).suffix
    mapping = {".json": jsonParse,
               ".nack": compiler, ".fand": compiler,
               ".thklst": decompiler, ".thk": decompiler}
    if extension not in mapping:
        raise ValueError(
            "%s is not a .thklst, .thk, .fand, .nack or .json file" % inputFile)
    return mapping[extension]


def main(arglist, display = True):
    if not arglist:
        arglist.append("-h")
    parser = generateArgParse()
    args = parser.parse_args(arglist)
    mode = getMode(args.input[0])
    try:
        mode(arglist)
        if display: print("Process Succeeded")
    except Exception:
        if not display:
            return
        print(traceback.format_exc())
        # or
        print(sys.exc_info()[2])
        print("Process Failed")


if __name__ in "__main__":
    try:
        main(sys.argv[1:])
    except ValueError:
        raise
    except:
        pass
    finally:
        input ("Press Any Key to Close")