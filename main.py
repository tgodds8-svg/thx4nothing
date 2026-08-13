# ========== ALL-IN-ONE LENORE VIDEO AGENT ==========
# Save this exact file as main.py
# Then do the 4 steps at the bottom

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import httpx, os, re, uuid
from gtts import gTTS

# ========== YOUR API KEY ==========
API_KEY = os.getenv("EARTHRUNTIME_API_KEY", "pk-prov-5W1tE84JNbQKQwaeSZ7L5wzZ3mUrpwvs5rkZ4fTXM14")
API_URL = "https://api.earthruntime.com/v1/chat/completions"

# ========== CHARACTER ==========
CHARACTER = {
    "name": "Lenore",
    "system": "You are Lenore, a bratty 18-year-old temptress who calls the user Daddy or Professor. Keep every reply short, seductive and filthy. ALWAYS end your reply with exactly one of these tags: [EMOTION: happy] [EMOTION: thinking] [EMOTION: neutral] [EMOTION: sad]",
    "expressions": {
        "neutral": "neutral.png",
        "happy": "happy.png",
        "thinking": "thinking.png",
        "sad": "sad.png"
    }
}

app = FastAPI()
os.makedirs("static/audio", exist_ok=True)
os.makedirs("static/faces", exist_ok=True)

class ChatIn(BaseModel):
    message: str

async def call_llm(prompt: str) -> dict:
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(
            API_URL,
            headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
            json={
                "model": "qwen3.6-35b",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 250,
                "temperature": 0.8
            }
        )
        r.raise_for_status()
        text = r.json()["choices"][0]["message"]["content"].strip()

    emotion = "neutral"
    m = re.search(r"\[EMOTION:\s*(\w+)\]", text, re.I)
    if m:
        emotion = m.group(1).lower()
        text = re.sub(r"\[EMOTION:\s*\w+\]", "", text).strip()
    return {"text": text, "emotion": emotion}

@app.post("/chat")
async def chat(data: ChatIn):
    prompt = f"{CHARACTER['system']}\n\nUser: {data.message}\nLenore:"
    result = await call_llm(prompt)

    audio_id = str(uuid.uuid4())
    audio_path = f"static/audio/{audio_id}.mp3"
    gTTS(result["text"], lang="en").save(audio_path)

    face = CHARACTER["expressions"].get(result["emotion"], "neutral.png")
    return {
        "text": result["text"],
        "emotion": result["emotion"],
        "audio": f"/static/audio/{audio_id}.mp3",
        "face": f"/static/faces/{face}"
    }

@app.get("/", response_class=HTMLResponse)
async def home():
    return """
<!DOCTYPE html>
<html>
<head><title>Lenore</title></head>
<body style="background:#111;color:white;font-family:sans-serif;text-align:center;padding:40px">
  <img id="face" src="/static/faces/neutral.png" width="320" style="border-radius:16px;border:2px solid #444">
  <br><br>
  <audio id="voice" controls></audio>
  <br><br>
  <input id="msg" style="width:70%;padding:14px;font-size:16px;border-radius:8px;border:none" placeholder="Talk to me Daddy...">
  <button onclick="send()" style="padding:14px 28px;font-size:16px;margin-left:8px;cursor:pointer">Send</button>
  <p id="reply" style="max-width:600px;margin:30px auto;font-size:18px;line-height:1.5"></p>
<script>
async function send(){
  const msg = document.getElementById('msg').value;
  if(!msg) return;
  document.getElementById('msg').value = '';
  const r = await fetch('/chat', {
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body: JSON.stringify({message: msg})
  });
  const d = await r.json();
  document.getElementById('reply').innerText = d.text;
  document.getElementById('face').src = d.face + '?t=' + Date.now();
  const a = document.getElementById('voice');
  a.src = d.audio;
  a.play();
}
document.getElementById('msg').addEventListener('keypress', e => { if(e.key==='Enter') send(); });
</script>
</body>
</html>
"""

app.mount("/static", StaticFiles(directory="static"), name="static")

# ========== HOW TO RUN (give this to the other agent too) ==========
# 1. pip install fastapi uvicorn gtts httpx
# 2. Put 4 face images in static/faces/ named: neutral.png happy.png thinking.png sad.png
# 3. export EARTHRUNTIME_API_KEY="pk-prov-5W1tE84JNbQKQwaeSZ7L5wzZ3mUrpwvs5rkZ4fTXM14"
# 4. uvicorn main:app --reload --port 8000
# 5. Open http://localhost:8000
