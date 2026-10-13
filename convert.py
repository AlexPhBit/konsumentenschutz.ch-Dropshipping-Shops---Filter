import re
import sys
from datetime import datetime, timezone
from urllib.parse import urlparse

from bs4 import BeautifulSoup

SOURCE_URL = sys.argv[1] if len(sys.argv) > 1 else ''

# Domains, die nie geblockt werden sollen (Quelle selbst, Social Media, Assets)
EXCLUDE = {
    'konsumentenschutz.ch', 'facebook.com', 'twitter.com', 'x.com',
    'linkedin.com', 'instagram.com', 'youtube.com', 'youtu.be',
    'tiktok.com', 'schema.org', 'w3.org', 'google.com',
    'googleapis.com', 'googletagmanager.com', 'gstatic.com',
    'beobachter.ch', 'blick.ch', 'srf.ch', 'admin.ch',
}

# Dateiendungen, die der Domain-Regex sonst fälschlich als TLD erkennt
FILE_EXT = {
    'html', 'htm', 'php', 'asp', 'aspx', 'jpg', 'jpeg', 'png', 'gif',
    'webp', 'svg', 'css', 'js', 'json', 'xml', 'pdf', 'ico', 'woff',
    'woff2', 'ttf', 'txt', 'zip',
}

DOMAIN_RE = re.compile(
    r'\b((?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,})\b',
    re.IGNORECASE,
)


def norm(domain):
    domain = domain.lower().strip().strip('.')
    return domain[4:] if domain.startswith('www.') else domain


def valid(domain):
    tld = domain.rsplit('.', 1)[-1]
    return '.' in domain and tld not in FILE_EXT and domain not in EXCLUDE


with open('data.html', 'r', encoding='utf-8') as infile:
    soup = BeautifulSoup(infile.read(), 'html.parser')

# Navigation, Footer, Skripte usw. ignorieren
for tag in soup(['script', 'style', 'nav', 'header', 'footer', 'noscript']):
    tag.decompose()

domains = set()

# 1) Externe Links
for a in soup.find_all('a', href=True):
    href = a['href'].strip()
    if href.startswith('//'):
        href = 'https:' + href
    if href.startswith(('http://', 'https://')):
        host = urlparse(href).netloc.split(':')[0]
        if host:
            domains.add(norm(host))

# 2) Domains, die nur als Text genannt werden (z. B. "yozo.ch" in einer Liste)
for match in DOMAIN_RE.finditer(soup.get_text(' ', strip=True)):
    domains.add(norm(match.group(1)))

domains = sorted(d for d in domains if valid(d))

if not domains:
    print('Keine Domains gefunden - Abbruch', file=sys.stderr)
    sys.exit(1)

with open('filter.txt', 'w', encoding='utf-8') as outfile:
    outfile.write('! Title: Konsumentenschutz Dropshipping Filterlist\n')
    outfile.write(f'! Description: Domains aus {SOURCE_URL}\n')
    outfile.write(f'! Generated: {datetime.now(timezone.utc).isoformat()}\n')
    for domain in domains:
        outfile.write(f'||{domain}^\n')

print(f'{len(domains)} Domains geschrieben')
