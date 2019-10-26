import yaml
import sys
import struct

class HexInt(int): pass

MAGIC = b"SQB\x00"

def representer(dumper, data):
    return yaml.ScalarNode('tag:yaml.org,2002:int', "{0:#010x}".format(data))

def read_u16(io):
    return struct.unpack("<H", io.read(2))[0]

def read_s16(io):
    return struct.unpack("<h", io.read(2))[0]

def read_u32(io):
    return struct.unpack("<I", io.read(4))[0]

def read_u64(io):
    return struct.unpack("<Q", io.read(8))[0]

def write_u16(io, val):
    io.write(val.to_bytes(2, "little", signed=False))

def write_s16(io, val):
    io.write(val.to_bytes(2, "little", signed=True))

def write_u32(io, val):
    io.write(val.to_bytes(4, "little", signed=False))

def write_u64(io, val):
    io.write(val.to_bytes(8, "little", signed=False))

class Entry:
    def __init__(self, io):
        self.id = HexInt(read_u64(io))
        self.unk1 = read_u16(io)
        self.probability = read_u16(io)
        self.unk3 = read_s16(io)
        self.unk4 = read_s16(io)
        self.unk5 = read_u32(io)
    
    def write(self, io):
        write_u64(io, self.id)
        write_u16(io, self.unk1)
        write_u16(io, self.probability)
        write_s16(io, self.unk3)
        write_s16(io, self.unk4)
        write_u32(io, self.unk5) #padding?

class Seq:
    def __init__(self, io):
        self.id = HexInt(read_u64(io))
        self.unk1 = read_u16(io)
        count = read_u16(io)
        read_u32(io) #padding

        self.entries = []
        for _ in range(0, count):
            self.entries.append(Entry(io))
    
    def write(self, io):
        write_u64(io, self.id)
        write_u16(io, self.unk1)
        write_u16(io, len(self.entries))
        write_u32(io, 0)

        for entry in self.entries:
            entry.write(io)

class Sqb:
    def __init__(self, io):
        assert(io.read(4) == MAGIC)
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
    
    def write(self, io):
        io.write(MAGIC)
        write_u16(io, 1)

        table_len = len(self.seqs)
        table_size = 4 * table_len

        write_u16(io, table_len)
        write_u32(io, table_size)
        
        table_pos = io.tell()
        write_pos = table_pos + table_size
        first_write_pos = write_pos
        
        for seq in self.seqs:
            io.seek(table_pos)
            write_u32(io, write_pos - first_write_pos)
            io.seek(write_pos)
            seq.write(io)
            table_pos += 4
            write_pos = io.tell()

if __name__ == "__main__":
    if len(sys.argv) <= 1:
        print("py-sqb: sqb <----> yaml")
        sys.exit("Expected arg: <file> (either .sqb or .yml)")

    filename = sys.argv[1]
    
    if filename.endswith(".sqb"):
        print("dumping sqb...")
        obj = None
        with open(filename, "rb") as i:
            obj = Sqb(i)
        yaml.add_representer(HexInt, representer)
        yaml_str = yaml.dump(obj, indent=2)
        new_name = filename[:-3] + "yml"
        with open(new_name, "w") as o:
            o.write(yaml_str)
    elif filename.endswith(".yml"):
        print("creating sqb...")
        obj = None
        with open(filename, "r") as i:
            obj = yaml.load(i)
        new_name = filename[:-3] + "sqb"
        with open(new_name, "wb") as o:
            obj.write(o)
    else:
        sys.exit("unrecognized file type")
    
    print("Complete")