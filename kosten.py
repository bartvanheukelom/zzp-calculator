#!/usr/bin/env python3
import sys

import berekening

# deze module wordt niet gecommit vanwege prive-informatie
import prive

import matplotlib.pyplot as plt
from matplotlib.widgets import Slider

E = berekening.E

dagenrange = (4, 20)
dagenrangerange = range(dagenrange[0], dagenrange[1]+1)
urenrange = range(dagenrange[0]*8, dagenrange[1]*8+1)


def simplemain():
    persoonlijke_berekening(12, E(80), True)


def plotmain():
    plt.switch_backend('QT4Agg')

    fig, ax = plt.subplots()
    plt.subplots_adjust(bottom=0.25)

    plt.ylabel('Bedrag')
    plt.xlabel('Dagen per maand')
    plt.axis([
        *dagenrange,
        0, 100000
    ])
    plt.xticks(dagenrangerange)
    plt.yticks(range(0, 100001, 10000))
    plt.grid()

    lines = [plt.plot([], [], label=u)[0] for u in berekening.Berekening.uitkomsten()]
    plt.legend()

    slider_uurtarief = Slider(
        plt.axes([0.1, 0.1, 0.8, 0.04]),
        'Uurtarief', 40, 150, 80
    )

    # for uti in range(60, 125, 10):
    def update(_=None):
        uurtarief = E(slider_uurtarief.val)
        x, y = plot_dagenmaand_nettoinkomen(uurtarief)
        for i, ln in enumerate(lines):
            ln.set_xdata(x)
            ln.set_ydata([e[i] for e in y])
        fig.canvas.draw_idle()
    update()
    slider_uurtarief.on_changed(update)

    plt.get_current_fig_manager().window.showMaximized()
    plt.show()


def persoonlijke_berekening(dagenmaand, uurtarief, printit=False):
    return berekening.Berekening(out=print if printit else None).bereken(
        dagenmaand, uurtarief,
        extra_bruto_inkomen=prive.brutoloon_baan(dagenmaand)
    )


def plot_dagenmaand_nettoinkomen(uurtarief):
    x = []
    y = []
    for urenmaand in urenrange:
        dagenmaand = urenmaand / 8
        res = persoonlijke_berekening(dagenmaand, uurtarief)
        x.append(dagenmaand)
        y.append(res)
    return x, y


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'simple':
        simplemain()
    else:
        plotmain()
