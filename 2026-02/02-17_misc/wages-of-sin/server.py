import os

key, value = input("env key: "), input("env value: ")
os.environ[key] = value
if os.system("qemu-x86_64 -cpu Skylake-Client-v3,-xsavec ./chall") == 0:
    print("Alpaca{*** REDACTED ***}")
