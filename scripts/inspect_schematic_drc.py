from com.sun.electric.tool.drc import Schematic

print("Schematic DRC class:", Schematic)
for m in Schematic.getDeclaredMethods():
    print(" method:", m.getName(), [p.getSimpleName() for p in m.getParameterTypes()])
for f in Schematic.getDeclaredFields():
    print(" field:", f.getName(), f.getType().getSimpleName())
