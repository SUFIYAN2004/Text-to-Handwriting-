import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import io
import requests

st.set_page_config(page_title="Perfect Handwriting Generator", layout="centered")
st.title("🖋️ Handwriting Generator (Full-Width Simulation)")

uploaded_font = st.sidebar.file_uploader("Upload a .ttf font (optional)", type=["ttf"])
github_font_url = st.sidebar.text_input("Or paste a GitHub raw font URL:", help="Link to a .ttf font on GitHub")

text = st.text_area("Enter your text", height=300)
font_size = st.slider("Font Size", 20, 100, 38)
color = st.color_picker("Pick pen color", "#000000")

diagram_files = st.file_uploader("Upload diagrams (PNG/JPG)", type=["png", "jpg", "jpeg"], accept_multiple_files=True)
diagram_map_text = st.text_area("Map diagrams using: filename.png:5,10", height=120)

# Load font
def get_font(font_size):
    try:
        if uploaded_font:
            return ImageFont.truetype(uploaded_font, font_size)
        elif github_font_url:
            r = requests.get(github_font_url)
            return ImageFont.truetype(io.BytesIO(r.content), font_size)
        else:
            return ImageFont.truetype("DejaVuSans.ttf", font_size)
    except:
        return ImageFont.load_default()

font = get_font(font_size)

# Parse diagram insert map
def parse_diagram_map(text, uploaded_files):
    file_map = {}
    file_dict = {f.name: f for f in uploaded_files}
    for line in text.strip().splitlines():
        if ":" in line:
            fname, lines = line.split(":")
            fname = fname.strip()
            if fname in file_dict:
                nums = [int(x.strip()) for x in lines.split(",") if x.strip().isdigit()]
                for num in nums:
                    file_map.setdefault(num, []).append(file_dict[fname])
    return file_map

# Measure text size using bbox
def get_text_size(draw, text, font):
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]

# Wrap text to max line width
def wrap_text_to_full_width(draw, text, font, max_width, margin=80):
    words = text.split()
    lines = []
    line = ""
    while words:
        test_line = line + words[0] + " "
        width, _ = get_text_size(draw, test_line, font)
        if width + margin * 2 <= max_width:
            line = test_line
            words.pop(0)
        else:
            lines.append(line.rstrip())
            line = ""
    if line:
        lines.append(line.rstrip())
    return lines

# Generate output
if st.button("Generate PDF"):
    if not text.strip():
        st.warning("Please enter some text.")
        st.stop()

    img_width, img_height = 1240, 1754
    margin = 80
    y_start = 100
    line_spacing = int(font_size * 0.2)

    draw_temp = ImageDraw.Draw(Image.new("RGB", (img_width, img_height)))
    lines = wrap_text_to_full_width(draw_temp, text, font, img_width, margin)
    diagram_map = parse_diagram_map(diagram_map_text, diagram_files)

    pages = []
    img = Image.new("RGB", (img_width, img_height), "white")
    draw = ImageDraw.Draw(img)
    y = y_start
    cur_line = 0

    for line in lines:
        cur_line += 1

        # Insert diagram(s)
        if cur_line in diagram_map:
            for diag_file in diagram_map[cur_line]:
                diag_img = Image.open(diag_file).convert("RGBA")
                max_diag_width = img_width - 2 * margin
                if diag_img.width > max_diag_width:
                    ratio = max_diag_width / diag_img.width
                    diag_img = diag_img.resize((int(diag_img.width * ratio), int(diag_img.height * ratio)))
                if y + diag_img.height > img_height - margin:
                    pages.append(img)
                    img = Image.new("RGB", (img_width, img_height), "white")
                    draw = ImageDraw.Draw(img)
                    y = y_start
                img.paste(diag_img, (margin, y), diag_img)
                y += diag_img.height + line_spacing

        # Draw line
        width, height = get_text_size(draw, line, font)
        if y + height > img_height - margin:
            pages.append(img)
            img = Image.new("RGB", (img_width, img_height), "white")
            draw = ImageDraw.Draw(img)
            y = y_start

        draw.text((margin, y), line, font=font, fill=color)
        y += height + line_spacing

    pages.append(img)

    # Preview
    preview_buf = io.BytesIO()
    pages[0].save(preview_buf, format="PNG")
    preview_buf.seek(0)
    st.image(preview_buf, caption="Preview Page", use_container_width=True)

    # PDF
    pdf_buf = io.BytesIO()
    pages[0].save(pdf_buf, format="PDF", save_all=True, append_images=pages[1:])
    pdf_buf.seek(0)
    st.success(f"Generated {len(pages)} page(s).")
    st.download_button("📥 Download PDF", data=pdf_buf, file_name="handwritten.pdf", mime="application/pdf")
