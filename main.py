from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
import vtracer
import rembg
from PIL import Image
import io
import base64

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {"durum": "Çalışıyor ✅"}

@app.post("/vektore-cevir")
async def vektore_cevir(dosya: UploadFile = File(...)):
    try:
        icerik = await dosya.read()
        img = Image.open(io.BytesIO(icerik))
        if img.mode != "RGB":
            img = img.convert("RGB")
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        png_bytes = buffer.getvalue()
        svg = vtracer.convert_raw_image_to_svg(
            png_bytes,
            img_format='png',
            colormode='color',
            hierarchical='stacked',
            mode='spline',
            filter_speckle=4,
            color_precision=6,
            layer_difference=16,
            corner_threshold=60,
            length_threshold=4.0,
            max_iterations=10,
            splice_threshold=45,
            path_precision=3
        )
        return Response(
            content=svg,
            media_type="image/svg+xml",
            headers={"Content-Disposition": "attachment; filename=cikti.svg"}
        )
    except Exception as e:
        return {"hata": str(e)}

@app.post("/arka-plan-sil")
async def arka_plan_sil(dosya: UploadFile = File(...)):
    try:
        icerik = await dosya.read()
        sonuc = rembg.remove(icerik)
        return Response(
            content=sonuc,
            media_type="image/png",
            headers={"Content-Disposition": "attachment; filename=arkaplan-silindi.png"}
        )
    except Exception as e:
        return {"hata": str(e)}
