## 2026/03/03 問題

https://alpacahack.com/daily/challenges/glibcs-secret-function

## 問題文

```
glibc has a secret function!
```

## 考察

### コードの中身を確認

```
char input[112], work[112];
printf("Input > ");
scanf("%111s", input);

size_t len = strlen(input);
if (len == sizeof(expected))
{
    strcpy(work, input);
    memfrob(work, len);
    if(!memcmp(work, expected, sizeof(expected)))
    {
        printf("Correct! The flag is %s\n", input);
        return 0;
    }
}
```

大まかな流れ

- 入力を読む（`scanf("%111s", input)`）
- 入力長が `sizeof(expected)` と一致するかチェック
  - `expected` は `unsigned char expected[97]` なので、`sizeof(expected) == 97`
- 入力を `work` にコピーして `memfrob(work, len)` を実行
  - `memfrob` は各バイトを `0x2a`（`*`）で XOR する関数
- `memcmp(work, expected, sizeof(expected))` が一致、つまり入力とフラグが一致したら、それを表示する

### 逆変換して元の入力を得る

XOR はビットが 1 ならば入力値を反転させる関数。 \
`0x2a` は16進数であり、これを２進数に変換すると `00101010` となる。

`memfrob(work, len)` は入力値 `work` の各バイトを `0x2a` で XOR する。第2引数は XOR 処理を何バイト行うかを指定する。つまり今回の場合は入力値の全バイトに対して XOR 処理を行う。

`memfrob` は `x ^= 0x2a` を全バイトに適用するだけなので可逆。 \
よって `expected[i] ^ 0x2a` を計算すれば、元の `input[i]` が得られる。

`expected[]` は C の配列として `main.c` に埋め込まれているため、スクリプトで配列をパースして XOR すればよい。

## 解答

スクリプト `rev.py` を実行する。

```
$ python3 2026-03/03-03_rev/rev.py
len(expected) = 97
Alpaca{This_is_the_*MYSTERIOUS_and_WONDERFUL*_function_in_glibc!_Also_how_about_strfry_function?}
```
