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
            pass # フォントDL失敗時はデフォルトを使用

download_font()

# インスタ縦長サイズ (1080 x 1350) 4:5
CANVAS_W = 1080
CANVAS_H = 1350
GRID_SIZE = 1080
CELL_SIZE = GRID_SIZE // 3
OFFSET_Y = 250  # タイトルエリア用

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

# アプリのタイトル
st.title("🍺 #私を構成する9本のビール打線 メーカー")

# 導入文（「9枚揃わなくてもOK」を追記）
st.write("""
ビールは、人生を語る。
あなたを形作った「思い出の9本」で、最強の布陣を組んでみませんか？

「最近ハマったビール」でも「人生を変えた1杯」でも、あなたが好きなビールなら何でもOKです！

---

**【入力のヒント】**

✅ **9枚全部埋まらなくても大丈夫！**
（1枚からでも画像は作れます。空いた枠は白枠として残るので、まずは今のベストを形にしましょう）

✅ **ブルワリー名や銘柄はわかる範囲でOK！**
（わからない情報は空欄でも大丈夫です。ブルワリー名だけでも立派なリストになります）

✅ **1番（左上）と4番（真ん中）から決めるのがコツ！**

1番：あなたがビール沼に落ちた「きっかけの1本」
4番：あなたの人生で最も影響を与えた「不動のエース」

※画像では自動的に4番が中央に配置されます。
""")

st.success("""
**📸 完成したらSNSでシェアしよう！**

ハッシュタグ： **#私を構成する9本のビール打線**

を付けて投稿してください！
@world_beer_lab をタグ付けしてもらえると全力で見に行きます🍻
""")

st.info("""
📸 **写真がない時は？**

「昔飲んだあの1本の写真がない！」という時は、公式サイトの画像を**引用（スクリーンショット等）**して、あなたの思い出を補完してもOKです。
""")

# インスタID入力
user_id = st.text_input(
    "👤 あなたのInstagram ID (任意)", 
    "@", 
    help="入力すると画像にあなたのIDが入り、あなたのオリジナル作品であることが証明されます。不要な場合は空欄（@のみ）でOKです。"
)

# 4番を中央(インデックス4)に固定するマッピング
order_to_grid_map = {1: 0, 2: 1, 3: 2, 4: 4, 5: 5, 6: 3, 7: 6, 8: 7, 9: 8}

images = {}
labels = {}

st.subheader("⚾️ 打線を組む")
st.write("1番打者から順番に、好きなビールを入力してください（全部埋めなくてもOKです）。")

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
                    st.error("エラー")
            labels[order] = st.text_input(f"ブルワリー / ビール名", key=f"txt_{order}", placeholder="例：ヤッホー / よなよな")

# 画像生成ロジック
if st.button("🍺 この打線でインスタ縦長画像を生成する"):
    if not images:
        st.error("最低1枚は画像をアップロードしてください。")
    else:
        with st.spinner('画像を生成中...'):
            canvas = Image.new('RGB', (CANVAS_W, CANVAS_H), (20, 20, 20))
            draw = ImageDraw.Draw(canvas)

            # 日本語フォント設定
            try:
                title_font = ImageFont.truetype(FONT_PATH, 75)
                id_font = ImageFont.truetype(FONT_PATH, 35)
                label_font = ImageFont.truetype(FONT_PATH, 32)
            except:
                title_font = ImageFont.load_default()
                id_font = ImageFont.load_default()
                label_font = ImageFont.load_default()

            # 1. タイトルの描画（〇〇のベスト9打線）
            display_id = user_id if user_id != "@" else "私"
            title_text = f"{display_id} を構成する\n9本のビール打線"
            
            bbox = draw.textbbox((0, 0), title_text, font=title_font)
            tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
            draw.multiline_text(((CANVAS_W - tw) // 2, 40), title_text, font=title_font, fill=(255, 255, 255), align="center", spacing=15)

            # 2. 各セルの描画
            for order in range(1, 10):
                grid_pos = order_to_grid_map[order]
                r, c = grid_pos // 3, grid_pos % 3
                x, y = c * CELL_SIZE, r * CELL_SIZE + OFFSET_Y
                
                if order in images:
                    # 画像あり
                    img_cropped = center_crop(images[order])
                    canvas.paste(img_cropped, (x, y))
                    
                    overlay = Image.new('RGBA', (CELL_SIZE, 120), (0, 0, 0, 200))
                    canvas.paste(overlay, (x, y + CELL_SIZE - 120), overlay)
                    
                    raw_text = labels[order].replace("/", "\n").replace(" ", "\n")
                    display_text = f"{order}. {raw_text}"
                    draw.multiline_text((x + 15, y + CELL_SIZE - 105), display_text, font=label_font, fill=(255, 255, 255), spacing=5)
                else:
                    # 画像なし：白枠（薄いグレーの枠）を描画
                    draw.rectangle([x, y, x + CELL_SIZE, y + CELL_SIZE], fill=(40, 40, 40), outline=(100, 100, 100), width=2)
                    draw.text((x + CELL_SIZE//3, y + CELL_SIZE//2), f"{order}番", font=label_font, fill=(100, 100, 100))

            # 3. フッター (Instagram ID)
            if user_id and user_id != "@":
                footer_text = f"Created by {user_id}"
                draw.text((CANVAS_W - 400, CANVAS_H - 70), footer_text, font=id_font, fill=(180, 180, 180))

            st.image(canvas, caption="完成！長押しして保存してください")
            
            buf = io.BytesIO()
            canvas.save(buf, format="PNG")
            st.download_button(label="📥 画像をダウンロード", data=buf.getvalue(), file_name="beer_lineup.png", mime="image/png")

st.write("---")
st.caption("Produced by @world_beer_lab")
