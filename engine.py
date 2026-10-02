import sys, os, re
from PIL import Image
import pytesseract
from dateutil import parser
from ics import Calendar, Event

IMAGE_PATH = sys.argv[1] if len(sys.argv) > 1 else "syllabus.jpg"
OUTPUT_ICS = "course_schedule.ics"

def parse_syllabus_ocr(image_path):
    print("[*] Running lightweight Tesseract OCR...")
    raw_text = pytesseract.image_to_string(Image.open(image_path))
    cal = Calendar()
    lines = raw_text.split("\n")
    date_pattern = r"(\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2}|\b\d{1,2}/\d{1,2}(?:/\d{2,4})?)"
    count = 0
    for line in lines:
        match = re.search(date_pattern, line, re.IGNORECASE)
        if match:
            date_str = match.group(0)
            try:
                parsed_date = parser.parse(date_str, fuzzy=True)
                title = line.replace(date_str, "").strip(" :-|")
                if not title or len(title) < 3:
                    title = "Course Exam / Deadline"
                e = Event()
                e.name = title
                e.begin = parsed_date.strftime("%Y-%m-%d 09:00:00")
                e.make_all_day()
                cal.events.add(e)
                count += 1
                print(f"  + Extracted: {parsed_date.strftime("%Y-%m-%d")} | {title}")
            except Exception:
                continue
    with open(OUTPUT_ICS, "w") as f:
        f.writelines(cal.serialize_iter())
    print(f"\n[+] Success! Created {OUTPUT_ICS} with {count} events.")

if __name__ == "__main__":
    if not os.path.exists(IMAGE_PATH):
        print(f"[-] Error: '{IMAGE_PATH}' not found in ~/syllabus_engine/")
        sys.exit(1)
    parse_syllabus_ocr(IMAGE_PATH)
