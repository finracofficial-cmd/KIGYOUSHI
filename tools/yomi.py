"""Japanese reading helpers for narration.

speech_for(line, readings, mode)
  mode "kanji": apply explicit readings ([表示|よみ], episode readings, channel/yomi.json) and leave
                the rest as written (for models that read kanji well, e.g. ElevenLabs v3).
  mode "kana":  additionally convert every remaining kanji word to hiragana with SudachiPy, so models
                that misread kanji (on/kun readings) get unambiguous text.
kana_key(text)  katakana reading of any text, used to compare a script with what was heard.
cer(a, b)       character error rate between two reading strings.
"""
from __future__ import annotations

import json
import re
from functools import lru_cache

from episode_lib import ROOT, tokens

KANJI = re.compile(r"[㐀-鿿々〆ヵヶ]")
PUNCT = re.compile(r"[、。，．・「」『』（）()！？!?\s…―ー〜~:：;；\"'“”‘’]")


@lru_cache(maxsize=1)
def _tok():
    from sudachipy import dictionary, tokenizer
    return dictionary.Dictionary().create(), tokenizer.Tokenizer.SplitMode.C


@lru_cache(maxsize=1)
def channel_yomi() -> dict[str, str]:
    p = ROOT / "channel" / "yomi.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def kata2hira(s: str) -> str:
    return "".join(chr(ord(c) - 0x60) if "ァ" <= c <= "ヶ" else c for c in s)


def _to_kana(text: str) -> str:
    tk, mode = _tok()
    out = []
    for m in tk.tokenize(text, mode):
        surf = m.surface()
        out.append(kata2hira(m.reading_form()) if KANJI.search(surf) else surf)
    return "".join(out)


def speech_for(line: str, readings: dict[str, str], mode: str = "kanji") -> str:
    merged = {**channel_yomi(), **readings}
    parts = []
    for t in tokens(line, merged):
        if t[0] == "dual":
            parts.append(t[2])
        else:
            parts.append(_to_kana(t[1]) if mode == "kana" else t[1])
    return "".join(parts)


def kana_key(text: str) -> str:
    """Katakana reading without punctuation (digits are left as they are)."""
    tk, mode = _tok()
    text = PUNCT.sub("", text)
    return "".join(m.reading_form() for m in tk.tokenize(text, mode)) if text else ""


def cer(ref: str, hyp: str) -> float:
    if not ref:
        return 0.0
    d = list(range(len(hyp) + 1))
    for i, a in enumerate(ref, 1):
        p = d[:]
        d[0] = i
        for j, b in enumerate(hyp, 1):
            d[j] = min(p[j] + 1, d[j - 1] + 1, p[j - 1] + (a != b))
    return d[len(hyp)] / len(ref)


def diff_words(ref_text: str, heard_text: str, limit: int = 6) -> list[str]:
    """Short human-readable list of where the heard reading departs from the script."""
    import difflib
    a, b = kana_key(ref_text), kana_key(heard_text)
    out = []
    for op, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b).get_opcodes():
        if op != "equal":
            out.append(f"{a[max(0, i1 - 3):i2 + 3]} → {b[max(0, j1 - 3):j2 + 3]}")
        if len(out) >= limit:
            break
    return out
