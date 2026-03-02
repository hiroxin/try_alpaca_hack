import os
from flask import Flask, render_template_string

app = Flask(__name__)

FLAG = os.environ.get("FLAG", "Alpaca{REDACTED}")

HTML = """
<!doctype html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no">
  <title>Barcode</title>
  <style>
    html, body {
      margin: 0;
      height: 100%;
      overflow: hidden;
      overscroll-behavior: none;
      touch-action: none;
      background: #0b1020;
      color: #e5e7eb;
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", monospace;
    }
    pre {
      margin: 0;
      padding: 12px;
      font-size: 14px;
      line-height: 1.4;
      white-space: pre;
      user-select: none;
      -webkit-user-select: none;
      -webkit-touch-callout: none;
    }
  </style>
</head>
<body>
  <pre>FLAG: {{ flag }}</pre>
  <script>
    document.addEventListener("contextmenu", function(e) {
      e.preventDefault();
    }, true);

    function blockAllKeys(e) {
      e.preventDefault();
      e.stopPropagation();
      return false;
    }

    document.addEventListener("keydown", blockAllKeys, true);
    document.addEventListener("keypress", blockAllKeys, true);
    document.addEventListener("keyup", blockAllKeys, true);

    document.addEventListener("wheel", function(e) {
      e.preventDefault();
    }, { passive: false, capture: true });

    document.addEventListener("touchmove", function(e) {
      e.preventDefault();
    }, { passive: false, capture: true });

    document.addEventListener("touchstart", function(e) {
      e.preventDefault();
    }, { passive: false, capture: true });

    document.addEventListener("selectstart", function(e) {
      e.preventDefault();
    }, true);

    document.addEventListener("dragstart", function(e) {
      e.preventDefault();
    }, true);

    document.addEventListener("copy", function(e) {
      e.preventDefault();
    }, true);

    document.addEventListener("cut", function(e) {
      e.preventDefault();
    }, true);

    document.addEventListener("paste", function(e) {
      e.preventDefault();
    }, true);

    window.addEventListener("scroll", function() {
      window.scrollTo(0, 0);
    }, { passive: true });
  </script>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(HTML, flag=FLAG)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000, debug=False)