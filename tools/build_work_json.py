"""Turn a raw Find a Tender pull (list of slim OCDS releases, JSON) into data/work.json.
Usage: python3 tools/build_work_json.py raw_tenders.json
Keeps hand-written entries already in work.json (richer 'why' text) when the notice id matches."""
import json, re, sys, os
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REGIONS = ['North East', 'North West', 'Yorkshire and the Humber', 'East Midlands', 'West Midlands',
           'East of England', 'London', 'South East', 'South West', 'Wales', 'Scotland', 'Northern Ireland']
NUTS = {'UKC': 'North East', 'UKD': 'North West', 'UKE': 'Yorkshire and the Humber', 'UKF': 'East Midlands',
        'UKG': 'West Midlands', 'UKH': 'East of England', 'UKI': 'London', 'UKJ': 'South East', 'UKK': 'South West',
        'UKL': 'Wales', 'UKM': 'Scotland', 'UKN': 'Northern Ireland',
        'TLC': 'North East', 'TLD': 'North West', 'TLE': 'Yorkshire and the Humber', 'TLF': 'East Midlands',
        'TLG': 'West Midlands', 'TLH': 'East of England', 'TLI': 'London', 'TLJ': 'South East', 'TLK': 'South West',
        'TLL': 'Wales', 'TLM': 'Scotland', 'TLN': 'Northern Ireland'}
PC = {}
def _pc(region, areas):
    for a in areas.split(): PC[a] = region
_pc('North East', 'NE SR DH DL TS')
_pc('North West', 'M L WA WN BL OL SK CH CW PR BB FY LA CA')
_pc('Yorkshire and the Humber', 'LS BD HD HX WF S DN HU YO HG')
_pc('East Midlands', 'NG DE LE NN LN')
_pc('West Midlands', 'B CV DY WS WV ST TF WR HR')
_pc('East of England', 'CB CO CM IP NR PE SG AL LU MK SS EN')
_pc('London', 'E EC N NW SE SW W WC BR CR DA HA IG KT RM SM TW UB')
_pc('South East', 'BN CT GU ME OX PO RG RH SL SO TN HP')
_pc('South West', 'BA BS BH DT EX GL PL SN SP TA TQ TR')
_pc('Wales', 'CF LD LL NP SA')
_pc('Scotland', 'AB DD DG EH FK G HS IV KA KW KY ML PA PH TD ZE')
_pc('Northern Ireland', 'BT')

def region_of(x):
    for r in x.get('regs') or []:
        r = (r or '').upper().replace(' ', '')
        if r[:3] in NUTS: return NUTS[r[:3]]
        for name in REGIONS:
            if name.upper().replace(' ', '') in r: return name
    m = re.match(r'([A-Z]{1,2})\d', (x.get('bpc') or '').upper().replace(' ', ''))
    if m and m.group(1) in PC: return PC[m.group(1)]
    if (x.get('breg') or '').upper()[:3] in NUTS: return NUTS[x['breg'].upper()[:3]]
    return ''

KW = [
    (r'\blift|elevator|escalator|stairlift', 'Lifts'),
    (r'demoli|asbestos', 'Demolition'),
    (r'roof|cladding|gutter', 'Roofing & cladding'),
    (r'boiler|heating|heat pump|plumb|gas serv|ventilat|hvac|air condition|mechanical', 'Heating & plumbing'),
    (r'electric|rewir|lighting|solar|photovolt|\bpv\b|ev charg|fire alarm|illuminat', 'Electrical & renewables'),
    (r'resurfac|surfacing|footpath|footway|car park|carriageway|highway|paving|drainage|groundwork|civils', 'Surfacing & groundworks'),
    (r'grounds|grass|mowing|landscap|tree |trees|hedge|verge|play area|playground', 'Grounds & landscaping'),
    (r'fenc', 'Fencing'),
    (r'repair|maintenance|responsive|voids|planned works', 'Maintenance & repairs'),
    (r'refurb|extension|classroom|new build|construction|kitchen|bathroom|window|door|decorat|painting|flooring|alteration|conversion|fit[- ]out', 'Building & refurbishment'),
    (r'plant hire|operated plant', 'Plant hire'),
]
CPV = [
    ('45313', 'Lifts'), ('5075', 'Lifts'), ('45111', 'Demolition'), ('452626', 'Demolition'),
    ('45261', 'Roofing & cladding'), ('45262', 'Roofing & cladding'),
    ('4533', 'Heating & plumbing'), ('50720', 'Heating & plumbing'), ('50721', 'Heating & plumbing'),
    ('4531', 'Electrical & renewables'), ('4532', 'Electrical & renewables'), ('50711', 'Electrical & renewables'), ('09331', 'Electrical & renewables'),
    ('4523', 'Surfacing & groundworks'), ('4524', 'Surfacing & groundworks'), ('4511', 'Surfacing & groundworks'), ('45232', 'Surfacing & groundworks'),
    ('7731', 'Grounds & landscaping'), ('7734', 'Grounds & landscaping'), ('45112', 'Grounds & landscaping'),
    ('45342', 'Fencing'), ('4550', 'Plant hire'),
    ('507', 'Maintenance & repairs'), ('508', 'Maintenance & repairs'),
    ('4521', 'Building & refurbishment'), ('454', 'Building & refurbishment'), ('4545', 'Building & refurbishment'), ('452', 'Building & refurbishment'), ('45', 'Building & refurbishment'),
]
TRADES = ['Building & refurbishment', 'Maintenance & repairs', 'Heating & plumbing', 'Electrical & renewables',
          'Roofing & cladding', 'Surfacing & groundworks', 'Grounds & landscaping', 'Lifts', 'Demolition', 'Fencing', 'Plant hire']

def trades_of(x):
    text = ((x.get('t') or '') + ' ' + (x.get('d') or '')[:250]).lower()
    out = []
    for pat, tr in KW:
        if re.search(pat, (x.get('t') or '').lower()) and tr not in out: out.append(tr)
    for c in x.get('cpv') or []:
        for pre, tr in CPV:
            if c.startswith(pre):
                if tr not in out and not (tr == 'Building & refurbishment' and out): out.append(tr)
                break
    if not out:
        for pat, tr in KW:
            if re.search(pat, text): out.append(tr); break
    return out[:2] or ['Building & refurbishment']

def money(v):
    if not v: return ''
    if v >= 1_000_000: return '£%sm' % ('%.1f' % (v / 1e6)).rstrip('0').rstrip('.')
    return '£{:,}'.format(int(round(v, -3) if v >= 10000 else v))

def call_of(x):
    v = x.get('v') or 0
    t = (x.get('t') or '').lower() + ' ' + (x.get('d') or '').lower()[:400]
    fw = bool(re.search(r'framework|dynamic (purchasing|market)|\bdps\b|approved list', t))
    if v and v > 5_000_000:
        return 'check', 'A large contract. Usually needs strong turnover and track record; smaller firms do better on lots or as a named subcontractor.'
    if fw:
        return 'check', 'A framework or approved list. Getting on it is the hard part; after that, work is called off for years.'
    if x.get('sme'):
        return 'bid', 'Marked by the buyer as suitable for small firms. A realistic one to go for.'
    if v and v <= 500_000:
        return 'bid', 'A single job at a size a small or medium firm can win.'
    return 'check', 'Check the size, insurance levels and experience they ask for before deciding.'

def notice_id(x):
    m = re.match(r'(\d{6}-\d{4})', x.get('id') or '')
    if m: return m.group(1)
    m = re.search(r'(\d{6}-\d{4})', x.get('ocid') or '')
    return m.group(1) if m else (x.get('id') or x.get('ocid'))

def main(raw_path):
    raw = json.load(open(raw_path))
    if isinstance(raw, dict): raw = list(raw.values())
    wj = json.load(open(os.path.join(ROOT, 'data', 'work.json')))
    keep = {t['id']: t for t in wj.get('tenders', [])}
    out = {}
    now = datetime.now(timezone.utc)
    for x in raw:
        nid = notice_id(x)
        try: end = datetime.fromisoformat(x['end'].replace('Z', '+00:00'))
        except Exception: continue
        if end <= now: continue
        v = x.get('v') or 0
        if v and v > 25_000_000: continue
        region = region_of(x)
        if nid in keep:
            t = dict(keep[nid]); t['area'] = 'East Midlands' if t.get('area') in ('Derbyshire', 'Nottinghamshire', 'Leicestershire', 'Lincolnshire', 'Northamptonshire', 'Rutland') else (t.get('area') or region)
            t['county'] = keep[nid].get('area', '')
        else:
            call, why = call_of(x)
            t = {'id': nid, 'title': (x.get('t') or '').strip()[:140], 'buyer': (x.get('buyer') or '').strip(),
                 'area': region, 'place': (x.get('bloc') or '').title(), 'value': money(v),
                 'term': '', 'closes': end.astimezone(timezone.utc).strftime('%Y-%m-%dT%H:%M'),
                 'call': call, 'why': why, 'route': 'Framework' if 'framework' in why.lower() else 'Tender',
                 'portal': 'Find a Tender notice', 'trades': trades_of(x), 'sme': bool(x.get('sme'))}
        t['url'] = 'https://www.find-tender.service.gov.uk/Notice/' + nid
        out[nid] = t
    for nid, t in keep.items():
        if nid not in out:
            try:
                if datetime.fromisoformat(t['closes']).replace(tzinfo=timezone.utc) > now:
                    t = dict(t); t['county'] = t.get('area', ''); t['area'] = 'East Midlands'
                    t['url'] = 'https://www.find-tender.service.gov.uk/Notice/' + nid; out[nid] = t
            except Exception: pass
    tenders = sorted(out.values(), key=lambda t: t['closes'])
    for p in wj.get('projects', []):
        if p.get('area') in ('Derbyshire', 'Nottinghamshire', 'Leicestershire', 'Lincolnshire', 'Northamptonshire', 'Rutland'):
            p['county'] = p['area']; p['area'] = 'East Midlands'
    wj['tenders'] = tenders
    wj['areas'] = [r for r in REGIONS if any(t['area'] == r for t in tenders)]
    wj['trades'] = TRADES
    wj['updated'] = now.strftime('%Y-%m-%d')
    json.dump(wj, open(os.path.join(ROOT, 'data', 'work.json'), 'w'), ensure_ascii=False, indent=1)
    from collections import Counter
    print(len(tenders), 'tenders'); print(Counter(t['area'] or '?' for t in tenders)); print(Counter(tr for t in tenders for tr in t['trades'])); print(Counter(t['call'] for t in tenders))

if __name__ == '__main__':
    main(sys.argv[1])
