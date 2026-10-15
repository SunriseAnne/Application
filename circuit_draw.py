# -*- coding: utf-8 -*-
"""Desenarea schemei cu porți logice (ȘI, SAU, NU, XOR) cu matplotlib."""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Circle
from boolean_core import kids

XS, HW = 2.6, 0.55          # distanța dintre nivele, semi-lățimea porții
NUME = {'and': 'ȘI', 'or': 'SAU', 'xor': 'SAU-EX', 'not': 'NU'}


def _build(e, ctr):
    ch = [_build(c, ctr) for c in kids(e)]
    if not ch:
        y, lvl = ctr[0], 0
        ctr[0] += 1.3
    else:
        y, lvl = sum(c['y'] for c in ch) / len(ch), 1 + max(c['lvl'] for c in ch)
    return dict(e=e, ch=ch, y=y, lvl=lvl)


def _q(p0, p1, p2, n=30):
    s = np.linspace(0, 1, n)
    return list(zip((1 - s) ** 2 * p0[0] + 2 * (1 - s) * s * p1[0] + s ** 2 * p2[0],
                    (1 - s) ** 2 * p0[1] + 2 * (1 - s) * s * p1[1] + s ** 2 * p2[1]))


def _gate(ax, t, x, y, h):
    xs, r, w = x - HW, h / 2, 2 * HW
    if t == 'and':
        a = np.linspace(-np.pi / 2, np.pi / 2, 30)
        pts = [(xs, y - r), (xs, y + r), (xs + w - r, y + r)] + \
              [(xs + w - r + r * np.cos(b), y + r * np.sin(b)) for b in a[::-1]] + [(xs + w - r, y - r)]
    else:
        pts = _q((xs, y - r), (xs + .65 * w, y - r), (xs + w, y)) + \
              _q((xs + w, y), (xs + .65 * w, y + r), (xs, y + r)) + _q((xs, y + r), (xs + .3, y), (xs, y - r))
        if t == 'xor':
            c = _q((xs - .12, y - r), (xs + .18, y), (xs - .12, y + r))
            ax.plot(*zip(*c), color='k', lw=1.6)
    ax.add_patch(Polygon(pts, closed=True, fc='white', ec='k', lw=1.6, zorder=3))


def deseneaza(e, nume="F"):
    ctr = [0.0]
    T = _build(e, ctr)
    fig, ax = plt.subplots()
    xg = lambda n: 1.7 + XS * (n['lvl'] - 1)
    ox = lambda n: 0.0 if n['lvl'] == 0 else xg(n) + (0.4 if n['e'][0] == 'not' else HW)

    def wire(xo, yo, xi, yi):
        xm = (xo + xi) / 2
        ax.plot([xo, xm, xm, xi], [yo, yo, yi, yi], color='k', lw=1.3, zorder=1)

    def draw(n):
        t, x, y = n['e'][0], None, n['y']
        if n['lvl'] == 0:
            ax.text(-0.12, y, str(n['e'][1]), ha='right', va='center', fontsize=13, fontweight='bold')
            return
        x = xg(n)
        for c in n['ch']:
            draw(c)
        k = len(n['ch'])
        if t == 'not':
            ax.add_patch(Polygon([(x - .4, y - .35), (x - .4, y + .35), (x + .25, y)], fc='white', ec='k', lw=1.6, zorder=3))
            ax.add_patch(Circle((x + .32, y), .07, fc='white', ec='k', lw=1.6, zorder=3))
            wire(ox(n['ch'][0]), n['ch'][0]['y'], x - .4, y)
            cap = .55
        else:
            h = min(1.3, max(0.9, 0.45 * k))
            _gate(ax, t, x, y, h)
            offs = np.linspace(-.3 * h, .3 * h, k) if k > 1 else [0]
            for c, d in zip(n['ch'], offs):
                dep = (0 if t == 'and' else (.15 if t == 'or' else .03)) * (1 - (d / (h / 2)) ** 2)
                wire(ox(c), c['y'], x - HW + dep + (-0.12 if t == 'xor' else 0), y + d)
            cap = h / 2 + .2
        ax.text(x, y + cap, NUME[t], ha='center', va='top', fontsize=7, color='#555')

    draw(T)
    xo = ox(T)
    ax.plot([xo, xo + 1.0], [T['y'], T['y']], color='k', lw=1.3)
    ax.text(xo + 1.1, T['y'], nume, ha='left', va='center', fontsize=13, fontweight='bold', color='#b00020')
    xmax, ymax = xo + 2.0, max(ctr[0], 1.3)
    ax.set_xlim(-1.0, xmax)
    ax.set_ylim(ymax, -0.9)
    ax.set_aspect('equal')
    ax.axis('off')
    fig.set_size_inches(max(4.0, (xmax + 1) * 0.55), max(2.0, (ymax + .9) * 0.55))
    fig.patch.set_facecolor('white')
    return fig
