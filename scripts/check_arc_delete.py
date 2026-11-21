from com.sun.electric.database.topology import ArcInst
from com.sun.electric.database.hierarchy import Cell

for m in ArcInst.getDeclaredMethods():
    if "del" in m.getName().lower() or "kill" in m.getName().lower() or "rem" in m.getName().lower():
        print("ArcInst method:", m.getName(), [p.getSimpleName() for p in m.getParameterTypes()])

for m in Cell.getDeclaredMethods():
    if "arc" in m.getName().lower():
        print("Cell arc method:", m.getName(), [p.getSimpleName() for p in m.getParameterTypes()])
