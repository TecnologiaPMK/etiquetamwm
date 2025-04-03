import streamlit as st
import datetime
import tempfile
import os
import webbrowser
from PIL import Image, ImageDraw, ImageFont
from reportlab.pdfgen import canvas # type: ignore
from reportlab.lib.pagesizes import mm # type: ignore
import segno
import sys

def carregar_fonte(font_name, size):
    try:
        return ImageFont.truetype(font_name, size)
    except IOError:
        return ImageFont.load_default()

def gerar_datamatrix(data):
    qr = segno.make(data, micro=False)
    temp_file = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    qr.save(temp_file.name, scale=10)
    img = Image.open(temp_file.name)
    return img

def criar_imagem_etiqueta(data_fabricacao, part_number, nivel_liberacao, serial_fabricacao, nf, logo_path, dpi=300, logo_position=(10, 10), text_offset=-50, PR_datamatrix=""):
    label_width, label_height = 110, 85 # mm (largura x altura na vertical)
    width_pixels, height_pixels = (int(label_width * dpi / 25.4), int(label_height * dpi / 25.4))

    img = Image.new('RGB', (width_pixels, height_pixels), color='white')
    draw = ImageDraw.Draw(img)
    
    font_title = carregar_fonte("arialbd.ttf", 60)
    font_data = carregar_fonte("calibri.ttf", 55)
    font_code = carregar_fonte("arialbd.ttf", 65)
    
    logo = Image.open(logo_path)
    logo = logo.resize((500, 150))
    img.paste(logo, logo_position)
    y_pos = logo_position[1] + logo.size[1] + text_offset
    
    info_texts = [
        ("Data de Fabricação:", data_fabricacao.strftime('%d/%m/%Y')),
        ("Part Number MWM:", part_number),
        ("Nível de Liberação:", nivel_liberacao),
        ("Serial de Fabricação:", serial_fabricacao),
        ("Identificação do Fornecedor:", "13785"),
        ("Número da NF:", nf),
    ]
    
    for title, value in info_texts:
        draw.text((650, y_pos), title, fill="black", font=font_title)
        y_pos += 55
        draw.text((650, y_pos), value, fill="black", font=font_data)
        y_pos += 75
    
    dm_data = f"{data_fabricacao.strftime('%d/%m/%Y')};{part_number};{nivel_liberacao};{serial_fabricacao};13785;{nf}"
    dm_img = gerar_datamatrix(dm_data)
    dm_img = dm_img.resize((600, 400))

    dm_x, dm_y = 5, 200
    img.paste(dm_img, (dm_x, dm_y))

    pr020_x = dm_x + dm_img.width // 2
    pr020_y = dm_y + dm_img.height + 20
    draw.text((pr020_x, pr020_y), PR_datamatrix, fill="black", font=font_code, anchor="mm")

    img = img.rotate(90, expand=True)

    return img

def salvar_como_pdf(img, quantity):
    pdf_path = os.path.join(tempfile.gettempdir(), "etiqueta_mwm.pdf")
    c = canvas.Canvas(pdf_path, pagesize=(150*mm, 100*mm))
    
    img_path = os.path.join(tempfile.gettempdir(), "etiqueta_mwm.png")
    img.save(img_path, format="PNG")
    
    for _ in range(quantity):
        c.drawImage(img_path, 0, 0, width=110*mm, height=85*mm)
        c.showPage()
    
    c.save()
    return pdf_path

dados_mwm = {
    "7000448C93": {"nivel": "A", "serial": "13785", "datamatrix":"PR019"},
    "7000666C93": {"nivel": "A", "serial": "13785", "datamatrix":"PR018"},
    "961201150166": {"nivel": "A", "serial": "13785", "datamatrix":"PR020"},
    "7000449C3": {"nivel": "A", "serial": "13785", "datamatrix":"PR023"},
}

st.title("Etiquetas MWM")
data_fabricacao = st.date_input("Data de Fabricação", datetime.date.today())
part_number = st.selectbox("Part Number MWM:", list(dados_mwm.keys()))

nivel_liberacao = st.text_input("Nível de Liberação:", value=dados_mwm[part_number]["nivel"])
serial_fabricacao = st.text_input("Serial de Fabricação:", value=dados_mwm[part_number]["serial"])
PR_datamatrix = st.text_input("cod datamatrix", value=dados_mwm[part_number]["datamatrix"])

nf = st.text_input("Número da Nota Fiscal (NF):")
quantidade = st.number_input("Quantidade de Etiquetas:", min_value=1, value=1, step=1)

logo_path = os.path.join(sys._MEIPASS, "logoPMK.png") if getattr(sys, 'frozen', False) else "logoPMK.png"

if st.button("Visualizar Prévia"):
    img_preview = criar_imagem_etiqueta(data_fabricacao, part_number, nivel_liberacao, serial_fabricacao, nf, logo_path, PR_datamatrix=PR_datamatrix)
    st.image(img_preview, caption="Prévia da Etiqueta", width=500)

if st.button("Imprimir PDF"):
    img_pdf = criar_imagem_etiqueta(data_fabricacao, part_number, nivel_liberacao, serial_fabricacao, nf, logo_path, PR_datamatrix=PR_datamatrix)
    pdf_path = salvar_como_pdf(img_pdf, quantidade)
    st.markdown(f'<a href="{pdf_path}" target="_blank">Clique aqui para visualizar/imprimir o PDF</a>', unsafe_allow_html=True)
