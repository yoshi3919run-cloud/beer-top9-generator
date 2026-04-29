import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import io
from pillow_heif import register_heif_opener

register_heif_opener()

# インスタ用の正方形サイズ (1080x1080)
CANVAS_SIZE = 1080
CELL_SIZE = CANVAS_SIZE // 3

def center_crop(img):
    # 画像をRGBモードに強制変換（これで白飛びを防ぎます）
    img = img.convert("RGB")
    w, h = img.size
    new_size = min(w, h)
    left = (w - new_size) / 2
    top = (h - new_size) / 2
    right = (w + new_size) / 2
    bottom = (h + new_size) / 2
    # 綺麗に中央で切り抜いてセルサイズにリサイズ
    return img.crop((left, top, right, bottom)).resize((CELL_SIZE, CELL_SIZE), Image.LANCZOS)

st.set_page_config(page_title="私を構成する9本のビール打線メーカー", layout="wide")

st.title("🍺 #私を構成する9本のビール打線 メーカー")

st.write("""
あなたを形作った「思い出の9本」で、最強の布陣を組もう！
※画像では自動的に4番が中央に配置されます。
""")

st.success("**📸 完成したらSNSでシェアしよう！**\n#私を構成する9本のビール打線")

user_id = st.text_input("👤 Instagram ID (任意)", "@")

# 配置マッピング（4番を中央に固定）
# 1 2 3
# 6 4 5
# 7 8 9
order_to_grid_map = {
    1: 0, 2: 1, 3: 2,
    4: 4, 5: 5, 6: 3, 
    7: 6, 8: 7, 9: 8
}

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
                    img = Image.open(uploaded_file)
                    images[order] = img
                    st.write("✅ 読み込み完了")
                except:
                    st.error("読み込めません。スクショでお試しください。")
            labels[order] = st.text_input(f"銘柄名", key=f"txt_{order}", placeholder="例：よなよなエール")

if st.button("🍺 この打線で画像を生成する"):
    if not images:
        st.error("画像をアップロードしてください。")
    else:
        # 1. 土台の作成
        canvas = Image.new('RGB', (CANVAS_SIZE, CANVAS_SIZE), (255, 255, 255))
        draw = ImageDraw.Draw(canvas)
        
        # 2. 各セルの描画
        for order in range(1, 10):
            grid_pos = order_to_grid_map[order]
            r, c = grid_pos // 3, grid_pos % 3
            x, y = c * CELL_SIZE, r * CELL_SIZE
            
            if order in images:
                # 切り抜き加工して貼り付け
                img_cropped = center_crop(images[order])
                canvas.paste(img_cropped, (x, y))
                
                # テキストエリアの背景（黒の半透明）
                overlay = Image.new('RGBA', (CELL_SIZE, 100), (0, 0, 0, 180))
                canvas.paste(overlay, (x, y + CELL_SIZE - 100), overlay)
                
                # テキスト描画（フォントがない場合を考慮して数字を大きく、名前を添える）
                label_text = f"{order}. {labels[order]}" if labels[order] else f"{order}."
                # 簡易的な文字描画（フォントなしでも見えるように白で描画）
                draw.text((x + 20, y + CELL_SIZE - 70), label_text, fill=(255, 255, 255))
            else:
                # 空枠
                draw.rectangle([x, y, x + CELL_SIZE, y + CELL_SIZE], outline=(200, 200, 200), width=3)
                draw.text((x + CELL_SIZE//3, y + CELL_SIZE//2), f"{order}nd", fill=(150, 150, 150))

        # 3. IDの透かし
        if user_id and user_id != "@":
            draw.text((CANVAS_SIZE - 300, 40), user_id, fill=(255, 255, 255, 180))

        # 4. 表示
        st.image(canvas, caption="完成！長押しして保存してね")
        
        # 5. ダウンロード
        buf = io.BytesIO()
        canvas.save(buf, format="PNG")
        st.download_button(label="📥 画像をダウンロード", data=buf.getvalue(), file_name="beer_top9.png", mime="image/png")

st.write("---")
st.caption("Produced by @world_beer_lab")
