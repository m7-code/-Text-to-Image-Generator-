from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from diffusers import StableDiffusionPipeline
import torch
from io import BytesIO
import base64

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load model (CPU)
pipe = StableDiffusionPipeline.from_pretrained(
    "runwayml/stable-diffusion-v1-5",
    torch_dtype=torch.float32
)
pipe = pipe.to("cpu")

class GenerateRequest(BaseModel):
    prompt: str

@app.get("/", response_class=HTMLResponse)
def index():
    return """
<!DOCTYPE html>
<html>
<head>
<title>Text to Image</title>
<link rel="stylesheet" href="/static/styles.css">
</head>
<body>
<h2>Text to Image (CPU)</h2>
<input id="prompt" placeholder="cat" />
<button onclick="generate()">Generate</button>
<p id="status"></p>
<img id="result" width="256"/>

<script>
function generate() {
  document.getElementById("status").innerText = "Generating... please wait (2–5 minutes)";
  fetch("/generate", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({prompt: document.getElementById("prompt").value})
  })
  .then(res => res.json())
  .then(data => {
    document.getElementById("result").src = "data:image/png;base64," + data.image;
    document.getElementById("status").innerText = "Done!";
  });
}
</script>
</body>
</html>
"""

@app.post("/generate")
def generate(req: GenerateRequest):
    image = pipe(
        req.prompt,
        num_inference_steps=10,   # MUCH faster on CPU
        guidance_scale=7.5
    ).images[0]

    buffer = BytesIO()
    image.save(buffer, format="PNG")
    img_base64 = base64.b64encode(buffer.getvalue()).decode()

    return {"image": img_base64}
