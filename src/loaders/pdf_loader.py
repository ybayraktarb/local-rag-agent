import os
from typing import List
import pdfplumber
from langchain_core.documents import Document
from src.loaders.base_loader import BaseLoader

class PDFLoader(BaseLoader):
    """
    Loader for PDF files that extracts text page-by-page.
    Preserves table structures by converting them to Markdown tables.
    """
    
    def load(self) -> List[Document]:
        """
        Loads the PDF and returns a list of LangChain Document objects,
        one Document per page.
        
        Returns:
            List[Document]: List of documents containing extracted page content and metadata.
        """
        documents = []
        if not os.path.exists(self.file_path):
            raise FileNotFoundError(f"PDF dosyası bulunamadı: {self.file_path}")
            
        filename = os.path.basename(self.file_path)
        
        try:
            with pdfplumber.open(self.file_path) as pdf:
                for page in pdf.pages:
                    page_num = page.page_number
                    text = self._extract_page_content(page)
                    
                    metadata = {
                        "source": filename,
                        "page": page_num
                    }
                    
                    documents.append(Document(page_content=text, metadata=metadata))
        except Exception as e:
            raise RuntimeError(f"PDF yüklenirken bir hata oluştu ({self.file_path}): {str(e)}")
            
        return documents

    def _safe_within_bbox(self, page, bbox):
        """
        Clamps bounding box coordinates to the page width and height
        to prevent out-of-bounds exceptions on poorly formatted PDFs.
        """
        x0, y0, x1, y1 = bbox
        
        # Clamp to page boundaries
        x0 = max(0.0, min(float(page.width), float(x0)))
        x1 = max(0.0, min(float(page.width), float(x1)))
        y0 = max(0.0, min(float(page.height), float(y0)))
        y1 = max(0.0, min(float(page.height), float(y1)))
        
        # Prevent degenerate dimensions
        if x0 >= x1 or y0 >= y1:
            return None
            
        try:
            return page.within_bbox((x0, y0, x1, y1))
        except Exception:
            return None

    def _extract_page_content(self, page) -> str:
        """
        Extracts text from a single page, embedding tables in Markdown format
        in their correct vertical positions.
        """
        tables = page.find_tables()
        # Sort tables by their top bounding box coordinate to maintain reading order
        tables = sorted(tables, key=lambda t: t.bbox[1])
        
        if not tables:
            return (page.extract_text() or "").strip()
            
        segments = []
        last_bottom = 0
        
        for table in tables:
            tx0, ttop, tx1, tbottom = table.bbox
            
            # 1. Extract running text above the table
            if ttop > last_bottom:
                above_page = self._safe_within_bbox(page, (0, last_bottom, page.width, ttop))
                if above_page:
                    above_text = above_page.extract_text()
                    if above_text and above_text.strip():
                        segments.append(above_text.strip())
                    
            # 2. Extract and format the table itself
            table_data = table.extract()
            if table_data:
                markdown_table = self._format_markdown_table(table_data)
                if markdown_table:
                    segments.append(markdown_table)
                    
            last_bottom = tbottom
            
        # 3. Extract remaining text below the last table
        if last_bottom < page.height:
            below_page = self._safe_within_bbox(page, (0, last_bottom, page.width, page.height))
            if below_page:
                below_text = below_page.extract_text()
                if below_text and below_text.strip():
                    segments.append(below_text.strip())
                
        return "\n\n".join(segments)

    def _format_markdown_table(self, table_data: List[List[str]]) -> str:
        """
        Converts a list of list representation of a table into Markdown format.
        """
        if not table_data or not table_data[0]:
            return ""
            
        # Clean the cells: replace inner newlines, strip whitespaces, and handle None
        cleaned_table = []
        max_cols = max(len(row) for row in table_data)
        
        for row in table_data:
            cleaned_row = []
            for cell in row:
                if cell is None:
                    cleaned_row.append("")
                else:
                    # Clean whitespaces and newlines inside cells to not break markdown tables
                    cleaned_cell = str(cell).strip().replace("\n", " ")
                    cleaned_row.append(cleaned_cell)
            # Ensure row has max_cols columns
            cleaned_row += [""] * (max_cols - len(cleaned_row))
            cleaned_table.append(cleaned_row)
            
        headers = cleaned_table[0]
        rows = cleaned_table[1:]
        
        # Build headers
        header_str = "| " + " | ".join(headers) + " |"
        separator_str = "| " + " | ".join(["---"] * len(headers)) + " |"
        
        # Build row strings
        row_strs = []
        for row in rows:
            row_strs.append("| " + " | ".join(row) + " |")
            
        return "\n".join([header_str, separator_str] + row_strs)
