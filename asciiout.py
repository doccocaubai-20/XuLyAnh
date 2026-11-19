"""asciiout.py - bo dau tieng Viet khi in ra man hinh (tranh loi font tren Windows/Jupyter).
Chi can `import asciiout`; moi lenh print sau do se in khong dau. File CSV van giu nguyen tieng Viet co dau.
"""
import sys
import unicodedata


class _Ascii:
    def __init__(self, stream):
        self._s = stream

    def write(self, text):
        t = unicodedata.normalize("NFD", text.replace("đ", "d").replace("Đ", "D"))
        t = "".join(c for c in t if not unicodedata.combining(c))
        return self._s.write(t.encode("ascii", "replace").decode("ascii"))

    def flush(self):
        self._s.flush()

    def __getattr__(self, name):
        return getattr(self._s, name)


if not isinstance(sys.stdout, _Ascii):
    sys.stdout = _Ascii(sys.stdout)
    sys.stderr = _Ascii(sys.stderr)
