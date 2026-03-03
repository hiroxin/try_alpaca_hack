from __future__ import annotations

import re
from pathlib import Path


XOR_KEY = 0x2A  # memfrob は各バイトを 0x2a で XOR する


def parse_expected_from_main_c(main_c_path: Path) -> bytes:
    text = main_c_path.read_text(encoding="utf-8")
    # 読み込んだテキストの中から「expected[数字] = {数字の並び};」というパターンを探す
    # {} で囲まれた部分（数字の並び）だけを抽出する
    # \s* : スペース改行が0回以上繰り返される
    # \{([\s\S]*?)\} : {} で囲われた任意の文字が0回以上の繰り返し
    m = re.search(r"expected\s*\[\s*\d+\s*\]\s*=\s*\{([\s\S]*?)\}\s*;", text)
    if not m:
        raise ValueError("expected 配列が見つかりませんでした")

    # re.search の正規表現内の1つ目の括弧で囲まれた部分 `[\s\S]*?` だけを返す
    # 今回の場合は expected の配列の要素（数字の並び）だけを返す
    body = m.group(1)
    nums = []
    for token in body.split(","):
        t = token.strip()
        if not t:
            continue
        nums.append(int(t, 10))
    return bytes(nums)


def memfrob_reverse(data: bytes, key: int = XOR_KEY) -> bytes:
    # ジェネレータ式を使って複合 (XOR 処理)を行う
    return bytes(b ^ key for b in data)


def main() -> None:
    base = Path(__file__).resolve().parent
    main_c = base / "glibcs-secret-function" / "main.c"
    expected = parse_expected_from_main_c(main_c)
    flag_bytes = memfrob_reverse(expected)

    print(f"len(expected) = {len(expected)}")
    print(flag_bytes.decode(errors="replace"))


if __name__ == "__main__":
    main()