from com.sun.electric.tool.io.output import Spice
PrefClass = None
for c in Spice.getDeclaredClasses():
    if 'SpicePreferences' in c.getSimpleName():
        PrefClass = c
print('Found:', PrefClass)
for cons in PrefClass.getDeclaredConstructors():
    print('Constructor:', [p.getSimpleName() for p in cons.getParameterTypes()])
