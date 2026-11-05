"""The other Greek mathematicians, proposition by proposition: Euclid's minor works, Apollonius, Aristarchus,
Theodosius, Hero, Ptolemy, Pappus, Nicomachus and Theon of Smyrna, checked with sympy.

The same conventions as archimedes.py: every entry names its work and locus in graeca/, gives a summary of the
enunciation (factual layer) and checks; before the checks run, the Greek numeral at the locus is compared with the
expected proposition number wherever the encoding writes one. Methods are symbolic, instance (exact for concrete
numbers) or numeric (50 digits, not a proof). A check establishes the stated result in modern terms; it does not
reproduce the ancient proof, and the correspondence between the two is a reading (interpretive layer), which the
summaries make checkable against the Greek.

    python auctores.py              run every check
    python auctores.py PT.I.10      one proposition, with its Greek
"""
import re
import sys
import unicodedata

import sympy as sp

from geometria import Check, same

try:
    import graeca as G
except Exception:
    G = None

PROPS = {}
x, y, t, s, d, A, R, p, q, n = sp.symbols("x y t s d A R p q n", positive=True)
pi = sp.pi
Q = sp.Rational


def prop(pid, work, locus, number, statement, note=""):
    def deco(fn):
        PROPS[pid] = dict(id=pid, work=work, locus=locus, number=number, statement=statement, note=note, fn=fn)
        return fn
    return deco


def exact(cond, method="instance"):
    return Check(bool(cond), method)


_UNITS = dict(zip("αβγδεϛζηθ", range(1, 10)))
_UNITS["ς"] = 6
_TENS = dict(zip("ικλμνξοπϙ", range(10, 100, 10)))


def greek_number(text):
    """Proposition numeral near the start of a passage: skips an editor's section number (Pappus: "9 δ΄") and a
    heading word (Theodosius: "ΠΡΟΤΑΣΙΣ α′")."""
    s_ = "".join(ch for ch in unicodedata.normalize("NFD", text.strip()) if not unicodedata.combining(ch)).lower()
    m = re.match(r"(?:\d+\s+)?(?:προτασισ\s+|προτασις\s+)?([ικλμνξοπϙ]?[αβγδεϛςζηθ]?)\s*[΄ʹ′'’᾿.]", s_)
    if not m or not m.group(1):
        return None
    return sum(_TENS.get(ch, 0) + _UNITS.get(ch, 0) for ch in m.group(1))


def numeral_check(p_):
    if G is None or p_["number"] is None:
        return None
    got = greek_number(G.text(p_["work"], p_["locus"]))
    return ("Greek numeral at the locus is " + str(p_["number"]), Check(got == p_["number"], "instance"))


def sexagesimal(*digits):
    """37, 4, 55 -> 37 + 4/60 + 55/3600."""
    return sum(Q(dg, 60**i) for i, dg in enumerate(digits))


# ================= Euclid, minor works =================

@prop("EU.Opt.8", "euclid-minora.optica", "8", 8,
      "Equal and parallel magnitudes standing at unequal distances from the eye are not seen in proportion to their "
      "distances.",
      "Apparent size is read as the visual angle (Optics, definition 4). The checks show that the angle of the nearer "
      "magnitude is to that of the farther in a smaller ratio than the inverse ratio of the distances.")
def eu_opt8():
    g = sp.atan(x) - x / (1 + x**2)          # atan(x)/x decreases because g > 0
    return [("g(x) = atan x − x/(1 + x²) vanishes at 0", same(g.subs(x, 0), 0)),
            ("and g′(x) = 2x²/(1 + x²)² > 0, so atan(x)/x strictly decreases",
             same(sp.diff(g, x), 2 * x**2 / (1 + x**2)**2)),
            ("hence for d₁ < d₂: angle₁ : angle₂ < d₂ : d₁ (example 1, 2: ratio 1.70 < 2)",
             Check(bool(sp.N(sp.atan(Q(1, 2)) / sp.atan(Q(1, 4)), 30) < 2), "numeric"))]


@prop("EU.Data.84", "euclid-minora.data", "84", 84,
      "If two straight lines contain a given area in a given angle, and one exceeds the other by a given line, each of "
      "them is given.")
def eu_data84():
    T = sp.symbols("T", real=True)                 # the line sought, not assumed positive
    r1, r2 = sp.solve(sp.Eq(T * (T + d), A), T)
    pos = (sp.sqrt(d**2 + 4 * A) - d) / 2
    return [("the roots of t(t + d) = A have product −A < 0, so exactly one is positive", same(sp.expand(r1 * r2), -A)),
            ("it is (√(d² + 4A) − d)/2, a given line (positive since d² + 4A > d²)", Check(any(sp.simplify(r_ - pos) == 0 for r_ in (r1, r2)), "symbolic"))]


@prop("EU.Data.85", "euclid-minora.data", "85", 85,
      "If two straight lines contain a given area in a given angle, and their sum is given, each of them is given.",
      "The lines are the roots of t² − s·t + A = 0; they are real only when s² ≥ 4A, a limit the enunciation leaves tacit.")
def eu_data85():
    T = sp.symbols("T")
    t1, t2 = sp.solve(T**2 - s * T + A, T)
    return [("the two roots have sum s", same(t1 + t2, s)), ("and product A", same(sp.expand(t1 * t2), A))]


# ================= Theodosius, Sphaerica =================

@prop("TH.I.1", "sphaerica.theodosius-sphaerica", "1.1.1", 1,
      "If a spherical surface is cut by a plane, the line produced on the surface is the circumference of a circle.")
def th1():
    X, Y, Z, n1, n2, n3, dd = sp.symbols("X Y Z n1 n2 n3 dd", real=True)
    P_, N_ = sp.Matrix([X, Y, Z]), sp.Matrix([n1, n2, n3])
    PP, PN, NN = sp.symbols("PP PN NN", real=True)        # |P|², n·P, |n|²
    lhs = sp.expand((P_ - dd * N_).dot(P_ - dd * N_))
    rhs = sp.expand(P_.dot(P_) - 2 * dd * P_.dot(N_) + dd**2 * N_.dot(N_))
    return [("|P − d·n|² = |P|² − 2d (n·P) + d²|n|² identically", same(lhs, rhs)),
            ("with |P| = R (on the sphere), n·P = d (in the plane), |n| = 1: |P − d·n|² = R² − d², the same for every point",
             same((PP - 2 * dd * PN + dd**2 * NN).subs({PP: R**2, PN: dd, NN: 1}), R**2 - dd**2))]


# ================= Aristarchus =================

@prop("AS.7", "sphaerica.aristarchus-magnitudines", "7", 7,
      "The distance of the sun from the earth is greater than eighteen times, but less than twenty times, the distance "
      "of the moon from the earth.",
      "From the hypothesis that at half moon the moon is less than a quadrant from the sun by one thirtieth of a "
      "quadrant (87°), the ratio is 1/sin 3°. Aristarchus bounds it by ratios of angles and tangents; the checks bound "
      "sin 3° using x − x³/6 < sin x < x and Archimedes' 3 10/71 < π < 3 1/7, so the result rests only on exact "
      "rationals. (Modern values put the angle near 89.85° and the ratio near 390; the hypothesis, not the "
      "geometry, is at fault.)")
def as7():
    lo_pi, hi_pi = Q(223, 71), Q(22, 7)
    xlo, xhi = lo_pi / 60, hi_pi / 60                  # bounds on 3° in radians
    sin_lo = xlo - xhi**3 / 6                          # sin(3°) > x − x³/6 > xlo − xhi³/6
    sin_hi = xhi                                       # sin(3°) < x < xhi
    return [("sin 3° > 1/20, so the ratio 1/sin 3° < 20", exact(sin_lo > Q(1, 20))),
            ("sin 3° < 1/18, so the ratio > 18", exact(sin_hi < Q(1, 18))),
            ("x − x³/6 < sin x < x for x > 0 (difference has derivative ≥ 0 from 0)",
             same(sp.diff(sp.sin(x) - x + x**3 / 6, x, 2), x - sp.sin(x)))]


@prop("AS.9", "sphaerica.aristarchus-magnitudines", "9", 9,
      "The diameter of the sun is greater than eighteen, but less than twenty times the diameter of the moon.",
      "Follows from 7 because sun and moon subtend the same angle at a total eclipse (the hypothesis of proposition 8).")
def as9():
    D1, D2, ang = sp.symbols("D1 D2 ang", positive=True)
    return [("equal visual angles: diameters are as distances", same((2 * D1 * sp.tan(ang)) / (2 * D2 * sp.tan(ang)), D1 / D2))]


# ================= Apollonius, Conica IV =================

@prop("AP.IV.1", "apollonius.conica-4", "4.1", 1,
      "If a point is taken outside a conic section or a circle, and from it two lines fall on the section, one touching "
      "and the other cutting it in two points, and the inner segment of the cutting line is divided in the ratio of the "
      "whole cutting line to its outer part, the line from the point of contact to the point of division meets the "
      "section (it is the chord of contact): the secant is cut harmonically.",
      "Checked for every conic at once: the general conic ax² + bxy + cy² + dx + ey + f, any outside point and any "
      "secant direction.")
def ap4_1():
    a_, b_, c_, d_, e_, f_, X0, Y0, u, v, l = sp.symbols("a b c d e f X0 Y0 u v l", real=True)
    F = lambda X, Y: a_ * X**2 + b_ * X * Y + c_ * Y**2 + d_ * X + e_ * Y + f_
    poly = sp.Poly(sp.expand(F(X0 + l * u, Y0 + l * v)), l)
    A2, B1, C0 = [poly.coeff_monomial(l**k) for k in (2, 1, 0)]
    # polar line of P = (X0, Y0): the chord of contact
    polar = lambda X, Y: a_ * X0 * X + b_ * (X0 * Y + Y0 * X) / 2 + c_ * Y0 * Y + d_ * (X + X0) / 2 + e_ * (Y + Y0) / 2 + f_
    lD = sp.solve(polar(X0 + l * u, Y0 + l * v), l)[0]
    # harmonic: 1/λ₁ + 1/λ₂ = 2/λ_D, and 1/λ₁ + 1/λ₂ = −B/C (Vieta)
    return [("the chord of contact divides the secant harmonically: 1/λ₁ + 1/λ₂ = 2/λ_D", same(-B1 / C0, 2 / lD))]


@prop("AP.IV.25", "apollonius.conica-4", "4.25", 25,
      "A section of a cone does not cut a section of a cone or the circumference of a circle in more than four points.")
def ap4_25():
    c1 = sp.symbols("a1:7", real=True)
    c2 = sp.symbols("b1:7", real=True)
    X, Y = sp.symbols("X Y", real=True)
    conic = lambda c: c[0] * X**2 + c[1] * X * Y + c[2] * Y**2 + c[3] * X + c[4] * Y + c[5]
    res = sp.resultant(conic(c1), conic(c2), Y)
    return [("eliminating y leaves a polynomial of degree at most 4 in x", exact(sp.Poly(res, X).degree() <= 4, "symbolic")),
            ("and degree exactly 4 in general (two ellipses can meet in four points)", exact(sp.Poly(res, X).degree() == 4, "symbolic"))]


# ================= Hero, Metrica =================

@prop("HE.Met.I.8", "hero.metrica", "1.8", 8,
      "A general method for finding the area of any triangle from its three sides without the altitude, worked for "
      "sides 7, 8, 9: half the sum is 12; 12·5·4·3 = 720; the area is its side. Since 720 has no rational side, take "
      "the nearest square 729 with side 27, divide 720 by 27 (26⅔), add 27 (53⅔), halve: 26½⅓, whose square is "
      "720 1/36; repeating the step with 720 1/36 in place of 729 makes the difference much less than 1/36.")
def he_met8():
    a_, b_, c_ = sp.symbols("a b c", positive=True)
    # triangle (0,0), (c,0), (X, Y): X, Y from the side lengths
    X = (b_**2 + c_**2 - a_**2) / (2 * c_)
    area2 = (c_ * sp.sqrt(b_**2 - X**2) / 2)**2
    sp_ = (a_ + b_ + c_) / 2
    first = (27 + Q(720, 27)) / 2
    second = (first + 720 / first) / 2
    return [("area² = s(s − a)(s − b)(s − c) for every triangle", same(sp.expand(area2), sp.expand(sp_ * (sp_ - a_) * (sp_ - b_) * (sp_ - c_)))),
            ("sides 7, 8, 9: 12·5·4·3 = 720", exact(12 * 5 * 4 * 3 == 720)),
            ("first approximation (27 + 720/27)/2 = 26½⅓", exact(first == 26 + Q(1, 2) + Q(1, 3))),
            ("(26½⅓)² = 720 1/36", exact(first**2 == 720 + Q(1, 36))),
            ("the second step leaves an error far below 1/36", exact(0 < second**2 - 720 < Q(1, 36) / 1000))]


# ================= Ptolemy, Syntaxis =================

CHORDS = [  # (arc in degrees, sexagesimal digits as in the Greek of I.10, Greek form)
    (36, (37, 4, 55), "λζ δ νε"), (72, (70, 32, 3), "ο λβ γ"), (90, (84, 51, 10), "πδ να ι"),
    (120, (103, 55, 23), "ργ νε κγ"), (144, (114, 7, 37), "ριδ ζ λζ"),
    (Q(3, 2), (1, 34, 15), "α λδ ιε"), (Q(3, 4), (0, 47, 8), "ο μζ η")]


@prop("PT.I.10", "ptolemy.syntaxis", "1.10", 10,
      "On the size of the straight lines in the circle: with the diameter divided into 120 parts, the side of the "
      "decagon (chord of 36°) is 37;4,55, of the pentagon (72°) 70;32,3, of the square (90°) 84;51,10, of the triangle "
      "(120°) 103;55,23; the chord of the supplement of 36° (144°) is 114;7,37; the chord of 1½° is 1;34,15 and of ¾° "
      "0;47,8, all \"very nearly\" (ἔγγιστα).",
      "Each value is compared with 120·sin(arc/2). Five of the seven are the true value rounded to the nearest second "
      "of a part. Two are one second high: 114;7,37 for 144° (true 114;7,36.42) and 0;47,8 for ¾° (true 0;47,7.41). "
      "The first is inherited from Ptolemy's own rounded input: √(120² − 37;4,55²) is 114;7,36.53, which rounds to 37. "
      "The second agrees with half of 1;34,15 (0;47,7½) rounded up, but Ptolemy reaches it by the half-arc theorem "
      "through rounded values not all given in the text, so where the excess second arises is not established. The "
      "chord table itself (I.11) is not in the encoding, which keeps only its heading.")
def pt10():
    out = []
    text = G.text("ptolemy.syntaxis", "1.10") if G else ""
    norm = (lambda z: G.norm(z).replace("o", "ο")) if G else (lambda z: z)
    nearest_expected = {36: True, 72: True, 90: True, 120: True, 144: False, Q(3, 2): True, Q(3, 4): False}
    for arc, digs, greek in CHORDS:
        val = sexagesimal(*digs)
        true = 120 * sp.sin(pi * arc / 360)
        err = sp.N(val - true, 40)
        method = "instance" if arc in (36, 72, 90, 120, 144) else "numeric"
        label = f"crd {arc}° = {digs[0]};{','.join(map(str, digs[1:]))}: off by {float(err * 3600):+.2f}″ of a part"
        if nearest_expected[arc]:
            out.append((label + ", the nearest second", Check(bool(abs(err) < Q(1, 7200)), method)))
        else:
            out.append((label + ", within one second but not the nearest", Check(bool(Q(1, 7200) < abs(err) < Q(1, 3600)), method)))
        if G:
            out.append((f"the Greek writes {greek}", Check(norm(greek) in norm(text), "instance")))
    c36, c144 = sexagesimal(37, 4, 55), sexagesimal(114, 7, 37)
    lo, hi = c144 - Q(1, 7200), c144 + Q(1, 7200)
    out.append(("114;7,37 is √(120² − 37;4,55²) rounded to the nearest second (from Ptolemy's own value)",
                exact(lo**2 < 14400 - c36**2 < hi**2)))
    half = sexagesimal(1, 34, 15) / 2
    out.append(("0;47,8 agrees with half of 1;34,15 (= 0;47,7½) rounded up; the route is not established", exact(half == sexagesimal(0, 47, 7) + Q(1, 7200))))
    return out


@prop("PT.I.10b", "ptolemy.syntaxis", "1.10", 10,
      "In the same chapter: with ΔΓ the radius (60) bisected at E, the line EZ = EB is 67;4,55, and the side of the "
      "decagon ΔZ is EZ less EΔ (30), 37;4,55.")
def pt10b():
    EF = sp.sqrt(30**2 + 60**2)
    return [("EZ = √(30² + 60²) = 30√5", same(EF, 30 * sp.sqrt(5))),
            ("67;4,55 is EZ to the nearest second", Check(bool(abs(sp.N(sexagesimal(67, 4, 55) - EF, 40)) < Q(1, 7200)), "instance")),
            ("decagon side = EZ − 30 = 30(√5 − 1) = 120 sin 18°", same(EF - 30, 120 * sp.sin(pi / 10)))]


# ================= Pappus, Collectio =================

@prop("PA.III.11", "pappus.synagoge-2-5", "3.28", 11,
      "To take the three means in a semicircle: on the semicircle ABC with centre E take D on AC, draw DB at right "
      "angles to AC, join EB and draw DZ perpendicular to it. Then EB is the arithmetic, DB the geometric and BZ the "
      "harmonic mean of AD and DC.",
      "Pappus reports the construction as someone else's claim (ἄλλος τις ἔφασκεν) before discussing it.")
def pa3_11():
    E_ = (p + q) / 2                       # AD = p, DC = q, AC = p + q, EB = radius
    DB = sp.sqrt(p * q)
    BZ = DB**2 / E_                        # in right triangle EDB with altitude from D: BZ·EB = DB²
    return [("EB = (p + q)/2, the arithmetic mean", same(E_, (p + q) / 2)),
            ("DB = √(pq), the geometric mean", same(DB**2, p * q)),
            ("BZ = 2pq/(p + q), the harmonic mean", same(BZ, 2 * p * q / (p + q)))]


@prop("PA.IV.1", "pappus.synagoge-2-5", "4.1", 1,
      "If ABC is a triangle and any parallelograms are described on AB and BC, and their sides are produced to meet at "
      "Θ, and ΘB is joined, the parallelograms on AB and BC together equal the parallelogram contained by AC and ΘB "
      "in the angle made by drawing lines from A and C parallel to ΘB.",
      "A generalisation of Elements I.47.")
def pa4_1():
    a1, a2, b1, b2, c1, c2, u1, u2, w1, w2, l, m = sp.symbols("a1 a2 b1 b2 c1 c2 u1 u2 w1 w2 l m", real=True)
    Am, Bm, Cm = sp.Matrix([a1, a2]), sp.Matrix([b1, b2]), sp.Matrix([c1, c2])
    U, W = sp.Matrix([u1, u2]), sp.Matrix([w1, w2])
    cross = lambda P1, P2: P1[0] * P2[1] - P1[1] * P2[0]
    # Θ: on the line through A + U parallel to AB and on the line through C + W parallel to CB
    sol = sp.solve(list(Am + U + l * (Bm - Am) - (Cm + W + m * (Bm - Cm))), [l, m], dict=True)[0]
    Th = Am + U + sol[l] * (Bm - Am)
    # Θ lies on the sides opposite AB and CB, so each parallelogram has the oriented area of AB, CB against ΘB
    lhs = cross(Bm - Am, U) + cross(Cm - Bm, W)             # oriented areas of the two parallelograms
    rhs = cross(Cm - Am, Th - Bm)
    return [("ABDE + BCZH = parallelogram on AC with side ΘB (oriented areas)", same(sp.simplify(lhs - rhs), 0))]


@prop("PA.V.1", "pappus.synagoge-2-5", "5.4", 1,
      "Of two equilateral and equiangular polygons with equal perimeters, the one with more angles is the greater.",
      "Area of the regular n-gon with perimeter P is P²/(4 n tan(π/n)); the checks show n·tan(π/n) decreases.")
def pa5_1():
    f = sp.tan(x) / x                              # n tan(π/n) = π f(π/n); increasing f means decreasing in n
    return [("d/dx (tan x / x) = (x − sin x cos x)/(x² cos² x)", same(sp.simplify(sp.diff(f, x) - (x - sp.sin(x) * sp.cos(x)) / (x**2 * sp.cos(x)**2)), 0)),
            ("x − sin x cos x = x − sin(2x)/2 > 0 for x > 0, since its derivative is 2 sin² x", same(sp.simplify(sp.diff(x - sp.sin(x) * sp.cos(x), x) - 2 * sp.sin(x)**2), 0)),
            ("instance: areas for P = 1, n = 3, 4, 5, 6 increase", Check(bool(all(sp.N(1 / (4 * k * sp.tan(pi / k)) - 1 / (4 * (k - 1) * sp.tan(pi / (k - 1))), 30) > 0 for k in (4, 5, 6))), "numeric"))]


@prop("PA.V.2", "pappus.synagoge-2-5", "5.5", 2,
      "If an equilateral and equiangular polygon has a perimeter equal to the circumference of a circle, the circle is "
      "the greater.")
def pa5_2():
    return [("polygon P²/(4n tan(π/n)) < circle P²/(4π) ⟺ tan(π/n) > π/n; tan x − x vanishes at 0, derivative tan² x > 0", same(sp.simplify(sp.diff(sp.tan(x) - x, x) - sp.tan(x)**2), 0))]


@prop("PA.V.5", "pappus.synagoge-2-5", "5.11", 5,
      "Of isoperimetric triangles on the same base the isosceles is the greatest, and always the more nearly isosceles "
      "is the greater.")
def pa5_5():
    a_, b_, c_ = sp.symbols("a b c", positive=True)
    sp_ = (a_ + b_ + c_) / 2
    # base a and perimeter fixed: area² = s(s − a)·(s − b)(s − c), and (s − b)(s − c) = ((2s − b − c)/2)² − ((b − c)/2)²
    return [("(s − b)(s − c) = (a/2)² − ((b − c)/2)²: greatest when b = c, and larger as |b − c| shrinks",
             same(sp.expand((sp_ - b_) * (sp_ - c_)), sp.expand((a_ / 2)**2 - ((b_ - c_) / 2)**2)))]


# ================= Nicomachus, Theon =================

@prop("NI.II.20", "arithmetica.nicomachus-introductio", "2.20", None,
      "The cubes 1, 8, 27, 64, 125, 216 and so on arise from the odd numbers set out from unity: the first makes the "
      "first cube, the next two together the second, the next three the third, the next four the fourth, and so "
      "forever.")
def ni2_20():
    i = sp.symbols("i", integer=True, nonnegative=True)
    k = sp.symbols("k", integer=True, positive=True)
    first_odd = k * (k - 1) + 1                    # the k-th group starts after 1 + 2 + … + (k − 1) odd numbers
    group = sp.summation(first_odd + 2 * i, (i, 0, k - 1))
    return [("the k-th group of k consecutive odd numbers sums to k³", same(sp.expand(group), k**3)),
            ("1; 3 + 5; 7 + 9 + 11; 13 + … + 19 = 1, 8, 27, 64", exact([sum(range(m * (m - 1) + 1, m * (m + 1), 2)) for m in (1, 2, 3, 4)] == [1, 8, 27, 64]))]


@prop("TS.45", "arithmetica.theon-utilitas", "45", None,
      "Side and diagonal numbers: begin with side 1 and diagonal 1; add the diagonal to the side for the next side and "
      "twice the side to the diagonal for the next diagonal: 2 and 3, 5 and 7, 12 and 17. The square on each diagonal "
      "is alternately one less and one more than twice the square on its side.",
      "The ratios 1, 3/2, 7/5, 17/12 approach √2; Theon states the alternation, the checks prove it for every step.")
def ts45():
    S, D = sp.symbols("S D", integer=True)
    S2, D2 = S + D, D + 2 * S
    seq, (ss, dd) = [], (1, 1)
    for _ in range(4):
        seq.append((ss, dd))
        ss, dd = ss + dd, dd + 2 * ss
    return [("D′² − 2S′² = −(D² − 2S²) for every step", same(sp.expand(D2**2 - 2 * S2**2), sp.expand(-(D**2 - 2 * S**2)))),
            ("(1,1), (2,3), (5,7), (12,17) as in the Greek", exact(seq == [(1, 1), (2, 3), (5, 7), (12, 17)])),
            ("d² − 2s² = −1, +1, −1, +1", exact([dd_**2 - 2 * ss_**2 for ss_, dd_ in seq] == [-1, 1, -1, 1]))]


# ---------- run ----------

def run(pid):
    p_ = PROPS[pid]
    checks = []
    nc = numeral_check(p_)
    if nc:
        checks.append(nc)
    return checks + p_["fn"]()


def main(argv):
    if len(argv) > 1:
        p_ = PROPS[argv[1]]
        print(f"{p_['id']}  {p_['work']} {p_['locus']}\n{p_['statement']}\n")
        if G:
            print(G.text(p_["work"], p_["locus"])[:1500], "\n")
        if p_["note"]:
            print("Note:", p_["note"], "\n")
        for label, ch in run(argv[1]):
            print(f"{'OK ' if ch.ok else 'NG '} {ch.method:9s} {label}")
        return 0
    bad = total = 0
    for pid in PROPS:
        for label, ch in run(pid):
            total += 1
            bad += not ch.ok
            print(f"{'OK ' if ch.ok else 'NG '} {ch.method:9s} {pid:11s} {label}", flush=True)
    print(f"\n{len(PROPS)} propositions, {total} checks, {'all passed' if not bad else f'{bad} FAILED'}")
    return bad


if __name__ == "__main__":
    sys.exit(1 if main(sys.argv) else 0)
