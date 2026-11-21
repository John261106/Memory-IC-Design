# -*- coding: utf-8 -*-
from com.sun.electric.database.variable import Variable
for m in dir(Variable):
    if "new" in m.lower() or "inst" in m.lower():
        print(m)
for m in Variable.getDeclaredMethods():
    if m.getName() == "newInst":
        print("newInst:", [p.getName() for p in m.getParameterTypes()])
