import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import io
import requests
import os
import textwrap
from pillow_heif import register_heif_opener

# iPhone写真(HEIC)対応
register_heif_opener()

# --- 日本語フォントのセットアップ ---
FONT_URL = "https://github.com/googlefonts/noto-cjk/raw/main/Sans/OTF/Japanese/NotoSansCJKjp-Bold.otf"
FONT_PATH = "NotoSansCJKjp-Bold.otf"

@st.cache_data
def download_font():
    if not os.path.exists(FONT_PATH):
        try:
            response = requests.get(FONT_URL)
            with open(FONT_PATH, "wb") as f:
                f.write(response.content)
        except:
            pass

download_font()

# インスタ縦長サイズ (1080 x 1350) 4:5
CANVAS_W = 1080
CANVAS_H = 1350
GRID_SIZE = 1080
CELL_SIZE = GRID_SIZE // 3
HEADER_H = 210  # タイトルエリア
FOOTER_H = 60   # 最下部のフッターエリア
OFFSET_Y = HEADER_H

# --- ヘルパー関数：フォントサイズを自動調整（Excelの縮小表示） ---
def get_fitting_font(text, max_width, initial_size):
    size = initial_size
    while size > 15:
        font = ImageFont.truetype(FONT_PATH, size)
        bbox = ImageDraw.Draw(Image.new('RGB', (1, 1))).textbbox((0, 0), text, font=font)
        if (bbox[2] - bbox[0]) <= max_width:
            return font
        size -= 2
    return ImageFont.truetype(FONT_PATH, size)

# --- ヘルパー関数：日本語対応のテキスト折り返し ---
def wrap_text(text, font, max_width):
    lines = []
    current_line = ""
    for char in text:
        test_line = current_line + char
        bbox = ImageDraw.Draw(Image.new('RGB', (1, 1))).textbbox((0, 0), test_line, font=font)
        if (bbox[2] - bbox[0]) <= max_width:
            current_line = test_line
        else:
            lines.append(current_line)
            current_line = char
    lines.append(current_line)
    return "\n".join(lines[:3]) # 最大3行まで

def center_crop(img):
    img = img.convert("RGB")
    w, h = img.size
    new_size = min(w, h)
    left = (w - new_size) / 2
    top = (h - new_size) / 2
    right = (w + new_size) / 2
    bottom = (h + new_size) / 2
    return img.crop((left, top, right, bottom)).resize((CELL_SIZE, CELL_SIZE), Image.LANCZOS)

st.set_page_config(page_title="私を構成する9本のビール打線メーカー", layout="wide")
st.title("🍺 #私を構成する9本のビール打線 メーカー")

st.write("""
あなたを形作った「思い出の9本」で、最強の布陣を組んでみませんか？
※9枚全部埋まらなくてもOKです！
""")

st.success("**📸 完成したらSNSでシェア！**\n#私を構成する9本のビール打線")

user_id = st.text_input("👤 あなたのInstagram ID (任意)", "@")

order_to_grid_map = {1: 0, 2: 1, 3: 2, 4: 4, 5: 5, 6: 3, 7: 6, 8: 7, 9: 8}
images = {}
labels = {}

st.subheader("⚾️ 打線を組む")

for row in range(3):
    cols = st.columns(3)
    for col in range(3):
        order = row * 3 + col + 1 
        with cols[col]:
            st.markdown(f"### 【{order}番打者】")
            uploaded_file = st.file_uploader(f"画像を選択", type=['jpg', 'jpeg', 'png', 'heic', 'webp'], key=f"up_{order}")
            if uploaded_file:
                try: images[order] = Image.open(uploaded_file)
                except: st.error("エラー")
            labels[order] = st.text_input(f"ブルワリー / ビール名", key=f"txt_{order}", placeholder="例：ヤッホー / よなよなエール")

if st.button("🍺 この打線でインスタ縦長画像を生成する"):
    if not images:
        st.error("最低1枚は画像をアップロードしてください。")
    else:
        with st.spinner('画像を生成中...'):
            canvas = Image.new('RGB', (CANVAS_W, CANVAS_H), (15, 15, 15))
            draw = ImageDraw.Draw(canvas)

            # 1. タイトルセクション
            display_id = user_id if user_id != "@" else "私"
            suffix = " を構成する ビール打線"
            full_title = f"{display_id}{suffix}"
            hashtag_text = "#私を構成する9本のビール打線"

            # タイトルのオートリサイズ（Excelの縮小表示風）
            title_font = get_fitting_font(full_title, CANVAS_W - 100, 70)
            bbox_t = draw.textbbox((0, 0), full_title, font=title_font)
            tw = bbox_t[2] - bbox_t[0]
            draw.text(((CANVAS_W - tw) // 2, 50), full_title, font=title_font, fill=(255, 255, 255))

            # ハッシュタグ
            hash_font = ImageFont.truetype(FONT_PATH, 35)
            bbox_h = draw.textbbox((0, 0), hashtag_text, font=hash_font)
            hw = bbox_h[2] - bbox_h[0]
            draw.text(((CANVAS_W - hw) // 2, 145), hashtag_text, font=hash_font, fill=(180, 180, 180))

            # 2. グリッドセクション
            label_font = ImageFont.truetype(FONT_PATH, 30)
            for order in range(1, 10):
                grid_pos = order_to_grid_map[order]
                r, c = grid_pos // 3, grid_pos % 3
                x, y = c * CELL_SIZE, r * CELL_SIZE + OFFSET_Y
                
                if order in images:
                    canvas.paste(center_crop(images[order]), (x, y))
                    overlay_h = 145 # 文字がはみ出さないよう高さを確保
                    overlay = Image.new('RGBA', (CELL_SIZE, overlay_h), (0, 0, 0, 210))
                    canvas.paste(overlay, (x, y + CELL_SIZE - overlay_h), overlay)
                    
                    # 銘柄の描画（改行と収まりを重視）
                    raw_text = labels[order].replace(" / ", "\n").replace("/", "\n")
                    display_text = f"{order}. {raw_text}"
                    wrapped = wrap_text(display_text, label_font, CELL_SIZE - 30)
                    draw.multiline_text((x + 15, y + CELL_SIZE - overlay_h + 10), wrapped, font=label_font, fill=(255, 255, 255), spacing=6)
                else:
                    draw.rectangle([x, y, x + CELL_SIZE, y + CELL_SIZE], fill=(30, 30, 30), outline=(80, 80, 80), width=2)
                    draw.text((x + CELL_SIZE//3, y + CELL_SIZE//2), f"{order}番", font=label_font, fill=(80, 80, 80))

            # 3. フッターセクション（枠外に配置）
            if user_id != "@":
                footer_text = f"Created by {user_id}"
                footer_font = ImageFont.truetype(FONT_PATH, 30)
                bbox_f = draw.textbbox((0, 0), footer_text, font=footer_font)
                fw = bbox_f[2] - bbox_f[0]
                # グリッドのすぐ下の枠外スペースに配置
                draw.text(((CANVAS_W - fw) // 2, CANVAS_H - 55), footer_text, font=footer_font, fill=(120, 120, 120))

            st.image(canvas, caption="完成！長押しで保存してください")
            buf = io.BytesIO()
            canvas.save(buf, format="PNG")
            st.download_button(label="📥 画像をダウンロード", data=buf.getvalue(), file_name="beer_lineup.png", mime="image/png")

st.write("---")
st.caption("Produced by @world_beer_lab")
