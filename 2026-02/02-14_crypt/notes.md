# 2026/02/14 問題

https://alpacahack.com/challenges/a-fact-of-CTF

## 問題文

```
The very first challenge ever completed for AlpacaHack was never released because we adjusted the difficulty for the first Crypto round. (Organizers' note)
```

スクリプトや暗号化されたフラッグは添付ファイルに入っている。

## 考察

暗号化スクリプトを解読して復号スクリプトを作成する。

暗号化スクリプトのざっくりとした流れ

1. 環境変数の取得
   - 環境変数 `FLAG` を読み込み、存在しない場合はデフォルト値 "not_a_flag" を代入
2. 長さのバリデーション
   - 300未満の素数は 62 個あるので、flag が 62 文字以下であることを保証する
3. 計算処理
   - flag の i 番目の文字 `c` に対して、その文字コード `ord(c)` を取得
   - リストの i 番目の素数 `primes[i]` のべき乗を計算して、全てを掛け合わせる
4. 出力
   - 最終的な巨大な整数を 16 進数表記で表示する

上記を参考に復号スクリプト decrypt.py を作成

実行

```
$ export CODE=$(cat 2026/02/02-14_crypt/a-fact-of-CTF/output.txt)
$ python3 2026/02/02-14_crypt/decrypt.py
Alpaca{prime_factorization_solves_everything}
```
