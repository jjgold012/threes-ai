import PIL.Image as Image
import numpy as np
import os
import re

DNAME = os.path.dirname(__file__)

CONFIGS = {
    # (screen_width, screen_height): settings dictionary
    # x0,y0: top left corner of the first tile
    # w,h: size of the tile sample
    # dx,dy: spacing between adjacent tiles
    # tx,ty: next-tile sample point
    # sw,sh: screen width and height (set automatically)

    (640, 1136): dict(x0=92, y0=348,  w=96, h=80,  dx=120, dy=160,  tx=320, ty=146),    # Retina 4" iPhone/iPod
}

for w,h in CONFIGS:
    CONFIGS[w,h]['sw'] = w
    CONFIGS[w,h]['sh'] = h

def to_ind(val):
    return {0:0, 1:1, 2:2, 3:3, 6:4, 12:5, 24:6, 48:7, 96:8, 192:9, 384:10, 768:11, 1536:12, 3072:13}[val]

def to_imgkey(imc):
    return np.asarray(imc).tostring()

def get_exemplar_dir(cfg):
    return os.path.join(DNAME, 'exemplars', '%dx%d' % (cfg['sw'], cfg['sh']))

def load_exemplars(cfg):
    import glob
    data = {}
    for fn in glob.glob(os.path.join(get_exemplar_dir(cfg), '*.png')):
        val = re.findall(r'.*/(\d+).*\.png', fn)[0]
        data[to_imgkey(Image.open(fn))] = int(val)
    cfg['exemplars'] = data
    return data

def extract(cfg, im, r, c):
    x = cfg['x0'] + c*cfg['dx']
    y = cfg['y0'] + r*cfg['dy']

    return im.crop((x, y, x+cfg['w'], y+cfg['h']))

def config_for_image(im):
    w,h = im.size
    if (w,h) not in CONFIGS:
        raise Exception("No OCR configuration for screen size %dx%d!" % (w,h))
    return CONFIGS[w,h]

def saveall(fn):
    im = Image.open(fn)
    cfg = config_for_image(im)
    fn, ext = os.path.splitext(fn)

    for r in xrange(4):
        for c in xrange(4):
            extract(cfg, im, r, c).save(fn + '-r%dc%d.png' % (r,c))

#saveall('sample/IMG_3189.PNG')

def classify(cfg, imc):
    if 'exemplars' not in cfg:
        load_exemplars(cfg)
    exemplars = cfg['exemplars']

    key = to_imgkey(imc)
    val = exemplars.get(key, None)
    if val is not None:
        return val

    imc.show()
    vst = raw_input("Unrecognized object! Recognize it and type in the value: ")
    for i in xrange(1, 1000):
        fn = os.path.join(get_exemplar_dir(cfg), '%s.%d.png' % (vst, i))
        if not os.path.isfile(fn):
            imc.save(fn)
            break
    else:
        print "Failed to save exemplar."
    exemplars = load_exemplars(cfg)
    return exemplars[key]

def find_next_tile(cfg, im):
    px = im.getpixel((cfg['tx'], cfg['ty']))
    ret = {
        (102, 204, 255): 1,
        (255, 102, 128): 2,
        (254, 255, 255): 3,
        (0, 0, 0): 4}.get(px, 0)
    if ret == 0:
        print "Warning: unknown next tile (px=%s)!" % (px,)
        im.show()
    return ret

def ocr(fn):
    im = Image.open(fn)
    cfg = config_for_image(im)

    out = np.zeros((4,4), dtype=int)

    for r in xrange(4):
        for c in xrange(4):
            imc = extract(cfg, im, r, c)
            out[r,c] = to_ind(classify(cfg, imc))

    return out, find_next_tile(cfg, im)

if __name__ == '__main__':
    import sys
    for fn in sys.argv[1:]:
        print fn
        print ocr(fn)
        print
