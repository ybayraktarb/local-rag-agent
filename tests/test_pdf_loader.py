import os
import pytest
from langchain_core.documents import Document
from src.loaders.base_loader import BaseLoader
from src.loaders.pdf_loader import PDFLoader
from src.loaders.loader_factory import LoaderFactory

# ReportLab imports for generating the mock PDF
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

MOCK_PDF_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../docs/sample/mock_sample.pdf"))

def generate_test_pdf(filename: str):
    """
    Generates a 2-page mock PDF containing Turkish text and a data table.
    """
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    
    # Register Arial font to support Turkish characters properly in PDF
    font_path = "/System/Library/Fonts/Supplemental/Arial.ttf"
    if os.path.exists(font_path):
        pdfmetrics.registerFont(TTFont('Arial', font_path))
        font_name = 'Arial'
    else:
        font_name = 'Helvetica' # Fallback, though Arial exists on macOS

    doc = SimpleDocTemplate(filename, pagesize=letter)
    styles = getSampleStyleSheet()
    
    # Configure styles to use Arial
    title_style = styles['Title']
    title_style.fontName = font_name
    
    normal_style = styles['Normal']
    normal_style.fontName = font_name
    
    heading_style = styles['Heading1']
    heading_style.fontName = font_name
    
    story = []
    
    # Page 1: Heading, Paragraph in Turkish, and a Table
    story.append(Paragraph("Müşteri Kredi Başvuru Rehberi", title_style))
    story.append(Spacer(1, 12))
    story.append(Paragraph(
        "Bu doküman, banka personelinin müşteri kredi başvurularını değerlendirirken "
        "izlemesi gereken adımları ve kuralları içerir. İstisnai durumlarda yetkili "
        "onayı gerekmektedir.", normal_style
    ))
    story.append(Spacer(1, 12))
    
    # A standard table
    table_data = [
        ["Kredi Türü", "Limit (TL)", "Faiz Oranı"],
        ["İhtiyaç Kredisi", "100.000", "%2.5"],
        ["Konut Kredisi", "2.000.000", "%1.8"],
        ["Taşıt Kredisi", "500.000", "%2.1"]
    ]
    t = Table(table_data)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.grey),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('BOTTOMPADDING', (0,0), (-1,0), 6),
        ('GRID', (0,0), (-1,-1), 1, colors.black),
        ('FONTNAME', (0,0), (-1,-1), font_name),
        ('FONTSIZE', (0,0), (-1,-1), 10),
    ]))
    story.append(t)
    story.append(Spacer(1, 20))
    story.append(Paragraph("Kılavuzun birinci sayfasının sonu.", normal_style))
    
    # Page Break
    story.append(PageBreak())
    
    # Page 2: Text only (to test multiple pages and metadata)
    story.append(Paragraph("İkinci Sayfa Başlığı", heading_style))
    story.append(Spacer(1, 12))
    story.append(Paragraph(
        "Bu ikinci sayfadır ve burada farklı kurallar tanımlanmıştır. "
        "Örneğin, kampanya tanımlama işlemleri bu sayfada açıklanmıştır. Türkçe karakterler: ş, ç, ğ, ı, ö, ü.",
        normal_style
    ))
    
    doc.build(story)

@pytest.fixture(scope="module", autouse=True)
def setup_mock_pdf():
    """
    Fixture to create mock PDF before tests run and clean it up afterwards.
    """
    generate_test_pdf(MOCK_PDF_PATH)
    yield
    if os.path.exists(MOCK_PDF_PATH):
        try:
            os.remove(MOCK_PDF_PATH)
        except OSError:
            pass

def test_base_loader_contract():
    """
    Test that PDFLoader inherits from BaseLoader.
    """
    loader = PDFLoader(MOCK_PDF_PATH)
    assert isinstance(loader, BaseLoader)

def test_pdf_loader_text_and_pages():
    """
    Test page count, text correctness, and metadata of the extracted documents.
    """
    loader = PDFLoader(MOCK_PDF_PATH)
    docs = loader.load()
    
    assert len(docs) == 2
    
    # Test Page 1 Metadata
    assert docs[0].metadata["source"] == "mock_sample.pdf"
    assert docs[0].metadata["page"] == 1
    
    # Test Page 1 Content
    assert "Müşteri Kredi Başvuru Rehberi" in docs[0].page_content
    assert "İhtiyaç Kredisi" in docs[0].page_content
    
    # Test Page 2 Metadata
    assert docs[1].metadata["source"] == "mock_sample.pdf"
    assert docs[1].metadata["page"] == 2
    
    # Test Page 2 Content and Turkish characters
    assert "İkinci Sayfa Başlığı" in docs[1].page_content
    assert "ş, ç, ğ, ı, ö, ü" in docs[1].page_content

def test_pdf_loader_table_structure():
    """
    Test that table structure is converted to Markdown correctly and row/column relationships are kept.
    """
    loader = PDFLoader(MOCK_PDF_PATH)
    docs = loader.load()
    
    page1_content = docs[0].page_content
    
    # Assert Markdown table syntax is present
    assert "| Kredi Türü | Limit (TL) | Faiz Oranı |" in page1_content
    assert "| --- | --- | --- |" in page1_content
    assert "| İhtiyaç Kredisi | 100.000 | %2.5 |" in page1_content
    assert "| Konut Kredisi | 2.000.000 | %1.8 |" in page1_content
    assert "| Taşıt Kredisi | 500.000 | %2.1 |" in page1_content

def test_loader_factory():
    """
    Test LoaderFactory returns PDFLoader for PDF files and raises ValueError for unsupported types.
    """
    loader = LoaderFactory.get_loader("test.pdf")
    assert isinstance(loader, PDFLoader)
    assert loader.file_path == "test.pdf"
    
    with pytest.raises(ValueError) as excinfo:
        LoaderFactory.get_loader("test.docx")
    assert "Desteklenmeyen dosya uzantısı" in str(excinfo.value)
