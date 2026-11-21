# -*- coding: utf-8 -*-
from com.sun.electric.database.hierarchy import Cell
for m in dir(Cell):
    if "icon" in m.lower():
        print(m)
