## 2026/03/02 問題

https://alpacahack.com/daily/challenges/bars

## 問題文

```
Bars, bars, and more bars.

http://34.170.146.252:55224
```

## 考察

コードを確認する

```
import os
from flask import Flask, render_template_string

app = Flask(__name__)

FLAG = os.environ.get("FLAG", "Alpaca{REDACTED}")

HTML = """
<!doctype html>
<html lang="ja">

~~~ snip ~~~

<body>
  <pre>FLAG: {{ flag }}</pre>
  <script>
    document.addEventListener("contextmenu", function(e) {
      e.preventDefault();

~~~ snip ~~~

</html>
"""

@app.route("/")
def index():
    return render_template_string(HTML, flag=FLAG)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000, debug=False)
```

環境変数に埋め込まれた FLAG を取得して、それをそのまま表示しているだけ。　\
ただし、 JavaScript のイベントハンドラでマウス操作を全て禁止している。

## 解答

ブラウザのメニューから More Tools > Developer Tools を開き、対象のプロパティを選択。すれば FLAG をコピペできる。

```
Alpaca{|1||I|l1|IIIl1|1lII|1II|1|I||||1IIlII|11I11II|l11|111l1lllI|I|1|lIIII1I1ll|l1|l1Il1I|11IIl1|1l1IlIII|I1I1I|llllll|l11l1ll11II||||ll11|1lIl11llI1Ill||I1||1|11llIlIIII|IIll1II|lll|I1l||IIIl1I11|1I|III|II|1||1III1I1lllI1l1l|I|1l1lI|II|1|||l|Il|IlII|ll|lIlI1IlIl1Ill11|II111||lI|lII|||IllllIII|l||l|l1Ill}
```

## 参考

### この問題の目的

あまりにもあっさり溶けてしまい表示抜けしたため Gemini に何がポイントだったのか確認

> この問題の意図は、まさにあなたが看破した通り、「ブラウザの画面上でどれだけマウスやキーボードの操作をJavaScriptで禁止しても、セキュリティとしては全く無意味である」というWebの鉄則を体感することにあります。

また、この他にも別の解法があるとのこと

> - ブラウザの機能を使う: URLの先頭に view-source: を付けて view-source:http://問題のURL にアクセスする（JSが実行される前の生のHTMLが表示される）。
> - ブラウザのJSをオフにする: ブラウザの設定でJavaScriptを無効化してリロードすれば、バリア自体が動かなくなり普通にコピペできるようになります。
> - コマンドラインから叩く: ターミナルから curl http://問題のURL を実行する（ブラウザですらないので、JSもCSSもガン無視で生のHTMLテキストが降ってきます）。

### バリアの解説

#### テキスト選択の禁止

```
pre {
~~~ snip ~~~
  user-select: none;
  -webkit-user-select: none;
~~~ snip ~~~
}
```

どちらも「テキスト選択の禁止」。違いはどのブラウザに向けた命令かという点

- `user-select`
  - W3C が定めた標準規格。現在の最新の Chrome, Firefox, Edge でサポートされている。
- `webkit-user-select`
  - WebKit ベースのブラウザ（Safari や古い Chrome など）でサポートされている。

#### 右クリックでのメニュー表示禁止

```
document.addEventListener("contextmenu", function(e) {
  e.preventDefault();
}, true);
```

- `contextmenu`
  - ハンドリングの対象。右クリックメニュー（コンテキストメニュー）を開く
- `function(e){...}`
  - イベントをキャッチした際に行われる処理。　`e` は発生したイベントの全情報が格納されたオブジェクト。「画面のどの座標が右クリックされたか」などのデータが詰まっている
- `e.preventDefault()`
  - デフォルト（標準）の振る舞いを防ぐ。今回は右クリックメニューの表示を強制的にキャンセルしている。
- `true`
  - キャプチャリングフェーズでのイベントのハンドリングを有効にする。

### キャプチャリングフェーズとは

Webページでクリックなどのイベントが起きた時、その情報波は以下の2つの経路をたどる。

- 1. キャプチャリングフェーズ（上から下へ）：
  - イベントを検知した要素 (今回の場合 `document`) から始まり、徐々に下の階層の要素（`div` → `p` → 実際にクリックされたターゲット）へとイベントが降りていく段階

- 2. バブリングフェーズ（下から上へ）：
  - ターゲットに到達した後、逆に親要素へ向かってイベントが伝わっていく段階

通常の `addEventListener`（第3引数を書かない、または `false` にした場合）は、「2. バブリング（下から上）」のタイミングで処理を実行される。この場合、 `body` や `pre` などの下の階層の要素が「右クリックされた時に独自のカスタムメニューを開く」などと言ったプログラムを持っていた場合は、 `document` に上がる前に実行されてしまう。

これを防ぐために `addEventListener` の第3引数に `true` を指定して、キャプチャリングフェーズでのイベントハンドリングを有効にすることで、下位要素の処理を `e.preventDefault()` で握りつぶすことができる。

さらに以下のように `e.stopPropagation()` を追加することで、イベントを検知した要素より下位の要素にイベントが伝わらないようにすることができる。

```
document.addEventListener("contextmenu", function(e) {
  e.preventDefault();
  e.stopPropagation();
}, true);
```
