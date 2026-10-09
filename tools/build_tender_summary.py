"""Build a one-page Contract Ladder tender summary PDF for a firm that replied "yes".

Usage: python3 tools/build_tender_summary.py summary.json out.pdf

summary.json keys (all strings unless noted; only use facts from the notice or tender pack, never invent):
  firm            "J.C. Surfacing Ltd"
  date            "9 October 2026"            (date prepared)
  title           "Resurfacing of Blatherwick's Yard car park, Arnold"
  subline         "Gedling Borough Council · Ref CON005822 · Arnold, NG5 7FP"
  facts           [[label, value], ...] exactly 6, e.g. VALUE, INC VAT, WORKS, ROUTE, QUESTIONS BY, CLOSES
  call            "BID" | "CHECK" | "DON'T BOTHER"
  call_reason     one or two sentences
  want            [paragraph, ...]   what the buyer wants
  score           [paragraph, ...]   how they'll score it
  missing         [bullet, ...]      what the firm might be missing (3-5)
  offer           "Fixed £595 + VAT for this quotation. Turned round in 3 working days. You check it and press submit."
  source          "Find a Tender notice 2026/S 000-092527, published 30 Sep 2026."
"""
import os, sys, json
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor, white
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import simpleSplit

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
pdfmetrics.registerFont(TTFont('Cond', os.path.join(ROOT, 'tools', 'fonts', 'BarlowCondensed-ExtraBold.ttf')))
INK = HexColor('#151A18'); CAB = HexColor('#1B2421'); AMB = HexColor('#E8A600'); PAPER = HexColor('#F3F4F1')
GO = HexColor('#2F7D4F'); RED = HexColor('#B3372B'); DEEP = HexColor('#9C6B00'); CON = HexColor('#C9CCC5'); MUT = HexColor('#5B655F')
W, H = A4; M = 40; CW = W - 2 * M


def build(d, out):
    c = canvas.Canvas(out, pagesize=A4, pageCompression=1)
    c.setTitle('Tender summary: ' + d['title']); c.setAuthor('Contract Ladder')
    c.setFillColor(PAPER); c.rect(0, 0, W, H, stroke=0, fill=1)
    c.setFillColor(INK); c.rect(0, H - 70, W, 70, stroke=0, fill=1)
    t = 34; u = t / 48; x0, y0 = M, H - 52
    c.setFillColor(AMB); c.roundRect(x0, y0, t, t, 3 * u, stroke=0, fill=1); c.setFillColor(INK)
    for bx, by in ((8, 31), (14, 20.5), (20, 10)):
        c.rect(x0 + bx * u, y0 + (48 - by - 7) * u, 21 * u, 7 * u, stroke=0, fill=1)
    fs = t * 0.56; tx = x0 + t + t * 0.2; c.setFillColor(white); c.setFont('Cond', fs)
    c.drawString(tx, y0 + t - fs * 0.78, 'CONTRACT'); c.drawString(tx, y0 + t - fs * 0.78 - fs * 0.86, 'LADDER')
    c.setFont('Cond', 22); c.setFillColor(AMB); c.drawRightString(W - M, H - 38, 'TENDER SUMMARY')
    c.setFont('Helvetica', 9); c.setFillColor(HexColor('#B9C2BC'))
    c.drawRightString(W - M, H - 54, 'Prepared for %s · %s' % (d['firm'], d['date']))
    y = H - 102
    c.setFillColor(INK)
    for i, ln in enumerate(simpleSplit(d['title'].upper(), 'Cond', 21, CW)):
        c.setFont('Cond', 21); c.drawString(M, y, ln); y -= 22
    y += 6
    c.setFont('Helvetica', 10); c.setFillColor(MUT); c.drawString(M, y, d['subline']); y -= 16
    bh = 40; bw = (CW - 10) / 3
    for k, (l, v) in enumerate(d['facts'][:6]):
        col = k % 3; row = k // 3; bx = M + col * (bw + 5); by = y - (row + 1) * bh - row * 5
        c.setFillColor(white); c.setStrokeColor(CON); c.roundRect(bx, by, bw, bh, 3, stroke=1, fill=1)
        c.setFont('Courier-Bold', 7.5); c.setFillColor(MUT); c.drawString(bx + 10, by + bh - 14, l.upper())
        c.setFont('Courier-Bold', 10.5); c.setFillColor(DEEP if l.upper() == 'CLOSES' else INK); c.drawString(bx + 10, by + 10, v)
    y -= 2 * bh + 5 + 16
    call = d['call'].upper(); col = {'BID': GO, 'CHECK': AMB}.get(call, RED)
    c.setFillColor(col); c.roundRect(M, y - 50, CW, 50, 4, stroke=0, fill=1)
    txt = INK if call == 'CHECK' else white
    c.setFillColor(txt); c.setFont('Cond', 20); c.drawString(M + 14, y - 30, 'OUR CALL: ' + call)
    c.setFont('Helvetica', 9.8)
    for i, w in enumerate(simpleSplit(d['call_reason'], 'Helvetica', 9.8, CW - 175)[:3]):
        c.drawString(M + 165, y - 20 - i * 13, w)
    y -= 72

    def section(title, lines, y, bullet=False):
        c.setFillColor(INK); c.setFont('Cond', 15); c.drawString(M, y, title); y -= 4
        c.setStrokeColor(AMB); c.setLineWidth(2); c.line(M, y, M + 40, y); y -= 14
        c.setFont('Helvetica', 9.8); c.setFillColor(INK)
        for ln in lines:
            ind = 14 if bullet else 0
            for i, w in enumerate(simpleSplit(ln, 'Helvetica', 9.8, CW - ind)):
                if bullet and i == 0: c.drawString(M, y, '•')
                c.drawString(M + ind, y, w); y -= 13.5
            y -= 3
        return y - 6
    y = section('WHAT THEY WANT', d['want'], y)
    y = section("HOW THEY'LL SCORE IT", d['score'], y)
    y = section('WHAT YOU MIGHT BE MISSING', d['missing'], y, bullet=True)
    if y < 120: raise SystemExit('Too long for one page: shorten the text (y=%d)' % y)
    c.setFillColor(CAB); c.roundRect(M, 58, CW, 46, 4, stroke=0, fill=1)
    c.setFillColor(AMB); c.setFont('Cond', 14); c.drawString(M + 14, 84, 'WANT US TO WRITE IT?')
    c.setFillColor(white); c.setFont('Helvetica', 9.5); c.drawString(M + 14, 68, d['offer'])
    c.setFont('Helvetica', 7.5); c.setFillColor(MUT)
    c.drawString(M, 34, 'Source: %s Check the tender documents before bidding.' % d['source'])
    c.drawString(M, 24, 'Contract Ladder is a trading name of Tactics Automation Limited. Registered in England & Wales, company no. 16356318. luke@contractladder.co.uk')
    c.save()


if __name__ == '__main__':
    build(json.load(open(sys.argv[1])), sys.argv[2])
    print('Wrote', sys.argv[2])
