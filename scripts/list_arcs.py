from com.sun.electric.technology import Technology

tech = Technology.findTechnology("mocmos")

print("Technology:", tech)

it = tech.getArcs()
while it.hasNext():
    arc = it.next()
    print("Arc:", arc.getName())