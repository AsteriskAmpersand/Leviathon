# -*- coding: utf-8 -*-
"""
Created on Sun Oct 17 19:42:07 2021

@author: Asterisk
"""

import argparse
import sys
from pathlib import Path
from decompiler import THKDecompiler, THKLDecompiler, DecompilerSettings
from common.fexLayer import buildResolver


def generateArgParse():
    parser = argparse.ArgumentParser(description='Leviathon Decompiler')
    parser.add_argument('input', nargs=1, type=str,
                        help='File to decompile (.thk or thklst)')
    parser.add_argument('-nullShow', action='store_true',  # aliases=['sN'],
                        help='Keep empty nodes on decompiled output')
    parser.add_argument('-fixShow', action='store_true',  # aliases=['sN'],
                        help='Keep placeholder empty instruction for decompiler corrections')
    parser.add_argument('-lastShow', action='store_true',  # aliases=['kL'],
                        help='Keep the last node even if empty')
    parser.add_argument('-indexShow', action='store_true',  # aliases=['sI'],
                        help="Preserve each node's index in the file")
    parser.add_argument('-idShow', action='store_true',  # aliases=['sId'],
                        help='Preserve node Id in the file')
    # parser.add_argument('-xreferences', action='store_true',  # aliases=['xref'],
    #                    help='Adds a comment before each node listing all nodes that call it in the project')
    parser.add_argument('-noActions', action='store_true',  # aliases=['sId'],
                        help='Do not resolve actions to names')
    parser.add_argument('-raiseInvalidReferences', action='store_true',  # aliases=['iRef'],
                        help='Stop decompilation if an illegal call is found')
    parser.add_argument('-warningsHide', action='store_true',  # aliases=['w'],
                        help='Hide decompilation warnings as comments on offending segments')
    parser.add_argument('-keepRegisters', action='store_true',  # aliases=['reg'],
                        help="Keep registers as fixed identifiers during decompilation")
    parser.add_argument('-renameNackFiles', action='store_true',  # aliases=['ren'],
                        help='Rename .nack files to their function')
    parser.add_argument('-analyze', action='store_true',  # aliases=['ra'],
                        help='Analyse the code flow of the project and report on action, register and call usage')

    parser.add_argument('-outputPath', type=str, default=None,  # aliases=['o'],
                        help='Root folder where the decompiled files will be outputted')
    parser.add_argument('-analysisOutputPath', type=str, default=None,  # aliases=['ao'],
                        help='Folder to output the results of the code analysis')
    parser.add_argument('-fexty', type=str, default=None,  # aliases=['f'],
                        help='Forked Functional Extension input file')
    return parser


def buildSettings(args):
    settings = DecompilerSettings()
    settingsRemap = {"nullShow": "keepVoid", "lastShow": "keepLast", "indexShow": "forceIndex",
                     "fixShow": "genPlaceholder",
                     "idShow": "forceId",  # "xreferences": "listCrossreferences",
                     "noActions":"disableActionMapping",
                     "raiseInvalidReferences": "raiseInvalidReferences", "warningsHide": "supressWarnings",
                     "keepRegisters": "keepRegisters", "renameNackFiles": "functionAsThkName",
                     "analyze": "runCodeAnalysis", "outputPath": "outputPath",
                     "analysisOutputPath": 'statisticsOutputPath'}
    for setting in settingsRemap:
        setattr(settings, settingsRemap[setting], getattr(args, setting))
    return settings


def pickDecompiler(inputFile, settings):
    extension = Path(inputFile).suffix
    decompilers = {'.thklst': THKLDecompiler, ".thk": THKDecompiler}
    if extension not in decompilers:
        raise ValueError("%s is not a .thklst or .thk file" % inputFile)
    decomp = decompilers[extension]
    return decomp(settings)


def main(arglist):
    parser = generateArgParse()
    args = parser.parse_args(arglist)
    args.input = args.input[0]
    settings = buildSettings(args)
    decompiler = pickDecompiler(args.input, settings)
    if args.fexty:
        functionResolver = buildResolver(args.fexty)
        decompiler.read(args.input).writeFile(
            functionResolver=functionResolver)
    else:
        decompiler.read(args.input).writeFile()


if __name__ in "__main__":
    main(sys.argv[1:])
