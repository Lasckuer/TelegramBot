import math
import app.keyboards.inline as kb_inline

def generate_page_text(matches: list, query: str, page: int, per_page: int = 5):
    total_pages = math.ceil(len(matches) / per_page)
    start = page * per_page
    end = start + per_page
    page_items = matches[start:end]

    text = f"🔍 Результаты по запросу «{query}» (Стр. {page+1} из {total_pages}):\n\n"
    for row in page_items:
        date_str = row.get('date', '-')
        text += f"• <b>{row.get('name', '-')}</b> — {row.get('price', 0)}р <i>({date_str})</i>\n"

    markup = kb_inline.get_pagination_kb(page, total_pages)
    return text, markup