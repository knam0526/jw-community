#!/usr/bin/env python3
"""CAFE ING 음료교환권 — 60×45mm × 15매 A4 인쇄물 생성."""

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

COUPON_W_MM = 60
COUPON_H_MM = 45
COLS = 3
ROWS = 5
A4_W_MM = 210
A4_H_MM = 297
DPI = 300

NAVY = (26, 74, 156)
NAVY_HEX = "#1A4A9C"
RED = (192, 23, 42)
RED_HEX = "#C0172A"
INK = (28, 28, 28)
HEADER_BG = (236, 236, 236)
FOOTER_BG = (243, 243, 243)
LINE = (50, 50, 50)
BORDER = (30, 30, 30)

HEADER_H_MM = 7.6
FOOTER_H_MM = 10.4


def mm_to_px(mm_val: float, dpi: int = DPI) -> int:
    return int(round(mm_val / 25.4 * dpi))


def load_fonts() -> dict[str, Path]:
    return {
        "gothic": FONTS / "NanumGothic.ttf",
        "gothic_bold": FONTS / "NanumGothicBold.ttf",
        "square_bold": FONTS / "NanumSquareB.ttf",
    }


def register_pdf_fonts(paths: dict[str, Path]) -> None:
    pdfmetrics.registerFont(TTFont("Gothic", str(paths["gothic"])))
    pdfmetrics.registerFont(TTFont("GothicBold", str(paths["gothic_bold"])))
    pdfmetrics.registerFont(TTFont("SquareBold", str(paths["square_bold"])))


def draw_coupon_pdf(c: canvas.Canvas, x: float, y: float, drink: ImageReader) -> None:
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

    c.setFillColorRGB(*rgb(INK))
    c.setFont("SquareBold", 11)
    c.drawCentredString(x + w / 2, y + h - header_h + 2.35 * mm, "CAFE ING")

    # footer
    c.setFillColorRGB(*rgb(FOOTER_BG))
    c.rect(x, y, w, footer_h, stroke=0, fill=1)
    c.setStrokeColorRGB(*rgb(LINE))
    c.setLineWidth(0.35)
    c.line(x, y + footer_h, x + w, y + footer_h)

    c.setFillColorRGB(*rgb(RED))
    c.setFont("GothicBold", 7.1)
    c.drawCentredString(x + w / 2, y + footer_h - 4.15 * mm, "카페아이앤지 CAFE ING")

    c.setFillColorRGB(*rgb(INK))
    c.setFont("Gothic", 6.15)
    c.drawCentredString(x + w / 2, y + 3.15 * mm, "경삼관, 장준하통일관점 사용가능")

    # middle: title + price + drink
    body_top = y + h - header_h
    body_bot = y + footer_h
    body_h = body_top - body_bot
    body_mid_x = x + w * 0.38

    c.setFillColorRGB(*rgb(NAVY))
    c.setFont("GothicBold", 13.2)
    title_y = body_bot + body_h / 2 + 1.55 * mm
    c.drawCentredString(body_mid_x, title_y, "음료교환권")
    c.setFont("GothicBold", 8.4)
    c.drawCentredString(body_mid_x, title_y - 4.35 * mm, "(2,000원)")

    drink_h = 20.2 * mm
    drink_w = drink_h * (697 / 848)
    drink_x = x + w - drink_w - 2.2 * mm
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


def build_pdf(drink_path: Path, pdf_path: Path, paths: dict[str, Path]) -> None:
    register_pdf_fonts(paths)
    drink = ImageReader(str(drink_path))

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
            draw_coupon_pdf(c, x, y, drink)

    c.save()


def pil_font(path: Path, size_pt: float, dpi: int = DPI) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(path), int(round(size_pt / 72 * dpi)))


def render_coupon_png(drink_im: Image.Image, paths: dict[str, Path], dpi: int = DPI) -> Image.Image:
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

    square = pil_font(paths["square_bold"], 11, dpi)
    gothic_b = pil_font(paths["gothic_bold"], 13.2, dpi)
    gothic_price = pil_font(paths["gothic_bold"], 8.4, dpi)
    gothic_red = pil_font(paths["gothic_bold"], 7.1, dpi)
    gothic = pil_font(paths["gothic"], 6.15, dpi)

    def center_text(text: str, font: ImageFont.FreeTypeFont, cy: float, fill) -> None:
        bbox = d.textbbox((0, 0), text, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        d.text(((w - tw) / 2 - bbox[0], cy - th / 2 - bbox[1]), text, font=font, fill=fill)

    center_text("CAFE ING", square, header_h / 2, INK)

    body_top = header_h
    body_bot = h - footer_h
    body_h = body_bot - body_top
    left_cx = w * 0.38

    title = "음료교환권"
    price = "(2,000원)"
    title_bbox = d.textbbox((0, 0), title, font=gothic_b)
    price_bbox = d.textbbox((0, 0), price, font=gothic_price)
    title_h = title_bbox[3] - title_bbox[1]
    price_h = price_bbox[3] - price_bbox[1]
    gap = mm_to_px(1.1, dpi)
    block_h = title_h + gap + price_h
    block_top = body_top + (body_h - block_h) / 2
    d.text(
        (left_cx - (title_bbox[2] - title_bbox[0]) / 2 - title_bbox[0], block_top - title_bbox[1]),
        title,
        font=gothic_b,
        fill=NAVY,
    )
    d.text(
        (
            left_cx - (price_bbox[2] - price_bbox[0]) / 2 - price_bbox[0],
            block_top + title_h + gap - price_bbox[1],
        ),
        price,
        font=gothic_price,
        fill=NAVY,
    )

    drink_h = mm_to_px(20.2, dpi)
    drink_w = int(drink_h * (drink_im.width / drink_im.height))
    drink = drink_im.resize((drink_w, drink_h), Image.Resampling.LANCZOS)
    dx = w - drink_w - mm_to_px(2.2, dpi)
    dy = body_top + (body_h - drink_h) // 2
    img.paste(drink, (dx, dy))

    center_text("카페아이앤지 CAFE ING", gothic_red, h - footer_h + footer_h * 0.36, RED)
    center_text("경삼관, 장준하통일관점 사용가능", gothic, h - footer_h + footer_h * 0.70, INK)
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
      font-family: "NanumGothic";
      src: url("fonts/NanumGothic.ttf") format("truetype");
      font-weight: 400;
    }}
    @font-face {{
      font-family: "NanumGothic";
      src: url("fonts/NanumGothicBold.ttf") format("truetype");
      font-weight: 700;
    }}
    @font-face {{
      font-family: "NanumSquare";
      src: url("fonts/NanumSquareB.ttf") format("truetype");
      font-weight: 700;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    html, body {{ background: #ddd; }}
    .toolbar {{
      font-family: "NanumGothic", sans-serif;
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
      font-family: "NanumSquare", "NanumGothic", sans-serif;
      font-weight: 700;
      font-size: 11pt;
      letter-spacing: 0.04em;
      color: #1c1c1c;
    }}
    .body {{
      flex: 1;
      display: grid;
      grid-template-columns: 1.15fr 0.85fr;
      align-items: center;
      min-height: 0;
      padding: 0 1.6mm 0 1.2mm;
    }}
    .copy {{
      text-align: center;
      color: {NAVY_HEX};
      font-family: "NanumGothic", sans-serif;
      font-weight: 700;
    }}
    .copy h2 {{
      font-size: 13.2pt;
      line-height: 1.15;
      font-weight: 700;
    }}
    .copy p {{
      font-size: 8.4pt;
      margin-top: 0.8mm;
    }}
    .drink {{
      height: 20.2mm;
      width: auto;
      max-width: 100%;
      object-fit: contain;
      display: block;
      margin: 0 auto;
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
      font-family: "NanumGothic", sans-serif;
      text-align: center;
      padding: 0 1.5mm;
    }}
    .footer .brand {{
      color: {RED_HEX};
      font-weight: 700;
      font-size: 7.1pt;
    }}
    .footer .place {{
      color: #1c1c1c;
      font-size: 6.15pt;
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
    <div>CAFE ING 음료교환권 (2,000원) · 1매 60×45mm · A4 15매</div>
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
        <header class="header">CAFE ING</header>
        <div class="body">
          <div class="copy">
            <h2>음료교환권</h2>
            <p>(2,000원)</p>
          </div>
          <img class="drink" src="assets/iced-americano.png" alt="아이스 아메리카노" />
        </div>
        <footer class="footer">
          <div class="brand">카페아이앤지 CAFE ING</div>
          <div class="place">경삼관, 장준하통일관점 사용가능</div>
        </footer>
      </article>
    """


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    paths = load_fonts()
    drink_path = ASSETS / "iced-americano.png"
    drink_im = Image.open(drink_path).convert("RGB")

    pdf_path = OUTPUT / "CAFE_ING_음료교환권_2000원_A4_15매.pdf"
    build_pdf(drink_path, pdf_path, paths)

    coupon = render_coupon_png(drink_im, paths)
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
