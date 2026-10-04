#!/usr/bin/env python3
"""Genera el sitio KM1.

  dist/           sitio estático multipágina, listo para subir a public_html
  preview.html    vista previa de un solo archivo (rutas por #hash, imágenes embebidas)

Uso: python3 build.py
"""
import base64
import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).parent
SRC = ROOT / "src"
DIST = ROOT / "dist"
ASSETS = ROOT / "assets"

PAGES = ["inicio", "paraderos", "capital", "red-nacional", "impacto", "nosotros", "contacto", "legal", "panel"]
NAV = [("inicio", "Inicio"), ("paraderos", "Paraderos KM1"), ("capital", "KM1 Capital"),
       ("red-nacional", "Red Nacional"), ("impacto", "Impacto y Energía"), ("nosotros", "Nosotros"),
       ("contacto", "Contacto")]
FONTS = '<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap">'

ICONS = {
    "fuel": '<path d="M4 20V5a2 2 0 0 1 2-2h7a2 2 0 0 1 2 2v15M3 20h13M7 7h5v4H7zM15 9l3 3v6a1.5 1.5 0 0 0 3 0V9l-3-3"/>',
    "bolt": '<path d="M13 2 4 14h7l-1 8 9-12h-7z"/>',
    "cup": '<path d="M4 9h13v5a5 5 0 0 1-5 5H9a5 5 0 0 1-5-5zM17 10h1.5a2.5 2.5 0 0 1 0 5H17M8 2v3M12 2v3"/>',
    "bed": '<path d="M3 18V7M3 14h18v4M21 14v-2a3 3 0 0 0-3-3h-7v5M7 11.5h.01"/>',
    "check": '<path d="M5 12.5 10 17 19 7"/>',
    "info": '<circle cx="12" cy="12" r="9"/><path d="M12 11v6M12 7.5h.01"/>',
    "shield": '<path d="M12 3 4 6v6c0 5 3.5 8 8 9 4.5-1 8-4 8-9V6z"/><path d="m9 12 2 2 4-4"/>',
    "map": '<path d="M9 4 3 6v14l6-2 6 2 6-2V4l-6 2zM9 4v14M15 6v14"/>',
    "phone": '<rect x="7" y="2" width="10" height="20" rx="2"/><path d="M11 18h2"/>',
    "leaf": '<path d="M5 19c0-9 6-14 15-14 0 9-5 15-14 15"/><path d="M5 19 13 11"/>',
    "cart": '<path d="M3 4h2l2.5 11h10L20 7H6.5"/><circle cx="9" cy="19" r="1.5"/><circle cx="17" cy="19" r="1.5"/>',
    "users": '<circle cx="9" cy="8" r="3.5"/><path d="M2.5 20a6.5 6.5 0 0 1 13 0M16 4.5a3.5 3.5 0 0 1 0 7M18 14a6 6 0 0 1 3.5 6"/>',
    "pin": '<path d="M12 21s-7-6.2-7-12a7 7 0 0 1 14 0c0 5.8-7 12-7 12z"/><circle cx="12" cy="9" r="2.5"/>',
    "building": '<path d="M4 21V5l8-3v19M12 9h8v12M3 21h18M8 8h.01M8 12h.01M8 16h.01M16 13h.01M16 17h.01"/>',
    "chart": '<path d="M4 20V10M10 20V4M16 20v-7M22 20H2"/>',
}


def icon(name):
    return ('<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" '
            'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' + ICONS[name] + "</svg>")


# ---------- Mapa de México (contorno simplificado, proyección equirectangular) ----------
OUTLINE = [
    (-117.1, 32.5), (-115.0, 32.7), (-114.8, 32.5), (-111.0, 31.3), (-108.2, 31.33), (-108.2, 31.78), (-106.5, 31.75),
    (-104.9, 30.6), (-104.4, 29.6), (-103.1, 29.0), (-102.4, 29.8), (-100.9, 29.3), (-100.5, 28.7), (-99.5, 27.5),
    (-98.3, 26.1), (-97.2, 25.9), (-97.6, 24.0), (-97.85, 22.2), (-97.4, 21.0), (-96.1, 19.2), (-94.4, 18.15),
    (-92.6, 18.6), (-91.8, 18.65), (-90.5, 19.8), (-90.4, 20.9), (-89.7, 21.3), (-87.1, 21.6), (-86.8, 21.1),
    (-87.45, 20.2), (-88.3, 18.5), (-89.15, 17.8), (-90.98, 17.8), (-90.98, 17.25), (-91.4, 17.25), (-90.4, 16.1),
    (-91.7, 16.07), (-92.2, 15.25), (-92.25, 14.5), (-93.9, 15.9), (-95.2, 16.15), (-97.1, 15.85), (-99.9, 16.85),
    (-102.2, 17.95), (-104.3, 19.05), (-105.6, 20.4), (-105.3, 21.5), (-106.4, 23.2), (-107.6, 24.6), (-109.0, 25.6),
    (-110.9, 27.9), (-111.95, 28.8), (-113.1, 30.8), (-114.8, 31.8), (-114.85, 31.0), (-113.5, 28.9), (-112.3, 27.3),
    (-111.35, 26.0), (-110.3, 24.15), (-109.9, 22.9), (-110.2, 23.4), (-112.1, 24.8), (-112.2, 26.0), (-113.6, 26.7),
    (-114.1, 27.9), (-115.1, 27.85), (-114.0, 28.4), (-115.8, 30.0), (-116.6, 31.85),
]
CITIES = {
    "leon": (-101.68, 21.12), "qro": (-100.39, 20.59),
    "cdmx": (-99.13, 19.43), "gdl": (-103.35, 20.67), "slp": (-100.98, 22.15), "ags": (-102.29, 21.88),
    "sal": (-101.0, 25.42), "mty": (-100.31, 25.67),
    "nld": (-99.5, 27.48), "pue": (-98.2, 19.04), "ver": (-96.13, 19.17), "tep": (-104.89, 21.5),
    "maz": (-106.41, 23.24), "trc": (-103.41, 25.54), "chi": (-106.09, 28.63), "oax": (-96.72, 17.06),
    "cul": (-107.39, 24.8), "her": (-110.96, 29.07), "tij": (-117.0, 32.5), "vsa": (-92.93, 17.99),
    "mer": (-89.62, 20.97), "cun": (-86.85, 21.16), "tam": (-97.86, 22.25),
}
STAGE_NODES = {
    2: ["cdmx", "gdl", "slp", "ags", "sal", "mty"],
    3: ["nld", "pue", "ver", "tep", "maz", "trc", "chi", "oax"],
    4: ["cul", "her", "tij", "vsa", "mer", "cun", "tam"],
}
STAGE_LINES = {
    2: [("leon", "gdl"), ("qro", "cdmx"), ("qro", "slp"), ("slp", "sal"), ("sal", "mty"), ("leon", "ags"), ("leon", "qro")],
    3: [("mty", "nld"), ("cdmx", "pue"), ("pue", "ver"), ("gdl", "tep"), ("tep", "maz"), ("sal", "trc"), ("trc", "chi"), ("pue", "oax")],
    4: [("maz", "cul"), ("cul", "her"), ("her", "tij"), ("ver", "vsa"), ("vsa", "mer"), ("mer", "cun"), ("mty", "tam")],
}


def proj(lon, lat):
    return round((lon + 118.2) * 19.6, 1), round((33.2 - lat) * 21.4, 1)


def mexico_svg():
    d = "M" + " L".join(f"{x} {y}" for x, y in (proj(*p) for p in OUTLINE)) + " Z"
    parts = [f'<path class="mx-land" d="{d}"/>']
    for st, lines in STAGE_LINES.items():
        for a, b in lines:
            (x1, y1), (x2, y2) = proj(*CITIES[a]), proj(*CITIES[b])
            parts.append(f'<line class="route-line st{st}" x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" style="fill:none"/>')
    for st, nodes in STAGE_NODES.items():
        for n in nodes:
            x, y = proj(*CITIES[n])
            parts.append(f'<circle class="node st{st}" cx="{x}" cy="{y}" r="4.5"/>')
    for n in ("leon", "qro"):
        x, y = proj(*CITIES[n])
        parts.append(f'<circle class="pulse" cx="{x}" cy="{y}" r="7"/><circle class="node-pilot" cx="{x}" cy="{y}" r="6.5"/>')
    lx, ly = proj(*CITIES["leon"])
    qx, qy = proj(*CITIES["qro"])
    parts.append(f'<text class="map-text" x="{lx - 12}" y="{ly - 12}" text-anchor="end">León</text>')
    parts.append(f'<text class="map-text" x="{qx + 12}" y="{qy + 20}">Querétaro</text>')
    parts.append(f'<text class="map-sub" x="{qx + 12}" y="{qy + 34}">Zona piloto propuesta · Bajío</text>')
    return ('<svg viewBox="0 0 640 420" role="img" aria-label="Mapa de México con el plan de expansión de KM1: '
            'zona piloto propuesta en el Bajío (León y Querétaro) y nodos de corredores futuros sin ubicación confirmada">'
            + "".join(parts) + "</svg>")


def network_section():
    stages = [
        (1, "Piloto Bajío", "León, Querétaro y corredores industriales.", "Zona piloto propuesta"),
        (2, "Corredores prioritarios", "Rutas de alto tránsito, logística y turismo.", "Plan de expansión"),
        (3, "Portafolio nacional", "Red conectada por datos de KM1 GO.", "Plan de expansión"),
        (4, "Franquicia y capital institucional", "Expansión con estándares de marca y operación.", "Plan de expansión"),
    ]
    btns = "".join(
        f'<button type="button" class="stage" data-stage="{n}" aria-pressed="{"true" if n == 1 else "false"}">'
        f'<span class="km-post"><small>ETAPA</small><b>{n}</b></span>'
        f'<span><h3>{t}</h3><p>{p}</p><span class="status">{s}</span></span></button>'
        for n, t, p, s in stages)
    return f'''<section class="section on-dark" data-network>
  <div class="wrap">
    <div class="section-head">
      <p class="eyebrow">Red Nacional</p>
      <h2>No construimos paraderos aislados. Construimos una red.</h2>
    </div>
    <div class="network">
      <div class="map-card">
        <span class="map-label">Plan de expansión</span>
        <div data-map data-stage="1">{mexico_svg()}</div>
        <div class="map-legend"><span><i style="background:var(--solar)"></i>Zona piloto propuesta</span><span><i style="background:var(--blanco)"></i>Nodo de corredor en estudio</span></div>
      </div>
      <div style="display:grid; gap:18px">
        <div class="stages">{btns}</div>
        <p class="disclaimer">Mapa ilustrativo del plan de expansión. Ninguna ubicación está confirmada; el Bajío es la zona piloto propuesta.</p>
      </div>
    </div>
  </div>
</section>'''


def header(spa):
    def href(slug):
        return f"#{slug}" if spa else ("index.html" if slug == "inicio" else f"{slug}.html")
    links = "".join(f'<a href="{href(s)}" data-nav="{s}">{label}</a>' for s, label in NAV)
    return f'''<a class="skip" href="#contenido">Saltar al contenido</a>
<header class="site-header">
  <div class="topbar">
    <div class="wrap topbar-inner">
      <p><b>Parada KM1</b> · Energía, sabor y descanso en cada kilómetro</p>
      <div class="header-ctas">
        <span class="lang" title="Versión en inglés próximamente"><b>ES</b> / <button type="button" aria-disabled="true">EN</button></span>
        <a class="btn btn-ghost-light" href="{href('red-nacional')}">Encuentra tu próxima parada</a>
        <a class="btn btn-lima" href="{href('capital')}">Conoce KM1 Capital</a>
      </div>
    </div>
  </div>
  <div class="mainbar">
    <div class="wrap header-inner">
      <a class="brand" href="{href('inicio')}" aria-label="Parada KM1, inicio">
        <img src="assets/logo.jpg" alt="">
        <span class="brand-name"><b>Parada KM1</b><span>Mi parada en el camino</span></span>
      </a>
      <nav class="main-nav" aria-label="Principal">{links}</nav>
      <button class="menu-btn" type="button" aria-label="Abrir menú" aria-expanded="false"><span></span><span></span><span></span></button>
    </div>
  </div>
</header>
<div class="mobile-ctas">
  <a class="btn btn-outline" href="{href('red-nacional')}">Encuentra tu próxima parada</a>
  <a class="btn btn-primary" href="{href('capital')}">Conoce KM1 Capital</a>
</div>'''


def footer():
    return '''<footer class="site-footer">
  <div class="wrap">
    <div class="footer-grid">
      <div class="footer-brand">
        <img src="assets/logo.jpg" alt="Parada KM1" style="width:84px; border-radius:50%">
        <p class="tagline">Mi parada <span>en el camino</span></p>
        <p>La red de paraderos inteligentes que mejora el viaje por México.</p>
      </div>
      <div><h4>Viajeros</h4><ul><li><a href="@paraderos">Paraderos KM1</a></li><li><a href="@red-nacional">Red Nacional</a></li><li><a href="@impacto">Impacto y Energía</a></li><li><a href="@nosotros">Nosotros</a></li></ul></div>
      <div><h4>Negocios</h4><ul><li><a href="@paraderos#aliados">Aliados y franquicia</a></li><li><a href="@capital">KM1 Capital</a></li><li><a href="@capital#form-inversion">Solicitar evaluación</a></li><li><a href="@contacto">Contacto</a></li></ul></div>
      <div><h4>Legales</h4><ul><li><a href="@legal#privacidad">Aviso de privacidad</a></li><li><a href="@legal#terminos">Términos de uso</a></li><li><a href="@legal#riesgos">Declaración de riesgos</a></li><li><a href="@legal#cumplimiento">Cumplimiento</a></li><li><a href="@panel">Panel interno (demo)</a></li></ul></div>
    </div>
    <p class="footer-legal-note">La información de KM1 Capital es de carácter informativo y no constituye una oferta pública de valores, recomendación de inversión ni promesa de rendimiento. Cualquier oportunidad está sujeta a evaluación, perfilamiento, documentación y a la estructura legal aplicable. Las imágenes son representaciones de concepto. Los mapas y etapas corresponden a un plan de expansión.</p>
    <div class="footer-bottom"><span>© 2026 Parada KM1 · KM1 Capital</span><span>Energía, sabor y descanso en cada kilómetro.</span></div>
  </div>
</footer>'''


def read_page(slug):
    raw = (SRC / "pages" / f"{slug}.html").read_text(encoding="utf-8")
    m = re.match(r"<!--\s*(\{.*?\})\s*-->\s*", raw, re.S)
    meta = json.loads(m.group(1))
    return meta, raw[m.end():]


def render(text, spa):
    text = text.replace("{{network}}", network_section())
    text = re.sub(r"\{\{icon:(\w+)\}\}", lambda m: icon(m.group(1)), text)

    def link(m):
        slug, anchor = m.group(1), m.group(2)
        if spa:
            return f'href="#{slug}"' + (f' data-anchor="{anchor}"' if anchor else "")
        page = "index.html" if slug == "inicio" else f"{slug}.html"
        return f'href="{page}' + (f"#{anchor}" if anchor else "") + '"'
    return re.sub(r'href="@([\w-]+)(?:#([\w-]+))?"', link, text)


def data_uri(path):
    mime = "image/jpeg" if path.suffix in (".jpg", ".jpeg") else "image/png"
    return f"data:{mime};base64," + base64.b64encode(path.read_bytes()).decode()


def build():
    css = (SRC / "styles.css").read_text(encoding="utf-8")
    js = (SRC / "main.js").read_text(encoding="utf-8")

    # ----- dist multipágina -----
    if DIST.exists():
        shutil.rmtree(DIST)
    (DIST / "css").mkdir(parents=True)
    (DIST / "js").mkdir()
    shutil.copytree(ASSETS, DIST / "assets")
    (DIST / "css" / "styles.css").write_text(css, encoding="utf-8")
    (DIST / "js" / "main.js").write_text(js, encoding="utf-8")
    for slug in PAGES:
        meta, body = read_page(slug)
        robots = '<meta name="robots" content="noindex, nofollow">' if meta.get("noindex") else ""
        html = f'''<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{meta["title"]}</title>
<meta name="description" content="{meta.get("desc", "")}">
{robots}
<link rel="icon" href="assets/logo.jpg">
{FONTS}
<link rel="stylesheet" href="css/styles.css">
</head>
<body data-page="{slug}">
{render(header(False), False)}
<main id="contenido">
{render(body, False)}
</main>
{render(footer(), False)}
<script src="js/main.js"></script>
</body>
</html>
'''
        if meta.get("nav"):
            html = html.replace(f'data-nav="{meta["nav"]}"', f'data-nav="{meta["nav"]}" aria-current="page"', 1)
        out = "index.html" if slug == "inicio" else f"{slug}.html"
        (DIST / out).write_text(html, encoding="utf-8")
    (DIST / "robots.txt").write_text("User-agent: *\nDisallow: /panel.html\n", encoding="utf-8")

    # ----- vista previa de un solo archivo -----
    mains = []
    for slug in PAGES:
        meta, body = read_page(slug)
        hidden = "" if slug == "inicio" else " hidden"
        mains.append(f'<main data-page="{slug}" data-title="{meta["title"]}"{hidden}>\n{render(body, True)}\n</main>')
    preview = f'''<title>Parada KM1</title>
{FONTS}
<style>
{css}
</style>
{render(header(True), True)}
<div id="contenido">
{chr(10).join(mains)}
</div>
{render(footer(), True)}
<script>window.KM1_SPA = true;</script>
<script>
{js}
</script>
'''
    for img in ASSETS.iterdir():
        preview = preview.replace(f"assets/{img.name}", data_uri(img))
    (ROOT / "preview.html").write_text(preview, encoding="utf-8")
    print("dist:", sorted(p.name for p in DIST.iterdir()))
    print("preview.html", round(len(preview) / 1024), "KB")


if __name__ == "__main__":
    build()
