import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import io

# インスタ用の正方形サイズ (1080x1080)
CANVAS_SIZE = 1080
CELL_SIZE = CANVAS_SIZE // 3

def center_crop(img):
    w, h = img.size
    new_size = min(w, h)
    left = (w - new_size) / 2
    top = (h - new_size) / 2
    right = (w + new_size) / 2
    bottom = (h + new_size) / 2
    return img.crop((left, top, right, bottom)).resize((CELL_SIZE, CELL_SIZE))

st.set_page_config(page_title="私を構成する9本のビール打線メーカー", layout="wide")

# アプリのタイトルと導入文
st.title("🍺 #私を構成する9本のビール打線 メーカー")
st.write("""
ビールは、人生を語る。
あなたを形作った、忘れられない9本で最強の布陣を組んでみませんか？

**【打線の組み方ガイド】**
⚾️ **1番（左上）：** あなたがビール沼に落ちた「きっかけの1本」
⚾️ **4番（真ん中）：** あなたの人生で最も影響を与えた「不動のエース」
※その他の打順は、あなたの自由な感性で選んでください！

📸 **写真についてのヒント**
「あの頃の1本の写真がない！」という時は、公式サイトの画像を**引用（スクリーンショット等）**して、あなたの思い出を補完してもOKです。
""")

# サイドパネル設定
st.sidebar.header("⚙️ 設定")
user_id = st.sidebar.text_input("Instagram ID (任意)", "@")
st.sidebar.write("---")
st.sidebar.write("完成したら #私を構成する9本のビール打線 をつけてシェア！")

# グリッドの見た目通りの打順配置
# [1番, 2番, 3番]
# [6番, 4番, 5番]  <- 真ん中に4番(主砲)を配置
# [7番, 8番, 9番]
grid_layout = [
    [1, 2, 3],
    [6, 4, 5],
    [7, 8, 9]
]

images = {}
labels = {}

st.subheader("⚾️ 打線を組む")
st.info("スマホの方は、上から順番に入力していけば自然な打順になります。")

# 入力フォームの生成
for r_idx, row_orders in enumerate(grid_layout):
    cols = st.columns(3)
    for c_idx, order in enumerate(row_orders):
        grid_pos = (r_idx * 3) + c_idx
        with cols[c_idx]:
            st.markdown(f"### 【{order}番打者】")
            uploaded_file = st.file_uploader(f"画像を選択", type=['jpg', 'jpeg', 'png'], key=f"up_{order}")
            if uploaded_file:
                images[grid_pos] = Image.open(uploaded_file)
            labels[grid_pos] = st.text_input(f"ブルワリー / ビール名", key=f"txt_{order}", placeholder="例: El Segundo")

# 画像生成ロジック
if st.button("🍺 この打線で画像を生成する"):
    if not images:
        st.error("画像を1枚以上アップロードしてください。")
    else:
        # キャンバス作成
        canvas = Image.new('RGB', (CANVAS_SIZE, CANVAS_SIZE), (255, 255, 255))
        draw = ImageDraw.Draw(canvas)
        
        for i in range(9):
            row, col = i // 3, i % 3
            x, y = col * CELL_SIZE, row * CELL_SIZE
            
            # 打順番号を取得
            order_num = grid_layout[row][col]

            if i in images:
                # 画像加工
                img = center_crop(images[i])
                canvas.paste(img, (x, y))
                
                # テキスト用の黒帯（半透明）
                overlay = Image.new('RGBA', (CELL_SIZE, 80), (0, 0, 0, 180))
                canvas.paste(overlay, (x, y + CELL_SIZE - 80), overlay)
                
                # テキスト描画
                text = f"{order_num}. {labels[i]}"
                draw.text((x + 15, y + CELL_SIZE - 60), text, fill=(255, 255, 255))
            else:
                # 空枠の描画
                draw.rectangle([x, y, x + CELL_SIZE, y + CELL_SIZE], outline=(220, 220, 220))
                draw.text((x + CELL_SIZE//3, y + CELL_SIZE//2), f"{order_num}番打者", fill=(200, 200, 200))

        # インスタIDの透かし
        if user_id and user_id != "@":
            draw.text((CANVAS_SIZE - 250, 30), user_id, fill=(255, 255, 255, 150))

        # 完成画像の表示
        st.image(canvas, caption="完成イメージ（長押しで保存、または下のボタンから保存）", use_column_width=True)
        
        # ダウンロードボタン
        buf = io.BytesIO()
        canvas.save(buf, format="PNG")
        st.download_button(label="📥 画像をダウンロード", data=buf.getvalue(), file_name="beer_lineup.png", mime="image/png")

# 免責事項（フッター）
st.write("---")
st.caption("""
※本サービスは個人のエンターテインメント目的のものです。アップロードする画像の著作権等は、各権利者に帰属します。引用の範囲内で、利用者自身の責任においてご利用ください。
Produced by @world_beer_lab
""")
