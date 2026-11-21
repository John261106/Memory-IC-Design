from com.sun.electric.tool.io.output import Spice
for c in Spice.getDeclaredClasses():
    if 'SpicePreferences' in c.getSimpleName():
        for f in c.getDeclaredFields():
            print(f.getName(), f.getType().getSimpleName())
        for m in c.getDeclaredMethods():
            print(m.getName(), [p.getSimpleName() for p in m.getParameterTypes()])
