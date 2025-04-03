# שרת API ל-Crawl4AI

שרת API פשוט המבוסס על FastAPI לשימוש ב-Crawl4AI, שניתן להעלות בקלות לשירות Render.

## תוכן עניינים

- [תכונות](#תכונות)
- [תיקיות הפרויקט](#תיקיות-הפרויקט)
- [התקנה מקומית](#התקנה-מקומית)
- [העלאה ל-Render](#העלאה-ל-render)
- [שימוש בAPI](#שימוש-בapi)
- [שילוב עם n8n](#שילוב-עם-n8n)

## תכונות

- ✅ נקודות קצה (Endpoints) לביצוע זחילת אתרים
- ✅ תמיכה בזחילה עמוקה (עם אסטרטגיות BFS/DFS/BestFirst)
- ✅ אחזור תוכן בפורמט Markdown
- ✅ חילוץ קישורים ותמונות
- ✅ אבטחה בסיסית באמצעות מפתח API
- ✅ מוכן להעלאה ל-Render
- ✅ דוגמאות שימוש כולל אינטגרציה עם n8n

## תיקיות הפרויקט

```
crawl4ai-api/
├── main.py              # קוד ראשי של השרת
├── requirements.txt     # דרישות Python
├── Dockerfile           # להרצה ב-Docker
├── render.yaml          # הגדרות Render
├── example_client.py    # קוד לדוגמה
└── README.md            # תיעוד
```

## התקנה מקומית

### דרישות מקדימות

- Python 3.10 ומעלה
- pip (מנהל חבילות Python)

### צעדי התקנה

1. הורד את קוד המקור:

```bash
git clone https://github.com/your-username/crawl4ai-api.git
cd crawl4ai-api
```

2. צור סביבת וירטואלית והתקן את הדרישות:

```bash
python -m venv venv
source venv/bin/activate  # במערכות Linux/macOS
# או
venv\Scripts\activate  # במערכות Windows

pip install -r requirements.txt
```

3. הרץ את התקנת הדפדפן של Playwright:

```bash
playwright install --with-deps chromium
```

4. הפעל את השרת:

```bash
uvicorn main:app --reload
```

השרת יפעל בכתובת http://localhost:8000.

## העלאה ל-Render

1. צור חשבון ב-[Render](https://render.com/) (אם אין לך).

2. התחבר ל-GitHub והעלה את הקוד למאגר.

3. ב-Render, בחר "New" ואז "Blueprint".

4. חבר את המאגר שלך מ-GitHub.

5. Render יזהה את ה-`render.yaml` ויתקין אוטומטית את השירות.

6. שים לב למפתח ה-API שנוצר עבורך - תמצא אותו בהגדרות הסביבה של השירות ב-Render.

## שימוש בAPI

### נקודות קצה זמינות

- `POST /api/crawl`: התחלת משימת זחילה חדשה
- `GET /api/task/{task_id}`: בדיקת סטטוס משימה
- `GET /api/result/{task_id}`: קבלת תוצאות משימה
- `GET /api/health`: בדיקת בריאות השירות

### דוגמת שימוש בPython

ראה את הקובץ `example_client.py` לדוגמה מלאה.

```python
import requests

# הגדרות
API_URL = "https://your-render-app-url.onrender.com"
API_KEY = "your-api-key"

# שליחת משימת זחילה
headers = {"X-API-Key": API_KEY, "Content-Type": "application/json"}
payload = {"url": "https://www.example.com", "depth": 0}

response = requests.post(f"{API_URL}/api/crawl", headers=headers, json=payload)
task_id = response.json()["task_id"]

# קבלת תוצאות
result = requests.get(f"{API_URL}/api/result/{task_id}", headers=headers)
data = result.json()
print(data["markdown"])
```

## שילוב עם n8n

n8n הוא כלי אוטומציה ללא קוד שמאפשר לך ליצור תהליכי עבודה אוטומטיים.

### הגדרת אישורים (Credentials)

1. ב-n8n, צור אישור חדש מסוג `HTTP Header Auth`
2. הוסף את שם המפתח `X-API-Key` ואת הערך שלו (מפתח ה-API שקיבלת מ-Render)

### יצירת תהליך עבודה

ראה את הקובץ `n8n-workflow.json` עבור תהליך עבודה מלא לדוגמה שמבצע:

1. שליחת בקשת זחילת אתר
2. בדיקת סטטוס המשימה עד להשלמתה
3. קבלת התוצאות ועיבודם

## סימוכין ורישיון

API זה מבוסס על הספרייה [Crawl4AI](https://github.com/unclecode/crawl4ai) וכפוף לתנאי הרישיון שלה.
