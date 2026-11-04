"""Corpus Geometriae: classical geometric constructions and propositions as verifiable code parts.

Each part is a function registered with @part that returns (objects, checks).
  objects : the constructed objects (sympy points, circles, expressions)
  checks  : a list of (label, Check). A Check records the result and the method used.

Verification methods:
  symbolic  holds identically in general symbols (a, b, r, t, ...)
  instance  holds exactly (as algebraic numbers) for a concrete construction
  numeric   confirmed only to 50 significant digits; this is not a proof

Run:  python geometria.py   verifies every part (requires sympy).
"""
from dataclasses import dataclass
from itertools import combinations, product

import sympy as sp
from sympy.geometry import Circle, Line, Point, Segment

PARTS = {}


def part(**meta):
    def deco(fn):
        PARTS[meta["id"]] = {**meta, "fn": fn}
        return fn
    return deco


@dataclass
class Check:
    ok: bool
    method: str


def same(a, b, method="symbolic"):
    """Decide a == b exactly. Falls back to numeric only when exact simplification is inconclusive, and records that."""
    d = sp.simplify(sp.expand(sp.sympify(a) - sp.sympify(b)))
    if d == 0:
        return Check(True, method)
    d = sp.nsimplify(sp.radsimp(sp.sqrtdenest(d)))
    if d == 0:
        return Check(True, method)
    return Check(abs(sp.N(d, 60)) < sp.Float("1e-50"), "numeric")


def close(a, b):
    """Confirm equality to 50 digits (for deeply nested radicals where exact simplification is impractical)."""
    return Check(abs(sp.N(sp.sympify(a) - sp.sympify(b), 60)) < sp.Float("1e-50"), "numeric")


def greater(lhs, rhs):
    """Confirm lhs > rhs to 50 digits."""
    return Check(bool(sp.N(sp.sympify(lhs) - sp.sympify(rhs), 50) > 0), "numeric")


def shoelace(*pts):
    """Signed area of a polygon. Uses no distance formula (and hence no Pythagorean theorem)."""
    s = 0
    for (x1, y1), (x2, y2) in zip(pts, pts[1:] + pts[:1]):
        s += x1 * y2 - x2 * y1
    return sp.expand(s / 2)


a, b, c, d, k, r, t, h, x, y, z = sp.symbols("a b c d k r t h x y z", positive=True)
phi = (1 + sp.sqrt(5)) / 2


# === Euclid, Elements ===

@part(id="euclid-I-1", tradition="euclid")
def euclid_I_1():
    """On a given finite straight line, construct an equilateral triangle."""
    A, B = Point(0, 0), Point(2, 0)
    c1 = Circle(A, A.distance(B))          # circle with centre A and radius AB
    c2 = Circle(B, B.distance(A))          # circle with centre B and radius BA
    C = max(c1.intersection(c2), key=lambda p: p.y)
    return dict(A=A, B=B, C=C, c1=c1, c2=c2), [
        ("CA = AB", same(C.distance(A), A.distance(B), "instance")),
        ("CB = AB", same(C.distance(B), A.distance(B), "instance")),
    ]


@part(id="euclid-I-10", tradition="euclid")
def euclid_I_10():
    """Bisect a given finite straight line (modern two-circle construction)."""
    A, B = Point(0, 0), Point(2 * a, 0)
    c1, c2 = Circle(A, 2 * a), Circle(B, 2 * a)
    P, Q = c1.intersection(c2)
    M = Line(P, Q).intersection(Line(A, B))[0]
    return dict(A=A, B=B, P=P, Q=Q, M=M), [
        ("AM = MB", same(A.distance(M), M.distance(B))),
        ("PQ ⊥ AB", same(Line(P, Q).direction.dot(Line(A, B).direction), 0)),
    ]


@part(id="euclid-I-47", tradition="euclid")
def euclid_I_47():
    """In a right triangle the square on the hypotenuse equals the squares on the other two sides.
    The coordinate distance formula presupposes this very theorem, so areas are computed with the
    shoelace formula, following the skeleton of Euclid's proof (the altitude, extended, divides the
    square on the hypotenuse into two rectangles)."""
    A, B, C = (0, 0), (c, 0), (0, b)                 # right angle at A
    D, E = (c + b, c), (b, b + c)                    # square B C E D on BC (outward)
    s = (c * c) / (b * b + c * c)                    # foot of the perpendicular from A: K = B + s·(C - B)
    K = (c - s * c, s * b)                           # (projection by dot product; no distances used)
    L = (K[0] + b, K[1] + c)                         # AK extended meets DE at L
    sq_AB = shoelace((0, 0), (0, -c), (c, -c), (c, 0))
    sq_AC = shoelace((0, 0), (0, b), (-b, b), (-b, 0))
    rect_B = shoelace(B, D, L, K)
    rect_C = shoelace(K, L, E, C)
    sq_BC = shoelace(B, D, E, C)
    return dict(A=A, B=B, C=C, D=D, E=E, K=K, L=L), [
        ("rectangle BDLK = square on AB", same(abs(rect_B), abs(sq_AB))),
        ("rectangle KLEC = square on AC", same(abs(rect_C), abs(sq_AC))),
        ("square on BC = sum of the two squares", same(abs(sq_BC), abs(sq_AB) + abs(sq_AC))),
    ]


@part(id="euclid-II-11", tradition="euclid")
def euclid_II_11():
    """Cut a given line AB at G so that the rectangle contained by the whole and one segment equals
    the square on the other segment (extreme and mean ratio, later the "golden ratio")."""
    AB = a
    # square ABDC on AB, E the midpoint of AC, F on CA produced with EF = EB, AG = AF
    EB = sp.sqrt(AB**2 + (AB / 2) ** 2)
    AG = EB - AB / 2
    GB = AB - AG
    return dict(AB=AB, AG=AG, GB=GB), [
        ("AB·GB = AG²", same(AB * GB, AG**2)),
        ("AB : AG = AG : GB = φ", same(AB / AG, phi)),
    ]


@part(id="euclid-III-31", tradition="euclid")
def euclid_III_31():
    """The angle in a semicircle is right."""
    A, B = Point(-1, 0), Point(1, 0)
    P = Point(sp.cos(t), sp.sin(t))                 # arbitrary point on the circle
    return dict(A=A, B=B, P=P), [
        ("PA · PB = 0 (∠APB = 90°)", same((A - P).dot(B - P), 0)),
    ]


@part(id="euclid-IV-11", tradition="ptolemy")
def ptolemy_pentagon():
    """Construct the side of a regular pentagon inscribed in the unit circle (Ptolemy's method)."""
    O, A, P = Point(0, 0), Point(0, 1), Point(1, 0)
    E = Segment(O, P).midpoint                      # midpoint of OP
    F = Point(E.x - E.distance(A), 0)               # circle centre E, radius EA, meets the negative x-axis
    s10, s5 = O.distance(F), A.distance(F)          # side of decagon, side of pentagon
    V = [Point(sp.cos(sp.pi / 2 + 2 * sp.pi * i / 5), sp.sin(sp.pi / 2 + 2 * sp.pi * i / 5)) for i in range(5)]
    side, diag = V[0].distance(V[1]), V[0].distance(V[2])
    return dict(O=O, A=A, E=E, F=F, s5=s5, s10=s10), [
        ("OF = side of regular decagon = 2 sin 18°", same(s10, 2 * sp.sin(sp.pi / 10), "instance")),
        ("AF = side of regular pentagon = 2 sin 36°", same(s5, 2 * sp.sin(sp.pi / 5), "instance")),
        ("diagonal : side = φ (Elements XIII.8)", same(diag / side, phi, "instance")),
    ]


@part(id="euclid-VI-13", tradition="euclid")
def euclid_VI_13():
    """Find a mean proportional between two given lines a and b."""
    M, R = (a + b) / 2, (a + b) / 2                 # semicircle on AB = a + b as diameter
    D = (a, sp.sqrt(a * b))                         # perpendicular at C = (a, 0) meets the semicircle
    return dict(D=D), [
        ("D lies on the semicircle", same((D[0] - M) ** 2 + D[1] ** 2, R**2)),
        ("CD² = AC·CB", same(D[1] ** 2, a * b)),
    ]


def _solid(name):
    if name == "tetra":
        return [(1, 1, 1), (1, -1, -1), (-1, 1, -1), (-1, -1, 1)]
    if name == "cube":
        return list(product((1, -1), repeat=3))
    if name == "octa":
        return [p for i in range(3) for s in (1, -1) for p in [tuple(s if j == i else 0 for j in range(3))]]
    if name == "icosa":
        return _cyclic([(0, s1, s2 * phi) for s1 in (1, -1) for s2 in (1, -1)])
    if name == "dodeca":
        return list(product((1, -1), repeat=3)) + _cyclic(
            [(0, s1 / phi, s2 * phi) for s1 in (1, -1) for s2 in (1, -1)])


def _cyclic(pts):
    return [p[i:] + p[:i] for p in pts for i in range(3)]


def _dist2(p, q):
    return sp.nsimplify(sp.expand(sum((u - v) ** 2 for u, v in zip(p, q))))


@part(id="euclid-XIII-18", tradition="euclid")
def euclid_XIII_18():
    """Compare the edges of the five regular solids inscribed in the same sphere."""
    ratio = {}
    for name in ("tetra", "octa", "cube", "icosa", "dodeca"):
        V = _solid(name)
        e2 = min(_dist2(p, q) for p, q in combinations(V, 2))
        R2 = _dist2(V[0], (0, 0, 0))
        ratio[name] = sp.sqrt(sp.nsimplify(e2 / R2))  # edge / circumradius
    order = ["tetra", "octa", "cube", "icosa", "dodeca"]
    return dict(ratio=ratio), [
        ("tetrahedron: edge = √(8/3)·R", same(ratio["tetra"], sp.sqrt(sp.Rational(8, 3)), "instance")),
        ("octahedron: edge = √2·R", same(ratio["octa"], sp.sqrt(2), "instance")),
        ("cube: edge = 2/√3·R", same(ratio["cube"], 2 / sp.sqrt(3), "instance")),
        ("icosahedron: edge = 4/√(10+2√5)·R", same(ratio["icosa"], 4 / sp.sqrt(10 + 2 * sp.sqrt(5)), "instance")),
        ("dodecahedron: edge = (√15−√3)/3·R", same(ratio["dodeca"], (sp.sqrt(15) - sp.sqrt(3)) / 3, "instance")),
        ("order: tetrahedron > octahedron > cube > icosahedron > dodecahedron",
         Check(all(sp.N(ratio[p] - ratio[q], 50) > 0 for p, q in zip(order, order[1:])), "numeric")),
    ]


# === Archimedes ===

@part(id="archimedes-circle", tradition="archimedes")
def archimedes_pi():
    """Double the sides from the hexagon to the 96-gon and bound the ratio of circumference to diameter."""
    p, P = sp.Integer(3), 2 * sp.sqrt(3)            # half-perimeters of inscribed and circumscribed hexagons (radius 1)
    n = 6
    while n < 96:
        P = 2 * p * P / (p + P)                     # circumscribed 2n-gon: harmonic mean
        p = sp.sqrt(p * P)                          # inscribed 2n-gon: geometric mean
        n *= 2
    return dict(n=n, inner=p, outer=P), [
        ("half-perimeter of inscribed 96-gon = 96·sin(π/96)", close(p, 96 * sp.sin(sp.pi / 96))),
        ("3 10/71 < inscribed 96-gon", greater(p, sp.Rational(223, 71))),
        ("circumscribed 96-gon < 3 1/7", greater(sp.Rational(22, 7), P)),
        ("hence 223/71 < π < 22/7", Check(greater(p, sp.Rational(223, 71)).ok and greater(sp.Rational(22, 7), P).ok
                                          and greater(sp.pi, p).ok and greater(P, sp.pi).ok, "numeric")),
    ]


@part(id="archimedes-parabola", tradition="archimedes")
def archimedes_parabola():
    """A parabolic segment is 4/3 of the triangle with the same base and height."""
    f = lambda u: u**2
    p, q = a, a + b                                 # x-coordinates of the chord's endpoints (b > 0)
    m = (p + q) / 2                                 # point of tangency parallel to the chord (vertex of the segment)
    chord = f(p) + (f(q) - f(p)) / (q - p) * (x - p)
    segment = sp.integrate(chord - f(x), (x, p, q))
    triangle = sp.Abs(shoelace((p, f(p)), (m, f(m)), (q, f(q))))
    n = sp.symbols("n", integer=True, nonnegative=True)
    return dict(segment=segment, triangle=triangle), [
        ("segment = (4/3)·triangle", same(segment, sp.Rational(4, 3) * triangle)),
        ("exhaustion: 1 + 1/4 + 1/16 + ... = 4/3", same(sp.summation(sp.Rational(1, 4) ** n, (n, 0, sp.oo)), sp.Rational(4, 3))),
    ]


@part(id="archimedes-sphere", tradition="archimedes")
def archimedes_sphere():
    """A sphere is 2/3 of its circumscribed cylinder, and its surface equals the cylinder's lateral surface."""
    V_sphere = sp.integrate(sp.pi * (r**2 - z**2), (z, -r, r))   # stack circular cross-sections
    V_cyl = sp.pi * r**2 * 2 * r
    V_cone = sp.pi * r**2 * r / 3
    S_sphere = sp.diff(V_sphere, r)
    S_cyl_side = 2 * sp.pi * r * 2 * r
    return dict(V_sphere=V_sphere), [
        ("sphere : cylinder = 2 : 3", same(V_sphere / V_cyl, sp.Rational(2, 3))),
        ("sphere = 4 × cone with base a great circle and height the radius", same(V_sphere, 4 * V_cone)),
        ("surface of sphere = lateral surface of cylinder", same(S_sphere, S_cyl_side)),
    ]


@part(id="archimedes-arbelos", tradition="archimedes")
def arbelos_twins():
    """The twin circles of the arbelos are equal, with radius ab/(a+b)."""
    rr, yy = sp.symbols("rho y0", positive=True)
    # A=(0,0), C=(2a,0), B=(2a+2b,0). Left twin: centre (2a−ρ, y0), tangent to the line x = 2a
    eqs = [
        sp.Eq((2 * a - rr - a) ** 2 + yy**2, (a + rr) ** 2),          # externally tangent to small semicircle (radius a)
        sp.Eq((2 * a - rr - (a + b)) ** 2 + yy**2, (a + b - rr) ** 2),  # internally tangent to large semicircle (radius a+b)
    ]
    rho_L = sp.solve(eqs, [rr, yy], dict=True)[0][rr]
    eqs_R = [
        sp.Eq((2 * a + rr - (2 * a + b)) ** 2 + yy**2, (b + rr) ** 2),
        sp.Eq((2 * a + rr - (a + b)) ** 2 + yy**2, (a + b - rr) ** 2),
    ]
    rho_R = sp.solve(eqs_R, [rr, yy], dict=True)[0][rr]
    return dict(rho_L=rho_L, rho_R=rho_R), [
        ("radius of left circle = ab/(a+b)", same(rho_L, a * b / (a + b))),
        ("radius of right circle = radius of left circle", same(rho_R, rho_L)),
    ]


@part(id="archimedes-spiral", tradition="archimedes")
def archimedes_spiral():
    """The spiral r = aθ: the area of the first turn is 1/3 of the first circle, the tangent at the end of the
    first turn cuts off on the perpendicular a line equal to the circumference of that circle, and the
    spiral divides any angle in any given ratio."""
    th = sp.symbols("theta", positive=True)
    rho = a * th
    R = rho.subs(th, 2 * sp.pi)                     # radius of the "first circle"
    area_turn = sp.integrate(rho**2 / 2, (th, 0, 2 * sp.pi))
    # tangent at P = end of the first turn, meeting the line through O perpendicular to OP at T
    X, Y = rho * sp.cos(th), rho * sp.sin(th)
    P = (X.subs(th, 2 * sp.pi), Y.subs(th, 2 * sp.pi))
    v = (sp.diff(X, th).subs(th, 2 * sp.pi), sp.diff(Y, th).subs(th, 2 * sp.pi))
    s = -P[0] / v[0]                                # parameter where the tangent crosses x = 0
    OT = sp.Abs(P[1] + s * v[1])
    third = sp.solve(sp.Eq(rho, rho.subs(th, t) / 3), th)[0]
    return dict(R=R, area=area_turn, OT=OT), [
        ("area of first turn = 1/3 of the first circle (prop. 24)", same(area_turn, sp.pi * R**2 / 3)),
        ("OT = circumference of the first circle (prop. 18)", same(OT, 2 * sp.pi * R)),
        ("radius divided in ratio 1 : 3 gives angle divided in ratio 1 : 3", same(third, t / 3)),
    ]


# === Apollonius / Pappus ===

@part(id="apollonius-tangencies", tradition="apollonius")
def apollonius_tangencies():
    """Given three circles, find the circles tangent to all three (the Problem of Apollonius): in general eight."""
    given = [((0, 0), 1), ((6, 0), 2), ((2, 5), sp.Rational(3, 2))]
    X, Y, R = sp.symbols("X Y R", real=True)
    found = []
    for signs in product((1, -1), repeat=3):        # +1: tangent externally, -1: tangent internally
        eqs = [(X - cx) ** 2 + (Y - cy) ** 2 - (R + s * ri) ** 2 for ((cx, cy), ri), s in zip(given, signs)]
        # differences of the equations are linear in X, Y, R (the reduction used since Viète)
        for sol in sp.solve(eqs, [X, Y, R], dict=True):
            if sp.N(sol[R]) > 0 and all(abs(sp.N(sol[R] - f[R])) > 1e-9 or abs(sp.N(sol[X] - f[X])) > 1e-9 for f in found):
                found.append(sol)
    tangent = all(
        any(close((f[X] - cx) ** 2 + (f[Y] - cy) ** 2, (f[R] + s * ri) ** 2).ok for s in (1, -1))
        for f in found for (cx, cy), ri in given)
    return dict(given=given, solutions=found), [
        ("eight distinct real solutions", Check(len(found) == 8, "instance")),
        ("each solution is tangent to all three given circles", Check(tangent, "numeric")),
    ]


@part(id="apollonius-circle", tradition="apollonius")
def apollonius_circle():
    """The locus of points whose distances from two fixed points A, B are in a constant ratio k (≠1) is a circle."""
    A, B = (0, 0), (d, 0)
    locus = (x**2 + y**2) - k**2 * ((x - d) ** 2 + y**2)            # PA² − k²·PB² = 0
    P1 = k / (1 + k) * d                            # internal division of AB in ratio k
    P2 = k / (k - 1) * d                            # external division of AB in ratio k
    m, rho = (P1 + P2) / 2, (P2 - P1) / 2
    circle = (x - m) ** 2 + y**2 - rho**2           # circle on P1P2 as diameter
    return dict(P1=P1, P2=P2, center=sp.simplify(m), radius=sp.simplify(rho)), [
        ("locus equation = (1−k²)·(circle on P1P2)", same(locus, (1 - k**2) * circle)),
        ("centre = −k²d/(1−k²)", same(m, -k**2 * d / (1 - k**2))),
    ]


@part(id="apollonius-ellipse", tradition="apollonius")
def apollonius_ellipse():
    """The sum of the distances from a point of an ellipse to the two foci equals the major axis."""
    e = sp.sqrt(a**2 - b**2)                        # focal distance (a > b)
    Px, Py = a * sp.cos(t), b * sp.sin(t)
    d1sq, d2sq = (Px - e) ** 2 + Py**2, (Px + e) ** 2 + Py**2
    # without taking roots, confirm PF1 = a − e cos t and PF2 = a + e cos t by squaring (both sides positive)
    return dict(focus=e), [
        ("PF1² = (a − e·cos t)²", same(d1sq, (a - e * sp.cos(t)) ** 2)),
        ("PF2² = (a + e·cos t)²", same(d2sq, (a + e * sp.cos(t)) ** 2)),
        ("PF1 + PF2 = 2a", same((a - e * sp.cos(t)) + (a + e * sp.cos(t)), 2 * a)),
    ]


# === Hippocrates of Chios ===

@part(id="hippocrates-lune", tradition="hippocrates")
def hippocrates_lune():
    """The lune on a side of an isosceles right triangle equals a triangle in area."""
    # isosceles right triangle ABC inscribed in a circle of radius r (AB a diameter, right angle at C)
    AC = sp.sqrt(2) * r
    semicircle_AC = sp.pi * (AC / 2) ** 2 / 2       # outward semicircle on AC as diameter
    segment_AC = sp.pi * r**2 / 4 - r**2 / 2        # segment of the large circle cut off by chord AC
    lune = semicircle_AC - segment_AC
    tri_AOC = r**2 / 2
    return dict(lune=lune), [
        ("lune = triangle AOC", same(lune, tri_AOC)),
        ("two lunes = triangle ABC", same(2 * lune, r**2)),
    ]


# === Menaechmus (via Eutocius) ===

@part(id="menaechmus-cube", tradition="menaechmus")
def menaechmus_cube():
    """From the intersection of two parabolas, obtain the duplication of the cube (∛2)."""
    X = a * sp.cbrt(2)
    Y = X**2 / a                                    # on the parabola x² = a·y
    return dict(X=X, Y=Y), [
        ("(X, Y) lies on y² = 2a·x", same(Y**2, 2 * a * X)),
        ("X³ = 2a³ (edge of the doubled cube)", same(X**3, 2 * a**3)),
        ("a : X = X : Y = Y : 2a (two mean proportionals)",
         Check(same(a / X, X / Y).ok and same(X / Y, Y / (2 * a)).ok, "symbolic")),
    ]


# === Alberti ===

@part(id="alberti-perspective", tradition="alberti")
def alberti_perspective():
    """Costruzione legittima: project the floor grid onto the picture plane, eye height h, viewing distance d."""
    def project(X, Z):                              # floor point (X, depth Z) -> picture (x', y')
        return (X * d / (d + Z), h * Z / (d + Z))
    vp = (0, h)                                     # centric (vanishing) point
    Z = sp.Symbol("Z", positive=True)
    ortho = [sp.limit(c_, Z, sp.oo) for c_ in project(c, Z)]
    diag = project(Z + c, Z)                        # floor diagonal X = Z + c
    dist_pt = (d, h)                                # distance point
    collinear = sp.Matrix([[*project(c, 0), 1], [*diag, 1], [*dist_pt, 1]]).det()
    rows = [project(0, n)[1] for n in range(4)]
    return dict(rows=rows), [
        ("orthogonal X = c converges to the centric point (0, h)", same(ortho[0] - vp[0] + ortho[1] - vp[1], 0)),
        ("every diagonal's image passes through the distance point (d, h)", same(collinear, 0)),
        ("height of transversal y_n = h·n/(d + n)", same(rows[2], 2 * h / (d + 2))),
    ]


# === Pacioli, De divina proportione ===

@part(id="pacioli-proportion", tradition="pacioli")
def pacioli_proportion():
    """Algebraic properties of the extreme and mean ratio (divina proportione)."""
    lesser, greater_, whole = 1 / phi, 1, phi       # the whole φ divided in extreme and mean ratio
    half = whole / 2
    return dict(phi=phi), [
        ("whole : greater = greater : lesser", same(whole / greater_, greater_ / lesser)),
        ("φ² = φ + 1", same(phi**2, phi + 1)),
        ("1/φ = φ − 1", same(1 / phi, phi - 1)),
        ("(greater + half the whole)² = 5·(half the whole)² (XIII.1)", same((greater_ + half) ** 2, 5 * half**2)),
    ]


@part(id="pacioli-icosahedron", tradition="pacioli")
def pacioli_icosahedron():
    """The 12 vertices of three mutually perpendicular golden rectangles form a regular icosahedron."""
    V = _solid("icosa")
    edges = [(p, q) for p, q in combinations(V, 2) if _dist2(p, q) == 4]
    degree = {v: sum(v in e for e in edges) for v in V}
    faces = [f for f in combinations(V, 3) if all(_dist2(p, q) == 4 for p, q in combinations(f, 2))]
    return dict(vertices=V, edges=edges), [
        ("12 vertices", Check(len(V) == 12, "instance")),
        ("30 edges (all of length 2)", Check(len(edges) == 30, "instance")),
        ("5 edges at every vertex", Check(set(degree.values()) == {5}, "instance")),
        ("20 faces (equilateral triangles)", Check(len(faces) == 20, "instance")),
        ("Euler V − E + F = 2", Check(len(V) - len(edges) + len(faces) == 2, "instance")),
    ]


# === Leonardo ===

@part(id="leonardo-lunulae", tradition="leonardo")
def leonardo_lunulae():
    """Erect outward semicircles on the sides of a square inscribed in a circle: the four lunes together equal the square."""
    side = sp.sqrt(2) * r
    square = side**2
    four_semicircles = 4 * sp.pi * (side / 2) ** 2 / 2
    circle_minus_square = sp.pi * r**2 - square     # the four circular segments together
    lunes = four_semicircles - circle_minus_square
    return dict(lunes=lunes), [
        ("four lunes = square", same(lunes, square)),
        ("four semicircles = circle", same(four_semicircles, sp.pi * r**2)),
    ]


# === run ===

def run(pid):
    objs, checks = PARTS[pid]["fn"]()
    return objs, checks


if __name__ == "__main__":
    bad = 0
    for pid in PARTS:
        _, checks = run(pid)
        for label, ch in checks:
            bad += not ch.ok
            print(f"{'OK ' if ch.ok else 'NG '} {ch.method:9s} {pid:22s} {label}", flush=True)
    print(f"\n{len(PARTS)} parts, {'all checks passed' if not bad else f'{bad} FAILED'}")
