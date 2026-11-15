# scripts/check_ports.py
from com.sun.electric.technology import Technology
from com.sun.electric.tool.io import FileType
from com.sun.electric.util import TextUtils

def check():
    mocmos = Technology.findTechnology("mocmos")
    n_proto = mocmos.findNodeProto("N-Transistor")
    print("N-Transistor ports:")
    for p in n_proto.getPorts():
        print("  Port: %s" % p.getName())

    sch_tech = Technology.findTechnology("schematic")
    sch_n = sch_tech.findNodeProto("Transistor")
    print("Schematic Transistor ports:")
    for p in sch_n.getPorts():
        print("  Port: %s" % p.getName())

if __name__ == "__main__":
    check()
