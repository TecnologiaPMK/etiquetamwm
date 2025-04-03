import streamlit as st
import datetime
import tempfile
import os
from PIL import Image, ImageDraw, ImageFont
import treepoem
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import mm
import sys

def is_streamlit_cloud():
    return os.environ.get("STREAMLIT_SERVER_RUNNING") is not None

def get_printers():
    if is_streamlit_cloud():
        st.warning("Impressão direta não é suportada no Streamlit Cloud. Utilize a opção de download do PDF.")
        return None
    try:
        import cups
        conn = cups.Connection()
        printers = conn.getPrinters()
        return list(printers.keys()) if printers else None
    except Exception as e:
        st.error(f"Erro ao obter impressoras: {str(e)}")
        return None

def select_printer():
    printers = get_printers()
    if not printers:
        st.info("Nenhuma impressora disponível ou impressão direta não suportada neste ambiente.")
        return None
    return st.selectbox("Selecione a Impressora:", printers)

def load_font(font_name, size):
    try:
        return ImageFont.truetype(font_name, size)
    except IOError:
        return ImageFont.load_default()

def create_label_image(data_fabricacao, part_number, nivel_liberacao, serial_fabricacao, nf, logo_path, dpi=300, logo_position=(10, 10), text_offset=-30):
    label_width, label_height = 110, 85  # mm
    width_pixels, height_pixels = (int(label_width * dpi / 25.4), int(label_height * dpi / 25.4))
    
    img = Image.new('RGB', (width_pixels, height_pixels), color='white')
    draw = ImageDraw.Draw(img)
    
    font_title = load_font("arialbd.ttf", 45)
    font_data = load_font("calibri.ttf", 40)
    font_code = load_font("arialbd.ttf", 50)
    
    logo = Image.open(logo_path)
    logo = logo.resize((500, 120))
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

    # Gera o DataMatrix utilizando treepoem
    dm_data = f"{data_fabricacao.strftime('%d/%m/%Y')};{part_number};{nivel_liberacao};{serial_fabricacao};13785;{nf}"
    dm_img = treepoem.generate_barcode(barcode_type="datamatrix", data=dm_data)
    dm_img = dm_img.convert("RGB")
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

def print_pdf(pdf_path, printer_name):
    try:
        import cups
        conn = cups.Connection()
        conn.printFile(printer_name, pdf_path, "Etiqueta", {})
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
PR_datamatrix = st.text_input("Cod DataMatrix", value=dados_mwm[part_number]["datamatrix"])

nf = st.text_input("Número da Nota Fiscal (NF):")
quantidade = st.number_input("Quantidade de Etiquetas:", min_value=1, value=1, step=1)

# Certifique-se de que o arquivo "logoPMK.png" esteja no repositório
logo_path = "logoPMK.png"

if st.button("Visualizar Prévia"):
    img_preview = create_label_image(data_fabricacao, part_number, nivel_liberacao, serial_fabricacao, nf, logo_path)
    st.image(img_preview, caption="Prévia da Etiqueta", width=500)

if st.button("Salvar como PDF"):
    img_pdf = create_label_image(data_fabricacao, part_number, nivel_liberacao, serial_fabricacao, nf, logo_path)
    pdf_path = save_as_pdf(img_pdf, quantidade)
    with open(pdf_path, "rb") as f:
        st.download_button(label="Baixar PDF", data=f, file_name="etiqueta.pdf", mime="application/pdf")

if st.button("Imprimir Etiqueta") and printer_name:
    st.info("Impressão direta não está disponível neste ambiente. Por favor, utilize a opção de download do PDF para imprimir localmente.")
