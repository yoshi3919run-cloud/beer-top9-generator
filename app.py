import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import io
import requests
import os
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

# --- ボタンとUIのカスタマイズCSS ---
st.markdown("""
<style>
    /* チームを作るボタン（ゴールド） */
    div.stButton > button:first-child {
        background-color: #ffbf00 !important;
        color: #000000 !important;
        font-weight: bold !important;
        border: 2px solid #ffffff !important;
        border-radius: 10px !important;
        padding: 10px 24px !important;
        width: 100% !important;
    }
    /* 保存ボタン（スタジアムグリーン） */
    div.stDownloadButton > button {
        background-color: #1a4d2e !important;
        color: #ffffff !important;
        font-weight: bold !important;
        border: 2px solid #ffffff !important;
        border-radius: 10px !important;
        padding: 10px 24px !important;
        width: 100% !important;
    }
</style>
""", unsafe_allow_html=True)

# インスタ縦長サイズ (1080 x 1350)
CANVAS_W = 1080
CANVAS_H = 1350
GRID_SIZE = 1080
CELL_SIZE = GRID_SIZE // 3
IMG_PADDING = 15 
IMG_SIZE = CELL_SIZE - (IMG_PADDING * 2)
OFFSET_Y = 210  

# フォントサイズ自動調整
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

# テキスト折り返し
def wrap_text_tight(text, font, max_width, max_lines=3):
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
    return "\n".join(lines[:max_lines])

def center_crop(img):
    img = img.convert("RGB")
    w, h = img.size
    new_size = min(w, h)
    left, top = (w - new_size) / 2, (h - new_size) / 2
    right, bottom = (w + new_size) / 2, (h + new_size) / 2
    return img.crop((left, top, right, bottom)).resize((IMG_SIZE, IMG_SIZE), Image.LANCZOS)

st.set_page_config(page_title="#推しビールで打線を組んでみた", layout="wide")
st.title("⚾️ #推しビールで打線を組んでみた メーカー")

# --- 統一された説明文 ---
st.write("""
ビールは、人生を語る。
あなたを形作った、忘れられない9本で最強の布陣を組んでみませんか？

---

**【打線の組み方ガイド】**

✅ **1番（左上）：『原点』**
あなたがビール沼に落ちた「きっかけの1本」を選びましょう。

✅ **4番（真ん中）：『エース』**
あなたの人生で最も影響を与えた「不動のエース」を配置してください。

✅ **9枚全部埋まらなくてもOK！**
1枚からでも作成可能です。空いた枠はスタジアム風のパネルとして表示されます。

📸 **写真についてのヒント**
「あの1本の写真がない！」という時は、公式サイトの画像を**引用（スクリーンショット等）**して思い出を補完してもOKです。
なお、写真がなくても文字だけの打線を作ることも可能です。
""")

# --- ご指定のSNS共有案内（2行に分けて改行） ---
st.success("""
📸 **完成したらSNSでシェアしよう！**

#推しビールで打線を組んでみた を付けて投稿！

**@world_beer_lab** をタグ付けしてシェアしてくれたら、監督（ジミー）が全力でコメントしに伺います🍻
""")

team_name = st.text_input("👤 監督名（またはチーム名）を入力", "@")

order_to_grid_map = {1: 0, 2: 1, 3: 2, 4: 4, 5: 5, 6: 3, 7: 6, 8: 7, 9: 8}
images, labels = {}, {}

st.subheader("🏟️ 打順を入力する")
st.write("「ブルワリー / ビール名」のようにスラッシュを入れると境目がわかりやすくなります。")

for row in range(3):
    cols = st.columns(3)
    for col in range(3):
        order = row * 3 + col + 1 
        with cols[col]:
            st.markdown(f"### 【{order}番】")
            uploaded_file = st.file_uploader(f"画像を選択", type=['jpg', 'jpeg', 'png', 'heic', 'webp'], key=f"up_{order}")
            if uploaded_file:
                try: images[order] = Image.open(uploaded_file)
                except: st.error("ERR")
            labels[order] = st.text_input(f"ブルワリー / ビール名", key=f"txt_{order}", placeholder="例：ヤッホー / よなよな")

if st.button("⚾️ チームを作る（スコアボード生成）"):
    if not images and not any(labels.values()):
        st.error("入力が必要です")
    else:
        with st.spinner('スタジアムを設営中...'):
            canvas = Image.new('RGB', (CANVAS_W, CANVAS_H), (15, 60, 35)) 
            draw = ImageDraw.Draw(canvas)
            draw.rectangle([50, 40, CANVAS_W - 50, 190], fill=(5, 10, 5), outline=(100, 100, 100), width=2)
            led_yellow = (255, 191, 0) 

            try:
                title_font = get_fitting_font(f"{team_name} のビール打線", CANVAS_W - 200, 70)
                hash_font = ImageFont.truetype(FONT_PATH, 34)
                label_font = ImageFont.truetype(FONT_PATH, 28)
                footer_font = ImageFont.truetype(FONT_PATH, 30)
                panel_font = ImageFont.truetype(FONT_PATH, 36)
            except: title_font = hash_font = label_font = footer_font = panel_font = ImageFont.load_default()

            draw.text(((CANVAS_W - draw.textbbox((0,0), f"{team_name} のビール打線", font=title_font)[2])//2, 55), f"{team_name} のビール打線", font=title_font, fill=led_yellow)
            draw.text(((CANVAS_W - draw.textbbox((0,0), "#推しビールで打線を組んでみた", font=hash_font)[2])//2, 135), "#推しビールで打線を組んでみた", font=hash_font, fill=led_yellow)

            for order in range(1, 10):
                grid_pos = order_to_grid_map[order]
                r, c = grid_pos // 3, grid_pos % 3
                x, y = c * CELL_SIZE, r * CELL_SIZE + OFFSET_Y
                draw.rectangle([x, y, x + CELL_SIZE, y + CELL_SIZE], outline=(255, 255, 255, 15), width=1)

                prefix = "【原点】" if order == 1 else "【エース】" if order == 4 else ""
                
                if order in images:
                    # 画像あり
                    canvas.paste(center_crop(images[order]), (x + IMG_PADDING, y + IMG_PADDING))
                    overlay_h = 135 
                    overlay_color = (184, 134, 11, 230) if order == 4 else (0, 0, 0, 210)
                    overlay = Image.new('RGBA', (IMG_SIZE, overlay_h), overlay_color)
                    canvas.paste(overlay, (x + IMG_PADDING, y + IMG_PADDING + IMG_SIZE - overlay_h), overlay)
                    display_text = f"{order}. {prefix} {labels[order]}"
                    wrapped = wrap_text_tight(display_text, label_font, IMG_SIZE - 20)
                    draw.multiline_text((x + IMG_PADDING + 10, y + IMG_PADDING + IMG_SIZE - overlay_h + 10), wrapped, font=label_font, fill=(255, 255, 255), spacing=4)
                elif labels[order]:
                    # 文字のみパネル
                    panel_color = (184, 134, 11, 255) if order == 4 else (20, 50, 30, 255)
                    draw.rectangle([x + IMG_PADDING, y + IMG_PADDING, x + CELL_SIZE - IMG_PADDING, y + CELL_SIZE - IMG_PADDING], fill=panel_color, outline=(255,255,255,30))
                    display_text = f"{order}. {prefix}\n{labels[order]}"
                    wrapped = wrap_text_tight(display_text, panel_font, IMG_SIZE - 40, max_lines=5)
                    draw.multiline_text((x + CELL_SIZE//2, y + CELL_SIZE//2), wrapped, font=panel_font, fill=(255, 255, 255), anchor="mm", align="center", spacing=8)
                else:
                    # 空枠
                    draw.rectangle([x + 15, y + 15, x + CELL_SIZE - 15, y + CELL_SIZE - 15], fill=(30, 80, 50))
                    status = "原点" if order == 1 else "エース" if order == 4 else f"{order}番"
                    draw.text((x + 115, y + 155), status, font=label_font, fill=(60, 120, 80))

            draw.text(((CANVAS_W - draw.textbbox((0,0), "Produced by World Beer Lab", font=footer_font)[2])//2, CANVAS_H - 55), "Produced by World Beer Lab", font=footer_font, fill=(255, 255, 255, 100))

            st.image(canvas, caption="長押しして保存してください")
            
            buf = io.BytesIO()
            canvas.save(buf, format="PNG")
            st.download_button(label="📥 チームを保存（スコアボード保存）", data=buf.getvalue(), file_name="beer_lineup.png", mime="image/png")

st.write("---")
st.caption("© World Beer Lab")
