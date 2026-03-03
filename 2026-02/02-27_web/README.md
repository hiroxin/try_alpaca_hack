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

### コード解説

- `GET /`：現在の連勝数（streak）を表示し、じゃんけんのボタンを出す
- `POST /rpsls`：あなたの手を受け取り、相手の手をランダムに決めて勝敗を判定し、Cookie に streak を保存して / にリダイレクトする

#### 1〜12行目：ライブラリ読み込みと初期化

```
import express from "express";
import cookieParser from "cookie-parser";
import crypto from "crypto";
```

- `express`：ルーティング（`GET /` とか）やレスポンス返す処理を書くための Web フレームワーク
- `cookie-parser`：リクエストの Cookie を読みやすくし、さらに **署名付き Cookie** を扱えるようにする
- `crypto`：乱数など（ここでは UUID と乱数生成）

```
const FLAG = process.env.FLAG ?? "Alpaca{fake_flag}";
```

環境変数 `FLAG` があればそれ、なければダミーを使う。

```
const app = express();
const secret = crypto.randomUUID();
```

- `app`：Web アプリ本体
- `secret`：Cookie 署名に使う秘密鍵。サーバ起動中は固定だが再起動すると変わる

```
app.use(express.urlencoded({ extended: false }));
app.use(cookieParser(secret));
```

- `app.use(...)`：ミドルウェア登録（全リクエストに適用）
- `express.urlencoded(...)`：`POST` のフォーム（`application/x-www-form-urlencoded`）を `req.body` にパースする
- `cookieParser(secret)`：Cookie を `req.cookies` / `req.signedCookies` に展開する
  - `signedCookies` は「改ざん検知付き」の Cookie

#### 13〜20行目：ゲームのルール定義

```
const valid_inputs = ["rock", "paper", "scissors", "lizard", "spock"];
```

入力として受け付ける手の一覧。

```
const winsAgainst = {
  rock: ["scissors", "lizard"],
  paper: ["rock", "spock"],
  scissors: ["paper", "lizard"],
  lizard: ["spock", "paper"],
  spock: ["scissors", "rock"],
};
```

`winsAgainst[input]` が「input が勝てる相手の手」の配列。

- 例：`winsAgainst["rock"]` は `["scissors","lizard"]`

#### 22〜50行目：`GET /`（画面を返す）

```
app.get("/", async (req, res) => {
```

- `app.get(path, handler)`：`GET` のルート定義
- `req` はリクエスト、`res` はレスポンス

```
const rawStreak = req.signedCookies.streak ?? "0";
const parsedStreak = Number.parseInt(rawStreak, 10);
const streak = Number.isNaN(parsedStreak) ? 0 : parsedStreak;
```

- `req.signedCookies.streak`：署名付き Cookie の `streak` を読む
  - 無ければ `"0"`
- `Number.parseInt(str, 10)`：10進数として整数化
- `NaN`（数字にならない）なら 0 にする

```
const flash = req.signedCookies.flash;
if (flash) {
  res.clearCookie("flash", { signed: true });
}
```

- `flash` は 1回だけ表示したいメッセージ（勝った/負けた等）
- 表示したら `res.clearCookie` で消す（署名付きなので `{ signed: true }`）

```
const buttons = valid_inputs
  .map(
    (choice) =>
      `<button type="submit" name="input" value="${choice}">${choice}</button>`
  )
  .join("");
```

- `valid_inputs` をボタン HTML の配列に変換して、`join("")` で連結
- `name="input"` なので、押したボタンの `value` が `POST /rpsls` の `req.body.input` になる

```
return res.send(`<!DOCTYPE html> ...`);
```

`res.send`：レスポンス本文を送って終了。

```
${streak >= 100 ? FLAG : "..."}
```

連勝が 100 以上なら FLAG をページに表示、そうでなければメッセージ。

#### 53〜79行目：`POST /rpsls`（勝敗判定して Cookie 更新 → リダイレクト）

```
app.post("/rpsls", async (req, res) => {
  const { input } = req.body;
```

- `app.post`：`POST` ルート
- `req.body` はさっきの `express.urlencoded` のおかげで使える
- `{ input }` は分割代入（`req.body.input` を `input` という変数に）

入力バリデーション:

```
if(!valid_inputs.includes(input)) {
  res.cookie("streak", "0", { signed: true });
  res.cookie("flash", "Invalid input", { signed: true });
  return res.redirect("/");
}
```

- `includes`：配列にその要素が含まれるか
- 不正入力なら streak を 0 にして、flash をセットして `/` に戻す
- `res.cookie(name, value, options)`：`Set-Cookie` を返す
- `res.redirect("/")`：302 を返してブラウザに `/` を開かせる

相手の手をランダムに決める:

```
const opponent = valid_inputs[Math.floor(crypto.randomInt(valid_inputs.length))];
```

- `crypto.randomInt(n)`：0〜n-1 の整数乱数
- `Math.floor(...)` は不要に見えるけど（randomInt が整数なので）、意図として「整数にする」
- それで `valid_inputs[...]` を引いて相手の手を決める

現在の streak を読む:

```
const currentStreakRaw = req.signedCookies.streak ?? "0";
const currentStreakParsed = Number.parseInt(currentStreakRaw, 10);
const currentStreak = Number.isNaN(currentStreakParsed) ? 0 : currentStreakParsed;
```

`GET /` のときと同じ：Cookie から今の連勝数を読み取る。

勝敗判定して Cookie 更新:

```
if (input === opponent) {
  res.cookie("streak", "0", { signed: true });
  res.cookie("flash", "Draw!", { signed: true });
} else if (winsAgainst[input].includes(opponent)) {
  const nextStreak = currentStreak + 1;
  res.cookie("streak", String(nextStreak), { signed: true });
  res.cookie("flash", `You beat ${opponent}!`, { signed: true });
} else {
  res.cookie("streak", "0", { signed: true });
  res.cookie("flash", `You lost! ${opponent} beats ${input}.`, { signed: true });
}
```

- 引き分け：0 に戻す
- 勝ち：+1 して Cookie に保存
  - `String(nextStreak)` は Cookie が文字列なので文字列化
- 負け：0 に戻す
- どのケースでも flash Cookie にメッセージを入れる

最後に:

```
return res.redirect("/");
```

更新した Cookie を持ってトップページへ戻る。

#### ポイント

- streak はサーバDBじゃなく Cookie で管理されている
  - → ブラウザ（クライアント）が持つ状態がゲームの進行を決める
  - ただし 署名付き Cookie なので、値を雑に改ざんしても req.signedCookies 側では無効になる（改ざん検知）
  - POST /rpsls は毎回 streak を返してくれるので、クライアントが都合の良い Cookie だけ保存すると言った戦略が可能になる
