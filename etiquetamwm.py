import streamlit as st
import datetime
import win32print
import tempfile
import os
import win32api
from PIL import Image, ImageDraw, ImageFont
from pylibdmtx.pylibdmtx import encode
from reportlab.pdfgen import canvas # type: ignore
from reportlab.lib.pagesizes import mm # type: ignore
import sys

def get_printers():
    try:
        printers = [printer[2] for printer in win32print.EnumPrinters(
            win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS
        )]
        return printers if printers else None
    except Exception as e:
        st.error(f"Erro ao obter impressoras: {str(e)}")
        return None

def select_printer():
    printers = get_printers()
    if not printers:
        st.warning("Nenhuma impressora encontrada.")
        return None
    return st.selectbox("Selecione a Impressora:", printers)

def load_font(font_name, size):
    try:
        return ImageFont.truetype(font_name, size)
    except IOError:
        return ImageFont.load_default()

def create_label_image(data_fabricacao, part_number, nivel_liberacao, serial_fabricacao, nf, logo_path, dpi=300, logo_position=(10, 10), text_offset=-50, PR_datamatrix=""):
    label_width, label_height = 110, 85 # mm (largura x altura na vertical)
    width_pixels, height_pixels = (int(label_width * dpi / 25.4), int(label_height * dpi / 25.4))

    img = Image.new('RGB', (width_pixels, height_pixels), color='white')
    draw = ImageDraw.Draw(img)
    
    font_title = load_font("arialbd.ttf", 45)
    font_data = load_font("calibri.ttf", 40)
    font_code = load_font("arialbd.ttf", 50)
    
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
        y_pos += 45
        draw.text((650, y_pos), value, fill="black", font=font_data)
        y_pos += 65
    
    dm_data = f"{data_fabricacao.strftime('%d/%m/%Y')};{part_number};{nivel_liberacao};{serial_fabricacao};13785;{nf}"
    datamatrix = encode(dm_data.encode('utf-8'))
    dm_img = Image.frombytes('RGB', (datamatrix.width, datamatrix.height), datamatrix.pixels)
    dm_img = dm_img.resize((600, 400))

    dm_x, dm_y = 5, 200
    img.paste(dm_img, (dm_x, dm_y))

    pr020_x = dm_x + dm_img.width // 2
    pr020_y = dm_y + dm_img.height + 20
    draw.text((pr020_x, pr020_y), PR_datamatrix, fill="black", font=font_code, anchor="mm")

    img = img.rotate(90, expand=True)

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

def print_pdf(pdf_path):
    try:
        win32api.ShellExecute(0, "print", pdf_path, None, ".", 0)
        st.success("Etiqueta(s) enviada(s) para impressão!")
    except Exception as e:
        st.error(f"Erro ao imprimir: {str(e)}")

dados_mwm = {
    "7000448C93": {"nivel": "A", "serial": "13785", "datamatrix":"PR019"},
    "7000666C93": {"nivel": "A", "serial": "13785", "datamatrix":"PR018"},
    "961201150166": {"nivel": "A", "serial": "13785", "datamatrix":"PR020"},
    "7000449C3": {"nivel": "A", "serial": "13785", "datamatrix":"PR023"},
}

st.title("Etiquetas MWM")
printer_name = select_printer()
data_fabricacao = st.date_input("Data de Fabricação", datetime.date.today())
part_number = st.selectbox("Part Number MWM:", list(dados_mwm.keys()))

nivel_liberacao = st.text_input("Nível de Liberação:", value=dados_mwm[part_number]["nivel"])
serial_fabricacao = st.text_input("Serial de Fabricação:", value=dados_mwm[part_number]["serial"])
PR_datamatrix = st.text_input("cod datamatrix", value=dados_mwm[part_number]["datamatrix"])

nf = st.text_input("Número da Nota Fiscal (NF):")
quantidade = st.number_input("Quantidade de Etiquetas:", min_value=1, value=1, step=1)

logo_path = os.path.join(sys._MEIPASS, "logoPMK.png") if getattr(sys, 'frozen', False) else "logoPMK.png"

if st.button("Visualizar Prévia"):
    img_preview = create_label_image(data_fabricacao, part_number, nivel_liberacao, serial_fabricacao, nf, logo_path, PR_datamatrix=PR_datamatrix)
    st.image(img_preview, caption="Prévia da Etiqueta", width=500)
