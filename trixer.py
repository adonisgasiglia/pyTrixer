# -*- coding: utf-8 -*-
__author__ = 'Adônis Gasiglia'

import argparse, os, pickle, sys, ConfigParser, math
from PIL import Image, ImageDraw, ImageFont

### AUXILIAR FUNCTIONS ###

def getKey0(item):
    return item[0]

def getKey1(item):
    return item[1]

def calcPixelLuminance(pixel):
    return pixel[0]*0.2126 + pixel[1]*0.7152 + pixel[2]*0.0722

def calcBlockLuminance(file,blockx,blocky,lumitable):
    im = Image.open(file)
    px = im.load()

    luminance = 0

    for x in xrange(blockx*lumitable.blockWidth,(blockx*lumitable.blockWidth)+lumitable.blockWidth):
        for y in xrange(blocky*lumitable.blockHeight,(blocky*lumitable.blockHeight)+lumitable.blockHeight):
            luminance += calcPixelLuminance(px[x,y])

    luminance = luminance/(lumitable.blockHeight*lumitable.blockWidth)

    return luminance

### LUMITABLE CLASS ###

class lumitable:

    def __init__(self,fontname,fontsize,range,blockheight,blockwidth):
        self.fontName = fontname
        self.fontSize = fontsize
        self.charRange = range
        self.charNumber = range[1] - range[0]
        self.blockHeight = blockheight
        self.blockWidth = blockwidth
        self.table = []

    def generateFontStrip(self):
        if self.fontName is not None:
            base = Image.new('RGBA', (self.charNumber*self.blockWidth,self.blockHeight), (255,255,255,255))

            txt = Image.new('RGBA', base.size, (255,255,255,0))

            fnt = ImageFont.truetype(("lumitables/" + self.fontName + '.ttf'), self.fontSize)
            d = ImageDraw.Draw(txt)

            for num in range(self.charRange[0],self.charRange[1]):
                pos = (num-self.charRange[0])*self.blockWidth
                d.text((pos,0), chr(num), font=fnt, fill=(0,0,0,255))

            out = Image.alpha_composite(base, txt)

            # write to stdout
            out.save(("lumitables/" + self.fontName + ".png"), "PNG")

            v_print(2,"Fontstrip generated!")

    def generateLuminanceTable(self):
        for block in xrange(0,self.charNumber):
            self.table.append([block+self.charRange[0],calcBlockLuminance("lumitables/" + self.fontName + ".png",block,0,self)])

        self.table.sort(key=getKey1)

        with open("lumitables/" + self.fontName + ".lut", 'wb') as f:
            pickle.dump(self, f)

        v_print(2,"Lumitable generated!")

### IMAGETABLE CLASS ###

class imagetable:
    def __init__(self,file,lumitable,colorMode):
        self.file = file

        self.image = Image.open(file)

        self.xBlocks = math.floor(self.image.size[0].__float__() / lumitable.blockWidth.__float__()).__int__()
        self.yBlocks = math.floor(self.image.size[1].__float__() / lumitable.blockHeight.__float__()).__int__()

        self.lumitable = lumitable

        self.colorMode = colorMode

        self.table = []

        if colorMode == "colors": ##### CONSERRRRRTAAAAAAAA
            self.colorTable = [[0 for x in range(self.xBlocks*3)] for x in range(self.yBlocks*3)]

        ready = 0.0
        total = self.xBlocks*self.yBlocks

        for x in range(0,self.xBlocks):
            for y in range(0,self.yBlocks):
                luminance = calcBlockLuminance(self.file,x,y,self.lumitable)
                if colorMode == "colors":
                    self.colorTable[x][y] = self.calcColorAverage(x,y,self.lumitable)
                found = False
                for i in self.table:
                    if i[0] == luminance:
                        i[1].append((x,y))
                        found = True
                        break
                if not found:
                    self.table.append([luminance,[(x,y)]])
                ready += 1.0
                v_print(2,"Generating imagetable: {0:.2f}%".format((ready/total)*100.0))

        self.table.sort(key=getKey0)

        v_print(2,"Imagetable generated!")

    def calcColorAverage(self,blockx,blocky,lumitable):
        im = Image.open(self.file)
        px = im.load()

        red = 0
        green = 0
        blue = 0

        for x in xrange(blockx*lumitable.blockWidth,(blockx*lumitable.blockWidth)+lumitable.blockWidth):
            for y in xrange(blocky*lumitable.blockHeight,(blocky*lumitable.blockHeight)+lumitable.blockHeight):
                red += px[x,y][0]
                green += px[x,y][1]
                blue += px[x,y][2]

        red = red / (lumitable.blockHeight*lumitable.blockWidth)
        green = green / (lumitable.blockHeight*lumitable.blockWidth)
        blue = blue / (lumitable.blockHeight*lumitable.blockWidth)

        return (red,green,blue)

### Trix Class ###

class trix:
    def __init__(self,name,lumi,imagetb):
        self.name = name

        self.lumitable = lumi

        self.imagetable = imagetb
        self.imagetable.table.reverse()

        self.image = Image.new('RGBA', (self.imagetable.xBlocks*self.lumitable.blockWidth,self.imagetable.yBlocks*self.lumitable.blockHeight), (255,255,255,255))

        self.blockPerChar = math.ceil(len(self.imagetable.table).__float__() / len(self.lumitable.table).__float__())

        self.trixtable = []

    def generateTrixtable(self):
        trixindex = -1

        ready = 0.0
        total = len(self.lumitable.table)

        for i in self.lumitable.table:

            trixindex += 1
            self.trixtable.append([i[0],[]])

            for n in range(0,self.blockPerChar.__int__()):
                if(len(self.imagetable.table)>0):
                     self.trixtable[trixindex][1].append((self.imagetable.table.pop()[1]))
                else:
                    break

            ready += 1.0
            v_print(2,"Generating trixtable: {0:.2f}%".format((ready/total)*100.0))

        v_print(2,"Trixtable generated!")

    def printTrix(self,output):

        txt = Image.new('RGBA', self.image.size, (255,255,255,0))

        fnt = ImageFont.truetype("lumitables/"+self.lumitable.fontName+".ttf", self.lumitable.fontSize)
        d = ImageDraw.Draw(txt)

        for currtrix in self.trixtable:
            if len(currtrix) > 0:
                for i in range(0,self.blockPerChar.__int__()):
                    if len(currtrix[1]) > i:
                        for tuple in currtrix[1][i]:
                            x = tuple[0] * self.lumitable.blockWidth
                            y = tuple[1] * self.lumitable.blockHeight
                            if self.imagetable.colorMode == "colors":
                                red = self.imagetable.colorTable[tuple[0]][tuple[1]][0]
                                green = self.imagetable.colorTable[tuple[0]][tuple[1]][1]
                                blue = self.imagetable.colorTable[tuple[0]][tuple[1]][2]
                                d.text((x,y), chr(currtrix[0]), font=fnt, fill=(red,green,blue,255))
                            else:
                                d.text((x,y), chr(currtrix[0]), font=fnt, fill=(0,0,0,255))

        out = Image.alpha_composite(self.image, txt)

        out.save("output/" + output)

        v_print(2,"Trix saved!")

### Default Configs ###

class configs():

    def __init__(self):

        # Open defauls.cfg if it exists or create a new one if it doesn't.

        ConfigPrs = ConfigParser.ConfigParser()

        if os.path.isfile("defaults.cfg"):
            ConfigPrs.read("defaults.cfg")
        else:
            cfgfile = open("defaults.cfg",'w')

            # add the settings to the structure of the file, and lets write it out...
            ConfigPrs.add_section('Defaults')
            ConfigPrs.set('Defaults','lumitable','courier.lut')
            ConfigPrs.set('Defaults','colorMode', 'colors')
            ConfigPrs.set('Defaults','verbosity', "1") # 0 = nothing / 1 = errors / 2 = info
            ConfigPrs.write(cfgfile)
            cfgfile.close()

        # -/

        self.input = ""
        self.output = ""
        self.lumitable = ConfigPrs.get("Defaults","lumitable")
        self.colorMode = ConfigPrs.get("Defaults","colorMode")
        self.verbosity = int(ConfigPrs.get("Defaults","verbosity"))

### --------------- ###

### MAIN FUNCTION ###

def main():

    ### Arguments parsing ###
        # Configure and parse the command line parameters.

    parser = argparse.ArgumentParser(description='Creates a number matrix based on an image file.')

    parser.add_argument('-i','--input',help="Input file pathname.",required=True)
    parser.add_argument('-o','--output',help="Output file pathname.",required=True)
    parser.add_argument('-l','--lumitable',help="Lumitable name.",required=False)
    parser.add_argument('-c','--colorMode',help="Color mode (bw/colors).",required=False)
    parser.add_argument('-v','--verbosity',help="Controls how much information the program will print.\n0 = none | 1 = errors | 2 = errors and info", required=False)

    args = parser.parse_args()

    ### ----------------- ###

    if not os.path.isfile(args.input):
        v_print(1,"EXITING: Input file not found!")
        sys.exit(-1)
    else:
        conf.input = args.input

    # TODO: solve permission problems on Windows
    if os.path.isfile("output/" + args.output):
        op = raw_input("Output file already exists. Overwrite existing file? (Y/N)")
        if(op == "n" or op == "N"):
            v_print(1,"EXITING: Process canceled. Output file already exists.")
            sys.exit(-1)
    else:
        conf.output = args.output

    if args.lumitable != None:
        if os.path.isfile("lumitables/" + args.lumitable) :
            v_print(1,"EXITING: Lumitable " + args.lumitable +  " not found on /lumitables folder!")
            sys.exit(-1)
        else:
            conf.lumitable = args.lumitable

    if args.colorMode != None:
        if args.colorMode != "colors" and args.colorMode != "bw":
            v_print(1,"EXITING: Color mode " + args.colorMode +  " don't exist!")
            sys.exit(-1)
        else:
            conf.colorMode = args.colorMode

    if args.verbosity != None:
        if int(args.verbosity) < 0 or int(args.verbosity) > 2:
            v_print(1,"EXITING: Verbosity level " + args.verbosity +  " don't exist!")
            sys.exit(-1)
        else:
            conf.verbosity = args.verbosity

    ### The Program Core ###

    with open("lumitables/" + conf.lumitable, 'rb') as f:
        lumi = pickle.load(f)

    imtable = imagetable(conf.input,lumi,conf.colorMode)

    tri = trix(conf.input,lumi,imtable)
    tri.generateTrixtable()
    tri.printTrix(conf.output)

    ### ---------------- ###

if __name__ == "__main__":
    conf = configs()

    ### Implementing Verbosity ###
    if conf.verbosity:
        def _v_print(*verb_args):
            if verb_args[0] <= conf.verbosity:
                if verb_args[0] == 1: print ("ERROR " + verb_args[1])
                if verb_args[0] == 2: print ("INFO " + verb_args[1])
    else:
        _v_print = lambda *a: None  # do-nothing function

    global v_print
    v_print = _v_print


    sys.exit(main())

