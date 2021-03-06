#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import division

from .plugin import graphic_directory, glass_directory
from PIL import Image, ImageOps, ImageDraw, ImageChops


def createEmptyImage(piconSize):
    width, height = piconSize
    bg = Image.new('RGBA', (width, height), (255, 255, 255, 0))
    return bg


def addColour(piconSize, colour, transparency):
    width, height = piconSize
    h = colour
    r, g, b = tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
    a = int(transparency, 16)
    bg = Image.new('RGBA', (width, height), (r, g, b, a))
    bg.save('/tmp/preview.png', "PNG")
    return bg


def addGraphic(piconSize, background):
    width, height = piconSize
    bg = Image.open(graphic_directory + background).convert('RGBA')
    bg = bg.resize((width, height), Image.ANTIALIAS)
    return bg


def createPreview(picon, piconSize, padding):
    width, height = piconSize

    if padding * 2 > (height / 2):
        padding = int(height / 2) / 2

    pwidth = width - (padding * 2)
    pheight = height - (padding * 2)
    thumbsize = [int(pwidth), int(pheight)]

    im = Image.open(picon)
    im = im.convert('RGBA')
    im = autocrop_image(im)

    imagew, imageh = im.size
    if imagew > pwidth or imageh > pheight:
        im.thumbnail(thumbsize, Image.ANTIALIAS)

    return im


def createReflectedPreview(picon, piconSize, padding, reflectionstrength, reflectionsize):
    width, height = piconSize

    if padding * 2 > (height / 2):
        padding = int(height / 2) / 2

    pwidth = width - (padding * 2)
    pheight = height - (padding * 2)

    thumbsize = [int(pwidth), int(pheight)]

    im = Image.open(picon)
    im = im.convert('RGBA')
    im = autocrop_image(im)
    imagew, imageh = im.size

    mirrorheight = float(reflectionsize) / 100

    ref = ImageOps.flip(im)
    # reflectionheight = int(imageh * mirrorheight)

    left = 0
    top = 0
    right = imagew
    bottom = int(imageh * mirrorheight)
    ref = ref.crop((left, top, right, bottom))

    mask = ""

    if reflectionstrength == 1:
        mask = Image.open('/usr/lib/enigma2/python/Plugins/Extensions/E2Piconizer/icons/reflection-mask-1.png')
    if reflectionstrength == 2:
        mask = Image.open('/usr/lib/enigma2/python/Plugins/Extensions/E2Piconizer/icons/reflection-mask-2.png')
    if reflectionstrength == 3:
        mask = Image.open('/usr/lib/enigma2/python/Plugins/Extensions/E2Piconizer/icons/reflection-mask-3.png')

    if mask != "":
        mask = mask.resize((ref.size[0], ref.size[1]), Image.ANTIALIAS)

        ref_alpha = ref.convert('RGBA').split()[-1]
        ref_alpha = ImageChops.darker(mask, ref_alpha)
        ref.putalpha(ref_alpha)

    combined = Image.new('RGBA', (imagew, imageh + int(imageh * mirrorheight)), (0, 0, 0, 0))
    combined.paste(im, (0, 0), im)
    combined.paste(ref, (0, imageh), ref)
    combinedw, combinedh = combined.size
    if combinedw > pwidth or combinedh > pheight:
        combined.thumbnail(thumbsize, Image.ANTIALIAS)
    return combined


def blendBackground(im, bg, background, reflection, offsety):
    imagew, imageh = im.size
    im_alpha = im.convert('RGBA').split()[-1]

    bgwidth, bgheight = bg.size
    bg_alpha = bg.convert('RGBA').split()[-1]

    temp = Image.new('L', (bgwidth, bgheight), 0)
    if reflection:
        temp.paste(im_alpha, ((bgwidth - imagew) // 2, (bgheight - imageh) // 2 + int(offsety)), im_alpha)
    else:
        temp.paste(im_alpha, ((bgwidth - imagew) // 2, (bgheight - imageh) // 2), im_alpha)

    bg_alpha = ImageChops.screen(bg_alpha, temp)

    if background != "transparent":
        if reflection:
            bg.paste(im, ((bgwidth - imagew) // 2, (bgheight - imageh) // 2 + int(offsety)), im)
        else:
            bg.paste(im, ((bgwidth - imagew) // 2, (bgheight - imageh) // 2), im)

        bg.putalpha(bg_alpha)
    else:
        bg.paste(im, ((bgwidth - imagew) // 2, (bgheight - imageh) // 2))

    return bg


def addGlass(piconSize, im, bg):
    width, height = piconSize
    im = Image.open(glass_directory + im).convert('RGBA')
    im = im.resize((width, height), Image.ANTIALIAS)

    imagew, imageh = im.size
    im_alpha = im.convert('RGBA').split()[-1]

    bgwidth, bgheight = bg.size
    bg_alpha = bg.convert('RGBA').split()[-1]

    temp = Image.new('L', (bgwidth, bgheight), 0)
    temp.paste(im_alpha, (0, 0), im_alpha)

    bg_alpha = ImageChops.screen(bg_alpha, temp)
    bg.paste(im, (0, 0), im)
    bg.putalpha(bg_alpha)

    return bg


def addCorners(im, radius):
    n = 4  # upscale for smooth corners
    w, h = im.size
    if radius > h / 2:
        radius = int(h / 2)

    circle = Image.new('L', (radius * 2 * n, radius * 2 * n), 0)
    draw = ImageDraw.Draw(circle)
    draw.ellipse((0, 0, radius * 2 * n, radius * 2 * n), fill=255)
    alpha = Image.new('L', im.size, 255)
    circle = circle.resize((radius * 2, radius * 2), Image.ANTIALIAS)

    alpha.paste(circle.crop((0, 0, radius, radius)), (0, 0))
    alpha.paste(circle.crop((0, radius, radius, radius * 2)), (0, h - radius))
    alpha.paste(circle.crop((radius, 0, radius * 2, radius)), (w - radius, 0))
    alpha.paste(circle.crop((radius, radius, radius * 2, radius * 2)), (w - radius, h - radius))

    if im.mode in ('RGBA', 'LA') or (im.mode == 'P' and 'transparency' in im.info):
        bg_alpha = im.convert('RGBA').split()[-1]
        alpha = ImageChops.darker(alpha, bg_alpha)

    im.putalpha(alpha)
    return im


def autocrop_image(image):
    # Get the bounding box
    r, g, b, a = image.split()
    bbox = a.getbbox()

    # Crop the image to the contents of the bounding box
    image = image.crop(bbox)

    # Determine the width and height of the cropped image
    (width, height) = image.size

    # Create a new image object for the output image
    cropped_image = Image.new("RGBA", (width, height), (0, 0, 0, 0))

    # Paste the cropped image onto the new image
    cropped_image.paste(image, (0, 0))

    return cropped_image
