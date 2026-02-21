"""
Decrypt for AlpacaHack daily: copper-copper-copper (2026-02-21).

Given:
- N, e, c (RSA)
- pbar = floor(p / 2^k) * 2^k  (upper bits of p; lower k bits are unknown)
- kbits = k

Recover p using a Coppersmith-style lattice (LLL) approach, then decrypt m.

No third-party libraries required.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import math
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple


@dataclass(frozen=True)
class PublicData:
    N: int
    e: int
    c: int
    pbar: int
    kbits: int


# -------------------------
# Parsing
# -------------------------


def parse_output_txt(path: Path) -> PublicData:
    values: Dict[str, int] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or "=" not in line:
            continue
        k, v = line.split("=", 1)
        values[k.strip()] = int(v.strip())

    missing = [k for k in ("N", "e", "c", "pbar", "kbits") if k not in values]
    if missing:
        raise ValueError(f"Missing keys in output.txt: {missing}")

    return PublicData(
        N=values["N"],
        e=values["e"],
        c=values["c"],
        pbar=values["pbar"],
        kbits=values["kbits"],
    )


# -------------------------
# Small utilities
# -------------------------


def egcd(a: int, b: int) -> Tuple[int, int, int]:
    if b == 0:
        return a, 1, 0
    g, x1, y1 = egcd(b, a % b)
    return g, y1, x1 - (a // b) * y1


def modinv(a: int, m: int) -> int:
    g, x, _y = egcd(a % m, m)
    if g != 1:
        raise ValueError("inverse does not exist")
    return x % m


def crt_pair(a: int, m: int, b: int, n: int) -> Tuple[int, int]:
    """Combine x≡a (mod m), x≡b (mod n) for coprime m,n. Return (x mod mn, mn)."""
    g, s, _t = egcd(m, n)
    if g != 1:
        raise ValueError("moduli not coprime in crt_pair")
    x = (a + ((b - a) * s % n) * m) % (m * n)
    return x, m * n


def int_to_bytes(x: int) -> bytes:
    if x == 0:
        return b"\x00"
    length = (x.bit_length() + 7) // 8
    return x.to_bytes(length, "big")


def nearest_int(fr: Fraction) -> int:
    """Nearest integer rounding for Fractions."""
    n, d = fr.numerator, fr.denominator
    if n >= 0:
        return (n + d // 2) // d
    return -((-n + d // 2) // d)


# -------------------------
# LLL (pure Python)
# -------------------------


def _dot(u: Sequence[int], v: Sequence[int]) -> int:
    return sum(ui * vi for ui, vi in zip(u, v))


def _gram_schmidt(B: List[List[int]]) -> Tuple[List[List[Fraction]], List[List[Fraction]], List[Fraction]]:
    n = len(B)
    m = len(B[0])
    Bstar: List[List[Fraction]] = [[Fraction(0) for _ in range(m)] for _ in range(n)]
    mu: List[List[Fraction]] = [[Fraction(0) for _ in range(n)] for _ in range(n)]
    norm: List[Fraction] = [Fraction(0) for _ in range(n)]

    for i in range(n):
        Bstar[i] = [Fraction(x) for x in B[i]]
        for j in range(i):
            mu[i][j] = Fraction(_dot(B[i], Bstar[j]), norm[j])
            for k in range(m):
                Bstar[i][k] -= mu[i][j] * Bstar[j][k]
        norm[i] = _dot(Bstar[i], Bstar[i])

    return Bstar, mu, norm


def lll_reduce(basis: List[List[int]], delta: Fraction = Fraction(99, 100)) -> List[List[int]]:
    """Basic LLL reduction. Good enough for small dimensions in CTF tasks."""
    if not basis:
        return []

    B = [row[:] for row in basis]
    n = len(B)
    m = len(B[0])

    k = 1
    Bstar, mu, norm = _gram_schmidt(B)
    while k < n:
        # size reduction
        for j in range(k - 1, -1, -1):
            q = nearest_int(mu[k][j])
            if q:
                for t in range(m):
                    B[k][t] -= q * B[j][t]
        Bstar, mu, norm = _gram_schmidt(B)

        # Lovász condition
        if norm[k] >= (delta - mu[k][k - 1] ** 2) * norm[k - 1]:
            k += 1
        else:
            B[k], B[k - 1] = B[k - 1], B[k]
            Bstar, mu, norm = _gram_schmidt(B)
            k = max(k - 1, 1)

    return B


# -------------------------
# Polynomial helpers (univariate)
# -------------------------


def poly_trim(p: List[int]) -> List[int]:
    while len(p) > 1 and p[-1] == 0:
        p.pop()
    return p


def poly_mul(a: List[int], b: List[int]) -> List[int]:
    res = [0] * (len(a) + len(b) - 1)
    for i, ai in enumerate(a):
        for j, bj in enumerate(b):
            res[i + j] += ai * bj
    return poly_trim(res)


def poly_pow(a: List[int], e: int) -> List[int]:
    res = [1]
    base = a[:]
    while e:
        if e & 1:
            res = poly_mul(res, base)
        e >>= 1
        if e:
            base = poly_mul(base, base)
    return res


def poly_scale(p: List[int], s: int) -> List[int]:
    return [c * s for c in p]


def poly_shift(p: List[int], k: int) -> List[int]:
    return [0] * k + p


def poly_eval_mod(coeff: Sequence[int], x: int, mod: int) -> int:
    r = 0
    for c in reversed(coeff):
        r = (r * x + (c % mod)) % mod
    return r


# -------------------------
# Root finding (mod primes + CRT)
# -------------------------


def is_prime_small(n: int) -> bool:
    if n < 2:
        return False
    if n % 2 == 0:
        return n == 2
    d = 3
    while d * d <= n:
        if n % d == 0:
            return False
        d += 2
    return True


def small_primes_16bit(start: int = 65537, count: int = 40) -> List[int]:
    primes: List[int] = []
    x = start
    while len(primes) < count:
        if is_prime_small(x):
            primes.append(x)
        x += 2  # keep odd
    return primes


def find_roots_mod_prime_bruteforce(coeff: Sequence[int], p: int) -> List[int]:
    # degree is small in our usage; brute force over 16-bit primes is fine.
    roots = []
    for r in range(p):
        if poly_eval_mod(coeff, r, p) == 0:
            roots.append(r)
    return roots


def find_small_integer_roots_via_crt(coeff: List[int], bound: int) -> List[int]:
    primes = small_primes_16bit(count=30)

    # candidates as congruences x ≡ a (mod M)
    candidates: List[Tuple[int, int]] = [(0, 1)]
    for p in primes:
        roots = find_roots_mod_prime_bruteforce(coeff, p)
        if not roots:
            continue

        new: List[Tuple[int, int]] = []
        for a, M in candidates:
            for r in roots:
                x, M2 = crt_pair(a, M, r, p)
                new.append((x, M2))

        # de-duplicate by residue
        uniq: Dict[int, int] = {}
        for x, M2 in new:
            uniq[x % M2] = M2
        candidates = [(x, M2) for x, M2 in uniq.items()]

        # stop once modulus exceeds bound
        if candidates and candidates[0][1] > bound:
            break

        # avoid explosion (shouldn't happen for small degrees)
        if len(candidates) > 5000:
            candidates = candidates[:5000]

    sols = set()
    for a, M in candidates:
        x0 = a % M
        if 0 <= x0 < bound:
            sols.add(x0)
    return sorted(sols)


# -------------------------
# Coppersmith-style recovery of p
# -------------------------


def _vector_to_integer_poly(vec: Sequence[int], X: int) -> List[int] | None:
    """
    Convert lattice vector (scaled by X^j) back to integer polynomial coefficients.
    We only accept vectors where each coefficient is exactly divisible by X^j.
    """
    coeff: List[int] = []
    for j, c in enumerate(vec):
        denom = pow(X, j)
        if c % denom != 0:
            return None
        coeff.append(c // denom)
    return poly_trim(coeff)


def _primitive(poly: List[int]) -> List[int]:
    g = 0
    for c in poly:
        g = math.gcd(g, abs(c))
    if g > 1:
        poly = [c // g for c in poly]
    # normalize sign
    if poly and poly[-1] < 0:
        poly = [-c for c in poly]
    return poly


def recover_p(N: int, pbar: int, kbits: int) -> int:
    """
    Recover p from N and pbar (MSBs of p).

    Model:
      p = pbar + x,  0 <= x < 2^kbits
    """
    X = 1 << kbits

    # f(x) = x + pbar
    f = [pbar, 1]

    # Try a small parameter grid; this instance is solved by (m=2, t=3).
    for m in range(2, 6):
        for t in range(1, 8):
            polys: List[List[int]] = []

            # g_{i}(x) = f(x)^i * N^{m-i} for i=0..m-1
            for i in range(m):
                g = poly_pow(f, i)
                g = poly_scale(g, pow(N, m - i))
                polys.append(g)

            # x^k * f(x)^m for k=0..t-1
            fm = poly_pow(f, m)
            for k in range(t):
                polys.append(poly_shift(fm, k))

            maxdeg = max(len(p) - 1 for p in polys)

            # build lattice basis with coefficient scaling by X^j
            basis: List[List[int]] = []
            for p in polys:
                v = [0] * (maxdeg + 1)
                for j, c in enumerate(p):
                    v[j] = c * pow(X, j)
                basis.append(v)

            reduced = lll_reduce(basis)

            # From reduced basis vectors, derive polynomials and hunt small roots
            for vec in reduced[:25]:
                poly = _vector_to_integer_poly(vec, X)
                if not poly or len(poly) <= 1:
                    continue
                poly = _primitive(poly)

                # Find candidate small integer roots by CRT reconstruction
                for x0 in find_small_integer_roots_via_crt(poly, X):
                    p = pbar + x0
                    g = math.gcd(p, N)
                    if 1 < g < N:
                        return g

    raise RuntimeError("failed to recover p (parameters may need tuning)")


# -------------------------
# RSA decryption
# -------------------------


def decrypt_m(N: int, e: int, c: int, p: int) -> bytes:
    q = N // p
    if p * q != N:
        raise ValueError("invalid p (does not divide N)")

    phi = (p - 1) * (q - 1)
    d = pow(e, -1, phi)
    m = pow(c, d, N)
    return int_to_bytes(m)


# -------------------------
# main
# -------------------------


def main() -> None:
    base = Path(__file__).resolve().parent
    data = parse_output_txt(base / "copper-copper-copper" / "output.txt")

    p = recover_p(data.N, data.pbar, data.kbits)
    pt = decrypt_m(data.N, data.e, data.c, p)
    print(pt.decode(errors="replace"))


if __name__ == "__main__":
    main()

