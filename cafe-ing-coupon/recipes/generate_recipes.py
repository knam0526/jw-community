#!/usr/bin/env python3
"""카페아이엔지 메뉴 레시피 — 수기 수정본 A4 PDF."""

from __future__ import annotations

import re
from pathlib import Path

from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

ROOT = Path(__file__).resolve().parent
FONTS = ROOT.parent / "fonts"
OUTPUT = ROOT / "output"
LOGO = ROOT.parent / "assets" / "cafe-ing-logo.png"

MAROON = (0.545, 0.184, 0.184)
MAROON_DK = (0.42, 0.12, 0.12)
TAN = (0.82, 0.64, 0.42)
TAN_BG = (0.96, 0.90, 0.78)
HOT_BG = (0.98, 0.88, 0.88)
ICED_BG = (0.86, 0.92, 0.98)
YELLOW = (1.0, 0.97, 0.82)
HEADER_ROW = (0.93, 0.82, 0.76)
GRID = (0.25, 0.25, 0.25)
INK = (0.12, 0.12, 0.12)
HOT = (0.75, 0.12, 0.12)
ICED = (0.12, 0.32, 0.72)
RUST = (0.70, 0.28, 0.10)
WHITE = (1, 1, 1)
NOTE_RED = (0.72, 0.10, 0.10)

VERSION = "ver.260906"
STORE = "경삼관점 · 장준하통일관점"


def register_fonts() -> None:
    pdfmetrics.registerFont(TTFont("Body", str(FONTS / "Pretendard-Medium.ttf")))
    pdfmetrics.registerFont(TTFont("Bold", str(FONTS / "Pretendard-Bold.ttf")))
    pdfmetrics.registerFont(TTFont("Display", str(FONTS / "Cafe24Ssurround.ttf")))


def group_hot_iced(
    rows: list[tuple[str, str, str, str]],
) -> list[tuple[str, list[tuple[str, str, str]]]]:
    """빈 품목명은 직전 메뉴의 HOT/ICED 짝으로 묶는다."""
    groups: list[tuple[str, list[tuple[str, str, str]]]] = []
    for name, kind, rec, note in rows:
        if name or not groups:
            groups.append((name, [(kind, rec, note)]))
        else:
            groups[-1][1].append((kind, rec, note))
    return groups


def wrap(text: str, font: str, size: float, max_w: float) -> list[str]:
    if not text:
        return [""]
    lines: list[str] = []
    for para in text.split("\n"):
        cur = ""
        for ch in para:
            trial = cur + ch
            if pdfmetrics.stringWidth(trial, font, size) <= max_w:
                cur = trial
            else:
                if cur:
                    lines.append(cur)
                cur = ch
        lines.append(cur)
    return lines or [""]


# 원본 인쇄본: 얼음 안내는 파랑, 나머지 계량(g/샷/스푼/펌프)은 빨강.
ICE_RE = re.compile(
    r"얼음\s*(?:한컵가득|가득|밑선↓|밑선)\([^)]+\)"
    r"|밑선↓\([^)]+\)"
    r"|밑선=\d+g"
    r"|가득(?:\(플랫\))?=\d+g"
)
AMT_RE = re.compile(
    r"약\s*\d+g"
    r"|우유\d+:거품\d+"
    r"|\d+(?:\.\d+)?(?:샷|초|줄|회|cm|EA)"
    r"|\d+(?:\.\d+)?(?:SF|P|S)\(\d+g\)"
    r"|\d+(?:\.\d+)?(?:SF|P|S)(?=$|[^A-Za-z가-힣])"
    r"|\d{1,3}(?:,\d{3})+g"
    r"|(?<![A-Za-z0-9])\d+(?:\.\d+)?g"
)


def colorize_recipe(text: str) -> list[tuple[str, tuple[float, float, float]]]:
    if not text:
        return [("", INK)]
    marks: list[tuple[int, int, tuple[float, float, float]]] = []
    for m in ICE_RE.finditer(text):
        marks.append((m.start(), m.end(), ICED))
    for m in AMT_RE.finditer(text):
        if any(not (m.end() <= a or m.start() >= b) for a, b, _c in marks):
            continue
        marks.append((m.start(), m.end(), HOT))
    marks.sort(key=lambda t: (t[0], t[1]))
    out: list[tuple[str, tuple[float, float, float]]] = []
    pos = 0
    for a, b, col in marks:
        if a > pos:
            out.append((text[pos:a], INK))
        out.append((text[a:b], col))
        pos = b
    if pos < len(text):
        out.append((text[pos:], INK))
    return out or [("", INK)]


def wrap_colored(
    spans: list[tuple[str, tuple[float, float, float]]],
    font: str,
    size: float,
    max_w: float,
) -> list[list[tuple[str, tuple[float, float, float]]]]:
    lines: list[list[tuple[str, tuple[float, float, float]]]] = []
    cur: list[tuple[str, tuple[float, float, float]]] = []
    cur_w = 0.0

    def push_ch(ch: str, color: tuple[float, float, float]) -> None:
        nonlocal cur_w
        if cur and cur[-1][1] == color:
            cur[-1] = (cur[-1][0] + ch, color)
        else:
            cur.append((ch, color))
        cur_w += pdfmetrics.stringWidth(ch, font, size)

    for text, color in spans:
        for ch in text:
            if ch == "\n":
                lines.append(cur or [("", color)])
                cur = []
                cur_w = 0.0
                continue
            cw = pdfmetrics.stringWidth(ch, font, size)
            if cur and cur_w + cw > max_w:
                lines.append(cur)
                cur = []
                cur_w = 0.0
            push_ch(ch, color)
    if cur:
        lines.append(cur)
    return lines or [[("", INK)]]


class Page:
    def __init__(self, path: Path, landscape: bool) -> None:
        self.w = (297 if landscape else 210) * mm
        self.h = (210 if landscape else 297) * mm
        self.c = canvas.Canvas(str(path), pagesize=(self.w, self.h))
        self.c.setTitle("카페아이엔지 메뉴 레시피 수정본")
        self.c.setAuthor("CAFE ING")
        self.y = self.h - 6 * mm
        self.ml = 6 * mm
        self.mr = 6 * mm
        self.content_w = self.w - self.ml - self.mr

    def save(self) -> None:
        self.c.save()

    def set_fill(self, rgb: tuple[float, float, float]) -> None:
        self.c.setFillColorRGB(*rgb)

    def set_stroke(self, rgb: tuple[float, float, float]) -> None:
        self.c.setStrokeColorRGB(*rgb)

    def footer_bar(self) -> None:
        self.c.setFillColorRGB(*TAN_BG)
        self.c.rect(self.ml, 3.2 * mm, self.content_w, 5.2 * mm, stroke=0, fill=1)
        self.c.setFillColorRGB(*INK)
        self.c.setFont("Body", 7)
        self.c.drawString(self.ml + 2 * mm, 5 * mm, f"카페아이엔지  {STORE}")
        self.c.setFont("Body", 7)
        self.c.drawRightString(self.w - self.mr - 2 * mm, 5 * mm, VERSION)

    def title_header(self, subtitle: str = "") -> None:
        if LOGO.exists():
            self.c.drawImage(
                str(LOGO),
                self.ml,
                self.y - 8.2 * mm,
                width=28 * mm,
                height=7.4 * mm,
                mask="auto",
                preserveAspectRatio=True,
            )
        self.c.setFillColorRGB(*INK)
        self.c.setFont("Display", 16)
        self.c.drawCentredString(self.w / 2, self.y - 6.4 * mm, "카페아이엔지 메뉴 레시피")
        self.c.setFont("Body", 8)
        self.c.setFillColorRGB(0.35, 0.35, 0.35)
        self.c.drawRightString(self.w - self.mr, self.y - 6.2 * mm, f"{subtitle}  {VERSION}")
        self.y -= 11 * mm

    def section_bar(self, title: str, height: float = 7.2 * mm) -> None:
        self.y -= height
        self.set_fill(MAROON)
        self.c.rect(self.ml, self.y, self.content_w, height, stroke=0, fill=1)
        self.set_fill(WHITE)
        self.c.setFont("Bold", 11)
        self.c.drawCentredString(self.ml + self.content_w / 2, self.y + 2.2 * mm, title)

    def col_header(self, cols: list[tuple[str, float]], height: float = 5.6 * mm) -> None:
        self.y -= height
        x = self.ml
        self.set_fill(HEADER_ROW)
        self.c.rect(self.ml, self.y, self.content_w, height, stroke=0, fill=1)
        self.set_stroke(GRID)
        self.c.setLineWidth(0.5)
        self.c.rect(self.ml, self.y, self.content_w, height, stroke=1, fill=0)
        self.set_fill(INK)
        self.c.setFont("Bold", 8)
        xx = x
        for label, w in cols:
            self.c.line(xx, self.y, xx, self.y + height)
            self.c.drawCentredString(xx + w / 2, self.y + 1.7 * mm, label)
            xx += w
        self.c.line(self.ml + self.content_w, self.y, self.ml + self.content_w, self.y + height)

    def _wrap_cell(self, text: str, font: str, size: float, width: float) -> list[str]:
        return wrap(text or "", font, size, max(width - 2.4 * mm, 6))

    def _wrap_recipe(self, text: str, font: str, size: float, width: float):
        return wrap_colored(colorize_recipe(text), font, size, max(width - 2.4 * mm, 6))

    def _text_block_h(self, n_lines: int, font_size: float, pad: float) -> float:
        return n_lines * (font_size + 1.6) + pad * 2

    def _draw_rich_lines(
        self,
        x: float,
        y: float,
        w: float,
        h: float,
        lines: list[list[tuple[str, tuple[float, float, float]]]],
        font: str,
        size: float,
        align: str = "left",
        valign: str = "center",
        pad: float = 1.3 * mm,
    ) -> None:
        line_h = size + 1.6
        content_h = (len(lines) - 1) * line_h + size
        if valign == "center":
            first = y + (h - content_h) / 2 + (content_h - size)
        else:
            first = y + h - pad - size
        self.c.setFont(font, size)
        for i, spans in enumerate(lines):
            yy = first - i * line_h
            if align == "center":
                tw = sum(pdfmetrics.stringWidth(t, font, size) for t, _c in spans)
                xx = x + (w - tw) / 2
            else:
                xx = x + 1.2 * mm
            for frag, color in spans:
                self.set_fill(color)
                self.c.setFont(font, size)
                self.c.drawString(xx, yy, frag)
                xx += pdfmetrics.stringWidth(frag, font, size)

    def _draw_lines(
        self,
        x: float,
        y: float,
        w: float,
        h: float,
        lines: list[str],
        font: str,
        size: float,
        fg: tuple[float, float, float],
        align: str = "left",
        valign: str = "center",
        pad: float = 1.3 * mm,
    ) -> None:
        self._draw_rich_lines(
            x, y, w, h, [[(line, fg)] for line in lines], font, size, align=align, valign=valign, pad=pad
        )

    def draw_row(
        self,
        cells: list[tuple[str, float, str, tuple[float, float, float] | None, tuple[float, float, float]]],
        font_size: float = 7.4,
        min_h: float = 6.4 * mm,
        pad: float = 1.3 * mm,
        colorize_idx: int | None = None,
    ) -> None:
        wrapped: list[list[list[tuple[str, tuple[float, float, float]]]]] = []
        max_lines = 1
        for i, (text, w, font, _bg, fg) in enumerate(cells):
            if colorize_idx is not None and i == colorize_idx:
                lines = self._wrap_recipe(text, font, font_size, w)
            else:
                lines = [[(ln, fg)] for ln in self._wrap_cell(text, font, font_size, w)]
            wrapped.append(lines)
            max_lines = max(max_lines, len(lines))
        h = max(min_h, self._text_block_h(max_lines, font_size, pad))
        self.y -= h
        x = self.ml
        self.set_stroke(GRID)
        self.c.setLineWidth(0.7)
        for (_text, w, font, bg, _fg), lines in zip(cells, wrapped):
            if bg:
                self.set_fill(bg)
                self.c.rect(x, self.y, w, h, stroke=0, fill=1)
            self.set_stroke(GRID)
            self.c.rect(x, self.y, w, h, stroke=1, fill=0)
            self._draw_rich_lines(x, self.y, w, h, lines, font, font_size, align="left", valign="top", pad=pad)
            x += w

    def draw_item_group(
        self,
        item_w: float,
        kind_w: float,
        rec_w: float,
        note_w: float,
        item_name: str,
        variants: list[tuple[str, str, str]],
        font_size: float = 7.0,
        min_h: float = 5.8 * mm,
        pad: float = 1.3 * mm,
        note_fg: tuple[float, float, float] | None = None,
    ) -> None:
        """품목·비고를 HOT/ICED 행에 걸쳐 합친다. variants: [(kind, recipe, note), ...]"""
        item_lines = self._wrap_cell(item_name, "Bold", font_size, item_w)
        notes = [n for _k, _r, n in variants if n]
        note_text = "\n".join(dict.fromkeys(notes))
        note_lines = self._wrap_cell(note_text, "Body", font_size, note_w)
        if note_fg is None:
            note_fg = NOTE_RED if any(ch in note_text for ch in ("X", "주의", "★★★")) else INK

        kind_wraps: list[tuple[str, list[str], tuple | None, tuple]] = []
        rec_wraps: list[list[list[tuple[str, tuple[float, float, float]]]]] = []
        need_hs: list[float] = []
        for kind, rec, _note in variants:
            label, kbg, kfg = self.kind_cell(kind)
            k_lines = self._wrap_cell(label, "Bold", font_size, kind_w)
            r_lines = self._wrap_recipe(rec, "Body", font_size, rec_w)
            kind_wraps.append((label, k_lines, kbg, kfg))
            rec_wraps.append(r_lines)
            need_hs.append(
                max(
                    min_h,
                    self._text_block_h(max(len(k_lines), len(r_lines)), font_size, pad),
                )
            )

        n = max(len(variants), 1)
        pair_each = max(need_hs) if need_hs else min_h
        h = max(
            n * pair_each,
            self._text_block_h(len(item_lines), font_size, pad),
            self._text_block_h(len(note_lines), font_size, pad),
            min_h,
        )
        sub_h = h / n
        total_w = item_w + kind_w + rec_w + note_w

        self.y -= h
        y = self.y
        x = self.ml

        self.c.setLineWidth(0.7)
        cy = y + h
        for i, ((label, k_lines, kbg, kfg), r_lines) in enumerate(zip(kind_wraps, rec_wraps)):
            if kbg:
                self.set_fill(kbg)
                self.c.rect(x + item_w, cy - sub_h, kind_w, sub_h, stroke=0, fill=1)
            self._draw_lines(x + item_w, cy - sub_h, kind_w, sub_h, k_lines, "Bold", font_size, kfg, align="center")
            self._draw_rich_lines(x + item_w + kind_w, cy - sub_h, rec_w, sub_h, r_lines, "Body", font_size, align="left")
            if i < n - 1:
                self.set_stroke(GRID)
                self.c.line(x + item_w, cy - sub_h, x + item_w + kind_w + rec_w, cy - sub_h)
            cy -= sub_h

        self._draw_lines(x, y, item_w, h, item_lines, "Bold", font_size, INK, align="center")
        self._draw_lines(x + item_w + kind_w + rec_w, y, note_w, h, note_lines, "Body", font_size, note_fg, align="left")

        self.set_stroke(GRID)
        self.c.rect(x, y, total_w, h, stroke=1, fill=0)
        vx = x
        for w in (item_w, kind_w, rec_w, note_w):
            vx += w
            self.c.line(vx, y, vx, y + h)

    def kind_cell(self, kind: str) -> tuple[str, tuple, tuple]:
        if kind == "HOT":
            return "HOT", HOT_BG, HOT
        if kind == "ICED":
            return "ICED", ICED_BG, ICED
        return kind, None, INK

    def tip_box(self, lines: list[str], height: float | None = None) -> None:
        h = height or (8.2 * mm + len(lines) * 3.6 * mm)
        self.y -= h + 1.2 * mm
        self.set_fill(TAN)
        self.c.rect(self.ml, self.y + h - 6.2 * mm, 38 * mm, 6.2 * mm, stroke=0, fill=1)
        self.set_fill(WHITE)
        self.c.setFont("Bold", 8.5)
        self.c.drawCentredString(self.ml + 19 * mm, self.y + h - 4.3 * mm, "ING 레시피 TIP")
        self.set_fill(TAN_BG)
        self.c.rect(self.ml + 38 * mm, self.y, self.content_w - 38 * mm, h, stroke=0, fill=1)
        self.set_stroke(GRID)
        self.c.rect(self.ml, self.y, self.content_w, h, stroke=1, fill=0)
        self.c.line(self.ml + 38 * mm, self.y, self.ml + 38 * mm, self.y + h)
        self.c.setFont("Body", 7.1)
        ty = self.y + h - 9.4 * mm
        for line in lines:
            xx = self.ml + 40 * mm
            for frag, color in colorize_recipe(line):
                self.set_fill(color)
                self.c.setFont("Body", 7.1)
                self.c.drawString(xx, ty, frag)
                xx += pdfmetrics.stringWidth(frag, "Body", 7.1)
            ty -= 3.55 * mm


def page1_smoothie(path: Path) -> None:
    p = Page(path, landscape=True)
    p.title_header("기타 · 스무디 · 프라페")
    item_w, rec_w, note_w = 38 * mm, 168 * mm, p.content_w - 206 * mm
    cols = [("품목", item_w), ("제조순서", rec_w), ("비고", note_w)]

    p.section_bar("기타 제조방법")
    p.col_header(cols)
    others = [
        ("설탕시럽", "블렌딩[설탕 1 : 온수 1] / 식힌 후 사용", "믹싱 시 폭발주의★★"),
        ("콜드브루원액", "그라인더 굵기 : 3.5 / 원두 400g + 정수 2,000g = 총 12시간 이상 추출", ""),
        (
            "크림베이스",
            "블렌딩/거품용[달콤휘핑 100g + 우유 70g + 스틱설탕 1EA] / 1번 버튼 3회 = BMP(스텐통)에 랩핑(밀봉) 후 냉장보관",
            "블렌더볼·크림·우유를 차가운 상태로 제조해야 단단한 크림이 생성됨  *우유 베이스 3일 사용",
        ),
        (
            "흑임자크림베이스",
            "블렌딩/거품용[달콤휘핑 100g + 우유 70g + 흑임자파우더 45g] / 1번 버튼 3회 = BMP(스텐통)에 랩핑(밀봉) 후 냉장보관",
            "",
        ),
        ("아이스티", "아이스티 원액 500g + 정수 1,500g", ""),
    ]
    for name, rec, note in others:
        p.draw_row(
            [
                (name, item_w, "Bold", None, INK),
                (rec, rec_w, "Body", None, INK),
                (note, note_w, "Body", None, NOTE_RED if "주의" in note or "3일" in note else INK),
            ],
            colorize_idx=1,
        )

    p.section_bar("SMOOTHIE")
    p.col_header(cols)
    smoothies = [
        ("플레인요거트스무디", "블렌딩[우유 160g + 요거트파우더 4S(56g) + 얼음 가득(300g)]", ""),
        (
            "딸기요거트스무디",
            "블렌딩[우유 160g + 요거트파우더 2S(42g) + 딸기리플잼 60g + 얼음 가득(300g)] + 딸기리플잼 20g(벽면)",
            "벽면에 베이스를 고루 펴발라주기",
        ),
        (
            "블루베리요거트스무디",
            "블렌딩[우유 160g + 요거트파우더 2S(32g) + 블루베리리플잼 60g + 얼음 가득(300g)] + 블루베리리플잼 20g(벽면)",
            "벽면에 베이스를 고루 펴발라주기",
        ),
        (
            "망고요거트스무디",
            "블렌딩[우유 160g + 요거트파우더 2S(32g) + 망고리플잼 60g + 얼음 가득(300g)] + 망고리플잼 20g(벽면)",
            "벽면에 베이스를 고루 펴발라주기",
        ),
    ]
    for name, rec, note in smoothies:
        p.draw_row(
            [(name, item_w, "Bold", None, INK), (rec, rec_w, "Body", None, INK), (note, note_w, "Body", None, INK)],
            colorize_idx=1,
        )

    p.section_bar("FRAPPE")
    p.col_header(cols)
    frappes = [
        (
            "커피프라페(모카)",
            "블렌딩[우유 120g + 에스프레소 2샷 + 초코소스 1P(37g) + 코코초코파우더 2S(30g) + 얼음 가득(300g)] + 휘핑크림",
            "초코소스 드리즐(#모양, 약 5g)",
        ),
        (
            "자바칩프라페",
            "블렌딩[우유 170g + 자바칩파우더 3S(42g) + 쉐이크파우더 1S(12g) + 얼음 가득(300g)] + 휘핑크림",
            "",
        ),
        (
            "쿠앤크프라페",
            "블렌딩[우유 170g + 쿠앤크파우더 4S(48g) + 쉐이크파우더 1S(12g) + 얼음 가득(300g)] + 휘핑크림",
            "",
        ),
        (
            "제주산말차프라페",
            "블렌딩[우유 170g + 녹차파우더 3S(45g) + 쉐이크파우더 1S(12g) + 얼음 가득(300g)] + 휘핑크림",
            "",
        ),
        (
            "바닐라프라페",
            "블렌딩[우유 170g + 바닐라파우더 3S(42g) + 쉐이크파우더 1S(12g) + 얼음 가득(300g)] + 휘핑크림",
            "",
        ),
        (
            "민트초코프라페",
            "블렌딩[우유 170g + 민트초코파우더 3S(45g) + 쉐이크파우더 1S(12g) + 얼음 가득(300g)] + 휘핑크림",
            "",
        ),
        (
            "블랙카카오프라페",
            "블렌딩[우유 160g + 미드나잇파우더 4S(56g) + 얼음 가득(300g)] + 음료 중간 휘핑크림 1줄 + 나머지 음료 + 휘핑크림",
            "중간 휘핑 토핑 ★★★(비주얼 UP)",
        ),
        (
            "코코넛커피스무디",
            "블렌딩[우유 170g + 코코넛파우더 4S(40g) + 얼음 가득(300g)] + 에스프레소 2샷(사이드)",
            "",
        ),
        ("쉑쉑 밀크쉐이크", "블렌딩[우유 160g + 쉐이크파우더 5S(60g) + 얼음 가득(300g)]", ""),
    ]
    for name, rec, note in frappes:
        p.draw_row(
            [
                (name, item_w, "Bold", None, INK),
                (rec, rec_w, "Body", None, INK),
                (note, note_w, "Body", None, NOTE_RED if "★★★" in note else INK),
            ],
            colorize_idx=1,
        )

    p.tip_box(
        [
            "▷ 블렌디드 음료 제조 시 블렌더 볼에 (액체 → 원물 → 얼음) 투입 순서를 꼭 지켜주세요!  (★★기계 작동이 멈춘 후 볼 제거하기★★)",
            "▷ 블렌딩[ ] : 블렌디드(블렌더 활용) 음료     ▷ 휘핑크림 : 포모나, 약 두바퀴 반(25g)     ▷ 계량단위 : P=펌프, S=스푼, SF=스푼가득, EA=개",
            "▷ (벽면) : 계량 후 컵을 돌려가며 벽면에 펴발라주기     ▷ 얼음 : 가득=300g",
        ]
    )
    p.footer_bar()
    p.save()


def page2_tea_juice(path: Path) -> None:
    p = Page(path, landscape=True)
    p.title_header("티 · 에이드 · 주스")
    item_w, kind_w, rec_w = 38 * mm, 16 * mm, 166 * mm
    note_w = p.content_w - item_w - kind_w - rec_w
    cols = [("품목", item_w), ("구분", kind_w), ("제조순서", rec_w), ("비고", note_w)]

    p.section_bar("TEA & ADE")
    p.col_header(cols)

    teas = [
        ("허브티, 홍차\n(티백류)", "HOT", "해당티백 2EA + 온수 400g", ""),
        ("", "ICED", "우리기[해당티백 2EA + 온수 200g] + 얼음 한컵가득(350g) + 우려낸 티백과 함께 붓고 제공", ""),
        ("수제차\n(레몬/자몽/유자)", "HOT", "해당청 3S(75g) + 온수 350g", ""),
        ("", "ICED", "해당청 3S(75g) + 얼음 가득(300g) + 정수 200g", ""),
        ("로얄밀크티", "HOT", "얼그레이파우더 3S(48g) + 스팀우유 300g", ""),
        ("", "ICED", "mix[얼그레이파우더 3S(48g) + 온수] + 얼음 가득(300g) + 우유 200g + 우유거품(2cm)", ""),
        ("흑당밀크티", "ICED", "mix[얼그레이파우더 3S(48g) + 온수] + 흑당시럽 30g(벽면) + 얼음 밑선(250g) + 우유 200g", "벽면에 베이스를 고루 펴발라주기"),
        ("흑임자밀크티", "HOT", "얼그레이파우더 3S(48g) + 스팀우유 300g + 흑임자크림베이스 1SF(20g)", "크림베이스 거품 스푼 사용"),
        ("", "ICED", "mix[얼그레이파우더 3S(48g) + 온수] + 얼음 밑선(250g) + 우유 240g + 흑임자크림베이스 1SF(20g)", ""),
        ("아이스티(피치)", "ICED", "아이스티원액 65g + 얼음 가득(300g) + 정수 200g", ""),
        ("제로자몽허니블랙티", "HOT", "제로자몽허니블랙티시럽 6P(45g) + 온수 350g", ""),
        ("", "ICED", "얼음 가득(300g) + 제로자몽허니블랙티시럽 6P(45g) + 정수 200g", ""),
        ("제로피치우롱티", "HOT", "제로피치우롱티시럽 6S(45g) + 온수 350g", ""),
        ("", "ICED", "얼음 가득(300g) + 제로피치우롱티시럽 6S(45g) + 정수 200g", ""),
        ("에이드\n(레몬/자몽/청포도/한라봉)", "ICED", "해당농축에이드 1.5P(45g, 계량 체크 필요) + 얼음 가득(300g) + 사이다 1EA", "블루레몬에이드\n레몬농축액 1P(30g) + 블루레몬시럽 2P(20g)"),
    ]
    for name, variants in group_hot_iced(teas):
        p.draw_item_group(item_w, kind_w, rec_w, note_w, name, variants, font_size=7.1, min_h=5.6 * mm)

    p.section_bar("JUICE / Only iced")
    p.col_header([("품목", item_w + kind_w), ("제조순서", rec_w), ("비고", note_w)])
    juices = [
        ("딸기주스", "블렌딩[정수 220g + 냉동딸기 130g + 설탕시럽 4P(40g)] + 얼음 밑선↓(200g)에 붓고 제공", "당도는 손님의 선택에 맞게 제조"),
        ("딸기바나나주스", "블렌딩[정수 220g + 냉동딸기 60g + 냉동바나나 60g + 설탕시럽 4P(40g)] + 얼음 밑선↓(200g)에 붓고 제공", ""),
        ("망고주스", "블렌딩[정수 220g + 냉동망고 130g + 설탕시럽 4P(40g)] + 얼음 밑선↓(200g)에 붓고 제공", ""),
        ("초코바나나주스", "블렌딩[우유 220g + 초코소스 1P(37g) + 냉동바나나 80g] + 얼음 밑선↓(200g)에 붓고 제공", ""),
        ("바나나주스", "블렌딩[우유 220g + 냉동바나나 110g + 설탕시럽 4P(40g)] + 얼음 밑선↓(200g)에 붓고 제공", ""),
        ("키위주스", "블렌딩[정수 220g + 냉동키위 160g + 설탕시럽 4P(40g)] + 얼음 밑선↓(200g)에 붓고 제공", "*키위주스 제조 시 씨갈림 주의*"),
        ("키위바나나주스", "블렌딩[정수 220g + 냉동키위 120g + 냉동바나나 50g + 설탕시럽 4P(40g)] + 얼음 밑선↓(200g)에 붓고 제공", ""),
    ]
    for name, rec, note in juices:
        p.draw_row(
            [
                (name, item_w + kind_w, "Bold", None, INK),
                (rec, rec_w, "Body", None, INK),
                (note, note_w, "Body", None, NOTE_RED if note else INK),
            ],
            font_size=7.1,
            min_h=5.8 * mm,
            colorize_idx=1,
        )

    p.tip_box(
        [
            "▷ 블렌디드 음료 제조 시 블렌더 볼에 (액체 → 원물 → 얼음) 투입 순서를 꼭 지켜주세요!  (★★기계 작동이 멈춘 후 볼 제거하기★★)",
            "▷ mix[ ] : 원물1 : 정수 or 온수1 배합 섞어주기     ▷ 휘핑크림 : 포모나, 약 두바퀴 반(25g)     ▷ 계량단위 : P=펌프, S=스푼, SF=스푼가득, EA=개",
            "▷ 우리기 : 티백 + 온수 / 3분     ▷ 블렌딩[ ] : 블렌디드(블렌더 활용) 음료     ▷ (벽면) : 계량 후 컵을 돌려가며 벽면에 펴발라주기     ▷ 얼음 : 가득=300g, 밑선↓=200g",
        ],
        height=16 * mm,
    )
    p.footer_bar()
    p.save()


def page3_coffee(path: Path) -> None:
    p = Page(path, landscape=True)
    p.title_header("COFFEE")
    item_w, kind_w, rec_w = 36 * mm, 16 * mm, 168 * mm
    note_w = p.content_w - item_w - kind_w - rec_w
    cols = [("품목", item_w), ("구분", kind_w), ("제조순서", rec_w), ("비고", note_w)]
    p.section_bar("COFFEE (espresso)")
    p.col_header(cols)

    rows = [
        ("에스프레소", "ICED", "2샷 기준 = 그라인딩 원두 18g + 추출 40g / 추출시간 27초", ""),
        ("아메리카노", "HOT", "온수 350g + 에스프레소 2샷", "헤이즐넛아메리카노 + 헤이즐넛시럽 3P(30g)"),
        ("", "ICED", "얼음 가득(300g) + 정수 200g + 에스프레소 2샷", ""),
        ("카페라떼", "HOT", "에스프레소 2샷 + 스팀우유 300g(우유8:거품2) - 이하 모든 라떼류 스팀 동일", "바닐라/헤이즐넛라떼 + 해당시럽 3P(30g)"),
        ("", "ICED", "얼음 가득(300g) + 우유 200g + 에스프레소 2샷", ""),
        ("카푸치노", "HOT", "에스프레소 2샷 + 스팀우유 300g(우유6:거품4)", "고객 취향에 따라 시나몬 가루 토핑"),
        ("", "ICED", "얼음 밑선(250g) + 우유 200g + 에스프레소 2샷 + 우유거품(2cm)", ""),
        ("카페모카(다크)", "HOT", "초코소스 1P(37g) + 에스프레소 2샷 + 스팀우유 300g + 휘핑크림", "ICED 휘핑 시 얼음 밑선(250g)"),
        ("", "ICED", "mix[초코소스 1P(37g) + 에스프레소 2샷] + 얼음 가득(300g) + 우유 200g + 휘핑크림", ""),
        ("연유라떼", "HOT", "연유 45g + 에스프레소 2샷 + 스팀우유 300g", "mix[ ] = 믹싱 후 음료 위에 부어주기 (이하 모든 ICED mix 동일)"),
        ("", "ICED", "mix[연유 45g + 에스프레소 2샷] + 얼음 가득(300g) + 우유 200g", ""),
        ("아인슈페너", "HOT", "온수 350g + 에스프레소 2샷 + 크림베이스 1SF(20g) + 코코초코파우더 1g(토핑)", "크림베이스 전용 스푼 사용"),
        ("", "ICED", "얼음 밑선(250g) + 정수 200g + 에스프레소 2샷 + 크림베이스 1SF(20g) + 코코초코파우더 1g(토핑)", ""),
        ("아인슈페너라떼", "HOT", "에스프레소 2샷 + 스팀우유 300g + 크림베이스 1SF(20g) + 코코초코파우더 1g(토핑)", ""),
        ("", "ICED", "얼음 밑선(250g) + 우유 200g + 에스프레소 2샷 + 크림베이스 1SF(20g) + 코코초코파우더 1g(토핑)", ""),
        ("흑당카페라떼", "ICED", "흑당시럽 30g(벽면) + 얼음 가득(300g) + 우유 200g + 에스프레소 2샷", "벽면에 베이스를 고루 펴발라주기"),
        ("카라멜마끼아또", "HOT", "카라멜소스 1P(37g) + 바닐라시럽 1P(10g) + 에스프레소 2샷 + 스팀우유 300g + 카라멜소스 드리즐(약 5g)", "#모양 드리즐"),
        ("", "ICED", "카라멜소스 1P(37g) + 바닐라시럽 1P(10g) + 얼음 밑선(250g) + 우유 200g + 에스프레소 2샷 + 우유거품(2cm) + 카라멜소스 드리즐(약 5g)", ""),
        ("콜드브루커피", "ICED", "얼음 밑선(250g) + 정수 200g + 콜드브루 원액 100g", ""),
        ("콜드브루라떼", "ICED", "얼음 밑선(250g) + 우유 200g + 콜드브루 원액 100g", ""),
    ]
    for name, variants in group_hot_iced(rows):
        p.draw_item_group(item_w, kind_w, rec_w, note_w, name, variants, font_size=7.1, min_h=5.6 * mm)

    p.tip_box(
        [
            "▷ 샷추가 : 2샷 추출 후 20g 사용     ▷ 휘핑크림 : 포모나, 두바퀴 반(약 25g)     ▷ 우유거품 : 거품기 사용(50g)     ▷ 계량단위 : P=펌프, S=스푼(플랫), SF=스푼가득",
            "▷ mix[ ] : 원물+에스프레소 배합 섞어주기     ▷ 얼음 : 밑선=250g, 가득(플랫)=300g     ▷ 계량스푼 : 갈색스푼(파우더), 거품스푼(크림)",
        ],
        height=16 * mm,
    )
    p.footer_bar()
    p.save()


def page4_noncoffee(path: Path) -> None:
    p = Page(path, landscape=True)
    p.title_header("NON-COFFEE")
    item_w, kind_w, rec_w = 38 * mm, 16 * mm, 168 * mm
    note_w = p.content_w - item_w - kind_w - rec_w
    cols = [("품목", item_w), ("구분", kind_w), ("제조순서", rec_w), ("비고", note_w)]
    p.section_bar("NON-COFFEE")
    p.col_header(cols)

    rows = [
        ("초콜릿(다크)", "HOT", "코코초코파우더 3S(45g) + 스팀우유 300g", ""),
        ("", "ICED", "mix[코코초코파우더 3S(45g) + 온수] + 얼음 가득(300g) + 우유 200g", ""),
        ("제주산말차라떼", "HOT", "녹차파우더 2S(30g) + 설탕시럽 1P(10g) + 스팀우유 300g", ""),
        ("", "ICED", "mix[녹차파우더 2S(30g) + 설탕시럽 1P(10g) + 온수] + 얼음 가득(300g) + 우유 200g", ""),
        ("고구마라떼", "HOT", "고구마페이스트 60g + 설탕시럽 1P(10g) + 스팀우유 300g", ""),
        ("", "ICED", "mix[고구마페이스트 60g + 설탕시럽 1P(10g) + 온수] + 얼음 가득(300g) + 우유 200g", ""),
        ("민트초코라떼", "HOT", "민트초코파우더 3S(45g) + 스팀우유 300g", ""),
        ("", "ICED", "mix[민트초코파우더 3S(45g) + 온수] + 얼음 가득(300g) + 우유 200g", ""),
        ("뚱바라떼", "ICED", "mix[리얼바나나파우더 3S(42g) + 온수] + 얼음 가득(300g) + 우유 200g", ""),
        ("딸기라떼", "ICED", "얼음 가득(300g) + 딸기리플잼 80g + 설탕시럽 1P(10g) + 우유 200g", ""),
        ("티라미수라떼", "HOT", "티라미수파우더 3S(33g) + 스팀우유 300g + 크림베이스 1SF(20g) + 코코초코파우더 1g(토핑)", "크림베이스 거품 스푼 사용 / 코코초코파우더 토핑은 크림베이스 덮어줌"),
        ("", "ICED", "mix[티라미수파우더 3S(33g) + 온수] + 얼음 밑선(250g) + 우유 240g + 크림베이스 1SF(20g) + 코코초코파우더 1g(토핑)", ""),
        ("미숫가루", "ICED", "정수 200g + 미숫가루파우더 5S(60g) + 얼음 가득(300g)", "온수 사용 X"),
        ("바닐라죠리퐁라떼", "ICED", "블렌딩[우유 160g + 바닐라파우더 3S(42g) + 쉐이크파우더 1S(12g) + 얼음 가득(300g)] + 죠리퐁 15g 토핑", ""),
        ("딸기죠리퐁라떼", "ICED", "블렌딩[우유 160g + 딸기리플잼 60g + 쉐이크파우더 1S(12g) + 얼음 가득(300g)] + 죠리퐁 15g 토핑", ""),
    ]
    for name, variants in group_hot_iced(rows):
        p.draw_item_group(item_w, kind_w, rec_w, note_w, name, variants, font_size=7.2, min_h=6.0 * mm)

    p.tip_box(
        [
            "▷ mix[ ] : 원물1 : 정수 or 온수1 배합 섞어주기     ▷ 우유거품 : 거품기 사용(50g)     ▷ 계량단위 : P=펌프, S=스푼(플랫), SF=스푼가득",
            "▷ 얼음 : 밑선=250g, 가득(플랫)=300g     ▷ 계량스푼 : 갈색스푼(파우더), 거품스푼(크림)",
        ],
        height=16 * mm,
    )
    p.footer_bar()
    p.save()


def merge_pdfs(paths: list[Path], out: Path) -> None:
    try:
        from pypdf import PdfWriter

        w = PdfWriter()
        for path in paths:
            w.append(str(path))
        w.write(str(out))
        return
    except Exception:
        pass
    # fallback: reportlab can't easily merge; write a note file
    print("pypdf unavailable; individual pages only")


def main() -> None:
    register_fonts()
    OUTPUT.mkdir(parents=True, exist_ok=True)
    p1 = OUTPUT / "01_기타_스무디_프라페.pdf"
    p2 = OUTPUT / "02_티_에이드_주스.pdf"
    p3 = OUTPUT / "03_커피.pdf"
    p4 = OUTPUT / "04_논커피.pdf"
    page1_smoothie(p1)
    page2_tea_juice(p2)
    page3_coffee(p3)
    page4_noncoffee(p4)
    try:
        import subprocess
        import sys

        subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "pypdf"])
    except Exception:
        pass
    merge_pdfs([p1, p2, p3, p4], OUTPUT / "카페아이엔지_메뉴레시피_수정본_A4.pdf")
    print("wrote", OUTPUT)


if __name__ == "__main__":
    main()
