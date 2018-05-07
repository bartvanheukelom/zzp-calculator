import datetime
import decimal
from decimal import Decimal
E = Decimal

uren_per_werkdag = 8

# belastingconstanten
urencriterium = 1225
mkb_vrijstelling = Decimal("0.14")


class Berekening:

    def __init__(self, out=None):
        self.out = out

    def bereken(self, dagen_werken_maand, uurtarief, extra_bruto_inkomen=E(0)):

        tijd_betaald, tijd_totaal = self.bereken_uren(
            dagen_werken_maand=dagen_werken_maand,
            tijdfactor_betaald=0.75,
            vakantiefactor=1/12
        )
        self.line()

        bruto_winst = self.bereken_bruto_winst(tijd_betaald, uurtarief=uurtarief)
        self.line()

        kosten = self.bereken_kosten(verzekeringen=[
            ('Bedrijfsaansprakelijkheid', E(150)),
            ('Rechtsbijstand', E(30)),
            # ('Inventaris', E(10)) # is gedekt op persoonlijke inboedel
            # TODO
        ])
        self.line()

        winst_uo = self.show("Winst uit onderneming", bruto_winst - kosten)
        self.line()

        # verwerk belastingaftrek
        belastbare_winst = self.bereken_belastbare_winst(winst_uo, tijd_totaal)
        self.line()

        # --- vanaf hier komen geld uit onderneming en andere stromingen samen! --- #

        # bereken aftrekbare prive-kostenposten die zonder zaak niet nodig zouden zijn
        aftrekbare_kosten = self.bereken_aftrekbare_kosten(tijd_totaal)

        # bereken inkomstenbelasting over alle inkomsten in box 1
        belasting = self.bereken_belasting(belastbare_winst + extra_bruto_inkomen - aftrekbare_kosten)
        self.line()

        # wat blijft er over na betalen van belasting en privekosten
        netto_inkomen = self.show('Netto inkomen', winst_uo + extra_bruto_inkomen - belasting)
        netto_na_uitgaven = self.show('Na uitgaven', netto_inkomen - aftrekbare_kosten)

        self.show('Maandloon', netto_na_uitgaven / 12)
        self.show('Uurloon', netto_na_uitgaven / uren(tijd_totaal))

        return winst_uo, extra_bruto_inkomen, netto_na_uitgaven

    @staticmethod
    def uitkomsten():
        return [
                'Winst uit onderneming',
                'Extra bruto inkomen',
                'Netto na uitgaven'
        ]

    def bereken_aftrekbare_kosten(self, tijd_totaal):
        # voor ICT zal AOV zo'n 1 euro per uur zijn
        premie_aov = self.show('Premie AOV', uren(tijd_totaal) * E(1))
        return self.show('Subtotaal aftrekbare kosten', premie_aov)

    def bereken_belasting(self, belastbare_winst):
        return self.show('Belasting', Decimal(0.2) * belastbare_winst)

    def bereken_kosten(self, verzekeringen):
        kosten = self.show('Verzekeringen', sum(b * 12 for a, b in verzekeringen))
        return self.show("Kosten", kosten)

    def bereken_belastbare_winst(self, winst_uo, tijd_totaal):
        belastbaar = winst_uo

        if uren(tijd_totaal) >= urencriterium:
            belastbaar -= self.show('Zelfstandigenaftrek', E(7280))
            belastbaar -= self.show('Startersaftrek', E(2123))

        belastbaar -= self.show('MKB-vrijstelling',
                                (mkb_vrijstelling * belastbaar).to_integral_exact(decimal.ROUND_CEILING))

        return self.show("Belastbare winst", belastbaar)

    def bereken_bruto_winst(self, tijd_betaald, uurtarief):
        return self.show("Omzet / bruto winst", uurtarief * uren(tijd_betaald))

    def bereken_uren(self, dagen_werken_maand, tijdfactor_betaald, vakantiefactor):
        werkdag = datetime.timedelta(hours=uren_per_werkdag)
        werktijd = (werkdag * dagen_werken_maand * 12) * (1-vakantiefactor)

        tijd_betaald = self.show("Uren declarabel", werktijd * tijdfactor_betaald)
        tijd_onbetaald = self.show("Uren overig", werktijd - tijd_betaald)
        tijd_totaal = self.show("Uren totaal", tijd_betaald + tijd_onbetaald)

        return tijd_betaald, tijd_totaal

    def show(self, label, amount):
        if self.out:
            if isinstance(amount, Decimal):
                s = fmtcur(amount)
            else:
                s = str(uren(amount))
            self.out(label + ': ' + s)
        return amount

    def line(self):
        if self.out:
            self.out('-----------------------------')


def uren(t):
    return Decimal(t.days * 24) + Decimal(t.seconds / 3600)


def fmthour(x):
    u = uren(x)
    resturen = u % uren_per_werkdag
    dagen = (u - resturen) / uren_per_werkdag
    return str(int(dagen)) + 'D ' + str(int(resturen)) + 'U'


def fmtcur(x):
    return '€ ' + str(round(x, 2))
