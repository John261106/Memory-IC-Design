from com.sun.electric.database.hierarchy import Cell

for m in Cell.getDeclaredMethods():
    if "move" in m.getName().lower() or "mod" in m.getName().lower() or "node" in m.getName().lower():
        print("Cell method:", m.getName(), [p.getSimpleName() for p in m.getParameterTypes()])
