"""
SHARDAN - Skimlinks Helper V1
Piano B automatico: se un negozio ti ha rifiutato su Awin, Skimlinks lo monetizza lo stesso.
- Link Awin / Amazon / già Skimlinks -> NON toccare (100% commissione)
- Link normale MediaWorld / Decathlon / Conrad / Unieuro / Euronics -> avvolgi con Skimlinks (75%)
Usa: SKIMLINKS_ID in Secrets GitHub (es. 123456X1234567)
Esempio: https://go.skimresources.com/?id=123456X...&url=https://www.mediaworld.it/...
"""
import os
from urllib.parse import quote

SKIM_ID = os.environ.get("SKIMLINKS_ID", "").strip()

def is_gia_affiliato(link: str) -> bool:
    if not link: return True
    l = link.lower()
    return any(k in l for k in ["awin", "go.skimresources", "skimresources", "amazon", "amzn", "sovrn", "go2cloud", "tidd.ly", "shareasale"])

def converti(link: str) -> tuple[str, str]:
    """Ritorna (link_finale, fonte). fonte = 'awin' | 'skimlinks' | 'diretto'"""
    if not link:
        return link, "diretto"
    if is_gia_affiliato(link):
        # Se è già Skimlinks, fonte skimlinks, altrimenti awin/amazon
        if "skimresources" in link.lower():
            return link, "skimlinks"
        return link, "awin"
    if not SKIM_ID:
        print(f"Skimlinks: SKIMLINKS_ID mancante, lascio link diretto: {link[:60]}")
        return link, "diretto"
    # Avvolgi: go.skimresources.com/?id=ID&url=URL_ENCODED
    finale = f"https://go.skimresources.com/?id={SKIM_ID}&url={quote(link, safe='')}"
    return finale, "skimlinks"

def test():
    print(f"SKIMLINKS_ID presente: {'SI' if SKIM_ID else 'NO - mettilo nei Secrets!'}")
    for u in ["https://www.mediaworld.it/it/product/iphone-16", "https://www.awin1.com/cread.php?id=123", "https://www.amazon.it/dp/B123"]:
        f, fonte = converti(u)
        print(f"  {fonte:10} | {u[:45]} -> {f[:80]}")

if __name__ == "__main__":
    test()
