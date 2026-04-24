from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
import vtracer
import rembg
from PIL import Image
import io

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
        
        # Görsel tipine göre optimize et
        genislik, yukseklik = img.size
        
        # Büyük görselleri küçült (kalite koruyarak)
        maks_boyut = 1024
        if genislik > maks_boyut or yukseklik > maks_boyut:
            img.thumbnail((maks_boyut, maks_boyut), Image.LANCZOS)
        
        if img.mode != "RGB":
            img = img.convert("RGB")
            
        buffer = io.BytesIO()
        img.save(buffer, format="PNG", optimize=True)
        png_bytes = buffer.getvalue()
        
        svg = vtracer.convert_raw_image_to_svg(
            png_bytes,
            img_format='png',
            colormode='color',
            hierarchical='stacked',
            mode='spline',
            filter_speckle=2,        # Daha az gürültü filtresi
            color_precision=8,        # Daha yüksek renk hassasiyeti
            layer_difference=8,       # Daha ince katman ayrımı
            corner_threshold=60,
            length_threshold=3.0,     # Daha ince detaylar
            max_iterations=20,        # Daha fazla iterasyon
            splice_threshold=30,
            path_precision=5          # Daha yüksek path hassasiyeti
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
        
        # Önce boyutu optimize et
        img = Image.open(io.BytesIO(icerik))
        maks_boyut = 1024
        if max(img.size) > maks_boyut:
            img.thumbnail((maks_boyut, maks_boyut), Image.LANCZOS)
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
