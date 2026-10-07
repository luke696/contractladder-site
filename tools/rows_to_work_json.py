"""Build data/work.json from tools/raw_rows.txt (pipe rows exported from the Find a Tender pull).
Row: id|title|buyer|region code|locality|value £|closes ISO|call code|trade indexes|sme
Keeps hand-written entries already in work.json (richer 'why') when ids match."""
import json, os, re
from datetime import datetime, timezone
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REG = {'NE':'North East','NW':'North West','YH':'Yorkshire and the Humber','EM':'East Midlands','WM':'West Midlands','EE':'East of England',
       'LO':'London','SE':'South East','SW':'South West','WA':'Wales','SC':'Scotland','NI':'Northern Ireland','':'UK-wide'}
ORDER = list(REG.values())
TR = ['Building & refurbishment','Maintenance & repairs','Heating & plumbing','Electrical & renewables','Roofing & cladding',
      'Surfacing & groundworks','Grounds & landscaping','Lifts','Demolition','Fencing','Plant hire']
WHY = {'L':('check','A large contract. Usually needs strong turnover and track record; smaller firms do better on lots or as a named subcontractor.'),
       'F':('check','A framework or approved list. Getting on it is the hard part; after that, work is called off for years.'),
       'S':('bid','Marked by the buyer as suitable for small firms. A realistic one to go for.'),
       'B':('bid','A single job at a size a small or medium firm can win.'),
       'C':('check','Check the size, insurance levels and experience they ask for before deciding.')}
DROP = re.compile(r'office furniture|power purchase|estate management services|archaeolog|ecologist|contact centre|architectural services|AV hardware|festive gardens|CCTV|hydro turbine|Zimbabwe|T(ü|u)rkiye|Istanbul|Venice|cleaning|removal services|seating replacement|training container|dental decontamination|x-ray room|laundry', re.I)
def money(v):
    if not v or v < 1000: return ''
    if v >= 1_000_000: return '£%sm' % ('%.1f' % (v/1e6)).rstrip('0').rstrip('.')
    return '£{:,}'.format(int(round(v, -3)))
wj = json.load(open(os.path.join(ROOT,'data','work.json')))
keep = {t['id']: t for t in wj['tenders']}
now = datetime.now(timezone.utc)
out = {}
for line in open(os.path.join(ROOT,'tools','raw_rows.txt'), encoding='utf-8'):
    p = line.rstrip('\n').split('|')
    if len(p) < 10: continue
    nid, title, buyer, reg, loc, val, end, call, tr, sme = p[:10]
    if DROP.search(title): continue
    try: closes = datetime.fromisoformat(end if 'T' in end else end + 'T12:00').replace(tzinfo=timezone.utc)
    except ValueError: continue
    if closes <= now: continue
    c, why = WHY[call]
    v = int(val or 0)
    t = {'id': nid, 'title': title.strip().rstrip('.'), 'buyer': buyer.strip(), 'area': REG.get(reg, 'UK-wide'),
         'place': loc.strip().title() if loc.isupper() else loc.strip(), 'value': money(v), 'term': '',
         'closes': closes.strftime('%Y-%m-%dT%H:%M'), 'call': c, 'why': why,
         'route': 'Framework' if call == 'F' else 'Tender', 'portal': 'Find a Tender notice',
         'trades': [TR[int(ch)] for ch in dict.fromkeys(tr) if ch.isdigit() and int(ch) < len(TR)][:2] or ['Building & refurbishment'],
         'sme': sme == '1'}
    if nid in keep:
        h = dict(keep[nid]); h['county'] = h.get('county') or h.get('area'); h['area'] = t['area']; t = h
    out[nid] = t
for nid, h in keep.items():
    if nid not in out and datetime.fromisoformat(h['closes']).replace(tzinfo=timezone.utc) > now:
        h = dict(h); h['county'] = h.get('county') or h.get('area'); h['area'] = 'East Midlands'; out[nid] = h
tenders = sorted(out.values(), key=lambda t: t['closes'])
for pr in wj.get('projects', []):
    if pr.get('area') in ('Derbyshire','Nottinghamshire','Leicestershire','Lincolnshire','Northamptonshire','Rutland'):
        pr['county'] = pr['area']; pr['area'] = 'East Midlands'
wj['tenders'] = tenders
wj['areas'] = [r for r in ORDER if any(t['area'] == r for t in tenders)]
wj['trades'] = TR
wj['updated'] = now.strftime('%Y-%m-%d')
json.dump(wj, open(os.path.join(ROOT,'data','work.json'),'w'), ensure_ascii=False, indent=1)
from collections import Counter
print(len(tenders)); print(Counter(t['area'] for t in tenders).most_common()); print(Counter(x for t in tenders for x in t['trades']).most_common()); print(Counter(t['call'] for t in tenders))
