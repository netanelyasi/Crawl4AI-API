import requests
import time
import json
import os

# תצורת ה-API
API_URL = "https://your-render-app-url.onrender.com"  # עדכן ל-URL האמיתי שלך ב-Render
API_KEY = "your-api-key"  # עדכן למפתח ה-API שלך

# פונקציה לביצוע זחילה ולקבלת התוצאות
def crawl_website(url, depth=0, max_pages=10, strategy="bfs", headless=True, extract_images=False):
    # שליחת בקשת זחילה
    headers = {
        "X-API-Key": API_KEY,
        "Content-Type": "application/json"
    }
    
    payload = {
        "url": url,
        "depth": depth,
        "max_pages": max_pages,
        "strategy": strategy,
        "headless": headless,
        "extract_images": extract_images,
        "extract_links": True
    }
    
    # שליחת הבקשה
    response = requests.post(f"{API_URL}/api/crawl", headers=headers, json=payload)
    
    if response.status_code != 200:
        print(f"שגיאה בשליחת הבקשה: {response.text}")
        return None
    
    result = response.json()
    task_id = result["task_id"]
    print(f"משימת זחילה נוצרה בהצלחה. מזהה משימה: {task_id}")
    
    # המתנה להשלמת המשימה
    completed = False
    while not completed:
        time.sleep(2)  # המתנה של 2 שניות בין בדיקות
        
        status_response = requests.get(f"{API_URL}/api/task/{task_id}", headers=headers)
        
        if status_response.status_code != 200:
            print(f"שגיאה בבדיקת סטטוס: {status_response.text}")
            return None
        
        status = status_response.json()
        print(f"סטטוס משימה: {status['status']}")
        
        if status["status"] in ["completed", "failed"]:
            completed = True
    
    # קבלת תוצאות
    if status["status"] == "completed":
        result_response = requests.get(f"{API_URL}/api/result/{task_id}", headers=headers)
        
        if result_response.status_code != 200:
            print(f"שגיאה בקבלת תוצאות: {result_response.text}")
            return None
        
        return result_response.json()
    else:
        print("המשימה נכשלה.")
        return None

# דוגמה לשימוש
if __name__ == "__main__":
    # הגדרת URL לזחילה
    target_url = "https://www.example.com"
    
    # ביצוע זחילה בסיסית
    result = crawl_website(
        url=target_url,
        depth=0,  # זחילה של דף אחד בלבד
        extract_images=True
    )
    
    if result:
        print("\n--- תוצאות זחילה ---")
        print(f"URL: {result['url']}")
        print(f"אורך Markdown: {len(result['markdown']) if result['markdown'] else 0} תווים")
        
        if result['links']:
            print(f"מספר קישורים: {len(result['links'])}")
            print("קישורים לדוגמה:")
            for link in result['links'][:5]:  # מציג 5 קישורים לדוגמה
                print(f"  - {link}")
        
        if result['images']:
            print(f"מספר תמונות: {len(result['images'])}")
        
        # שמירת ה-Markdown לקובץ
        if result['markdown']:
            with open("crawl_result.md", "w", encoding="utf-8") as f:
                f.write(result['markdown'])
            print("Markdown נשמר בהצלחה לקובץ 'crawl_result.md'")
