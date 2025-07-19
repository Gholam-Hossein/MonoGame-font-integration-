from PIL import Image
import json
import os
import glob

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

def batch_merge_fonts(input_folder, output_folder):
    # اطمینان از وجود پوشه خروجی
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    # پیدا کردن تمام فایل‌های JSON در پوشه ورودی
    json_files = glob.glob(os.path.join(input_folder, "*.json"))
    
    # پیدا کردن جفت‌های فایل (name.json و name_backup.json)
    pairs = []
    for json_file in json_files:
        if not json_file.endswith("_backup.json"):
            base_name = os.path.basename(json_file).replace(".json", "")
            backup_file = os.path.join(input_folder, f"{base_name}_backup.json")
            if os.path.exists(backup_file):
                pairs.append((json_file, backup_file))
    
    if not pairs:
        print("خطا: هیچ جفت فایل JSON (name.json و name_backup.json) در پوشه ورودی یافت نشد.")
        return
    
    # پردازش هر جفت فایل
    for json_path1, json_path2 in pairs:
        try:
            # استخراج نام پایه فایل
            base_name = os.path.basename(json_path1).replace(".json", "")
            output_json = os.path.join(output_folder, f"merged_{base_name}.json")
            output_image = os.path.join(output_folder, f"merged_{base_name}.png")
            
            # استخراج مسیر فایل‌های تصویر
            image_path1 = get_image_path_from_json(json_path1)
            image_path2 = get_image_path_from_json(json_path2)
            
            if image_path1 and image_path2:
                # ادغام تصاویر
                new_width, new_height, height1 = merge_images(image_path1, image_path2, output_image, merge_side='bottom')
                
                if new_width is not None:
                    # ادغام JSON
                    merge_json_fonts(json_path1, json_path2, output_json, os.path.basename(output_image), height1)
            else:
                print(f"خطا: نمی‌توان مسیر فایل‌های تصویر را برای {json_path1} یا {json_path2} استخراج کرد.")
                
        except Exception as e:
            print(f"خطا در پردازش جفت {json_path1} و {json_path2}: {e}")
    
    print("پردازش گروهی تکمیل شد.")

# مثال استفاده
try:
    input_folder = "unpacked"  # پوشه ورودی
    output_folder = "output_fonts"  # پوشه خروجی
    
    batch_merge_fonts(input_folder, output_folder)
    
except Exception as e:
    print(f"خطا: {e}")