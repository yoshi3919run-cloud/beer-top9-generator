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

st.set_page_config(page_title="Beer Top 9 Generator", layout="wide")
st.title("🍺 私を構成する9本のビール打線")
st.write("思い出のビール9枚を選んで、最強の布陣を完成させよう！")

# インスタID入力
user_id = st.sidebar.text_input("Instagram ID (例: @world_beer_lab)", "@")

# 打順とグリッド配置の対応表（真ん中に4番を配置）
# グリッド位置: [0, 1, 2, 3, 4, 5, 6, 7, 8]
# 打順番号:     [1, 2, 3, 6, 4, 5, 7, 8, 9]
order_to_grid = {1:0, 2:1, 3:2, 4:4, 5:5, 6:3, 7:6, 8:7, 9:8}
grid_to_order = {v: k for k, v in order_to_grid.items()}

images = {}
labels = {}

# 入力フォーム
st.subheader("⚾️ 打線を組む（画像をアップロード）")
cols = st.columns(3)
for order in range(1, 10):
    grid_pos = order_to_grid[order]
    with st.container():
        # 3カラムに分けて表示
        col_idx = (order - 1) % 3
        with cols[col_idx]:
            st.markdown(f"### 【{order}番打者】")
            uploaded_file = st.file_uploader(f"画像を選択", type=['jpg', 'jpeg', 'png'], key=f"up_{order}")
            if uploaded_file:
                images[grid_pos] = Image.open(uploaded_file)
            labels[grid_pos] = st.text_input(f"ブルワリー / ビール名", key=f"txt_{order}", placeholder="例: El Segundo / Apocalypse")

if st.button("🍺 この打線で画像を生成する"):
    if not images:
        st.error("画像をアップロードしてください。")
    else:
        canvas = Image.new('RGB', (CANVAS_SIZE, CANVAS_SIZE), (255, 255, 255))
        draw = ImageDraw.Draw(canvas)
        
        for i in range(9):
            row, col = i // 3, i % 3
            x, y = col * CELL_SIZE, row * CELL_SIZE
            
            if i in images:
                img = center_crop(images[i])
                canvas.paste(img, (x, y))
                
                # テキスト用の黒帯（半透明）
                overlay = Image.new('RGBA', (CELL_SIZE, 70), (0, 0, 0, 160))
                canvas.paste(overlay, (x, y + CELL_SIZE - 70), overlay)
                
                # 打順番号とテキスト
                text = f"{grid_to_order[i]}. {labels[i]}"
                draw.text((x + 15, y + CELL_SIZE - 50), text, fill=(255, 255, 255))
            else:
                # 未登録枠
                draw.rectangle([x, y, x + CELL_SIZE, y + CELL_SIZE], outline=(220, 220, 220))
                draw.text((x + CELL_SIZE//3, y + CELL_SIZE//2), f"{grid_to_order[i]}番打者", fill=(200, 200, 200))

        # IDの透かし
        if user_id:
            draw.text((CANVAS_SIZE - 200, 20), user_id, fill=(255, 255, 255, 128))

        st.image(canvas, caption="完成イメージ（このままインスタへ！）", use_column_width=True)
        
        # ダウンロード
        buf = io.BytesIO()
        canvas.save(buf, format="PNG")
        st.download_button(label="📥 画像をダウンロード", data=buf.getvalue(), file_name="beer_lineup.png", mime="image/png")
