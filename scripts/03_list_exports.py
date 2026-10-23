
# Electric VLSI 9.08 - List cell exports

from com.sun.electric.tool import Job

cell = Job.getUserInterface().getCurrentCell()

if cell is None:
    raise Exception("Open a schematic first.")

ports = cell.getPorts()
exports = []

while ports.hasNext():
    port = ports.next()
    name = str(port.getName())
    exports.append(name)
    print(name)

print("\n========== EXPORT SUMMARY ==========")
print("Total exports:", len(exports))

for prefix in ["WL", "WE", "RE", "SENSE", "BIT", "BITB"]:
    matches = [name for name in exports if name.startswith(prefix)]
    print(prefix, ":", len(matches), matches)

print("VDD exported:", "VDD" in exports)
print("GND exported:", "GND" in exports)
print("DATA exported:", "DATA" in exports)
print("PCB exported:", "PCB" in exports)
