#!/usr/bin/env python3
"""CAFE ING 음료교환권 — A4를 거의 채운 15매 인쇄물 생성."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / "assets"
FONTS = ROOT / "fonts"
OUTPUT = ROOT / "output"

COLS = 3
ROWS = 5
A4_W_MM = 210
A4_H_MM = 297
PAGE_MARGIN_MM = 4.0
COUPON_W_MM = (A4_W_MM - 2 * PAGE_MARGIN_MM) / COLS
COUPON_H_MM = (A4_H_MM - 2 * PAGE_MARGIN_MM) / ROWS
SCALE = COUPON_H_MM / 45.0
DPI = 300

NAVY = (26, 74, 156)
NAVY_HEX = "#1A4A9C"
RED = (195, 15, 35)
RED_HEX = "#C30F23"
BRAND_KO = "카페아이엔지 CAFE ING"
INK = (28, 28, 28)
HEADER_BG = (236, 236, 236)
FOOTER_BG = (243, 243, 243)
LINE = (50, 50, 50)
BORDER = (30, 30, 30)

HEADER_H_MM = 7.6 * SCALE
FOOTER_H_MM = 10.4 * SCALE
TITLE_PT = 13.6 * SCALE
PRICE_PT = 8.6 * SCALE
BRAND_PT = 7.35 * SCALE
PLACE_PT = 6.25 * SCALE
DRINK_H_MM = 20.2 * SCALE
LOGO_H_MM = 5.2 * SCALE
PLACE_LINE = "경삼관점, 장준하통일관점 사용가능"


def mm_to_px(mm_val: float, dpi: int = DPI) -> int:
    return int(round(mm_val / 25.4 * dpi))


def load_fonts() -> dict[str, Path]:
    return {
        "display": FONTS / "Cafe24Ssurround.ttf",
        "body": FONTS / "Pretendard-Medium.ttf",
    }


def register_pdf_fonts(paths: dict[str, Path]) -> None:
    pdfmetrics.registerFont(TTFont("Display", str(paths["display"])))
    pdfmetrics.registerFont(TTFont("Body", str(paths["body"])))


def draw_logo_pdf(c: canvas.Canvas, logo: ImageReader, x: float, y: float, w: float, header_h: float) -> None:
    logo_h = header_h * 0.68
    logo_w = logo_h * (640 / 169)
    c.drawImage(
        logo,
        x + (w - logo_w) / 2,
        y + (header_h - logo_h) / 2,
        width=logo_w,
        height=logo_h,
        mask="auto",
        preserveAspectRatio=True,
    )


def draw_coupon_pdf(c: canvas.Canvas, x: float, y: float, drink: ImageReader, logo: ImageReader) -> None:
    """Draw one coupon. (x, y) is the lower-left corner in PDF points."""
    w = COUPON_W_MM * mm
    h = COUPON_H_MM * mm
    header_h = HEADER_H_MM * mm
    footer_h = FOOTER_H_MM * mm

    def rgb(color: tuple[int, int, int]) -> tuple[float, float, float]:
        return tuple(channel / 255 for channel in color)

    c.saveState()
    c.setStrokeColorRGB(*rgb(BORDER))
    c.setLineWidth(0.45)
    c.rect(x, y, w, h, stroke=1, fill=0)

    # header
    c.setFillColorRGB(*rgb(HEADER_BG))
    c.rect(x, y + h - header_h, w, header_h, stroke=0, fill=1)
    c.setStrokeColorRGB(*rgb(LINE))
    c.setLineWidth(0.35)
    c.line(x, y + h - header_h, x + w, y + h - header_h)
    draw_logo_pdf(c, logo, x, y + h - header_h, w, header_h)

    # footer
    c.setFillColorRGB(*rgb(FOOTER_BG))
    c.rect(x, y, w, footer_h, stroke=0, fill=1)
    c.setStrokeColorRGB(*rgb(LINE))
    c.setLineWidth(0.35)
    c.line(x, y + footer_h, x + w, y + footer_h)

    c.setFillColorRGB(*rgb(RED))
    c.setFont("Display", BRAND_PT)
    c.drawCentredString(x + w / 2, y + footer_h * 0.58, BRAND_KO)

    c.setFillColorRGB(*rgb(INK))
    c.setFont("Body", PLACE_PT)
    c.drawCentredString(x + w / 2, y + footer_h * 0.28, PLACE_LINE)

    # middle: title + price vertically centered with the drink
    body_top = y + h - header_h
    body_bot = y + footer_h
    body_h = body_top - body_bot
    body_mid_x = x + w * 0.38

    title_size = TITLE_PT
    price_size = PRICE_PT
    gap = 1.2 * mm * SCALE
    title_ascent = pdfmetrics.getAscent("Display") * title_size / 1000
    title_descent = abs(pdfmetrics.getDescent("Display")) * title_size / 1000
    price_ascent = pdfmetrics.getAscent("Display") * price_size / 1000
    price_descent = abs(pdfmetrics.getDescent("Display")) * price_size / 1000
    block_h = title_ascent + title_descent + gap + price_ascent + price_descent
    block_top = body_bot + (body_h + block_h) / 2
    title_baseline = block_top - title_ascent
    price_baseline = title_baseline - title_descent - gap - price_ascent

    c.setFillColorRGB(*rgb(NAVY))
    c.setFont("Display", title_size)
    c.drawCentredString(body_mid_x, title_baseline, "음료교환권")
    c.setFont("Display", price_size)
    c.drawCentredString(body_mid_x, price_baseline, "(2,000원)")

    drink_h = DRINK_H_MM * mm
    drink_w = drink_h * (697 / 848)
    drink_x = x + w - drink_w - 2.2 * mm * SCALE
    drink_y = body_bot + (body_h - drink_h) / 2
    c.drawImage(
        drink,
        drink_x,
        drink_y,
        width=drink_w,
        height=drink_h,
        mask="auto",
        preserveAspectRatio=True,
    )

    c.restoreState()


def build_pdf(drink_path: Path, logo_path: Path, pdf_path: Path, paths: dict[str, Path]) -> None:
    register_pdf_fonts(paths)
    drink = ImageReader(str(drink_path))
    logo = ImageReader(str(logo_path))

    grid_w = COLS * COUPON_W_MM
    grid_h = ROWS * COUPON_H_MM
    left = (A4_W_MM - grid_w) / 2
    bottom = (A4_H_MM - grid_h) / 2

    c = canvas.Canvas(str(pdf_path), pagesize=(A4_W_MM * mm, A4_H_MM * mm))
    c.setTitle("CAFE ING 음료교환권 2,000원 × 15매")
    c.setAuthor("CAFE ING")

    for row in range(ROWS):
        for col in range(COLS):
            x = (left + col * COUPON_W_MM) * mm
            # PDF y grows upward; row 0 is the top row
            y = (bottom + (ROWS - 1 - row) * COUPON_H_MM) * mm
            draw_coupon_pdf(c, x, y, drink, logo)

    c.save()


def pil_font(path: Path, size_pt: float, dpi: int = DPI) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(path), int(round(size_pt / 72 * dpi)))


def render_coupon_png(
    drink_im: Image.Image, logo_im: Image.Image, paths: dict[str, Path], dpi: int = DPI
) -> Image.Image:
    w = mm_to_px(COUPON_W_MM, dpi)
    h = mm_to_px(COUPON_H_MM, dpi)
    header_h = mm_to_px(HEADER_H_MM, dpi)
    footer_h = mm_to_px(FOOTER_H_MM, dpi)

    img = Image.new("RGB", (w, h), (255, 255, 255))
    d = ImageDraw.Draw(img)

    d.rectangle((0, 0, w - 1, header_h - 1), fill=HEADER_BG)
    d.rectangle((0, h - footer_h, w - 1, h - 1), fill=FOOTER_BG)
    d.line((0, header_h, w, header_h), fill=LINE, width=max(1, mm_to_px(0.12, dpi)))
    d.line((0, h - footer_h, w, h - footer_h), fill=LINE, width=max(1, mm_to_px(0.12, dpi)))
    d.rectangle((0, 0, w - 1, h - 1), outline=BORDER, width=max(2, mm_to_px(0.16, dpi)))

    display_title = pil_font(paths["display"], TITLE_PT, dpi)
    display_price = pil_font(paths["display"], PRICE_PT, dpi)
    display_brand = pil_font(paths["display"], BRAND_PT, dpi)
    body_place = pil_font(paths["body"], PLACE_PT, dpi)

    def center_text(text: str, font: ImageFont.FreeTypeFont, cy: float, fill) -> None:
        bbox = d.textbbox((0, 0), text, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        d.text(((w - tw) / 2 - bbox[0], cy - th / 2 - bbox[1]), text, font=font, fill=fill)

    logo_h = int(header_h * 0.68)
    logo_w = int(logo_h * (logo_im.width / logo_im.height))
    logo_fitted = logo_im.resize((logo_w, logo_h), Image.Resampling.LANCZOS)
    logo_x = (w - logo_w) // 2
    logo_y = (header_h - logo_h) // 2
    img.paste(logo_fitted, (logo_x, logo_y), logo_fitted)

    body_top = header_h
    body_bot = h - footer_h
    body_h = body_bot - body_top
    left_cx = w * 0.38

    title = "음료교환권"
    price = "(2,000원)"
    title_bbox = d.textbbox((0, 0), title, font=display_title)
    price_bbox = d.textbbox((0, 0), price, font=display_price)
    gap = mm_to_px(1.2 * SCALE, dpi)
    block_h = (title_bbox[3] - title_bbox[1]) + gap + (price_bbox[3] - price_bbox[1])
    block_top = body_top + (body_h - block_h) / 2
    d.text(
        (left_cx - (title_bbox[2] - title_bbox[0]) / 2 - title_bbox[0], block_top - title_bbox[1]),
        title,
        font=display_title,
        fill=NAVY,
    )
    d.text(
        (
            left_cx - (price_bbox[2] - price_bbox[0]) / 2 - price_bbox[0],
            block_top + (title_bbox[3] - title_bbox[1]) + gap - price_bbox[1],
        ),
        price,
        font=display_price,
        fill=NAVY,
    )

    drink_h = mm_to_px(DRINK_H_MM, dpi)
    drink_w = int(drink_h * (drink_im.width / drink_im.height))
    drink = drink_im.resize((drink_w, drink_h), Image.Resampling.LANCZOS)
    dx = w - drink_w - mm_to_px(2.2 * SCALE, dpi)
    dy = body_top + (body_h - drink_h) // 2
    img.paste(drink, (dx, dy))

    center_text(BRAND_KO, display_brand, h - footer_h + footer_h * 0.36, RED)
    center_text(PLACE_LINE, body_place, h - footer_h + footer_h * 0.70, INK)
    return img


def render_a4_png(coupon: Image.Image, dpi: int = DPI) -> Image.Image:
    page = Image.new("RGB", (mm_to_px(A4_W_MM, dpi), mm_to_px(A4_H_MM, dpi)), (255, 255, 255))
    grid_w = COLS * coupon.width
    grid_h = ROWS * coupon.height
    left = (page.width - grid_w) // 2
    top = (page.height - grid_h) // 2
    for row in range(ROWS):
        for col in range(COLS):
            page.paste(coupon, (left + col * coupon.width, top + row * coupon.height))
    return page


def write_html(html_path: Path) -> None:
    html_path.write_text(
        f"""<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>CAFE ING 음료교환권 2,000원 × 15매 (A4)</title>
  <style>
    @font-face {{
      font-family: "Cafe24Ssurround";
      src: url("fonts/Cafe24Ssurround.ttf") format("truetype");
      font-weight: 700;
    }}
    @font-face {{
      font-family: "Pretendard";
      src: url("fonts/Pretendard-Medium.ttf") format("truetype");
      font-weight: 500;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    html, body {{ background: #ddd; }}
    .toolbar {{
      font-family: "Pretendard", sans-serif;
      background: #222;
      color: #fff;
      padding: 10px 16px;
      display: flex;
      gap: 12px;
      align-items: center;
      justify-content: space-between;
    }}
    .toolbar button {{
      font-family: inherit;
      font-weight: 700;
      background: {RED_HEX};
      color: #fff;
      border: 0;
      padding: 8px 14px;
      cursor: pointer;
    }}
    .sheet {{
      width: 210mm;
      height: 297mm;
      background: #fff;
      margin: 16px auto;
      padding: {(A4_H_MM - ROWS * COUPON_H_MM) / 2}mm {(A4_W_MM - COLS * COUPON_W_MM) / 2}mm;
      box-shadow: 0 4px 24px rgba(0,0,0,.25);
    }}
    .grid {{
      width: {COLS * COUPON_W_MM}mm;
      height: {ROWS * COUPON_H_MM}mm;
      display: grid;
      grid-template-columns: repeat({COLS}, {COUPON_W_MM}mm);
      grid-template-rows: repeat({ROWS}, {COUPON_H_MM}mm);
    }}
    .coupon {{
      width: {COUPON_W_MM}mm;
      height: {COUPON_H_MM}mm;
      border: 0.35pt solid #1e1e1e;
      display: flex;
      flex-direction: column;
      background: #fff;
      overflow: hidden;
    }}
    .header {{
      height: {HEADER_H_MM}mm;
      background: #ececec;
      border-bottom: 0.35pt solid #323232;
      display: flex;
      align-items: center;
      justify-content: center;
    }}
    .header .logo {{
      height: {LOGO_H_MM}mm;
      width: auto;
      display: block;
    }}
    .body {{
      flex: 1;
      display: flex;
      align-items: center;
      min-height: 0;
      padding: 0 1.6mm 0 1.2mm;
    }}
    .copy {{
      flex: 1;
      height: 100%;
      display: flex;
      flex-direction: column;
      justify-content: center;
      align-items: center;
      text-align: center;
      color: {NAVY_HEX};
      font-family: "Cafe24Ssurround", sans-serif;
      font-weight: 700;
    }}
    .copy h2 {{
      font-size: {TITLE_PT}pt;
      line-height: 1.15;
      font-weight: 700;
    }}
    .copy p {{
      font-size: {PRICE_PT}pt;
      margin-top: {0.8 * SCALE}mm;
    }}
    .drink {{
      height: {DRINK_H_MM}mm;
      width: auto;
      max-width: 42%;
      object-fit: contain;
      display: block;
      flex-shrink: 0;
    }}
    .footer {{
      height: {FOOTER_H_MM}mm;
      background: #f3f3f3;
      border-top: 0.35pt solid #323232;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      gap: 0.7mm;
      font-family: "Cafe24Ssurround", "Pretendard", sans-serif;
      text-align: center;
      padding: 0 1.5mm;
    }}
    .footer .brand {{
      color: {RED_HEX};
      font-family: "Cafe24Ssurround", sans-serif;
      font-weight: 700;
      font-size: {BRAND_PT}pt;
    }}
    .footer .place {{
      color: #1c1c1c;
      font-family: "Pretendard", sans-serif;
      font-size: {PLACE_PT}pt;
    }}
    @media print {{
      @page {{ size: A4; margin: 0; }}
      html, body {{ background: #fff; }}
      .toolbar {{ display: none; }}
      .sheet {{
        margin: 0;
        box-shadow: none;
        width: 210mm;
        height: 297mm;
      }}
    }}
  </style>
</head>
<body>
  <div class="toolbar">
    <div>CAFE ING 음료교환권 (2,000원) · 1매 {COUPON_W_MM:.1f}×{COUPON_H_MM:.1f}mm · A4 15매</div>
    <button type="button" onclick="window.print()">인쇄 / PDF 저장</button>
  </div>
  <div class="sheet">
    <div class="grid">
      {"".join(coupon_html() for _ in range(COLS * ROWS))}
    </div>
  </div>
</body>
</html>
""",
        encoding="utf-8",
    )


def coupon_html() -> str:
    return """
      <article class="coupon">
        <header class="header"><img class="logo" src="assets/cafe-ing-logo.png" alt="cafe ing" /></header>
        <div class="body">
          <div class="copy">
            <h2>음료교환권</h2>
            <p>(2,000원)</p>
          </div>
          <img class="drink" src="assets/iced-americano.png" alt="아이스 아메리카노" />
        </div>
        <footer class="footer">
          <div class="brand">카페아이엔지 CAFE ING</div>
          <div class="place">경삼관점, 장준하통일관점 사용가능</div>
        </footer>
      </article>
    """


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    paths = load_fonts()
    drink_path = ASSETS / "iced-americano.png"
    logo_path = ASSETS / "cafe-ing-logo.png"
    drink_im = Image.open(drink_path).convert("RGB")
    logo_im = Image.open(logo_path).convert("RGBA")

    pdf_path = OUTPUT / "CAFE_ING_음료교환권_2000원_A4_15매.pdf"
    build_pdf(drink_path, logo_path, pdf_path, paths)

    coupon = render_coupon_png(drink_im, logo_im, paths)
    coupon.save(OUTPUT / "coupon-single.png")
    page = render_a4_png(coupon)
    page.save(OUTPUT / "A4-15매-preview.png")
    # smaller web preview
    page.resize((page.width // 3, page.height // 3), Image.Resampling.LANCZOS).save(
        OUTPUT / "A4-15매-preview-small.jpg", quality=88
    )

    write_html(ROOT / "index.html")
    print(f"PDF: {pdf_path}")
    print(f"HTML: {ROOT / 'index.html'}")


if __name__ == "__main__":
    main()
