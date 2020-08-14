import struct

storedSize = 0x148
blockSize = 80

class PK8:
    def __init__(self, data):
        self.data = data

    def checkEncrypted(self):
        return self.data[0x70] != 0 and self.data[0xC0] != 0

    def getEncryptionConstant(self):
        return int(struct.unpack("I", bytes(self.data[0:4]))[0]) & 0xFFFFFFFF

    def advance(self, seed):
        return seed * 0x41C64E6D + 0x6073

    def Crypt(self):
        pkmWord = None
        seed = self.getEncryptionConstant()

        i = 8
        while i < storedSize:
            seed = self.advance(seed)
            pkmWord = (self.data[i + 1] << 8) | self.data[i]
            pkmWord = pkmWord ^ (seed >> 16)
            self.data[i + 1] = ((pkmWord & 0xFF00) >> 8) & 0xFF
            self.data[i] = pkmWord & 0xFF
            i += 2

    def getData(self):
        return self.data

    def getBlockPosition(self, index):
        blocks = [0, 1, 2, 3,
                0, 1, 3, 2,
                0, 2, 1, 3,
                0, 3, 1, 2,
                0, 2, 3, 1,
                0, 3, 2, 1,
                1, 0, 2, 3,
                1, 0, 3, 2,
                2, 0, 1, 3,
                3, 0, 1, 2,
                2, 0, 3, 1,
                3, 0, 2, 1,
                1, 2, 0, 3,
                1, 3, 0, 2,
                2, 1, 0, 3,
                3, 1, 0, 2,
                2, 3, 0, 1,
                3, 2, 0, 1,
                1, 2, 3, 0,
                1, 3, 2, 0,
                2, 1, 3, 0,
                3, 1, 2, 0,
                2, 3, 1, 0,
                3, 2, 1, 0,

                #duplicates of 0-7 to eliminate modulus
                0, 1, 2, 3,
                0, 1, 3, 2,
                0, 2, 1, 3,
                0, 3, 1, 2,
                0, 2, 3, 1,
                0, 3, 2, 1,
                1, 0, 2, 3,
                1, 0, 3, 2,]
        return blocks[index]

    def copyExistingData(self, source, beginning, end, output, outBeginning):
        j = outBeginning
        i = beginning

        while i < end:
            output[j] = source[i]
            j+=1
            i+=1
            #print("End: " + str(end) + "\ni: " + str(i))

    def copyData(self, source, beginning, end, output, outBeginning):
        j = outBeginning
        i = beginning

        while i < end:
            output.append(source[i])
            i+=1
            j+=1

    def printData(self):
        length = len(self.data)
        s = ""
        for x in range(len(self.data)):
            if self.data[x] < 16 and self.data[x] >= 0:
                s = s + "0"
            s = s + hex(self.data[x]) + " "
            if (x % 10) == 0 and x != 0:
                s = s + "\n"
        #print(s)

    def ShuffleArray(self, shuffleValue):
        index = shuffleValue * 4
        originalData = list()

        self.copyData(self.data, 0, storedSize, originalData, 0)

        #print("shuffle array invoked")
        block = 0
        while block < 4:
            offset = self.getBlockPosition(index + block)
            self.copyExistingData(originalData, 8 + blockSize * offset,
                8 + blockSize * offset + blockSize,
                self.data, 8 + blockSize * block)
            block += 1

        self.printData()

    def decrypt(self):
        if(self.checkEncrypted()):
            shuffleValue = (self.getEncryptionConstant() >> 13) & 31
            self.Crypt()
            self.ShuffleArray(shuffleValue)

    def getIV32(self):
        return int(struct.unpack("I", bytes(self.data[0x8C : 0x8C + 4]))[0])

    def getIVs(self):
        IV32 = self.getIV32()
        IV1 = (IV32 >> 5 * 0) & 0x1F
        IV2 = (IV32 >> 5 * 1) & 0x1F
        IV3 = (IV32 >> 5 * 2) & 0x1F
        IV4 = (IV32 >> 5 * 3) & 0x1F
        IV5 = (IV32 >> 5 * 4) & 0x1F
        IV6 = (IV32 >> 5 * 5) & 0x1F
        return IV1, IV2, IV3, IV4, IV5, IV6

    def getPID(self):
        return int(struct.unpack("I", bytes(self.data[0x1C : 0x1C + 4]))[0])

    def getSID(self):
        return int(struct.unpack("H", bytes(self.data[0xE : 0xE + 2]))[0])

    def getSpecies(self):
        return int(struct.unpack("H", bytes(self.data[0x8 : 0x8 + 2]))[0])

    def getOTName(self):
        return bytes(self.data[0xF8 : 0xF8 + 24])

    def getNickname(self):
        return bytes(self.data[0x58 : 0x58 + 24])

    def getTID(self):
        return int(struct.unpack("H", bytes(self.data[0xC : 0xC + 2]))[0])

    def getPSV(self):
        pid = self.getPID()
        return((pid >> 16 ^ (pid & 0xFFFF)) >> 4)

    def getTSV(self):
        return ((self.getTID() ^ self.getSID()) >> 4)

    def isShiny(self):
        return self.getPSV() == self.getTSV()

    def isEgg(self):
        return ((self.getIV32() >> 30) & 1) == 1
