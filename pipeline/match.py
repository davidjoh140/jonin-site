"""Match a listing title (or a PSA cert) to a card in the Supabase card list."""
import re
from collections import defaultdict

NUM_RE = re.compile(r"(?<![A-Z0-9])(?:(PR|PS)\s?-?\s?(US)?\s?-?\s?(\d{1,4})|([NJMC])\s?-?\s?(US|C)?\s?-?\s?(\d{2,4})(B)?)(?![0-9])")
FOIL_WORDS = [("DIAMOND", "Diamond foil"), ("WAVY", "Wavy foil"), ("PRISM", "Prism foil"), ("CHECKER", "Prism foil"),
              ("SPIRAL", "Spiral foil"), ("FLAT", "Flat foil"), ("FULL FOIL", "Flat foil"), ("FULL ART", "Full art")]
GAME_PHRASES = re.compile(r"\bNARUTO(?=\s+(CCG|TCG|CARD|CARDS|SHIPPUDEN|COLLECTIBLE|TRADING|BANDAI)\b)")
STOP = {"THE", "OF", "A", "AN", "AND", "TO", "NO", "JUTSU", "STYLE"}


def norm_num(s):
    """'n064', 'N-064', 'N 64', 'N-US-12', 'PRUS 5' -> the card list's format ('N-064', 'N-US-012', 'PRUS005')."""
    m = NUM_RE.search(s.upper())
    return _fmt(m) if m else None


def _fmt(m):
    if m.group(1):
        return f"{m.group(1)}{m.group(2) or ''}{m.group(3).zfill(3)}"
    mid = f"-{m.group(5)}" if m.group(5) else ""
    return f"{m.group(4)}{mid}-{m.group(6).zfill(3)}{'b' if m.group(7) else ''}"


def _key(n):
    """Compare numbers without dashes or padding differences."""
    n = n.upper().replace("-", "")
    return re.sub(r"(?<=[A-Z])0+(?=\d)", "", n)


def words(s):
    return [w for w in re.findall(r"[A-Z0-9']+", s.upper()) if w not in STOP]


class Matcher:
    def __init__(self, cards, sets):
        self.by_num = defaultdict(list)
        for c in cards:
            self.by_num[_key(c["number"])].append(c)
        self.sets = {s["id"]: s for s in sets}

    def match(self, title, lot_words=(), allow_bare=False):
        """Returns (card, confidence, reason, printing, edition) or None.
        allow_bare: also try a bare number ("Third Hokage 968") when the title has no N-/J-/M- number;
        then the card's name must be in the title."""
        t = " " + re.sub(r"\s+", " ", title.upper()) + " "
        if any(f" {w.upper()} " in t or w.upper() in t and " " in w for w in lot_words):
            return None
        nums = {_fmt(m) for m in NUM_RE.finditer(t)}
        if not nums and allow_bare:
            return self._bare(t)
        if len(nums) != 1:            # no number, or several cards in one listing
            return None
        num = nums.pop()
        cands = self.by_num.get(_key(num), [])
        if not cands:
            return None
        tw = set(words(GAME_PHRASES.sub(" ", t)))  # "Naruto CCG" is the game, not the character
        scored = []
        for c in cands:
            nw = words(c["name"])
            name = sum(w in tw for w in nw) / len(nw) if nw else 0
            s = self.sets.get(c["set_id"], {})
            set_hit = bool(set(words(s.get("name", ""))) and set(words(s.get("name", ""))) <= tw) or \
                bool(s.get("code") and f" {s['code'].upper()} " in t)
            scored.append((name, set_hit, c))
        scored.sort(key=lambda x: (x[0], x[1]), reverse=True)
        name, set_hit, card = scored[0]
        if name < 0.5:
            return None
        conf = 0.6 + 0.3 * name
        reason = [f"number {num}", f"name {int(name * 100)}%"]
        if len(cands) > 1:            # reprint: same number in several sets
            if set_hit and not (len(scored) > 1 and scored[1][:2] == scored[0][:2]):
                conf += 0.05
                reason.append("set named")
            else:
                conf -= 0.25
                reason.append(f"number in {len(cands)} sets")
        elif set_hit:
            conf += 0.05
            reason.append("set named")
        printing = ""
        for w, p in FOIL_WORDS:
            if w in t and p in (card.get("printings") or []):
                printing = p
        if not printing and len(card.get("printings") or []) == 1:
            printing = card["printings"][0]
        edition = "1st Edition" if re.search(r"1ST\s?(ED|EDITION)?\b", t) else "Unlimited" if "UNLIMITED" in t else ""
        if edition and edition not in (card.get("editions") or []):
            edition = ""
        return card, round(min(conf, 0.99), 2), ", ".join(reason), printing, edition

    def _bare(self, t):
        """Bare 2-4 digit numbers: keep the card whose number and full name are both in the title."""
        tw = set(words(GAME_PHRASES.sub(" ", t)))
        hits = []
        for m in re.finditer(r"(?<![\w.$/#-])(\d{2,4})(?![\w.%/-])", t):
            n = int(m.group(1))
            if 1990 <= n <= 2030 or n < 10:
                continue
            for pre in ("N", "J", "M"):
                for c in self.by_num.get(_key(f"{pre}-{n:03d}"), []):
                    nw = words(c["name"])
                    if nw and all(w in tw for w in nw):
                        hits.append(c)
        ids = {c["id"] for c in hits}
        if len(ids) != 1:             # nothing, or ambiguous (reprint in several sets / several cards)
            return None
        card = hits[0]
        printing = ""
        for w, p in FOIL_WORDS:
            if w in t and p in (card.get("printings") or []):
                printing = p
        edition = "1st Edition" if re.search(r"1ST\s?(ED|EDITION)?\b", t) else "Unlimited" if "UNLIMITED" in t else ""
        if edition and edition not in (card.get("editions") or []):
            edition = ""
        return card, 0.75, f"bare number {card['number']}, full name", printing, edition
