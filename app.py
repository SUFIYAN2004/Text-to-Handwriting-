import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import io

st.title("🖋️ Handwriting Generator")

text = st.text_area("Enter the text")
uploaded_font = st.file_uploader("Upload a .ttf font", type=["ttf"])
font_size = st.slider("font Size", 20, 100, 40)
color = st.color_picker("pick pen color", "#000000")

if st.button("Generate Image"):
    if not text.strip():
        st.warning("Please enter some text. ")
    else:
        img = Image.new('RGB', (1240, 1754), color="White") 
        draw = ImageDraw.Draw(img) 

        try:
            if uploaded_font is not None:
                font = ImageFont.truetype(uploaded_font, font_size)
            else:
                font = ImageFont.truetype("arial.ttf", font_size) 
        except Exception as e:
            st.error("Font load Failed: {e}")
            st.stop()
        draw.text((100, 100), text, fill=color, font=font)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)

        st.image(img, caption="your handwritten text", use_container_width=True)
        st.download_button("Download Image", data=buf, file_name="handwritten_text.png", mime="image/png")