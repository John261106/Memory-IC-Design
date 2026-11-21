from com.sun.electric.tool.io.output import CellModelPrefs
for m in CellModelPrefs.getDeclaredMethods():
    print(m.getName(), [p.getSimpleName() for p in m.getParameterTypes()])
for f in CellModelPrefs.getDeclaredFields():
    print(f.getName(), f.getType().getSimpleName())
