# -*- coding: utf-8 -*-
from com.sun.electric.technology import Technology
mocmos = Technology.findTechnology("mocmos")
m1_m2 = mocmos.findNodeProto("Metal-1-Metal-2-Con")
for p in m1_m2.getPorts():
    print("Port: %s" % p.getName())
