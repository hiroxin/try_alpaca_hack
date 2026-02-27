## 2026/02/27 問題

https://alpacahack.com/daily/challenges/rock-paper-scissors-lizard-spock

## 問題文

```
https://www.youtube.com/watch?v=jnfz_9d9BUA

http://34.170.146.252:31548
```

## 考察

`rock-paper-scissors-lizard-spock/web/index.js` を確認する。

このアプリは、いわゆる Rock/Paper/Scissors に Lizard/Spock を加えたじゃんけんを行い、連勝数（streak）が 100 以上になると `/` のページに FLAG を表示する。

```
// GET /
const rawStreak = req.signedCookies.streak ?? "0";
const streak = Number.parseInt(rawStreak, 10) || 0;
...
${streak >= 100 ? FLAG : "Win 100 times in a row to get the flag!"}
```

連勝数の管理はサーバ側セッションではなく、**署名付き Cookie (`signedCookies.streak`)** で行っている。

```
app.use(cookieParser(secret));
...
res.cookie("streak", String(nextStreak), { signed: true });
```

ここで `secret` は `crypto.randomUUID()` で生成されるが、サーバが起動している間は固定なので、クライアントは「サーバが発行した署名付き Cookie」を再利用できる。

一方で、**自分で改ざんした Cookie を作って 100 にする**ことは難しい（署名が必要）。

### ではどうやって 100 連勝するか

`/rpsls` は毎回ランダムに相手の手を決める。

```
const opponent = valid_inputs[Math.floor(crypto.randomInt(valid_inputs.length))];
```

勝ちなら `streak` を `+1`、負け/引き分けなら `streak=0` に戻す。

```
if (input === opponent) {
  res.cookie("streak", "0", { signed: true });  // Draw
} else if (winsAgainst[input].includes(opponent)) {
  res.cookie("streak", String(currentStreak + 1), { signed: true });  // Win
} else {
  res.cookie("streak", "0", { signed: true });  // Lose
}
```

ここで重要なのは **streak が Cookie で管理されている**点で、負け/引き分けで `streak=0` を食らっても、
クライアント側で「過去の（連勝が高い）Cookie」を保持しておけば、次の試行でそれを送り直すことができる。

このように、**都合の悪い結果（streak=0 になる Cookie）を受け入れず、良い結果の Cookie だけ保存して巻き戻す**手口は、
ゲームで言うところのセーブ＆ロードに似ているため、CTF では俗に **Save Scumming** と呼ばれる。

具体的には:

1. `streak` が最も大きい Cookie を `best_cookie` として保持
2. `POST /rpsls` を連打して `Set-Cookie: streak=...` を観測
3. もし streak が増えていたら `best_cookie` を更新、そうでなければ更新しない
4. `best_cookie` を送り続ければ、いつか 100 まで到達する

また `POST /rpsls` は最後に `res.redirect("/")` を返すので、スクリプトでは `allow_redirects=False` を指定して高速化している。

## 解答

環境汚さないよう `/tmp` 配下に仮想環境を作成して実行

```
$ python3 -m venv /tmp/alpaca-venv
source /tmp/alpaca-venv/bin/activate
python -m pip install -U pip requests
python ~/workspace/personal/try_alpaca_hack/2026-02/02-27_web/exploit.py

~~ snip ~~

[*] Save Scumming...
[+] Win! : Streak 1 / 100
[+] Win! : Streak 2 / 100

[+] Win! : Streak 98 / 100
[+] Win! : Streak 99 / 100
[+] Win! : Streak 100 / 100

[*] Reached 100 Streak! Get the flag...

[!] FLAG: Alpaca{And_as_it_always_has_Rock_crushes_Scissors}
```

## 参考

### `cookie-parser` の署名付き Cookie 形式

`cookie-parser` で `{ signed: true }` を付けると、Cookie 値は `s:<value>.<signature>` の形式になる。
（今回の `exploit.py` が `s:` の後ろの数字を正規表現で抜いていたのはこのため。）

### `allow_redirects=False` について

`POST /rpsls` のレスポンスは `302 Found` で `/` にリダイレクトする。
`requests` はデフォルトでリダイレクトを追従して HTML まで取りに行くので、試行回数が多い場合は遅くなる。
`allow_redirects=False` にすると、`Set-Cookie` だけ受け取ってすぐ次の試行に移れる。
