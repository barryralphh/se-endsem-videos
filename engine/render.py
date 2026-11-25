import re, sys, os, glob, subprocess, asyncio, math, runpy, time
from PIL import Image, ImageDraw, ImageFont

NL = chr(10)
W, H = 1280, 720
FD = '/usr/share/fonts/truetype/dejavu/'
C = dict(bg=(15,23,42), bar=(2,6,23), panel=(30,41,59), paper=(255,250,235), ink=(25,25,40), white=(241,245,249), yel=(250,204,21), grn=(34,197,94), red=(239,68,68), blu=(56,189,248), org=(251,146,60), dim=(148,163,184))
PAL = [(37,99,235),(5,150,105),(217,119,6),(147,51,234),(220,38,38),(8,145,178)]
_fc = {}

def F(sz, b=False, m=False):
    k = (sz, b, m)
    if k not in _fc:
        n = ('DejaVuSansMono' if m else 'DejaVuSans') + ('-Bold' if b else '') + '.ttf'
        _fc[k] = ImageFont.truetype(FD + n, sz)
    return _fc[k]

def S(say, cap, left=None, right=None, title=None, full=False, pig=False):
    return dict(say=say, cap=cap, left=left or [], right=right or [], title=title, full=full, pig=pig)

def wrap(text, font, maxw):
    out = []
    for para in text.split(NL):
        ind = len(para) - len(para.lstrip(' '))
        pre = ' ' * ind
        pw = font.getlength(pre)
        line = ''
        for w in para.strip().split(' '):
            t = (line + ' ' + w) if line else w
            if font.getlength(t) + pw <= maxw:
                line = t
            else:
                if line:
                    out.append(pre + line)
                line = w
                while len(line) > 1 and font.getlength(line) + pw > maxw:
                    k = len(line) - 1
                    while k > 1 and font.getlength(line[:k]) + pw > maxw:
                        k -= 1
                    out.append(pre + line[:k])
                    line = line[k:]
        out.append(pre + line)
    return out

def draw_plot(d, x, y, w, h, pts, opt):
    ox, oy = x + 46, y + h - 34
    pw, ph = w - 62, h - 52
    xmax = max(p[0] for p in pts)
    ymax = max([p[1] for p in pts] + [l[0] for l in opt.get('lines', [])]) * 1.1
    d.line([ox, oy, ox + pw, oy], fill=C['dim'], width=2)
    d.line([ox, oy, ox, oy - ph], fill=C['dim'], width=2)
    def P(px, py):
        return (ox + px / xmax * pw, oy - py / ymax * ph)
    for yv, lab in opt.get('lines', []):
        a = P(0, yv)
        xx = a[0]
        while xx < ox + pw:
            d.line([xx, a[1], min(xx + 8, ox + pw), a[1]], fill=C['org'], width=2)
            xx += 14
        d.text((ox + pw, a[1] - 18), lab, font=F(15), fill=C['org'], anchor='ra')
    d.line([P(*p) for p in pts], fill=C['grn'], width=3)
    for p in pts:
        q = P(*p)
        d.ellipse([q[0] - 3, q[1] - 3, q[0] + 3, q[1] + 3], fill=C['yel'])
    d.text((ox + pw, oy + 8), opt.get('xl', 'x'), font=F(15), fill=C['dim'], anchor='ra')
    d.text((ox - 6, oy - ph), opt.get('yl', 'y'), font=F(15), fill=C['dim'], anchor='ra')
    for a in opt.get('marks', []):
        q = P(a[0], a[1])
        d.text((q[0] + 6, q[1] - 22), a[2], font=F(15, True), fill=C['red'])

def pig(d, cx, cy, r):
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(132, 204, 22), outline=(54, 83, 20), width=3)
    d.ellipse([cx - r * 0.35, cy - r * 0.05, cx + r * 0.35, cy + r * 0.5], fill=(163, 230, 53), outline=(54, 83, 20), width=2)
    for ex in (-0.15, 0.15):
        d.ellipse([cx + ex * r - 3, cy + r * 0.15, cx + ex * r + 3, cy + r * 0.3], fill=(54, 83, 20))
    for ex in (-0.45, 0.45):
        d.ellipse([cx + ex * r - r * 0.14, cy - r * 0.4 - r * 0.14, cx + ex * r + r * 0.14, cy - r * 0.4 + r * 0.14], fill=(255, 255, 255), outline=(0, 0, 0), width=2)
        d.ellipse([cx + ex * r - 3, cy - r * 0.4 - 3, cx + ex * r + 3, cy - r * 0.4 + 3], fill=(0, 0, 0))

def _clip(w, h, dx, dy, shape):
    if dx == 0 and dy == 0:
        return 0
    if shape == 'circ':
        return (w / 2) / math.hypot(dx, dy)
    tx = (w / 2) / abs(dx) if dx else 1e9
    ty = (h / 2) / abs(dy) if dy else 1e9
    return min(tx, ty)

def draw_graph(d, x, y, w, h, nodes, edges, sz):
    fs = max(12, min(sz - 2, 18))
    f = F(fs, True)
    pos = {}
    for i, n in enumerate(nodes):
        nid, lab, fx, fy = n[0], n[1], n[2], n[3]
        shape = n[4] if len(n) > 4 else 'box'
        ci = n[5] if len(n) > 5 else i
        ls = wrap(lab, f, min(w * 0.28, 190))
        tw = max(f.getlength(l) for l in ls)
        th = len(ls) * (fs + 3)
        if shape == 'dia':
            bw, bh = tw * 1.45 + 26, th * 1.5 + 18
        elif shape == 'circ':
            bw = bh = max(tw, th) + 18
        else:
            bw, bh = tw + 20, th + 12
        pos[nid] = (x + fx * w, y + fy * h, bw, bh, shape, ci, ls)
    for e in edges:
        a, b = pos[e[0]], pos[e[1]]
        lab = e[2] if len(e) > 2 else ''
        dx, dy = b[0] - a[0], b[1] - a[1]
        ta = _clip(a[2], a[3], dx, dy, a[4])
        tb = _clip(b[2], b[3], dx, dy, b[4])
        if ta + tb >= 1:
            continue
        x1, y1 = a[0] + dx * ta, a[1] + dy * ta
        x2, y2 = b[0] - dx * tb, b[1] - dy * tb
        d.line([x1, y1, x2, y2], fill=C['yel'], width=3)
        ang = math.atan2(y2 - y1, x2 - x1)
        hx, hy = 13, 6
        p1 = (x2 - hx * math.cos(ang) + hy * math.sin(ang), y2 - hx * math.sin(ang) - hy * math.cos(ang))
        p2 = (x2 - hx * math.cos(ang) - hy * math.sin(ang), y2 - hx * math.sin(ang) + hy * math.cos(ang))
        d.polygon([(x2, y2), p1, p2], fill=C['yel'])
        if lab:
            mx, my = (x1 + x2) / 2, (y1 + y2) / 2
            lf = F(max(12, fs - 2), True)
            tw = lf.getlength(lab)
            d.rounded_rectangle([mx - tw / 2 - 4, my - 11, mx + tw / 2 + 4, my + 11], 6, fill=(15, 23, 42))
            d.text((mx, my), lab, font=lf, fill=C['org'], anchor='mm')
    for nid, (cx, cy, bw, bh, shape, ci, ls) in pos.items():
        col = PAL[ci % 6]
        if shape == 'dia':
            d.polygon([(cx, cy - bh / 2), (cx + bw / 2, cy), (cx, cy + bh / 2), (cx - bw / 2, cy)], fill=col, outline=(255, 255, 255))
        elif shape == 'circ':
            d.ellipse([cx - bw / 2, cy - bh / 2, cx + bw / 2, cy + bh / 2], fill=col, outline=(255, 255, 255), width=2)
        elif shape == 'oval':
            d.rounded_rectangle([cx - bw / 2, cy - bh / 2, cx + bw / 2, cy + bh / 2], int(bh / 2), fill=col, outline=(255, 255, 255), width=2)
        else:
            d.rounded_rectangle([cx - bw / 2, cy - bh / 2, cx + bw / 2, cy + bh / 2], 8, fill=col)
        ty = cy - len(ls) * (fs + 3) / 2 + 1
        for ln in ls:
            d.text((cx, ty), ln, font=f, fill=(255, 255, 255), anchor='ma')
            ty += fs + 3

def draw_map(d, x, y, w, root, groups, sz):
    fs = max(11, sz - 10)
    f, fb = F(fs), F(fs + 2, True)
    rh = fs + 20
    d.rounded_rectangle([x + w * 0.2, y, x + w * 0.8, y + rh], 10, fill=(147, 51, 234))
    d.text((x + w / 2, y + rh / 2), root, font=F(fs + 5, True), fill=(255, 255, 255), anchor='mm')
    y += rh
    d.line([x + w / 2, y, x + w / 2, y + 12], fill=C['yel'], width=3)
    y += 14
    n = len(groups)
    nc = min(n, 4)
    gap = 10
    cw = (w - (nc - 1) * gap) / nc
    for ri in range(0, n, nc):
        cards = []
        for hd, leaves in groups[ri:ri + nc]:
            hl = wrap(hd, fb, cw - 14)
            ll = [wrap(t, f, cw - 30) for t in leaves]
            hh = len(hl) * (fs + 6) + 8
            tot = hh + 6 + sum(len(l) * (fs + 3) + 2 for l in ll) + 6
            cards.append((hl, ll, hh, tot))
        mh = max(c[3] for c in cards)
        for i, (hl, ll, hh, tot) in enumerate(cards):
            cx = x + i * (cw + gap)
            col = PAL[(ri + i) % 6]
            d.rounded_rectangle([cx, y, cx + cw, y + mh], 10, fill=(30, 41, 59), outline=col, width=3)
            d.rounded_rectangle([cx, y, cx + cw, y + hh], 10, fill=col)
            ty = y + 4
            for t in hl:
                d.text((cx + cw / 2, ty), t, font=fb, fill=(255, 255, 255), anchor='ma')
                ty += fs + 6
            ty = y + hh + 6
            for l in ll:
                d.text((cx + 8, ty), '\u2022', font=f, fill=C['org'])
                for t in l:
                    d.text((cx + 22, ty), t, font=f, fill=C['white'])
                    ty += fs + 3
                ty += 2
        y += mh + 10
    return y

def left_layout(d, items, x, y, w, sz):
    for it in items:
        k = it[0]
        if k == 'h':
            f = F(sz + 6, True)
            for ln in wrap(it[1], f, w):
                d.text((x, y), ln, font=f, fill=C['yel'])
                y += sz + 12
            y += 4
        elif k == 't':
            f = F(sz)
            for ln in wrap(it[1], f, w):
                d.text((x, y), ln, font=f, fill=C['white'])
                y += sz + 8
            y += 6
        elif k == 'b':
            f = F(sz)
            for p in it[1]:
                d.text((x, y), '\u2022', font=f, fill=C['org'])
                for ln in wrap(p, f, w - 28):
                    d.text((x + 28, y), ln, font=f, fill=C['white'])
                    y += sz + 7
                y += 3
            y += 4
        elif k == 'b2':
            cw = (w - 24) / 2
            f = F(sz)
            half = (len(it[1]) + 1) // 2
            ends = []
            for ci in range(2):
                yy = y
                for j, p in enumerate(it[1][ci * half:(ci + 1) * half]):
                    num = ci * half + j + 1
                    d.text((x + ci * (cw + 24), yy), str(num) + '.', font=F(sz, True), fill=C['org'])
                    for ln in wrap(p, f, cw - 40):
                        d.text((x + ci * (cw + 24) + 40, yy), ln, font=f, fill=C['white'])
                        yy += sz + 7
                    yy += 9
                ends.append(yy)
            y = max(ends)
        elif k == 'row':
            labs = it[1]
            n = len(labs)
            gap = 30 if n <= 4 else 14
            bw = (w - (n - 1) * gap) / n
            fs = min(sz, 22)
            while fs > 11 and any(F(fs, True).getlength(wd) > bw - 10 for l in labs for wd in l.split()):
                fs -= 1
            f = F(fs, True)
            ls = [wrap(l, f, bw - 10) for l in labs]
            mh = max(len(a) for a in ls) * (fs + 4) + 14
            for i, l in enumerate(ls):
                bx = x + i * (bw + gap)
                d.rounded_rectangle([bx, y, bx + bw, y + mh], 8, fill=PAL[i % 6])
                ty = y + 7
                for ln in l:
                    d.text((bx + bw / 2, ty), ln, font=f, fill=(255, 255, 255), anchor='ma')
                    ty += fs + 4
                if i < n - 1:
                    ax = bx + bw + 2
                    ay = y + mh / 2
                    d.line([ax, ay, ax + gap - 8, ay], fill=C['yel'], width=3)
                    d.polygon([(ax + gap - 8, ay - 6), (ax + gap - 8, ay + 6), (ax + gap, ay)], fill=C['yel'])
            y += mh + 14
        elif k == 'col':
            labs = it[1]
            fs = min(sz, 22)
            f = F(fs, True)
            bw = w * 0.86
            bx = x + (w - bw) / 2
            for i, l in enumerate(labs):
                ls = wrap(l, f, bw - 16)
                mh = len(ls) * (fs + 4) + 12
                d.rounded_rectangle([bx, y, bx + bw, y + mh], 8, fill=PAL[i % 6])
                ty = y + 6
                for ln in ls:
                    d.text((bx + bw / 2, ty), ln, font=f, fill=(255, 255, 255), anchor='ma')
                    ty += fs + 4
                y += mh
                if i < len(labs) - 1:
                    d.polygon([(x + w / 2 - 8, y + 2), (x + w / 2 + 8, y + 2), (x + w / 2, y + 16)], fill=C['yel'])
                    y += 18
            y += 12
        elif k == 'tbl':
            rows = it[1]
            nc = max(len(r) for r in rows)
            fs = max(12, sz - 5)
            f = F(fs)
            fb = F(fs, True)
            cw = [max(f.getlength(str(r[c])) if c < len(r) else 0 for r in rows) + 16 for c in range(nc)]
            tot = sum(cw)
            if tot > w:
                cw = [c * w / tot for c in cw]
            else:
                cw = [c + (w - tot) / nc for c in cw]
            for ri, r in enumerate(rows):
                ff = fb if ri == 0 else f
                cells = [wrap(str(r[c]) if c < len(r) else '', ff, cw[c] - 12) for c in range(nc)]
                rh = max(len(c) for c in cells) * (fs + 4) + 10
                cx = x
                for c in range(nc):
                    fill = (30, 64, 175) if ri == 0 else ((51, 65, 85) if ri % 2 else (71, 85, 105))
                    d.rectangle([cx, y, cx + cw[c], y + rh], fill=fill, outline=(15, 23, 42))
                    ty = y + 5
                    for ln in cells[c]:
                        d.text((cx + 6, ty), ln, font=ff, fill=C['white'])
                        ty += fs + 4
                    cx += cw[c]
                y += rh
            y += 12
        elif k == 'bits':
            s = it[1]
            labs = it[2] if len(it) > 2 else None
            n = len(s.replace(' ', ''))
            cs = min(46, int((w - 12) / (n + 0.5 * s.count(' '))))
            f = F(max(10, int(cs * 0.6)), True, True)
            cx = x
            i = 0
            for ch in s:
                if ch == ' ':
                    cx += cs * 0.5
                    continue
                d.rectangle([cx, y, cx + cs - 3, y + cs], fill=(51, 65, 85), outline=C['yel'])
                d.text((cx + (cs - 3) / 2, y + cs / 2), ch, font=f, fill=C['yel'], anchor='mm')
                if labs and i < len(labs):
                    d.text((cx + (cs - 3) / 2, y + cs + 4), labs[i], font=F(13), fill=C['dim'], anchor='ma')
                cx += cs
                i += 1
            y += cs + (22 if labs else 0) + 14
        elif k == 'plot':
            draw_plot(d, x, y, w, 290, it[1], it[2] if len(it) > 2 else {})
            y += 300
        elif k == 'graph':
            gh = it[3] if len(it) > 3 else 300
            draw_graph(d, x, y, w, gh, it[1], it[2], sz)
            y += gh + 10
        elif k == 'map':
            y = draw_map(d, x, y, w, it[1], it[2], sz)
    return y

def right_layout(d, lines, x, y, w, sz, spans=None):
    f = F(sz, False, True)
    fb = F(sz, True, True)
    lh = sz + 7
    for ln in lines:
        y0 = y
        if ln.startswith('## '):
            y += 4
            for t in wrap(ln[3:], fb, w):
                d.text((x, y), t, font=fb, fill=(185, 28, 28))
                y += lh
            d.line([x, y - 3, x + w, y - 3], fill=(185, 28, 28), width=2)
            y += 6
        elif ln.startswith('! '):
            ls = wrap(ln[2:], fb, w - 20)
            h = len(ls) * lh + 10
            d.rounded_rectangle([x - 4, y, x + w, y + h], 8, fill=(187, 247, 208), outline=(22, 101, 52), width=2)
            ty = y + 5
            for t in ls:
                d.text((x + 6, ty), t, font=fb, fill=(20, 83, 45))
                ty += lh
            y += h + 8
        elif ln.startswith('? '):
            for t in wrap(ln[2:], fb, w):
                d.text((x, y), t, font=fb, fill=(30, 64, 175))
                y += lh
            y += 2
        elif ln.startswith('~ '):
            for t in wrap(ln[2:], f, w):
                d.text((x, y), t, font=f, fill=(100, 100, 120))
                y += lh
        else:
            for t in wrap(ln, f, w):
                d.text((x, y), t, font=f, fill=C['ink'])
                y += lh
        if spans is not None:
            spans.append((y0, y))
    return y

_scr = Image.new('RGB', (W, H))

def fit(fn, maxh, sizes):
    d = ImageDraw.Draw(_scr)
    for sz in sizes:
        if fn(d, sz) <= maxh:
            return sz
    return sizes[-1]

def bird(d, cx, cy, r, mouth):
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(220, 38, 38), outline=(120, 20, 20), width=4)
    d.ellipse([cx - r * 0.6, cy + r * 0.05, cx + r * 0.6, cy + r * 0.95], fill=(253, 224, 200))
    d.polygon([(cx - 10, cy - r), (cx, cy - r - 26), (cx + 10, cy - r)], fill=(150, 20, 20))
    d.polygon([(cx + 8, cy - r + 2), (cx + 22, cy - r - 22), (cx + 26, cy - r + 6)], fill=(150, 20, 20))
    for ex in (-0.3, 0.3):
        ecx = cx + ex * r
        ecy = cy - 0.2 * r
        d.ellipse([ecx - r * 0.2, ecy - r * 0.2, ecx + r * 0.2, ecy + r * 0.2], fill=(255, 255, 255), outline=(0, 0, 0), width=2)
        d.ellipse([ecx + r * 0.02, ecy - r * 0.06, ecx + r * 0.12, ecy + r * 0.06], fill=(0, 0, 0))
    d.line([(cx - 0.55 * r, cy - 0.62 * r), (cx - 0.08 * r, cy - 0.36 * r)], fill=(20, 0, 0), width=7)
    d.line([(cx + 0.55 * r, cy - 0.62 * r), (cx + 0.08 * r, cy - 0.36 * r)], fill=(20, 0, 0), width=7)
    by = cy + 0.08 * r
    d.polygon([(cx, by - 0.1 * r), (cx + 0.62 * r, by + 0.05 * r), (cx, by + 0.18 * r)], fill=(250, 204, 21), outline=(120, 80, 0))
    if mouth:
        d.polygon([(cx + 0.02 * r, by + 0.2 * r), (cx + 0.5 * r, by + 0.28 * r), (cx + 0.02 * r, by + 0.42 * r)], fill=(234, 179, 8), outline=(120, 80, 0))

def frame(sc, idx, total, ltitle, nl, nr, lsz, rsz, mouth, full, has_r):
    im = Image.new('RGB', (W, H), C['bg'])
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, W, 64], fill=C['bar'])
    d.text((24, 14), sc.get('title') or ltitle, font=F(30, True), fill=C['yel'])
    d.text((W - 24, 22), 'Bird Squad SE Dojo  |  %d/%d' % (idx, total), font=F(20), fill=C['dim'], anchor='ra')
    bottom = 700 if full else 530
    lx1 = 632 if has_r else W - 24
    d.rounded_rectangle([16, 76, lx1 + 8, bottom], 14, fill=C['panel'])
    left_layout(d, sc['left'][:nl], 36, 90, lx1 - 36 - 12, lsz)
    if has_r:
        d.rounded_rectangle([648, 76, W - 16, bottom], 14, fill=C['paper'])
        d.text((664, 82), 'EXAM ANSWER / WORKING', font=F(16, True), fill=(120, 53, 15))
        right_layout(d, sc['right'][:nr], 664, 108, 584, rsz)
    if not full:
        by = 618 + (-4 if mouth else 0)
        bird(d, 84, by, 58, mouth)
        d.polygon([(142, 600), (166, 584), (166, 620)], fill=(255, 255, 255))
        d.rounded_rectangle([160, 548, W - 16, 704], 18, fill=(255, 255, 255))
        cf = F(26, True)
        if sc.get('pig'):
            pig(d, W - 66, 626, 34)
        cap = wrap(sc['cap'], cf, W - 16 - 160 - 36 - (84 if sc.get('pig') else 0))[:3]
        ty = 626 - len(cap) * 17
        for ln in cap:
            d.text((180, ty), ln, font=cf, fill=(30, 30, 50))
            ty += 34
    return im


CONN = ['Pehle', 'Ab agla step', 'Phir', 'Iske baad', 'Ab dekho', 'Chalo aage']

def words(t):
    t = t.replace('0x', 'hex ')
    t = re.sub(r'\d+\.\d+\.\d+\.\d+', lambda m: m.group(0).replace('.', ' dot '), t)
    t = re.sub(r'(?<=\d)\.(?=\d)', ' point ', t)
    t = t.replace('->', ' matlab ').replace('=>', ' matlab ').replace('\u2192', ' matlab ')
    t = t.replace('\u00d7', ' into ').replace('\u00f7', ' divided by ')
    t = re.sub(r'(?<=[\d)])\s*[x*]\s*(?=[\d(])', ' into ', t)
    t = re.sub(r'\s[x*]\s', ' into ', t)
    t = re.sub(r'(?<=[\w)])\s*/\s*(?=[\w(])', ' divided by ', t)
    t = re.sub(r'(?<![\w)])/(?=\d)', ' slash ', t)
    t = t.replace('<=', ' less than or equal to ').replace('>=', ' greater than or equal to ').replace('!=', ' not equal to ').replace('==', ' equals ')
    t = t.replace('^', ' power ').replace('=', ' barabar ').replace('+', ' plus ')
    t = re.sub(r'\s-\s', ' minus ', t)
    t = t.replace('%', ' percent').replace('(', ' ').replace(')', ' ')
    t = re.sub(r'\b(?=[0-9A-F]*\d)(?=[0-9A-F]*[A-F])[0-9A-F]{2,}\b', lambda m: ' '.join(m.group(0)), t)
    return re.sub(r'\s+', ' ', t).strip()

def spoken(ln, g):
    if ln.startswith('## '):
        return 'Ab dekhte hain, ' + words(ln[3:]) + '.'
    if ln.startswith('! '):
        return 'Yeh hamara answer hai. ' + words(ln[2:]) + '. Isko box kar do.'
    if ln.startswith('? '):
        return 'Sawal yeh hai. ' + words(ln[2:]) + '.'
    if ln.startswith('~ '):
        return 'Dhyan rakho. ' + words(ln[2:]) + '.'
    return CONN[g % len(CONN)] + '. ' + words(ln) + '.'

def calc_frame(lines, vis_to, a, b, idx, total, ltitle, rsz, mouth, cap, gi, gn):
    im = Image.new('RGB', (W, H), C['bg'])
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, W, 64], fill=C['bar'])
    d.text((24, 14), ltitle + '  |  EXAM ANSWER', font=F(30, True), fill=C['yel'])
    d.text((W - 24, 22), 'Bird Squad SE Dojo  |  %d/%d' % (idx, total), font=F(20), fill=C['dim'], anchor='ra')
    d.rounded_rectangle([16, 76, W - 16, 530], 14, fill=C['paper'])
    d.text((36, 84), 'EXAM ANSWER / WORKING   step %d of %d' % (gi, gn), font=F(16, True), fill=(120, 53, 15))
    vis = lines[:vis_to + 1]
    sp = []
    right_layout(ImageDraw.Draw(_scr), vis, 36, 112, 1176, rsz, sp)
    d.rounded_rectangle([28, sp[a][0] - 3, W - 28, sp[b][1] + 3], 8, fill=(254, 240, 138), outline=(202, 138, 4), width=2)
    right_layout(d, vis, 36, 112, 1176, rsz)
    by = 618 + (-4 if mouth else 0)
    bird(d, 84, by, 58, mouth)
    d.polygon([(142, 600), (166, 584), (166, 620)], fill=(255, 255, 255))
    d.rounded_rectangle([160, 548, W - 16, 704], 18, fill=(255, 255, 255))
    cf = F(26, True)
    cp = wrap(cap, cf, W - 16 - 160 - 36)[:3]
    ty = 626 - len(cp) * 17
    for ln in cp:
        d.text((180, ty), ln, font=cf, fill=(30, 30, 50))
        ty += 34
    return im

def probe(p):
    r = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', p], capture_output=True, text=True)
    return float(r.stdout.strip())

async def _edge(text, out):
    import edge_tts
    await edge_tts.Communicate(text, 'en-IN-PrabhatNeural', rate='-6%').save(out)

def tts(text, wav, mode):
    mp3 = wav[:-4] + '.mp3'
    ok = False
    if mode != 'none':
        for a in range(6):
            try:
                asyncio.run(_edge(text, mp3))
                ok = os.path.getsize(mp3) > 1000
                if ok:
                    break
            except Exception as e:
                print('tts retry', a, e)
                time.sleep(2 + 3 * a)
    if ok:
        subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', mp3, '-ar', '24000', '-ac', '1', '-af', 'apad=pad_dur=0.6', wav], check=True)
        return
    if mode != 'none':
        print('FALLBACK espeak')
        tmp = wav[:-4] + '_e.wav'
        subprocess.run(['espeak-ng', '-v', 'en-in', '-s', '150', '-w', tmp, text])
        subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', tmp, '-ar', '24000', '-ac', '1', '-af', 'apad=pad_dur=0.6', wav], check=True)
        return
    secs = max(3.0, len(text.split()) / 2.4)
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'lavfi', '-i', 'anullsrc=r=24000:cl=mono', '-t', str(secs), wav], check=True)

def load(n):
    path = glob.glob('content/U%s_*.py' % n)[0]
    L = runpy.run_path(path, init_globals={'S': S})['L']
    scenes = list(L['scenes'])
    pts = L['points']
    say = 'Ab final recap. Yeh ' + str(len(pts)) + ' points bas rat lo. ' + ' '.join('Point %d. %s.' % (i + 1, p) for i, p in enumerate(pts)) + ' Bas, ab tum is unit ke boss ho.'
    scenes.append(dict(say=say, cap='Golden points: yaad kar lo!', left=[['b2', pts]], right=[], title='Golden Points', full=True, pig=False))
    tg = [('s', 'Start', 0.5, 0.06, 'oval', 5), ('a', 'Definition (2-3 lines)', 0.5, 0.2, 'box', 0), ('b', 'Neat diagram + labels', 0.5, 0.34, 'box', 1), ('c', 'Points / steps / types', 0.5, 0.48, 'box', 2), ('d', 'Example (real life)', 0.5, 0.62, 'box', 3), ('e', 'Advantages + Disadvantages / table', 0.5, 0.76, 'box', 4), ('f', 'Conclusion (1 line)', 0.5, 0.92, 'oval', 5)]
    te = [('s', 'a'), ('a', 'b'), ('b', 'c'), ('c', 'd'), ('d', 'e'), ('e', 'f')]
    say2 = 'Last mein, chaar page ka formula. Kisi bhi topic ko aise likho. Pehle definition, do teen line. Phir neat diagram, labels ke saath. Phir points ya steps ya types. Phir ek real life example. Phir table, advantages aur disadvantages. Aur end mein ek line ka conclusion. Bas, yeh sequence follow karo, har sawaal chaar page ka ban jayega. Milte hain agle video mein!'
    scenes.append(dict(say=say2, cap='4-page answer formula: Def > Diagram > Points > Example > Table > Conclusion', left=[['graph', tg, te, 480]], right=[], title='4-Page Answer Formula', full=True, pig=False))
    return L, scenes

def chunks_of(total, nch):
    base, extra = divmod(total, nch)
    out = []
    a = 0
    for k in range(nch):
        sz = base + (1 if k < extra else 0)
        out.append(list(range(a + 1, a + sz + 1)))
        a += sz
    return out

def sizes_for(sc):
    full = sc.get('full', False)
    has_r = bool(sc['right']) and not full
    lw = (632 - 36 - 12) if has_r else (W - 24 - 36 - 12)
    bottom = 700 if full else 530
    lsz = fit(lambda d, sz: left_layout(d, sc['left'], 0, 0, lw, sz), bottom - 90 - 16, (28, 26, 24, 22, 20, 18, 17, 16, 15, 14))
    rsz = fit(lambda d, sz: right_layout(d, sc['right'], 0, 0, 584, sz), bottom - 108 - 16, (24, 22, 20, 18, 17, 16, 15, 14))
    return full, has_r, lsz, rsz

def preview(n):
    L, scenes = load(n)
    os.makedirs('out/prev', exist_ok=True)
    for i, sc in enumerate(scenes, 1):
        full, has_r, lsz, rsz = sizes_for(sc)
        frame(sc, i, len(scenes), L['title'], len(sc['left']), len(sc['right']), lsz, rsz, 1, full, has_r).save('out/prev/%s_%02d.png' % (n, i))
    print('preview done', len(scenes))

def build(n, mode, k=None, nch=1):
    L, scenes = load(n)
    sel = set(chunks_of(len(scenes), nch)[k]) if k is not None else set(range(1, len(scenes) + 1))
    work = 'work/%s_%s' % (n, k if k is not None else 'all')
    os.makedirs(work, exist_ok=True)
    os.makedirs('out', exist_ok=True)
    entries = []
    wavs = []
    total = len(scenes)
    cnt = [0]

    def newwav(say):
        cnt[0] += 1
        wav = '%s/a%03d.wav' % (work, cnt[0])
        tts(say, wav, mode)
        wavs.append(wav)
        return wav, probe(wav)

    def hold(imgs, sd):
        t = 0.0
        j = 0
        while t < sd - 1e-6:
            c = min(0.5, sd - t)
            entries.append((imgs[j % len(imgs)], c))
            t += c
            j += 1

    def emit_plain(sc, i, say):
        wav, D = newwav(say)
        full, has_r, lsz, rsz = sizes_for(sc)
        left, right = sc['left'], sc['right']
        steps = max(len(left), len(right), 1)
        for s in range(steps):
            nl = math.ceil((s + 1) * len(left) / steps)
            nr = math.ceil((s + 1) * len(right) / steps)
            imgs = []
            for mouth in ((0, 1) if not full else (0,)):
                p = '%s/f%03d_%02d_%d.png' % (work, cnt[0], s, mouth)
                frame(sc, i, total, L['title'], nl, nr, lsz, rsz, mouth, full, has_r).save(p)
                imgs.append(p)
            hold(imgs, D / steps)

    def emit_calc(sc, i):
        lines = sc['right']
        groups = []
        j = 0
        while j < len(lines):
            if lines[j].startswith('## ') and j + 1 < len(lines) and not lines[j + 1].startswith('## '):
                groups.append((j, j + 1))
                j += 2
            else:
                groups.append((j, j))
                j += 1
        rsz = fit(lambda d, sz: right_layout(d, lines, 0, 0, 1176, sz), 396, (30, 28, 26, 24, 22, 20, 18, 16, 14))
        for g, (a, b) in enumerate(groups):
            say = ' '.join(spoken(lines[t], g) for t in range(a, b + 1))
            if g == 0:
                say = 'Ab calculation karte hain, dhyan se dekho. ' + say
            wav, D = newwav(say)
            cap = ' '.join(re.sub(r'^(##|[!?~]) ', '', lines[t]) for t in range(a, b + 1))
            imgs = []
            for mouth in (0, 1):
                p = '%s/c%03d_%d.png' % (work, cnt[0], mouth)
                calc_frame(lines, b, a, b, i, total, L['title'], rsz, mouth, cap, g + 1, len(groups)).save(p)
                imgs.append(p)
            hold(imgs, D)

    for i, sc in enumerate(scenes, 1):
        if i not in sel:
            continue
        if sc['right'] and not sc.get('full'):
            if sc['left']:
                emit_plain(dict(sc, right=[]), i, sc['say'])
            emit_calc(sc, i)
        else:
            emit_plain(sc, i, sc['say'])
        print('scene', i, 'of', total)
    with open(work + '/frames.txt', 'w') as fh:
        for p, c in entries:
            fh.write('file ' + chr(39) + os.path.abspath(p) + chr(39) + NL + 'duration %.3f' % c + NL)
        fh.write('file ' + chr(39) + os.path.abspath(entries[-1][0]) + chr(39) + NL)
    with open(work + '/wavs.txt', 'w') as fh:
        for w in wavs:
            fh.write('file ' + chr(39) + os.path.abspath(w) + chr(39) + NL)
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', work + '/wavs.txt', '-c', 'copy', work + '/all.wav'], check=True)
    out = ('out/seg_%s_%d.mp4' % (n, k)) if k is not None else ('out/%s.mp4' % n)
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', work + '/frames.txt', '-i', work + '/all.wav', '-vf', 'fps=10,format=yuv420p', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '30', '-tune', 'stillimage', '-c:a', 'aac', '-b:a', '64k', '-shortest', out], check=True)
    print('built', out, round(sum(c for _, c in entries)), 'sec')

def notes(n):
    L, scenes = load(n)
    with open('videos/U%s.md' % n, 'w') as fh:
        fh.write('# Unit ' + n + ': ' + L['title'] + NL + NL + '## Golden Points' + NL)
        for i, p in enumerate(L['points'], 1):
            fh.write('%d. %s' % (i, p) + NL)
        fh.write(NL + '## Exam answers / numericals (as shown in video)' + NL)
        for i, sc in enumerate(L['scenes'], 1):
            if sc['right']:
                fh.write(NL + '### Scene %d: %s' % (i, sc['cap']) + NL)
                for r in sc['right']:
                    fh.write('    ' + r + NL)

def merge_all():
    os.makedirs('videos', exist_ok=True)
    units = sorted(set(re.findall(r'seg_(\d+)_', ' '.join(glob.glob('out/seg_*.mp4')))))
    for u in units:
        segs = sorted(glob.glob('out/seg_%s_*.mp4' % u), key=lambda p: int(re.findall(r'_(\d+)\.mp4', p)[0]))
        lst = 'out/list_%s.txt' % u
        with open(lst, 'w') as fh:
            for p in segs:
                fh.write('file ' + chr(39) + os.path.abspath(p) + chr(39) + NL)
        subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', lst, '-c', 'copy', 'videos/U%s.mp4' % u], check=True)
        notes(u)
        print('merged unit', u, len(segs), 'segments')

def plan(units, nch):
    import json
    have = sorted(re.findall(r'U(\d+)_', ' '.join(glob.glob('content/U*_*.py'))))
    want = [u.strip() for u in units.split(',') if u.strip()] or have
    inc = [dict(u=u, k=k, n=nch) for u in want if u in have for k in range(nch)]
    print('matrix=' + json.dumps(dict(include=inc)))

def lint(n):
    L, scenes = load(n)
    bad = 0
    for i, sc in enumerate(scenes, 1):
        full, has_r, lsz, rsz = sizes_for(sc)
        d = ImageDraw.Draw(_scr)
        lw = (632 - 36 - 12) if has_r else (W - 24 - 36 - 12)
        bottom = 700 if full else 530
        hl = left_layout(d, sc['left'], 0, 0, lw, lsz)
        hr = right_layout(d, sc['right'], 0, 0, 584, rsz) if has_r else 0
        flag = ''
        if hl > bottom - 90 - 6 or (has_r and hr > bottom - 108 - 6):
            flag = '  <== OVERFLOW'
            bad += 1
        print('scene %2d lsz=%2d rsz=%2d leftH=%4d/%d rightH=%4d say=%3dw%s' % (i, lsz, rsz, hl, bottom - 106, hr, len(sc['say'].split()), flag))
    print('lint done, overflow scenes:', bad)

if __name__ == '__main__':
    a = sys.argv[1:]
    mode = 'edge'
    if '--notts' in a:
        mode = 'none'
        a.remove('--notts')
    c = a[0]
    if c == 'preview':
        preview(a[1])
    elif c == 'lint':
        lint(a[1])
    elif c == 'chunk':
        build(a[1], mode, int(a[2]), int(a[3]))
    elif c == 'merge-all':
        merge_all()
    elif c == 'plan':
        plan(a[1] if len(a) > 1 else '', int(a[2]) if len(a) > 2 else 4)
    elif c == 'notes':
        notes(a[1])
    else:
        build(a[1], mode)
