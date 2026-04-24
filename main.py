from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
import rembg
from PIL import Image
import io
import httpx
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
        
        # Görseli optimize et
        img = Image.open(io.BytesIO(icerik))
        if max(img.size) > 1024:
            img.thumbnail((1024, 1024), Image.LANCZOS)
        if img.mode != "RGB":
            img = img.convert("RGB")
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        png_bytes = buffer.getvalue()
        
        # Vector.express API'ye gönder
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://vector.express/api/v2/public/convert/png/svg/",
                content=png_bytes,
                headers={"Content-Type": "image/png"}
            )
        
        if response.status_code == 200:
            return Response(
                content=response.content,
                media_type="image/svg+xml",
                headers={"Content-Disposition": "attachment; filename=cikti.svg"}
            )
        else:
            # Yedek: VTracer kullan
            import vtracer
            svg = vtracer.convert_raw_image_to_svg(
                png_bytes,
                img_format='png',
                colormode='color',
                hierarchical='stacked',
                mode='spline',
                filter_speckle=2,
                color_precision=8,
                layer_difference=8,
                corner_threshold=60,
                length_threshold=3.0,
                max_iterations=20,
                splice_threshold=30,
                path_precision=5
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
        img = Image.open(io.BytesIO(icerik))
        if max(img.size) > 1024:
            img.thumbnail((1024, 1024), Image.LANCZOS)
            buffer = io.BytesIO()
            img.save(buffer, format="PNG")
            icerik = buffer.getvalue()
        
        sonuc = rembg.remove(
            icerik,
            alpha_matting=True,
            alpha_matting_foreground_threshold=240,
            alpha_matting_background_threshold=10,
            alpha_matting_erode_size=10
        )
        
        return Response(
            content=sonuc,
            media_type="image/png",
            headers={"Content-Disposition": "attachment; filename=arkaplan-silindi.png"}
        )
    except Exception as e:
        return {"hata": str(e)}
