import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import io
from pillow_heif import register_heif_opener

# iPhone写真(HEIC)対応
register_heif_opener()

# インスタ縦長サイズ (1080 x 1350) 4:5
CANVAS_W = 1080
CANVAS_H = 1350
GRID_SIZE = 1080
CELL_SIZE = GRID_SIZE // 3
OFFSET_Y = 180  # 上部のタイトルと余白用

def center_crop(img):
    # RGBモードに強制変換（白飛び・透過エラー防止）
    img = img.convert("RGB")
    w, h = img.size
    new_size = min(w, h)
    left = (w - new_size) / 2
    top = (h - new_size) / 2
    right = (w + new_size) / 2
    bottom = (h + new_size) / 2
    # 中央で正方形に切り抜いてリサイズ
    return img.crop((left, top, right, bottom)).resize((CELL_SIZE, CELL_SIZE), Image.LANCZOS)

st.set_page_config(page_title="私を構成する9本のビール打線メーカー", layout="wide")

# アプリのタイトル
st.title("🍺 #私を構成する9本のビール打線 メーカー")

# 導入文とガイド
st.write("""
ビールは、人生を語る。
あなたを形作った「思い出の9本」で、最強の布陣を組んでみませんか？

「最近ハマったビール」でも「人生を変えた1杯」でも、あなたが好きなビールなら何でもOKです！

---

**【入力のヒント】**

✅ **ブルワリー名や銘柄はわかる範囲でOK！**
（わからない情報は空欄でも大丈夫です。ブルワリー名だけでも立派なリストになります）

✅ **1番（左上）と4番（真ん中）から決めるのがコツ！**

1番：あなたがビール沼に落ちた「きっかけの1本」
4番：あなたの人生で最も影響を与えた「不動のエース」

※画像では自動的に4番が中央に配置されます。
""")

# ハッシュタグとシェアの案内
st.success("""
**📸 完成したらSNSでシェアしよう！**

ハッシュタグ： **#私を構成する9本のビール打線**

を付けて投稿してください！
@world_beer_lab をタグ付けしてもらえると全力で見に行きます🍻
""")

# 写真についての補足
st.info("""
📸 **写真がない時は？**

「昔飲んだあの1本の写真がない！」という時は、公式サイトの画像を**引用（スクリーンショット等）**して、あなたの思い出を補完してもOKです。
""")

# インスタID入力：理由を添えて離脱を防ぐ
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

# 入力フォームの生成 (1から9まで順番に表示)
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
                    st.error("読み込みエラー。スクショでお試しください。")
            labels[order] = st.text_input(f"ブルワリー / ビール名", 
                                         key=f"txt_{order}", 
                                         placeholder="例：ヤッホーブルーイング よなよなエール")

# 画像生成ロジック
if st.button("🍺 この打線でインスタ縦長画像を生成する"):
    if not images:
        st.error("まずは画像を1枚以上アップロードしてください。")
    else:
        with st.spinner('画像を生成中...'):
            # 背景（シックなダークグレー）
            canvas = Image.new('RGB', (CANVAS_W, CANVAS_H), (30, 30, 30))
            draw = ImageDraw.Draw(canvas)

            # タイトルの描画（textsizeエラー回避版）
            title_text = "#私を構成する9本のビール打線"
            try:
                # Pillow 10+ の新方式でテキストサイズ取得
                bbox = draw.textbbox((0, 0), title_text)
                tw = bbox[2] - bbox[0]
                draw.text(((CANVAS_W - tw) // 2, 60), title_text, fill=(255, 255, 255))
            except:
                draw.text((100, 60), title_text, fill=(255, 255, 255))

            # 各セルの描画
            for order in range(1, 10):
                grid_pos = order_to_grid_map[order]
                r, c = grid_pos // 3, grid_pos % 3
                x, y = c * CELL_SIZE, r * CELL_SIZE + OFFSET_Y
                
                if order in images:
                    # 画像加工
                    img_cropped = center_crop(images[order])
                    canvas.paste(img_cropped, (x, y))
                    
                    # テキスト用の黒帯（半透明）
                    overlay = Image.new('RGBA', (CELL_SIZE, 90), (0, 0, 0, 180))
                    canvas.paste(overlay, (x, y + CELL_SIZE - 90), overlay)
                    
                    # テキスト描画
                    display_text = f"{order}. {labels[order]}" if labels[order] else f"{order}."
                    draw.text((x + 20, y + CELL_SIZE - 65), display_text, fill=(255, 255, 255))
                else:
                    # 空枠
                    draw.rectangle([x, y, x + CELL_SIZE, y + CELL_SIZE], outline=(80, 80, 80), width=2)
                    draw.text((x + CELL_SIZE//3, y + CELL_SIZE//2), f"{order}番打者", fill=(100, 100, 100))

            # フッター (ID)
            if user_id and user_id != "@":
                draw.text((CANVAS_W - 300, CANVAS_H - 100), user_id, fill=(150, 150, 150))

            # 完成画像の表示
            st.image(canvas, caption="完成イメージ（長押しで保存、または下のボタンからダウンロード）", use_column_width=True)
            
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
