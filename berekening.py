import datetime
import decimal
from decimal import Decimal
E = Decimal

uren_per_werkdag = 8

# belastingconstanten
urencriterium = 1225
mkb_vrijstelling = Decimal("0.14")

# https://www.belastingdienst.nl/wps/wcm/connect/bldcontentnl/belastingdienst/prive/inkomstenbelasting/heffingskortingen_boxen_tarieven/boxen_en_tarieven/overzicht_tarieven_en_schijven/u-hebt-in-2018-de-aow-leeftijd-nog-niet-bereikt
box1schijven = [
    (E(20143), Decimal("0.3655")),
    (E(33995), Decimal("0.4085")),
    (E(68507), Decimal("0.4085")),
    (None    , Decimal("0.5195"))
]
algemene_heffingskorting_bereik = (E(20142), E(68507))
algemene_heffingskorting_pct = Decimal("0.04683")
algemene_heffingskorting_basis = E(2265)


class Berekening:

    def __init__(self, out=None):
        self.out = out

    def bereken(self, dagen_werken_maand, uurtarief, extra_bruto_inkomen=E(0)):

        tijd_betaald, tijd_totaal = self.bereken_uren(
            dagen_werken_maand=dagen_werken_maand,
            tijdfactor_betaald=0.75,
            vakantiefactor=5/52
        )
        self.line()

        bruto_winst = self.bereken_bruto_winst(tijd_betaald, uurtarief=uurtarief)
        self.line()

        kosten = self.bereken_kosten(verzekeringen=[
            ('Bedrijfsaansprakelijkheid', E(150)),
            ('Rechtsbijstand', E(30)),
            # ('Inventaris', E(10)) # is gedekt op persoonlijke inboedel
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
        self.line()

        # bereken inkomstenbelasting over alle inkomsten in box 1
        verzamelinkomen = self.show('Verzamelinkomen',
                                    belastbare_winst + extra_bruto_inkomen - aftrekbare_kosten)
        arbeidsinkomen = self.show('Arbeidsinkomen', winst_uo + extra_bruto_inkomen)
        self.line()
        belasting = self.bereken_belasting(verzamelinkomen, arbeidsinkomen)
        self.line()

        # wat blijft er over na betalen van belasting en privekosten
        netto_inkomen = self.show('Netto inkomen', winst_uo + extra_bruto_inkomen - belasting)
        netto_na_uitgaven = self.show('Na uitgaven', netto_inkomen - aftrekbare_kosten)

        self.show('Maandloon', netto_na_uitgaven / 12)
        self.show('Uurloon', netto_na_uitgaven / uren(tijd_totaal))

        return winst_uo, extra_bruto_inkomen, verzamelinkomen, netto_na_uitgaven

    @staticmethod
    def uitkomsten():
        return [
                'Winst uit onderneming',
                'Extra bruto inkomen',
                'Verzamelinkomen',
                'Netto na uitgaven'
        ]

    def bereken_aftrekbare_kosten(self, tijd_totaal):
        # voor ICT zal AOV zo'n 1 euro per uur zijn
        premie_aov = self.show('Premie AOV', uren(tijd_totaal) * E(1))
        return self.show('Subtotaal aftrekbare kosten', premie_aov)

    def bereken_belasting(self, verzamelinkomen, arbeidsinkomen):

        heffing = E(0)

        # basisheffing met de schijven en zo
        inkomen_over = verzamelinkomen
        for s in range(0, len(box1schijven)):
            onderschijf = box1schijven[s-1] if s > 0 else None
            dezeschijf = box1schijven[s]
            schijfnaam = 'Schijf ' + str(s+1)

            # laatste schijf
            if dezeschijf[0] is None:
                inkomen_in_deze_schijf = self.show('Inkomen ' + schijfnaam, inkomen_over)
            else:
                schijfgrootte = dezeschijf[0] - (E(0) if onderschijf is None else onderschijf[0])
                inkomen_in_deze_schijf = self.show('Inkomen ' + schijfnaam, min(schijfgrootte, inkomen_over))
            heffing += self.show('Heffing ' + schijfnaam, inkomen_in_deze_schijf * dezeschijf[1])
            inkomen_over -= inkomen_in_deze_schijf

        # algemene heffingskorting
        ahmin, ahmax = algemene_heffingskorting_bereik
        if verzamelinkomen <= ahmin:
            ahk = algemene_heffingskorting_basis
        elif verzamelinkomen > ahmax:
            ahk = E(0)
        else:
            ahk = algemene_heffingskorting_basis - algemene_heffingskorting_pct * (verzamelinkomen - ahmin)
        heffing -= self.show('Algemene heffingskorting', ahk)

        # arbeidskorting
        # meh, geen zin al deze getallen netjes bovenaan te zetten /shrug
        if arbeidsinkomen <= E(9468):
            arbeidskorting = Decimal("0.01764") * arbeidsinkomen
        elif arbeidsinkomen <= E(20450):
            arbeidskorting = E(167) + Decimal("0.28064") * (arbeidsinkomen - E(9468))
        elif arbeidsinkomen <= E(33112):
            arbeidskorting = E(3249)
        elif arbeidsinkomen <= E(123362):
            arbeidskorting = E(3249) - Decimal("0.036") * (arbeidsinkomen - E(33112))
        else:
            arbeidskorting = E(0)
        heffing -= self.show('Arbeidskorting', arbeidskorting)

        return self.show('Totale heffing box 1', heffing)

    def bereken_kosten(self, verzekeringen):
        kosten = self.show('Verzekeringen', sum(b * 12 for a, b in verzekeringen))
        kosten += self.show('Laptop', E(600))  # 1800 per 3 jaar
        kosten += self.show('Servers', E(30) * 12)
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
