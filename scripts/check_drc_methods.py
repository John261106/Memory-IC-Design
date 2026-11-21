import java.lang.reflect
from com.sun.electric.tool.drc import DRC
from com.sun.electric.tool.erc import ERC

print("DRC methods:")
for m in DRC.getDeclaredMethods():
    print(" ", m.getName(), [p.getSimpleName() for p in m.getParameterTypes()])

try:
    print("ERC methods:")
    for m in ERC.getDeclaredMethods():
        print(" ", m.getName(), [p.getSimpleName() for p in m.getParameterTypes()])
except:
    print("No ERC class found")
