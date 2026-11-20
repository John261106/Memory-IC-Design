import struct

with open("com/sun/electric/database/geometry/PolyBase$PolyBaseTreeImpl.class", "rb") as f:
    data = bytearray(f.read())

cp_count = struct.unpack(">H", data[8:10])[0]
pos = 10
cp = [None] * cp_count
i = 1
while i < cp_count:
    tag = data[pos]
    pos += 1
    if tag == 1:
        length = struct.unpack(">H", data[pos:pos+2])[0]
        pos += 2
        val = data[pos:pos+length].decode("latin1")
        pos += length
        cp[i] = ("Utf8", val)
    elif tag in (3, 4):
        pos += 4
        cp[i] = ("Int/Float",)
    elif tag in (5, 6):
        pos += 8
        cp[i] = ("Long/Double",)
        i += 1
    elif tag in (7, 8):
        idx = struct.unpack(">H", data[pos:pos+2])[0]
        pos += 2
        cp[i] = ("Class/String", idx)
    elif tag in (9, 10, 11):
        cidx, ntidx = struct.unpack(">HH", data[pos:pos+4])
        pos += 4
        cp[i] = ("Ref", cidx, ntidx)
    elif tag == 12:
        nidx, tidx = struct.unpack(">HH", data[pos:pos+4])
        pos += 4
        cp[i] = ("NameAndType", nidx, tidx)
    elif tag in (15, 16, 17, 18, 19, 20):
        if tag == 15: pos += 3
        elif tag in (16, 19, 20): pos += 2
        else: pos += 4
        cp[i] = ("Misc", tag)
    i += 1

# Interfaces, fields
access_flags, this_class, super_class, interfaces_count = struct.unpack(">HHHH", data[pos:pos+8])
pos += 8 + 2 * interfaces_count

# Fields
fields_count = struct.unpack(">H", data[pos:pos+2])[0]
pos += 2
for _ in range(fields_count):
    f_acc, f_name, f_desc, f_attr_count = struct.unpack(">HHHH", data[pos:pos+8])
    pos += 8
    for _ in range(f_attr_count):
        a_name, a_len = struct.unpack(">HI", data[pos:pos+6])
        pos += 6 + a_len

# Methods
methods_count = struct.unpack(">H", data[pos:pos+2])[0]
pos += 2
for _ in range(methods_count):
    m_acc, m_name, m_desc, m_attr_count = struct.unpack(">HHHH", data[pos:pos+8])
    pos += 8
    for _ in range(m_attr_count):
        a_name, a_len = struct.unpack(">HI", data[pos:pos+6])
        pos += 6 + a_len

# Class attributes
class_attr_count = struct.unpack(">H", data[pos:pos+2])[0]
pos += 2
print("Class attributes count:", class_attr_count)
for _ in range(class_attr_count):
    a_name, a_len = struct.unpack(">HI", data[pos:pos+6])
    print("  Attribute:", cp[a_name][1], "len=", a_len)
    pos += 6 + a_len
print("Total bytes consumed:", pos, "File length:", len(data))
