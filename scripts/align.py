"""MMS forced alignment (torchaudio MMS_FA) o'zbek lotin matni uchun.

score <wav16k> <t0> <t1> "variant 1" "variant 2" ...  -> har variantning CTC NLL'i (past = ovozga mosroq)
words <wav16k> <segments.json> <out.json>           -> har so'zning boshlanish/tugash vaqti
"""
import json
import re
import sys

import torch
import torchaudio

_BIR = ["nol", "bir", "ikki", "uch", "to'rt", "besh", "olti", "yetti", "sakkiz", "to'qqiz"]
_ON = ["", "o'n", "yigirma", "o'ttiz", "qirq", "ellik", "oltmish", "yetmish", "sakson", "to'qson"]


def uz_num(n):
    """0..999999 -> o'zbekcha so'z (MMS uchun lotin, apostrof bilan)."""
    n = int(n)
    if n == 0:
        return "nol"
    out = []
    if n >= 1000:
        k = n // 1000
        out += ([] if k == 1 else [uz_num(k)]) + ["ming"]
        n %= 1000
    if n >= 100:
        k = n // 100
        out += ([] if k == 1 else [_BIR[k]]) + ["yuz"]
        n %= 100
    if n >= 10:
        out.append(_ON[n // 10])
        n %= 10
    if n:
        out.append(_BIR[n])
    return " ".join(out)


class _Num(dict):
    def get(self, k, d=None):
        return uz_num(k) if str(k).isdigit() else d


NUM = _Num()
bundle = torchaudio.pipelines.MMS_FA
model = bundle.get_model(with_star=False).eval()
DICT = bundle.get_dict(star=None)
SR = bundle.sample_rate


def norm_word(w):
    w = w.lower().replace("’", "'").replace("ʻ", "'").replace("‘", "'").replace("`", "'")
    if re.search(r"\d", w):
        w = " ".join(NUM.get(n, n) for n in re.findall(r"\d+", w))
    w = re.sub(r"[^a-z' ]", "", w.replace("-", " "))
    return w.split()


def load(path):
    wav, sr = torchaudio.load(path)
    if sr != SR:
        wav = torchaudio.functional.resample(wav, sr, SR)
    return wav.mean(0, keepdim=True)


def emit(wav, t0, t1):
    seg = wav[:, int(t0 * SR):int(t1 * SR)]
    with torch.inference_mode():
        em, _ = model(seg)
    return torch.log_softmax(em, dim=-1)


def ids(words):
    return [DICT[c] for w in words for c in w if c in DICT]


def nll(em, text):
    toks = [t for w in text.split() for t in norm_word(w)]
    tg = torch.tensor([ids(toks)], dtype=torch.int32)
    loss = torch.nn.functional.ctc_loss(em.transpose(0, 1), tg, torch.tensor([em.shape[1]]), torch.tensor([tg.shape[1]]),
                                        blank=0, reduction="sum", zero_infinity=True)
    return float(loss)


if __name__ == "__main__":
    mode, wavp = sys.argv[1], sys.argv[2]
    wav = load(wavp)
    if mode == "score":
        t0, t1 = float(sys.argv[3]), float(sys.argv[4])
        em = emit(wav, t0, t1)
        res = sorted((nll(em, v), v) for v in sys.argv[5:])
        for s, v in res:
            print(f"{s:8.1f}  {v}")
    else:
        segs = json.load(open(sys.argv[3]))
        out = []
        for sg in segs:
            t0, t1 = sg["t0"], sg["t1"]
            em = emit(wav, t0, t1)
            disp = sg["text"].split()
            norm = [norm_word(w) for w in disp]
            flat = [p for n in norm for p in n]
            tg = torch.tensor([ids(flat)], dtype=torch.int32)
            ali, sc = torchaudio.functional.forced_align(em, tg, blank=0)
            ali, sc = ali[0], sc[0].exp()
            spans = torchaudio.functional.merge_tokens(ali, sc)
            ratio = (t1 - t0) / em.shape[1]
            k = 0
            for dw, parts in zip(disp, norm):
                n = sum(len([c for c in p if c in DICT]) for p in parts)
                sp = spans[k:k + n]
                k += n
                if not sp:
                    continue
                out.append(dict(text=dw, start=round(t0 + sp[0].start * ratio, 3), end=round(t0 + sp[-1].end * ratio, 3),
                                score=round(float(sum(s.score for s in sp) / len(sp)), 3)))
        json.dump(out, open(sys.argv[4], "w"), ensure_ascii=False, indent=1)
        print(len(out), "so'z ->", sys.argv[4])
