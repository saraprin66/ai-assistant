from pathlib import Path
from pypdf import PdfReader
from docx import Document
from embedder import Embedder
from database import Database
import requests
from bs4 import BeautifulSoup


def extract_pdf(file_path):
    reader = PdfReader(file_path)

    pages = []

    for index, page in enumerate(reader.pages, start=1):
        text = page.extract_text()

        if text:
            pages.append({
                "page": index,
                "text": text
            })

    return pages


def extract_docx(file_path):
    document = Document(file_path)

    content = []

    for paragraph in document.paragraphs:
        content_text = paragraph.text

        if content_text:
            content.append({
                "page": None,
                "text": content_text
            })

    return content

def extract_web(url):
    response = requests.get(url)

    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    text = soup.get_text("", strip=True)
    return [
        {
            "page":None,
            "text":text
        }
    ]



def split_text(text, chunk_size=1000, overlap=200):
    chunks_list = []

    start = 0

    while start < len(text):
        end = start + chunk_size
        sliced_text = text[start:end]

        chunks_list.append(sliced_text)

        start = end - overlap

    return chunks_list


def ingest_file(file_path):
    extension = Path(file_path).suffix
    embedder = Embedder()
    
    database = Database()

    if extension == ".pdf":
        pages = extract_pdf(file_path)

    elif extension == ".docx":
        pages = extract_docx(file_path)

    else:
        print("That is an unsupported file type.")
        return
    document_path = Path(file_path)
    document_name = document_path.name
    document_id = document_path.stem

    for page in pages:
        page_text = page["text"]

        chunks = split_text(
            page_text,
            chunk_size=1000,
            overlap=200
        )
        
        for chunk_index, chunk in enumerate(chunks) :
            chunk_embedding = embedder.get_embedding(chunk)

            source = document_name

            metadata = {
                "page": page["page"]
            }
            
            database.insert_chunk(document_id=document_id,
                document_name=document_name,
                chunk_index=chunk_index,
                content=chunk,
                embedding=chunk_embedding,
                source=source,
                metadata=metadata
            )
def ingest_web(url):
    embedder = Embedder()
    database = Database()

    document_id = url
    document_name = url
    source = url

    pages = extract_web(url)

    for page in pages:
        page_text = page["text"]

        chunks = split_text(
            page_text,
            chunk_size=1000,
            overlap=200
        )

        for chunk_index, chunk in enumerate(chunks):
            chunk_embedding = embedder.get_embedding(chunk)

            metadata = {
                "page": page["page"]
            }

            database.insert_chunk(
                document_id=document_id,
                document_name=document_name,
                chunk_index=chunk_index,
                content=chunk,
                embedding=chunk_embedding,
                source=source,
                metadata=metadata
            )


     