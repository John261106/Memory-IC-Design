from com.sun.electric.database.topology import NodeInst

for m in NodeInst.getDeclaredMethods():
    if "move" in m.getName().lower() or "pos" in m.getName().lower() or "geom" in m.getName().lower() or "loc" in m.getName().lower() or "modify" in m.getName().lower() or "center" in m.getName().lower() or "trans" in m.getName().lower():
        print(m.getName(), [p.getSimpleName() for p in m.getParameterTypes()])
