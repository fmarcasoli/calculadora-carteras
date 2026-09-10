# Constructor de carteras

Herramienta de análisis cuantitativo de carteras (HTML sin dependencias).
Los datos (precios de Yahoo Finance + disponibilidad de CEDEAR en BYMA) viven en
`datos.js` (el HTML los carga con `<script src>`) y se refrescan con `actualizar.py`.

## Uso local

Abrí `constructor-carteras.html` en el navegador (doble clic). No necesita servidor.
`datos.js` tiene que estar en la misma carpeta.

Refrescar los datos a mano:

```bash
python3 actualizar.py            # 5 años de historia, universo curado + todos los CEDEARs
python3 actualizar.py --anios 8  # más historia
python3 actualizar.py --sin-todos-cedears   # solo el universo curado (más liviano)
```

## Online con datos que se actualizan solos

Hosteado en **Vercel** (sirve el HTML estático) + **GitHub Actions** (cron que
corre `actualizar.py` y commitea los datos nuevos; Vercel redeploya en cada push).

Puesta a punto (una sola vez):

1. **GitHub** — creá un repo vacío en https://github.com/new y subí esta carpeta:
   ```bash
   git remote add origin https://github.com/<usuario>/<repo>.git
   git push -u origin main
   ```
2. **Vercel** — entrá a https://vercel.com/new, importá el repo de GitHub y
   deploy. Framework preset: **Other**. No hace falta build command.
3. Listo. El workflow `.github/workflows/actualizar.yml` corre lun-vie tras el
   cierre US, actualiza los datos y Vercel publica la versión nueva. Podés
   dispararlo a mano desde la pestaña **Actions → Actualizar datos → Run workflow**.

### Notas

- El cron de Actions usa UTC (`30 21 * * 1-5` ≈ 18:30 ART). Cambiá la línea
  `cron:` para otra cadencia (ej. `0 12 * * 1` = lunes 09:00 ART, semanal).
- Yahoo a veces limita IPs de datacenter (HTTP 429). El script reintenta; si una
  corrida falla, no commitea nada y la anterior sigue publicada.
- Cada corrida reescribe `datos.js` (~2,4 MB); el HTML (44 KB) queda fijo. El
  repo igual crece con el histórico de `datos.js`. Si algún día molesta, se puede
  servir la data desde Vercel Blob o regenerarla en el deploy para no versionarla.
