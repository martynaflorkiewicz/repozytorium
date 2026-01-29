import os
import re
import cv2
import time
import pandas as pd
from paddleocr import PaddleOCR

CROPS_DIR = "out_crops"
INDEX_CSV = "out_crops/index.csv"

ocr = PaddleOCR(use_angle_cls=False, lang="en", drop_score=0.0)


def normalize_text(s: str) -> str:
    s = s.upper()
    s = re.sub(r"[^A-Z0-9]", "", s)
    if len(s) > 8 and s.startswith("PL"):
        s = s[2:]
    return s


def adaptive_balanced_logic_text(text: str) -> str:
    text = normalize_text(text)
    if len(text) < 4:
        return text

    chars = list(text)
    prefix_len = 3 if (len(chars) > 2 and chars[2].isalpha()) else 2

    for i in range(len(chars)):
        c = chars[i]
        if i < prefix_len:
            if c == "5": chars[i] = "S"
            if c == "0": chars[i] = "O"
            if c == "8": chars[i] = "B"
            if c == "1": chars[i] = "I"
        else:
            if c == "B": chars[i] = "8"
            if c in ("O", "Q"): chars[i] = "0"
            if c == "I": chars[i] = "1"
            if c == "S":
                prev_is_digit = (i - 1 >= 0 and chars[i - 1].isdigit())
                next_is_digit = (i + 1 < len(chars) and chars[i + 1].isdigit())
                if prev_is_digit or next_is_digit:
                    chars[i] = "5"

    res = "".join(chars)
    if len(res) > 8:
        res = res[:8]
    return res


def plate_score(s: str) -> float:
    if not s:
        return -1e9
    sc = 0.0
    if len(s) == 8:
        sc += 6.0
    elif len(s) == 7:
        sc += 5.5
    elif 6 <= len(s) <= 9:
        sc += 2.0
    else:
        sc -= 4.0

    if len(s) >= 2 and s[0].isalpha() and s[1].isalpha():
        sc += 6.0
    else:
        sc -= 10.0

    if s[0].isdigit():
        sc -= 4.0

    if any(c.isalpha() for c in s) and any(c.isdigit() for c in s):
        sc += 1.0
    return sc


def best_by_prefix_trim(det: str) -> str:
    det = normalize_text(det)
    if not det:
        return det
    cands = [det]
    if len(det) >= 2:
        cands.append(det[1:])
    if len(det) >= 3:
        cands.append(det[2:])

    best, best_sc = "", -1e18
    for c in cands:
        c2 = c[:8] if len(c) > 8 else c
        sc = plate_score(c2)
        if sc > best_sc:
            best_sc = sc
            best = c2
    return best


def preprocess_like_v62_for_paddle(crop_bgr):

    gray = cv2.cvtColor(crop_bgr, cv2.COLOR_BGR2GRAY)
    clahe = cv2.createCLAHE(clipLimit=1.5, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)
    enhanced = cv2.bilateralFilter(enhanced, 7, 75, 75)
    return cv2.cvtColor(enhanced, cv2.COLOR_GRAY2BGR)


def _to_float(x, default=0.0) -> float:
    try:
        if isinstance(x, (float, int)):
            return float(x)
        if isinstance(x, str):
            return float(x)
        if isinstance(x, (list, tuple)) and len(x) > 0:
            for v in x:
                if isinstance(v, (float, int)):
                    return float(v)
                if isinstance(v, str):
                    try:
                        return float(v)
                    except Exception:
                        pass
            return _to_float(x[0], default=default)
    except Exception:
        pass
    return default


def paddle_read_rec_only(img_bgr):

    result = ocr.ocr(img_bgr, det=False, rec=True, cls=False)

    out = []

    if not result:
        return out

    for item in result:
        if isinstance(item, (list, tuple)) and len(item) >= 2:
            txt = item[0]
            score = item[1]
            out.append((str(txt), _to_float(score)))
            continue

        if isinstance(item, (list, tuple)) and len(item) == 1 and isinstance(item[0], (list, tuple)) and len(item[0]) >= 2:
            txt = item[0][0]
            score = item[0][1]
            out.append((str(txt), _to_float(score)))
            continue

    return out



def calculate_final_grade(accuracy_percent: float, processing_time_sec: float) -> float:
    """Oblicza ocenę końcową na podstawie celności OCR i czasu przetwarzania."""
    if accuracy_percent < 60 or processing_time_sec > 60:
        return 2.0

    # Normalizacja celności: 60% → 0.0, 100% → 1.0
    accuracy_norm = (accuracy_percent - 60) / 40
    # Normalizacja czasu: 60s → 0.0, 10s → 1.0 (zakładamy limit 50s zakresu)
    time_norm = (60 - processing_time_sec) / 50
    # Ograniczenie do zakresu 0-1 (na wypadek czasu < 10s)
    time_norm = max(0.0, min(1.0, time_norm))

    # Składowa oceny: 0.7 wagi dla celności, 0.3 dla czasu
    score = 0.7 * accuracy_norm + 0.3 * time_norm

    # Mapowanie wyniku 0.0-1.0 na skalę ocen 2.0-5.0
    final_grade = 2.0 + (score * 3.0)

    # Zaokrąglenie do najbliższego 0.5
    return round(final_grade * 2) / 2
def evaluate():
    df = pd.read_csv(INDEX_CSV)
    df = df[df["crop_file"].astype(str) != ""].copy()
    grouped = df.groupby("filename", sort=False)

    correct = 0
    total = 0
    t0 = time.time()

    for filename, g in grouped:
        truth = normalize_text(str(g["plate_truth"].iloc[0]))

        best_det = ""
        best_sc = -1e18

        for _, r in g.iterrows():
            crop_file = str(r["crop_file"])
            crop_path = os.path.join(CROPS_DIR, crop_file)
            if not os.path.exists(crop_path):
                continue

            crop = cv2.imread(crop_path)
            if crop is None:
                continue

            crop_pp = preprocess_like_v62_for_paddle(crop)

            lines = paddle_read_rec_only(crop_pp)
            if not lines:
                continue

            texts = [t for (t, c) in lines if t is not None]
            candidates = texts + ["".join(texts)]

            for cand in candidates:
                det = adaptive_balanced_logic_text(cand)
                det = best_by_prefix_trim(det)

                sc = plate_score(det) + float(r["box_conf"]) * 0.5
                if sc > best_sc:
                    best_sc = sc
                    best_det = det

        if best_det == truth:
            correct += 1
        else:
            print(f" {filename} | Oryg: {truth} | Det: {best_det}")

        total += 1

    dur = time.time() - t0
    acc = (correct / total) * 100 if total else 0.0


    ocena = calculate_final_grade(acc, dur)
    print("\n" + "=" * 60)
    print("      --- RAPORT KOŃCOWY: OCENA ALGORYTMU ---")
    print("=" * 60)
    print(f"  CELNOŚĆ (%)             : {acc:.2f}%")
    print(f"  CZAS CAŁKOWITY (s)      : {dur:.2f}s")
    print("-" * 60)
    print(f"  WYLICZONA OCENA         : {ocena}")
    print("=" * 60)
if __name__ == "__main__":
    evaluate()
