# -*- coding: utf-8 -*-
"""
Created on Tue Nov  9 06:52:03 2021

@author: Asterisk
"""


def Autonumber(reserved=set()):
    i = 0
    while True:
        while i in reserved:
            i += 1
        yield i
        i += 1


def loggerLevel(func):
    def loggy(self, string, arguments=[]):
        message = func.__name__.upper()+": "+string % arguments
        f = self.log if func.__name__ in self.level else self.secondary
        f.append(message)
    return loggy


class CustomLogger():
    levels = ["critical", "error", "warning", "info", "debug"]

    def __init__(self):
        self.log = []
        self.secondary = []
        self.setLevel("warning")

    def setLevel(self, level):
        if level in self.levels:
            self.level = self.levels[:self.levels.index(level)+1]
        else:
            self.level = self.levels

    @loggerLevel
    def debug(self, message, arguments=[]): pass
    @loggerLevel
    def info(self, message, arguments=[]): pass
    @loggerLevel
    def warning(self, message, arguments=[]): pass
    @loggerLevel
    def error(self, message, arguments=[]): pass
    @loggerLevel
    def critical(self, message, arguments=[]): pass
