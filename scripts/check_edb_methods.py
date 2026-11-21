from com.sun.electric.database.hierarchy import EDatabase

for m in EDatabase.getDeclaredMethods():
    if "data" in m.getName().lower() or "curr" in m.getName().lower() or "set" in m.getName().lower() or "lib" in m.getName().lower():
        print(m.getName(), [p.getSimpleName() for p in m.getParameterTypes()])
