"""Bounded, offline Chromium rendering of trusted A4 document pages."""

import asyncio
import base64
import html
import math
import threading
from pathlib import Path

from app.services.auth import AuthError

LAYOUT_VERSION = "a4-v1"
PAGE_ROW_BUDGET = 800
COLUMN_WIDTHS = (0.12, 0.23, 0.23, 0.16, 0.14, 0.12)
MAX_PAGES = 30
MAX_ROWS = 3000
MAX_BYTES = 20 * 1024 * 1024
_RENDER_SLOT = threading.BoundedSemaphore(1)


def estimated_row_height(row):
    """Conservative fixed-template estimate, independent of locale/browser state.

    At 10px font, reserve 20px per codepoint (including wide glyphs), four
    spaces per tab, explicit newlines, 13px line-height and 12px borders/padding.
    The actual renderer still verifies every table against its footer.
    """
    heights = [61]
    for index, cell in enumerate(row):
        fraction = COLUMN_WIDTHS[index] if index < len(COLUMN_WIDTHS) else min(COLUMN_WIDTHS)
        chars_per_line = max(1, math.floor((703 * fraction - 12) / 20))
        text = str(cell).replace("\r\n", "\n").replace("\r", "\n").expandtabs(4)
        lines = sum(max(1, math.ceil(len(line) / chars_per_line)) for line in text.split("\n"))
        heights.append(lines * 13 + 12)
    return max(heights)


def paginate(rows):
    if len(rows) > MAX_ROWS:
        raise AuthError(422, "Documento excede o limite de registros")
    pages, current, used = [], [], 0
    for row in rows:
        height = estimated_row_height(row)
        if height > PAGE_ROW_BUDGET:
            raise AuthError(422, "Registro excede a altura de uma página")
        if current and used + height > PAGE_ROW_BUDGET:
            pages.append(current)
            current, used = [], 0
        current.append(row)
        used += height
        if len(pages) >= MAX_PAGES:
            raise AuthError(422, "Documento excede o limite de 30 páginas; filtre unidade ou dia")
    pages.append(current)
    return pages


def document_html(pages, title, label):
    font = Path(__file__).parents[1] / "assets" / "fonts" / "manrope-variable.ttf"
    encoded = base64.b64encode(font.read_bytes()).decode("ascii")
    escape = lambda value: html.escape(str(value), quote=True)  # noqa: E731
    sections = []
    for number, rows in enumerate(pages, 1):
        body = (
            "".join(
                "<tr>" + "".join(f"<td>{escape(cell)}</td>" for cell in row) + "</tr>"
                for row in rows
            )
            or '<tr><td colspan="6">Nenhum registro neste recorte.</td></tr>'
        )
        sections.append(
            '<section class="sheet"><header><b>RecepHub</b>'
            f"<h1>{escape(title)}</h1><strong>{escape(label)}</strong></header>"
            '<table><colgroup><col style="width:12%"><col style="width:23%">'
            '<col style="width:23%"><col style="width:16%"><col style="width:14%">'
            '<col style="width:12%"></colgroup><thead><tr><th>Data</th><th>Colaboradora</th>'
            "<th>Unidade</th><th>Período</th><th>Intervalo</th><th>Posto / estado</th>"
            f"</tr></thead><tbody>{body}</tbody></table>"
            f"<footer>{escape(label)} · Página {number} de {len(pages)} · {LAYOUT_VERSION}"
            "</footer></section>"
        )
    return (
        '<!doctype html><html lang="pt-BR"><meta charset="utf-8"><style>'
        f"@font-face{{font-family:Document;src:url(data:font/ttf;base64,{encoded})}}"
        "@page{size:A4;margin:0}*{box-sizing:border-box}html,body{margin:0;padding:0}"
        "body{font:11px Document,sans-serif;font-variant-ligatures:none;"
        "color:#172c3c;background:white}"
        ".sheet{width:210mm;height:297mm;padding:12mm;position:relative;break-after:page}"
        ".sheet:last-child{break-after:auto}header{height:29mm}h1{font-size:19px;margin:5px 0}"
        "strong{font-size:11px}table{width:100%;table-layout:fixed;border-collapse:collapse}"
        "th,td{text-align:left;padding:5px;border:1px solid #a6b8bd;overflow-wrap:anywhere;"
        "white-space:pre-wrap;vertical-align:top}th{background:#e9f2f1}td{font-size:10px;"
        "line-height:13px}tr{height:16mm}footer{position:absolute;bottom:10mm;left:12mm;"
        "right:12mm;border-top:1px solid #a6b8bd;padding-top:3mm;font-size:10px}"
        "</style><body>" + "".join(sections) + "</body></html>"
    )


async def _render(markup, output_format, page_number):
    from playwright.async_api import async_playwright

    async with async_playwright() as runtime:
        browser = await runtime.chromium.launch(headless=True, timeout=10000)
        try:
            context = await browser.new_context(
                java_script_enabled=False,
                viewport={"width": 794, "height": 1123},
                device_scale_factor=1240 / (210 * 96 / 25.4),
            )
            await context.route("**/*", lambda route: route.abort())
            page = await context.new_page()
            page.set_default_timeout(10000)
            await page.set_content(markup, wait_until="load", timeout=10000)
            await page.evaluate("document.fonts.ready")
            await page.emulate_media(media="print")
            fits = await page.locator(".sheet").evaluate_all(
                "sheets => sheets.every(sheet => "
                "sheet.querySelector('table').getBoundingClientRect().bottom + 8 <= "
                "sheet.querySelector('footer').getBoundingClientRect().top && "
                "sheet.querySelector('header strong').getBoundingClientRect().bottom <= "
                "sheet.querySelector('header').getBoundingClientRect().bottom)"
            )
            if not fits:
                raise RuntimeError("Document layout exceeds page")
            if output_format == "pdf":
                return await page.pdf(format="A4", print_background=True, prefer_css_page_size=True)
            # Move the selected original page to origin, avoiding raster rounding at
            # fractional A4 offsets on later sheets. Its printed page label stays intact.
            await page.locator(".sheet").evaluate_all(
                "(sheets, selected) => sheets.forEach((sheet, index) => {"
                "if (index !== selected) sheet.remove();})",
                page_number - 1,
            )
            return await page.locator(".sheet").first.screenshot(type="png", timeout=10000)
        finally:
            await browser.close()


def render_document(markup, output_format, page_number):
    if not _RENDER_SLOT.acquire(blocking=False):
        raise AuthError(503, "Exportação ocupada; tente novamente", retry_after=2)
    try:

        async def bounded():
            return await asyncio.wait_for(_render(markup, output_format, page_number), timeout=30)

        result = asyncio.run(bounded())
        if len(result) > MAX_BYTES:
            raise RuntimeError("Render limits")
        return result
    except Exception:
        raise AuthError(503, "Não foi possível gerar o documento; tente novamente") from None
    finally:
        _RENDER_SLOT.release()
