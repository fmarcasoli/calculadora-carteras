#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
actualizar.py — refresca los datos de constructor-carteras.html

Uso:
    python actualizar.py
    python actualizar.py --agregar TSLA,SHOP,PBR
    python actualizar.py --quitar INTC
    python actualizar.py --anios 5
    python actualizar.py --html /ruta/al/constructor-carteras.html

No necesita instalar nada: usa solo la librería estándar de Python 3.8+.
Deja una copia de seguridad del archivo anterior antes de escribir.
"""

import argparse, json, os, re, ssl, sys, time, urllib.request, urllib.parse, urllib.error
from datetime import datetime, timezone

# ─────────────────────────────────────────────────────────────────────────────
#  UNIVERSO DE ACTIVOS
#  Para sumar un activo: agregá una línea "TICKER": ("Nombre visible", "Categoría")
#  El ticker es el de Yahoo Finance (BRK-B, no BRKB). Para sacarlo, borrá la línea.
#  También podés usar --agregar / --quitar sin tocar el archivo.
# ─────────────────────────────────────────────────────────────────────────────
UNIVERSO = {
    # índices amplios
    "SPY": ("S&P 500", "Índice"), "IVV": ("S&P 500 (iShares)", "Índice"),
    "QQQ": ("Nasdaq 100", "Índice"), "DIA": ("Dow Jones 30", "Índice"),
    "IWM": ("Russell 2000 (small cap)", "Índice"), "RSP": ("S&P 500 equiponderado", "Índice"),
    "IJH": ("S&P Mid Cap 400", "Índice"), "ACWI": ("MSCI All Country World", "Índice"),
    "VEA": ("Desarrollados ex-US", "Índice"), "EEM": ("Emergentes", "Índice"),
    "IEMG": ("Emergentes core", "Índice"), "EFA": ("EAFE", "Índice"),
    "IVW": ("S&P 500 Growth", "Índice"), "IVE": ("S&P 500 Value", "Índice"),
    "SPHQ": ("S&P 500 Quality", "Índice"), "VIG": ("Dividend Growth", "Índice"),
    "EWZ": ("Brasil", "Índice"), "ILF": ("LatAm 40", "Índice"), "EWJ": ("Japón", "Índice"),
    "FXI": ("China large cap", "Índice"), "IEUR": ("Europa", "Índice"),
    # sectores
    "XLE": ("Energía", "Sector"), "XLF": ("Financiero", "Sector"), "XLK": ("Tecnología", "Sector"),
    "XLV": ("Salud", "Sector"), "XLI": ("Industrial", "Sector"), "XLY": ("Consumo discrecional", "Sector"),
    "XLP": ("Consumo defensivo", "Sector"), "XLU": ("Utilities", "Sector"), "XLB": ("Materiales", "Sector"),
    "XLRE": ("Real estate", "Sector"), "XLC": ("Comunicaciones", "Sector"),
    "SMH": ("Semiconductores", "Sector"), "IBB": ("Biotech", "Sector"), "ITA": ("Defensa", "Sector"),
    "XME": ("Minería", "Sector"), "ARKK": ("ARK Innovation", "Sector"), "ICLN": ("Energía limpia", "Sector"),
    "URA": ("Uranio", "Sector"), "COPX": ("Cobre", "Sector"), "GDX": ("Mineras de oro", "Sector"),
    "CIBR": ("Ciberseguridad", "Sector"),
    # renta fija (referencia: la mayoría no tiene CEDEAR)
    "SHV": ("T-Bills < 1 año", "Renta fija"), "SHY": ("Treasury 1-3 años", "Renta fija"),
    "IEF": ("Treasury 7-10 años", "Renta fija"), "TLT": ("Treasury 20+ años", "Renta fija"),
    "AGG": ("Agregado US", "Renta fija"), "LQD": ("Corporativo IG", "Renta fija"),
    "HYG": ("High yield", "Renta fija"), "EMB": ("Soberano emergente USD", "Renta fija"),
    "TIP": ("Treasury indexado inflación", "Renta fija"),
    # commodities
    "GLD": ("Oro", "Commodity"), "SLV": ("Plata", "Commodity"), "USO": ("Petróleo WTI", "Commodity"),
    # Argentina
    "YPF": ("YPF", "Argentina"), "PAM": ("Pampa Energía", "Argentina"), "IRS": ("IRSA", "Argentina"),
    "VIST": ("Vista Energy", "Argentina"), "GGAL": ("Grupo Galicia", "Argentina"),
    "BMA": ("Banco Macro", "Argentina"), "SUPV": ("Supervielle", "Argentina"),
    "BBAR": ("BBVA Argentina", "Argentina"), "CEPU": ("Central Puerto", "Argentina"),
    "TGS": ("Transportadora Gas Sur", "Argentina"), "EDN": ("Edenor", "Argentina"),
    "LOMA": ("Loma Negra", "Argentina"), "CRESY": ("Cresud", "Argentina"),
    "TEO": ("Telecom Argentina", "Argentina"), "GLOB": ("Globant", "Argentina"),
    # LatAm
    "VALE": ("Vale", "LatAm"), "PBR": ("Petrobras", "LatAm"), "ITUB": ("Itaú", "LatAm"),
    "BBD": ("Bradesco", "LatAm"), "MELI": ("MercadoLibre", "LatAm"), "NU": ("Nu Holdings", "LatAm"),
    "STNE": ("StoneCo", "LatAm"), "GGB": ("Gerdau", "LatAm"), "ARCO": ("Arcos Dorados", "LatAm"),
    # acciones US
    "AAPL": ("Apple", "Acción US"), "MSFT": ("Microsoft", "Acción US"), "GOOGL": ("Alphabet", "Acción US"),
    "AMZN": ("Amazon", "Acción US"), "META": ("Meta", "Acción US"), "NVDA": ("Nvidia", "Acción US"),
    "TSLA": ("Tesla", "Acción US"), "AVGO": ("Broadcom", "Acción US"), "AMD": ("AMD", "Acción US"),
    "PLTR": ("Palantir", "Acción US"), "NFLX": ("Netflix", "Acción US"), "ORCL": ("Oracle", "Acción US"),
    "CRM": ("Salesforce", "Acción US"), "JPM": ("JPMorgan", "Acción US"), "V": ("Visa", "Acción US"),
    "MA": ("Mastercard", "Acción US"), "BRK-B": ("Berkshire Hathaway", "Acción US"),
    "JNJ": ("Johnson & Johnson", "Acción US"), "PG": ("Procter & Gamble", "Acción US"),
    "KO": ("Coca-Cola", "Acción US"), "WMT": ("Walmart", "Acción US"), "XOM": ("Exxon", "Acción US"),
    "CVX": ("Chevron", "Acción US"), "UNH": ("UnitedHealth", "Acción US"), "HD": ("Home Depot", "Acción US"),
    "COST": ("Costco", "Acción US"), "LLY": ("Eli Lilly", "Acción US"), "TSM": ("TSMC", "Acción US"),
    "ASML": ("ASML", "Acción US"), "MU": ("Micron", "Acción US"), "INTC": ("Intel", "Acción US"),
    "QCOM": ("Qualcomm", "Acción US"), "DIS": ("Disney", "Acción US"), "BABA": ("Alibaba", "Acción US"),
    "SHOP": ("Shopify", "Acción US"), "COIN": ("Coinbase", "Acción US"), "UBER": ("Uber", "Acción US"),
    "CAT": ("Caterpillar", "Acción US"), "BA": ("Boeing", "Acción US"), "PEP": ("PepsiCo", "Acción US"),
}

# CEDEARs cuyo símbolo en BYMA difiere del ticker de Yahoo
ALIAS_CEDEAR = {"BRK-B": "BRKB", "DIS": "DISN", "GOOG": "GOGL"}

# BYMA → Yahoo, cuando el candidato automático no acierta
ALIAS_BYMA = {"BRKB": "BRK-B", "DISN": "DIS", "GOGL": "GOOGL",
              "GOGLC": "GOOGL", "GOGLD": "GOOGL"}

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
CTX = ssl.create_default_context()


def http_json(url, timeout=25):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout, context=CTX) as r:
        return json.loads(r.read().decode("utf-8", "replace"))


def bajar_precios(ticker, anios, intentos=3):
    """Devuelve {fecha_iso: precio_ajustado} o None."""
    url = ("https://query1.finance.yahoo.com/v8/finance/chart/"
           + urllib.parse.quote(ticker)
           + f"?range={anios}y&interval=1d&events=div,splits")
    for k in range(intentos):
        try:
            d = http_json(url)["chart"]["result"][0]
            ts = d["timestamp"]
            try:
                px = d["indicators"]["adjclose"][0]["adjclose"]
            except (KeyError, IndexError, TypeError):
                px = d["indicators"]["quote"][0]["close"]
            out = {}
            for t, p in zip(ts, px):
                if p is None:
                    continue
                out[datetime.fromtimestamp(t, timezone.utc).strftime("%Y-%m-%d")] = float(p)
            return out or None
        except Exception:
            if k < intentos - 1:
                time.sleep(2 + 3 * k)
    return None


def buscar_nombre(ticker):
    """Nombre corto desde Yahoo, para tickers agregados por línea de comandos."""
    try:
        url = ("https://query1.finance.yahoo.com/v1/finance/search?q="
               + urllib.parse.quote(ticker) + "&quotesCount=4&newsCount=0")
        for q in http_json(url).get("quotes", []):
            if q.get("symbol", "").upper() == ticker.upper():
                return (q.get("shortname") or q.get("longname") or ticker)[:44]
    except Exception:
        pass
    return ticker


def bajar_cedears():
    """Símbolos con CEDEAR listado en BYMA."""
    try:
        return {x["symbol"] for x in http_json("https://data912.com/live/arg_cedears", timeout=30)}
    except Exception as e:
        print(f"  aviso: no pude traer la lista de CEDEARs ({e}). Se marcan todos como 'no'.")
        return set()


def base_cedears(cedears):
    """Del listado crudo de BYMA saca los símbolos 'base', sin variantes de
    especie C (cable) ni D (dólar). Ej: {AAPL, AAPLC, AAPLD} -> AAPL."""
    S = set(cedears)
    base = []
    for s in sorted(S):
        # variante 'AAPL.C' / 'AAPL.D' de un base existente
        if (s.endswith(".C") or s.endswith(".D")) and s[:-2] in S:
            continue
        # variante 'AAPLC' / 'AAPLD' de un base existente
        if len(s) > 1 and s[-1] in "CD" and s[:-1] in S:
            continue
        base.append(s)
    return base


def candidatos_yahoo(sym):
    """Tickers de Yahoo a probar para un símbolo BYMA, en orden."""
    c = []
    if sym in ALIAS_BYMA:
        c.append(ALIAS_BYMA[sym])
    c.append(sym)
    if "." in sym:
        c.append(sym.replace(".", "-"))          # AKO.B -> AKO-B
    if re.search(r"\d$", sym):
        c.append(sym + ".SA")                     # ABEV3 -> ABEV3.SA (B3 Brasil)
    seen, out = set(), []
    for x in c:
        if x not in seen:
            seen.add(x); out.append(x)
    return out


def yahoo_tiene_datos(ticker):
    """True si Yahoo tiene serie diaria usable (chequeo liviano, 1 año)."""
    try:
        u = ("https://query1.finance.yahoo.com/v8/finance/chart/"
             + urllib.parse.quote(ticker) + "?range=1y&interval=1d")
        ts = http_json(u)["chart"]["result"][0].get("timestamp") or []
        return len(ts) > 150
    except Exception:
        return False


def resolver_cedears(cedears, ya_cubiertos):
    """Descubre todos los CEDEARs de BYMA y resuelve su ticker de Yahoo.

    Devuelve:
      nuevos = {clave_byma: (nombre, "CEDEAR")}   activos a sumar al universo
      dl     = {clave_byma: ticker_yahoo}          de dónde bajar los precios
    'ya_cubiertos' es el conjunto de símbolos BYMA que el universo curado ya tiene."""
    base = base_cedears(cedears)
    print(f"CEDEARs en BYMA: {len(cedears)} especies → {len(base)} símbolos base.")
    nuevos, dl, fallidos = {}, {}, []
    for i, s in enumerate(base, 1):
        if s in ya_cubiertos:
            continue
        y = None
        for c in candidatos_yahoo(s):
            if yahoo_tiene_datos(c):
                y = c; break
            time.sleep(0.15)
        if not y:
            fallidos.append(s); continue
        nuevos[s] = (buscar_nombre(y), "CEDEAR")
        dl[s] = y
        if i % 40 == 0 or i == len(base):
            print(f"  resueltos {i}/{len(base)}")
        time.sleep(0.15)
    if fallidos:
        print(f"  sin serie en Yahoo (se omiten {len(fallidos)}): " + ", ".join(fallidos[:30])
              + (" …" if len(fallidos) > 30 else ""))
    return nuevos, dl


def main():
    ap = argparse.ArgumentParser(description="Actualiza los datos del constructor de carteras.")
    aqui = os.path.dirname(os.path.abspath(__file__))
    ap.add_argument("--html", default=os.path.join(aqui, "constructor-carteras.html"),
                    help="ruta al HTML (solo para el mensaje final; ya no se reescribe)")
    ap.add_argument("--datos", default=os.path.join(aqui, "datos.js"),
                    help="ruta al archivo de datos a escribir (default datos.js)")
    ap.add_argument("--anios", type=int, default=5, help="años de historia a descargar (default 5)")
    ap.add_argument("--agregar", default="", help="tickers extra separados por coma, ej: TSLA,SHOP")
    ap.add_argument("--quitar", default="", help="tickers a excluir, separados por coma")
    ap.add_argument("--sin-backup", action="store_true", help="no guardar copia del archivo anterior")
    ap.add_argument("--sin-todos-cedears", action="store_true",
                    help="no descubrir el universo completo de CEDEARs de BYMA (solo el curado)")
    args = ap.parse_args()

    if not os.path.exists(args.html):
        sys.exit(f"No encuentro el HTML en:\n  {args.html}\n"
                 "Poné este script en la misma carpeta que constructor-carteras.html, "
                 "o pasá la ruta con --html")

    universo = dict(UNIVERSO)
    for t in [x.strip().upper() for x in args.quitar.split(",") if x.strip()]:
        universo.pop(t, None)
    nuevos = [x.strip().upper() for x in args.agregar.split(",") if x.strip()]
    for t in nuevos:
        if t not in universo:
            universo[t] = (buscar_nombre(t), "Agregado")
            print(f"  nuevo: {t} — {universo[t][0]}")

    # ---- lista de CEDEARs de BYMA (para marcar 'ced' y, opcional, poblar el universo) ----
    cedears = bajar_cedears()
    dl = {}             # clave del universo -> ticker de Yahoo (si difiere)
    forzar_ced = set()  # activos que son CEDEAR por construcción
    if not args.sin_todos_cedears and not cedears:
        # Guard: pediste todos los CEDEARs pero data912 vino vacío (corte
        # transitorio). Abortar en vez de generar un universo degradado que
        # pisaría datos.js. En el cron esto falla la corrida y deja el anterior.
        sys.exit("data912 no devolvió CEDEARs (posible corte). Aborto para no "
                 "degradar los datos. Reintentá, o usá --sin-todos-cedears a propósito.")
    if cedears and not args.sin_todos_cedears:
        # símbolos BYMA que el universo curado ya cubre (para no duplicar)
        cubiertos = {ALIAS_CEDEAR.get(t, t) for t in universo}
        desc, dld = resolver_cedears(cedears, cubiertos)
        for s, meta in desc.items():
            universo[s] = meta
            forzar_ced.add(s)
        dl.update(dld)
        print(f"  sumados {len(desc)} CEDEARs nuevos al universo.")

    print(f"Descargando {len(universo)} activos, {args.anios} años de historia…")
    precios, fallidos = {}, []
    for i, t in enumerate(universo, 1):
        p = bajar_precios(dl.get(t, t), args.anios)
        if p and len(p) > 200:
            precios[t] = p
        else:
            fallidos.append(t)
        if i % 20 == 0 or i == len(universo):
            print(f"  {i}/{len(universo)}")
        time.sleep(0.35)
    if fallidos:
        print("  sin datos (se omiten): " + ", ".join(fallidos))
    if len(precios) < 5:
        sys.exit("Bajaron muy pocos activos. Puede ser un corte de red o un bloqueo temporal "
                 "de Yahoo; probá de nuevo en unos minutos.")

    # ---- calendario común: los días de rueda de SPY (mercado US) ----
    #  Un solo calendario de referencia evita que los feriados de otras bolsas
    #  (.SA Brasil, .DE Alemania) ensucien el eje. Cada activo se alinea a él.
    CAL = "SPY" if "SPY" in precios else max(precios, key=lambda t: len(precios[t]))
    fechas = sorted(precios[CAL].keys())
    if len(fechas) < 120:
        sys.exit("No hay suficientes fechas en el calendario de referencia.")
    ND = len(fechas) - 1          # cantidad de retornos (fechas[1:])
    MIN_RET = 60                  # historia mínima útil, en ruedas

    import math

    def tiene_cedear(t):
        return (t in forzar_ced) or (ALIAS_CEDEAR.get(t, t) in cedears) or (t in cedears)

    # ---- serie de cada activo sobre el calendario, con su propio inicio ----
    #  off = primer índice de retorno donde el activo ya cotiza. Los activos
    #  listados después arrancan con off>0; nadie recorta la historia del resto.
    activos, cortos = {}, []
    for t, p in precios.items():
        # precio alineado al calendario, completando huecos internos hacia adelante
        v, ult, d0 = [], None, None
        for k, f in enumerate(fechas):
            if f in p:
                ult = p[f]
                if d0 is None:
                    d0 = k
            v.append(ult)                       # None antes del primer dato
        if d0 is None or (ND - d0) < MIN_RET:
            cortos.append(t)
            continue
        off = d0                                # primer índice de retorno usable (r[k]=log(v[k+1]/v[k]))
        r = [int(round(math.log(v[k + 1] / v[k]) * 1e5)) for k in range(off, ND)]
        nombre, cat = universo[t]
        activos[t] = {"n": nombre, "c": cat, "ced": bool(tiene_cedear(t)),
                      "off": off, "r": r}
    if cortos:
        print(f"  historia muy corta (<{MIN_RET} ruedas, se omiten {len(cortos)}): "
              + ", ".join(cortos[:30]) + (" …" if len(cortos) > 30 else ""))
    if len(activos) < 5:
        sys.exit("Quedaron muy pocos activos con historia. Reintentá en unos minutos.")

    datos = {
        "generado": datetime.now().strftime("%Y-%m-%d"),
        "desde": fechas[1], "hasta": fechas[-1],
        "cal": CAL,
        "fechas": fechas[1:],
        "activos": activos,
    }

    # ---- escribir la data en datos.js (se carga con <script src>) ----
    #  Archivo separado del HTML: sirve igual online (Vercel) y localmente
    #  (doble clic), sin el CORS que rompería un fetch de datos.json en file://.
    nuevo_json = json.dumps(datos, separators=(",", ":"), ensure_ascii=False)
    contenido = "window.__DATA__=" + nuevo_json + ";\n"

    if not args.sin_backup and os.path.exists(args.datos):
        bak = args.datos + ".bak"
        with open(bak, "w", encoding="utf-8") as f:
            f.write(open(args.datos, encoding="utf-8").read())
        print(f"Copia de seguridad: {os.path.basename(bak)}")

    with open(args.datos, "w", encoding="utf-8") as f:
        f.write(contenido)

    con_ced = sum(1 for t in datos["activos"] if datos["activos"][t]["ced"])
    print(f"\nListo. {len(datos['activos'])} activos · {len(datos['fechas'])} ruedas · "
          f"{datos['desde']} a {datos['hasta']}")
    print(f"{con_ced} con CEDEAR en BYMA · {os.path.basename(args.datos)} "
          f"{round(os.path.getsize(args.datos)/1024)} KB")
    print(f"Abrí {os.path.basename(args.html)} en el navegador.")


if __name__ == "__main__":
    main()
