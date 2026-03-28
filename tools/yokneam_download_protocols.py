#!/usr/bin/env python3
"""
Script to download protocols and decisions from Yokneam Illit Planning Committee
https://vaada.yoqneam.org.il/

Downloads all protocols and agendas from committee meetings.
Run: python3 yokneam_download_protocols.py
"""

import os
import requests
import time
import csv

BASE_URL = "https://archive.gis-net.co.il/Yoqneam/Pirsumim"

# All 64 documents collected from the site (Jan 2025 - Mar 2026)
# Format: (meetingNumber, committeeType, date, docType, folder, guid)
DOCUMENTS = [
    # רשות רישוי מקומית (committeeType=1)
    ("20250001", "1", "08/01/2025", "סדר יום", "776", "8314bba3-82b5-421b-b2e2-24531d13aff3"),
    ("20250001", "1", "08/01/2025", "פרוטוקול החלטות", "775", "6599c510-bf78-4e58-8b62-ad3c6d73fb03"),
    ("20250002", "1", "25/02/2025", "סדר יום", "776", "836b2a29-c955-4e8d-97d4-f2c925f1ffbb"),
    ("20250002", "1", "25/02/2025", "פרוטוקול החלטות רישוי", "775", "31dd6042-d2e0-4839-9fe2-32955e963da0"),
    ("20250003", "1", "25/03/2025", "סדר יום", "776", "c0199981-8409-4d67-a980-dc856ce6a24a"),
    ("20250003", "1", "25/03/2025", "פרוטוקול החלטות", "775", "1e527331-9001-46ca-980c-ad6a54730d97"),
    ("20250004", "1", "30/04/2025", "סדר יום", "776", "b3d9ba12-e528-4ee6-ada4-d2d6a9942824"),
    ("20250004", "1", "30/04/2025", "פרוטוקול החלטות", "775", "93b6539f-71a8-4f69-90a9-a744830405cb"),
    ("20250005", "1", "27/05/2025", "סדר יום", "776", "2a473312-0e1b-4364-8d10-72b2b99df646"),
    ("20250005", "1", "27/05/2025", "פרוטוקול החלטות", "775", "a6f7fb0b-7065-4748-b28a-6f3ae4dfe65d"),
    ("20250006", "1", "24/06/2025", "סדר יום", "776", "ec5a39c0-b907-4ac4-bd09-0f4bd76d36ae"),
    ("20250006", "1", "24/06/2025", "פרוטוקול", "775", "5b6d8589-dbb5-4e95-91b3-39f10139c044"),
    ("20250008", "1", "14/07/2025", "סדר יום", "776", "f2298366-8f63-41ba-bde0-4f9b2083a9ed"),
    ("20250008", "1", "14/07/2025", "פרוטוקול", "775", "a763d8f4-fa4f-43a7-b0ff-5bee4dc70b0e"),
    ("20250009", "1", "02/09/2025", "סדר יום", "776", "3f5211bf-744b-46ce-90db-7d2ffe988697"),
    ("20250009", "1", "02/09/2025", "פרוטוקול חתום", "775", "5a444383-c751-4a9c-a5f0-525fb80e79cc"),
    ("20250010", "1", "10/08/2025", "סדר יום", "776", "31deecfe-5125-489e-825e-732d430f1825"),
    ("20250010", "1", "10/08/2025", "פרוטוקול החלטות", "775", "fb3bf418-0422-4480-ba97-2b55a6093cb2"),
    ("20250011", "1", "28/10/2025", "סדר יום", "776", "9c9f181d-8748-4b3a-a6f6-fcf833cb3d32"),
    ("20250011", "1", "28/10/2025", "פרוטוקול החלטות", "775", "6003bd3e-2292-4d55-8d58-7e75288f973e"),
    ("20250012", "1", "28/10/2025", "סדר יום", "776", "6250e442-851e-49ca-9f2f-8efe7ea8bd63"),
    ("20250012", "1", "28/10/2025", "פרוטוקול החלטות", "775", "32598428-c959-432f-91ac-4e30f4d48227"),
    ("20250013", "1", "19/11/2025", "סדר יום", "776", "ff95a357-8eac-445a-b015-1eff3deb4720"),
    ("20250013", "1", "19/11/2025", "פרוטוקול החלטות", "775", "2374e5ce-93ff-404f-8a0e-d010dd470b9f"),
    ("20250014", "1", "24/12/2025", "פרוטוקול החלטות", "775", "375fc68e-d5f3-40b5-b79a-d7bf0489963f"),
    ("20260001", "1", "20/01/2026", "פרוטוקול החלטות", "775", "96f22008-46f6-4594-baa8-f552d96854a0"),
    ("20260002", "1", "23/03/2026", "סדר יום", "776", "a3584fa1-4517-48f4-901d-dee9723ad962"),
    ("20260002", "1", "23/03/2026", "פרוטוקול החלטות", "775", "e144af3d-f2e0-4703-9340-ef1c748f45c3"),

    # ועדת משנה (committeeType=2)
    ("20250001", "2", "27/01/2025", "סדר יום", "776", "3228f707-f75c-42e4-a73e-14dcc184b243"),
    ("20250001", "2", "27/01/2025", "פרוטוקול החלטות", "775", "8987d682-848f-4721-9aa1-8efcfa7f7fbf"),
    ("20250001", "2", "27/01/2025", "פרוטוקול מהלך דיון", "775", "40fc7f09-aee6-43db-8fc4-e06d1110443a"),
    ("20250002", "2", "25/02/2025", "סדר יום ועדת משנה", "776", "6cfd560c-30fb-4653-8769-6593f301c423"),
    ("20250002", "2", "25/02/2025", "סדר יום מליאת הועדה", "776", "eb986746-4d28-484b-b603-787bb5a8f55a"),
    ("20250002", "2", "25/02/2025", "פרוטוקול החלטות", "775", "98023f92-90d7-4f63-8f2b-44da2aab5d2c"),
    ("20250003", "2", "12/03/2025", "סדר יום", "776", "519179e3-4a04-4466-bd09-11fe541a9c99"),
    ("20250003", "2", "12/03/2025", "פרוטוקול החלטות", "775", "e4c6154b-7868-4188-975f-34419724a6b4"),
    ("20250003", "2", "12/03/2025", "פרוטוקול מהלך דיון", "775", "c5d752d5-2206-4fdb-894a-b2be709d7b47"),
    ("20250004", "2", "07/04/2025", "סדר יום", "776", "7b3b241c-c116-4759-aec4-2eec70b0cf4c"),
    ("20250004", "2", "07/04/2025", "פרוטוקול החלטות", "775", "6e2b5db5-1efe-41ae-b410-590b487e66bc"),
    ("20250004", "2", "07/04/2025", "פרוטוקול מהלך דיון", "775", "2c26313b-a3f8-4b9d-bbe8-0a9fd3ac4fc7"),
    ("20250005", "2", "12/05/2025", "סדר יום", "776", "de58e1b9-ef96-4dae-89e4-a6a862a72e57"),
    ("20250005", "2", "12/05/2025", "פרוטוקול החלטות", "775", "489e966e-7e1a-44d6-aa9a-645553f222ec"),
    ("20250005", "2", "12/05/2025", "פרוטוקול מהלך דיון", "775", "e2f0a54c-6873-4b63-af54-33c753e6189e"),
    ("20250006", "2", "30/06/2025", "סדר יום", "776", "e7a9a8cb-22e3-4b4b-a789-fa8bd5cd0a05"),
    ("20250006", "2", "30/06/2025", "פרוטוקול החלטות", "775", "3be543d1-bebb-40d4-a303-f92def7bfd20"),
    ("20250006", "2", "30/06/2025", "פרוטוקול מהלך דיון", "775", "fd275607-6721-46e0-a43a-5256bf16f24a"),
    ("20250007", "2", "30/07/2025", "סדר יום", "776", "428a8f8d-da18-4d98-ba44-113c0fd35174"),
    ("20250007", "2", "30/07/2025", "פרוטוקול החלטות", "775", "847c7494-7ec9-4818-8c7d-8480909dac65"),
    ("20250007", "2", "30/07/2025", "פרוטוקול מהלך דיון", "775", "e9a62dfd-b498-47ed-b292-c464a114d28f"),
    ("20250008", "2", "03/09/2025", "סדר יום", "776", "4eb26649-bb4e-49ef-b8b9-3c05f1efce13"),
    ("20250008", "2", "03/09/2025", "פרוטוקול החלטות", "775", "88dca532-d0e3-406f-b7da-fc5fa325570a"),
    ("20250008", "2", "03/09/2025", "פרוטוקול מהלך דיון", "775", "4f3b0954-de84-4714-9c4d-f7add2f77918"),
    ("20250009", "2", "29/10/2025", "סדר יום", "776", "2dcf7d0f-67f5-4a02-b60d-510199fe0cd9"),
    ("20250009", "2", "29/10/2025", "פרוטוקול החלטות", "775", "ebef5676-22f8-43b3-8f9b-13952695ba65"),
    ("20250009", "2", "29/10/2025", "תמליל", "775", "5b80404d-d5f9-49bd-8fc5-01001e121dd0"),
    ("20250010", "2", "10/12/2025", "סדר יום", "776", "49029720-c249-4c2c-be6b-e7f62376ed4b"),
    ("20250010", "2", "10/12/2025", "פרוטוקול החלטות", "775", "dd584c8f-e3da-41e2-a49f-7ae3ed5182ce"),
    ("20260001", "2", "21/01/2026", "פרוטוקול החלטות", "775", "f997c068-2858-40b4-bd6f-a67c69ad456e"),
    ("20260001", "2", "21/01/2026", "פרוטוקול דיון", "775", "bc2e7c93-06b4-4e39-89e1-ac58b4e69bb1"),
    ("20260002", "2", "22/02/2026", "פרוטוקול החלטות", "775", "c27b44ce-6a93-4af9-bd75-c5f6e176b2bb"),
    ("20260003", "2", "29/03/2026", "סדר יום", "776", "396db680-0a1b-4791-8180-d38dd2fceef9"),

    # מליאת הועדה (committeeType=3)
    ("20260001", "3", "29/03/2026", "סדר יום מליאה", "776", "f1e4f2e5-681b-4237-9cd4-46f60e441e50"),

    # ועדת שימור (committeeType=4)
    ("20250003", "4", "09/06/2025", "הזמנה לוועדת שימור", "776", "435e8f10-214c-4ccd-baf3-c99b0d1ffbb5"),
    ("20250003", "4", "09/06/2025", "פרוטוקול החלטות", "775", "f6634894-4984-4ba5-a0dd-d1a6d8c8bb0e"),
]

COMMITTEE_NAMES = {
    "1": "רשות_רישוי_מקומית",
    "2": "ועדת_משנה",
    "3": "מליאת_הועדה",
    "4": "ועדת_שימור",
}


def download_file(url, filepath):
    """Download a file from URL and save to filepath"""
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        with open(filepath, 'wb') as f:
            f.write(response.content)
        return True, len(response.content)
    except Exception as e:
        print(f"  ERROR downloading {url}: {e}")
        return False, 0


def main():
    import sys
    sys.stdout.reconfigure(encoding='utf-8')

    output_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'yokneam_protocols')
    os.makedirs(output_dir, exist_ok=True)

    for dirname in COMMITTEE_NAMES.values():
        os.makedirs(os.path.join(output_dir, dirname), exist_ok=True)

    csv_path = os.path.join(output_dir, "documents_index.csv")
    with open(csv_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["meeting_number", "committee_type", "committee_name", "date", "doc_type", "url", "local_file", "success", "size_bytes"])

    total = len(DOCUMENTS)
    success = 0
    failed = 0
    total_size = 0

    print(f"Downloading {total} documents from Yokneam Illit Planning Committee...")
    print("=" * 70)

    for i, (meeting_num, comm_type, date, doc_type, folder, guid) in enumerate(DOCUMENTS):
        url = f"{BASE_URL}/{folder}/{guid}.pdf"
        committee_dir = COMMITTEE_NAMES.get(comm_type, "other")
        date_str = date.replace("/", "-")
        doc_type_clean = doc_type.replace("/", "-").replace(" ", "_")
        filename = f"{date_str}_{meeting_num}_{doc_type_clean}.pdf"
        filepath = os.path.join(output_dir, committee_dir, filename)

        print(f"[{i+1}/{total}] {date} | {committee_dir} | {doc_type}")

        downloaded, size = download_file(url, filepath)
        if downloaded:
            success += 1
            total_size += size
            print(f"  OK -> {filename} ({size:,} bytes)")
        else:
            failed += 1

        with open(csv_path, 'a', newline='', encoding='utf-8-sig') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([meeting_num, comm_type, committee_dir, date, doc_type, url, filepath,
                           "yes" if downloaded else "no", size])

        time.sleep(0.3)

    print("=" * 70)
    print(f"Done! {success} downloaded, {failed} failed. Total size: {total_size:,} bytes")
    print(f"Index saved to: {csv_path}")


if __name__ == "__main__":
    main()
