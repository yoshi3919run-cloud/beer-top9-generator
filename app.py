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
        except:
            pass

download_font()

# インスタ縦長サイズ (1080 x 1350) 4:5
CANVAS_W = 1080
CANVAS_H = 1350
GRID_SIZE = 1080
CELL_SIZE = GRID_SIZE // 3
HEADER_H = 220  # タイトルエリア
OFFSET_Y = HEADER_H

# --- ヘルパー関数：フォントサイズを自動調整（Excelの縮小表示風） ---
def get_fitting_font(text, max_width, initial_size):
    size = initial_size
    while size > 20:
        try:
            font = ImageFont.truetype(FONT_PATH, size)
            bbox = ImageDraw.Draw(Image.new('RGB', (1, 1))).textbbox((0, 0), text, font=font)
            if (bbox[2] - bbox[0]) <= max_width:
                return font
        except:
            return ImageFont.load_default()
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

st.set_page_config(page_title="私を構成する9本のビール打線メーカー", layout="wide")

# アプリUIのデザイン
st.title("⚾️ #私を構成する9本のビール打線 メーカー")

st.write("""
ビールは、人生を語る。
あなたを形作った「思い出の9本」で、最強の布陣を組んでみませんか？

---

**【打線の組み方ガイド】**

✅ **1番（左上）：『原点』**
あなたがビール沼に落ちた「きっかけの1本」を選びましょう。

✅ **4番（真ん中）：『エース』**
あなたの人生で最も影響を与えた「不動の4番バッター」を配置してください。

✅ **9枚全部埋まらなくてもOK！**
1枚からでも作成可能です。空いた枠はスタジアムのパネル風に表示されます。
""")

st.success("""
**📸 完成したらSNSでシェアしよう！**

ハッシュタグ **#私を構成する9本のビール打線** を付けて投稿！
@world_beer_lab をタグ付けしてもらえると、監督（ジミー）が全力で見に行きます🍻
""")

st.info("""
📸 **写真についてのヒント**

「あの頃の1本の写真がない！」という時は、公式サイトの画像を**引用（スクリーンショット等）**して思い出を補完してもOKです。
""")

# 入力項目（チーム名/IDを1つに統合）
team_name = st.text_input(
    "👤 チーム名 または Instagram ID", 
    "@", 
    help="画像の中央タイトルになります。例：『三軒茶屋IPAズ』や自分のIDなど"
)

# 4番を中央(インデックス4)に固定するマッピング
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
            uploaded_file = st.file_uploader(f"画像を選択", type=['jpg', 'jpeg', 'png', 'heic', 'webp'], key=f"up_{order}")
            if uploaded_file:
                try: images[order] = Image.open(uploaded_file)
                except: st.error("エラー")
            labels[order] = st.text_input(f"ブルワリー / ビール名", key=f"txt_{order}", placeholder="例：ヤッホー / よなよな")

# 画像生成
if st.button("🏟️ スコアボードを生成する"):
    if not images and not labels:
        st.error("入力を開始してください。")
    else:
        with st.spinner('スタジアムを設営中...'):
            # 背景：スタジアム・グリーン
            canvas = Image.new('RGB', (CANVAS_W, CANVAS_H), (26, 77, 46)) # 深い緑
            draw = ImageDraw.Draw(canvas)

            # フォント読み込み
            try:
                id_font = ImageFont.truetype(FONT_PATH, 32)
                hash_font = ImageFont.truetype(FONT_PATH, 38)
                label_font = ImageFont.truetype(FONT_PATH, 30)
                num_font = ImageFont.truetype(FONT_PATH, 34)
            except:
                id_font = hash_font = label_font = num_font = ImageFont.load_default()

            # 1. タイトルのオートリサイズ描画
            display_title = f"⚾️ {team_name} のビール打線 🍺"
            title_font = get_fitting_font(display_title, CANVAS_W - 120, 75)
            bbox_t = draw.textbbox((0, 0), display_title, font=title_font)
            tw = bbox_t[2] - bbox_t[0]
            draw.text(((CANVAS_W - tw) // 2, 55), display_title, font=title_font, fill=(255, 255, 255))

            # ハッシュタグ
            hashtag_text = "#私を構成する9本のビール打線"
            bbox_h = draw.textbbox((0, 0), hashtag_text, font=hash_font)
            hw = bbox_h[2] - bbox_h[0]
            draw.text(((CANVAS_W - hw) // 2, 155), hashtag_text, font=hash_font, fill=(200, 200, 200))

            # 2. グリッドセクション
            for order in range(1, 10):
                grid_pos = order_to_grid_map[order]
                r, c = grid_pos // 3, grid_pos % 3
                x, y = c * CELL_SIZE, r * CELL_SIZE + OFFSET_Y
                
                # 枠線（スコアボード風）
                draw.rectangle([x, y, x + CELL_SIZE, y + CELL_SIZE], outline=(255, 255, 255, 30), width=1)

                if order in images:
                    # 画像あり
                    canvas.paste(center_crop(images[order]), (x, y))
                    
                    # ラベルエリア
                    overlay_h = 140
                    # 4番（エース）は琥珀色ゴールド、他は黒
                    overlay_color = (184, 134, 11, 220) if order == 4 else (0, 0, 0, 200)
                    overlay = Image.new('RGBA', (CELL_SIZE, overlay_h), overlay_color)
                    canvas.paste(overlay, (x, y + CELL_SIZE - overlay_h), overlay)
                    
                    # 称号とテキスト
                    prefix = "【原点】" if order == 1 else "【エース】" if order == 4 else ""
                    raw_text = labels[order].replace(" / ", "\n").replace("/", "\n")
                    display_text = f"{order}. {prefix}\n{raw_text}"
                    
                    wrapped = wrap_text(display_text, label_font, CELL_SIZE - 20)
                    draw.multiline_text((x + 15, y + CELL_SIZE - overlay_h + 10), wrapped, font=label_font, fill=(255, 255, 255), spacing=5)
                else:
                    # 画像なし：スコアボードパネル
                    draw.rectangle([x + 10, y + 10, x + CELL_SIZE - 10, y + CELL_SIZE - 10], fill=(35, 90, 55))
                    status_text = "原点" if order == 1 else "エース" if order == 4 else f"{order}番"
                    bbox_s = draw.textbbox((0, 0), status_text, font=num_font)
                    sw = bbox_s[2] - bbox_s[0]
                    draw.text((x + (CELL_SIZE - sw) // 2, y + CELL_SIZE // 2 - 20), status_text, font=num_font, fill=(80, 140, 100))

            # 3. 最下部枠外フッター
            footer_text = "Created by World Beer Lab"
            bbox_f = draw.textbbox((0, 0), footer_text, font=id_font)
            fw = bbox_f[2] - bbox_f[0]
            draw.text(((CANVAS_W - fw) // 2, CANVAS_H - 65), footer_text, font=id_font, fill=(255, 255, 255, 100))

            # 表示とダウンロード
            st.image(canvas, caption="長押しして保存してください")
            buf = io.BytesIO()
            canvas.save(buf, format="PNG")
            st.download_button(label="📥 スコアボードをダウンロード", data=buf.getvalue(), file_name="beer_scoreboard.png", mime="image/png")

st.write("---")
st.caption("Produced by @world_beer_lab")
