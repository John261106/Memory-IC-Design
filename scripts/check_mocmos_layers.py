# -*- coding: utf-8 -*-
from com.sun.electric.technology import Technology
mocmos = Technology.findTechnology("mocmos")
print("mocmos node protos:")
nit = mocmos.getNodes()
while nit.hasNext():
    n = nit.next()
    print("  NodeProto: %s" % n.getName())
print("\nmocmos arc protos:")
ait = mocmos.getArcs()
while ait.hasNext():
    a = ait.next()
    print("  ArcProto: %s" % a.getName())
