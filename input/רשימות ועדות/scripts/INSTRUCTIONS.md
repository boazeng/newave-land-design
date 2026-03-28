# הוראות הרצה - הורדת פרוטוקולי ועדות תכנון מחוז תל אביב

## התקנת תלויות
```bash
pip install requests lxml beautifulsoup4 openpyxl
```

## הרצה מהירה (הכל בפקודה אחת)
```bash
cd scripts
python3 run_all_telaviv.py --count-only
```
זה יספור את כל הפרוטוקולים בלי להוריד (מומלץ להריץ קודם כדי לוודא שהכל עובד).

## הרצה מלאה (עם הורדת קבצים)
```bash
python3 run_all_telaviv.py
```

## הרצת ועדה בודדת

### ועדות Complot (רמת גן, חולון, בת ים, אור יהודה, רמת השרון)
```bash
# שלב 1: מציאת Site IDs (פעם אחת בלבד)
python3 find_complot_ids.py

# שלב 2: הרצת סקריפט עם ה-ID שנמצא
python3 complot_scraper.py --site-id 3 --city-name "רמת_גן" --protocols-only --start-year 2015
python3 complot_scraper.py --site-id 34 --city-name "חולון" --protocols-only --start-year 2015
```

### ועדות Bartech (קרית אונו, אזור)
```bash
python3 bartech_scraper.py --city-code ono --city-name "קרית_אונו" --protocols-only --start-year 2015
python3 bartech_scraper.py --city-code azr --city-name "אזור" --protocols-only --start-year 2015
```

### ועדות SharePoint/muni.il (בני ברק, גבעתיים, הרצליה)
```bash
python3 sharepoint_scraper.py --city bnei-brak --start-year 2015
python3 sharepoint_scraper.py --city givatayim --start-year 2015
python3 sharepoint_scraper.py --city herzliya --start-year 2015
```

### תל אביב-יפו
```bash
python3 telaviv_scraper.py --start-year 2015
```

## מבנה הפלט
```
output/
├── סיכום_פרוטוקולים_מחוז_תל_אביב.xlsx   ← טבלת סיכום
├── רמת_גן/
│   ├── רמת_גן_data.json
│   └── [PDF files organized by committee type]
├── חולון/
├── בת_ים/
├── ...
└── תל_אביב_יפו/
```

## 11 ועדות מחוז תל אביב

| # | ועדה | פלטפורמה | Site ID / קוד |
|---|------|----------|---------------|
| 1 | רמת גן | Complot | site_id=3 |
| 2 | חולון | Complot | site_id=34 |
| 3 | בת ים | Complot | צריך סריקה |
| 4 | אור יהודה | Complot | צריך סריקה |
| 5 | רמת השרון | Complot | צריך סריקה |
| 6 | קרית אונו | Bartech | city_code=ono |
| 7 | אזור | Bartech | city_code=azr |
| 8 | בני ברק | SharePoint | bnei-brak |
| 9 | גבעתיים | SharePoint | givatayim |
| 10 | הרצליה | SharePoint | herzliya |
| 11 | תל אביב-יפו | tel-aviv.gov.il | - |

## הערות
- הסקריפטים הראשיים (Complot) מבוססים על API ישיר ועובדים ללא דפדפן
- סקריפטים של Bartech ו-SharePoint עובדים עם requests + HTML parsing
- אם סקריפט לא מצליח למצוא פרוטוקולים, יתכן שהאתר שינה מבנה - יש לבדוק ידנית
- כל סקריפט שומר JSON עם כל הנתונים שחולצו (קישורים, תאריכים, ספירות)
