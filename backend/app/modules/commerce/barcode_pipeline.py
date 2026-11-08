import re
import difflib
from PIL import Image, ImageEnhance, ImageFilter, ImageOps
import zxingcpp
import pytesseract

def decode_barcode_robust(img: Image.Image, active_skus: list[str]) -> tuple[str | None, str | None]:
    # 1. Direct pass
    res = zxingcpp.read_barcode(img, try_rotate=True, try_downscale=True, try_invert=True)
    if res and res.text:
        return res.text.strip(), str(res.format)

    # Prepare variations
    w, h = img.size
    crops = [
        img,
        img.crop((int(w * 0.15), int(h * 0.15), int(w * 0.85), int(h * 0.85))), # 70% center
        img.crop((int(w * 0.25), int(h * 0.25), int(w * 0.75), int(h * 0.75))), # 50% center
        img.crop((int(w * 0.05), int(h * 0.3), int(w * 0.95), int(h * 0.7))),  # horizontal belt
    ]

    for crop in crops:
        # Grayscale
        gray = crop.convert('L')
        
        # De-moiré for LCD screens (blur out pixel grid)
        for blur_radius in [0, 0.8, 1.2]:
            blurred = gray.filter(ImageFilter.GaussianBlur(radius=blur_radius)) if blur_radius > 0 else gray
            
            # High contrast
            enhanced = ImageEnhance.Contrast(blurred).enhance(2.2)
            sharp = ImageEnhance.Sharpness(enhanced).enhance(1.8)
            
            for binarizer in [zxingcpp.Binarizer.LocalAverage, zxingcpp.Binarizer.GlobalHistogram]:
                res = zxingcpp.read_barcode(sharp, binarizer=binarizer, try_rotate=True, try_downscale=True, try_invert=True)
                if res and res.text:
                    return res.text.strip(), str(res.format)
                
                # Try inverted
                inverted = ImageOps.invert(sharp)
                res = zxingcpp.read_barcode(inverted, binarizer=binarizer, try_rotate=True, try_downscale=True)
                if res and res.text:
                    return res.text.strip(), str(res.format)

    # 2. OCR Fallback (reads text printed below barcode or on garment tag)
    for crop in crops[:2]:
        gray = crop.convert('L')
        enhanced = ImageEnhance.Contrast(gray).enhance(2.5)
        text = pytesseract.image_to_string(enhanced, config='--psm 6').strip()
        
        # Look for exact or fuzzy SKU matches in active_skus
        words = re.findall(r'[A-Za-z0-9_-]{5,}', text)
        for w_word in words:
            clean_word = w_word.upper().replace(' ', '').replace('O', '0')
            # Check exact match
            for sku in active_skus:
                if sku.upper() == clean_word:
                    return sku, "OCR-Exact"
            # Check close match
            matches = difflib.get_close_matches(clean_word, active_skus, n=1, cutoff=0.75)
            if matches:
                return matches[0], "OCR-Fuzzy"

    return None, None
