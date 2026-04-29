import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import io
import os
import urllib.request
import textwrap
from pillow_heif import register_heif_opener

register_heif_opener()

# --- 日本語フォントのセットアップ ---
FONT_URL = "https://github.com/googlefonts/noto-cjk/raw/main/Sans/OTF/Japanese/NotoSansCJKjp-Bold.otf"
FONT_PATH = "NotoSansCJKjp-Bold.otf"

@st.cache_resource
def load_font():
    if not os.path.exists(FONT_PATH):
        urllib.request.urlretrieve(FONT_URL, FONT_PATH)
    return FONT_PATH

# --- サイズ定義 (インスタ縦長 4:5 ルール) ---
CANVAS_W = 1080
CANVAS_H = 1350 # 1080 / 4 * 5
HEADER_H = 270  # タイトルエリアの高さ
GRID_W = CANVAS_W
GRID_H = CANVAS_W # グリッド自体は正方形
CELL_SIZE = GRID_W // 3

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
あなたを形作った、忘れられない9本で最強の布陣を組んでみませんか？
「最近ハマったビール」でも「人生を変えた1杯」でも、あなたが好きなビールなら何でもOKです！

---

**【打線の組み方ガイド】**

⚾️ **1番（左上）：** あなたがビール沼に落ちた「きっかけの1本」
⚾️ **4番（真ん中）：** あなたの人生で最も影響を与えた「不動のエース」

※画像では自動的に4番が中央に配置されます。
※出力画像はInstagramフィード投稿（縦長）に最適なサイズになります。
""")

st.success("""
**📸 完成したらSNSでシェアしよう！**
ハッシュタグ： **#私を構成する9本のビール打線** を付けて投稿してください！
@world_beer_lab をタグ付けしてもらえると全力で見に行きます🍻
""")

# インスタID入力（タイトルに使います）
user_id = st.text_input("👤 あなたのInstagram ID (任意)", "@")

# 配置マッピング
order_to_grid_map = {1:0, 2:1, 3:2, 4:4, 5:5, 6:3, 7:6, 8:7, 9:8}
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
                try:
                    images[order] = Image.open(uploaded_file)
                    st.write("✅ 読み込み完了")
                except:
                    st.error("読み込めません")
            labels[order] = st.text_input(f"銘柄名", key=f"txt_{order}", placeholder="例：ヤッホー よなよなエール")

if st.button("🍺 この打線でインスタ縦長画像を生成する"):
    if not images:
        st.error("画像をアップロードしてください。")
    else:
        with st.spinner('最強の布陣を画像化中...'):
            font_file = load_font()
            
            # --- フォントサイズ設定 ---
            title_font = ImageFont.truetype(font_file, 55)    # メインタイトル（デカく）
            id_title_font = ImageFont.truetype(font_file, 40) # ID入りサブタイトル
            cell_font = ImageFont.truetype(font_file, 30)     # セル内の銘柄名
            watermark_font = ImageFont.truetype(font_file, 25) # 下部のID透かし

            # 縦長キャンバスの作成 (背景は白)
            canvas = Image.new('RGB', (CANVAS_W, CANVAS_H), (255, 255, 255))
            draw = ImageDraw.Draw(canvas)
            
            # --- 1. ヘッダーエリア（タイトル）の描画 ---
            
            # メインタイトル
            main_title_text = "俺を構成する9本のビールで打線を組んでみた"
            # 中央揃えにするための計算
            w, h = draw.textsize(main_title_text, font=title_font)
            draw.text(((CANVAS_W - w) / 2, 70), main_title_text, font=title_font, fill=(0, 0, 0)) # 黒文字

            # サブタイトル（ID入り）
            if user_id and user_id != "@":
                # "@world_beer_lab チームの最強布陣" のような文章
                sub_title_text = f"{user_id} チームの最強布陣"
            else:
                sub_title_text = "最強のベストナイン打線"
            
            w_sub, h_sub = draw.textsize(sub_title_text, font=id_title_font)
            # メインタイトルの下に配置
            draw.text(((CANVAS_W - w_sub) / 2, 160), sub_title_text, font=id_title_font, fill=(50, 50, 50)) # 少しグレー
            
            # --- 2. グリッドエリアの描画（ヘッダーの下に配置） ---
            
            for order in range(1, 10):
                grid_pos = order_to_grid_map[order]
                r, c = grid_pos // 3, grid_pos % 3
                # Y座標はヘッダーの高さを足す
                x, y = c * CELL_SIZE, (r * CELL_SIZE) + HEADER_H
                
                if order in images:
                    img_cropped = center_crop(images[order])
                    canvas.paste(img_cropped, (x, y))
                    
                    # 黒帯
                    overlay_h = 130
                    overlay = Image.new('RGBA', (CELL_SIZE, overlay_h), (0, 0, 0, 180))
                    canvas.paste(overlay, (x, y + CELL_SIZE - overlay_h), overlay)
                    
                    # テキストの折り返し
                    label_text = f"{order}. {labels[order]}" if labels[order] else f"{order}."
                    wrapped_text = textwrap.fill(label_text, width=12)
                    
                    # 描画
                    draw.multiline_text((x + 20, y + CELL_SIZE - 110), wrapped_text, font=cell_font, fill=(255, 255, 255), spacing=8)
                else:
                    # 空枠
                    draw.rectangle([x, y, x + CELL_SIZE, y + CELL_SIZE], outline=(220, 220, 220), width=3)
                    draw.text((x + CELL_SIZE//3, y + CELL_SIZE//2), f"{order}nd", font=cell_font, fill=(180, 180, 180))

            # --- 3. IDの透かし（右下に移動） ---
            if user_id and user_id != "@":
                draw.text((CANVAS_W - 250, CANVAS_H - 50), user_id, font=watermark_font, fill=(200, 200, 200, 150)) # 薄いグレー

            st.image(canvas, caption="完成！長押しして保存してね（インスタ縦長サイズ）")
            
            buf = io.BytesIO()
            canvas.save(buf, format="PNG")
            st.download_button(label="📥 画像をダウンロード", data=buf.getvalue(), file_name="beer_lineup_portrait.png", mime="image/png")

st.write("---")
st.caption("Produced by @world_beer_lab")
