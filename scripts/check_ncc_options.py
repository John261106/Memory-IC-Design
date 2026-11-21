# -*- coding: utf-8 -*-
from com.sun.electric.tool.ncc import Ncc, NccOptions
opts = NccOptions()
print("NccOptions fields:")
for f in dir(opts):
    if not f.startswith("_"):
        print("  %s = %s" % (f, getattr(opts, f)))
