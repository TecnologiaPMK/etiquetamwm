import segno
import tempfile
import os
import streamlit as st
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import mm
from PIL import Image, ImageDraw, ImageFont
import datetime

def is_streamlit_cloud():
    return os.environ.get("STREAMLIT_SERVER_RUNNING") is not None

def create_label_image(data_fabricacao, part_number, nivel_liberacao, serial_fabricacao, nf, logo_path, dpi=300):
    label_width, label_height = 110, 85  # mm
    width_pixels, height_pixels = (int(label_width * dpi / 25.4), int(label_height * dpi / 25.4))
    
    img = Image.new('RGB', (width_pixels, height_pixels), color='white')
    draw = ImageDraw.Draw(img)
    font = ImageFont.load_default()
    
    try:
        logo = Image.open(logo_path)
        logo = logo.resize((500, 120))
        img.paste(logo, (10, 10))
    except:
        pass
    
    y_pos = 150
    info_texts = [
        f"Data de Fabricação: {data_fabricacao.strftime('%d/%m/%Y')}",
        f"Part Number MWM: {part_number}",
        f"Nível de Liberação: {nivel_liberacao}",
        f"Serial de Fabricação: {serial_fabricacao}",
        f"Número da NF: {nf}",
    ]
    
    for text in info_texts:
        draw.text((20, y_pos), text, fill="black", font=font)
        y_pos += 30
    
    dm_data = f"{data_fabricacao.strftime('%d/%m/%Y')};{part_number};{nivel_liberacao};{serial_fabricacao};{nf}"
    qrcode = segno.make(dm_data)
    qr_path = tempfile.NamedTemporaryFile(suffix=".png", delete=False).name
    qrcode.save(qr_path, scale=10)
    
    dm_img = Image.open(qr_path)
    dm_img = dm_img.resize((200, 200))
    img.paste(dm_img, (20, y_pos))
    
    return img

def save_as_pdf(img, quantity):
    pdf_path = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False).name
    c = canvas.Canvas(pdf_path, pagesize=(150*mm, 100*mm))
    img_path = tempfile.NamedTemporaryFile(suffix=".png", delete=False).name
    img.save(img_path, format="PNG")
    
    for _ in range(quantity):
        c.drawImage(img_path, 0, 0, width=110*mm, height=85*mm)
        c.showPage()
    
    c.save()
    os.remove(img_path)
    return pdf_path

dados_mwm = {
    "7000448C93": {"nivel": "A", "serial": "13785"},
    "7000666C93": {"nivel": "A", "serial": "13785"},
    "961201150166": {"nivel": "A", "serial": "13785"},
    "7000449C3": {"nivel": "A", "serial": "13785"},
}

st.title("Etiquetas MWM")
data_fabricacao = st.date_input("Data de Fabricação", datetime.date.today())
part_number = st.selectbox("Part Number MWM:", list(dados_mwm.keys()))

nivel_liberacao = st.text_input("Nível de Liberação:", value=dados_mwm[part_number]["nivel"])
serial_fabricacao = st.text_input("Serial de Fabricação:", value=dados_mwm[part_number]["serial"])
nf = st.text_input("Número da Nota Fiscal (NF):")
quantidade = st.number_input("Quantidade de Etiquetas:", min_value=1, value=1, step=1)

logo_path = "logoPMK.png"

if st.button("Visualizar Prévia"):
    img_preview = create_label_image(data_fabricacao, part_number, nivel_liberacao, serial_fabricacao, nf, logo_path)
    st.image(img_preview, caption="Prévia da Etiqueta", width=500)

if st.button("Salvar como PDF"):
    img_pdf = create_label_image(data_fabricacao, part_number, nivel_liberacao, serial_fabricacao, nf, logo_path)
    pdf_path = save_as_pdf(img_pdf, quantidade)
    with open(pdf_path, "rb") as f:
        st.download_button(label="Baixar PDF", data=f, file_name="etiqueta.pdf", mime="application/pdf")
