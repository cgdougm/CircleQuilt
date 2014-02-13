#!/bin/env python26
#-------------------------------------------------------------------------------

try:
    from PIL import Image, ImageDraw
except ImportError:
    import Image, ImageDraw # linux

from path import path as Path

TilesDir = Path("./tiles")
TilePngPaths = TilesDir.files("tile-?.png")

left, upper, right, lower = 0,0,255,255


def main():
    for tilePath in TilePngPaths:
        print str(tilePath)
        im = Image.open(str(tilePath))
        cropped = im.crop((left, upper, right, lower))
        icon = cropped.resize((64,64),Image.BICUBIC)
        thumbPath = TilesDir / ("%s_thumb%s" % (tilePath.namebase,tilePath.ext))
        print str(thumbPath)
        icon.save(thumbPath)
        print
        
        iconMatte = Image.new("L",icon.size,0)
        draw = ImageDraw.Draw(iconMatte)
        draw.ellipse((0, 0, iconMatte.size[0], iconMatte.size[1]), fill=255)
        del draw
        iconMatte.save("matte.png")
        
        empty = Image.new("RGBA",icon.size,(0,0,0,0))
        
        roundIcon = Image.composite(icon,empty,iconMatte)
        thumbRoundPath = TilesDir / ("%s_thumbRound%s" % (tilePath.namebase,tilePath.ext))
        roundIcon.save(thumbRoundPath)
        

if __name__ == '__main__':
    main()
