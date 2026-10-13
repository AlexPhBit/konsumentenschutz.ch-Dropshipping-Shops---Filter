import csv
import re
import sys
from datetime import datetime, timezone

SOURCE_URL = 'https://www.konsumentenschutz.ch/online-ratgeber/dropshipping-die-stolpersteine-beim-onlinehandel-mit-billigware-aus-china/'
INPUT_FILE = sys.argv[1] if len(sys.argv) > 1 else 'data.html'
OUTPUT_FILE = 'filter.txt'

DOMAIN_RE = re.compile(r'^(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,}$')


def clean(raw):
    d = raw.strip().strip('"').lower()
    d = re.sub(r'^https?://', '', d)
    d = d.split('/')[0].split('?')[0].split(':')[0]
    if d.startswith('www.'):
        d = d[4:]
    try:
        d = d.encode('idna').decode('ascii')  # Umlaute -> Punycode (xn--...)
    except UnicodeError:
        return None
    return d if DOMAIN_RE.match(d) else None


def read_csv(path):
    raws = []
    with open(path, 'r', encoding='utf-8-sig', newline='') as f:
        sample = f.read(4096)
        f.seek(0)
        reader = csv.reader(f, csv.Sniffer().sniff(sample, delimiters=',;'))
        header = next(reader, [])
        col = header.index('Website') if 'Website' in header else 0
        for row in reader:
            if len(row) > col and row[col].strip():
                raws.append(row[col])
    return raws


def read_html(path):
    from bs4 import BeautifulSoup
    with open(path, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'html.parser')
    raws = []
    # Nur Tabellen mit der Spalte "Website" beruecksichtigen, nichts sonst von der Seite
    for table in soup.find_all('table'):
        headers = [c.get_text(' ', strip=True).lower() for c in table.find_all('th')]
        if 'website' not in headers:
            continue
        col = headers.index('website')
        for tr in table.find_all('tr'):
            cells = tr.find_all('td')
            if len(cells) > col:
                text = cells[col].get_text(' ', strip=True)
                if text:
                    raws.append(text)
    return raws


raws = read_csv(INPUT_FILE) if INPUT_FILE.lower().endswith('.csv') else read_html(INPUT_FILE)

if not raws:
    print("Keine Tabelle mit der Spalte 'Website' gefunden - Abbruch. "
          "Vermutlich wird die Liste per JavaScript nachgeladen. "
          "Alternative: CSV manuell als data.csv ins Repo legen und 'python3 convert.py data.csv' ausfuehren.",
          file=sys.stderr)
    sys.exit(1)

domains = set()
skipped = []
for raw in raws:
    d = clean(raw)
    if d:
        domains.add(d)
    else:
        skipped.append(raw)

if not domains:
    print('Keine gueltigen Domains gefunden - Abbruch', file=sys.stderr)
    sys.exit(1)

with open(OUTPUT_FILE, 'w', encoding='utf-8') as outfile:
    outfile.write('! Title: Inoffizielle Kopie - Liste problematischer Dropshipping-Shops (Konsumentenschutz)\n')
    outfile.write(f'! Source: {SOURCE_URL}\n')
    outfile.write('! Disclaimer: Inoffizielle, automatisch erzeugte Kopie. Keine Verbindung zur Stiftung fuer Konsumentenschutz. Keine Gewaehr fuer Richtigkeit und Vollstaendigkeit.\n')
    outfile.write(f'! Generated: {datetime.now(timezone.utc).isoformat()}\n')
    for domain in sorted(domains):
        outfile.write(f'||{domain}^\n')

print(f'{len(domains)} Domains aus {len(raws)} Zeilen geschrieben')
if skipped:
    print(f'{len(skipped)} ungueltige Eintraege uebersprungen: {skipped}')
