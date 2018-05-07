#!/usr/bin/env python3
import sys
import statistics

import berekening

# deze module wordt niet gecommit vanwege prive-informatie
import prive

import matplotlib.pyplot as plt
from matplotlib.widgets import Slider

E = berekening.E

dagenrange = (2, 24)
dagenrangerange = range(dagenrange[0], dagenrange[1]+1)
urenrange = range(dagenrange[0]*8, dagenrange[1]*8+1)

uurtarief_bereik = (40, 80, 140)


def simplemain():
    persoonlijke_berekening(12, E(80), True)


def plotmain():
    plt.switch_backend('QT4Agg')

    fig, ax = plt.subplots()
    plt.subplots_adjust(bottom=0.25)

    plt.ylabel('Bedrag')
    plt.xlabel('Dagen per maand')
    #plt.xlabel('Uurtarief')
    plt.axis([
        *dagenrange,
        #uurtarief_bereik[0], uurtarief_bereik[2],
        0, 100000
    ])
    plt.xticks(dagenrangerange)
    #plt.xticks(range(uurtarief_bereik[0], uurtarief_bereik[2]+1, 10))
    plt.yticks(range(0, 100001, 10000))
    plt.grid()

    lines = [plt.plot([], [], label=u)[0] for u in berekening.Berekening.uitkomsten()]
    plt.legend()

    slider1 = Slider(
        plt.axes([0.1, 0.1, 0.8, 0.04]),
        'Uurtarief', 40, 150, 80
        #'Dagen per maand', dagenrange[0], dagenrange[1], statistics.median(dagenrange)
    )

    # for uti in range(60, 125, 10):
    def update(_=None):

        uurtarief = E(slider1.val)
        #dagenmaand = slider1.val

        x = []
        y = []
        for urenmaand in urenrange:
        #for ut in range(uurtarief_bereik[0], uurtarief_bereik[2]+1):
            dagenmaand = urenmaand / 8
            #uurtarief = E(ut)
            res = persoonlijke_berekening(dagenmaand, uurtarief)
            x.append(dagenmaand)
            #x.append(uurtarief)
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
