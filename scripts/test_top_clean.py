# Test updated routing in scripts/test_top_clean.py
from com.sun.electric.tool.io.input import LibraryFiles
from com.sun.electric.tool.io import FileType
from com.sun.electric.util import TextUtils
from com.sun.electric.database import EditingPreferences
from com.sun.electric.technology import Technology
from com.sun.electric.database.text import Setting
from com.sun.electric.tool.drc import Quick, DRC
from com.sun.electric.database.geometry import GeometryHandler
from com.sun.electric.tool.user import ErrorLogger
import java.lang.Double

print("Testing environment ready.")
