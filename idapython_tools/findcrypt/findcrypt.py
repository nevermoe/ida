import struct
import idc, idautils
import ida_bytes
from consts import *

if idc.BADADDR == 0xFFFFFFFF:
    digits = 8
else:
    digits = 16

def convert_to_byte_array(const):
    byte_array = []
    if const["size"] == "B":
        byte_array = const["array"]
    elif const["size"] == "L":
        for val in const["array"]:
            byte_array += map(lambda x:ord(x), struct.pack("<L", val))
    elif const["size"] == "Q":
        for val in const["array"]:
            byte_array += map(lambda x:ord(x), struct.pack("<Q", val))
    return byte_array

def main():
    print("[*] loading crypto constants")
    for const in non_sparse_consts:
        const["byte_array"] = convert_to_byte_array(const)

    for start in idautils.Segments():
        print("[*] searching for crypto constants in %s" % idc.SegName(start))

        ea = start
        while ea < idc.SegEnd(start):
            bbbb = list(struct.unpack("BBBB", idc.GetManyBytes(ea, 4) or "AAAA"))
            for const in non_sparse_consts:
                if bbbb != const["byte_array"][:4]:
                    continue
                if map(lambda x:ord(x), idc.GetManyBytes(ea, len(const["byte_array"])) or list() ) == const["byte_array"]:
                    print(("0x%0" + str(digits) + "X: found const array %s (used in %s)") % (ea, const["name"], const["algorithm"]))
                    idc.MakeName(ea, const["name"])
                    if const["size"] == "B":
                        idc.MakeByte(ea)
                    elif const["size"] == "L":
                        idc.MakeDword(ea)
                    elif const["size"] == "Q":
                        idc.MakeQword(ea)
                    MakeArray(ea, len(const["array"]))
                    ea += len(const["byte_array"]) - 4
                    break
            ea += 4
            #print "ea: 0x%x " % ea

        ea = start
        if idc.GetSegmentAttr(ea, SEGATTR_TYPE) == 2:
            while ea < idc.SegEnd(start):
                d = idc.Dword(ea)
                for const in sparse_consts:
                    if d != const["array"][0]:
                        continue
                    tmp = ea + 4
                    for val in const["array"][1:]:
                        for i in range(8):
                            if idc.Dword(tmp + i) == val:
                                tmp = tmp + i + 4
                                break
                        else:
                            break
                    else:
                        print(("0x%0" + str(digits) + "X: found sparse constants for %s") % (ea, const["algorithm"]))
                        cmt = idc.GetCommentEx(idc.prev_head(ea), 0)
                        if cmt:
                            idc.CommentEx(idc.prev_head(ea), cmt + ' ' + const["name"], 0)
                        else:
                            idc.CommentEx(idc.prev_head(ea), const["name"], 0)
                        ea = tmp
                        break
                ea += 1
    print("[*] finished")

if __name__ == '__main__':
    main()
