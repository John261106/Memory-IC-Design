# -*- coding: utf-8 -*-
from com.sun.electric.database.topology import NodeInst
for m in NodeInst.getMethods():
    if "newvar" in m.getName().lower() or "addvar" in m.getName().lower():
        print(m.getName(), [p.getName() for p in m.getParameterTypes()])
