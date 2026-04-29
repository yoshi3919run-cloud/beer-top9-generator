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

# アプリのタイトル
st.title("🍺 #私を構成する9本のビール打線 メーカー")

# 導入文とガイド（ご指摘の改行を反映）
st.write("""
ビールは人生を語る。
あなたを形作った「思い出の9本」で、自分だけの最強のビールチームをつくってみませんか？

「最近ハマったビール」でも「人生を変えた1杯」でも、あなたが好きなビールなら何でもOKです！

---

**【入力のヒント】**

✅ **ブルワリー名や銘柄はわかる範囲でOK！**
（わからない情報は空欄でも大丈夫です。ブルワリー名だけでも立派なリストになります）

✅ **1番（左上）と4番（真ん中）から決めるのがコツ！**

1番：あなたがビール沼に落ちた「きっかけの1本」

4番：あなたが一番好きな「エースで4番」

※画像では自動的に4番が中央に配置されます。
""")

# ハッシュタグとシェアの案内（ここも改行を強化）
st.success("""
**📸 完成したらSNSでシェアしよう！**

ハッシュタグ： **#私を構成する9本のビール打線**

を付けて投稿してください！
@worldbeer_labo をタグ付けしてもらえると全力で見に行きます🍻
""")

# 写真についての補足（ここも改行を強化）
st.info("""
📸 **写真がない時は？**

「昔飲んだあの1本の写真がない！」という時は、公式サイトの画像やラベルの**スクリーンショット（引用）**を使って思い出を補完してもOKです。
""")

# インスタID入力
user_id = st.text_input(
    "👤 あなたのInstagram ID (任意)", 
    "@", 
    help="入力すると画像にあなたのIDが入り、あなたのオリジナル作品であることが証明されます。不要な場合は空欄（@のみ）でOKです。"
)

# 4番を中央(インデックス4)に固定するマッピング
order_to_grid_map = {
    1: 0, 2: 1, 3: 2,
    4: 4, 5: 5, 6: 3, 
    7: 6, 8: 7, 9: 8
}

images = {}
labels = {}

st.subheader("⚾️ 打線を組む")
st.write("1番打者から順番に、あなたの好きなビールを教えてください。")

# 入力フォームの生成
for row in range(3):
    cols = st.columns(3)
    for col in range(3):
        order = row * 3 + col + 1 
        with cols[col]:
            st.markdown(f"### 【{order}番打者】")
            uploaded_file = st.file_uploader(f"画像を選択", type=['jpg', 'jpeg', 'png'], key=f"up_{order}")
            if uploaded_file:
                images[order] = Image.open(uploaded_file)
            labels[order] = st.text_input(f"ビール名 / ブルワリー名", 
                                         key=f"txt_{order}", 
                                         placeholder="例：よなよなエール / ヤッホーブルーイング")

# 画像生成ロジック
if st.button("🍺 この打線で画像を生成する"):
    if not images:
        st.error("まずは画像を1枚以上アップロードしてください。")
    else:
        canvas = Image.new('RGB', (CANVAS_SIZE, CANVAS_SIZE), (255, 255, 255))
        draw = ImageDraw.Draw(canvas)
        
        for order in range(1, 10):
            grid_pos = order_to_grid_map[order]
            r, c = grid_pos // 3, grid_pos % 3
            x, y = c * CELL_SIZE, r * CELL_SIZE
            
            if order in images:
                img = center_crop(images[order])
                canvas.paste(img, (x, y))
                
                overlay = Image.new('RGBA', (CELL_SIZE, 80), (0, 0, 0, 180))
                canvas.paste(overlay, (x, y + CELL_SIZE - 80), overlay)
                
                display_text = f"{order}. {labels[order]}" if labels[order] else f"{order}."
                draw.text((x + 15, y + CELL_SIZE - 60), display_text, fill=(255, 255, 255))
            else:
                draw.rectangle([x, y, x + CELL_SIZE, y + CELL_SIZE], outline=(220, 220, 220))
                draw.text((x + CELL_SIZE//3, y + CELL_SIZE//2), f"{order}番打者", fill=(200, 200, 200))

        if user_id and user_id != "@":
            draw.text((CANVAS_SIZE - 250, 30), user_id, fill=(255, 255, 255, 150))

        st.image(canvas, caption="完成イメージ（長押しで保存、または下のボタンから保存）", use_column_width=True)
        
        buf = io.BytesIO()
        canvas.save(buf, format="PNG")
        st.download_button(label="📥 画像をダウンロード", data=buf.getvalue(), file_name="beer_lineup.png", mime="image/png")

st.write("---")
st.caption("""
※本サービスは個人のエンターテインメント目的のものです。アップロードする画像の著作権等は、各権利者に帰属します。引用の範囲内で、利用者自身の責任においてご利用ください。
Produced by @worldbeer_labo
""")
