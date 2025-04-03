import streamlit as st
import datetime
import tempfile
import os
import sys
from PIL import Image, ImageDraw, ImageFont
from reportlab.pdfgen import canvas # type: ignore
from reportlab.lib.pagesizes import mm # type: ignore
import segno

# Função para carregar a fonte
def load_font(font_name, size):
    try:
        return ImageFont.truetype(font_name, size)
    except IOError:
        return ImageFont.load_default()

# Função para gerar o código DataMatrix
def generate_datamatrix(data):
    qr = segno.make(data, micro=False)
    temp_file = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    qr.save(temp_file.name, scale=20)
    img = Image.open(temp_file.name)
    return img.rotate(0, expand=True)  # Garante que a rotação esteja correta


# Função para criar a imagem da etiqueta
def create_label_image(data_fabricacao, part_number, nivel_liberacao, serial_fabricacao, nf, logo_path, 
                       dpi=100, PR_datamatrix=""):
    label_width, label_height = 110, 85  # Dimensão da etiqueta em mm
    width_pixels, height_pixels = (int(label_width * dpi / 25.4), int(label_height * dpi / 25.4))
    img = Image.new('RGB', (width_pixels, height_pixels), color='white')
    draw = ImageDraw.Draw(img)

    # Carrega fontes
    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    font_title = ImageFont.truetype(font_path, 12)
    font_data = ImageFont.truetype(font_path, 12)
    font_code = ImageFont.truetype(font_path, 12)
                           
    # Adiciona o logo
    logo = Image.open(logo_path)
    logo = logo.resize((150, 50))
    img.paste(logo, (10, 10))
    y_pos = 80

    # Informações na etiqueta
    info_texts = [
        ("Data de Fabricacao ", data_fabricacao.strftime('%d/%m/%Y')),
        ("Part Number MWM ", part_number),
        ("Nivel de Liberacao ", nivel_liberacao),
        ("Serial de Fabricacao ", serial_fabricacao),
        ("Identificacao do Fornecedor ", "13785"),
        ("Numero da NF ", nf),
    ]

    for title, value in info_texts:
        draw.text((230, y_pos), title, fill="black", font=font_title)
        y_pos += 20  # Aumentei para evitar sobreposição
        draw.text((230, y_pos), value, fill="black", font=font_data)
        y_pos += 20

    # Gera o DataMatrix
    dm_data = f"{data_fabricacao.strftime('%d%m%Y')};{part_number};{nivel_liberacao};{serial_fabricacao};13785;{nf}"
    dm_img = generate_datamatrix(dm_data)
    dm_img = dm_img.resize((230, 230))
    img.paste(dm_img, (-2, 60))

    # Código PR
    draw.text((105, 280), PR_datamatrix, fill="black", font=font_code, anchor="mm")
    return img


# Mantive o restante do código igual


# Função para salvar a etiqueta como PDF
def save_as_pdf(img, quantity):
    pdf_path = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False).name
    c = canvas.Canvas(pdf_path, pagesize=(110*mm, 85*mm))
    img_path = tempfile.NamedTemporaryFile(suffix=".png", delete=False).name
    img.save(img_path, format="PNG")
    for _ in range(quantity):
        c.drawImage(img_path, 0, 0, width=110*mm, height=85*mm)
        c.showPage()
    c.save()
    os.remove(img_path)
    return pdf_path

# Dados dos Part Numbers
dados_mwm = {
    "7000448C93": {"nivel": "A", "serial": "13785", "datamatrix":"PR019"},
    "7000666C93": {"nivel": "A", "serial": "13785", "datamatrix":"PR018"},
    "961201150166": {"nivel": "A", "serial": "13785", "datamatrix":"PR020"},
    "7000449C3": {"nivel": "A", "serial": "13785", "datamatrix":"PR023"},
}

# Interface Streamlit
st.title("Etiquetas MWM")
data_fabricacao = st.date_input("Data de Fabricacao", datetime.date.today())
part_number = st.selectbox("Part Number MWM:", list(dados_mwm.keys()))
nivel_liberacao = st.text_input("Nível de Liberacao:", value=dados_mwm[part_number]["nivel"])
serial_fabricacao = st.text_input("Serial de Fabricacao:", value=dados_mwm[part_number]["serial"])
PR_datamatrix = st.text_input("Cod Datamatrix", value=dados_mwm[part_number]["datamatrix"])
nf = st.text_input("Número da Nota Fiscal (NF):")
quantidade = st.number_input("Quantidade de Etiquetas:", min_value=1, value=1, step=1)

logo_path = os.path.join(sys._MEIPASS, "logoPMK.png") if getattr(sys, 'frozen', False) else "logoPMK.png"

if st.button("Visualizar Prévia"):
    img_preview = create_label_image(data_fabricacao, part_number, nivel_liberacao, serial_fabricacao, nf, logo_path, PR_datamatrix=PR_datamatrix)
    st.image(img_preview, caption="Prévia da Etiqueta", width=500)

if st.button("Imprimir PDF"):
    img_pdf = create_label_image(data_fabricacao, part_number, nivel_liberacao, serial_fabricacao, nf, logo_path, PR_datamatrix=PR_datamatrix)
    pdf_path = save_as_pdf(img_pdf, quantidade)
    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()
    st.download_button(
        label="Baixar PDF",
        data=pdf_bytes,
        file_name="etiqueta.pdf",
        mime="application/pdf")
