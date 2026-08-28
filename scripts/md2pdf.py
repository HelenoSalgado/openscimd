#!/usr/bin/env python3
"""Conversor Editorial de Markdown para PDF usando Pandoc + Chrome Headless + Fontes Clássicas."""

import os
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path

def convert_md_to_pdf(input_md_path: str, output_pdf_path: str):
    input_path = Path(input_md_path).resolve()
    output_path = Path(output_pdf_path).resolve()
    
    if not input_path.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {input_path}")
        
    # Data de compilação atual
    comp_date_str = datetime.now().strftime("%d/%m/%Y")

    # Converter Markdown para fragmento HTML usando Pandoc
    cmd = ["pandoc", str(input_path), "-f", "markdown", "-t", "html5", "--no-highlight"]
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
    body_html = proc.stdout

    # Bloco institucional injetado automaticamente apenas no final do PDF
    colophon_html = f"""
    <div class="colophon-box">
        <h4>LeiaME &amp; OpenSciMD</h4>
        <p>Documento de orientação e padronização editorial para artigos e e-books.</p>
        <ul>
            <li><strong>Contato Geral:</strong> <a href="mailto:contato@heleno.dev">contato@heleno.dev</a></li>
            <li><strong>Suporte Editorial:</strong> <a href="mailto:suporte@leiame.heleno.dev">suporte@leiame.heleno.dev</a></li>
            <li><strong>Repositório e Issues:</strong> <a href="https://github.com/HelenoSalgado/openscimd">github.com/HelenoSalgado/openscimd</a></li>
        </ul>
        <p style="font-size: 9.5pt; color: #5F4700; margin: 2.5mm 0 1.5mm 0;">Documento compilado em {comp_date_str} · Versão 1.1 (Revisão Contínua)</p>
        <div class="colophon-copyright">© 2026 LeiaME · Artigos e E-books</div>
    </div>
    """

    # HTML completo com estilos editoriais paged-media e paleta oficial do LeiaME (#8B6B23 GoldLight)
    html_content = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<title>Guia de Tradução e Edição</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Cinzel:wght@600;700;800&family=Cormorant+Garamond:ital,wght@0,400;0,600;0,700;1,400;1,600&family=EB+Garamond:ital,wght@0,400;0,500;0,600;1,400;1,500&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
@page {{
    size: A4 portrait;
    margin: 22mm 20mm 24mm 20mm;
    @bottom-left {{
        content: "© 2026 LeiaME · Artigos e E-books";
        font-family: 'EB Garamond', serif;
        font-size: 8.5pt;
        color: #8B6B23;
        font-style: italic;
    }}
    @bottom-right {{
        content: counter(page);
        font-family: 'Cinzel', serif;
        font-size: 8.5pt;
        color: #718096;
    }}
    @top-right {{
        content: "OpenSciMD & LeiaME";
        font-family: 'Cinzel', serif;
        font-size: 7.5pt;
        letter-spacing: 0.1em;
        color: #8B6B23;
    }}
}}

@page:first {{
    margin-top: 26mm;
    @top-right {{
        content: "";
    }}
}}

* {{
    box-sizing: border-box;
}}

body {{
    font-family: 'EB Garamond', 'Georgia', serif;
    font-size: 14pt;
    line-height: 1.65;
    color: #1a202c;
    background-color: #ffffff;
    text-rendering: optimizeLegibility;
    -webkit-font-smoothing: antialiased;
}}

/* Cabeçalho Principal */
h1 {{
    font-family: 'Cinzel', 'Cormorant Garamond', serif;
    font-size: 24pt;
    font-weight: 700;
    line-height: 1.25;
    text-align: left;
    color: #5F4700;
    margin-top: 0;
    margin-bottom: 7mm;
    letter-spacing: 0.02em;
}}

/* Subtítulos */
h2 {{
    font-family: 'Cinzel', 'Cormorant Garamond', serif;
    font-size: 17pt;
    font-weight: 600;
    color: #8B6B23;
    border-bottom: 1.5px solid #E8DFCA;
    padding-bottom: 2mm;
    margin-top: 8mm;
    margin-bottom: 3.5mm;
    page-break-after: avoid;
    break-after: avoid;
}}

h3 {{
    font-family: 'Cormorant Garamond', serif;
    font-size: 15pt;
    font-weight: 700;
    color: #6E5318;
    margin-top: 6mm;
    margin-bottom: 2.5mm;
    page-break-after: avoid;
    break-after: avoid;
}}

p {{
    margin-top: 0;
    margin-bottom: 3.5mm;
    text-align: justify;
    text-justify: inter-word;
    hyphens: auto;
}}

/* Listas */
ul, ol {{
    margin-top: 0;
    margin-bottom: 4mm;
    padding-left: 7mm;
}}

li {{
    margin-bottom: 2mm;
    text-align: justify;
}}

/* Divisores elegantes */
hr {{
    border: 0;
    height: 1px;
    background-image: linear-gradient(to right, rgba(0, 0, 0, 0), rgba(139, 107, 35, 0.4), rgba(0, 0, 0, 0));
    margin: 7mm 0;
}}

/* Citações em Bloco */
blockquote {{
    margin: 5mm 0;
    padding: 3.5mm 6mm;
    border-left: 4px solid #8B6B23;
    background-color: #FDFBF7;
    font-style: italic;
    color: #4A3B2C;
    page-break-inside: avoid;
    break-inside: avoid;
}}

blockquote p {{
    margin-bottom: 0;
}}

/* Código em linha */
code {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 11pt;
    background-color: #F4ECD8;
    padding: 1.5px 5px;
    border-radius: 3px;
    color: #6E5318;
}}

/* Blocos de Código e Prompts */
pre {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 11pt;
    line-height: 1.55;
    background-color: #FAF8F5;
    border: 1px solid #E8DFCA;
    border-left: 4px solid #8B6B23;
    border-radius: 4px;
    padding: 4mm 5mm;
    margin: 5mm 0;
    overflow-x: auto;
    white-space: pre-wrap;
    word-wrap: break-word;
    page-break-inside: avoid;
    break-inside: avoid;
}}

pre code {{
    background-color: transparent;
    padding: 0;
    color: #2D241E;
}}

/* Links */
a {{
    color: #8B6B23;
    text-decoration: none;
    font-weight: 500;
}}

/* Colofão / Box Institucional Final */
.colophon-box {{
    margin-top: 12mm;
    padding: 7mm 8mm;
    background-color: #FDFBF7;
    border: 1px solid #E8DFCA;
    border-left: 5px solid #8B6B23;
    border-radius: 4px;
    page-break-inside: avoid;
    break-inside: avoid;
}}

.colophon-box h4 {{
    font-family: 'Cinzel', serif;
    font-size: 14pt;
    font-weight: 700;
    color: #5F4700;
    margin: 0 0 3mm 0;
    letter-spacing: 0.05em;
}}

.colophon-box p {{
    font-size: 12.5pt;
    margin-bottom: 3mm;
    color: #4A3B2C;
}}

.colophon-box ul {{
    font-size: 12pt;
    margin-bottom: 4mm;
    padding-left: 6mm;
}}

.colophon-box li {{
    margin-bottom: 2mm;
    color: #4A3B2C;
}}

.colophon-copyright {{
    font-family: 'EB Garamond', serif;
    font-size: 11pt;
    color: #8B6B23;
    font-style: italic;
    border-top: 1px dashed #E8DFCA;
    padding-top: 3mm;
    margin-top: 3mm;
}}
</style>
</head>
<body>
{body_html}
{colophon_html}
</body>
</html>
"""

    temp_html = tempfile.NamedTemporaryFile(suffix=".html", delete=False, mode="w", encoding="utf-8")
    try:
        temp_html.write(html_content)
        temp_html.flush()
        temp_html.close()

        # Executar Chrome Headless para imprimir em PDF
        chrome_cmd = [
            "/usr/bin/google-chrome-stable",
            "--headless=new",
            "--disable-gpu",
            "--no-sandbox",
            "--no-pdf-header-footer",
            "--virtual-time-budget=5000",
            f"--print-to-pdf={str(output_path)}",
            temp_html.name
        ]
        res = subprocess.run(chrome_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if res.returncode != 0:
            raise RuntimeError(f"Erro ao gerar PDF: {res.stderr}")
            
        print(f"✅ PDF gerado com sucesso em: {output_path}")
    finally:
        if os.path.exists(temp_html.name):
            os.remove(temp_html.name)

if __name__ == "__main__":
    import sys
    src = sys.argv[1] if len(sys.argv) > 1 else "guia-tradutor-leia-me.md"
    dst = sys.argv[2] if len(sys.argv) > 2 else "guia-tradutor-leia-me.pdf"
    convert_md_to_pdf(src, dst)
