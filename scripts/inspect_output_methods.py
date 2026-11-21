from com.sun.electric.tool.io.output import Output
for m in Output.getDeclaredMethods():
    print(m.getName(), [p.getSimpleName() for p in m.getParameterTypes()])
