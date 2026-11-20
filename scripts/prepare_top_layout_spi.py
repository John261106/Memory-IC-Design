import os
import re

extracted_path = r"D:\Projects\Memory-IC-Design\spice\Top_layout_extracted.spi"
with open(extracted_path, "r") as f:
    lines = f.readlines()

# Filter out preliminary Level 1 models (lines between .OPTIONS and .MODEL DIFFCAP)
clean_lines = []
skip = False
for line in lines:
    if line.startswith(".OPTIONS") or line.startswith(".MODEL N ") or line.startswith(".MODEL P ") or line.startswith(".MODEL DIFFCAP"):
        skip = True
        continue
    if skip:
        if line.startswith("+"):
            continue
        else:
            skip = False
    
    # Replace model N and P with CMOSN and CMOSP
    # Mnmos... N L=... -> CMOSN
    line = re.sub(r'\bN\s+L=', 'CMOSN L=', line)
    line = re.sub(r'\bP\s+L=', 'CMOSP L=', line)
    clean_lines.append(line)

print("Total clean lines:", len(clean_lines))

# Write out Top_layout.spi
top_layout_path = r"D:\Projects\Memory-IC-Design\spice\Top_layout.spi"
with open(top_layout_path, "w") as f:
    f.write("*** Post-Layout Extracted Netlist for Top{lay}\n")
    f.write(".include D:\\Projects\\Memory-IC-Design\\lib\\tsmc018.lib\n\n")
    # write subcircuits up to before the top level cell
    f.writelines(clean_lines)

print("Written Top_layout.spi successfully")
