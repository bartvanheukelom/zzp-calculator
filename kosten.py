#!/usr/bin/env python3
import sys
import statistics
from enum import Enum

import berekening

# deze module wordt niet gecommit vanwege prive-informatie
import prive

import numpy
import matplotlib
import matplotlib.ticker
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider

E = berekening.E

dagenrange = (2, 24)
dagenrangerange = range(dagenrange[0], dagenrange[1]+1)

uurtarief_bereik = (40, 80, 140)


class Var(Enum):
    DAGEN = 0
    UREN = 1


def simplemain():
    persoonlijke_berekening(12, E(80), True)


def plotmain(xvar=Var.DAGEN):

    # maak mooier
    plt.switch_backend('QT4Agg')

    fig, ax_ = plt.subplots()
    ax: plt.Axes = ax_

    # x-as
    if xvar == Var.DAGEN:
        plt.xlabel('Dagen per maand')
        plt.xlim(dagenrange)
        plt.xticks(dagenrangerange)
    else:
        plt.xlabel('Uurtarief')
        plt.xlim(uurtarief_bereik[0], uurtarief_bereik[2])
        plt.xticks(range(uurtarief_bereik[0], uurtarief_bereik[2]+1, 10))

    # y-as
    plt.ylabel('Bedrag')
    plt.ylim(0, 100000)
    plt.yticks(range(0, 100001, 10000))
    ax.get_yaxis().set_major_formatter(matplotlib.ticker.FuncFormatter(lambda x, p: berekening.fmtcur(x)))

    plt.grid()

    # welke lijnen komen er
    lines = [plt.plot([], [], label=u)[0] for u in berekening.Berekening.uitkomsten()]
    plt.legend()

    # voeg een slider toe
    plt.subplots_adjust(bottom=0.25)
    slidervar = Var.UREN if xvar == Var.DAGEN else Var.DAGEN
    if slidervar == Var.DAGEN:
        sliderargs = 'Dagen per maand', dagenrange[0], dagenrange[1], int(statistics.median(dagenrange))
    else:
        sliderargs = 'Uurtarief', uurtarief_bereik[0], uurtarief_bereik[2], uurtarief_bereik[1]
    slider1 = Slider(
        plt.axes([0.1, 0.1, 0.8, 0.04]),
        *sliderargs
    )

    def update(_=None):
        x = []
        y = []
        if xvar == Var.DAGEN:
            uurtarief = E(slider1.val)
            for dagenmaand in numpy.linspace(*dagenrange, 100):
                res = persoonlijke_berekening(dagenmaand, uurtarief)
                x.append(dagenmaand)
                y.append(res)
        else:
            dagenmaand = slider1.val
            for ut in range(uurtarief_bereik[0], uurtarief_bereik[2]+1):
                uurtarief = E(ut)
                res = persoonlijke_berekening(dagenmaand, uurtarief)
                x.append(uurtarief)
                y.append(res)

        for i, ln in enumerate(lines):
            ln.set_xdata(x)
            ln.set_ydata([e[i] for e in y])
        fig.canvas.draw_idle()

    update()
    slider1.on_changed(update)

    plt.get_current_fig_manager().window.showMaximized()
    plt.show()


def persoonlijke_berekening(dagenmaand, uurtarief, printit=False):
    return berekening.Berekening(out=print if printit else None).bereken(
        dagenmaand, uurtarief,
        extra_bruto_inkomen=prive.brutoloon_baan(dagenmaand)
    )


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'simple':
        simplemain()
    else:
        plotmain()
