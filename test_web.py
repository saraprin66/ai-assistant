from ingest import extract_web

url = "https://ensiasd.uiz.ac.ma"

pages = extract_web(url)

print(pages[0]["text"][:1000])