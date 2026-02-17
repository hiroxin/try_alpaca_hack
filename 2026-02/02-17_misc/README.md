# 2026/02/17 問題

http://alpacahack.com/daily/challenges/wages-of-sin

## 問題文

```
People believe the behavior of math functions are environment-dependent.

nc 34.170.146.252 39684
```

## 考察

とりあえず添付のコマンドを実行してみる

```
$ nc 34.170.146.252 39684
env key: 123
env value: 123
We got 0.2512157895691234 as expected.
```

server.py の中身を確認する

```
key, value = input("env key: "), input("env value: ")
os.environ[key] = value
if os.system("qemu-x86_64 -cpu Skylake-Client-v3,-xsavec ./chall") == 0:
    print("Alpaca{*** REDACTED ***}")
```

外部から環境変数を設定して、chall を実行する。実行結果が 0 であれば、フラグが出力される。 \
この時、`qemu-x86_64 -cpu Skylake-Client-v3,-xsavec` は、x86_64 の CPU を Skylake-Client-v3 に設定し、xsavec を無効化している。 \
`os.system()` はサブシェル内でコマンドを実行するための Python 関数 \
また `xsavec` とは、コンテキストスイッチの高速化とメモリの節約を実現する CPU の機能

chall.c の中身を確認する

```
int main(void) {
  double x = 0.253936121155405;
  double sin_x = sin(x);
  if (sin_x == 0.2512157895691234) {
    printf("We got %.16f as expected.\n", sin_x);
    return 1;
  } else {
    printf("Wow, we got %.16f!\n", sin_x);
  }
}
```

sin(x) の値を比較しているが、 x は固定されているので、常に偽が返るようになっている。

調べてみると、浮動小数点は環境 (CPU) によって値が異なることがあるらしい。

また、 glibc の sin 関数は、環境によって精度が異なる。

- `__sin_avx2` : 最新CPU用（FMA命令を使って計算・超高速・高精度）
- `__sin_sse2` : 古いCPU用（普通の命令で計算・そこそこ・普通の精度）
- `__sin_generic` : 超古いCPU用

プログラムを起動したタイミングで glibc は CPU の情報を取得して、その CPU に最適な sin 関数を使用する。　\
今回は Skylake-Client-v3 になっているので、精度の高い `__sin_avx2` が使用される。 \
この仕組みを IFUNC (Indirect Function) と呼ぶ。

ただし、 環境変数 `GLIBC_TUNABLES` によって glibc の内部挙動を変更することができる。
今回は `glibc.cpu.hwcaps=-AVX2` によって、 CPU は AVX2 を持っていないように見せ、精度の低い `__sin_sse2` を使用させることで、 sin(x) の値を変更することができる。

## 解答

```
$ nc 34.170.146.252 39684
env key: GLIBC_TUNABLES
env value: glibc.cpu.hwcaps=-AVX2
Wow, we got 0.2512157895691233!
Alpaca{FMA_is_eSSEntial_2_the_expected_behAVXior}
```

## 参考

浮動小数点は環境 (CPU) によって値 (精度) が異なるため、浮動小数点の比較に `==` を使用することは推奨されていない。 \
そのため、浮動小数点の比較には専用のライブラリか、もしくは計算機イプシロン `if (abs(a - b) < epsilon)` という近似比較を行うことが主流
