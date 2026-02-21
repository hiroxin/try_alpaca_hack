import os
from Crypto.Util.number import getPrime, bytes_to_long

FLAG = os.environ.get("FLAG", "Alpaca{ffffakeflagggg}")

KBITS = 200  # unknown lower bits of p

p = getPrime(512)
q = getPrime(512)
N = p * q
e = 65537

m = bytes_to_long(FLAG.encode())
c = pow(m, e, N)

pbar = p & (~((1 << KBITS) - 1))

print("N =", N)
print("e =", e)
print("c =", c)
print("pbar =", pbar)
print("kbits =", KBITS)
