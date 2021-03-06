# -*- coding: utf-8 -*-
"""
Created on Mon Oct 11 18:25:32 2021

@author: Asterisk
"""
from pathlib import Path
try:
    from decompiler import THKLDecompiler, DecompilerSettings
except:
    import sys
    sys.path.append("..")
    from decompiler import THKLDecompiler, DecompilerSettings

if __name__ in "__main__":
    def void(*args, **kwargs):
        pass

    def testDecompile(folder, file):
        # print(folder)
        # print(file)
        ts = DecompilerSettings()
        ts.verbose = False
        ts.outputPath = folder
        folder.mkdir(parents=True, exist_ok=True)
        ts.display = void
        ts.forceId = False
        ts.forceIndex = False
        ts.keepVoid = False
        THKLDecompiler(ts).read(file).writeFile()
    root = r"D:\Games SSD\MHW\chunk\em"
    outRoot = Path(r"D:\Games SSD\MHW-AI-Analysis\Leviathon\tests\ingameFiles")

    def congealPaths(path):
        return str(path.relative_to(root).parent)
        return str(path.relative_to(root).parent).replace("\\", "_")
    errors = []
    lst = list(Path(root).rglob("*.thklst"))
    for path in lst:
        p = congealPaths(path)
        s = path.stem
        (outRoot/p).mkdir(parents=True, exist_ok=True)
        try:
            testDecompile(outRoot/"em"/p, str(path))
        except:
            print("Errored", path)
            raise
