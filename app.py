import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import io
import requests
import os
from datetime import datetime
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
        except: pass

download_font()

# インスタ縦長サイズ (1080 x 1350) 4:5
CANVAS_W = 1080
CANVAS_H = 1350
GRID_SIZE = 1080
CELL_SIZE = GRID_SIZE // 3
HEADER_H = 240  # 電光掲示板エリア
OFFSET_Y = HEADER_H

# --- ヘルパー：フォントサイズ自動調整 ---
def get_fitting_font(text, max_width, initial_size):
    size = initial_size
    while size > 20:
        try:
            font = ImageFont.truetype(FONT_PATH, size)
            bbox = ImageDraw.Draw(Image.new('RGB', (1, 1))).textbbox((0, 0), text, font=font)
            if (bbox[2] - bbox[0]) <= max_width: return font
        except: return ImageFont.load_default()
        size -= 2
    return ImageFont.truetype(FONT_PATH, size)

# --- 日本語対応テキスト折り返し ---
def wrap_text(text, font, max_width):
    lines = []
    current_line = ""
    for char in text:
        test_line = current_line + char
        bbox = ImageDraw.Draw(Image.new('RGB', (1, 1))).textbbox((0, 0), test_line, font=font)
        if (bbox[2] - bbox[0]) <= max_width: current_line = test_line
        else:
            lines.append(current_line)
            current_line = char
    lines.append(current_line)
    return "\n".join(lines[:3])

def center_crop(img):
    img = img.convert("RGB")
    w, h = img.size
    new_size = min(w, h)
    left = (w - new_size) / 2
    top = (h - new_size) / 2
    right = (w + new_size) / 2
    bottom = (h + new_size) / 2
    return img.crop((left, top, right, bottom)).resize((CELL_SIZE, CELL_SIZE), Image.LANCZOS)

st.set_page_config(page_title="推しビールで打線を組んでみた", layout="wide")

st.title("⚾️ #推しビールで打線を組んでみた メーカー")

st.write("""
ビールは、人生を語る。
あなたを形作った「思い出の9本」で、最強の布陣を組んでみませんか？

---

**【打線の組み方ガイド】**

✅ **1番（左上）：『原点』**
あなたがビール沼に落ちた「きっかけの1本」

✅ **4番（真ん中）：『エース』**
あなたの人生で最も影響を与えた、不動の4番バッター

✅ **9枚全部埋まらなくてもOK！**
空いた枠はスタジアムのパネルとして表示されます。

📸 **写真がない時は？**
公式サイトの画像を**引用（スクリーンショット等）**して思い出を補完してもOKです。
""")

st.success("**📸 完成したら #推しビールで打線を組んでみた でシェア！**")

team_name = st.text_input("👤 監督名（またはチーム名）", "@", help="画像の中央タイトルになります。")

order_to_grid_map = {1: 0, 2: 1, 3: 2, 4: 4, 5: 5, 6: 3, 7: 6, 8: 7, 9: 8}
images = {}
labels = {}

st.subheader("🏟️ 打順を入力する")

for row in range(3):
    cols = st.columns(3)
    for col in range(3):
        order = row * 3 + col + 1 
        with cols[col]:
            st.markdown(f"### 【{order}番】")
            uploaded_file = st.file_uploader(f"画像", type=['jpg', 'jpeg', 'png', 'heic', 'webp'], key=f"up_{order}")
            if uploaded_file:
                try: images[order] = Image.open(uploaded_file)
                except: st.error("ERR")
            labels[order] = st.text_input(f"ブルワリー / ビール名", key=f"txt_{order}", placeholder="例：ヤッホー / よなよな")

if st.button("🏟️ スコアボードを生成する"):
    if not images and not labels:
        st.error("入力を開始してください。")
    else:
        with st.spinner('プレイボール！...'):
            # 背景：スタジアム・グリーン
            canvas = Image.new('RGB', (CANVAS_W, CANVAS_H), (15, 55, 35)) 
            draw = ImageDraw.Draw(canvas)

            # 1. 電光掲示板（ヘッダー）エリアの背景
            draw.rectangle([40, 30, CANVAS_W - 40, 210], fill=(10, 10, 10), outline=(80, 80, 80), width=3)

            # フォント設定
            try:
                led_color = (255, 180, 0) # 電光掲示板のアンバー色
                id_font = ImageFont.truetype(FONT_PATH, 30)
                hash_font = ImageFont.truetype(FONT_PATH, 38)
                label_font = ImageFont.truetype(FONT_PATH, 30)
                small_font = ImageFont.truetype(FONT_PATH, 24)
            except:
                led_color = (255, 255, 255)
                id_font = hash_font = label_font = small_font = ImageFont.load_default()

            # --- タイトル1：〇〇のビール打線 ---
            display_title = f"{team_name} のビール打線"
            # 縮小表示機能
            title_font = get_fitting_font(display_title, CANVAS_W - 200, 70)
            bbox_t = draw.textbbox((0, 0), display_title, font=title_font)
            tw = bbox_t[2] - bbox_t[0]
            draw.text(((CANVAS_W - tw) // 2, 55), display_title, font=title_font, fill=led_color)

            # --- タイトル2：ハッシュタグ ---
            hashtag_text = "#推しビールで打線を組んでみた"
            bbox_h = draw.textbbox((0, 0), hashtag_text, font=hash_font)
            hw = bbox_h[2] - bbox_h[0]
            draw.text(((CANVAS_W - hw) // 2, 145), hashtag_text, font=hash_font, fill=led_color)

            # 監督・日付情報（情報の整理）
            today = datetime.now().strftime("%Y.%m.%d")
            info_text = f"MANAGER: {team_name}   |   STADIUM: World Beer Lab   |   DATE: {today}"
            bbox_i = draw.textbbox((0, 0), info_text, font=small_font)
            iw = bbox_i[2] - bbox_i[0]
            draw.text(((CANVAS_W - iw) // 2, 220), info_text, font=small_font, fill=(200, 200, 200))

            # 2. グリッドセクション
            for order in range(1, 10):
                grid_pos = order_to_grid_map[order]
                r, c = grid_pos // 3, grid_pos % 3
                x, y = c * CELL_SIZE, r * CELL_SIZE + OFFSET_Y
                
                # 枠線
                draw.rectangle([x, y, x + CELL_SIZE, y + CELL_SIZE], outline=(255, 255, 255, 30), width=1)

                if order in images:
                    canvas.paste(center_crop(images[order]), (x, y))
                    
                    overlay_h = 150 # 高さを確保
                    # 4番（エース）は琥珀色ゴールド、他は黒パネル
                    overlay_color = (160, 110, 20, 230) if order == 4 else (0, 0, 0, 210)
                    overlay = Image.new('RGBA', (CELL_SIZE, overlay_h), overlay_color)
                    canvas.paste(overlay, (x, y + CELL_SIZE - overlay_h), overlay)
                    
                    # ラベルの描画
                    prefix = "【原点】" if order == 1 else "【エース】" if order == 4 else ""
                    raw_text = labels[order].replace(" / ", "\n").replace("/", "\n")
                    # 日本語の途中でも強制改行し、英単語はなるべく維持
                    display_text = f"{order}. {prefix}\n{raw_text}"
                    
                    wrapped = wrap_text(display_text, label_font, CELL_SIZE - 20)
                    draw.multiline_text((x + 15, y + CELL_SIZE - overlay_h + 10), wrapped, font=label_font, fill=(255, 255, 255), spacing=6)
                else:
                    # 空枠
                    draw.rectangle([x + 10, y + 10, x + CELL_SIZE - 10, y + CELL_SIZE - 10], fill=(25, 70, 45))
                    status = "原点" if order == 1 else "エース" if order == 4 else f"{order}番"
                    draw.text((x + 100, y + 150), status, font=label_font, fill=(50, 110, 70))

            # 3. フッター (枠外)
            footer_text = "Produced by World Beer Lab"
            bbox_f = draw.textbbox((0, 0), footer_text, font=small_font)
            fw = bbox_f[2] - bbox_f[0]
            draw.text(((CANVAS_W - fw) // 2, CANVAS_H - 60), footer_text, font=small_font, fill=(255, 255, 255, 100))

            # 表示
            st.image(canvas, caption="長押しして保存してください")
            buf = io.BytesIO()
            canvas.save(buf, format="PNG")
            st.download_button(label="📥 スコアボードを保存", data=buf.getvalue(), file_name="beer_lineup.png", mime="image/png")

st.write("---")
st.caption("© World Beer Lab")
