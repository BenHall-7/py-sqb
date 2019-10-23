import yaml
import sys
import struct

def read_u16(io):
    return struct.unpack("<H", io.read(2))[0]

def read_s16(io):
    return struct.unpack("<h", io.read(2))[0]

def read_u32(io):
    return struct.unpack("<I", io.read(4))[0]

def read_u64(io):
    return struct.unpack("<Q", io.read(8))[0]

class Entry:
    def __init__(self, io):
        self.id = hex(read_u64(io))
        self.unk1 = read_u16(io)
        self.probability = read_u16(io)
        self.unk3 = read_s16(io)
        self.unk4 = read_s16(io)
        self.unk5 = read_u32(io)

class Seq:
    def __init__(self, io):
        self.id = hex(read_u64(io))
        self.unk1 = read_u16(io)
        count = read_u16(io)
        read_u32(io) #most likely padding

        self.entries = []
        for _ in range(0, count):
            self.entries.append(Entry(io))

class Sqb:
    def __init__(self, io):
        assert(io.read(4) == b"SQB\x00")
        self.unk = read_u16(io)
        count = read_u16(io)
        _size = read_u32(io)
        offsets = []

        for _ in range(0, count):
            offsets.append(read_u32(io))
        
        start_pos = io.tell()
        self.seqs = []
        
        for offset in offsets:
            io.seek(start_pos + offset)
            self.seqs.append(Seq(io))

if __name__ == "__main__":
    filename = sys.argv[1]
    sqb = None
    with open(filename, "rb") as i:
        sqb = Sqb(i)
    yaml_str = yaml.dump(sqb, indent=2)
    with open("out.yml", "w") as o:
        o.write(yaml_str)
    print("Complete")