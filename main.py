import os, re, tempfile
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse, HTMLResponse
from PIL import Image
import pytesseract
from dateutil import parser
from ics import Calendar, Event

app = FastAPI(title="Syllabus Engine")

@app.get("/", response_class=HTMLResponse)
def index():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Syllabus Engine</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
    </head>
    <body style="font-family:sans-serif; text-align:center; padding:40px; background:#f4f4f9;">
        <div style="max-width:500px; margin:auto; background:white; padding:30px; border-radius:10px; box-shadow:0 4px 6px rgba(0,0,0,0.1);">
            <h2>Syllabus to Calendar</h2>
            <p>Upload a photo of your syllabus to generate a downloadable .ics calendar file.</p>
            <form action="/upload" enctype="multipart/form-data" method="post" style="margin-top:20px;">
                <input name="file" type="file" accept="image/*" required style="margin-bottom:15px;"><br>
                <input type="submit" value="Convert to Calendar (.ics)" style="padding:10px 20px; background:#007bff; color:white; border:none; border-radius:5px; cursor:pointer;">
            </form>
        </div>
    </body>
    </html>
    """

@app.post("/upload")
async def process_syllabus(file: UploadFile = File(...)):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    try:
        raw_text = pytesseract.image_to_string(Image.open(tmp_path))
        cal = Calendar()
        lines = raw_text.split('\n')
        date_pattern = r'(\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2}|\b\d{1,2}/\d{1,2}(?:/\d{2,4})?)'
        count = 0
        for line in lines:
            match = re.search(date_pattern, line, re.IGNORECASE)
            if match:
                date_str = match.group(0)
                try:
                    parsed_date = parser.parse(date_str, fuzzy=True)
                    title = line.replace(date_str, "").strip(" :-|") or "Course Exam / Deadline"
                    e = Event()
                    e.name = title
                    e.begin = parsed_date.strftime("%Y-%m-%d 09:00:00")
                    e.make_all_day()
                    cal.events.add(e)
                    count += 1
                except Exception:
                    continue

        output_path = tempfile.NamedTemporaryFile(delete=False, suffix=".ics").name
        with open(output_path, "w") as f:
            f.writelines(cal.serialize_iter())

        return FileResponse(output_path, filename="course_schedule.ics", media_type="text/calendar")
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
