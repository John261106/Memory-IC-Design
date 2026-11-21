from com.sun.electric.tool.io.output import Spice

for m in Spice.getDeclaredMethods():
    print(m.getName(), [p.getSimpleName() for p in m.getParameterTypes()])
