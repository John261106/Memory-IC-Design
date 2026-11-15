# scripts/trace_control_logic_nets.py
from com.sun.electric.technology import Technology
from com.sun.electric.database.hierarchy import Cell, Library, Export
from com.sun.electric.database import EditingPreferences
from com.sun.electric.tool.io.input import LibraryFiles
from com.sun.electric.tool.io import FileType
from com.sun.electric.util import TextUtils

def trace():
    jelib_path = "D:/Projects/Memory-IC-Design/src/Memory-IC-Design.jelib"
    url = TextUtils.makeURLToFile(jelib_path)
    ep = EditingPreferences(True, None)
    lib = LibraryFiles.readLibrary(ep, url, "Memory-IC-Design", FileType.JELIB, False)

    sch = lib.findNodeProto("Control_logic{sch}")

    # Map exports
    exp_map = {}
    eit = sch.getExports()
    while eit.hasNext():
        e = eit.next()
        print("Export dir:", dir(e))
        break

    # Map all transistors:
    nit = sch.getNodes()
    tx_list = []
    while nit.hasNext():
        n = nit.next()
        proto = n.getProto()
        pname = proto.getName() if proto else ""
        if "Transistor" in pname:
            w = 0.0
            l = 0.0
            model = ""
            vit = n.getVariables()
            while vit.hasNext():
                var = vit.next()
                k = str(var.getKey())
                if "ATTR_width" in k:
                    w = float(var.getObject())
                elif "ATTR_length" in k:
                    l = float(var.getObject())
                elif "SIM_spice_model" in k:
                    model = str(var.getObject())

            # Find connections
            pins = {}
            for pi in n.getPortInsts():
                pport = pi.getPortProto().getName()
                net = pi.getNet()
                net_name = net.getName() if net else "None"
                # Check if this net has an export
                if net in exp_map:
                    net_name = exp_map[net]
                pins[pport] = net_name
            tx_list.append((n.getName(), model, w, l, pins))

    tx_list.sort(key=lambda x: (int(x[0].split('@')[1]) if '@' in x[0] else 0, x[0]))
    print("\n--- ALL TRANSISTORS (with resolved nets) ---")
    for name, model, w, l, pins in tx_list:
        print("%s [%s W=%.1f L=%.1f]: gate=%s, d=%s, s=%s, b=%s" % (name, model, w, l, pins.get('g'), pins.get('d'), pins.get('s'), pins.get('b', 'None')))

if __name__ == "__main__":
    trace()
