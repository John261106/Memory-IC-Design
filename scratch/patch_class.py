import struct

def patch():
    # Start fresh from original
    import subprocess
    subprocess.check_call(['jar', 'xf', 'C:/Users/USER/OneDrive/Desktop/electricBinaryFull-9.08.jar.original', 'com/sun/electric/database/geometry/PolyBase$PolyBaseTreeImpl.class'])
    
    with open("com/sun/electric/database/geometry/PolyBase$PolyBaseTreeImpl.class", "rb") as f:
        data = bytearray(f.read())

    magic, minor, major = struct.unpack(">IHH", data[:8])
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

    cp_end_pos = pos
    print("CP count before: %d, CP bytes end at: %d" % (cp_count, cp_end_pos))

    new_cp_bytes = bytearray()
    
    idx_utf8_helper = cp_count
    s1 = "com/sun/electric/database/geometry/PolyTreeHelper".encode("utf-8")
    new_cp_bytes += struct.pack(">BH", 1, len(s1)) + s1
    
    idx_class_helper = cp_count + 1
    new_cp_bytes += struct.pack(">BH", 7, idx_utf8_helper)
    
    idx_utf8_add = cp_count + 2
    s2 = "add".encode("utf-8")
    new_cp_bytes += struct.pack(">BH", 1, len(s2)) + s2
    
    idx_utf8_desc = cp_count + 3
    s3 = "(Lcom/sun/electric/database/geometry/PolyBase$PolyBaseTreeImpl;Lcom/sun/electric/database/geometry/PolyBase$PolyBaseTreeImpl;)Z".encode("utf-8")
    new_cp_bytes += struct.pack(">BH", 1, len(s3)) + s3
    
    idx_nat = cp_count + 4
    new_cp_bytes += struct.pack(">BHH", 12, idx_utf8_add, idx_utf8_desc)
    
    idx_methodref = cp_count + 5
    new_cp_bytes += struct.pack(">BHH", 10, idx_class_helper, idx_nat)
    
    new_cp_count = cp_count + 6
    print("New CP count: %d, methodref index: %d" % (new_cp_count, idx_methodref))
    
    header = data[:8] + struct.pack(">H", new_cp_count) + data[10:cp_end_pos] + new_cp_bytes
    rest = data[cp_end_pos:]
    data = header + rest
    
    pos = len(header)
    access_flags, this_class, super_class, interfaces_count = struct.unpack(">HHHH", data[pos:pos+8])
    pos += 8 + 2 * interfaces_count

    fields_count = struct.unpack(">H", data[pos:pos+2])[0]
    pos += 2
    for _ in range(fields_count):
        f_acc, f_name, f_desc, f_attr_count = struct.unpack(">HHHH", data[pos:pos+8])
        pos += 8
        for _ in range(f_attr_count):
            a_name, a_len = struct.unpack(">HI", data[pos:pos+6])
            pos += 6 + a_len

    methods_count = struct.unpack(">H", data[pos:pos+2])[0]
    pos += 2
    replaced = False
    for _ in range(methods_count):
        if replaced: break
        m_acc, m_name, m_desc, m_attr_count = struct.unpack(">HHHH", data[pos:pos+8])
        m_name_str = cp[m_name][1]
        m_desc_str = cp[m_desc][1]
        pos += 8
        for _ in range(m_attr_count):
            a_name, a_len = struct.unpack(">HI", data[pos:pos+6])
            a_name_str = cp[a_name][1]
            attr_header_pos = pos
            attr_body_pos = pos + 6
            pos += 6 + a_len
            if m_name_str == "add" and a_name_str == "Code":
                print("Found add Code at pos: %d, length: %d" % (attr_header_pos, a_len))
                new_code_body = bytearray()
                new_code_body += struct.pack(">HHI", 2, 2, 6)
                new_code_body += bytearray([0x2a, 0x2b, 0xb8, (idx_methodref >> 8) & 0xff, idx_methodref & 0xff, 0xac])
                new_code_body += struct.pack(">HH", 0, 0)
                
                new_attr_bytes = struct.pack(">HI", a_name, len(new_code_body)) + new_code_body
                data = data[:attr_header_pos] + new_attr_bytes + data[pos:]
                print("Replaced Code attribute! Old len: %d, New len: %d" % (a_len, len(new_code_body)))
                replaced = True
                break

    with open("com/sun/electric/database/geometry/PolyBase$PolyBaseTreeImpl.class", "wb") as f:
        f.write(data)
    print("Saved patched class file: %d bytes" % len(data))

patch()
