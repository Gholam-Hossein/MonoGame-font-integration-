from PIL import Image
import json
import os

def merge_images(image_path1, image_path2, output_path, merge_side='bottom'):
    try:
        # باز کردن تصاویر و تبدیل به RGBA
        img1 = Image.open(image_path1).convert('RGBA')
        img2 = Image.open(image_path2).convert('RGBA')
        
        width1, height1 = img1.size
        width2, height2 = img2.size
        
        # تعیین ابعاد تصویر جدید
        if merge_side == 'bottom':
            new_width = max(width1, width2)
            new_height = height1 + height2
        else:  # merge_side == 'right'
            new_width = width1 + width2
            new_height = max(height1, height2)
        
        # ایجاد تصویر جدید با پس‌زمینه شفاف
        new_image = Image.new('RGBA', (new_width, new_height), (0, 0, 0, 0))
        new_image.paste(img1, (0, 0))
        new_image.paste(img2, (0, height1 if merge_side == 'bottom' else 0))
        
        # ذخیره تصویر خروجی
        new_image.save(output_path, quality=100)
        print(f"تصویر در {output_path} ذخیره شد. Bit Depth: 32 (RGBA)")
        return new_width, new_height, height1
    except FileNotFoundError:
        print(f"خطا: یکی از فایل‌های {image_path1} یا {image_path2} یافت نشد.")
        return None, None, None
    except Exception as e:
        print(f"خطا: {e}")
        return None, None, None

def merge_json_fonts(json_path1, json_path2, output_json_path, image_output_name, height1):
    try:
        # خواندن فایل‌های JSON
        with open(json_path1, 'r', encoding='utf-8') as f:
            font1 = json.load(f)
        with open(json_path2, 'r', encoding='utf-8') as f:
            font2 = json.load(f)
        
        # ایجاد JSON جدید
        merged_font = {
            "header": font1["header"],  # فقط از فونت اول
            "readers": font1["readers"],  # فقط از فونت اول
            "content": {
                "texture": {
                    "format": font1["content"]["texture"]["format"],
                    "export": image_output_name
                },
                "glyphs": [],
                "cropping": [],
                "characterMap": [],
                "verticalLineSpacing": font1["content"]["verticalLineSpacing"],  # فقط از فونت اول
                "horizontalSpacing": max(font1["content"]["horizontalSpacing"], font2["content"]["horizontalSpacing"]),
                "kerning": [],
                "defaultCharacter": font1["content"]["defaultCharacter"] or font2["content"]["defaultCharacter"]
            }
        }
        
        # ادغام گلیف‌ها (ابتدا فونت اول، سپس فونت دوم با تنظیم y)
        merged_font["content"]["glyphs"].extend(font1["content"]["glyphs"])
        for glyph in font2["content"]["glyphs"]:
            merged_font["content"]["glyphs"].append({
                "x": glyph["x"],
                "y": glyph["y"] + height1,
                "width": glyph["width"],
                "height": glyph["height"]
            })
        
        # ادغام cropping (ابتدا فونت اول، سپس فونت دوم)
        merged_font["content"]["cropping"].extend(font1["content"]["cropping"])
        merged_font["content"]["cropping"].extend(font2["content"]["cropping"])
        
        # ادغام characterMap (ابتدا فونت اول، سپس فونت دوم)
        merged_font["content"]["characterMap"].extend(font1["content"]["characterMap"])
        merged_font["content"]["characterMap"].extend(font2["content"]["characterMap"])
        
        # ادغام kerning (ابتدا فونت اول، سپس فونت دوم)
        merged_font["content"]["kerning"].extend(font1["content"]["kerning"])
        merged_font["content"]["kerning"].extend(font2["content"]["kerning"])
        
        # ذخیره JSON خروجی
        with open(output_json_path, 'w', encoding='utf-8') as f:
            json.dump(merged_font, f, ensure_ascii=False, indent=4)
        print(f"فایل JSON در {output_json_path} ذخیره شد.")
        
    except FileNotFoundError:
        print(f"خطا: یکی از فایل‌های {json_path1} یا {json_path2} یافت نشد.")
    except Exception as e:
        print(f"خطا: {e}")

def get_image_path_from_json(json_path):
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            font_data = json.load(f)
        image_path = font_data["content"]["texture"]["export"]
        # فرض می‌کنیم فایل تصویر در همان دایرکتوری فایل JSON است
        return os.path.join(os.path.dirname(json_path), image_path)
    except FileNotFoundError:
        print(f"خطا: فایل JSON {json_path} یافت نشد.")
        return None
    except KeyError:
        print(f"خطا: کلید 'content.texture.export' در فایل JSON {json_path} یافت نشد.")
        return None
    except Exception as e:
        print(f"خطا: {e}")
        return None

# مثال استفاده
try:
    # مسیر فایل‌های JSON
    json_path1 = "cardtitlefont.json"
    json_path2 = "cardtitlefont.2.json"
    output_image = "cardtitlefont.3.png"
    output_json = "cardtitlefont.3.json"
    
    # استخراج مسیر فایل‌های تصویر از JSON
    image_path1 = get_image_path_from_json(json_path1)
    image_path2 = get_image_path_from_json(json_path2)
    
    if image_path1 and image_path2:
        # ادغام تصاویر
        new_width, new_height, height1 = merge_images(image_path1, image_path2, output_image, merge_side='bottom')
        
        if new_width is not None:
            # ادغام JSON
            merge_json_fonts(json_path1, json_path2, output_json, image_output_name=output_image, height1=height1)
    else:
        print("خطا: نمی‌توان مسیر فایل‌های تصویر را استخراج کرد.")
        
except Exception as e:
    print(f"خطا: {e}")