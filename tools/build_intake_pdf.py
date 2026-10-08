"""Build the fillable Bid Profile PDF (img/.. -> downloads/contract-ladder-bid-profile.pdf).
Clients download it, fill it in any PDF reader (Adobe Reader, Edge, Chrome, Preview), save, come back, and email it back."""
import os
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor, white
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'downloads', 'contract-ladder-bid-profile.pdf')
os.makedirs(os.path.dirname(OUT), exist_ok=True)
pdfmetrics.registerFont(TTFont('Sans', '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'))
pdfmetrics.registerFont(TTFont('SansB', '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'))
pdfmetrics.registerFont(TTFont('Cond', os.path.join(ROOT, 'tools', 'fonts', 'BarlowCondensed-ExtraBold.ttf')))

INK, MUTED, LINE, ACCENT, DEEP, FILL = HexColor('#151a18'), HexColor('#5b655f'), HexColor('#c9ccc5'), HexColor('#e8a600'), HexColor('#151a18'), HexColor('#f4f6f2')
W, H = A4
M = 42
CW = W - 2 * M

class Form:
    def __init__(self, path):
        self.c = canvas.Canvas(path, pagesize=A4)
        self.c.setTitle('Contract Ladder: Your Bid Profile')
        self.c.setAuthor('Contract Ladder (Tactics Automation Limited)')
        self.c.setSubject('Fillable bid profile for trades and construction firms')
        self.page = 0
        self.names = set()
        self.new_page()

    def new_page(self):
        if self.page: self.footer(); self.c.showPage()
        self.page += 1
        c = self.c
        c.setFillColor(DEEP); c.rect(0, H - 44, W, 44, stroke=0, fill=1)
        # logo: amber tile, three dark bars stepping up to the right (48-unit grid), name stacked beside it
        t = 28; u = t / 48.0; x0, y0 = M, H - 34
        c.setFillColor(ACCENT); c.roundRect(x0, y0, t, t, 3 * u, stroke=0, fill=1)
        c.setFillColor(INK)
        for bx, by in ((8, 31), (14, 20.5), (20, 10)):
            c.rect(x0 + bx * u, y0 + (48 - by - 7) * u, 21 * u, 7 * u, stroke=0, fill=1)
        fs = t * 0.56; tx = x0 + t + t * 0.2
        c.setFillColor(white); c.setFont('Cond', fs)
        c.drawString(tx, y0 + t - fs * 0.78, 'CONTRACT'); c.drawString(tx, y0 + t - fs * 0.78 - fs * 0.86, 'LADDER')
        c.setFont('Sans', 8.5); c.setFillColor(HexColor('#b9c2bc')); c.drawRightString(W - M, H - 26, 'Your bid profile')
        self.y = H - 70

    def footer(self):
        c = self.c
        c.setFont('Sans', 7.5); c.setFillColor(MUTED)
        c.drawString(M, 24, 'Contract Ladder is a trading name of Tactics Automation Limited, company no. 16356318. Return to luke@contractladder.co.uk')
        c.drawRightString(W - M, 24, 'Page %d' % self.page)

    def need(self, h):
        if self.y - h < 50: self.new_page()

    def text(self, s, size=9.5, font='Sans', color=MUTED, lead=13, width=CW, x=M):
        c = self.c
        words, line = s.split(), ''
        lines = []
        for w in words:
            t = (line + ' ' + w).strip()
            if pdfmetrics.stringWidth(t, font, size) > width: lines.append(line); line = w
            else: line = t
        if line: lines.append(line)
        self.need(len(lines) * lead + 4)
        c.setFont(font, size); c.setFillColor(color)
        for ln in lines:
            c.drawString(x, self.y, ln); self.y -= lead

    def section(self, n, title, why):
        self.need(70)
        self.y -= 10
        c = self.c
        c.setFillColor(ACCENT); c.rect(M, self.y - 2, 4, 20, stroke=0, fill=1)
        c.setFont('Cond', 15); c.setFillColor(INK); c.drawString(M + 12, self.y + 2, ('%s  ' % n if n else '') + title.upper())
        self.y -= 18
        self.text(why)
        self.y -= 6

    def uniq(self, name):
        base, i = name, 2
        while name in self.names: name = '%s_%d' % (base, i); i += 1
        self.names.add(name); return name

    def field(self, name, label, x, w, h=20, multiline=False, hint=''):
        c = self.c
        c.setFont('SansB', 8.5); c.setFillColor(INK); c.drawString(x, self.y, label)
        if hint:
            lw = pdfmetrics.stringWidth(label, 'SansB', 8.5)
            c.setFont('Sans', 7.5); c.setFillColor(MUTED); c.drawString(x + lw + 6, self.y, hint)
        fy = self.y - 5 - h
        c.acroForm.textfield(name=self.uniq(name), tooltip=label, x=x, y=fy, width=w, height=h,
                             borderColor=LINE, fillColor=FILL, textColor=INK, forceBorder=True,
                             fontName='Helvetica', fontSize=0 if multiline else 10,
                             fieldFlags='multiline' if multiline else '', borderWidth=0.8)
        return fy

    def row(self, items):
        """items: list of (name, label, hint) laid out across the width."""
        self.need(42)
        gap = 12
        w = (CW - gap * (len(items) - 1)) / len(items)
        low = self.y
        for i, it in enumerate(items):
            name, label = it[0], it[1]; hint = it[2] if len(it) > 2 else ''
            fy = self.field(name, label, M + i * (w + gap), w, hint=hint)
            low = min(low, fy)
        self.y = low - 12

    def box(self, name, label, h=52, hint=''):
        self.need(h + 22)
        fy = self.field(name, label, M, CW, h=h, multiline=True, hint=hint)
        self.y = fy - 12

    def checks(self, prefix, labels, cols=3):
        c = self.c
        w = CW / cols
        rows = (len(labels) + cols - 1) // cols
        self.need(rows * 18 + 6)
        for i, lab in enumerate(labels):
            r, k = divmod(i, cols)
            x, y = M + k * w, self.y - r * 18
            c.acroForm.checkbox(name=self.uniq('%s_%02d' % (prefix, i)), tooltip=lab, x=x, y=y - 3, size=11,
                                buttonStyle='check', borderColor=LINE, fillColor=FILL, textColor=INK, forceBorder=True, borderWidth=0.8)
            c.setFont('Sans', 8.5); c.setFillColor(INK); c.drawString(x + 16, y, lab)
        self.y -= rows * 18 + 8

    def radio(self, group, options):
        c = self.c
        for val, title, desc in options:
            self.need(40)
            c.acroForm.radio(name=group, value=val, tooltip=title, x=M, y=self.y - 4, size=12, buttonStyle='circle',
                             borderColor=LINE, fillColor=FILL, textColor=INK, forceBorder=True, borderWidth=0.8, selected=False)
            c.setFont('SansB', 9); c.setFillColor(INK); c.drawString(M + 20, self.y, title)
            self.y -= 13
            self.text(desc, size=8.5, x=M + 20, width=CW - 20, lead=11)
            self.y -= 6

    def save(self):
        self.footer(); self.c.save()


f = Form(OUT)
c = f.c
c.setFont('Cond', 26); c.setFillColor(INK); c.drawString(M, f.y - 6, 'YOUR BID PROFILE'); f.y -= 30
f.text('Tell us about your firm once. We use it to write every bid for you, so you are never asked the same questions twice.', size=10.5, color=INK, lead=15)
f.y -= 4
for line in ['1.  Save this PDF to your computer first, then open it in Adobe Reader, Edge, Chrome or Preview.',
             '2.  Fill in what you can. Click Save (Ctrl+S / Cmd+S) any time and come back to it later.',
             '3.  Leave out anything you don\'t have. We\'ll tell you if it matters for a tender.',
             '4.  Email the saved PDF to luke@contractladder.co.uk with your certificates and policies attached.']:
    f.text(line, size=9, color=INK, lead=13)
f.y -= 2
f.text('Nothing is invented: we only ever write what is true about your firm, from what you give us here.', size=8.5)

f.section('1', 'Your company', 'Goes on the cover of every bid and the buyer\'s supplier forms.')
f.row([('company_name', 'Registered company name'), ('company_number', 'Company number')])
f.row([('vat_number', 'VAT number', 'if registered'), ('years_trading', 'Years trading'), ('employees', 'Employees')])
f.box('registered_address', 'Registered address', h=36)
f.row([('contact_name', 'Main contact for bids', 'name and role'), ('contact_phone', 'Phone')])
f.row([('contact_email', 'Email'), ('website', 'Website')])
f.row([('turnover', 'Turnover last year (£)', 'roughly is fine'), ('job_size', 'Job size you like', 'e.g. £20k–£250k')])

f.section('2', 'What you do and where', 'So we only bring you tenders you can win.')
f.box('trades', 'Your trades', hint='e.g. car park surfacing, footpaths, drainage')
f.box('areas', 'Where you work', hint='towns, postcodes or "within 40 miles of ..."')
f.box('clients_now', 'Who you work for now', hint='e.g. retail parks, schools, housing associations, main contractors')

f.section('3', 'Insurance', 'Almost every tender sets minimum levels. Below them, the bid is thrown out.')
f.row([('el_amount', "Employer's liability (£)", 'usually £5m or £10m'), ('el_renewal', 'Renewal date')])
f.row([('pl_amount', 'Public liability (£)', 'often £5m or £10m asked'), ('pl_renewal', 'Renewal date')])
f.row([('pi_amount', 'Professional indemnity (£)', 'only if you design'), ('other_cover', 'Contract works / other cover')])

f.section('4', 'Accreditations and memberships', 'Tick what you hold. They save pages of health and safety questions.')
f.checks('acc', ['CHAS', 'SafeContractor', 'Constructionline Silver', 'Constructionline Gold', 'SMAS Worksafe', 'Acclaim',
                 'ISO 9001 (quality)', 'ISO 14001 (environment)', 'ISO 45001 (safety)', 'Gas Safe', 'NICEIC / NAPIT',
                 'LOLER / SAFed (lifts)', 'NFDC (demolition)', 'Licensed asbestos', 'Considerate Constructors'])
f.box('acc_other', 'Anything else, and expiry dates', h=36)

f.section('5', 'Policies and safety record', 'Tick what you already have. Missing ones can be written for you as part of a Bid Library.')
f.checks('pol', ['Health and safety policy', 'RAMS', 'Quality policy', 'Environmental policy', 'Equality and diversity',
                 'Modern slavery statement', 'Data protection (GDPR)', 'Safeguarding', 'Business continuity', 'Anti-bribery'])
f.row([('riddor_3yrs', 'RIDDOR incidents, last 3 years', 'a number, even 0'), ('hse_notices', 'HSE notices in 3 years?', 'yes / no')])
f.box('site_cards', 'Site cards your team hold', h=36, hint='e.g. 6 CSCS, 2 SMSTS, 1 SSSTS, first aiders')

f.section('6', 'Your key people', 'Buyers score who will run the job. Real names and real experience score best.')
f.box('person_1', 'Person 1', h=46, hint='name, role, years in the trade, qualifications')
f.box('person_2', 'Person 2 (optional)', h=46)

f.section('7', 'Three past jobs', 'The strongest evidence in any bid. Private clients count. Pick jobs closest to what you want to win.')
for j in (1, 2, 3):
    f.need(190)
    c.setFont('SansB', 10); c.setFillColor(INK); c.drawString(M, f.y, 'Job %d' % j); f.y -= 16
    f.row([('job%d_client' % j, 'Client'), ('job%d_where' % j, 'Where')])
    f.row([('job%d_value' % j, 'Value (£)'), ('job%d_when' % j, 'When finished', 'month and year')])
    f.box('job%d_what' % j, 'What you did and how it went', h=50, hint='size, tricky bits, on time and budget?')
    f.row([('job%d_referee' % j, 'Referee name and role'), ('job%d_referee_contact' % j, 'Referee phone or email')])

f.section('8', 'Social value and environment', 'Usually 5–20% of the quality marks. We only claim what you really do.')
f.row([('staff_local', 'Staff living within 15 miles of your yard'), ('apprentices', 'Apprentices or trainees')])
f.box('local_suppliers', 'Local suppliers you use', h=36)
f.box('community', 'Community or charity work', h=36, hint='e.g. sponsoring a local team, school visits')
f.box('green', 'Environmental steps', h=36, hint='e.g. recycling, electric vans, low-carbon materials')

f.section('9', 'Pricing', 'On many quotations price is 60–80% of the marks. Choose how you want it handled.')
f.radio('pricing_choice', [
    ('rates', 'Use my rates, you build the price', 'Fill in your rates below. We build and check the full pricing schedule for each tender; you approve the total before anything is sent.'),
    ('self', "I'll fill the pricing in myself", "We send you the buyer's pricing form with notes on each line, then check yours adds up and matches the written answers.")])
f.row([('rate_labourer', 'Labourer day rate (£)'), ('rate_operative', 'Skilled operative day rate (£)'), ('rate_supervisor', 'Supervisor day rate (£)')])
f.row([('markup_materials', 'Materials markup (%)'), ('overheads_profit', 'Overheads and profit (%)'), ('smallest_job', 'Smallest job worth it (£)')])
f.box('plant_rates', 'Main plant hire rates', h=36, hint='e.g. 6t excavator £x/day')
f.box('pricing_notes', 'Anything else about how you price', h=36)

f.need(250)
f.section('', 'Check and send', 'Tick to confirm, save the PDF, then email it to luke@contractladder.co.uk with these attached:')
for d in ['Insurance certificates (all policies)', 'Accreditation certificates', 'Health and safety policy, and any other policies you ticked',
          'One example RAMS from a recent job', 'Photos of the three past jobs (optional, but they help)']:
    f.text('•  ' + d, size=9, color=INK, lead=13)
f.y -= 6
f.checks('confirm', ["Everything above is true, and I'm happy for Contract Ladder to use it to write bids for my company."], cols=1)
f.row([('signed_name', 'Your name'), ('signed_date', 'Date')])
f.save()
print(OUT, f.page, 'pages,', len(f.names), 'fields')
