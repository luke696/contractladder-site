"""Rebuild /t/<trade>/ landing pages from work.html. Run after editing work.html.
Each page is the work board pre-filtered to one trade, so outreach links can point
at a trade and the cookie-free visit counter shows which emails bring visits."""
import os
SLUGS = {'lifts':'Lifts','surfacing':'Surfacing & groundworks','grounds':'Grounds & landscaping',
 'demolition':'Demolition','building':'Building & refurbishment','maintenance':'Maintenance & repairs',
 'electrical':'Electrical & renewables','heating':'Heating & plumbing','plant':'Plant hire','roofing':'Roofing & cladding'}
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
import re
src = open(os.path.join(root, 'work.html')).read()
src = re.sub(r'\n<!-- seo -->.*?<!-- /seo -->', '', src, flags=re.S)
for slug, trade in SLUGS.items():
    page = src.replace('<head>', '<head>\n<base href="/">\n<meta name="robots" content="noindex">\n<link rel="canonical" href="https://contractladder.co.uk/work.html">\n<link rel="icon" href="/img/favicon.svg" type="image/svg+xml">', 1)
    page = page.replace('<script>', f'<script>window.PRESET_TRADE={trade!r};</script>\n<script>', 1)
    os.makedirs(os.path.join(root, 't', slug), exist_ok=True)
    open(os.path.join(root, 't', slug, 'index.html'), 'w').write(page)
print('built', len(SLUGS), 'trade pages')
