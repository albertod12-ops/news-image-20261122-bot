#!/usr/bin/env python3
"""news-image-20261122 v1: 36 stories, 7 regions, newspaper front page.
Draws entry.png (1024x1024, deterministic) from world.geo.json only.
ATM rebuild of the live top entries (jolly-stork-27 99.2369%,
evolution0795 99.1930%, gime22 99.1843%) — traits, never text: every
headline/caption is written in our own words, every art panel drawn
from scratch in our own code style. v1 changes vs the 20261121 v7
skeleton (kept whole: masthead, deck line, ticker, numbers strip,
region bar, UTC timeline, 3 heroes lead 396px + 2 rails 294px, 10
smalls in 5 columns, ALSO list 23, map, DATE CHECK box, footer):
 * all 36 stories re-dated to Sunday 22 Nov 2026 (verified live from
   Reuters/AP/AFP/BBC/Al Jazeera/Guardian/SCMP and the wires)
 * map is LIGHT (pale-blue ocean, tan land, navy dots, red pins) —
   v7's dark-navy map read as a black hole in the top entries' cream
   pages; the winners all use a light map
 * hero 1 art is new ("drones": night city + drone silhouettes +
   searchlights); cop31 banner fixed (DAY 14, TEXT LANDS — the final
   text landed at dawn, it is NOT "NO DEAL"); bahrain art's Saturday
   tanker labels replaced by a US 5th Fleet destroyer (today's story
   is the radar claim vs Bahrain's denial)
 * new small art: powercuts, factoryfire, hospital, strike, liquor
 * DOT_OFF support in draw_map (same leader-line pattern as
   PIN_OFF) — the Gulf, Brussels and NYC/DC clusters need it
NOTE: the first draw.py run right after an edit can render the pre-edit file
— always verify with 2-3 runs and take the later sha.
Run: python3 draw.py  -> writes entry.png in this directory."""
import json
import math
import os
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
W, H = 1024, 1024
PAPER = (247, 242, 231)
NEARWHITE = (253, 250, 242)
NAVY_DARK = (12, 28, 58)
LAND_TAN = (214, 196, 150)
INK = (17, 17, 17)
NAVY = (16, 62, 150)
RED = (220, 28, 60)
GOLD = (232, 178, 36)
YELLOW = (255, 210, 31)
GREY = (90, 90, 90)
RULE = (180, 170, 150)
OCEAN = (198, 226, 240)
SAND = (238, 220, 165)

FD = "/usr/share/fonts/truetype/dejavu"
FNOTO = "/usr/share/fonts/truetype/noto"
FLIB = "/usr/share/fonts/truetype/liberation"


def load_font(filename, size, base=FD):
    return ImageFont.truetype(os.path.join(base, filename), size)


# (name, file, size, base) — one table instead of thirty near-identical calls.
_FONT_TABLE = [
    # v20: masthead title 108->120px SQUEEZED. Probe-measured first
    # (font-size sweep 108/112/116/118/120/122/124): ink height grows
    # 100->103->107->108->109->112->114px; at 120px the ink is 109px
    # (on-page 19..127), matching #8's ~110px masthead. The layer is
    # 1335px wide, squeezed to 996px (0.746x; ink 0.753x) — more
    # condensed than v10's 0.834x but prototype-verified READABLE at 2x
    # (/tmp/mh-A120.png: glyphs narrow, no collisions, deck clear of
    # the 'y' descender). Font 122 (ink 112, 0.736x) was rejected: it
    # beats #8 by 2px but costs 3 more vertical px for no duel gain
    # and reads visibly more pinched. Ink top 19 (was 22): 1 blank row
    # below the kicker ink (ends 17) — the tightest legal top; deck
    # line moves to y=123 (ink 129-145, 2px clear of the title), bottom
    # rule to 147-149. The +5 masthead shift is funded below by tl_y
    # -1 and foot_y -1 (see main() comments), so the footer lands at
    # 1020, 1px slack to the 1021 limit. Deck stays 17px: its ink is
    # 17 rows tall at both 16px and 17px, so shrinking it buys 0px.
    ("F_TITLE", "LiberationSerif-Bold.ttf", 120, FLIB),
    ("F_EYE", "NotoSans-Black.ttf", 15, FNOTO),
    ("F_DECKLINE", "NotoSerif-Italic.ttf", 17, FNOTO),
    ("F_DATE", "NotoSans-Black.ttf", 30, FNOTO),
    ("F_DATE2", "NotoSans-Bold.ttf", 11, FNOTO),
    ("F_TTIME", "NotoSans-Bold.ttf", 12, FNOTO),
    ("F_TTEXT", "NotoSans-Bold.ttf", 10, FNOTO),
    ("F_KICK", "NotoSans-Bold.ttf", 10, FNOTO),
    # smalls kicker: 10px made #9 touch the pill (0.3px gap)
    ("F_KICK_S", "NotoSans-Bold.ttf", 9, FNOTO),
    # v8: fallback kicker size — card 12's kicker + CONFIRMED pill overflows
    # the 196px card at 9px (132+59+12=203); 8px fits (117+59+12=188).
    ("F_KICK_S8", "NotoSans-Bold.ttf", 8, FNOTO),
    ("F_PILL", "NotoSans-Bold.ttf", 8, FNOTO),
    ("F_SRC", "NotoSans-Bold.ttf", 9, FNOTO),
    # the BANNED/CLOSED stamp, big + bold like the user's reference
    ("F_STAMP", "NotoSans-Black.ttf", 12, FNOTO),
    ("F_HEAD", "LiberationSerif-Bold.ttf", 20, FLIB),
    # v8: hero headlines 22 -> 27px (28px measured: COP31 wraps to 3 lines;
    # 27px is the largest size fitting all three headlines in 2 lines).
    # Spacing 24 -> 31px in hero_card.
    ("F_HEAD_H", "LiberationSerif-Bold.ttf", 27, FLIB),
    ("F_HEAD_S", "LiberationSerif-Bold.ttf", 16, FLIB),
    ("F_DECK", "LiberationSerif-Regular.ttf", 12, FLIB),
    ("F_DECK_S", "LiberationSerif-Regular.ttf", 11, FLIB),
    ("F_LABEL", "NotoSans-Bold.ttf", 8, FNOTO),
    ("F_PIN", "NotoSans-Bold.ttf", 11, FNOTO),
    # v5.6: two-digit pins ("12"/"13" = 12.6px at 11px) overflow the 14px
    # circle; 9px (10.3px) leaves a real margin. Single digits stay 11px.
    ("F_PIN2", "NotoSans-Bold.ttf", 9, FNOTO),
    ("F_ART", "NotoSans-Black.ttf", 24, FNOTO),
    ("F_ART_S", "NotoSans-Bold.ttf", 12, FNOTO),
    ("F_ART2", "NotoSans-Black.ttf", 17, FNOTO),
    ("F_ART2_S", "NotoSans-Bold.ttf", 11, FNOTO),
    # 2/3 of F_ART (hero 3 label)
    ("F_LBL", "NotoSans-Black.ttf", 16, FNOTO),
    # 2/3 of F_ART_S
    ("F_LBL_S", "NotoSans-Bold.ttf", 9, FNOTO),
    # 2/3 of F_ART2 (small-card labels)
    ("F_LBL2", "NotoSans-Black.ttf", 12, FNOTO),
    # smaller steps so the solid art banner auto-fits long label pairs
    ("F_LBL2_11", "NotoSans-Black.ttf", 11, FNOTO),
    ("F_LBL2_10", "NotoSans-Black.ttf", 10, FNOTO),
    ("F_LBL2_9", "NotoSans-Black.ttf", 9, FNOTO),
    # 2/3 of F_ART2_S
    ("F_LBL2_S", "NotoSans-Bold.ttf", 8, FNOTO),
    ("F_ALSO", "NotoSans-Bold.ttf", 11, FNOTO),
    ("F_ALSO_N", "NotoSans-Bold.ttf", 11, FNOTO),
    ("F_SEC", "NotoSans-Black.ttf", 13, FNOTO),
    ("F_STATB", "NotoSerif-Black.ttf", 21, FNOTO),
    # v9: compressed stats strip (28px tall) — value 18px, caption 9px.
    ("F_STATB18", "NotoSerif-Black.ttf", 18, FNOTO),
    ("F_STATC9", "NotoSans-Bold.ttf", 9, FNOTO),
    ("F_STATC", "NotoSans-Bold.ttf", 10, FNOTO),
    ("F_LEGEND", "NotoSans-Bold.ttf", 10, FNOTO),
    ("F_DATECHK", "NotoSans-Bold.ttf", 11, FNOTO),
    ("F_FOOT", "NotoSans-Bold.ttf", 10, FNOTO),
]
for _fname, _ffile, _fsize, _fbase in _FONT_TABLE:
    globals()[_fname] = load_font(_ffile, _fsize, _fbase)
del _fname, _ffile, _fsize, _fbase, _FONT_TABLE

PILL_COL = {
    # v8: CONFIRMED (two named sources agree) joins REPORTED (one named
    # source) as the per-card verification tag, the #2 pattern. The pill
    # shows the tag; the old `status` field stays in FRONT for the record.
    "CONFIRMED": (16, 165, 90),
    "REPORTED": (16, 165, 90),
    "FORECAST": (20, 110, 230),
    "CLAIM": (230, 150, 0),
    # v5: OFFICIAL (on the record — signed pacts, official timing)
    "OFFICIAL": (0, 110, 160),
}

# num, region, topic, source, status, headline, deck, art big, art small,
# art key, verification tag — CONFIRMED where research-v2.md shows 2+
# named outlets agreeing, CLAIM where one side's account is unverified.
# v4 (22 Nov 2026): smalls reordered to top 1's relative order for the
# shared cards — 4 Hormuz, 5 Iran, 6 Trump, 7 China-Japan, 8 Davao,
# 9 Canberra, 10 Bitcoin, 11 Russell, 12 Rahul, 13 Kryvyi Rih (last,
# unchanged). Same 13 drawn cards, same headlines/decks/art; only the
# order and the card numbers change. Heroes 1-3 unchanged.
# v2 (21 Nov 2026): 35 stories, 13 drawn cards + 22 also-list. Every
# story happened or was first reported on Saturday 21 November 2026
# (Friday-event stories count only where Saturday reporting is the first
# wide report — Trump tax, China-Japan, Canberra AI talks, Denmark
# expulsion, Kryvyi Rih toll, Palisades verdict — see research-v2.md).
# Layout change from v1: 13 drawn cards (3 heroes + 2 rows x 5 smalls),
# hero art 160px, smalls art 64px, map 336x168.
FRONT = [
    (1, "KYIV REGION", "WAR", "UKRAINIAN AIR FORCE · REUTERS", "REPORTED",
     "Russia fires 186 drones; a Kyiv block is destroyed",
     "Defences downed 161 of 186 drones fired overnight; one hit a five-storey block in Dymer, 14 may be trapped.",
     "186 DRONES", "161 DOWNED", "drones", "CONFIRMED"),
    (2, "ANTALYA", "CLIMATE", "REUTERS · BBC", "REPORTED",
     "COP31 text lands, deal in doubt",
     "Keeps the 35% clean-electricity goal, drops $120bn — never names fossil fuels.",
     "FINAL TEXT", "NO FOSSIL FUELS", "cop31", "CONFIRMED"),
    (3, "MANAMA", "IRAN", "IRGC · BAHRAIN MOI", "CLAIM",
     "Iran's radar claim, Bahrain's denial",
     "Tehran says it hit two Patriot radars; Bahrain says a civilian site burned, no injuries.",
     "2 RADARS?", "CLAIM VS DENIAL", "bahrain", "CLAIM"),
    (4, "HONG KONG", "ELECTIONS", "SCMP", "REPORTED",
     "Hong Kong elects its Election Committee",
     "856 candidates for 723 seats; turnout hit 93.55% by 14:00.",
     "856 CANDIDATES", "723 SEATS", "spain", "CONFIRMED"),
    (5, "WELLINGTON", "CRICKET", "REUTERS", "REPORTED",
     "India declare on 720/9, a record in New Zealand",
     "Rahul 136, Gill 98; hosts 119/2, trailing by 233.",
     "720/9 DECLARED", "INDIA'S RECORD", "cricket", "CONFIRMED"),
    (6, "LAS VEGAS", "FORMULA 1", "FIA · AP", "REPORTED",
     "Verstappen takes the Las Vegas GP",
     "Wins from pole in 1:33.9, 0.639 s clear of Norris.",
     "VERSTAPPEN WINS", "LAS VEGAS GP", "russell", "CONFIRMED"),
    (7, "GULF OF FINLAND", "SEA", "REUTERS", "REPORTED",
     "Russian cargo ship Sparta II still burning",
     "Hit by drones Saturday; Finland leads salvage.",
     "SHIP ABLAZE", "16 CREW SAFE", "finland", "CONFIRMED"),
    (8, "TEHRAN", "ENERGY", "REUTERS", "REPORTED",
     "Iran begins rationing electricity",
     "Rolling cuts up to two hours a day as war damage bites.",
     "POWER CUTS", "2 HOURS A DAY", "powercuts", "CONFIRMED"),
    (9, "CIKANDE", "FIRE", "DETIKNEWS", "REPORTED",
     "Candy-factory fire in Cikande",
     "3 dead, 36 missing; search goes on.",
     "3 DEAD, 36 MISSING", "BANTEN PLANT", "factoryfire", "CONFIRMED"),
    (10, "BRASÍLIA", "HEALTH", "REUTERS", "REPORTED",
     "Bolsonaro in intensive care in Brasília",
     "Acute bowel obstruction, stable; surgery possible.",
     "IN INTENSIVE CARE", "BOWEL OBSTRUCTION", "hospital", "CONFIRMED"),
    (11, "WASHINGTON", "CYBER", "AP", "REPORTED",
     "FBI probes apparent hack of its crime database",
     "Washington State pauses gun-dealer checks; breach assessed.",
     "FBI PROBE", "CRIME DATABASE", "fbi", "REPORTED"),
    (12, "BRUSSELS", "TRAVEL", "REUTERS", "REPORTED",
     "Belgian controllers join Monday's national strike",
     "Most flights grounded 07:00–21:00 on Monday.",
     "FLIGHTS GROUNDED", "MONDAY STRIKE", "strike", "CONFIRMED"),
    (13, "MANIPUR", "POISONING", "XINHUA", "REPORTED",
     "Toxic-liquor toll in Manipur climbs to 19",
     "600 in hospital, six held; toll up from Saturday.",
     "TOLL AT 19", "600 IN HOSPITAL", "liquor", "REPORTED"),
]

# num, city, text, source — every item carries its outlet (the top-3 pattern);
# texts are terse (probe-measured with draw.py's own F_ALSO) so
# "City: text (SRC)" fits one 320px line (limit 298px).
# v1 20261122: all 23 lines re-dated to Sunday 22 Nov 2026, verified
# live from the wires. The Friday-20-Nov Peru quake stays ONLY as
# the Sunday toll update (14); Saturday-21-Nov stories stay OUT
# (El Chapo Isidro, Bayelsa boat, EU-Indonesia deal, BepiColombo,
# Fred Nile, the FT's Decart report) — they belong in the DATE CHECK
# box, not the list. 31 is Bangkok, not Seattle: the Decart deal was
# first reported by the FT on Saturday; the Kok River pollution-zone
# designation is the Sunday news (Reuters, govt said Sunday).
ALSO = [
    (14, "Junín", "Peru quake toll: 1 dead, 16 hurt", "REUTERS"),
    (15, "Warsaw", "Rutte vows NATO defence", "REUTERS"),
    (16, "Copenhagen", "Russian attaché expelled", "AL JAZEERA"),
    (17, "New Delhi", "Nepal PM Shah lands on state visit", "IANS"),
    (18, "Seoul", "minister quits over exam cheating", "REUTERS"),
    (19, "Manila", "Chinese bomber turns back 170 km out", "AP"),
    (20, "Hanoi", "death penalty scrapped for drugs", "REUTERS"),
    (21, "Tokyo", "record 93% friendly to Korea in poll", "YONHAP"),
    (22, "Beijing", "China renews UN bid to ban BLA", "REUTERS"),
    (23, "Khartoum", "drones strike homes near the capital", "AFP"),
    (24, "Nigeria", "mourners' boat capsizes, 24 dead", "AP"),
    (25, "Kordofan", "RSF accused of killing 5 children", "REUTERS"),
    (26, "Canberra", "Marles rejects US report on subs", "ABC"),
    (27, "Melbourne", "70 years on from 1956 Olympics", "ABC"),
    (28, "Gaza", "Israeli fire kills four, 3 in food van", "REUTERS"),
    (29, "Riyadh", "Saudi, Houthi forces exchange fire", "REUTERS"),
    (30, "New York", "US stocks fall into correction", "REUTERS"),
    (31, "Bangkok", "Kok River declared pollution zone", "REUTERS"),
    (32, "Los Angeles", "Hunger Games opens to $56M", "REUTERS"),
    (33, "Miami", "GTA 6 sets record $3.79B launch day", "REUTERS"),
    (34, "Leeds", "Leeds stun Chelsea 4-1 away", "REUTERS"),
    (35, "Vatican", "Pope hosts 1,300 poor guests", "VATICAN"),
    (36, "Turin", "Alcaraz faces Zverev for ATP Finals title", "ATP"),
]

# 6 figures, one per top story where a number carries it — all
# Sunday-dated, like top 1's strip.
STATS = [
    ("186", "drones fired"),
    ("161", "downed"),
    ("35%", "clean power by 2035"),
    ("$120bn", "adaptation cut"),
    ("720/9", "India's record"),
    ("856", "HK candidates"),
]

# Region counts counted from OUR actual 36-story list (FRONT 1-13 +
# ALSO 14-36), assigned by subject, not dateline city.
# EUROPE 8: 1 Kyiv-region, 7 Gulf of Finland, 12 Brussels, 15 Warsaw,
#   16 Copenhagen, 34 Leeds, 35 Vatican, 36 Turin.
# MIDDLE EAST 4: 3 Manama, 8 Tehran, 28 Gaza, 29 Riyadh.
# AFRICA 3: 23 Khartoum, 24 Nigeria, 25 Kordofan.
# ASIA-PACIFIC 11: 4 Hong Kong, 5 Wellington, 9 Cikande, 13 Manipur,
#   17 New Delhi, 18 Seoul, 19 Manila, 20 Hanoi, 21 Tokyo, 22 Beijing,
#   31 Bangkok.
# AMERICAS 7: 6 Las Vegas, 10 Brasília, 11 Washington, 14 Junín,
#   30 New York, 32 Los Angeles, 33 Miami.
# OCEANIA 2: 26 Canberra, 27 Melbourne.
# WORLD 1: 2 COP31 (Antalya venue, global subject).
# Total 8+4+3+11+7+2+1 = 36. ✓
# (label, count, fill, text colour)
REGIONS = [
    ("EUROPE", 8, (16, 62, 150), "white"),
    ("MIDDLE EAST", 4, (200, 60, 30), "white"),
    ("AFRICA", 3, (30, 130, 80), "white"),
    ("ASIA-PACIFIC", 11, (90, 60, 140), "white"),
    ("AMERICAS", 7, (16, 40, 90), "white"),
    ("OCEANIA", 2, (0, 120, 180), "white"),
    ("WORLD", 1, (90, 90, 90), "white"),
]

LEGEND = [
    # v8: CONFIRMED joins the legend (the per-card pill now shows the
    # verification tag, not the old status word).
    ("CONFIRMED", "two named sources agree"),
    ("OFFICIAL", "on the record"),
    ("REPORTED", "one named source"),
    ("FORECAST", "a landfall, schedule or draft"),
    ("CLAIM", "one side's claim, unverified"),
]

PINS = {
    1: (30.5, 50.4), 2: (30.7, 36.9), 3: (50.6, 26.2),
    4: (114.2, 22.3), 5: (174.8, -41.3), 6: (-115.1, 36.2),
    7: (24.5, 59.9), 8: (51.4, 35.7), 9: (106.1, -6.0),
    10: (-47.9, -15.8), 11: (-77.0, 38.9), 12: (4.4, 50.8),
    13: (94.0, 24.8),
}
# Every FRONT story has a pin (no location-less card this time —
# COP31's Antalya venue is pin 2).
DOTS = {
    14: (-76.0, -11.0), 15: (21.0, 52.2), 16: (12.6, 55.7),
    17: (77.2, 28.6), 18: (127.0, 37.5), 19: (121.0, 14.6),
    20: (105.8, 21.0), 21: (139.7, 35.7), 22: (116.4, 39.9),
    23: (32.6, 15.6), 24: (8.0, 9.0), 25: (29.0, 13.0),
    26: (149.1, -35.3), 27: (145.0, -37.8), 28: (34.5, 31.5),
    29: (46.7, 24.7), 30: (-74.0, 40.7), 31: (100.5, 13.8),
    32: (-118.2, 34.0), 33: (-80.2, 25.8), 34: (-1.5, 53.8),
    35: (12.45, 41.9), 36: (7.7, 45.1),
}
# v1 20261122: 36 dots, one per also-list line. Dot-dot tight pairs
# are true geography at this scale, not defects: 23 Khartoum /
# 25 Kordofan ~4.0px, 26 Canberra / 27 Melbourne ~4.3px, 35 Vatican /
# 36 Turin ~3.8px, 20 Hanoi / 31 Bangkok ~5.3px (2px-radius dots).
PROBLEMS = []


def wrap(d, text, fnt, width, max_lines=None):
    """Greedy word wrap to `width` px; records a PROBLEM if it overflows max_lines."""
    out = []
    line = ""
    for word in text.split():
        trial = word if not line else line + " " + word
        if d.textlength(trial, font=fnt) <= width:
            line = trial
        else:
            if line:
                out.append(line)
            line = word
    if line:
        out.append(line)
    if max_lines is not None and len(out) > max_lines:
        PROBLEMS.append("TRUNCATED (%d lines): %s" % (len(out), text))
        out = out[:max_lines]
    return out


def art_text(img, d, x, y, w, h, big, small, f_big, f_small, dy=0):
    """White bold label inside the art on a dark scrim, bottom-left.
    Draws nothing when both strings are empty — the art already says it.
    dy shifts the whole label up (negative) or down inside the art."""
    if not big and not small:
        return
    big_w = int(d.textlength(big, font=f_big))
    small_w = int(d.textlength(small, font=f_small)) if small else 0
    if max(big_w, small_w) + 22 > w:
        PROBLEMS.append("ART TEXT TOO WIDE: %s / %s" % (big, small))
    label_w = max(big_w, small_w)
    label_h = f_big.size + f_small.size + 10
    scrim = Image.new("RGBA", img.size, (0, 0, 0, 0))
    sd = ImageDraw.Draw(scrim)
    sd.rounded_rectangle([x + 4, y + h - label_h - 4 + dy,
                          x + 4 + label_w + 12, y + h - 4 + dy],
                         radius=3, fill=(0, 0, 0, 115))
    img.paste(scrim, (0, 0), scrim)
    d.text((x + 10, y + h - label_h + dy), big, font=f_big, fill="white",
           stroke_width=1, stroke_fill=(0, 0, 0))
    if small:
        d.text((x + 10, y + h - label_h + f_big.size + 2 + dy), small,
               font=f_small, fill="white", stroke_width=1,
               stroke_fill=(0, 0, 0))


def art_banner(img, d, x, y, w, h, big, small, fill):
    """v4: solid colour banner strip at the TOP of a small card's art box,
    white text on it — the top-3 pattern (their cards carry a red/blue label
    banner, not a bottom scrim). Big label left, small label right on one
    18px line; the big font auto-shrinks (12 -> 11 -> 10 -> 9) until the
    pair fits, so no wording ever changes. Art drawn under the banner's
    18px is hidden behind it, as in a magazine label overlap."""
    if not big and not small:
        return
    d.rectangle([x, y, x + w, y + 18], fill=fill)
    f_big = F_LBL2
    for cand in (F_LBL2, F_LBL2_11, F_LBL2_10, F_LBL2_9):
        if int(d.textlength(big, font=cand)) + int(d.textlength(small, font=F_LBL2_S)) + 14 <= w:
            f_big = cand
            break
    else:
        f_big = F_LBL2_9
        PROBLEMS.append("ART BANNER TOO WIDE: %s / %s" % (big, small))
    # v5.4: text vertically centred in the 18px strip — middle anchor
    # at the strip centre (y+9), not top-anchored at y+3/y+5.
    d.text((x + 6, y + 9), big, font=f_big, fill="white", anchor="lm")
    if small:
        d.text((x + w - 6, y + 9), small, font=F_LBL2_S, fill="white",
               anchor="rm")


def _star(d, cx, cy, r_out, r_in, fill="white"):
    """Small 5-point star centred at (cx, cy)."""
    points = []
    for k in range(10):
        radius = r_out if k % 2 == 0 else r_in
        angle = math.radians(-90 + k * 36)
        points.append((cx + radius * math.cos(angle),
                       cy + radius * math.sin(angle)))
    d.polygon(points, fill=fill)


def _skyline(d, w, h, base, col, seed):
    """Night skyline with lit windows, ported from 19 Nov (v3 density).
    Deterministic: seeded Random, so the render is reproducible."""
    import random
    rnd = random.Random(seed)
    x = 0
    while x < w:
        bw = rnd.randint(14, 30)
        bh = rnd.randint(int(h * 0.3), int(h * 0.75))
        d.rectangle([x, base - bh, x + bw, base], fill=col)
        for wy in range(base - bh + 6, base - 4, 10):
            for wx in range(x + 3, x + bw - 3, 7):
                if rnd.random() < 0.5:
                    d.rectangle([wx, wy, wx + 3, wy + 4], fill=(255, 210, 31))
        x += bw + 3


def stamp(img, x, y, text, angle=-15, font=None, ink=(200, 16, 46, 255),
          fill=None):
    """Diagonal rubber-stamp label (the #1 entry's signature device).
    `text` in bold caps inside a 3px outline box, drawn on a small
    RGBA tile that is rotated and pasted onto `img` at (x, y). The text is
    centred in the box (anchor "mm"). Default: red ink, transparent box;
    pass fill=(255, 255, 255, 255) + ink=(0, 0, 0, 255) for black-on-white."""
    fnt = font if font is not None else F_SRC
    probe = Image.new("RGBA", (1, 1))
    probe_d = ImageDraw.Draw(probe)
    box = probe_d.textbbox((0, 0), text, font=fnt)
    text_w, text_h = box[2] - box[0], box[3] - box[1]
    pad = 4
    tile_w, tile_h = text_w + pad * 2 + 4, text_h + pad * 2 + 4
    tile = Image.new("RGBA", (tile_w, tile_h), (0, 0, 0, 0))
    tile_d = ImageDraw.Draw(tile)
    tile_d.rectangle([2, 2, tile_w - 3, tile_h - 3],
                     fill=fill, outline=ink, width=3)
    tile_d.text((tile_w / 2, tile_h / 2), text, font=fnt,
                fill=ink, anchor="mm")
    tile = tile.rotate(angle, expand=True, resample=Image.BICUBIC)
    img.paste(tile, (x, y), tile)


def _cubic(p0, p1, p2, p3, t):
    mt = 1.0 - t
    return (mt ** 3 * p0[0] + 3 * mt * mt * t * p1[0]
            + 3 * mt * t * t * p2[0] + t ** 3 * p3[0],
            mt ** 3 * p0[1] + 3 * mt * mt * t * p1[1]
            + 3 * mt * t * t * p2[1] + t ** 3 * p3[1])


def smooth_arrow(img, p0, p1, p2, p3, color, w_tail=8.0, w_tip=5.0,
                 head_len=15.0, head_w=14.0, ss=4):
    """A smooth tapered curved arrow: cubic-bezier centreline sampled at
    81 points, band built from its two offset curves (width tapering
    from w_tail at the tail to w_tip near the head), ending in a clean
    filled arrowhead whose axis aligns with the curve tangent at the
    tip (head ~2.2x band width wide, ~1.6x long). Drawn on a 4x
    supersampled RGBA layer and downscaled with LANCZOS so the edges
    are anti-aliased, not jagged."""
    n = 81
    pts = [_cubic(p0, p1, p2, p3, i / (n - 1)) for i in range(n)]
    seg = [math.hypot(pts[i + 1][0] - pts[i][0],
                      pts[i + 1][1] - pts[i][1]) for i in range(n - 1)]
    back, hi = 0.0, n - 1
    while hi > 0 and back < head_len:
        back += seg[hi - 1]
        hi -= 1

    def tangent(i):
        a = pts[max(0, i - 1)]
        b = pts[min(n - 1, i + 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        m = math.hypot(dx, dy) or 1.0
        return dx / m, dy / m

    left, right = [], []
    for i in range(hi + 1):
        t = i / (n - 1)
        hw = (w_tail / 2) * (1 - t) + (w_tip / 2) * t
        tx, ty = tangent(i)
        nx, ny = -ty, tx
        left.append((pts[i][0] + nx * hw, pts[i][1] + ny * hw))
        right.append((pts[i][0] - nx * hw, pts[i][1] - ny * hw))
    tx, ty = tangent(n - 1)
    nx, ny = -ty, tx
    bx, by = pts[hi]
    head = [(p3[0], p3[1]),
            (bx + nx * head_w / 2, by + ny * head_w / 2),
            (bx - nx * head_w / 2, by - ny * head_w / 2)]
    w, h = img.size
    layer = Image.new("RGBA", (w * ss, h * ss), (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    fill = color + (255,)
    ld.polygon([(x * ss, y * ss) for x, y in left + right[::-1]], fill=fill)
    ld.polygon([(x * ss, y * ss) for x, y in head], fill=fill)
    layer = layer.resize((w, h), Image.LANCZOS)
    img.paste(layer, (0, 0), layer)


def art_image(key, w, h):
    """Flat-vector picture for one front story, drawn in code."""
    img = Image.new("RGB", (w, h), PAPER)
    d = ImageDraw.Draw(img)
    if key == "akvan":
        # v4: SATELLITE view, like the top-3 heroes — the line-art tornado
        # is gone (it can be restored on request; see NOTES.md). Dark teal
        # Bay of Bengal, the Odisha coast down the left with a Gopalpur dot,
        # a big white spiral cyclone with an eye over the sea, and a white
        # "Landfall · 8 am" strip at the bottom-right. The AKVAN scrim stays
        # bottom-left, as on the other heroes. Original PIL vector code.
        d.rectangle([0, 0, w, h], fill=(8, 64, 88))
        # deeper water, bottom-right
        d.rectangle([0, 78, w, h], fill=(6, 52, 74))
        # the Odisha coast: land down the left edge, wavy shoreline
        land = [(0, 0), (96, 0), (82, 22), (90, 46), (72, 68), (82, 88),
                (70, h), (0, h)]
        d.polygon(land, fill=(216, 196, 150))
        d.polygon([(0, 0), (52, 0), (44, 30), (30, 60), (38, h), (0, h)],
                  fill=(150, 170, 100))
        d.line([(96, 0), (82, 22), (90, 46), (72, 68), (82, 88), (70, h)],
               fill=(240, 235, 220), width=2)
        d.text((10, 8), "ODISHA", font=F_ART2_S, fill=(60, 50, 30))
        # rain bands over the sea, short diagonal streaks around the storm
        for rx, ry in ((150, 12), (180, 8), (300, 16), (330, 30), (150, 88),
                       (310, 84), (350, 60), (120, 40), (360, 12)):
            d.line([rx, ry, rx - 6, ry + 10], fill=(170, 205, 225), width=2)
        # the cyclone: a SPIRAL, not concentric rings (v4 fix: the first
        # version read as a target) — arcs of growing radius, each rotated
        # further round, plus two thick comma arms sweeping out to the
        # edges, and a dark eye at the centre. Centre (250, 50).
        cx, cy = 250, 50
        for rr, a0, a1, wd in ((12, 40, 300, 3), (20, 120, 20, 3),
                               (28, 200, 110, 3), (36, 280, 190, 2),
                               (44, 0, 270, 2)):
            d.arc([cx - rr, cy - rr, cx + rr, cy + rr], a0, a1,
                  fill="white", width=wd)
        # spiral arms: curved sweeps from the rings out to the edges
        d.arc([cx - 62, cy - 44, cx + 62, cy + 44], 300, 40,
              fill=(220, 235, 245), width=4)
        d.arc([cx - 70, cy - 34, cx + 70, cy + 34], 120, 220,
              fill=(200, 220, 240), width=3)
        d.ellipse([cx - 8, cy - 8, cx + 8, cy + 8], fill=(8, 64, 88),
                  outline="white", width=2)
        d.ellipse([cx - 3, cy - 3, cx + 3, cy + 3], fill="white")
        # Gopalpur dot on the coast, red with a white ring + label, clear
        # of the AKVAN scrim (which starts at the bottom-left, y ~66+)
        d.ellipse([78, 54, 88, 64], fill=RED, outline="white", width=2)
        d.text((92, 55), "Gopalpur", font=F_LBL2_S, fill="white",
               stroke_width=1, stroke_fill=(0, 0, 0))
        # white caption strip, bottom-right, over the sea (like #1)
        d.rectangle([248, 84, w - 4, 100], fill="white")
        d.text((318, 92), "Landfall · 8 am", font=F_ART2_S, fill=RED,
               anchor="mm")
    elif key == "kyiv":
        # v3: DENSITY — a night scene filling the whole frame: stars,
        # skyline with lit windows across the back, river with reflections
        # below, three towers + cables, deck with a broken middle span,
        # fire + a big smoke plume, debris and ripples. No empty dark top.
        d.rectangle([0, 0, w, h], fill=(14, 24, 52))
        # stars across the sky
        for sx, sy in ((10, 6), (40, 10), (90, 4), (130, 8), (180, 5),
                       (230, 9), (270, 4), (286, 12), (160, 12), (60, 14),
                       (20, 18), (110, 2), (200, 14), (250, 2), (70, 20),
                       (150, 2), (285, 20), (100, 16)):
            d.ellipse([sx, sy, sx + 2, sy + 2], fill="white")
        # v22: the missile trails moved BELOW the skyline/deck (see the
        # v22 block after the deck) — the v4 set was drawn here, before
        # the skyline, so the buildings covered most of each arc.
        # Kyiv skyline across the whole back, lit windows (19 Nov _skyline)
        _skyline(d, w, 52, 46, (38, 58, 96), 7)
        # a gold-domed church in the skyline, right side
        d.rectangle([238, 28, 262, 46], fill=(120, 140, 180))
        d.ellipse([240, 18, 260, 32], fill=GOLD)
        d.line([250, 10, 250, 18], fill=GOLD, width=2)
        # the river, from the deck line down, with reflections
        d.rectangle([0, 46, w, h], fill=(18, 54, 100))
        for ry in (56, 64, 72, 80, 88, 96):
            for rx0, rx1 in ((8, 60), (70, 120), (130, 200), (210, 286)):
                d.line([rx0, ry, rx1, ry], fill=(70, 120, 180), width=1)
        # firelight reflected under each fire, on the water
        for fx0, fx1 in ((132, 168), (222, 248)):
            for ry in (58, 66, 74):
                d.line([fx0 + 4, ry, fx1 - 4, ry], fill=(255, 170, 60),
                       width=2)
        # towers: pale, three of them, sky down into the river
        for tx in (48, 148, 248):
            d.rectangle([tx, 12, tx + 8, 80], fill=(220, 220, 220))
            d.rectangle([tx - 4, 24, tx + 12, 28], fill=(220, 220, 220))
            d.rectangle([tx - 4, 52, tx + 12, 56], fill=(200, 200, 200))
        # cables fanning from each tower top down to the deck
        for cx0, cx1 in ((52, 10), (52, 120), (152, 90), (152, 210),
                         (252, 180), (252, 290)):
            d.line([cx0, 14, cx1, 40], fill=(200, 200, 200), width=2)
        # the deck: gold and thick; the middle span is broken and dropped
        d.rectangle([0, 40, 132, 47], fill=(255, 205, 40))
        d.rectangle([168, 40, w, 47], fill=(255, 205, 40))
        d.polygon([(132, 40), (168, 40), (162, 58), (138, 58)],
                  fill=(120, 30, 30))
        # v22: SEVEN missile trails — #3's last edge. The v4 set was 3
        # thin dashed arcs drawn BEFORE the skyline, so the buildings
        # covered most of each arc and only specks showed at the top
        # edge. #3's Kyiv art is 5-7 long bold continuous streaks
        # across the whole sky. These 7 are solid width-3 arcs drawn
        # AFTER the skyline/church/towers/deck, so they read across
        # the full sky like #3's, fanning down-left from the top edge
        # to the deck; the two right-hand arcs are routed clear of the
        # gold dome (T6 passes left of it, T7 right of it). Heads and
        # glows are drawn last (after the fires) so every warhead
        # stays visible.
        for (x0, y0, xc, yc, x1, y1, col) in (
                (48, 0, 30, 24, 12, 46, (255, 170, 60)),
                (96, 0, 72, 26, 48, 48, (255, 110, 50)),
                (144, 0, 122, 26, 98, 48, (255, 200, 90)),
                (188, 0, 168, 26, 146, 48, (255, 170, 60)),
                (228, 0, 208, 26, 186, 46, (255, 110, 50)),
                (262, 0, 232, 24, 210, 46, (255, 200, 90)),
                (292, 0, 276, 22, 266, 42, (255, 170, 60))):
            prev = None
            for ti in range(41):
                t = ti / 40
                qx = int((1 - t) ** 2 * x0 + 2 * (1 - t) * t * xc + t ** 2 * x1)
                qy = int((1 - t) ** 2 * y0 + 2 * (1 - t) * t * yc + t ** 2 * y1)
                if prev is not None:
                    d.line([prev, (qx, qy)], fill=col, width=3)
                prev = (qx, qy)
        # fire on the broken span: layered burst with flame spikes, and a
        # big smoke plume rising from it (overlapping grey clouds)
        d.ellipse([132, 28, 168, 48], fill=(200, 40, 30))
        d.ellipse([136, 24, 164, 46], fill=(255, 140, 40))
        d.ellipse([142, 30, 160, 44], fill=(255, 220, 80))
        for fx, fy in ((138, 28), (148, 24), (158, 28)):
            d.polygon([(fx - 4, 30), (fx, fy - 10), (fx + 4, 30)],
                      fill=(255, 140, 40))
        d.ellipse([134, 6, 152, 22], fill=(200, 200, 200))
        d.ellipse([146, 0, 164, 16], fill=(220, 220, 220))
        d.ellipse([126, 12, 142, 26], fill=(210, 210, 210))
        # a second, smaller spiked fire on the right span
        d.ellipse([222, 32, 248, 46], fill=(255, 140, 40))
        d.ellipse([228, 37, 242, 44], fill=(255, 220, 80))
        d.polygon([(226, 34), (224, 26), (230, 32)], fill=(255, 140, 40))
        d.polygon([(240, 34), (242, 26), (244, 34)], fill=(255, 140, 40))
        d.ellipse([232, 20, 246, 32], fill=(205, 205, 205))
        # v4: a third, smaller fire on the left span + its smoke, and a
        # taller smoke column over the main break (more fires + smoke)
        d.ellipse([28, 34, 48, 46], fill=(255, 140, 40))
        d.ellipse([33, 38, 43, 44], fill=(255, 220, 80))
        d.polygon([(32, 36), (30, 28), (36, 34)], fill=(255, 140, 40))
        d.ellipse([34, 22, 46, 32], fill=(205, 205, 205))
        d.ellipse([142, -2, 158, 12], fill=(225, 225, 225))
        d.ellipse([128, 2, 142, 14], fill=(210, 210, 210))
        # v22: glowing warheads at all 7 trail ends + a wider smoke
        # cloud flanking the main column + embers rising from the
        # break. Drawn last so they sit on top of the deck/fires.
        for (hx, hy) in ((12, 46), (48, 48), (98, 48), (146, 48),
                         (186, 46), (210, 46), (266, 42)):
            d.ellipse([hx - 6, hy - 6, hx + 6, hy + 6], fill=(255, 120, 40))
            d.ellipse([hx - 3, hy - 3, hx + 3, hy + 3], fill=(255, 235, 150))
        d.ellipse([112, 8, 128, 20], fill=(215, 215, 215))
        d.ellipse([158, 6, 174, 18], fill=(225, 225, 225))
        for ex, ey in ((140, 20), (160, 14), (232, 16), (40, 26), (200, 30)):
            d.ellipse([ex, ey, ex + 2, ey + 2], fill=(255, 180, 80))
        # debris in the river under the break + a rescue boat, far right
        d.rectangle([138, 62, 150, 66], fill=(40, 40, 40))
        d.rectangle([152, 66, 160, 69], fill=(40, 40, 40))
        d.polygon([(262, 74), (288, 74), (284, 80), (266, 80)],
                  fill=(255, 210, 31))
        d.rectangle([272, 68, 280, 74], fill=(230, 200, 160))
    elif key == "cop31":
        # v1 20261122: the final text LANDED at dawn — the v7 "NO DEAL"
        # banner is wrong for today. Big globe left, red thermometer
        # (+1.5C / LIMIT AT RISK) centre, clock face (DAY 14) right,
        # big red TEXT LANDS banner bottom-centre (box widened to
        # 120px: "TEXT LANDS" at F_ART2 needs ~110px). Hero art is
        # drawn at 105px tall and stretched to 160px, so the globe
        # and clock are drawn squashed (height = width / 1.52) and
        # render round. The COP31 / DAY 14 · TEXT LANDS scrim stays
        # bottom-left, as on the other heroes.
        d.rectangle([0, 0, w, h], fill=(11, 110, 110))
        # globe: blue ocean + green continents, large and round-on-page
        d.ellipse([24, 20, 124, 86], fill=(30, 120, 200),
                  outline=(20, 20, 20), width=2)
        for lx0, ly0, lx1, ly1 in ((40, 34, 68, 52), (70, 54, 102, 74),
                                   (40, 60, 56, 72)):
            d.ellipse([lx0, ly0, lx1, ly1], fill=(60, 180, 90))
        # thermometer: white tube, red fill rising, round bulb, ticks
        d.rectangle([150, 14, 162, 64], fill="white", outline=(20, 20, 20))
        d.rectangle([152, 32, 160, 64], fill=(220, 30, 40))
        d.ellipse([144, 60, 168, 76], fill=(220, 30, 40),
                  outline=(20, 20, 20))
        for tick_y in (20, 28, 36, 44, 52, 60):
            d.line([162, tick_y, 167, tick_y], fill=(20, 20, 20), width=1)
        d.text((174, 16), "+1.5°C", font=F_ART2, fill="white")
        d.text((174, 38), "LIMIT", font=F_ART2_S, fill="white")
        d.text((174, 50), "AT RISK", font=F_ART2_S, fill="white")
        # clock face: white dial, hands at 1 o'clock (Day 14), DAY 14 below
        d.ellipse([310, 26, 378, 70], fill="white", outline=(20, 20, 20),
                  width=2)
        for ang in range(0, 360, 30):
            tx = 344 + int(30 * math.cos(math.radians(ang)))
            ty = 48 + int(19 * math.sin(math.radians(ang)))
            d.ellipse([tx - 1, ty - 1, tx + 1, ty + 1], fill=(20, 20, 20))
        d.line([344, 48, 344, 30], fill=(20, 20, 20), width=3)
        d.line([344, 48, 355, 33], fill=(20, 20, 20), width=3)
        d.ellipse([341, 45, 347, 51], fill=(20, 20, 20))
        d.text((344, 74), "DAY 14", font=F_ART2_S, fill="white",
               anchor="ma")
        # big red TEXT LANDS banner, bottom-centre — clear of the globe
        # (ends x124), the thermometer bulb (ends x168, y76), the clock
        # (starts x310) and the scrim (bottom-left, ends ~x101).
        d.rectangle([180, 78, 300, 102], fill=(179, 34, 44))
        d.text((240, 90), "TEXT LANDS", font=F_ART2, fill="white",
               anchor="mm")
    elif key == "kenya":
        # v6: Kenya spuds its first commercial oil well — a Turkana
        # oilfield: a lattice derrick on the left, a pumpjack (nodding
        # donkey) working the well in the middle, sun + dry scrub.
        # Original PIL vector code.
        d.rectangle([0, 0, w, h], fill=(238, 222, 178))
        # sun, top-right, clear of the banner (y0-18)
        d.ellipse([168, 22, 186, 40], fill=(255, 200, 60),
                  outline=(230, 170, 40), width=2)
        # dry scrub on the horizon
        for sx, sy in ((8, 52), (60, 54), (150, 52), (185, 54)):
            d.ellipse([sx, sy, sx + 10, sy + 4], fill=(120, 140, 70))
        # the ground, lower third
        d.rectangle([0, 56, w, h], fill=(190, 150, 95))
        d.line([0, 56, w, 56], fill=(150, 115, 70), width=2)
        # derrick: a lattice tower, left — two legs + crossbars + diagonals
        d.line([24, 56, 34, 20], fill=(60, 50, 40), width=3)
        d.line([48, 56, 38, 20], fill=(60, 50, 40), width=3)
        for bx0, by, bx1 in ((32, 26, 40), (30, 34, 42), (28, 42, 44),
                             (26, 50, 46)):
            d.line([bx0, by, bx1, by], fill=(60, 50, 40), width=2)
        d.line([32, 26, 42, 50], fill=(60, 50, 40), width=1)
        d.line([40, 26, 28, 50], fill=(60, 50, 40), width=1)
        d.rectangle([30, 18, 42, 22], fill=(60, 50, 40))
        # pumpjack: A-frame, walking beam, horse head + counterweight,
        # polished rod down to the wellhead
        d.polygon([(104, 56), (112, 36), (120, 56)], fill=(40, 40, 40))
        d.line([86, 34, 148, 42], fill=(30, 30, 30), width=4)
        # horse head: the rounded end of the beam, left
        d.ellipse([78, 28, 92, 42], fill=(30, 30, 30))
        # counterweight box, right end of the beam
        d.rectangle([144, 38, 156, 50], fill=(30, 30, 30))
        # polished rod + wellhead
        d.line([85, 36, 85, 56], fill=(80, 80, 80), width=2)
        d.rectangle([78, 54, 92, 60], fill=(60, 60, 60))
        # a black oil drop beside the wellhead
        d.ellipse([160, 60, 172, 70], fill=(20, 20, 20))
        d.polygon([(166, 52), (160, 62), (172, 62)], fill=(20, 20, 20))
    elif key == "selloff":
        # v5.2: user rejected the v5.1 3D blue bars — redraw as the
        # VERTICAL MIRROR of card 10 (the CPI rising chart, which the
        # user likes): same style — rainbow bars + ONE thick dark
        # curved arrow — but flipped: bars DESCEND left to right and
        # the arrow curves DOWN from top-left to bottom-right. Same
        # verified Friday data: Taipei -6.2, Seoul -5.2, Tokyo -5.1,
        # Hong Kong -1.9 (tallest to shortest, colours in the same
        # rainbow palette order as card 10: green, yellow, orange,
        # red). Art is 196x80 with the solid banner over y0-18; bars
        # sit on baseline y56, names + values in two lines below.
        # Original PIL vector code.
        d.rectangle([0, 0, w, h], fill=(246, 242, 233))
        for gy in range(20, 56, 12):
            d.line([0, gy, w, gy], fill=(228, 223, 208), width=1)
        base = 56
        bars = (("TAIPEI", "-6.2%", 32, (60, 180, 80)),
                ("SEOUL", "-5.2%", 27, (250, 200, 40)),
                ("TOKYO", "-5.1%", 26, (240, 130, 30)),
                ("HONG KONG", "-1.9%", 11, (220, 50, 50)))
        # flat rainbow bars, descending left to right, lighter top
        # strip per bar (same treatment as card 10's rising bars)
        for i, (name, val, bh, col) in enumerate(bars):
            bx = 12 + i * 48
            top = base - bh
            light = tuple(min(255, c + 60) for c in col)
            d.rectangle([bx, top, bx + 32, base], fill=col)
            d.rectangle([bx, top, bx + 32, top + 2], fill=light)
        d.line([6, base, w - 4, base], fill=(180, 175, 160), width=1)
        # v5.4: arrow path shrunk for clearance — tail top edge 6px
        # below the banner (was touching it), head bottom 8px above the
        # bar labels (was ~2px). Same smooth tapered style and colour.
        smooth_arrow(img, (10, 28), (58, 26), (118, 34), (180, 50),
                     (30, 30, 40))
        # names + values in two lines under the bars; the last name is
        # clamped so it clears the right edge ("HONG KONG" is 51px wide)
        for i, (name, val, bh, col) in enumerate(bars):
            cx = 12 + i * 48 + 16
            nw = d.textlength(name, font=F_LBL2_S)
            cx = min(cx, 192 - nw / 2)
            d.text((cx, 61), name, font=F_LBL2_S, fill=INK, anchor="ma")
            d.text((12 + i * 48 + 16, 70), val, font=F_LBL2_S, fill=RED,
                   anchor="ma")
    elif key == "ukeu":
        # two flags, one deal: EU stars on the left, the Union Jack's cross
        # on the right, a gold link between them. v4: BIGGER flags — wider
        # star circle (centre dropped to y46 so the top star clears the
        # solid banner), thicker Jack cross.
        d.rectangle([0, 0, w, h], fill=(20, 40, 120))
        for a in range(8):
            sx = 48 + int(32 * math.cos(math.radians(a * 45)))
            sy = 46 + int(26 * math.sin(math.radians(a * 45)))
            _star(d, sx, sy, 5, 2, fill=(255, 210, 31))
        d.rectangle([98, 0, 196, h], fill="white")
        d.rectangle([98, 32, 196, 48], fill=(200, 20, 40))
        d.rectangle([140, 0, 156, h], fill=(200, 20, 40))
        d.line([98, 0, 196, h], fill=(20, 40, 120), width=4)
        d.line([196, 0, 98, h], fill=(20, 40, 120), width=4)
        d.rectangle([90, 34, 106, 46], fill=GOLD)
        d.text((98, 40), "=", font=F_ART2, fill=(20, 20, 20), anchor="mm")
    elif key == "italy":
        # v5: Rome, not Paris — the CGIL general strike. St Peter's dome
        # and colonnade across the back, a tricolour flag, and marchers
        # with placards filling the street. The old "strike" branch (Paris
        # facades, "25+ COUNTRIES" banner) is gone with the wrong framing.
        # Original PIL vector code.
        d.rectangle([0, 0, w, h], fill=(205, 214, 226))
        # St Peter's dome, centre, behind the march (banner covers y0-18)
        d.ellipse([68, 8, 128, 56], fill=(150, 140, 120))
        d.rectangle([92, 2, 104, 16], fill=(150, 140, 120))
        d.ellipse([94, -2, 102, 8], fill=(150, 140, 120))
        # colonnade: a row of small columns under the dome
        d.rectangle([52, 52, 144, 56], fill=(120, 110, 95))
        for cx0 in range(56, 140, 12):
            d.rectangle([cx0, 44, cx0 + 4, 52], fill=(200, 190, 170))
        # the road, full width, with dashes
        d.rectangle([0, 62, w, h], fill=(110, 110, 116))
        d.line([0, 62, w, 62], fill=(60, 60, 65), width=2)
        for dx in range(4, w, 20):
            d.line([dx, 71, dx + 10, 71], fill="white", width=2)
        # tricolour flag on a pole, left — green/white/red vertical bands
        d.line([14, 22, 14, 52], fill=(60, 40, 20), width=2)
        for fi, fcol in enumerate(((0, 140, 60), "white", (200, 40, 40))):
            d.rectangle([14 + fi * 6, 22, 14 + fi * 6 + 6, 32], fill=fcol)
        # five marchers, in stride, placards up on the middle two
        skins = [(200, 140, 90), (220, 180, 140), (190, 130, 85),
                 (210, 160, 110), (200, 140, 90)]
        shirts = [(40, 90, 160), (200, 40, 40), (30, 140, 80),
                  (220, 170, 40), (90, 60, 140)]
        for i, x in enumerate((30, 62, 94, 126, 158)):
            d.ellipse([x + 3, 30, x + 15, 42], fill=skins[i])
            d.ellipse([x + 6, 35, x + 8, 37], fill=(20, 20, 20))
            d.ellipse([x + 10, 35, x + 12, 37], fill=(20, 20, 20))
            d.rectangle([x + 2, 42, x + 14, 56], fill=shirts[i])
            d.line([x + 5, 56, x + 1, 68], fill=(20, 20, 20), width=2)
            d.line([x + 9, 56, x + 15, 68], fill=(20, 20, 20), width=2)
            if i == 0:
                d.line([x + 4, 44, 46, 40], fill=skins[i], width=2)
            if i == 4:
                d.line([x + 10, 44, 156, 40], fill=skins[i], width=2)
            if i in (1, 3):
                # middle marchers hold small placards up
                d.line([x + 12, 44, x + 16, 34], fill=(60, 40, 20), width=2)
                d.rectangle([x + 10, 26, x + 24, 36], fill="white",
                            outline=INK)
    elif key == "iraq":
        # desert stronghold: a walled compound with a watchtower, two tanks
        # moving in across the sand
        d.rectangle([0, 0, w, h], fill=(228, 200, 150))
        d.rectangle([20, 30, 176, 62], fill=(190, 160, 110))
        d.rectangle([20, 30, 176, 36], fill=(160, 130, 85))
        d.rectangle([86, 12, 110, 36], fill=(170, 140, 95))
        d.rectangle([92, 18, 104, 24], fill=(60, 40, 20))
        for wx in range(30, 170, 18):
            d.rectangle([wx, 42, wx + 8, 50], fill=(90, 70, 40))
        # two SMALL tanks on the right: full-size tanks at the bottom-left
        # would sit under the art_text scrim and vanish. 32px wide, clear
        # of the scrim (which ends ~x126).
        for tx, ty in ((128, 62), (162, 62)):
            d.rectangle([tx, ty, tx + 32, ty + 8], fill=(70, 90, 60))
            d.rectangle([tx + 8, ty - 5, tx + 22, ty], fill=(70, 90, 60))
            d.line([tx + 22, ty - 2, tx + 34, ty - 2], fill=(40, 50, 35),
                   width=3)
            d.ellipse([tx + 3, ty + 8, tx + 8, ty + 11], fill=(40, 40, 40))
            d.ellipse([tx + 24, ty + 8, tx + 29, ty + 11], fill=(40, 40, 40))
        d.ellipse([160, 18, 178, 30], fill=(240, 230, 200))
        d.ellipse([166, 20, 188, 28], fill=(240, 230, 200))
    elif key == "seoul":
        # v6: Seoul moves to impeach its chief justice — a modern
        # courthouse (navy glass facade, pediment, steps) with a big
        # gavel striking in the foreground and a small Korean flag.
        # Original PIL vector code.
        d.rectangle([0, 0, w, h], fill=(215, 222, 232))
        # Korean flag on a pole, left — white field, red/blue taegeuk
        d.line([14, 24, 14, 56], fill=(60, 40, 20), width=2)
        d.rectangle([14, 24, 36, 38], fill="white", outline=INK, width=1)
        d.ellipse([20, 28, 30, 34], fill=(200, 40, 40))
        d.ellipse([20, 31, 30, 37], fill=(20, 60, 160))
        # courthouse: pediment + navy facade + white columns + steps
        d.polygon([(70, 34), (126, 20), (182, 34)], fill=(90, 100, 115))
        d.rectangle([70, 34, 182, 62], fill=(30, 50, 90))
        for cx0 in range(76, 176, 16):
            d.rectangle([cx0, 36, cx0 + 6, 60], fill=(220, 228, 240))
        d.rectangle([70, 62, 182, 66], fill=(200, 205, 215))
        d.rectangle([64, 66, 188, 70], fill=(180, 185, 195))
        # the gavel, foreground right: handle + head, striking the block
        d.line([138, 68, 168, 44], fill=(120, 80, 40), width=5)
        d.polygon([(160, 36), (180, 28), (186, 38), (166, 46)],
                  fill=(150, 100, 50))
        d.polygon([(156, 42), (176, 34), (182, 44), (162, 52)],
                  fill=(120, 80, 40))
        d.ellipse([140, 64, 162, 72], fill=(100, 65, 30))
    elif key == "cpi":
        # v5.1: per the user's new reference (5 ascending rainbow bars +
        # one thick dark curved arrow rising) — the v5 navy bars + red
        # zigzag are gone. Same verified CPI data (core 2.2%, headline
        # 2.3%). Light card background kept (not the reference's black).
        # Original PIL vector code.
        d.rectangle([0, 0, w, h], fill=(245, 240, 228))
        for gy in range(18, h, 12):
            d.line([0, gy, w, gy], fill=(210, 205, 190), width=1)
        for gx in range(0, w, 24):
            d.line([gx, 18, gx, h], fill=(228, 223, 208), width=1)
        # five rainbow bars, ascending left to right, baseline y68
        cols = ((60, 180, 80), (250, 200, 40), (240, 130, 30),
                (220, 50, 50), (40, 140, 220))
        for i, col in enumerate(cols):
            bx = 10 + i * 36
            top = 68 - (12 + i * 7)
            d.rectangle([bx, top, bx + 24, 68], fill=col)
            light = tuple(min(255, c + 60) for c in col)
            d.rectangle([bx, top, bx + 24, top + 2], fill=light)
        # v5.4: arrowhead pulled back for clearance — 17px from the
        # "2.3%" focal (was 9px), tail 6px above the coins, head top
        # 14px below the banner. Same smooth tapered style and colour.
        smooth_arrow(img, (8, 62), (44, 60), (90, 52), (134, 33),
                     (30, 30, 40))
        # red 2.3% focal, top-right, clear of the arrowhead (ends x148)
        d.text((192, 24), "2.3%", font=F_ART2, fill=RED, anchor="ra",
               stroke_width=1, stroke_fill="white")
        # gold coins along the bottom
        for cx in (14, 44, 74, 104, 134, 164):
            d.ellipse([cx, 72, cx + 12, 80], fill=GOLD,
                      outline=(180, 130, 20), width=1)
            d.ellipse([cx + 3, 74, cx + 9, 78], fill=(255, 220, 80))
    elif key == "cricket":
        # v5.6: Glenn Phillips 118 at the Basin Reserve — a full match
        # scene, not a bare pitch: packed crowd stands + floodlights
        # behind, green outfield, tan pitch, stumps with bails, and the
        # batsman BIG and mid-swing, bat connecting with the red ball
        # (motion trail flying off it), scoreboard with both lines.
        # The old v5 scene (small stick batsman, bare green, one-line
        # scoreboard) is gone. Original PIL vector code.
        d.rectangle([0, 0, w, h], fill=(60, 160, 90))
        # the stands, y20-34: dark stand band + two rows of crowd heads
        d.rectangle([0, 20, w, 34], fill=(45, 55, 70))
        crowd_cols = ((220, 180, 140), (180, 120, 80), (240, 200, 160),
                      (200, 60, 60), (60, 120, 200), (240, 240, 240),
                      (30, 30, 30), (250, 200, 40))
        for row, cy in ((0, 25), (1, 30)):
            for i, hx in enumerate(range(6, w - 4, 7)):
                col = crowd_cols[(i + row * 3) % len(crowd_cols)]
                d.ellipse([hx - 2, cy - 2, hx + 2, cy + 2], fill=col)
        d.rectangle([0, 34, w, 36], fill=(220, 220, 220))
        # floodlight poles at both edges, lamp heads + pale light cones
        for px0 in (6, 190):
            d.line([px0, 20, px0, 34], fill=(120, 125, 135), width=2)
            d.rectangle([px0 - 5, 20, px0 + 5, 26], fill=(90, 95, 105))
            for lx in (px0 - 3, px0 + 1):
                d.ellipse([lx - 1, 21, lx + 1, 23], fill="white")
        d.polygon([(4, 26), (14, 26), (30, 44), (0, 44)],
                  fill=(235, 235, 195))
        d.polygon([(182, 26), (192, 26), (196, 44), (166, 44)],
                  fill=(235, 235, 195))
        # mowing stripes across the outfield, below the stands
        for sy in range(36, h, 16):
            d.rectangle([0, sy, w, sy + 8], fill=(52, 148, 82))
        # the pitch: tan strip up the middle, crease lines in white
        d.rectangle([88, 38, 110, h], fill=(214, 186, 140))
        d.line([88, 42, 110, 42], fill="white", width=2)
        d.line([88, 74, 110, 74], fill="white", width=2)
        # stumps at the top of the pitch, three pale sticks + bails
        for sx in (94, 98, 102):
            d.rectangle([sx, 38, sx + 2, 48], fill=(240, 220, 140))
        d.line([94, 38, 104, 38], fill=(240, 220, 140), width=1)
        # the batsman, BIG and mid-swing: black NZ shirt, white pads,
        # front leg planted, bat swung high through the ball
        d.ellipse([120, 46, 130, 56], fill=(200, 140, 90))
        d.rectangle([120, 56, 131, 70], fill=(20, 20, 25))
        d.line([122, 70, 116, 79], fill="white", width=4)
        d.line([129, 70, 135, 79], fill="white", width=4)
        d.line([128, 58, 142, 48], fill=(200, 140, 90), width=3)
        d.line([142, 48, 156, 34], fill=(200, 170, 110), width=5)
        # the red ball AT the bat's tip (the moment of contact) + trail
        d.ellipse([155, 29, 163, 37], fill=(200, 40, 40),
                  outline="white", width=1)
        d.line([(166, 27), (172, 22)], fill="white", width=2)
        # fielders: small white dots on the outfield
        for fx, fy in ((28, 58), (58, 70), (170, 52)):
            d.ellipse([fx - 3, fy - 3, fx + 3, fy + 3], fill="white")
        # scoreboard, bottom-right: white box, two lines "NZ 368" +
        # "IND 720/9" (India's record total in NZ, declared Sunday).
        d.rectangle([136, 58, 194, 78], fill="white", outline=INK, width=1)
        d.text((165, 63), "NZ 368", font=F_LBL2_S, fill=INK, anchor="mm")
        d.text((165, 72), "IND 720/9", font=F_LBL2_S, fill=INK,
               anchor="mm")
    elif key == "bukele":
        # v5.6: Bukele registers for a third term — a full rally scene,
        # not a lone ballot box: the El Salvador flag fills the card, a
        # stylised candidate (flat-vector figure, no likeness) at a
        # podium with a microphone and one arm raised to the crowd,
        # supporters with small flags along the bottom, and the ballot
        # box "2027" with ballots at right. The old v5 scene (flag +
        # box only) is gone. Original PIL vector code.
        d.rectangle([0, 18, w, 38], fill=(0, 71, 171))
        d.rectangle([0, 38, w, 58], fill="white")
        d.rectangle([0, 58, w, h], fill=(0, 71, 171))
        # small coat-of-arms nod on the white band, left: green triangle
        # + gold sun
        d.polygon([(27, 42), (18, 54), (36, 54)], fill=(0, 120, 60))
        d.ellipse([24, 37, 30, 43], fill=GOLD)
        # supporters along the bottom, left: heads + two small flags
        for hx, col in ((10, (220, 180, 140)), (22, (180, 120, 80)),
                        (34, (240, 200, 160)), (46, (200, 140, 90)),
                        (58, (170, 110, 70))):
            d.ellipse([hx - 3, 71, hx + 3, 79], fill=col)
            d.ellipse([hx - 3, 71, hx + 3, 74], fill=(30, 25, 20))
        for fx, fy in ((46, 54), (58, 52)):
            d.line([fx, fy + 6, fx, 72], fill=(60, 40, 20), width=1)
            d.rectangle([fx, fy, fx + 12, fy + 3], fill=(0, 71, 171))
            d.rectangle([fx, fy + 3, fx + 12, fy + 6], fill="white")
        # one supporter + flag at the far right, past the ballot box
        d.ellipse([185, 71, 191, 79], fill=(220, 180, 140))
        d.ellipse([185, 71, 191, 74], fill=(30, 25, 20))
        d.line([188, 60, 188, 72], fill=(60, 40, 20), width=1)
        d.rectangle([188, 56, 196, 59], fill=(0, 71, 171))
        d.rectangle([188, 59, 196, 62], fill="white")
        # the candidate at the podium: dark suit, white shirt, red tie,
        # one arm raised waving to the crowd (stylised, no likeness)
        d.ellipse([83, 27, 99, 35], fill=(30, 25, 20))
        d.ellipse([84, 31, 98, 44], fill=(200, 150, 110))
        d.rectangle([74, 42, 108, 58], fill=(20, 30, 60))
        d.polygon([(88, 42), (96, 42), (91, 52)], fill="white")
        d.line([91, 44, 91, 54], fill=RED, width=2)
        d.line([104, 46, 118, 32], fill=(20, 30, 60), width=4)
        d.ellipse([115, 29, 121, 35], fill=(200, 150, 110))
        # microphone on the podium, in front of the candidate
        d.line([90, 58, 88, 46], fill=(60, 60, 60), width=2)
        d.ellipse([86, 43, 90, 47], fill=(40, 40, 40))
        # the podium: dark navy, white front panel + gold seal
        d.rectangle([68, 58, 112, 80], fill=(10, 20, 50))
        d.rectangle([74, 64, 106, 76], fill="white")
        d.ellipse([87, 67, 93, 73], fill=GOLD)
        # the ballot box, right: dark navy, slot, ballot half in, "2027"
        d.rectangle([140, 44, 180, 72], fill=(20, 40, 90),
                    outline="white", width=2)
        d.rectangle([150, 44, 170, 48], fill=(10, 20, 50))
        d.polygon([(152, 28), (166, 26), (168, 44), (154, 46)],
                  fill="white", outline=(120, 120, 120))
        d.line([156, 32, 164, 31], fill=RED, width=2)
        d.text((160, 58), "2027", font=F_ART2_S, fill="white", anchor="mm")
        d.ellipse([172, 62, 178, 68], fill=GOLD, outline="white", width=1)
    elif key == "poland":
        # v5: a Russian missile lands in Poland — a green field with a
        # smoking crater, debris, an airport control tower, and a Polish
        # white-over-red flag. Distinct from the Kyiv hero (night bridge
        # scene). The old "rikers" branch (cell block + CLOSED stamp) is
        # gone with the story. Original PIL vector code.
        d.rectangle([0, 0, w, h], fill=(200, 210, 225))
        # the field, lower half
        d.rectangle([0, 42, w, h], fill=(90, 160, 90))
        for fy in range(46, h, 12):
            d.line([0, fy, w, fy], fill=(80, 145, 80), width=1)
        # the crater: dark pit with a brown rim, left of centre
        d.ellipse([38, 50, 86, 68], fill=(90, 70, 50))
        d.ellipse([44, 53, 80, 65], fill=(40, 30, 22))
        # debris scattered around the crater
        for dx0, dy0, dw, dh in ((30, 48, 8, 3), (88, 56, 7, 3),
                                 (56, 70, 9, 3), (96, 46, 6, 3)):
            d.rectangle([dx0, dy0, dx0 + dw, dy0 + dh], fill=(40, 40, 40))
        # smoke column rising from the crater, drifting right
        for ex, ey, er, col in ((62, 44, 6, (150, 150, 150)),
                                 (70, 34, 7, (130, 130, 130)),
                                 (80, 26, 6, (160, 160, 160))):
            d.ellipse([ex - er, ey - er, ex + er, ey + er], fill=col)
        # Polish flag on a pole, left — white over red
        d.line([14, 26, 14, 60], fill=(60, 40, 20), width=2)
        d.rectangle([14, 26, 32, 33], fill="white")
        d.rectangle([14, 33, 32, 40], fill=(220, 40, 40))
        # airport control tower, right — grey shaft + glass cab
        d.rectangle([150, 34, 162, 76], fill=(120, 125, 135))
        d.rectangle([144, 24, 170, 34], fill=(90, 95, 105))
        d.rectangle([148, 27, 166, 31], fill=(180, 220, 240))
        d.ellipse([154, 20, 158, 24], fill=RED)
    elif key == "tonga":
        # v15: Tonga's El Nino drought — cracked earth, a hard sun and
        # a dry water tank beside a drooping palm. Original PIL vector
        # code.
        d.rectangle([0, 0, w, h], fill=(224, 196, 148))
        d.ellipse([118, 20, 146, 48], fill=(255, 140, 40),
                  outline=(220, 100, 20), width=2)
        d.rectangle([0, 52, w, h], fill=(190, 150, 95))
        for crack in ([(10, 52), (30, 62), (28, 72), (44, 78)],
                      [(60, 52), (70, 64), (88, 66), (96, 76)],
                      [(120, 52), (132, 62), (150, 64), (158, 74)],
                      [(170, 52), (176, 66), (188, 70), (192, 78)]):
            d.line(crack, fill=(110, 80, 50), width=2)
        d.rectangle([150, 48, 186, 74], fill=(140, 145, 155),
                    outline=(90, 95, 105), width=2)
        d.rectangle([156, 48, 180, 54], fill=(90, 95, 105))
        d.line([30, 52, 36, 22], fill=(120, 90, 50), width=4)
        for fx0, fy0, fx1, fy1 in ((36, 22, 14, 30), (36, 22, 20, 16),
                                   (36, 22, 52, 14), (36, 22, 58, 28),
                                   (36, 22, 44, 34)):
            d.line([fx0, fy0, fx1, fy1], fill=(40, 140, 70), width=3)
    elif key == "bepicolombo":
        # v17: BepiColombo at Mercury — starfield, the cratered planet on
        # its orbit, and the spacecraft. Original PIL vector code.
        d.rectangle([0, 0, w, h], fill=(12, 28, 58))
        for sx, sy in ((12, 12), (30, 26), (52, 8), (88, 16), (110, 30),
                       (140, 10), (168, 24), (186, 12), (24, 62), (120, 66),
                       (160, 58), (188, 66), (70, 70), (100, 6)):
            d.ellipse([sx, sy, sx + 2, sy + 2], fill="white")
        d.ellipse([34, 28, 106, 52], outline=(140, 180, 210), width=1)
        d.ellipse([54, 24, 86, 56], fill=(180, 180, 190),
                  outline=(140, 140, 150), width=1)
        d.ellipse([62, 32, 66, 36], fill=(140, 140, 150))
        d.ellipse([72, 44, 76, 48], fill=(140, 140, 150))
        d.ellipse([60, 46, 62, 48], fill=(140, 140, 150))
        d.rectangle([100, 36, 104, 40], fill="white")
        d.line([98, 38, 108, 38], fill=(140, 180, 210), width=1)
    elif key == "chinarates":
        # v17: China holds rates — two bars, 1-yr 3.0% and 5-yr 3.5%,
        # under a flat "held" line. Original PIL vector code.
        d.rectangle([0, 0, w, h], fill=(240, 238, 228))
        for gy in (16, 32, 48, 64):
            d.line([16, gy, w - 16, gy], fill=(210, 205, 190), width=1)
        d.line([16, 64, w - 16, 64], fill=INK, width=2)
        d.rectangle([48, 40, 78, 64], fill=(179, 34, 44))
        d.rectangle([118, 34, 148, 64], fill=(16, 62, 150))
        d.line([16, 28, w - 16, 28], fill=(30, 130, 80), width=2)
        for dx in range(20, w - 16, 12):
            d.line([dx, 28, dx + 6, 28], fill=(240, 238, 228), width=1)
        d.text((63, 24), "3.0%", font=F_ART2_S, fill=(179, 34, 44),
               anchor="ma")
        d.text((133, 18), "3.5%", font=F_ART2_S, fill=(16, 62, 150),
               anchor="ma")
        d.text((63, 68), "1-YR", font=F_ART2_S, fill=INK, anchor="ma")
        d.text((133, 68), "5-YR", font=F_ART2_S, fill=INK, anchor="ma")
    elif key == "cancerpill":
        # v17: the cancer pill — a big red/white capsule, small pills
        # beside it, on a pale clinical green. Original PIL vector code.
        d.rectangle([0, 0, w, h], fill=(225, 240, 230))
        for px0, py0 in ((150, 14), (164, 30), (140, 52), (172, 56)):
            d.ellipse([px0, py0, px0 + 14, py0 + 10], fill=(200, 220, 205),
                      outline=(150, 180, 160), width=1)
        d.ellipse([18, 52, 40, 66], fill="white", outline=(180, 180, 180),
                  width=1)
        d.line([98, 22, 62, 58], fill=(179, 34, 44), width=14)
        d.line([62, 58, 98, 22], fill="white", width=14)
        d.ellipse([58, 18, 102, 62], outline=(120, 120, 120), width=1)
        d.line([80, 40, 80, 40], fill="white")
    elif key == "shenzhen":
        # v1: the Shenzhen trilateral — three flags side by side: US
        # stars & stripes, China red with yellow stars, Russia
        # white-blue-red. Hero art (396x105); the "3 LEADERS" scrim
        # sits bottom-left over the US panel. Original PIL vector code.
        d.rectangle([0, 0, w, h], fill=(20, 40, 120))
        # US panel, left third: 7 stripes + blue canton with stars
        for si in range(7):
            if si % 2 == 0:
                d.rectangle([0, si * 15, 132, si * 15 + 15],
                            fill=(179, 34, 44))
            else:
                d.rectangle([0, si * 15, 132, si * 15 + 15],
                            fill="white")
        d.rectangle([0, 0, 58, 52], fill=(20, 40, 120))
        for sy in range(8, 50, 10):
            for sx in range(6, 54, 10):
                _star(d, sx, sy, 3, 1, fill="white")
        # China panel, middle third: red field, one big + four small stars
        d.rectangle([132, 0, 264, h], fill=(222, 41, 16))
        _star(d, 158, 26, 12, 5, fill=(255, 222, 0))
        for sx, sy in ((188, 12), (200, 22), (200, 38), (188, 48)):
            _star(d, sx, sy, 5, 2, fill=(255, 222, 0))
        # Russia panel, right third: white over blue over red
        d.rectangle([264, 0, w, 35], fill="white")
        d.rectangle([264, 35, w, 70], fill=(0, 57, 166))
        d.rectangle([264, 70, w, h], fill=(213, 0, 50))
        d.line([132, 0, 132, h], fill=GOLD, width=2)
        d.line([264, 0, 264, h], fill=GOLD, width=2)
    elif key == "icj":
        # v1: the world court — navy chamber, white columns, gold
        # scales of justice in the centre. Original PIL vector code.
        d.rectangle([0, 0, w, h], fill=(12, 28, 58))
        for cx0 in (8, 176):
            d.rectangle([cx0, 22, cx0 + 12, 74], fill=(220, 228, 240))
            d.rectangle([cx0 - 3, 18, cx0 + 15, 22], fill=(220, 228, 240))
            d.rectangle([cx0 - 3, 74, cx0 + 15, 78], fill=(220, 228, 240))
        # scales: post, beam, two hanging pans, base
        d.rectangle([96, 26, 100, 66], fill=GOLD)
        d.line([58, 30, 138, 30], fill=GOLD, width=3)
        d.line([58, 30, 58, 46], fill=GOLD, width=2)
        d.line([138, 30, 138, 46], fill=GOLD, width=2)
        d.polygon([(48, 46), (68, 46), (58, 58)], fill=GOLD)
        d.polygon([(128, 46), (148, 46), (138, 58)], fill=GOLD)
        d.ellipse([92, 20, 104, 30], fill=GOLD)
        d.rectangle([84, 66, 112, 72], fill=GOLD)
        d.rectangle([78, 72, 118, 76], fill=GOLD)
    elif key == "riyadh":
        # v3: night skyline + DOTTED intercept arcs rising to explosion
        # stars (the top-1/4/7 composition). The v2 straight white
        # trails with small bursts read as sticks at hero size; the
        # dotted arcs + big starbursts read at full size. h-relative so
        # the 105px hero render stretches cleanly to 160px.
        # Original PIL vector code.
        d.rectangle([0, 0, w, h], fill=(14, 24, 52))
        gy = int(h * 0.76)
        for sx, sy in ((12, 8), (40, 14), (80, 6), (120, 10), (160, 8),
                       (188, 14), (60, 20), (140, 18), (220, 6), (260, 12),
                       (30, 30), (100, 28), (180, 30), (240, 26)):
            d.ellipse([sx, sy, sx + 2, sy + 2], fill="white")
        # skyline: low blocks with lit windows across the back, then the
        # tall Kingdom tower with its arch, centre
        _skyline(d, w, 52, gy, (38, 58, 96), 7)
        tx0, tx1 = int(w * 0.44), int(w * 0.54)
        d.rectangle([tx0, int(h * 0.14), tx1, gy], fill=(38, 58, 96))
        d.polygon([(tx0, int(h * 0.14)), ((tx0 + tx1) // 2, int(h * 0.06)),
                   (tx1, int(h * 0.14))], fill=(38, 58, 96))
        d.ellipse([(tx0 + tx1) // 2 - 5, int(h * 0.10),
                   (tx0 + tx1) // 2 + 5, int(h * 0.10) + 10],
                  fill=(14, 24, 52))
        # five dotted interceptor arcs, ground -> explosion star. Heads
        # are routed clear of the Kingdom tower (x129-158 at this width).
        for (x0, xc, x1, y1) in ((28, 20, 44, 26), (78, 70, 98, 18),
                                 (112, 106, 124, 26), (196, 202, 228, 16),
                                 (252, 260, 276, 34)):
            for ti in range(41):
                t = ti / 40
                qx = (1 - t) ** 2 * x0 + 2 * (1 - t) * t * xc + t ** 2 * x1
                qy = (1 - t) ** 2 * gy + 2 * (1 - t) * t * 30 + t ** 2 * y1
                if ti % 3 == 0:
                    d.ellipse([qx - 2, qy - 2, qx + 2, qy + 2], fill="white")
            _star(d, x1, y1, 11, 4, fill=(255, 200, 60))
            _star(d, x1, y1, 6, 2, fill=(255, 140, 40))
            d.ellipse([x1 - 3, y1 - 3, x1 + 3, y1 + 3], fill="white")
    elif key == "fbi":
        # v1: the breach — dark server room, two racks with status
        # lights, a red lightning bolt cutting across. Original PIL
        # vector code.
        d.rectangle([0, 0, w, h], fill=(10, 20, 40))
        for rx0 in (24, 120):
            d.rectangle([rx0, 22, rx0 + 52, 74], fill=(30, 45, 70),
                        outline=(90, 110, 150), width=1)
            for ry in range(28, 72, 10):
                d.rectangle([rx0 + 6, ry, rx0 + 34, ry + 5],
                            fill=(20, 30, 50))
                d.ellipse([rx0 + 40, ry, rx0 + 45, ry + 5],
                          fill=(60, 200, 90) if ry % 20 else (255, 180, 40))
        # the bolt: red, jagged, across the middle
        d.polygon([(92, 18), (104, 18), (94, 40), (108, 40), (82, 70),
                   (90, 46), (78, 46)], fill=(220, 30, 40))
        d.ellipse([170, 20, 182, 32], fill=RED)
        d.text((176, 26), "!", font=F_ART2, fill="white", anchor="mm")
    elif key == "denmark":
        # v1: Denmark expels the Russian attaché — the Danish flag
        # fills the card, a white plane climbs out top-right.
        # Original PIL vector code.
        d.rectangle([0, 0, w, h], fill=(200, 16, 46))
        d.rectangle([56, 0, 72, h], fill="white")
        d.rectangle([0, 32, w, 48], fill="white")
        # plane: fuselage + wings + tail, climbing right
        d.polygon([(128, 26), (168, 18), (172, 22), (140, 32), (132, 32)],
                  fill="white")
        d.polygon([(146, 20), (156, 12), (160, 16), (152, 22)],
                  fill="white")
        d.polygon([(164, 18), (172, 12), (174, 16), (168, 20)],
                  fill="white")
        # a small suitcase, bottom-left, packed and leaving
        d.rectangle([18, 58, 44, 76], fill=(120, 80, 40),
                    outline=(60, 40, 20), width=1)
        d.line([18, 67, 44, 67], fill=(60, 40, 20), width=1)
        d.rectangle([26, 54, 36, 58], fill=(60, 40, 20))
    elif key == "peru":
        # v1: the Peruvian Andes quake — pale sky, two leaning
        # buildings, cracked ground, a red seismograph zigzag.
        # v3: the seismograph is ENLARGED across the full top of the
        # panel (the top-1 composition: one big red line reads instantly
        # at hero size; the v2 zigzag stopped at x188 and sat small).
        # Original PIL vector code.
        d.rectangle([0, 0, w, h], fill=(205, 214, 226))
        # seismograph zigzag across the whole top, peaks y8 / troughs y28
        zig = []
        _xx, _up = 8, True
        while _xx <= w - 8:
            zig.append((_xx, 8 if _up else 28))
            _up = not _up
            _xx += 16
        d.line(zig, fill=RED, width=3)
        # leaning buildings: polygons, tilted off vertical
        d.polygon([(30, 34), (58, 30), (62, 62), (34, 62)],
                  fill=(150, 140, 120))
        d.polygon([(120, 30), (148, 34), (146, 62), (118, 62)],
                  fill=(120, 110, 95))
        for wy in (38, 46, 54):
            d.rectangle([38, wy, 44, wy + 4], fill=(60, 60, 70))
            d.rectangle([126, wy, 132, wy + 4], fill=(60, 60, 70))
        # cracked ground
        d.rectangle([0, 62, w, h], fill=(190, 150, 95))
        d.line([(10, 62), (30, 70), (28, 78), (46, 80)], fill=(110, 80, 50),
               width=2)
        d.line([(90, 62), (100, 72), (118, 74), (126, 80)],
               fill=(110, 80, 50), width=2)
        d.line([(160, 62), (170, 70), (188, 72)], fill=(110, 80, 50),
               width=2)
    elif key == "anthropic":
        # v1: the $2T debut — light board, grid, a steep green chart
        # line rocketing to the top-right, gold coins along the bottom.
        # Original PIL vector code.
        d.rectangle([0, 0, w, h], fill=(245, 240, 228))
        for gy in range(18, h, 12):
            d.line([0, gy, w, gy], fill=(210, 205, 190), width=1)
        for gx in range(0, w, 24):
            d.line([gx, 18, gx, h], fill=(228, 223, 208), width=1)
        # the chart: flat, then a near-vertical rocket leg
        d.line([(10, 66), (70, 60), (120, 52), (150, 26), (180, 12)],
               fill=(30, 130, 80), width=4)
        d.polygon([(180, 12), (168, 14), (178, 24)], fill=(30, 130, 80))
        d.text((186, 16), "$2T", font=F_ART2, fill=(30, 130, 80),
               anchor="ra")
        for cx in (14, 44, 74, 104, 134, 164):
            d.ellipse([cx, 72, cx + 12, 80], fill=GOLD,
                      outline=(180, 130, 20), width=1)
            d.ellipse([cx + 3, 74, cx + 9, 78], fill=(255, 220, 80))
    elif key == "robots":
        # v1: killer-robot rules — UN-blue, a grey robot at left, a
        # white accord document with a green check at right.
        # Original PIL vector code.
        d.rectangle([0, 0, w, h], fill=(0, 91, 172))
        # robot: antenna, head, body, arms
        d.line([52, 24, 52, 32], fill=(200, 200, 210), width=2)
        d.ellipse([49, 20, 55, 26], fill=RED)
        d.rectangle([36, 32, 68, 50], fill=(200, 200, 210),
                    outline=(120, 125, 135), width=1)
        d.ellipse([42, 38, 48, 44], fill=(20, 60, 160))
        d.ellipse([56, 38, 62, 44], fill=(20, 60, 160))
        d.line([44, 48, 60, 48], fill=(20, 60, 160), width=2)
        d.rectangle([40, 52, 64, 74], fill=(160, 165, 175),
                    outline=(120, 125, 135), width=1)
        d.line([36, 54, 28, 66], fill=(160, 165, 175), width=3)
        d.line([68, 54, 76, 66], fill=(160, 165, 175), width=3)
        # the accord: white page, lines, green check
        d.rectangle([120, 22, 176, 70], fill="white", outline=INK, width=1)
        for ly in (30, 38, 46):
            d.line([128, ly, 168, ly], fill=(150, 150, 150), width=2)
        d.line([130, 62, 142, 72], fill=(30, 130, 80), width=3)
        d.line([142, 72, 162, 52], fill=(30, 130, 80), width=3)
    elif key == "mexico":
        # v1: the cartel-boss capture — desert, cactus, gold badge,
        # steel handcuffs in the centre. Original PIL vector code.
        d.rectangle([0, 0, w, h], fill=(238, 222, 178))
        d.ellipse([168, 20, 186, 38], fill=(255, 200, 60),
                  outline=(230, 170, 40), width=2)
        d.rectangle([0, 56, w, h], fill=(190, 150, 95))
        # cactus, left
        d.rectangle([18, 30, 26, 56], fill=(40, 140, 70))
        d.rectangle([10, 40, 18, 46], fill=(40, 140, 70))
        d.rectangle([10, 40, 14, 52], fill=(40, 140, 70))
        d.rectangle([26, 36, 34, 42], fill=(40, 140, 70))
        d.rectangle([30, 36, 34, 48], fill=(40, 140, 70))
        # handcuffs: two steel rings + chain
        d.ellipse([70, 44, 96, 68], outline=(90, 95, 105), width=4)
        d.ellipse([108, 44, 134, 68], outline=(90, 95, 105), width=4)
        d.line([96, 56, 108, 56], fill=(90, 95, 105), width=3)
        d.ellipse([98, 52, 106, 60], outline=(90, 95, 105), width=2)
        # gold badge, right
        _star(d, 162, 52, 12, 5, fill=GOLD)
        d.ellipse([158, 48, 166, 56], fill=(0, 71, 171))
    elif key == "greenland":
        # v1: Greenland hosts two new US bases — blue sea, the big
        # white island, two red base stars, small icebergs.
        # Original PIL vector code.
        d.rectangle([0, 0, w, h], fill=(30, 90, 160))
        d.line([0, 70, w, 70], fill=(140, 180, 210), width=1)
        d.line([0, 76, w, 76], fill=(100, 150, 190), width=1)
        # the island: a big white polygon, north-east leaning
        d.polygon([(70, 22), (120, 18), (160, 30), (168, 52), (140, 64),
                   (96, 60), (72, 44)], fill="white")
        d.polygon([(96, 26), (120, 24), (132, 36), (110, 44), (92, 38)],
                  fill=(220, 230, 240))
        # two base stars on the island
        _star(d, 108, 38, 7, 3, fill=RED)
        _star(d, 140, 50, 7, 3, fill=RED)
        # icebergs in the sea
        d.polygon([(20, 70), (30, 62), (40, 70)], fill="white")
        d.polygon([(170, 72), (178, 64), (186, 72)], fill="white")
    elif key == "spain":
        # v1: Spain votes 29 Nov — red-yellow-red bands, a dark ballot
        # box with a ballot half in, gold seal. Original PIL vector code.
        d.rectangle([0, 0, w, 22], fill=(200, 40, 40))
        d.rectangle([0, 22, w, 58], fill=(255, 210, 31))
        d.rectangle([0, 58, w, h], fill=(200, 40, 40))
        # ballot box, centre
        d.rectangle([76, 44, 120, 74], fill=(20, 40, 90),
                    outline="white", width=2)
        d.rectangle([86, 44, 110, 48], fill=(10, 20, 50))
        d.polygon([(88, 28), (106, 26), (108, 44), (90, 46)],
                  fill="white", outline=(120, 120, 120))
        d.line([92, 32, 102, 31], fill=RED, width=2)
        d.ellipse([108, 58, 114, 64], fill=GOLD, outline="white", width=1)
        # two small flags flanking the box
        for fx in (40, 146):
            d.line([fx, 48, fx, 74], fill=(60, 40, 20), width=2)
            d.rectangle([fx, 48, fx + 14, 52], fill=(200, 40, 40))
            d.rectangle([fx, 52, fx + 14, 56], fill=(255, 210, 31))
            d.rectangle([fx, 56, fx + 14, 60], fill=(200, 40, 40))
    elif key == "timor":
        # v1: the Timor-Leste quake — dark sea, a green island, a red
        # seismograph zigzag, calm wave lines (no tsunami).
        # Original PIL vector code.
        d.rectangle([0, 0, w, h], fill=(12, 60, 110))
        d.rectangle([0, 0, w, 22], fill=(220, 230, 240))
        d.ellipse([160, 6, 178, 24], fill=(240, 200, 90))
        d.line([0, 22, w, 22], fill=(140, 180, 210), width=1)
        # the island, left
        d.polygon([(14, 52), (40, 40), (70, 46), (78, 58), (52, 64),
                   (24, 62)], fill=(60, 140, 80))
        d.polygon([(30, 48), (44, 44), (54, 50), (38, 54)],
                  fill=(40, 110, 60))
        # seismograph zigzag across the sea
        zig = [(84, 40), (96, 30), (108, 48), (120, 28), (132, 46),
               (144, 32), (156, 44), (168, 34), (180, 42)]
        d.line(zig, fill=RED, width=2)
        # calm wave lines, bottom
        for wy in (68, 74):
            d.line([10, wy, 90, wy], fill=(140, 180, 210), width=1)
            d.line([110, wy, 186, wy], fill=(140, 180, 210), width=1)
    elif key == "davao":
        # v2: Air Niugini 767 emergency landing at Davao — dawn haze,
        # runway, white 767 with an orange flame on the right engine,
        # yellow evacuation slides, tiny figures walking clear.
        # Original PIL vector code.
        d.rectangle([0, 0, w, h], fill=(232, 222, 190))
        d.ellipse([w - 34, 8, w - 16, 26], fill=(255, 200, 90),
                  outline=(230, 170, 40), width=2)
        d.rectangle([0, 62, w, h], fill=(70, 70, 80))
        for dx in range(8, w - 8, 24):
            d.rectangle([dx, 70, dx + 12, 73], fill="white")
        # fuselage + tail fin + wing
        d.ellipse([18, 38, 172, 56], fill="white", outline=(180, 180, 190))
        d.polygon([(150, 40), (166, 20), (174, 20), (168, 40)],
                  fill="white", outline=(180, 180, 190))
        d.polygon([(86, 52), (110, 62), (118, 62), (100, 52)],
                  fill=(200, 200, 210))
        # engines under the wing; right one burning
        d.ellipse([64, 54, 78, 60], fill=(150, 150, 160))
        d.ellipse([124, 54, 138, 60], fill=(150, 150, 160))
        d.polygon([(131, 60), (126, 70), (136, 70)], fill=(255, 140, 40))
        d.polygon([(131, 62), (128, 68), (134, 68)], fill=RED)
        # evacuation slides from the doors + figures on the runway
        for sx in (48, 108):
            d.polygon([(sx, 52), (sx + 12, 52), (sx + 20, 62), (sx + 8, 62)],
                      fill=(255, 210, 31))
            d.ellipse([sx + 16, 64, sx + 20, 68], fill=(30, 30, 30))
        d.ellipse([150, 64, 154, 68], fill=(30, 30, 30))
    elif key == "bitcoin":
        # v2: Bitcoin below $59,000 — dark board, big gold coin with
        # a B, a red arrow curving down. Original PIL vector code.
        d.rectangle([0, 0, w, h], fill=(12, 28, 58))
        for gy in range(20, h, 12):
            d.line([0, gy, w, gy], fill=(24, 44, 80), width=1)
        d.ellipse([44, 22, 96, 74], fill=(240, 180, 40),
                  outline=(180, 120, 20), width=2)
        d.ellipse([50, 28, 90, 68], outline=(255, 220, 100), width=1)
        d.text((70, 48), "B", font=F_ART, fill=(120, 80, 0), anchor="mm")
        smooth_arrow(img, (118, 24), (148, 26), (168, 44), (186, 64),
                     (220, 40, 50))
    elif key == "rahul":
        # v2: KL Rahul's 124 not out, Wellington — green outfield,
        # pale pitch, stumps, batsman mid-drive, red ball.
        # Original PIL vector code.
        d.rectangle([0, 0, w, h], fill=(40, 140, 70))
        d.rectangle([0, 44, w, 66], fill=(210, 190, 140))
        d.line([0, 44, w, 44], fill="white", width=1)
        d.line([0, 66, w, 66], fill="white", width=1)
        # stumps + bails, right end of the pitch
        for sx in (162, 168, 174):
            d.line([sx, 32, sx, 44], fill=(255, 220, 60), width=2)
        d.line([162, 31, 176, 31], fill=(255, 220, 60), width=2)
        # batsman: helmet, white pads, brown bat mid-drive
        d.ellipse([122, 24, 134, 36], fill=(30, 30, 40))
        d.rectangle([120, 38, 128, 58], fill="white")
        d.rectangle([130, 38, 138, 58], fill="white")
        d.polygon([(132, 40), (150, 60), (146, 64), (128, 46)],
                  fill=(150, 100, 50))
        # red ball, left of the pitch
        d.ellipse([56, 50, 64, 58], fill=RED, outline=(120, 0, 0))
    elif key == "russell":
        # v2: Russell fastest in final Las Vegas practice — night
        # street circuit, neon track ribbon, silver F1 car.
        # Original PIL vector code.
        d.rectangle([0, 0, w, h], fill=(16, 16, 28))
        for sx, sy in ((14, 10), (60, 8), (110, 12), (160, 8), (188, 12)):
            d.ellipse([sx, sy, sx + 2, sy + 2], fill="white")
        # neon track: magenta band + cyan edge, curving across
        d.line([(8, 72), (60, 44), (120, 48), (188, 72)],
               fill=(255, 60, 180), width=8)
        d.line([(8, 68), (60, 40), (120, 44), (188, 68)],
               fill=(60, 220, 255), width=2)
        # silver car: rear wing, wedge body, front wing, two wheels
        d.rectangle([84, 44, 88, 58], fill=(200, 200, 210))
        d.polygon([(88, 50), (128, 50), (134, 58), (88, 58)],
                  fill=(210, 210, 220))
        d.rectangle([132, 54, 140, 58], fill=(200, 200, 210))
        for wx in (100, 122):
            d.ellipse([wx - 6, 56, wx + 6, 68], fill=(20, 20, 20))
            d.ellipse([wx - 2, 60, wx + 2, 64], fill=(160, 160, 170))
    elif key == "hormuz":
        # v2: Iran says it shot down a US MQ-9 over the Strait of
        # Hormuz — sky, sea, grey drone with long straight wings,
        # orange burst where the missile hit, a ship below.
        # Original PIL vector code.
        d.rectangle([0, 0, w, 44], fill=(180, 210, 235))
        d.rectangle([0, 44, w, h], fill=(20, 80, 140))
        d.line([0, 44, w, 44], fill=(140, 180, 210), width=1)
        # MQ-9: fuselage, long wings, V-tail, pusher prop
        d.ellipse([70, 28, 132, 40], fill=(120, 125, 135))
        d.rectangle([36, 32, 166, 37], fill=(100, 105, 115))
        d.polygon([(70, 34), (58, 26), (62, 28), (70, 38)],
                  fill=(100, 105, 115))
        d.polygon([(70, 36), (58, 44), (62, 42), (70, 38)],
                  fill=(100, 105, 115))
        d.line([132, 28, 132, 42], fill=(80, 85, 95), width=2)
        # burst at the wingtip
        d.ellipse([150, 20, 164, 34], fill=(255, 140, 40))
        d.ellipse([153, 23, 161, 31], fill=RED)
        d.line([148, 27, 166, 27], fill=(255, 200, 90), width=2)
        d.line([157, 18, 157, 36], fill=(255, 200, 90), width=2)
        # ship + wake, lower right
        d.polygon([(118, 62), (168, 62), (160, 70), (126, 70)],
                  fill=(40, 40, 50))
        d.rectangle([138, 54, 148, 62], fill=(40, 40, 50))
        d.line([110, 72, 176, 72], fill="white", width=1)
    elif key == "iran":
        # v2: Iran's uranium stays in Iran — dark teal, a big yellow
        # radiation trefoil (disc, three dark gaps, dark centre).
        # Original PIL vector code.
        d.rectangle([0, 0, w, h], fill=(10, 90, 90))
        cx, cy, r = 98, 48, 30
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(240, 200, 0))
        for a0 in (75, 195, 315):
            d.pieslice([cx - r, cy - r, cx + r, cy + r], start=a0,
                       end=a0 + 30, fill=(10, 90, 90))
        d.ellipse([cx - 9, cy - 9, cx + 9, cy + 9], fill=(10, 90, 90))
        d.ellipse([cx - 4, cy - 4, cx + 4, cy + 4], fill=(240, 200, 0))
    elif key == "trumptax":
        # v2: Trump vows a tax on data centres abroad — navy, a grey
        # data-centre block with lit server racks, a big gold $.
        # Original PIL vector code.
        d.rectangle([0, 0, w, h], fill=(16, 40, 90))
        d.rectangle([30, 30, 170, 34], fill=(90, 100, 115))
        d.rectangle([30, 34, 170, 74], fill=(120, 130, 145))
        for rx in (40, 76, 112, 146):
            for ry in (40, 50, 60):
                d.rectangle([rx, ry, rx + 18, ry + 7], fill=(30, 40, 55))
                d.ellipse([rx + 13, ry + 2, rx + 16, ry + 5],
                          fill=(60, 200, 90))
        d.rectangle([88, 62, 108, 74], fill=(30, 40, 55))
        d.text((158, 16), "$", font=F_ART, fill=(240, 200, 40))
    elif key == "chinajapan":
        # v2: China tells Japan to "correct" Taiwan words — the two
        # flags split down the middle: red with yellow stars, white
        # with the red disc, gold seam between them.
        # Original PIL vector code.
        half = w // 2
        d.rectangle([0, 0, half, h], fill=(200, 16, 46))
        d.rectangle([half, 0, w, h], fill="white")
        d.line([half, 0, half, h], fill=(240, 200, 40), width=2)
        _star(d, half // 2, 28, 9, 4, fill=(255, 220, 60))
        for sx, sy in ((half // 2 + 22, 16), (half // 2 + 28, 28),
                       (half // 2 + 22, 40), (half // 2 + 10, 44)):
            _star(d, sx, sy, 4, 2, fill=(255, 220, 60))
        d.ellipse([half + 33, 32, half + 65, 64], fill=RED)
    elif key == "canberra":
        # v2: Australia and China agree AI talks — blue sky, Southern
        # Cross stars, white Parliament House with its flagpole.
        # Original PIL vector code.
        d.rectangle([0, 0, w, 56], fill=(90, 160, 220))
        d.rectangle([0, 56, w, h], fill=(60, 140, 80))
        for sx, sy in ((20, 14), (42, 24), (168, 12), (186, 26)):
            _star(d, sx, sy, 4, 2, fill="white")
        d.polygon([(56, 44), (98, 26), (140, 44)], fill="white")
        d.rectangle([60, 44, 136, 74], fill="white")
        for cx in (70, 88, 106, 124):
            d.rectangle([cx, 52, cx + 6, 74], fill=(90, 160, 220))
        d.line([98, 26, 98, 12], fill=(60, 60, 60), width=2)
        d.rectangle([98, 12, 112, 20], fill=(16, 62, 150))
        _star(d, 105, 16, 3, 1, fill="white")
    elif key == "kryvyi":
        # v2: double-tap strike on Kryvyi Rih — smoke-grey sky, two
        # damaged apartment blocks with a broken roofline, fire glow
        # at the base, a red-cross badge for the killed paramedic.
        # Original PIL vector code.
        d.rectangle([0, 0, w, h], fill=(60, 60, 70))
        for ex, ey, er in ((60, 16, 12), (120, 12, 14), (160, 18, 10)):
            d.ellipse([ex - er, ey - er, ex + er, ey + er],
                      fill=(90, 90, 100))
        d.polygon([(40, 74), (44, 30), (60, 26), (66, 34), (80, 30),
                   (84, 74)], fill=(140, 140, 150))
        d.polygon([(110, 74), (114, 44), (130, 40), (134, 74)],
                  fill=(120, 120, 130))
        for wx, wy in ((50, 40), (64, 48), (70, 58), (118, 52), (124, 62)):
            d.rectangle([wx, wy, wx + 6, wy + 5], fill=(40, 40, 50))
        d.rectangle([52, 40, 58, 45], fill=(255, 140, 40))
        d.ellipse([56, 68, 92, 78], fill=(255, 140, 40))
        d.ellipse([64, 71, 84, 78], fill=(255, 210, 31))
        d.ellipse([152, 16, 172, 36], fill="white")
        d.rectangle([160, 20, 164, 32], fill=RED)
        d.rectangle([154, 24, 170, 28], fill=RED)
    elif key == "bahrain":
        # v1 20261122: Iran's radar claim vs Bahrain's denial — an
        # INFORMATIVE GULF MAP, our own composition: Iran's coast
        # along the top, the Arabian coast along the bottom rising to
        # the Musandam tip (Khasab), Bahrain island with two red base
        # bursts, the Strait of Hormuz labelled in the channel, a US
        # 5th Fleet destroyer in the open sea, dashed missile arcs in
        # from Iran. The v7 tanker pair (Saturday's UKMTO hits,
        # 11nm N / 17nm E) is GONE — today's story is the radar claim,
        # not tankers. Drawn at 105px tall and stretched to 132px
        # (1.26x), so verticals are drawn slightly short. The
        # bottom-left stays clear for the "2 RADARS? / CLAIM VS
        # DENIAL" scrim. Original PIL vector code.
        d.rectangle([0, 0, w, h], fill=(14, 48, 96))
        # Iran coast: tan band along the top, wavy southern edge
        d.polygon([(0, 0), (w, 0), (w, 14), (340, 18), (280, 12),
                   (200, 18), (120, 12), (60, 16), (0, 20)],
                  fill=(214, 196, 150))
        d.text((14, 4), "IRAN", font=F_ART2_S, fill=INK)
        # Arabian coast: tan band along the bottom, rising at the
        # right into the Musandam tip (Khasab) at (345, 58)
        d.polygon([(0, h), (0, 82), (70, 74), (140, 82), (210, 76),
                   (280, 84), (320, 76), (345, 58), (365, 66),
                   (w, 72), (w, h)], fill=(214, 196, 150))
        d.text((w - 8, 90), "SAUDI ARABIA", font=F_ART2_S, fill=INK,
               anchor="ra")
        # Bahrain island: small tan shape in the sea, centre-left
        d.ellipse([120, 30, 152, 52], fill=(214, 196, 150))
        # Qatar bump, right of Bahrain
        d.ellipse([176, 44, 196, 62], fill=(196, 176, 128))
        # dashed missile arcs in from Iran to the island. Arc 1
        # starts at y22 with a 12px hump (not y18/14): at y18 its
        # dots nicked the bottom of the IRAN label.
        for (ax0, ay0, ax1, ay1, hump) in ((0, 22, 128, 38, 12),
                                           (0, 48, 136, 44, 14)):
            for ti in range(21):
                t = ti / 20
                qx = ax0 + (ax1 - ax0) * t
                qy = ay0 + (ay1 - ay0) * t - hump * math.sin(math.pi * t)
                if ti % 2 == 0:
                    d.ellipse([qx - 2, qy - 2, qx + 2, qy + 2], fill="white")
        # two base bursts on the island
        for bx, by in ((128, 36), (144, 46)):
            _star(d, bx, by, 10, 4, fill=(255, 200, 60))
            _star(d, bx, by, 5, 2, fill=(255, 140, 40))
            d.ellipse([bx - 3, by - 3, bx + 3, by + 3], fill="white")
        # labels in the open sea (white, dark outline so they read).
        # BAHRAIN sits at y56, not 60: the art_text scrim starts at
        # y66, and at y60 the label's ink would touch its top edge.
        # NOTE: this branch now runs as a 294px RAIL (hero 3), not
        # the 396px lead it was written for in v7 — the HORMUZ label
        # (x360) and the KHASAB label (x345) fell off-canvas and are
        # dropped; THE GULF + BAHRAIN + SAUDI ARABIA carry the map.
        for lx, ly, txt, anch in (
                (136, 56, "BAHRAIN", "ma"),
                (208, 28, "THE GULF", "ma")):
            d.text((lx, ly), txt, font=F_ART2_S, fill="white",
                   anchor=anch, stroke_width=1, stroke_fill=(0, 0, 0))
        # a US 5th Fleet destroyer in the open sea, right of the
        # island — grey hull, island superstructure, wake. Its label
        # sits below the hull. Shifted 10px left vs v7: at 294px wide
        # the label's right edge sat on the canvas edge.
        d.polygon([(228, 34), (276, 34), (268, 42), (236, 42)],
                  fill=(120, 125, 135))
        d.rectangle([242, 26, 254, 34], fill=(120, 125, 135))
        d.line([248, 26, 248, 20], fill=(120, 125, 135), width=2)
        d.line([224, 44, 280, 44], fill="white", width=1)
        d.text((252, 50), "5TH FLEET", font=F_ART2_S, fill="white",
               anchor="ma", stroke_width=1, stroke_fill=(0, 0, 0))
    elif key == "cop31cal":
        # v5: COP31 overtime — the summit calendar, our own
        # composition: pale green board, 13 day boxes (9–21) in a row
        # with 21 in red, a red "+1 DAY" tag top-right, a small red
        # thermometer at right, approval line bottom-right. Drawn at
        # 105px tall and stretched to 132px (1.26x), so boxes are
        # drawn 20px tall to render ~25px. Original PIL vector code.
        d.rectangle([0, 0, w, h], fill=(214, 232, 214))
        d.text((12, 8), "NOV 9–20 SCHEDULED", font=F_ART2_S, fill=(60, 60, 60))
        # day boxes: 13 across, 19px wide, 2px gaps, drawn 20 tall
        for i, day in enumerate(range(9, 22)):
            bx = 12 + i * 21
            is_last = day == 21
            d.rectangle([bx, 34, bx + 19, 54],
                        fill=RED if is_last else "white",
                        outline=(60, 60, 60), width=1)
            d.text((bx + 9.5, 44), str(day), font=F_ART2_S,
                   fill="white" if is_last else INK, anchor="mm")
        # red +1 DAY tag, top-right
        d.rectangle([w - 64, 6, w - 8, 24], fill=RED)
        d.text((w - 36, 15), "+1 DAY", font=F_ART2_S, fill="white", anchor="mm")
        # approval line, bottom-right (clear of the scrim bottom-left)
        d.text((w - 40, 88), "APPROVAL SUN 06:00 GMT", font=F_ART2_S,
               fill=INK, anchor="ra")
        # thermometer, bottom-right
        d.rectangle([w - 30, 62, w - 22, 92], fill="white", outline=INK)
        d.rectangle([w - 28, 74, w - 24, 92], fill=RED)
        d.ellipse([w - 34, 88, w - 18, 100], fill=RED, outline=INK)
        d.text((w - 38, 70), "+1.5°C", font=F_ART2_S, fill=INK, anchor="ra")
    elif key == "finland":
        # v5: Sparta II hit by drones in the Gulf of Finland — grey
        # sea, a dark cargo ship with a container stack, two small
        # drones above, orange fire on the deck. Art is 196x80 with
        # the solid banner over y0-18; the scene sits below it.
        # Original PIL vector code.
        d.rectangle([0, 0, w, h], fill=(30, 90, 140))
        d.line([0, 56, w, 56], fill=(140, 180, 210), width=1)
        # the ship: dark hull + white superstructure + containers
        d.polygon([(28, 56), (168, 56), (158, 68), (38, 68)],
                  fill=(30, 30, 40))
        d.rectangle([128, 40, 152, 56], fill="white")
        for cx, col in ((48, (200, 60, 40)), (72, (40, 140, 90)),
                        (96, (230, 180, 40))):
            d.rectangle([cx, 44, cx + 20, 56], fill=col)
        # fire on the deck, mid-ship
        d.ellipse([84, 34, 100, 48], fill=(255, 140, 40))
        d.ellipse([88, 38, 96, 48], fill=(255, 210, 31))
        # two drones above the ship
        for dx, dy in ((60, 26), (140, 24)):
            d.ellipse([dx - 5, dy - 3, dx + 5, dy + 3], fill=(90, 95, 105))
            d.line([dx - 8, dy - 5, dx + 8, dy - 5], fill=(200, 200, 210), width=2)
            d.line([dx, dy + 3, dx, dy + 8], fill=(200, 200, 210), width=1)
        # wake
        d.line([20, 72, 176, 72], fill="white", width=1)
    elif key == "drones":
        # v1 20261122: hero 1 — Russia's 186-drone night attack on
        # Ukraine. Night sky, a city skyline with lit windows, drone
        # silhouettes crossing overhead, searchlight beams sweeping
        # up from the rooftops, orange bursts where defences hit.
        # Drawn at 105px tall and stretched to 132px (1.26x), so
        # verticals are drawn slightly short. The bottom-left stays
        # clear for the "186 DRONES / 161 DOWNED" scrim. Original
        # PIL vector code.
        d.rectangle([0, 0, w, h], fill=(8, 12, 30))
        d.rectangle([0, 0, w, 34], fill=(12, 18, 44))
        # stars
        for sx, sy in ((22, 10), (70, 16), (140, 8), (210, 14),
                       (280, 8), (340, 16), (378, 10), (120, 24),
                       (250, 26), (320, 30)):
            d.ellipse([sx, sy, sx + 2, sy + 2], fill="white")
        # searchlight beams from the rooftops, pale and NARROW —
        # the v1 beams were 30px wide at the top and read as grey
        # slabs; these are 8px at the top, 4px at the base.
        d.polygon([(63, 96), (67, 96), (116, 8), (108, 8)],
                  fill=(225, 228, 240))
        d.polygon([(303, 96), (307, 96), (338, 12), (330, 12)],
                  fill=(210, 218, 238))
        # the city skyline: dark towers with lit windows
        for bx, bw, bh in ((0, 52, 44), (52, 40, 58), (92, 48, 38),
                           (140, 44, 52), (184, 52, 40), (236, 40, 56),
                           (276, 48, 36), (324, 44, 48), (368, 28, 42)):
            d.rectangle([bx, h - bh, bx + bw, h], fill=(24, 26, 38))
            for wy in range(h - bh + 6, h - 6, 10):
                for wx in range(bx + 6, bx + bw - 6, 10):
                    if (wx * 7 + wy * 13) % 5 < 2:
                        d.rectangle([wx, wy, wx + 3, wy + 4],
                                    fill=(255, 210, 90))
        # a damaged block: one tower with a spiky fire burst at its top
        _star(d, 162, 44, 11, 4, fill=(255, 140, 40))
        _star(d, 162, 44, 6, 2, fill=(255, 210, 31))
        d.polygon([(150, 52), (158, 40), (166, 52)], fill=(60, 30, 20))
        # drones: small dark bodies with rotor lines, crossing the sky
        for dx, dy in ((96, 30), (200, 22), (252, 40), (330, 28),
                       (160, 18), (60, 44)):
            d.ellipse([dx - 7, dy - 4, dx + 7, dy + 4], fill=(10, 10, 14))
            d.line([dx - 11, dy - 6, dx + 11, dy - 6],
                   fill=(220, 220, 230), width=2)
            d.line([dx, dy + 4, dx, dy + 10], fill=(220, 220, 230), width=1)
        # two defence bursts in the sky — spiky stars, not plain discs
        # (the v1 discs read as orange suns)
        for ex, ey in ((228, 34), (88, 52)):
            _star(d, ex, ey, 10, 4, fill=(255, 140, 40))
            _star(d, ex, ey, 5, 2, fill=(255, 210, 31))
    elif key == "powercuts":
        # v1 20261122: Iran begins rationing electricity — a night
        # skyline, left half of the windows lit, right half dark,
        # and a transmission tower going dark. Art is 196x80 with
        # the solid banner over y0-18. The v1 render was too dark to
        # read at card size — sky and buildings lightened, tower in
        # pale grey so it reads against the sky. Original PIL vector
        # code.
        d.rectangle([0, 0, w, h], fill=(26, 34, 62))
        d.ellipse([168, 22, 182, 36], fill=(240, 230, 190))
        # buildings: lit windows left, dark right
        for i, (bx, bw, bh) in enumerate(((8, 34, 34), (46, 30, 44),
                                          (80, 34, 30), (118, 30, 40),
                                          (152, 36, 34))):
            d.rectangle([bx, h - bh, bx + bw, h], fill=(54, 58, 78))
            lit = i < 2
            for wy in range(h - bh + 5, h - 4, 8):
                for wx in range(bx + 5, bx + bw - 5, 9):
                    if lit and (wx + wy) % 3 == 0:
                        d.rectangle([wx, wy, wx + 3, wy + 4],
                                    fill=(255, 220, 110))
        # transmission tower, right, pale against the sky
        d.line([168, 80, 168, 40], fill=(150, 150, 170), width=3)
        d.line([156, 52, 180, 52], fill=(150, 150, 170), width=2)
        d.line([158, 40, 178, 40], fill=(150, 150, 170), width=2)
        d.line([168, 40, 168, 34], fill=(150, 150, 170), width=2)
        # the cut: a red lightning bolt between lit and dark
        d.polygon([(100, 24), (108, 24), (102, 34), (110, 34),
                   (96, 52), (100, 38), (94, 38)], fill=(220, 30, 40))
    elif key == "factoryfire":
        # v1 20261122: candy-factory fire in Cikande — a sawtooth-roof
        # factory, a big fire bursting from the roof, a smoke plume.
        # Art is 196x80 with the solid banner over y0-18. Original
        # PIL vector code.
        d.rectangle([0, 0, w, h], fill=(180, 190, 205))
        d.rectangle([0, 62, w, h], fill=(120, 120, 126))
        # factory: long body + sawtooth roof + chimney
        d.rectangle([20, 44, 176, 62], fill=(90, 90, 100))
        for sx in (20, 52, 84, 116, 148):
            d.polygon([(sx, 44), (sx + 16, 32), (sx + 32, 44)],
                      fill=(70, 70, 80))
        d.rectangle([168, 24, 176, 44], fill=(70, 70, 80))
        # fire bursting from the middle roof
        d.ellipse([78, 22, 118, 50], fill=(255, 140, 40))
        d.ellipse([88, 30, 108, 50], fill=(255, 210, 31))
        d.ellipse([94, 38, 104, 50], fill=(255, 120, 30))
        # smoke plume, grey puffs rising and drifting right
        for sx, sy, sr in ((98, 16, 7), (112, 10, 9), (130, 8, 8),
                           (146, 12, 6)):
            d.ellipse([sx - sr, sy - sr, sx + sr, sy + sr],
                      fill=(90, 90, 96))
        # windows along the body, one glowing from the fire inside
        for wx in (30, 56, 130, 156):
            d.rectangle([wx, 50, wx + 10, 58], fill=(40, 40, 50))
        d.rectangle([82, 50, 92, 58], fill=(255, 180, 60))
    elif key == "hospital":
        # v1 20261122: Bolsonaro in intensive care — a hospital
        # facade with a red-cross sign, lit ward windows, and an
        # ambulance at the kerb. Art is 196x80 with the solid banner
        # over y0-18. Original PIL vector code.
        d.rectangle([0, 0, w, h], fill=(200, 220, 235))
        d.rectangle([0, 64, w, h], fill=(110, 110, 116))
        # hospital block: white, four floors of windows
        d.rectangle([52, 24, 148, 64], fill="white", outline=(60, 60, 70))
        for wy in range(30, 60, 10):
            for wx in range(58, 144, 14):
                d.rectangle([wx, wy, wx + 8, wy + 6], fill=(120, 170, 210))
        # red-cross sign on the roof
        d.rectangle([88, 12, 112, 24], fill=(200, 30, 40))
        d.rectangle([96, 16, 104, 20], fill="white")
        d.rectangle([98, 14, 102, 22], fill="white")
        # entrance canopy + door
        d.rectangle([84, 58, 116, 64], fill=(200, 30, 40))
        d.rectangle([96, 54, 104, 64], fill=(40, 40, 50))
        # ambulance at the kerb, left
        d.rectangle([10, 48, 44, 62], fill="white", outline=(60, 60, 70))
        d.rectangle([32, 52, 44, 62], fill="white", outline=(60, 60, 70))
        d.rectangle([14, 52, 20, 58], fill=(200, 30, 40))
        d.ellipse([18, 60, 24, 66], fill=(20, 20, 20))
        d.ellipse([34, 60, 40, 66], fill=(20, 20, 20))
        # red cross on the ambulance side
        d.rectangle([22, 53, 28, 57], fill=(200, 30, 40))
    elif key == "strike":
        # v1 20261122: Belgian controllers join Monday's national
        # strike — an airport at dawn, two planes parked on the
        # tarmac, and a departures board reading CANCELLED. Art is
        # 196x80 with the solid banner over y0-18. Original PIL
        # vector code.
        d.rectangle([0, 0, w, h], fill=(205, 214, 226))
        d.rectangle([0, 56, w, h], fill=(90, 90, 98))
        d.line([0, 56, w, 56], fill=(60, 60, 66), width=2)
        for dx in range(6, w, 22):
            d.line([dx, 66, dx + 11, 66], fill="white", width=2)
        # control tower, left
        d.rectangle([18, 30, 28, 56], fill=(120, 120, 128))
        d.rectangle([12, 22, 34, 32], fill=(150, 150, 158),
                    outline=(60, 60, 66))
        # departures board, top-right, red CANCELLED
        d.rectangle([104, 22, 188, 44], fill=(20, 20, 26))
        d.text((146, 28), "CANCELLED", font=F_LBL2_S, fill=(255, 80, 80),
               anchor="ma")
        d.text((146, 38), "07:00–21:00", font=F_LBL2_S, fill="white",
               anchor="ma")
        # two parked planes, fuselage + tail + wing
        for px, py, pcol in ((48, 46, (200, 60, 50)),
                             (120, 50, (40, 90, 160))):
            d.ellipse([px, py, px + 52, py + 8], fill=pcol)
            d.polygon([(px + 44, py), (px + 50, py - 8), (px + 54, py)],
                      fill=pcol)
            d.polygon([(px + 18, py + 4), (px + 30, py + 12),
                       (px + 34, py + 4)], fill=pcol)
    elif key == "liquor":
        # v1 20261122: toxic-liquor toll in Manipur — a dark green
        # shelf, a green bottle, and a red warning triangle. Art is
        # 196x80 with the solid banner over y0-18. Original PIL
        # vector code.
        d.rectangle([0, 0, w, h], fill=(16, 60, 44))
        d.rectangle([0, 66, w, h], fill=(10, 40, 30))
        # bottle: neck, shoulders, body, label
        d.rectangle([88, 24, 108, 34], fill=(30, 120, 70))
        d.rectangle([92, 20, 104, 26], fill=(30, 120, 70))
        d.polygon([(88, 34), (108, 34), (116, 44), (80, 44)],
                  fill=(30, 120, 70))
        d.rectangle([80, 44, 116, 66], fill=(30, 120, 70))
        d.rectangle([86, 48, 110, 60], fill=(240, 230, 200))
        d.text((98, 54), "19", font=F_ART2_S, fill=(200, 30, 40),
               anchor="mm")
        # warning triangle, right of the bottle
        d.polygon([(140, 34), (162, 62), (118, 62)], fill=(255, 210, 31),
                  outline=(20, 20, 20))
        d.rectangle([138, 44, 142, 54], fill=(20, 20, 20))
        d.ellipse([138, 56, 142, 60], fill=(20, 20, 20))
        # skull-less skull: two crossed bones, left of the bottle
        d.line([34, 40, 56, 56], fill="white", width=3)
        d.line([56, 40, 34, 56], fill="white", width=3)
        for bx, by in ((34, 40), (56, 40), (34, 56), (56, 56)):
            d.ellipse([bx - 3, by - 3, bx + 3, by + 3], fill="white")
    elif key == "ieupact":
        # v5: EU–Indonesia trade pact — the two flags split down the
        # middle like our chinajapan card: EU blue with a yellow star
        # circle left, Indonesia red-over-white right, gold seam.
        # Art is 196x80 with the solid banner over y0-18.
        # Original PIL vector code.
        half = w // 2
        d.rectangle([0, 0, half, h], fill=(16, 62, 150))
        d.rectangle([half, 0, w, h], fill="white")
        d.rectangle([half, 0, w, 40], fill=(200, 16, 46))
        d.line([half, 0, half, h], fill=(240, 200, 40), width=2)
        # EU star circle, centre-left
        for k in range(12):
            ang = math.radians(-90 + k * 30)
            sx = half // 2 + int(30 * math.cos(ang))
            sy = 50 + int(22 * math.sin(ang))
            _star(d, sx, sy, 4, 2, fill=(255, 220, 60))
    return img

# v1 20261122 pin offsets (map 336x148): computed numerically from
# PINS + DOTS (probe script, same method as v6). Only two pins need
# fanning: 1 Kyiv E (12,0) clears Antalya pin 2 (11.4px un-offset);
# 8 Tehran NE (10,-8) clears Bahrain pin 3 (7.9px un-offset).
PIN_OFF = {1: (12, 0), 8: (10, -8)}

# v1 20261122 dot offsets — same leader-line pattern as PIN_OFF, for
# dots that sit on a pin's circle: 15 Warsaw S (0,8) clears Finland
# pin 7 (7.2px un-offset); 16 Copenhagen N (0,-6) clears Brussels pin
# 12 (8.7px); 28 Gaza SW (-8,6) clears Antalya pin 2 (5.4px);
# 29 Riyadh SE (12,8) clears Bahrain pin 3 (3.8px); 30 New York NE
# (8,-6) clears Washington pin 11 (3.2px); 32 Los Angeles W (-10,6)
# clears Las Vegas pin 6 (3.4px); 34 Leeds NW (-10,-8) clears
# Brussels pin 12 (6.0px); 36 Turin SE (8,4) clears Brussels pin 12
# (5.6px); 19 Manila SE (6,4) clears Hong Kong pin 4 (8.96px);
# 20 Hanoi S (0,8) clears Hong Kong pin 4 (7.91px) and Manipur pin 13
# (15.6px after the move). All clearances verified by the probe script.
DOT_OFF = {15: (0, 8), 16: (0, -6), 19: (6, 4), 20: (0, 8),
           28: (-8, 6), 29: (12, 8),
           30: (8, -6), 32: (-10, 6), 34: (-10, -8), 36: (8, 4)}


def draw_map(d, x0, y0, mw, mh):
    with open(os.path.join(HERE, "world.geo.json")) as f:
        geo = json.load(f)
    shapes = []
    for feat in geo["features"]:
        geom = feat["geometry"]
        if geom["type"] == "Polygon":
            shapes.append(geom["coordinates"])
        elif geom["type"] == "MultiPolygon":
            shapes.extend(geom["coordinates"])
    for shape in shapes:
        for ring in shape:
            pts = []
            for lon, lat in ring:
                px = (lon + 180.0) / 360.0 * mw
                py = (90.0 - lat) / 180.0 * mh
                pts.append((px, py))
            # filled continents, not dots, like the top entries
            d.polygon([(x0 + px, y0 + py) for px, py in pts],
                      fill=SAND)

    def project(lon, lat):
        return (x0 + (lon + 180.0) / 360.0 * mw,
                y0 + (90.0 - lat) / 180.0 * mh)

    for n, (lon, lat) in DOTS.items():
        px, py = project(lon, lat)
        dx, dy = DOT_OFF.get(n, (0, 0))
        if (dx, dy) != (0, 0):
            # leader line from the true spot to the moved dot
            d.line([px, py, px + dx, py + dy], fill=NAVY, width=1)
            d.ellipse([px - 2, py - 2, px + 2, py + 2], fill=NAVY)
            px, py = px + dx, py + dy
        d.ellipse([px - 2, py - 2, px + 2, py + 2], fill=NAVY)
    # v6: no Mercury callout on the map — BepiColombo left the list
    # entirely (it was also-list 23 in v5, a scheduled tonight event,
    # not a place) and, like Bitcoin, has no Earth dot.
    for n, (lon, lat) in PINS.items():
        px, py = project(lon, lat)
        dx, dy = PIN_OFF.get(n, (0, 0))
        if (dx, dy) != (0, 0):
            # leader line from the true spot to the moved pin circle
            d.line([px, py, px + dx, py + dy], fill=RED, width=1)
            d.ellipse([px - 2, py - 2, px + 2, py + 2], fill=RED)
            px, py = px + dx, py + dy
        d.ellipse([px - 7, py - 7, px + 7, py + 7], fill=RED, outline="white")
        # v5.5: number centred on the circle's exact centre by its measured
        # ink box — the old top-anchored draw at py-5 sat every number ~2px
        # too low (measured on v5.4: dy +1.8..+2.4 on all 13 pins).
        label = str(n)
        # v5.6: two-digit labels use the smaller pin font so they sit
        # fully INSIDE the 14px circle; single digits keep the 11px font.
        fnt = F_PIN2 if len(label) == 2 else F_PIN
        box = d.textbbox((0, 0), label, font=fnt)
        tw, th = box[2] - box[0], box[3] - box[1]
        if n in (12, 13):
            # v5.7: optical centring on the RASTERIZED circle centre.
            # PIL floors the ellipse bbox, so the drawn circle sits at
            # (int(px), int(py)) while the v5.5 label was centred on the
            # float (px, py) — measured on v5.6 as +1.0px right on both
            # pins (margins L=4 R=2). Place the ink box by integers so
            # its centre lands on the circle centre: the ink centre
            # relative to the anchor is ((box0+box2-1)/2, (box1+box3-1)/2).
            # The 10px ink box in the 15px disc can never centre exactly
            # (0.5px either way); X uses floor because the "1" glyph's
            # bright stem sits right of its ink-box edge, so the visible
            # mass reads right-shifted at round() — floor nudges both
            # pins 1px left onto the bright mass (pin 13's X is
            # unchanged by floor: 176.5 -> 176, as round() gave).
            icx = (box[0] + box[2] - 1) / 2
            icy = (box[1] + box[3] - 1) / 2
            d.text((math.floor(int(px) - icx), round(int(py) - icy)),
                   label, font=fnt, fill="white")
        else:
            d.text((px - tw / 2 - box[0], py - th / 2 - box[1]), label,
                   font=fnt, fill="white")


# v19 layout constants: HERO-DOMINANT broadsheet (ROUND 3 iteration 1).
# ONE decisive change: giant hero art 150px (matches #8's ~150px scale) +
# the FRIDAY IN UTC timeline strip restored (v12/v13 device, 7 points
# since v21 — 08:00 Hang Seng closes -1.9% added),
# 3 figures), funded by smalls art 40px + map 72px + also-list 11 rows
# at pitch 11 + legend header dropped + hero/small text pitches tightened
# (all probe-measured, see NOTES.md v19 space audit). 40 stories, 18
# drawn cards kept. Hero card 256 tall, small card 117 tall, rows pitch
# 118, footer ink ~1017 (probe-measured).
# v5: 13 drawn cards — hero art 132 (card 238), smalls art 64 (card
# 141), 2 smalls rows at pitch 150, map 336x168. The 28px cut funds
# the restored UTC timeline strip (176-205); hero art is rendered at
# 105px and stretched 1.26x (was 1.52x) — the new hero art is drawn
# for that stretch, and the reused peru/riyadh art is h-relative.
HERO_ART_H = 132
HERO_CARD_H = HERO_ART_H + 14 + 92
SMALL_ART_H = 64
SMALL_CARD_H = SMALL_ART_H + 77


def hero_card(img, d, story, x, y, w):
    """One hero card: v5 132px art (the hero-dominant concept; the art is
    rendered at 105px and LANCZOS-resized to 132px, so flat vector
    shapes stretch vertically 1.26x and stay clean), navy kicker strip
    (14px) with the verification-tag pill, a 2-line 27px Times headline
    (30px pitch, probe-measured ink 26px) and a 2-line serif deck
    (13px pitch, ink 12px), all inside a 1px ink box. The
    headline+deck block is vertically centred in the 92px text area
    below the kicker strip.
    Budget (2-line headline): art 0-132, kicker 132-146, headline
    148-208, deck 210-236, card bottom 238."""
    num, reg, topic, src, status, head, deck, big, small, key, vtag = story
    d.rectangle([x, y, x + w, y + HERO_CARD_H], fill=NEARWHITE)
    art = art_image(key, w, 105)
    art_d = ImageDraw.Draw(art)
    art_text(art, art_d, 0, 0, w, 105, big, small, F_LBL, F_LBL_S)
    art = art.resize((w, HERO_ART_H), Image.LANCZOS)
    img.paste(art, (x, y))
    # navy kicker strip: verification-tag pill left, "N. REGION · TOPIC"
    # after it, source right in gold. Strip text is centred on the glyph
    # centre (strip centre y+HERO_ART_H+7).
    d.rectangle([x, y + HERO_ART_H, x + w, y + HERO_ART_H + 14], fill=NAVY)
    pill_w = d.textlength(vtag, font=F_PILL) + 10
    d.rounded_rectangle([x + 8, y + HERO_ART_H + 2, x + 8 + pill_w,
                         y + HERO_ART_H + 12],
                        radius=2, fill=PILL_COL[vtag])
    d.text((x + 13, y + HERO_ART_H + 7), vtag, font=F_PILL, fill="white",
           anchor="lm")
    d.text((x + 14 + pill_w, y + HERO_ART_H + 7), "%d. %s · %s" % (num, reg, topic),
           font=F_KICK, fill="white", anchor="lm")
    d.text((x + w - 8, y + HERO_ART_H + 7), src, font=F_SRC, fill=GOLD, anchor="rm")
    head_lines = wrap(d, head, F_HEAD_H, w - 16, max_lines=2)
    deck_lines = wrap(d, deck, F_DECK, w - 16, max_lines=2)
    # centre the text block in the 92px text area (kicker bottom
    # y+HERO_ART_H+14 to card bottom y+HERO_CARD_H): 2+2 lines = 88px,
    # 1+2 lines = 58px.
    block_h = len(head_lines) * 30 + 2 + len(deck_lines) * 13
    text_y = y + HERO_ART_H + 14 + (92 - block_h) // 2
    for j, line in enumerate(head_lines):
        d.text((x + 8, text_y + j * 30), line, font=F_HEAD_H, fill=INK)
    for j, line in enumerate(deck_lines):
        d.text((x + 8, text_y + len(head_lines) * 30 + 2 + j * 13),
               line, font=F_DECK, fill=(60, 60, 60))
    d.rectangle([x, y, x + w, y + HERO_CARD_H], outline=INK, width=1)


def small_card(img, d, story, x, y):
    """One small card: v2 64px art (rendered at 80 and LANCZOS-downscaled
    to 64, so the art code itself is untouched; the banner text displays
    at ~14px), with a v4 SOLID colour banner at its top (red, navy for the
    court/rates cards) carrying the art label in white, navy kicker
    strip with the verification-tag pill on the right, a 2-line Times
    headline (16px pitch, probe-measured ink 15px) and a 2-line serif
    deck (12px pitch, ink 10px) + source, all inside a 1px ink box
    with a fixed bottom per row. Card interior near-white on cream.
    v8: the pill shows the verification tag (CONFIRMED/REPORTED), and the
    kicker font auto-shrinks 9 -> 8px when kicker + pill would overflow
    the 196px card (card 12 only: 132+59+12=203 at 9px, 188 at 8px) —
    the same pattern art_banner uses for long label pairs. Card 109 tall:
    art 32, kicker 15, headline 2x16, deck 2x12."""
    num, reg, topic, src, status, head, deck, big, small, key, vtag = story
    w = 196
    d.rectangle([x, y, x + w, y + SMALL_CARD_H], fill=NEARWHITE)
    art = art_image(key, w, 80)
    art_d = ImageDraw.Draw(art)
    banner_fill = NAVY if key in ("cpi", "chinarates") else RED
    art_banner(art, art_d, 0, 0, w, 80, big, small, banner_fill)
    art = art.resize((w, SMALL_ART_H), Image.LANCZOS)
    img.paste(art, (x, y))
    d.rectangle([x, y + SMALL_ART_H, x + w, y + SMALL_ART_H + 15], fill=NAVY)
    # v5.4: strip text vertically centred on the strip centre
    # (y+SMALL_ART_H+7.5) with middle anchors, not top-anchored at y+81.
    kick_text = "%d. %s · %s" % (num, reg, topic)
    pill_w = d.textlength(vtag, font=F_PILL) + 10
    f_kick = F_KICK_S
    if d.textlength(kick_text, font=f_kick) + pill_w + 12 > w:
        f_kick = F_KICK_S8
    d.text((x + 4, y + SMALL_ART_H + 7.5), kick_text,
           font=f_kick, fill="white", anchor="lm")
    d.rounded_rectangle([x + w - 4 - pill_w, y + SMALL_ART_H + 2,
                         x + w - 4, y + SMALL_ART_H + 12],
                        radius=2, fill=PILL_COL[vtag])
    d.text((x + w + 1 - pill_w, y + SMALL_ART_H + 7.5), vtag, font=F_PILL,
           fill="white", anchor="lm")
    head_lines = wrap(d, head, F_HEAD_S, w - 16, max_lines=2)
    for j, line in enumerate(head_lines):
        d.text((x + 8, y + SMALL_ART_H + 19 + j * 16), line, font=F_HEAD_S, fill=INK)
    deck_lines = wrap(d, deck + " — " + src, F_DECK_S, w - 16, max_lines=2)
    for j, line in enumerate(deck_lines):
        d.text((x + 8, y + SMALL_ART_H + 19 + len(head_lines) * 16 + 1 + j * 12),
               line, font=F_DECK_S, fill=(60, 60, 60))
    d.rectangle([x, y, x + w, y + SMALL_CARD_H], outline=INK, width=1)


def main():
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)

    # ---- masthead 0-149 (v20): title 120px squeezed to 996px (see the
    # F_TITLE comment) — ink 19-127 (109px tall), top 1px clear of the
    # kicker ink (ends 17); deck line at y=123 (ink 129-145, 2px clear
    # of the title descenders); bottom rule 147-149 (1 blank row clear
    # of the deck). Kicker unchanged. The +5 rule shift is funded by
    # tl_y -1 (timeline label gap 4->3 blank rows) and foot_y -1
    # (date-check box -> footer gap 4->3 blank rows), so the footer
    # lands at 1020 with ink ending 1020 (1px slack, measured). ----
    # v20: render the title at 120px on its own layer, squeeze it
    # horizontally to 996px (LANCZOS), paste so its ink top sits at 19.
    # Vertical scale is untouched, so the ink stays 109px tall.
    _title = "Sunday 22 November 2026"
    _tw = int(d.textlength(_title, font=F_TITLE)) + 8
    _layer = Image.new("RGBA", (_tw, 150), (0, 0, 0, 0))
    _lt = ImageDraw.Draw(_layer)
    _lt.text((4, 0), _title, font=F_TITLE, fill=INK + (255,))
    _tbb = _layer.getbbox()
    _sq = _layer.resize((996, 150), Image.LANCZOS)
    img.paste(_sq, (12, 19 - _tbb[1]), _sq)
    deck_line = ("186 drones fired at Ukraine overnight · COP31's final text skips fossil fuels · "
                 "Iran's radar claim, Bahrain's denial")
    d.text((12, 123), deck_line, font=F_DECKLINE, fill=RED)
    d.text((1012, 1), "36 STORIES · 7 REGIONS · EVERY ONE DATED SUNDAY 22 NOVEMBER 2026",
           font=F_EYE, fill=INK, anchor="ra")
    d.rectangle([0, 147, W, 149], fill=INK)

    # ---- one-line numbers strip 150-162 (v20: moved +5 with the
    # masthead reflow; v2 content, 6 figures, ~770px at 12px in
    # the 1000px slot. Ink 153-163, region bar at 164 — same 0-blank-row
    # adjacency as v19 (ink 148-158, bar 159). ----
    d.text((12, 150), "THE DAY IN NUMBERS:", font=F_TTIME, fill=RED)
    _nx = 12 + int(d.textlength("THE DAY IN NUMBERS:  ", font=F_TTIME))
    for _i, (_value, _caption) in enumerate(STATS):
        d.text((_nx, 150), _value, font=F_TTIME, fill=RED)
        _nx += int(d.textlength(_value, font=F_TTIME)) + 4
        d.text((_nx, 150), _caption, font=F_TTIME, fill=INK)
        _nx += int(d.textlength(_caption, font=F_TTIME))
        if _i < len(STATS) - 1:
            d.text((_nx, 150), "  ·  ", font=F_TTIME, fill=GREY)
            _nx += int(d.textlength("  ·  ", font=F_TTIME))

    # ---- region bar 164-175 (v20: moved +5 with the masthead reflow;
    # 11px tall, 7 segments for v1's 36: EUROPE 8, MIDDLE EAST 4,
    # AFRICA 3, ASIA-PACIFIC 10, AMERICAS 8, OCEANIA 2, WORLD 1) ----
    bar_x, bar_y, bar_w, bar_h = 12, 164, 1000, 11
    seg_w = bar_w / len(REGIONS)
    for i, (label, count, fill, ink) in enumerate(REGIONS):
        sx = bar_x + i * seg_w
        d.rectangle([sx, bar_y, sx + seg_w - 1, bar_y + bar_h], fill=fill)
        # v5.4: label vertically centred in the segment (bar_y+6),
        # not top-anchored.
        d.text((sx + seg_w / 2, bar_y + 6), "%s %d" % (label, count),
               font=F_SRC, fill=ink, anchor="mm")

    # ---- THE DAY IN UTC timeline 176-205 (v5: restored — 7 events
    # now carry verified UTC clock times; the v21 device in the same
    # shape: evenly spaced columns, NOT to scale; time bold 11px above
    # a ruled line with red dots, event bold 10px below. Label box at
    # left ("THE DAY IN UTC", 78px), columns span 98-1012 (130.6px
    # each). Probe-measured: longest event "Verstappen wins Vegas"
    # 115.1px in the 130.6px column (15.5px clear); last event ends
    # 1001.4, inside the 1012 edge. Times verified live 2026-11-22. ----
    tl_y = 176
    d.rectangle([12, tl_y, 90, tl_y + 20], fill=INK)
    d.text((51, tl_y + 10), "THE DAY IN UTC", font=F_SRC, fill="white",
           anchor="mm")
    tl = [("01:00", "HK polls open"),
          ("03:00", "COP31 objections end"),
          ("05:30", "Verstappen wins Vegas"),
          ("06:00", "COP31 approval due"),
          ("08:00", "161 drones downed"),
          ("14:00", "HK turnout 93.55%"),
          ("17:00", "Alcaraz–Zverev final")]
    tl_x0, tl_x1 = 98, 1012
    tl_col = (tl_x1 - tl_x0) / len(tl)
    d.line([tl_x0, tl_y + 14, tl_x1, tl_y + 14], fill=INK, width=1)
    for i, (tt, ev) in enumerate(tl):
        cx = tl_x0 + tl_col * (i + 0.5)
        d.text((cx, tl_y + 1), tt, font=F_TTIME, fill=RED, anchor="ma")
        d.ellipse([cx - 3, tl_y + 11, cx + 3, tl_y + 17], fill=RED)
        d.text((cx, tl_y + 19), ev, font=F_TTEXT, fill=INK, anchor="ma")

    # ---- heroes 208-446 (v5: art 132, card 238; lead 396 wide, rails
    # 294; each card boxed like top 1) ----
    hero_y = 208
    hero_widths = [396, 294, 294]
    hero_x = 12
    for i, story in enumerate(FRONT[:3]):
        hero_card(img, d, story, hero_x, hero_y, hero_widths[i])
        hero_x += hero_widths[i] + 8

    # ---- smalls 454-745 (v2: art 64, card 141, row pitch 150;
    # 2 rows x 5, image 196x64, gaps 9 — the top-1 whitespace level;
    # the rows are cards 4-13) ----
    for r in range(2):
        for c in range(5):
            k = 3 + r * 5 + c
            small_card(img, d, FRONT[k], 12 + c * 204, 454 + r * 150)

    # ---- map + also 753-929 (v1 20261122: map is LIGHT — pale-blue
    # ocean, tan land, navy dots, red pins — the v7 dark-navy map
    # read as a black hole in the top entries' cream pages; the
    # winners all use a light map. Map 148 tall; also-list 23 items
    # in 12 rows at pitch 13, col 0 takes 12, col 1 takes 11. The
    # legend line under the map is GONE — its definitions now live in
    # the HOW WE CHECKED box, and at 148 tall the legend would
    # collide with the also-list's last row) ----
    map_y = 753
    d.text((12, map_y), "WHERE IT HAPPENED", font=F_SEC, fill=INK)
    d.line([12, map_y + 16, 348, map_y + 16], fill=INK, width=1)
    d.rectangle([12, map_y + 22, 348, map_y + 170], fill=OCEAN,
                outline=RULE, width=1)
    draw_map(d, 12, map_y + 22, 336, 148)

    also_x = 364
    d.text((also_x, map_y), "ALSO ON SUNDAY 22 NOVEMBER", font=F_SEC, fill=INK)
    d.text((1012, map_y), "23 MORE STORIES", font=F_SEC, fill=INK, anchor="ra")
    d.line([also_x, map_y + 16, 1012, map_y + 16], fill=INK, width=1)
    col_w = 320
    rows = 12
    for i, (num, city, txt, src) in enumerate(ALSO):
        col = 0 if i < rows else 1
        row = i if i < rows else i - rows
        x = also_x + col * (col_w + 8)
        y = map_y + 22 + row * 13
        d.text((x, y), "%d." % num, font=F_ALSO_N, fill=RED)
        full = "%s: %s (%s)" % (city, txt, src)
        lines = wrap(d, full, F_ALSO, col_w - 22, max_lines=1)
        d.text((x + 20, y), lines[0] if lines else "", font=F_ALSO, fill=INK)

    # ---- date check 935-962 (v1 20261122: lists the Friday 20 Nov
    # news left out plus the Saturday 21 Nov news left out plus the
    # not-yet-confirmed items. Box 27 tall, lines at -1/+10 as in
    # v19 — probe-verified clearances.) ----
    chk_y = 935
    d.rectangle([12, chk_y, 1012, chk_y + 27], outline=RED, width=2)
    chk = ("DATE CHECK — Left out, first reported Friday 20 Nov: Peru quake · Myanmar genocide ruling · "
           "Nvidia SEC probe · Russia's 400-drone barrage. Saturday 21 Nov: 'El Chapo Isidro' captured · "
           "Bayelsa boat, 24 dead · EU–Indonesia trade deal · BepiColombo Mercury burn · Fred Nile dies. "
           "Not yet confirmed: COP31 final text · ATP Finals title match, later today.")
    chk_lines = wrap(d, chk, F_DATECHK, 976, max_lines=2)
    # lines at chk_y-1 / chk_y+10 (see the box comment above).
    for j, ln in enumerate(chk_lines):
        d.text((20, chk_y - 1 + j * 11), ln, font=F_DATECHK, fill=INK)

    # ---- footer 966-1017 (v6: foot_y = chk_y+31; 2 centred lines at
    # 966/976, then the HOW WE CHECKED box 988-1017 — promoted from
    # footer line 3 to a proper box, the top-1 pattern. Box lines at
    # 992/1002 (probe-measured 745.7/282.5px in the 984px interior);
    # box bottom 1017, 4px slack to the 1021 safe limit. The drone
    # count and "Corrections: none" live in the box. ----
    foot_y = 966
    d.text((512, foot_y), "Every story here happened, or was first reported, on Sunday 22 November 2026.",
           font=F_FOOT, fill=GREY, anchor="ma")
    # Line 2 is just the source list.
    d.text((512, foot_y + 10), "Sources: Reuters · AP · AFP · BBC · Al Jazeera · SCMP · IRGC · Bahrain MoI · "
           "Ukrainian Air Force · FIA · DetikNews · Xinhua · IANS · Yonhap · ABC · Vatican News · ATP.",
           font=F_FOOT, fill=GREY, anchor="ma")
    # The HOW WE CHECKED box: red lead, ink body, 2 lines.
    d.rectangle([12, 988, 1012, 1017], outline=RED, width=2)
    _hx = 20 + int(d.textlength("HOW WE CHECKED — ", font=F_FOOT))
    d.text((20, 992), "HOW WE CHECKED — ", font=F_FOOT, fill=RED)
    d.text((_hx, 992), "CONFIRMED 2+ named sources agree · OFFICIAL on the record · "
           "REPORTED one named source · CLAIM one side's claim, unverified",
           font=F_FOOT, fill=INK)
    d.text((20, 1002), "Drone count: Ukrainian Air Force 186 fired, 161 downed · Corrections: none",
           font=F_FOOT, fill=INK)

    out_path = os.path.join(HERE, "entry.png")
    img.save(out_path)
    print("saved", out_path, os.path.getsize(out_path), "bytes")
    if PROBLEMS:
        print("PROBLEMS:")
        for problem in PROBLEMS:
            print(" -", problem)
    else:
        print("no truncation")


if __name__ == "__main__":
    main()
