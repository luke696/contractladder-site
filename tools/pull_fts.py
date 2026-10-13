"""Pull open UK construction tenders from the Find a Tender OCDS API into a slim JSON list
for tools/build_work_json.py. Usage: python3 tools/pull_fts.py raw_tenders.json [days_back]
Run daily by .github/workflows/refresh-work-board.yml."""
import json, sys, time, urllib.request, urllib.parse
from datetime import datetime, timedelta, timezone
DAYS = int(sys.argv[2]) if len(sys.argv) > 2 else 75
SINCE = (datetime.now(timezone.utc) - timedelta(days=DAYS)).strftime('%Y-%m-%dT00:00:00')
BASE='https://www.find-tender.service.gov.uk/api/1.0/ocdsReleasePackages'
url=BASE+'?'+urllib.parse.urlencode({'stages':'tender','limit':100,'updatedFrom':SINCE})
slim={}; pages=0
while url and pages<400:
    for a in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(url,headers={'Accept':'application/json','User-Agent':'contractladder-work-board'}),timeout=60) as r: pk=json.load(r); break
        except Exception as e:
            print('retry',e,file=sys.stderr); time.sleep(5*(a+1))
    else: sys.exit('Find a Tender API unreachable after %d pages' % pages)
    pages+=1
    for rel in pk.get('releases',[]):
        tn=rel.get('tender') or {}
        cpv=[c.get('id','') for c in [tn.get('classification') or {}]+[i.get('classification') or {} for i in tn.get('items',[])]+[ac for i in tn.get('items',[]) for ac in i.get('additionalClassifications',[])] if c]
        if not any(c.startswith(('45','50','77','71','09331','4533','5075')) for c in cpv): continue
        end=(tn.get('tenderPeriod') or {}).get('endDate')
        if not end: continue
        regs=[a.get('region','') for i in tn.get('items',[]) for a in i.get('deliveryAddresses',[])]
        parties={p.get('id'):p for p in rel.get('parties',[])}
        b=parties.get((rel.get('buyer') or {}).get('id'),{}); ad=b.get('address') or {}
        sme=bool((tn.get('suitability') or {}).get('sme')) or any((l.get('suitability') or {}).get('sme') for l in tn.get('lots',[]))
        v=(tn.get('value') or {}).get('amount') or 0
        x=dict(id=rel.get('id'),ocid=rel.get('ocid'),t=tn.get('title'),d=tn.get('description') or '',end=end,v=v,sme=sme,regs=regs,
               bpc=ad.get('postalCode',''),breg=ad.get('region',''),bloc=ad.get('locality',''),buyer=(rel.get('buyer') or {}).get('name') or b.get('name',''),cpv=cpv,
               status=tn.get('status'),date=rel.get('date'))
        k=rel.get('ocid')
        if k not in slim or (x['date'] or '')>(slim[k]['date'] or ''): slim[k]=x
    url=(pk.get('links') or {}).get('next')
    time.sleep(0.3)
slim={k:x for k,x in slim.items() if (x.get('status') or '') not in ('cancelled','unsuccessful','complete','withdrawn')}
json.dump(list(slim.values()),open(sys.argv[1],'w'))
print('pages', pages, 'kept', len(slim))
if len(slim) < 50: sys.exit('Too few tenders pulled (%d); not rebuilding' % len(slim))
