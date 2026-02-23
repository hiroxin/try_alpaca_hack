# 2026/02/23 問題

https://alpacahack.com/daily/challenges/alpaca-quest

## 問題文

```
You are a rookie adventurer who wandered into an alpaca village.
```

## 考察

`alpaca-quest.apk` というファイルが添付されている。この `.apk` とは Android アプリの配布用フォーマットのこと。取り扱うには専用のデコンパイラが必要になる。

とりあえず、 `jadx` を入れて `jadx-gui` を実行してみる。

まずはアプリの設計図にあたる `AndroidManifest.xml` を確認する。

```
<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    android:versionCode="1"
    android:versionName="1.0"
    android:compileSdkVersion="36"
    android:compileSdkVersionCodename="16"
    package="ctf.alpacaquest"

~~~ snip ~~~

        <activity
            android:name="ctf.alpacaquest.TitleActivity"
            android:exported="true">
            <intent-filter>
                <action android:name="android.intent.action.MAIN"/>
                <category android:name="android.intent.category.LAUNCHER"/>
            </intent-filter>
        </activity>
        <activity
            android:name="ctf.alpacaquest.MainActivity"
            android:exported="false"/>
        <provider

~~~ snip ~~~

</manifest>
```

`package="ctf.alpacaquest"` がアプリのパッケージ名になる

`<activity android:name="ctf.alpacaquest.TitleActivity">` タグの配下に `<action android:name="android.intent.action.MAIN"/>` とある。 \
つまり、アプリ起動時に `ctf.alpacaquest/TitleActivity` が最初に実行されることになる。

```
package ctf.alpacaquest;

import android.content.Intent;
import android.os.Bundle;

~~~ snip ~~~

    /* JADX INFO: Access modifiers changed from: private */
    public final void startGame(String lang) {
        Intent intent = new Intent(this, (Class<?>) MainActivity.class);
        intent.putExtra("lang", lang);
        startActivity(intent);
    }
}
```

`TitleActivity` では、 `MainActivity.class` を起動している。

MainActivity.class の中身を確認すると、コードの中に FLAG が隠されているので解答

```
TextView flagText = (TextView) findViewById(R.id.flag_text);
flagText.setText("Alpaca{h0w_d1d_y0u_b34t_th3_4lp4c4}");
```
