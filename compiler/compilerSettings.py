class CompilerSettings():
    def __init__(self):
        self.verbose = False
        self.display = print

        self.entityMap = None
        self.functionResolver = None
        self.root = None
        self.thkMap = None
        self.inlineForeign = True
        self.foreignGlobal = False
        self.projectNames = "index"
        #self.deduplicateModules = False

        self.preprocessor = False

        self.verify = True
        self.forceCritical = False
        self.forceError = False
        self.symbols = False
        self.repeatedProperty = "Warning"

        self.thklistPath = "em000.thklst"
        self.symbolsPath = "symbols.mhpdb"
        self.outputRoot = ""