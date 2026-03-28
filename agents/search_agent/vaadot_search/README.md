# סקריפטים להורדת פרוטוקולי ועדות תכנון ובניה

## מבנה

```
vaadot_search/
├── yokneam/              # יקנעם עילית (gis-net/complot API)
│   └── yokneam_scraper_auto.py
├── complot/              # ועדות על פלטפורמת Complot
│   ├── complot_scraper.py
│   ├── find_complot_ids.py
│   ├── רמת_גן/          (site_id=3)
│   ├── חולון/            (site_id=34)
│   ├── בת_ים/
│   ├── אור_יהודה/
│   └── רמת_השרון/
├── bartech/              # ועדות על פלטפורמת Bartech
│   ├── bartech_scraper.py
│   ├── קרית_אונו/       (city_code=ono)
│   └── אזור/             (city_code=azr)
├── sharepoint/           # ועדות על פלטפורמת SharePoint/muni.il
│   ├── sharepoint_scraper.py
│   ├── בני_ברק/
│   ├── גבעתיים/
│   └── הרצליה/
├── telaviv/              # תל אביב-יפו (אתר ייעודי)
│   └── telaviv_scraper.py
└── run_all_telaviv.py    # הרצת כל ועדות מחוז תל אביב
```

## התקנת תלויות
```bash
pip install requests lxml beautifulsoup4 openpyxl
```

## הרצה

### יקנעם עילית
```bash
cd yokneam
python yokneam_scraper_auto.py                    # כל המסמכים 2020-2026
python yokneam_scraper_auto.py --start-year 2026   # רק חדשים
python yokneam_scraper_auto.py --protocols-only    # רק פרוטוקולים
```

### ועדות Complot (רמת גן, חולון, בת ים, אור יהודה, רמת השרון)
```bash
cd complot
python find_complot_ids.py                         # מציאת Site IDs (פעם אחת)
python complot_scraper.py --site-id 3 --city-name "רמת_גן" --start-year 2020
python complot_scraper.py --site-id 34 --city-name "חולון" --start-year 2020
```

### ועדות Bartech (קרית אונו, אזור)
```bash
cd bartech
python bartech_scraper.py --city-code ono --city-name "קרית_אונו" --start-year 2020
python bartech_scraper.py --city-code azr --city-name "אזור" --start-year 2020
```

### ועדות SharePoint (בני ברק, גבעתיים, הרצליה)
```bash
cd sharepoint
python sharepoint_scraper.py --city bnei-brak --start-year 2020
python sharepoint_scraper.py --city givatayim --start-year 2020
python sharepoint_scraper.py --city herzliya --start-year 2020
```

### תל אביב-יפו
```bash
cd telaviv
python telaviv_scraper.py --start-year 2020
```

### כל מחוז תל אביב בפקודה אחת
```bash
python run_all_telaviv.py                          # הורדה מלאה
python run_all_telaviv.py --count-only             # רק ספירה
```

## לאחר הורדה
הקבצים מועלים לשיירפוינט באמצעות:
```bash
python ../../tools/upload_to_sharepoint.py
```
