"""Gerador de arte conceitual de capas com IA (Gemini, OpenAI ou Agy)."""

from __future__ import annotations

import base64
import os
import shutil
import subprocess
import time
from pathlib import Path

import requests
from dotenv import load_dotenv
from google import genai

from scripts.covers import find_markdown_metadata, inject_cover_text

_JOURNAL_PALETTE_HINTS: dict[str, str] = {
    "fides reformata": "deep petrol blue (#0D3B4C), emerald green (#134E3F), and matte gold (#8C733E)",
    "peitho": "Greek terracotta (#8C3827), burnt sienna (#59281E), and slate blue (#1C2630)",
    "ipda": "deep burgundy (#4A121A), dark wine (#2E0B12), and patina bronze (#7A5C28)",
    "history of science": "dark cobalt blue (#1A2E40), academic olive (#3B4A2D), and patina bronze (#736345)",
    "boletim cearense": "dark cobalt blue (#1A2E40), academic olive (#3B4A2D), and patina bronze (#736345)",
    "hispania sacra": "imperial purple (#4D1024) and burnt amber (#663C1B)",
    "educação": "deep royal blue (#12284C) and ochre copper (#6B4423)",
}


def get_env(base_dir: str | Path) -> os._Environ[str] | dict[str, str]:
    env_path = Path(base_dir) / ".env"
    if not env_path.exists():
        print("❌ Arquivo .env não localizado! Copie .env.example para .env")
        return {}
    load_dotenv(dotenv_path=env_path)
    return os.environ


def _build_cover_prompt(
    metadata: dict,
    is_book: bool,
    base_name: str,
    custom_style: str | None = None,
) -> str:
    summary = str(metadata.get("summary", "") or "")
    title = str(metadata.get("title", base_name) or base_name)
    categories = metadata.get("categories", [])
    categories_str = ", ".join(categories) if isinstance(categories, list) else str(categories)

    summary_text = f'Core philosophical and theological themes: "{summary}". ' if summary else ""
    cat_text = f"Categories: {categories_str}. " if categories_str else ""

    if is_book:
        base_prompt = (
            f"Masterpiece fine-art 2D background artwork for an editorial classic book / treatise, "
            f"vertical 2:3 aspect ratio (portrait orientation), 100% full-bleed flat 2D surface. "
            f"Aesthetic: High-end classical publishing house (Penguin Classics, Oxford World's Classics, Gallimard) "
            f"with historically authentic fine-art oil or engraving textures and solemn chiaroscuro. "
            f'Subject: A solemn historical scene or museum-grade fine-art visual interpretation of the core thesis of: "{title}". '
            f"{summary_text}{cat_text}"
            f"Historical human figures in authentic period attire are permitted when appropriate to the treatise. "
            f"Keep the upper third balanced and dark/calm enough for high-contrast serif typography overlay, "
            f"and keep the bottom 10% calm and uncluttered for historical date breathing room. "
            f"Strictly NO text, NO letters, NO words, NO titles, NO borders, NO horizontal divider bars, "
            f"NO 3D mockups, NO isolated open books, NO scrolls, NO lamps, NO kitsch devotional clichés, "
            f"and strictly NO figurative depictions of Jesus Christ (Second Commandment)."
        )
    else:
        journal_raw = str(metadata.get("journal", "") or "").lower()
        palette = "electric indigo (#141E38) and neutral graphite (#242933)"
        for key, hint in _JOURNAL_PALETTE_HINTS.items():
            if key in journal_raw:
                palette = hint
                break
        base_prompt = (
            f"Flat 2D minimalist geometric editorial background artwork for an academic scholarly article, "
            f"vertical 2:3 aspect ratio (portrait orientation), 100% full-bleed canvas. "
            f"Background: Deep textured charcoal / anthracite linen (#111418 to #15181D). "
            f"Center visual (33% to 82% vertical zone): Fine vector-like matte gold geometric lines (#D4AF37) "
            f"combined with subtle translucent circular and arc forms in {palette}. "
            f'Conceptual inspiration from thesis: "{title}". {summary_text}{cat_text}'
            f"Keep the upper 30% and lower 15% completely clean dark charcoal for serif title and footer breathing room. "
            f"Strictly NO text, NO letters, NO numbers, NO realistic illustrations, NO human figures, "
            f"NO borders, NO frames, NO 3D mockups, NO books, NO scrolls."
        )

    return f"{base_prompt} Specific visual nuances: {custom_style}." if custom_style else base_prompt


def generate_cover(
    base_dir: str,
    article_name: str,
    custom_style: str | None = None,
    provider: str = "gemini",
) -> None:
    env = get_env(base_dir)

    metadata, is_book, canonical_slug = find_markdown_metadata(base_dir, article_name)
    if not metadata:
        print(
            f"❌ Documento Markdown correspondente não encontrado em content/books nem em content/articles para: {article_name}"
        )
        return

    base_name = canonical_slug
    cover_dest = Path(base_dir) / "assets" / "covers" / f"{base_name}.png"
    final_prompt = _build_cover_prompt(metadata, is_book, base_name, custom_style=custom_style)

    if provider == "gemini":
        api_key = env.get("IA_KEY")
        if not api_key:
            print("❌ Erro: Chave IA_KEY não preenchida no .env")
            return

        model_name = env.get("IA_MODEL_NAME", "gemini-3.1-flash-image")
        print(f"🎨 Modelo de IA: {model_name}\n⏳ Enviando requisição conceitual para o Google Gemini...")

        client = genai.Client(api_key=api_key)
        try:
            result = client.models.generate_images(
                model=model_name,
                prompt=final_prompt,
                config=genai.types.GenerateImagesConfig(
                    number_of_images=1,
                    output_mime_type="image/png",
                ),
            )

            if not result.generated_images or not result.generated_images[0].image:
                print("❌ Nenhuma imagem retornada pelo Gemini.")
                return

            img_bytes = result.generated_images[0].image.image_bytes
            if not img_bytes:
                print("❌ Bytes de imagem vazios retornados pelo Gemini.")
                return

            cover_dest.parent.mkdir(parents=True, exist_ok=True)
            temp_path = cover_dest.parent / f".tmp_raw_{base_name}.png"
            temp_path.write_bytes(img_bytes)

            print("🎨 Compondo tipografia editorial nobre...")
            inject_cover_text(base_dir, str(temp_path), target_slug=base_name)

        except Exception as exc:
            print(f"❌ Erro na geração Gemini: {exc}")

    elif provider == "openai":
        api_key = env.get("IA_KEY")
        api_url = env.get("IA_API_URL")
        model_name = env.get("IA_MODEL_NAME")
        if not api_key or not api_url:
            print("❌ Erro: IA_KEY ou IA_API_URL não preenchidas no .env")
            return

        print(f"🎨 Modelo de IA (OpenAI API): {model_name or 'Padrão'}\n⏳ Enviando requisição conceitual...")
        try:
            resp = requests.post(
                api_url,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {api_key}",
                },
                json={
                    "model": model_name,
                    "prompt": final_prompt,
                    "n": 1,
                    "size": "1024x1536",
                    "response_format": "url",
                },
                timeout=60,
            )
            resp.raise_for_status()
            data = resp.json()
            url = data.get("data", [{}])[0].get("url") or data.get("url") or data.get("image")
            b64 = data.get("data", [{}])[0].get("b64_json")

            cover_dest.parent.mkdir(parents=True, exist_ok=True)
            temp_path = cover_dest.parent / f".tmp_raw_{base_name}.png"
            if url:
                img_data = requests.get(url, timeout=60).content
                temp_path.write_bytes(img_data)
            elif b64:
                temp_path.write_bytes(base64.b64decode(b64))

            print("🎨 Compondo tipografia editorial nobre...")
            inject_cover_text(base_dir, str(temp_path), target_slug=base_name)
        except Exception as exc:
            print(f"❌ Erro API: {exc}")

    elif provider == "agy":
        agy_bin = shutil.which("agy")
        if not agy_bin:
            print("❌ Erro: CLI 'agy' não foi encontrada no PATH do sistema.")
            return

        print("🎨 Provedor: Antigravity CLI (agy)\n⏳ Acionando agy para geração de imagem conceitual...")
        start_time = time.time() - 5

        raw_slug = base_name.replace("-", "_")
        prompt_instruction = (
            f"Gere uma imagem conceitual de capa na proporção '2:3' com o ImageName '{raw_slug}_raw' "
            f"utilizando a ferramenta generate_image com o seguinte prompt estrito em inglês:\n\n{final_prompt}"
        )

        try:
            res = subprocess.run(
                [agy_bin, "--dangerously-skip-permissions", "-p", prompt_instruction],
                capture_output=True,
                text=True,
                check=False,
            )

            brain_dir = Path.home() / ".gemini" / "antigravity-cli" / "brain"
            found_img: Path | None = None

            search_slugs = {
                base_name,
                base_name.replace("-", "_"),
                base_name.replace("_", "-"),
                raw_slug,
                f"{raw_slug}_raw",
                f"{base_name}_raw",
            }

            candidates: list[Path] = []
            if brain_dir.exists():
                for ext in ["*.jpg", "*.jpeg", "*.png", "*.webp"]:
                    for img_p in brain_dir.rglob(ext):
                        if any(slug in img_p.stem for slug in search_slugs):
                            candidates.append(img_p)

            for ext in ["*.jpg", "*.jpeg", "*.png", "*.webp"]:
                for img_p in Path(base_dir).rglob(ext):
                    if any(slug in img_p.stem for slug in search_slugs):
                        candidates.append(img_p)

            if candidates:
                recent = [c for c in candidates if c.stat().st_mtime >= start_time]
                if recent:
                    recent.sort(key=lambda p: p.stat().st_mtime, reverse=True)
                    found_img = recent[0]
                else:
                    candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
                    found_img = candidates[0]

            if not found_img:
                print("❌ Não foi possível localizar a imagem gerada pelo agy.")
                if res.stderr:
                    print(f"   Log agy: {res.stderr}")
                return

            print(f"📦 Arte conceitual recuperada: {found_img.name}")
            cover_dest.parent.mkdir(parents=True, exist_ok=True)
            target_cover_path = cover_dest.parent / f"{base_name}.png"
            shutil.copy2(found_img, target_cover_path)

            print("🎨 Compondo tipografia editorial nobre...")
            inject_cover_text(base_dir, str(target_cover_path), target_slug=base_name)

        except Exception as exc:
            print(f"❌ Erro na integração com agy: {exc}")
