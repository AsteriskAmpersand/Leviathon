# -*- coding: utf-8 -*-
import re
from monsterEnum import loadEntities

entityMap = loadEntities()

def writeFile(monId,contents):
    with open("./ActionDumps/em%03d.txt"%monId,"w") as outf:
        outf.write("\n".join(contents).replace(" ",""))

def ripId(line):
    #[ 11:32:01 ] Actions For 0
    m = re.match(r"\[[^\]]*\] Actions For (\d+)",line)
    if m:
        return int(m.groups()[0])
    return None


def breakFile(file):
    inside = True
    content = []
    monId = None
    for line in file:
        if not line.strip():
            if inside:
                inside = False
                if content and monId:
                    writeFile(monId,content)
                content = []
                monId = None
        else:
            if inside:
                content.append(line.strip())
            else:
                monId = ripId(line)
                inside = monId is not None
    if inside:
        inside = False
        if content and monId:
            writeFile(monId,content)
                
if __name__ in "__main__":
    with open("ActionDump.log","r") as inf:
        breakFile(inf)