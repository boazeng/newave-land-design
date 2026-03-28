# Newave Land Design - מדריך התקנה והרצה

## דרישות מקדימות
- Python 3.11+
- Node.js 18+
- Git

---

## שלב 1: הורדת הפרויקט מ-GitHub

```bash
git clone https://github.com/boazeng/newave-land-design.git
cd newave-land-design
```

---

## שלב 2: התקנת תלויות

### Frontend
```bash
cd frontend
npm install
cd ..
```

### Backend
```bash
cd backend
pip install -r requirements.txt
cd ..
```

### כלים נוספים (לסקריפטים ולעיבוד נתונים)
```bash
pip install geopandas fiona openpyxl lxml beautifulsoup4 msal
```

---

## שלב 3: הגדרת קבצי סביבה (.env)

### קובץ גלובלי (משותף לכל הפרויקטים)
צור את הקובץ `C:\Users\User\Aiprojects\env\.env` עם:
```
# Priority
PRIORITY_URL_REAL=https://p.priority-connect.online/odata/Priority/tabz0qun.ini/ebyael/
PRIORITY_USERNAME=<מפתח API>
PRIORITY_PASSWORD=PAT

# SharePoint
SHAREPOINT_TENANT_ID=<tenant id>
SHAREPOINT_CLIENT_ID=<client id>
SHAREPOINT_CLIENT_SECRET=<secret>

# AI
OPENAI_API_KEY=<key>
ANTHROPIC_API_KEY=<key>
```

### קובץ מקומי לפרויקט
העתק את `.env.example` ל-`.env` ומלא ערכים:
```bash
cp .env.example .env
```

---

## שלב 4: נתוני מקרקעין (גושים וחלקות)

הקובץ `data/cadastre.gpkg` (1.6GB) לא נמצא ב-GitHub כי הוא גדול מדי.

### אפשרות א - הורדה מהשיירפוינט (מומלץ)
1. היכנס ל: https://yaelisrael.sharepoint.com/sites/newwave
2. פתח תיקיה: `נתוני מקרקעין`
3. הורד את `cadastre.gpkg`
4. שים אותו ב: `data/cadastre.gpkg`

### אפשרות ב - בנייה מאפס
1. הורד מ-data.gov.il:
   - גושים: https://data.gov.il/dataset/subgushallshape → שמור כ `data/blocks.zip`
   - חלקות: https://data.gov.il/dataset/shape → שמור כ `data/parcels.zip`
2. חלץ:
   ```bash
   cd data
   unzip blocks.zip -d blocks
   unzip parcels.zip -d parcels
   cd ..
   ```
3. המר ל-GeoPackage:
   ```bash
   python tools/convert_shapefiles.py
   ```
   זה ייצור את `data/cadastre.gpkg` (לוקח ~2 דקות)

---

## שלב 5: הרצת המערכת

### Backend (טרמינל 1)
```bash
cd backend
python -m uvicorn main:app --port 8001
```

### Frontend (טרמינל 2)
```bash
cd frontend
npm run dev
```

### פתיחה בדפדפן
http://localhost:3000

---

## מבנה הפרויקט

```
newave-land-design/
├── frontend/              # React + Vite + Tailwind
│   └── src/
│       ├── components/    # Map, Search, Layers
│       └── pages/         # Home, Map, Databases, Parking, Committees
├── backend/               # FastAPI
│   ├── routers/           # cadastre, search, autocomplete, parking, chargers, committees
│   └── services/          # business logic + geocoding
├── agents/
│   ├── parking/           # סוכן סנכרון מתקני חניה מפריוריטי
│   └── search_agent/
│       └── vaadot_search/ # סקריפטים להורדת פרוטוקולי ועדות
├── tools/                 # סקריפטים עזר (המרה, העלאה לשיירפוינט)
├── data/                  # נתונים מקומיים
│   ├── cadastre.gpkg      # גושים וחלקות (לא ב-GitHub, הורד מהשיירפוינט)
│   ├── streets.csv        # 63,438 רחובות
│   ├── committees_local.json
│   ├── committees_district.json
│   └── districts.geojson
└── database/              # סכמות DB (לשימוש עתידי עם PostgreSQL)
```

---

## תכונות המערכת

### מפה אינטראקטיבית (`/map`)
- מפת ישראל עם שמות בעברית
- שכבות: מחוזות תכנון, גושים (זום 12+), חלקות (זום 15+)
- חיפוש כתובת עם autocomplete (עיר → רחוב → מספר בית)
- חיפוש גוש/חלקה
- הצגת בסיסי נתונים על המפה (מתקני חניה, מטענים) עם בחירת סמן

### בסיסי נתונים (`/databases`)
- **מתקני חניה** - סנכרון מפריוריטי (SERNUMBERS), קיבוץ לפי אתר
- **מטענים** - מוכן לסנכרון כשיהיו DCODE בפריוריטי
- **גושים** - 18,656 גושי רישום
- **חלקות** - 1,094,533 חלקות
- **רחובות** - 63,438 רחובות מ-data.gov.il

### ועדות תכנון ובניה (`/committees`)
- 131 ועדות מקומיות עם קישורים לאתרים
- 7 ועדות מחוזיות עם קישורים למסמכי מדיניות

---

## הורדת פרוטוקולי ועדות

הסקריפטים נמצאים ב-`agents/search_agent/vaadot_search/`.
ראה `README.md` באותה תיקיה להוראות מפורטות.

### דוגמה - יקנעם עילית:
```bash
cd agents/search_agent/vaadot_search/yokneam
python yokneam_scraper_auto.py --start-year 2026   # רק חדשים
```

### העלאה לשיירפוינט:
```bash
python tools/upload_to_sharepoint.py
```

---

## עדכון מ-GitHub

```bash
git pull origin main
```

לאחר עדכון, ייתכן שצריך להריץ:
```bash
cd frontend && npm install && cd ..
cd backend && pip install -r requirements.txt && cd ..
```

---

## פורטים

| שירות | פורט |
|--------|-------|
| Frontend (Vite) | 3000 |
| Backend (FastAPI) | 8001 |

הגדרת הפורט של ה-Backend נמצאת ב-`frontend/vite.config.js` (proxy).
