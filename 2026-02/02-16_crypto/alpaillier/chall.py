import os
from Crypto.Util.number import getPrime, GCD, getRandomRange

def main():
    flag = os.getenv("FLAG", "Alpaca{REDACTED}").encode()

    bits = 1024
    p = getPrime(bits // 2)
    q = getPrime(bits // 2)
    n = p * q
    n2 = n * n
    g = n + 1

    r = getRandomRange(2, n - 1)
    while GCD(r, n) != 1:
        r = getRandomRange(2, n - 1)

    cs = []
    rn = pow(r, n, n2)
    for b in flag:
        c = (pow(g, b, n2) * rn) % n2
        cs.append(c)

    print(f"n = {n}\n")
    print(f"c = {cs}\n")

if __name__ == "__main__":
    main()
