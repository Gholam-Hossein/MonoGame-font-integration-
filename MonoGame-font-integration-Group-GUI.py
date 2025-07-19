import sys
import os
import json
import glob
from PIL import Image
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLineEdit, QLabel, QCheckBox, QTextEdit, QFileDialog)
from PyQt6.QtCore import Qt

class FontMergerWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ادغام گروهی فونت‌های MonoGame")
        self.setGeometry(100, 100, 600, 500)

        # ویجت اصلی و لایه‌بندی
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout()
        main_widget.setLayout(layout)

        # بخش انتخاب پوشه ورودی
        input_layout = QHBoxLayout()
        self.input_folder_edit = QLineEdit()
        self.input_folder_edit.setPlaceholderText("پوشه ورودی را انتخاب کنید")
        input_browse_btn = QPushButton("مرور")
        input_browse_btn.clicked.connect(self.browse_input_folder)
        input_layout.addWidget(QLabel("پوشه ورودی:"))
        input_layout.addWidget(self.input_folder_edit)
        input_layout.addWidget(input_browse_btn)
        layout.addLayout(input_layout)

        # بخش انتخاب پوشه خروجی
        output_layout = QHBoxLayout()
        self.output_folder_edit = QLineEdit()
        self.output_folder_edit.setPlaceholderText("پوشه خروجی را انتخاب کنید")
        output_browse_btn = QPushButton("مرور")
        output_browse_btn.clicked.connect(self.browse_output_folder)
        output_layout.addWidget(QLabel("پوشه خروجی:"))
        output_layout.addWidget(self.output_folder_edit)
        output_layout.addWidget(output_browse_btn)
        layout.addLayout(output_layout)

        # بخش انتخاب منبع برای مقادیر
        options_layout = QVBoxLayout()
        options_layout.addWidget(QLabel("انتخاب منبع برای مقادیر:"))
        self.options = {
            "header": QCheckBox("header از فونت دوم (اگر تیک نزنید، از فونت اول)"),
            "readers": QCheckBox("readers از فونت دوم"),
            "format": QCheckBox("format از فونت دوم"),
            "verticalLineSpacing": QCheckBox("verticalLineSpacing از فونت دوم"),
            "horizontalSpacing": QCheckBox("horizontalSpacing از فونت دوم"),
            "defaultCharacter": QCheckBox("defaultCharacter از فونت دوم")
        }
        for checkbox in self.options.values():
            options_layout.addWidget(checkbox)
        layout.addLayout(options_layout)

        # دکمه ادغام
        merge_btn = QPushButton("اجرای ادغام گروهی")
        merge_btn.clicked.connect(self.run_batch_merge)
        layout.addWidget(merge_btn)

        # کادر متنی برای نمایش لاگ
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        layout.addWidget(QLabel("وضعیت:"))
        layout.addWidget(self.log_text)

    def browse_input_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "انتخاب پوشه ورودی")
        if folder:
            self.input_folder_edit.setText(folder)

    def browse_output_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "انتخاب پوشه خروجی")
        if folder:
            self.output_folder_edit.setText(folder)

    def log(self, message):
        self.log_text.append(message)

    def merge_images(self, image_path1, image_path2, output_path, merge_side='bottom'):
        try:
            img1 = Image.open(image_path1).convert('RGBA')
            img2 = Image.open(image_path2).convert('RGBA')
            width1, height1 = img1.size
            width2, height2 = img2.size

            if merge_side == 'bottom':
                new_width = max(width1, width2)
                new_height = height1 + height2
            else:
                new_width = width1 + width2
                new_height = max(height1, height2)

            new_image = Image.new('RGBA', (new_width, new_height), (0, 0, 0, 0))
            new_image.paste(img1, (0, 0))
            new_image.paste(img2, (0, height1 if merge_side == 'bottom' else 0))

            new_image.save(output_path, quality=100)
            self.log(f"تصویر در {output_path} ذخیره شد. Bit Depth: 32 (RGBA)")
            return new_width, new_height, height1
        except FileNotFoundError:
            self.log(f"خطا: یکی از فایل‌های {image_path1} یا {image_path2} یافت نشد.")
            return None, None, None
        except Exception as e:
            self.log(f"خطا: {e}")
            return None, None, None

    def merge_json_fonts(self, json_path1, json_path2, output_json_path, image_output_name, height1):
        try:
            with open(json_path1, 'r', encoding='utf-8') as f:
                font1 = json.load(f)
            with open(json_path2, 'r', encoding='utf-8') as f:
                font2 = json.load(f)

            merged_font = {
                "header": font2["header"] if self.options["header"].isChecked() else font1["header"],
                "readers": font2["readers"] if self.options["readers"].isChecked() else font1["readers"],
                "content": {
                    "texture": {
                        "format": font2["content"]["texture"]["format"] if self.options["format"].isChecked() else font1["content"]["texture"]["format"],
                        "export": image_output_name
                    },
                    "glyphs": [],
                    "cropping": [],
                    "characterMap": [],
                    "verticalLineSpacing": font2["content"]["verticalLineSpacing"] if self.options["verticalLineSpacing"].isChecked() else font1["content"]["verticalLineSpacing"],
                    "horizontalSpacing": font2["content"]["horizontalSpacing"] if self.options["horizontalSpacing"].isChecked() else font1["content"]["horizontalSpacing"],
                    "kerning": [],
                    "defaultCharacter": font2["content"]["defaultCharacter"] if self.options["defaultCharacter"].isChecked() else font1["content"]["defaultCharacter"]
                }
            }

            merged_font["content"]["glyphs"].extend(font1["content"]["glyphs"])
            for glyph in font2["content"]["glyphs"]:
                merged_font["content"]["glyphs"].append({
                    "x": glyph["x"],
                    "y": glyph["y"] + height1,
                    "width": glyph["width"],
                    "height": glyph["height"]
                })

            merged_font["content"]["cropping"].extend(font1["content"]["cropping"])
            merged_font["content"]["cropping"].extend(font2["content"]["cropping"])

            merged_font["content"]["characterMap"].extend(font1["content"]["characterMap"])
            merged_font["content"]["characterMap"].extend(font2["content"]["characterMap"])

            merged_font["content"]["kerning"].extend(font1["content"]["kerning"])
            merged_font["content"]["kerning"].extend(font2["content"]["kerning"])

            with open(output_json_path, 'w', encoding='utf-8') as f:
                json.dump(merged_font, f, ensure_ascii=False, indent=4)
            self.log(f"فایل JSON در {output_json_path} ذخیره شد.")

        except FileNotFoundError:
            self.log(f"خطا: یکی از فایل‌های {json_path1} یا {json_path2} یافت نشد.")
        except Exception as e:
            self.log(f"خطا: {e}")

    def get_image_path_from_json(self, json_path):
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                font_data = json.load(f)
            image_path = font_data["content"]["texture"]["export"]
            return os.path.join(os.path.dirname(json_path), image_path)
        except FileNotFoundError:
            self.log(f"خطا: فایل JSON {json_path} یافت نشد.")
            return None
        except KeyError:
            self.log(f"خطا: کلید 'content.texture.export' در فایل JSON {json_path} یافت نشد.")
            return None
        except Exception as e:
            self.log(f"خطا: {e}")
            return None

    def run_batch_merge(self):
        input_folder = self.input_folder_edit.text()
        output_folder = self.output_folder_edit.text()

        if not input_folder or not os.path.exists(input_folder):
            self.log("خطا: پوشه ورودی معتبر نیست.")
            return
        if not output_folder:
            self.log("خطا: پوشه خروجی مشخص نشده است.")
            return

        if not os.path.exists(output_folder):
            os.makedirs(output_folder)

        json_files = glob.glob(os.path.join(input_folder, "*.json"))
        pairs = []
        for json_file in json_files:
            if not json_file.endswith("_backup.json"):
                base_name = os.path.basename(json_file).replace(".json", "")
                backup_file = os.path.join(input_folder, f"{base_name}_backup.json")
                if os.path.exists(backup_file):
                    pairs.append((json_file, backup_file))

        if not pairs:
            self.log("خطا: هیچ جفت فایل JSON (name.json و name_backup.json) یافت نشد.")
            return

        for json_path1, json_path2 in pairs:
            try:
                base_name = os.path.basename(json_path1).replace(".json", "")
                output_json = os.path.join(output_folder, f"merged_{base_name}.json")
                output_image = os.path.join(output_folder, f"merged_{base_name}.png")

                image_path1 = self.get_image_path_from_json(json_path1)
                image_path2 = self.get_image_path_from_json(json_path2)

                if image_path1 and image_path2:
                    new_width, new_height, height1 = self.merge_images(image_path1, image_path2, output_image)
                    if new_width is not None:
                        self.merge_json_fonts(json_path1, json_path2, output_json, os.path.basename(output_image), height1)
                else:
                    self.log(f"خطا: نمی‌توان مسیر فایل‌های تصویر را برای {json_path1} یا {json_path2} استخراج کرد.")
            except Exception as e:
                self.log(f"خطا در پردازش جفت {json_path1} و {json_path2}: {e}")

        self.log("پردازش گروهی تکمیل شد.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FontMergerWindow()
    window.show()
    sys.exit(app.exec())