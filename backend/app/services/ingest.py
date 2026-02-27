import httpx
from bs4 import BeautifulSoup
from sqlmodel import Session
from app.models.document import Document

async def fetch_and_clean_url(url: str, user_id: int, session: Session) -> Document:
    async with httpx.AsyncClient() as client:
        response = await client.get(url, follow_redirects=True, timeout=15.0)
        response.raise_for_status()
        raw_html = response.text
        
    soup = BeautifulSoup(raw_html, "html.parser")
    title = soup.title.string if soup.title and soup.title.string else url
    
    # Very basic readability pass
    for element in soup(["script", "style", "meta", "noscript", "header", "footer", "nav", "aside", "svg"]):
        element.extract()
    
    cleaned_content = soup.get_text(separator="\n", strip=True)
    
    doc = Document(
        user_id=user_id,
        url=url,
        title=title.strip()[:200],
        raw_content=raw_html,
        cleaned_content=cleaned_content
    )
    session.add(doc)
    session.commit()
    session.refresh(doc)
    return doc
