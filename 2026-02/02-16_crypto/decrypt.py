from pathlib import Path
import ast

# データ読み込み
text = Path('alpaillier/output.txt').read_text()
n = int([l for l in text.splitlines() if l.startswith('n =')][0].split('=')[1].strip())
line = [l for l in text.splitlines() if l.startswith('c =')][0]
cs = ast.literal_eval(line.split('=', 1)[1].strip())

n2 = n * n
c0 = cs[0]

# バイト差を計算
deltas = []
for c in cs:
    d = (c * pow(c0, -1, n2)) % n2
    delta = (d - 1) // n
    # 範囲調整（必要に応じて）
    if delta > 255:
        delta -= n
    elif delta < -255:
        delta += n
    deltas.append(delta)

# b_0 を総当たり
for b0 in range(256):
    bs = [b0 + delta for delta in deltas]
    # 範囲チェック
    if all(0 <= b <= 255 for b in bs):
        msg = bytes(bs)
        # ASCII 文字列として自然かチェック
        if all(32 <= b < 127 for b in msg) or b'Alpaca{' in msg:
            print(msg.decode())
            break
