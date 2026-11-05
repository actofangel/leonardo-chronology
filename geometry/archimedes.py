"""Archimedes, proposition by proposition: the enunciations of his works checked with sympy.

Each entry names the work and locus in graeca/archimedes.json (Mugler's edition as encoded by First1KGreek), the
proposition number written in the Greek, a summary of the enunciation (factual layer: what the text states), and
checks. Before any check runs, the Greek numeral at the locus is read from the text and compared with the expected
number, so a shift in the encoding's numbering (as in De conoidibus from proposition 23 on) cannot pass unnoticed.

Verification methods, as in geometria.py:
  symbolic  holds identically in general symbols
  instance  holds exactly for concrete numbers (here mostly Archimedes' own rational values)
  numeric   confirmed to 50 digits; not a proof

What a check establishes is the truth of the stated result in modern terms (coordinates, integrals, exact
arithmetic). It does not reproduce Archimedes' method of proof (exhaustion, the lever, the Method). That the
modern computation and the Greek enunciation say the same thing is itself a reading of the text and belongs to the
interpretive layer; the summaries are given so that reading can be checked against the Greek.

    python archimedes.py                  run every check
    python archimedes.py SC.I.33          one proposition, with its Greek enunciation
"""
import re
import sys
import unicodedata

import sympy as sp

from geometria import Check, same

try:
    import graeca as G
except Exception:  # the checks still run without the Greek layer
    G = None

PROPS = {}
R, h, H, a, b, c, r1, r2, s, u, v, x, y, t, k, n = sp.symbols("R h H a b c r1 r2 s u v x y t k n", positive=True)
pi = sp.pi


def prop(pid, work, locus, number, statement, note="", transmission=""):
    def deco(fn):
        PROPS[pid] = dict(id=pid, work=f"archimedes.{work}", locus=locus, number=number,
                          statement=statement, note=note, transmission=transmission, fn=fn)
        return fn
    return deco


def exact(cond, method="instance"):
    """An exact inequality or identity between rationals or with a provable sign."""
    return Check(bool(cond), method)


def sign_positive(expr, method="symbolic"):
    """expr > 0 for all positive symbols, shown by factoring into factors with evident sign."""
    f = sp.factor(sp.simplify(expr))
    return Check(bool(f.is_positive), method)


def integral(f, *lims):
    return sp.integrate(f, *lims)


# ---------- Greek numerals ----------

_UNITS = dict(zip("αβγδεϛζηθ", range(1, 10)))
_UNITS["ς"] = 6
_TENS = dict(zip("ικλμνξοπϙ", range(10, 100, 10)))


def greek_number(text):
    """The proposition numeral at the start of a passage (κδ΄ -> 24), or None."""
    s = "".join(ch for ch in unicodedata.normalize("NFD", text.strip()) if not unicodedata.combining(ch))
    m = re.match(r"([ικλμνξοπϙ]?[αβγδεϛςζηθ]?)\s*[΄ʹ'’᾿.]?", s)
    if not m or not m.group(1):
        return None
    tok = m.group(1)
    return sum(_TENS.get(ch, 0) + _UNITS.get(ch, 0) for ch in tok)


def numeral_check(p):
    if G is None or p["number"] is None:
        return None
    text = G.text(p["work"], p["locus"])
    got = greek_number(text)
    return ("Greek numeral at the locus is " + str(p["number"]), Check(got == p["number"], "instance"))


# ================= Dimensio circuli =================

@prop("DC.1", "dimensio-circuli", "1", 1,
      "Every circle is equal to a right triangle with one leg equal to the radius and the other equal to the circumference.")
def dc1():
    return [("π r² = ½ · r · 2π r", same(pi * R**2, sp.Rational(1, 2) * R * 2 * pi * R))]


@prop("DC.2", "dimensio-circuli", "2", 2,
      "A circle has to the square on its diameter the ratio 11 : 14.",
      "True only with π replaced by 22/7, the upper bound of proposition 3, on which it depends although it "
      "precedes it in the transmitted order. The checks show both the dependence and the size of the error.")
def dc2():
    return [("(22/7)/4 = 11/14 exactly", exact(sp.Rational(22, 7) / 4 == sp.Rational(11, 14))),
            ("π/4 lies below 11/14, by less than 1/2500", Check(bool(0 < sp.Rational(11, 14) - pi / 4 < sp.Rational(1, 2500)), "symbolic"))]


@prop("DC.3", "dimensio-circuli", "3", 3,
      "The circumference of every circle is three times the diameter and exceeds it by less than one seventh "
      "but more than ten seventy-firsts of the diameter.",
      "The checks redo Archimedes' arithmetic with his own numbers as they stand in the Greek (306 : 153, 265 : 153, "
      "571, 591⅛, 1162⅛, 1172⅛, 2334¼, 2339¼, 4673½ for the circumscribed 96-gon; 1351 : 780, 1560, 2911, 3013¾, "
      "1823 : 240, 1838 9/11, 1007 : 66, 1009⅙, 2016⅙, 2017¼ for the inscribed one). Each square root he bounds is "
      "bounded the right way, and each final ratio yields his bound. In the encoding the fraction sign ½ appears as "
      "\"U+2220\" and the numeral 96 as \"(??)ς\".")
def dc3():
    Q = sp.Rational
    ch = []
    # circumscribed polygon: lower bounds for cot(θ) with θ = 30°, 15°, 7.5°, 3.75°, 1.875° (times 153)
    ch.append(("√3 > 265/153 (153² · 3 > 265²)", exact(153**2 * 3 > 265**2)))
    a_, hyp = Q(265), Q(306)
    steps = [(Q(591) + Q(1, 8), "591⅛"), (Q(1172) + Q(1, 8), "1172⅛"), (Q(2339) + Q(1, 4), "2339¼")]
    sums = []
    names = iter(["571", "1162⅛", "2334¼"])
    for bound, label in steps:
        a_ = a_ + hyp
        sums.append(a_)
        ch.append((f"√({next(names)}² + 153²) > {label}", exact(a_**2 + 153**2 > bound**2)))
        hyp = bound
    a_ = a_ + hyp
    ch.append(("the cotangent chain reaches 4673½ : 153", exact(a_ == Q(4673) + Q(1, 2))))
    ch.append(("intermediate sums 571, 1162⅛, 2334¼ as in the Greek", exact(sums == [571, Q(1162) + Q(1, 8), Q(2334) + Q(1, 4)])))
    ch.append(("perimeter of circumscribed 96-gon : diameter = 14688 : 4673½ < 3 1/7", exact(Q(14688) / (Q(4673) + Q(1, 2)) < Q(22, 7))))
    # inscribed polygon: upper bounds (times 780, rescaled as Archimedes does)
    ch.append(("√3 < 1351/780 (1351² > 3 · 780²)", exact(1351**2 > 3 * 780**2)))
    ch.append(("√(2911² + 780²) < 3013¾", exact(2911**2 + 780**2 < (Q(3013) + Q(3, 4))**2)))
    ch.append(("2911 + 3013¾ = 5924¾, and 5924¾ : 780 = 1823 : 240", exact(2911 + Q(3013) + Q(3, 4) == Q(5924) + Q(3, 4) and (Q(5924) + Q(3, 4)) / 780 == Q(1823, 240))))
    ch.append(("√(1823² + 240²) < 1838 9/11", exact(1823**2 + 240**2 < (Q(1838) + Q(9, 11))**2)))
    ch.append(("1823 + 1838 9/11 = 3661 9/11, and 3661 9/11 : 240 = 1007 : 66", exact((1823 + Q(1838) + Q(9, 11)) / 240 == Q(1007, 66))))
    ch.append(("√(1007² + 66²) < 1009⅙", exact(1007**2 + 66**2 < (Q(1009) + Q(1, 6))**2)))
    ch.append(("√(2016⅙² + 66²) < 2017¼", exact((Q(2016) + Q(1, 6))**2 + 66**2 < (Q(2017) + Q(1, 4))**2)))
    ch.append(("perimeter of inscribed 96-gon : diameter > 6336 : 2017¼ > 3 10/71", exact(Q(6336) / (Q(2017) + Q(1, 4)) > Q(223, 71))))
    ch.append(("so 3 10/71 < π < 3 1/7", Check(bool(Q(223, 71) < pi < Q(22, 7)), "symbolic")))
    return ch


# ================= De sphaera et cylindro =================

@prop("SC.I.13", "sphaera-cylindrus", "1.13", 13,
      "The surface of any right cylinder, excluding the bases, is equal to a circle whose radius is a mean "
      "proportional between the side of the cylinder and the diameter of its base.")
def sc13():
    return [("2π r·H = π (√(H·2r))²", same(2 * pi * R * H, pi * (sp.sqrt(H * 2 * R))**2))]


@prop("SC.I.14", "sphaera-cylindrus", "1.14", 14,
      "The surface of any isosceles cone, excluding the base, is equal to a circle whose radius is a mean "
      "proportional between the side of the cone and the radius of its base.")
def sc14():
    side = sp.sqrt(R**2 + H**2)
    lateral = integral(2 * pi * (R * t) * side, (t, 0, 1))  # sum of rings of radius R·t along the side
    return [("lateral surface (integral over the side) = π · side · r", same(lateral, pi * side * R)),
            ("= circle of radius √(side · r)", same(lateral, pi * (sp.sqrt(side * R))**2))]


@prop("SC.I.16", "sphaera-cylindrus", "1.16", 16,
      "If an isosceles cone is cut by a plane parallel to the base, the surface between the parallel planes is equal "
      "to a circle whose radius is a mean proportional between the side between the planes and the sum of the radii "
      "of the two circles.")
def sc16():
    side = sp.sqrt((r2 - r1)**2 + H**2)
    frustum = integral(2 * pi * (r1 + (r2 - r1) * t) * side, (t, 0, 1))
    return [("lateral surface of the frustum = π · side · (r₁ + r₂)", same(frustum, pi * side * (r1 + r2)))]


@prop("SC.I.33", "sphaera-cylindrus", "1.33", 33,
      "The surface of any sphere is four times its greatest circle.")
def sc33():
    surf = integral(2 * pi * R * sp.sin(t) * R, (t, 0, pi))
    return [("∫ 2π R sin θ · R dθ = 4 π R²", same(surf, 4 * pi * R**2))]


@prop("SC.I.34", "sphaera-cylindrus", "1.34", 34,
      "Any sphere is four times the cone with base equal to the greatest circle and height equal to the radius. "
      "Corollary: the cylinder with base the greatest circle and height the diameter is half as large again as the "
      "sphere, and its surface with the bases is half as large again as the surface of the sphere.")
def sc34():
    V = integral(pi * (R**2 - x**2), (x, -R, R))
    cone = pi * R**2 * R / 3
    cyl_v, cyl_s = pi * R**2 * 2 * R, 2 * pi * R * 2 * R + 2 * pi * R**2
    return [("sphere = 4 · cone(base πR², height R)", same(V, 4 * cone)),
            ("corollary: cylinder = 3/2 · sphere (volume)", same(cyl_v, sp.Rational(3, 2) * V)),
            ("corollary: cylinder surface with bases = 3/2 · sphere surface", same(cyl_s, sp.Rational(3, 2) * 4 * pi * R**2))]


@prop("SC.I.42", "sphaera-cylindrus", "1.42", 42,
      "The surface of any segment of a sphere less than a hemisphere is equal to a circle whose radius is the line "
      "drawn from the vertex of the segment to the circumference of its base. (I.43: the same for a segment greater "
      "than a hemisphere.)")
def sc42():
    zone = integral(2 * pi * R, (x, R - h, R))          # Archimedes' result in modern form: area of zone = 2πRh
    chord2 = (R - (R - h))**2 + (R**2 - (R - h)**2)       # vertex (R,0) to rim (R-h, √(R²-(R-h)²))
    return [("surface of the cap of height h = 2π R h", same(zone, 2 * pi * R * h)),
            ("(vertex to rim)² = 2 R h, so cap = π · (vertex to rim)², for any h in (0, 2R)", same(zone, pi * chord2))]


@prop("SC.I.44", "sphaera-cylindrus", "1.44", 44,
      "Any sector of a sphere is equal to the cone with base equal to the surface of the segment of the sphere in the "
      "sector and height equal to the radius.")
def sc44():
    # sector = cap + cone from centre to the base circle of the cap
    cap = integral(pi * (R**2 - x**2), (x, R - h, R))
    cone = pi * (R**2 - (R - h)**2) * (R - h) / 3
    return [("sector = (1/3) · (2π R h) · R", same(cap + cone, sp.Rational(1, 3) * 2 * pi * R * h * R))]


@prop("SC.II.2", "sphaera-cylindrus", "2.2", 2,
      "Any segment of a sphere is equal to the cone with the same base and with height to the height of the segment "
      "as the radius together with the height of the remaining segment is to the height of the remaining segment.")
def sc2_2():
    seg = integral(pi * (R**2 - x**2), (x, R - h, R))
    Hrem = 2 * R - h
    base = pi * (R**2 - (R - h)**2)
    cone_height = h * (R + Hrem) / Hrem
    return [("segment = cone(base of segment, height h·(R + h′)/h′), h′ = 2R − h", same(seg, base * cone_height / 3))]


@prop("SC.II.4", "sphaera-cylindrus", "2.4", 4,
      "To cut a given sphere by a plane so that the segments have to one another a given ratio.",
      "Archimedes reduces the problem to cutting a line under a solid condition, whose solution he promises and "
      "Eutocius supplies by conics. In modern terms the condition is a cubic in the height of the segment; the checks "
      "show that the cubic always has exactly one admissible root, so the problem is always solvable.")
def sc2_4():
    m = sp.symbols("m", positive=True)  # given ratio, segment : remainder = m
    V = lambda z: pi * z**2 * (3 * R - z) / 3
    eq = sp.expand(V(h) - m * V(2 * R - h))
    deg = sp.degree(sp.Poly(eq, h))
    # V(h)/V(2R-h) increases strictly from 0 to ∞ on (0, 2R): derivative of V(h) − m V(2R−h) is positive there
    deriv = sp.factor(sp.diff(eq, h))
    return [("the condition is a cubic in h", exact(deg == 3, "symbolic")),
            ("V(h) − m·V(2R − h) is strictly increasing on (0, 2R)", Check(bool(sp.simplify(deriv - pi * (m + 1) * h * (2 * R - h)) == 0), "symbolic")),
            ("it is −m·(4/3)πR³ at h = 0 and +(4/3)πR³ at h = 2R, so exactly one root lies between",
             Check(bool(sp.simplify(eq.subs(h, 0) + m * sp.Rational(4, 3) * pi * R**3) == 0 and sp.simplify(eq.subs(h, 2 * R) - sp.Rational(4, 3) * pi * R**3) == 0), "symbolic"))]


@prop("SC.II.8", "sphaera-cylindrus", "2.8", 8,
      "If a sphere is cut by a plane not through the centre, the greater segment has to the less a ratio less than "
      "the duplicate and greater than the sesquialterate of the ratio of the surface of the greater to that of the less.")
def sc2_8():
    # heights x > y of the two segments, x + y = 2R; surfaces are 2πRx, 2πRy, so surface ratio is x/y
    X, Y = u**2, v**2           # heights x = u², y = v² with u > v > 0; segment volumes ∝ z²(3R − z)
    Rr = (X + Y) / 2
    V = lambda z: z**2 * (3 * Rr - z)
    upper = (X / Y)**2 * V(Y) - V(X)                  # > 0 means V₁ : V₂ < (x/y)²
    lower = V(X) * v**3 - V(Y) * u**3                # > 0 means V₁ : V₂ > (x/y)^{3/2} (multiplied by v³·V(y) > 0)
    return [("(S₁:S₂)²·V₂ − V₁ = u⁴(u − v)(u + v) > 0 for u > v", same(upper, u**4 * (u - v) * (u + v))),
            ("V₁·v³ − V₂·u³ = u³v³(u − v)³/2 > 0 for u > v", same(lower, u**3 * v**3 * (u - v)**3 / 2))]


@prop("SC.II.9", "sphaera-cylindrus", "2.9", 9,
      "Of all spherical segments contained by equal surfaces, the hemisphere is the greatest.")
def sc2_9():
    K = sp.symbols("K", positive=True)        # fixed surface S = 2πK, K = R·h
    Vh = pi * h**2 * (3 * K / h - h) / 3       # R = K/h
    crit = sp.solve(sp.diff(Vh, h), h)
    return [("dV/dh = π(K − h²) vanishes only at h = √K", exact(crit == [sp.sqrt(K)], "symbolic")),
            ("there R = K/h = h, the segment is a hemisphere", same(K / sp.sqrt(K), sp.sqrt(K))),
            ("and it is a maximum (d²V/dh² < 0)", Check(bool(sp.diff(Vh, h, 2).subs(h, sp.sqrt(K)).is_negative), "symbolic"))]


# ================= De conoidibus et sphaeroidibus =================

@prop("CS.4", "conoides", "4", 4,
      "The area bounded by an ellipse is to the circle on its major axis as the minor axis to the major.")
def cs4():
    ell = 4 * integral(b * sp.sqrt(1 - x**2 / a**2), (x, 0, a))
    return [("ellipse = π a b, and π a b : π a² = b : a", same(ell / (pi * a**2), b / a))]


@prop("CS.21", "conoides", "21", 21,
      "Any segment of a paraboloid of revolution cut off by a plane at right angles to the axis is half as large again "
      "as the cone with the same base and the same axis.")
def cs21():
    seg = integral(pi * x / c, (x, 0, h))       # paraboloid r² = x/c
    cone = pi * (h / c) * h / 3
    return [("segment = 3/2 · cone", same(seg, sp.Rational(3, 2) * cone))]


@prop("CS.25", "conoides", "24", 25,
      "Any segment of a hyperboloid of revolution cut off by a plane at right angles to the axis has to the cone with "
      "the same base and height the ratio of the axis of the segment together with three times the line adjoining the "
      "axis, to the axis together with twice the adjoining line.",
      "The \"adjoining line\" (ποτεοῦσα τῷ ἄξονι) is read as the semi-transverse axis, the distance from the vertex to "
      "the centre. In the encoding this is locus 24; the Greek numeral is κε΄ (25), because the encoding skips 23.")
def cs25():
    rr = lambda z: b**2 / a**2 * ((a + z)**2 - a**2)      # hyperbola (X/a)² − (r/b)² = 1, vertex at X = a
    seg = integral(pi * rr(x), (x, 0, h))
    cone = pi * rr(h) * h / 3
    return [("segment : cone = (h + 3a) : (h + 2a)", same(seg / cone, (h + 3 * a) / (h + 2 * a)))]


@prop("CS.27", "conoides", "26", 27,
      "If a spheroid is cut through the centre by a plane at right angles to the axis, the half spheroid is double the "
      "cone with the same base and the same axis.")
def cs27():
    half = integral(pi * b**2 * (1 - x**2 / a**2), (x, 0, a))
    return [("half spheroid = 2 · cone", same(half, 2 * pi * b**2 * a / 3))]


@prop("CS.29", "conoides", "28", 29,
      "If a spheroid is cut not through the centre by a plane at right angles to the axis, the smaller segment has to "
      "the cone with the same base and axis the ratio of half the axis of the spheroid together with the axis of the "
      "greater segment, to the axis of the greater segment. (Proposition 31, at locus 31, gives the same for the "
      "greater segment with the axes exchanged.)")
def cs29():
    def ratio(hh):
        seg = integral(pi * b**2 * (1 - x**2 / a**2), (x, a - hh, a))
        cone = pi * b**2 * (1 - (a - hh)**2 / a**2) * hh / 3
        return sp.simplify(seg / cone)
    return [("segment of height h : cone = (a + (2a − h)) : (2a − h)", same(ratio(h), (a + 2 * a - h) / (2 * a - h))),
            ("the formula holds for h < a and h > a alike (proposition 31)", same(ratio(2 * a - h), (a + h) / h))]


# ================= De lineis spiralibus =================

SPIRAL = "Spiral r = cθ; the n-th circle has radius 2πnc."


@prop("SL.18", "spirales", "18", 18,
      "If a straight line touches the spiral of the first turn at its end, and from the origin a line is drawn at right "
      "angles to the initial line, it meets the tangent, and the part between the tangent and the origin is equal to "
      "the circumference of the first circle.", SPIRAL)
def sl18():
    rr = c * t
    subtangent = (rr**2 / sp.diff(rr, t)).subs(t, 2 * pi)
    return [("polar subtangent at θ = 2π equals 2π · (2πc)", same(subtangent, 2 * pi * (2 * pi * c)))]


@prop("SL.24", "spirales", "24", 24,
      "The area bounded by the spiral of the first turn and the first line of the initial position is one third of the "
      "first circle.", SPIRAL)
def sl24():
    A = integral((c * t)**2 / 2, (t, 0, 2 * pi))
    return [("area = (1/3) π (2πc)²", same(A, pi * (2 * pi * c)**2 / 3))]


@prop("SL.25", "spirales", "25", 25,
      "The area bounded by the spiral of the second turn and the second line has to the second circle the ratio 7 : 12, "
      "which is the ratio of the rectangle of the radii of the second and first circles together with one third of the "
      "square on their difference, to the square on the radius of the second circle.", SPIRAL)
def sl25():
    A = integral((c * t)**2 / 2, (t, 2 * pi, 4 * pi))
    r1_, r2_ = 2 * pi * c, 4 * pi * c
    return [("area : second circle = 7 : 12", same(A / (pi * r2_**2), sp.Rational(7, 12))),
            ("= (r₂r₁ + (r₂ − r₁)²/3) : r₂²", same(sp.Rational(7, 12), (r2_ * r1_ + (r2_ - r1_)**2 / 3) / r2_**2))]


@prop("SL.26", "spirales", "26", 26,
      "The area bounded by an arc of the spiral less than one turn and the lines from its ends to the origin has to the "
      "sector with radius the greater of those lines and the same arc the ratio of the rectangle of the two lines "
      "together with one third of the square on their difference, to the square on the greater.", SPIRAL)
def sl26():
    t1, t2 = sp.symbols("t1 t2", positive=True)
    A = integral((c * t)**2 / 2, (t, t1, t2))
    sector = (c * t2)**2 * (t2 - t1) / 2
    q1, q2 = c * t1, c * t2
    return [("area : sector = (r₁r₂ + (r₂ − r₁)²/3) : r₂² for any arc", same(A / sector, (q1 * q2 + (q2 - q1)**2 / 3) / q2**2))]


@prop("SL.27", "spirales", "27", 27,
      "Of the areas bounded by the spirals and the lines in the revolutions, the third is double the second, the fourth "
      "triple, the fifth quadruple, and so on by the successive numbers; the first area is one sixth of the second.", SPIRAL)
def sl27():
    swept = lambda m: integral((c * t)**2 / 2, (t, 2 * pi * (m - 1), 2 * pi * m))   # area swept in the m-th turn
    ring = lambda m: sp.expand(swept(m) - swept(m - 1)) if m > 1 else swept(1)       # new area added by the m-th turn
    m = sp.symbols("m", integer=True, positive=True)     # m ≥ 2
    sw = lambda mm: (c**2 / 6) * ((2 * pi * mm)**3 - (2 * pi * (mm - 1))**3)
    ring_m = sp.expand(sw(m) - sw(m - 1))
    ring_2 = sp.expand(sw(2) - sw(1))
    return [("first area = 1/6 of the second", same(ring(1), ring(2) / 6)),
            ("third = 2 × second, fourth = 3 ×, fifth = 4 ×", Check(all(sp.simplify(ring(j) - (j - 1) * ring(2)) == 0 for j in (3, 4, 5)), "instance")),
            ("in general the m-th area = (m − 1) × the second", same(ring_m, (m - 1) * ring_2))]


# ================= Quadratura parabolae =================

@prop("QP.19", "quadratura-parabolae", "19", 19,
      "In a segment of a parabola, the line drawn (parallel to the diameter) from the middle of the base is four thirds "
      "of the line drawn from the middle of half the base.")
def qp19():
    p, q = sp.symbols("p q", real=True)
    depth = lambda X: (p + q) * X - p * q - X**2          # chord minus parabola y = x², chord from x=p to x=q
    mid, quarter = (p + q) / 2, p + (q - p) / 4
    return [("depth at the middle : depth at the quarter = 4 : 3", same(depth(mid) / depth(quarter), sp.Rational(4, 3)))]


@prop("QP.23", "quadratura-parabolae", "23", 23,
      "If magnitudes are set in succession in the ratio four to one, all of them together with one third of the least "
      "are four thirds of the greatest.")
def qp23():
    A = sp.symbols("A", positive=True)
    m = sp.symbols("m", integer=True, nonnegative=True)
    i = sp.symbols("i", integer=True, nonnegative=True)
    total = sp.summation(A / 4**i, (i, 0, m)) + A / (3 * 4**m)
    return [("Σ_{i=0..m} A/4^i + (1/3)·A/4^m = (4/3) A for every m", same(sp.simplify(total), sp.Rational(4, 3) * A))]


@prop("QP.24", "quadratura-parabolae", "24", 24,
      "Every segment bounded by a straight line and a section of a right-angled cone is four thirds of the triangle "
      "with the same base and equal height.")
def qp24():
    p, q = sp.symbols("p q", real=True)
    seg = integral((p + q) * x - p * q - x**2, (x, p, q))
    depth_mid = ((p + q) / 2) * (p + q) - p * q - ((p + q) / 2)**2   # vertical depth at the middle of the base
    tri = (q - p) * depth_mid / 2                                       # triangle on the chord with vertex on the curve
    return [("segment = 4/3 · triangle (any chord of y = x²)", same(seg, sp.Rational(4, 3) * tri))]


# ================= De planorum aequilibriis =================

@prop("PE.I.6", "aequilibria", "1.6", 6,
      "Commensurable magnitudes balance at distances reciprocally proportional to their weights. (I.7 extends this to "
      "incommensurable magnitudes.)")
def pe16():
    w1, w2, d = sp.symbols("w1 w2 d", positive=True)
    d1, d2 = d * w2 / (w1 + w2), d * w1 / (w1 + w2)       # distances reciprocal to the weights
    return [("w₁ d₁ = w₂ d₂, so the centre of weight is at the fulcrum", same(w1 * d1, w2 * d2))]


@prop("PE.I.14", "aequilibria", "1.14", 14,
      "The centre of weight of any triangle is the point where the lines drawn from the angles to the middles of the "
      "sides meet. (I.13: it lies on each such line.)")
def pe114():
    X0, Y0, X1, Y1, X2, Y2 = sp.symbols("X0 Y0 X1 Y1 X2 Y2", real=True)
    # centroid by integration over the triangle in barycentric parameters
    w, z = sp.symbols("w z", nonnegative=True)
    P = lambda A0, A1, A2: A0 + w * (A1 - A0) + z * (A2 - A0)
    area = integral(integral(1, (z, 0, 1 - w)), (w, 0, 1))
    gx = integral(integral(P(X0, X1, X2), (z, 0, 1 - w)), (w, 0, 1)) / area
    gy = integral(integral(P(Y0, Y1, Y2), (z, 0, 1 - w)), (w, 0, 1)) / area
    # the medians from A0 and A1 meet at the point dividing each in 2:1
    mx, my = X0 + sp.Rational(2, 3) * ((X1 + X2) / 2 - X0), Y0 + sp.Rational(2, 3) * ((Y1 + Y2) / 2 - Y0)
    return [("centre of weight = intersection of the medians (x)", same(gx, mx)),
            ("centre of weight = intersection of the medians (y)", same(gy, my))]


@prop("PE.II.8", "aequilibria", "2.8", 8,
      "The centre of weight of any parabolic segment divides its diameter so that the part towards the vertex is half "
      "as large again as the part towards the base.")
def pe28():
    # right segment of y² = x/c cut off by x = h; diameter along the axis from the vertex
    area = integral(2 * sp.sqrt(x / c), (x, 0, h))
    gx = integral(x * 2 * sp.sqrt(x / c), (x, 0, h)) / area
    return [("centre at 3/5 of the diameter from the vertex, so vertex part : base part = 3 : 2", same(gx / (h - gx), sp.Rational(3, 2)))]


@prop("PE.II.10", "aequilibria", "2.10", 10,
      "The centre of weight of a frustum cut from a parabolic segment lies on its diameter: divide the diameter into "
      "five equal parts; the centre lies in the middle fifth, dividing it so that the part nearer the smaller base is to "
      "the rest as the solid with base the square on the greater base and height twice the smaller base plus the "
      "greater, to the solid with base the square on the smaller base and height twice the greater plus the smaller.")
def pe210():
    # right frustum of x = y² (diameter along x) between half-chords u < v, i.e. x from u² to v²; bases 2u and 2v
    area = integral(2 * sp.sqrt(x), (x, u**2, v**2))
    gx = sp.simplify(integral(x * 2 * sp.sqrt(x), (x, u**2, v**2)) / area)
    L = v**2 - u**2
    lo, hi = u**2 + 2 * L / 5, u**2 + 3 * L / 5
    B1, B2 = 2 * u, 2 * v
    claim = (B2**2 * (2 * B1 + B2)) / (B1**2 * (2 * B2 + B1))
    return [("the centre divides the middle fifth in the stated ratio", same((gx - lo) / (hi - gx), claim))]


# ================= Ad Eratosthenem methodus =================

@prop("ME.pr", "methodus", "pr1", None,
      "Preface: (1) the hoof cut from a cylinder inscribed in a square prism by a plane through the centre of one base "
      "and a side of the opposite square is one sixth of the prism; (2) the solid common to two cylinders inscribed in "
      "a cube with axes at right angles is two thirds of the cube.",
      "The proof of (2) is lost with the end of the palimpsest; the check establishes the stated result only.")
def mepr():
    # (1) hoof over the half disc |x| ≤ R, 0 ≤ y ≤ √(R² − x²), height z = (2R / R)·y up to the side of the top square
    # prism of side 2R, cylinder axis vertical; the plane through the centre of the lower base and the upper side
    # y = R, z = 2R is z = 2y, so the hoof has height 2y over the half disc y ≥ 0
    hoof = integral(integral(2 * y, (y, 0, sp.sqrt(R**2 - x**2))), (x, -R, R))
    prism = (2 * R)**3
    # (2) two cylinders x² + z² ≤ R², y² + z² ≤ R²: square cross sections of side 2√(R² − z²)
    bicyl = integral(4 * (R**2 - z_**2), (z_, -R, R))
    return [("hoof = 1/6 of the prism", same(hoof, prism / 6)),
            ("common solid of the two cylinders = 2/3 of the cube", same(bicyl, sp.Rational(2, 3) * (2 * R)**3))]


z_ = sp.symbols("z_", real=True)


@prop("ME.6", "methodus", "6", 6,
      "The centre of weight of any hemisphere is on its axis, dividing it so that the part towards the surface is to "
      "the rest as five to three.")
def me6():
    vol = integral(pi * (R**2 - x**2), (x, 0, R))
    gx = integral(x * pi * (R**2 - x**2), (x, 0, R)) / vol
    return [("centre at 3R/8 from the base: surface part : base part = 5 : 3", same((R - gx) / gx, sp.Rational(5, 3)))]


@prop("ME.9", "methodus", "9", 9,
      "The centre of weight of any segment of a sphere is on its axis, dividing it so that the part towards the vertex "
      "is to the rest as the axis of the segment together with four times the axis of the opposite segment, to the axis "
      "of the segment together with twice the axis of the opposite segment.")
def me9():
    vol = integral(pi * (R**2 - x**2), (x, R - h, R))
    gx = integral(x * pi * (R**2 - x**2), (x, R - h, R)) / vol
    hopp = 2 * R - h
    return [("(vertex part) : (rest) = (h + 4h′) : (h + 2h′)", same((R - gx) / (gx - (R - h)), (h + 4 * hopp) / (h + 2 * hopp)))]


@prop("ME.11", "methodus", "11", 11,
      "A segment of a hyperboloid of revolution is to the cone with the same base and axis as the axis together with "
      "three times the adjoining line, to the axis together with twice the adjoining line; and its centre of weight "
      "divides the axis so that the part towards the vertex is to the rest as three times the axis together with eight "
      "times the adjoining line, to the axis together with four times the adjoining line.",
      "The volume repeats De conoidibus 25; the centre of weight is stated only here.")
def me11():
    rr = lambda z: b**2 / a**2 * ((a + z)**2 - a**2)
    vol = integral(pi * rr(x), (x, 0, h))
    gx = integral(x * pi * rr(x), (x, 0, h)) / vol
    return [("segment : cone = (h + 3a) : (h + 2a)", same(vol / (pi * rr(h) * h / 3), (h + 3 * a) / (h + 2 * a))),
            ("vertex part : rest = (3h + 8a) : (h + 4a)", same(gx / (h - gx), (3 * h + 8 * a) / (h + 4 * a)))]


# ================= Liber assumptorum =================

LA = "The Book of Lemmas survives only in Arabic; the Greek is Mugler's edition of the text."


@prop("LA.4", "liber-assumptorum", "4", 4,
      "If on the diameter of a semicircle a point is taken, semicircles are drawn inside on the two segments, and a "
      "perpendicular is raised at the point to the circumference, the figure bounded by the three arcs (the arbelos) "
      "is equal to the circle whose diameter is the perpendicular.", LA)
def la4():
    arb = pi / 8 * ((u + v)**2 - u**2 - v**2)
    perp2 = u * v                 # perpendicular² = product of the two segments (Elements VI.13)
    return [("arbelos = π/4 · (perpendicular)²", same(arb, pi / 4 * perp2))]


@prop("LA.6", "liber-assumptorum", "6", 6,
      "If in the arbelos a circle is inscribed touching the three semicircles, to find the ratio of the diameter of the "
      "given semicircle to the diameter of the inscribed circle. The worked case has AD one and a half times DC, and "
      "finds the ratio 19 : 6.", LA)
def la6():
    # arbelos with outer diameter 1, inner diameters p and 1 − p; inscribed circle (Pappus) diameter p(1−p)/(1 − p + p²)
    p = sp.symbols("p", positive=True)
    X0, Y0, rho = sp.symbols("X0 Y0 rho", real=True)
    eqs = [sp.Eq(sp.sqrt(X0**2 + Y0**2), sp.Rational(1, 2) - rho),                         # inside the outer circle, centre (0,0)
           sp.Eq(sp.sqrt((X0 + sp.Rational(1, 2) - sp.Rational(3, 10))**2 + Y0**2), sp.Rational(3, 10) + rho),  # left circle radius 3/10
           sp.Eq(sp.sqrt((X0 - sp.Rational(1, 2) + sp.Rational(1, 5))**2 + Y0**2), sp.Rational(1, 5) + rho)]   # right circle radius 1/5
    sol = [s_ for s_ in sp.solve([e.lhs**2 - e.rhs**2 for e in eqs], [X0, Y0, rho], dict=True) if s_[rho] > 0 and s_[Y0] > 0]
    return [("with AD : DC = 3 : 2 the inscribed circle has diameter 6/19 of AC", exact(len(sol) == 1 and sp.nsimplify(2 * sol[0][rho]) == sp.Rational(6, 19)))]


@prop("LA.8", "liber-assumptorum", "8", 8,
      "If a chord AB of a circle is produced to C so that BC equals the radius, and from C a line is drawn through the "
      "centre to meet the circle at E, the arc AE is three times the arc BF (F the nearer intersection).",
      "The lemma behind the neusis trisection of an angle. " + LA)
def la8():
    f = sp.symbols("f", positive=True)
    # unit circle, centre D at the origin, line CE the x axis, E = (1, 0), F = (−1, 0); B at angle f from DF
    B_ = sp.Matrix([-sp.cos(f), sp.sin(f)])
    C_ = sp.Matrix([-2 * sp.cos(f), 0])                       # on the x axis with BC = 1 = radius
    lam = 4 * sp.cos(f)**2 - 1                                # second root of |C + λ(B − C)| = 1 (the first is λ = 1)
    A_ = C_ + lam * (B_ - C_)
    return [("A lies on the circle", same(sp.simplify(A_.dot(A_)), 1)),
            ("BC = radius", same(sp.simplify((B_ - C_).dot(B_ - C_)), 1)),
            ("A is at angle 3f from E while B is at angle f from F: arc AE = 3 arc BF",
             Check(sp.simplify(sp.expand_trig(A_[0] - sp.cos(3 * f))) == 0 and sp.simplify(sp.expand_trig(A_[1] - sp.sin(3 * f))) == 0, "symbolic"))]


@prop("LA.11", "liber-assumptorum", "11", 11,
      "If two chords of a circle cut at right angles, not through the centre, the squares on the four segments together "
      "equal the square on the diameter.", LA)
def la11():
    p, q = sp.symbols("p q", real=True)                    # the chords are x = p and y = q, crossing at (p, q)
    yb = sp.sqrt(R**2 - p**2)
    xb = sp.sqrt(R**2 - q**2)
    segs = (yb - q)**2 + (yb + q)**2 + (xb - p)**2 + (xb + p)**2
    return [("sum of the four squares = (2R)²", same(segs, 4 * R**2))]


@prop("LA.14", "liber-assumptorum", "14", 14,
      "If on the diameter of a semicircle two equal segments are taken from the ends, semicircles drawn inside on them "
      "and outside on the remaining middle segment, the circle whose diameter is the radius of the semicircle together "
      "with the radius of the outer one is equal to the figure bounded by the arcs, which is called the salinon.", LA)
def la14():
    rho = R - a                                   # AC = DB = a, outer semicircle on CD has radius R − a
    salinon = pi / 2 * (R**2 - 2 * (a / 2)**2 + rho**2)
    return [("salinon = π/4 · (R + ρ)²", same(salinon, pi / 4 * (R + rho)**2))]


@prop("LA.15", "liber-assumptorum", "15", 15,
      "Let AB be a semicircle and AC the side of the inscribed regular pentagon; bisect the arc AC at D, join CD and "
      "produce it to E, draw DB cutting AC at F, and from F the perpendicular FH to AB. Then EH is equal to the radius.",
      "E is read as the intersection of CD produced with AB produced. " + LA)
def la15():
    O = sp.Matrix([0, 0])
    A_, B_ = sp.Matrix([-1, 0]), sp.Matrix([1, 0])
    pt = lambda ang: sp.Matrix([sp.cos(ang), sp.sin(ang)])
    C_ = pt(pi - 2 * pi / 5)            # arc AC = 72°, the side of the pentagon, measured from A
    D_ = pt(pi - pi / 5)                # midpoint of arc AC
    def meet(P1, P2, Q1, Q2):
        l1, l2 = sp.symbols("l1 l2", real=True)
        s_ = sp.solve(list(P1 + l1 * (P2 - P1) - Q1 - l2 * (Q2 - Q1)), [l1, l2], dict=True)[0]
        return sp.simplify(P1 + s_[l1] * (P2 - P1))
    E_ = meet(C_, D_, A_, B_)
    F_ = meet(D_, B_, A_, C_)
    H_ = sp.Matrix([F_[0], 0])
    EH = sp.sqrt(sp.simplify((E_ - H_).dot(E_ - H_)))
    return [("EH = radius (unit circle)", same(sp.nsimplify(sp.simplify(EH)), 1, "instance"))]


# ================= Arenarius, Problema bovinum =================

@prop("AR.4", "arenarius", "4", None,
      "The number of grains of sand that would fill the sphere of the fixed stars as Aristarchus supposes it is less "
      "than a thousand myriads of the eighth numbers, which is the sixty-fourth term from unity in the proportion.",
      "Section numbers in this work are the encoding's chapters, not propositions. In modern notation the bound is 10⁶³.")
def ar4():
    myriad2 = 10**8
    eighth_numbers_unit = myriad2**7               # the unit of the eighth numbers
    bound = 1000 * 10**4 * eighth_numbers_unit
    return [("a thousand myriads of eighth numbers = 10⁶³", exact(bound == 10**63)),
            ("which is the 64th term of the progression 1, 10, 100, …", exact(bound == 10**(64 - 1)))]


@prop("PB.1", "problema-bovinum", "1", None,
      "The herd of the Sun in four colours. Bulls: white = (1/2 + 1/3) black + yellow; black = (1/4 + 1/5) dappled + "
      "yellow; dappled = (1/6 + 1/7) white + yellow. Cows: white = (1/3 + 1/4) of the whole black herd; black = (1/4 + "
      "1/5) of the dappled herd; dappled = (1/5 + 1/6) of the yellow herd; yellow = (1/6 + 1/7) of the white herd. "
      "Further: white and black bulls together make a square, yellow and dappled together a triangle.",
      "\"Square\" renders ἰσόμετροι εἰς βάθος εἰς εὖρός τε and \"triangle\" σχῆμα τὸ τρικράσπεδον; both are readings. "
      "The checks solve the first part exactly and show that the second reduces to the Pell equation "
      "x² − 4729494·(2·4657)²·y² = 1 (Amthor 1880), whose solution is not computed here.")
def pb1():
    W, B, Y, D, w, b_, y_, d = sp.symbols("W B Y D w b y d", positive=True)
    Q = sp.Rational
    eqs = [W - (Q(1, 2) + Q(1, 3)) * B - Y, B - (Q(1, 4) + Q(1, 5)) * D - Y, D - (Q(1, 6) + Q(1, 7)) * W - Y,
           w - (Q(1, 3) + Q(1, 4)) * (B + b_), b_ - (Q(1, 4) + Q(1, 5)) * (D + d),
           d - (Q(1, 5) + Q(1, 6)) * (Y + y_), y_ - (Q(1, 6) + Q(1, 7)) * (W + w)]
    sol = sp.solve(eqs, [W, B, D, w, b_, d, y_], dict=True)[0]
    vals = {s_: sp.together(e / Y) for s_, e in sol.items()}
    vals[Y] = sp.Integer(1)
    den = sp.ilcm(*[sp.fraction(v_)[1] for v_ in vals.values()])
    smallest = {str(s_): int(v_ * den) for s_, v_ in vals.items()}
    known = dict(W=10366482, B=7460514, Y=4149387, D=7358060, w=7206360, b=4893246, y=5439213, d=3515820)
    sq, tri = smallest["W"] + smallest["B"], smallest["Y"] + smallest["D"]
    # W + B = k·17826996 must be a square: k = 4456749·m² (4456749 = 3·11·29·4657); Y + D triangular: 8(Y + D) + 1 = x²
    kfac = 3 * 11 * 29 * 4657
    D_pell = 8 * tri * kfac
    return [("smallest solution of the first part: 50389082 bulls and cows", exact(smallest == known and sum(known.values()) == 50389082)),
            ("W + B = 17826996 = 2²·3·11·29·4657", exact(sq == 17826996 and sp.factorint(sq) == {2: 2, 3: 1, 11: 1, 29: 1, 4657: 1})),
            ("square condition forces k = 4456749·m²", exact(sp.sqrt(sq * kfac).is_integer)),
            ("triangular condition becomes x² − 410286423278424·m² = 1 = x² − 4729494·9314²·m²", exact(D_pell == 410286423278424 == 4729494 * (2 * 4657)**2))]


# ---------- run ----------

def run(pid):
    p = PROPS[pid]
    checks = []
    nc = numeral_check(p)
    if nc:
        checks.append(nc)
    return checks + p["fn"]()


def main(argv):
    if len(argv) > 1:
        p = PROPS[argv[1]]
        print(f"{p['id']}  {p['work']} {p['locus']}\n{p['statement']}\n")
        if G:
            print(G.text(p["work"], p["locus"])[:1500], "\n")
        if p["note"]:
            print("Note:", p["note"], "\n")
        for label, ch in run(argv[1]):
            print(f"{'OK ' if ch.ok else 'NG '} {ch.method:9s} {label}")
        return
    bad = total = 0
    for pid in PROPS:
        for label, ch in run(pid):
            total += 1
            bad += not ch.ok
            print(f"{'OK ' if ch.ok else 'NG '} {ch.method:9s} {pid:10s} {label}", flush=True)
    print(f"\n{len(PROPS)} propositions, {total} checks, {'all passed' if not bad else f'{bad} FAILED'}")
    return bad


if __name__ == "__main__":
    sys.exit(1 if main(sys.argv) else 0)
