from com.sun.electric.database.topology import ArcInst

for m in ArcInst.getDeclaredMethods():
    if "mod" in m.getName().lower() or "move" in m.getName().lower() or "geom" in m.getName().lower() or "update" in m.getName().lower() or "redo" in m.getName().lower():
        print(m.getName(), [p.getSimpleName() for p in m.getParameterTypes()])
