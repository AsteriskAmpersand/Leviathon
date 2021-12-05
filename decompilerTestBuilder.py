# -*- coding: utf-8 -*-
"""
Created on Sun Dec  5 19:38:07 2021

@author: Asterisk
"""

from decompiler.decompiler import THKLDecompiler
from decompiler.decomilerSettings import DecompilerSettings
from pathlib import Path

def void(*args,**kwargs):
    pass
def testDecompile(folder,file):
    #print(folder)
    #print(file)
    ts = DecompilerSettings()
    ts.verbose = True
    ts.outputPath = folder
    ts.display = void
    #ts.statisticsOutputPath = r"D:\Games SSD\MHW-AI-Analysis\KushalaTest"
    THKLDecompiler(ts).read(file).writeFile()
    #print()

if __name__ in "__main__":
    root = r"D:\Games SSD\MHW\chunk\em"
    outRoot = Path(r"D:\Games SSD\MHW-AI-Analysis\Leviathon\tests\ingameFiles")
    def congealPaths(path):
        return  str(path.relative_to(root).parent).replace("\\","_")
    errors = []
    lst = list(Path(root).rglob("*.thklst"))
    #lst = list(map(Path,[
    #        r"D:\Games SSD\MHW\chunk\em\em105\00\data\em105.thklst",
    #        r"D:\Games SSD\MHW\chunk\em\ems003\00\data\ems003.thklst",
    #        r"D:\Games SSD\MHW\chunk\em\ems003\05\data\ems003.thklst",
    #        r"D:\Games SSD\MHW\chunk\em\ems060\00\data\ems060.thklst",
    #        r"D:\Games SSD\MHW\chunk\em\ems060\00\data\ems060_401.thklst",
    #        r"D:\Games SSD\MHW\chunk\em\ems060\01\data\ems060.thklst",
    #        r"D:\Games SSD\MHW\chunk\em\ems060\01\data\ems060_401.thklst"
    #        ]))
    for path in lst:
        p = congealPaths(path)
        s = path.stem
        (outRoot/p).mkdir(parents = True, exist_ok = True)
        try:
            testDecompile(str(outRoot/p),str(path))
        except:
            testDecompile(str(outRoot/p),str(path))
            try:
                testDecompile(str(outRoot/p),str(path))
            except:
                print ("Errored",path)
                errors.append(path)