from com.sun.electric.tool.drc import DRC
from com.sun.electric.tool.io.input import LibraryFiles
from com.sun.electric.tool.io import FileType
from com.sun.electric.util import TextUtils

for c in DRC.getDeclaredClasses():
    if "CheckDRCJob" in c.getName():
        print("Constructors of CheckDRCJob:")
        for cons in c.getDeclaredConstructors():
            print(" ", [p.getSimpleName() for p in cons.getParameterTypes()])
        for f in c.getDeclaredFields():
            print("  field:", f.getName(), f.getType().getSimpleName())
