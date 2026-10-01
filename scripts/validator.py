import os
from pathlib import Path
from typing import List, Tuple
from scripts.utils import parse_markdown_file, parse_date_to_timestamp, get_files_recursively
from scripts.categories import validate_categories


def validate_articles(base_dir: str) -> bool:
    """Valida formato, metadados e categorias dos artigos acadêmicos."""
    print("🧪 Iniciando validação de formato e metadados dos artigos...\n")
    articles_dir = Path(base_dir) / "content" / "articles"
    covers_dir = Path(base_dir) / "assets" / "covers"
    raw_dir = Path(base_dir) / "assets" / "data" / "raw"

    if not articles_dir.exists():
        print(f"❌ Diretório de artigos não encontrado em: {articles_dir}")
        return False

    invalid_count = 0
    total_errors = 0
    total_warnings = 0

    files = [Path(p) for p in get_files_recursively(articles_dir)]

    for file in files:
        errors: List[str] = []
        warnings: List[str] = []
        base_name = file.stem
        rel_path = file.relative_to(articles_dir).as_posix()

        try:
            with open(file, "r", encoding="utf-8") as f:
                content = f.read()

            if not content.startswith("---"):
                errors.append('O arquivo não inicia com delimitadores de metadados ("---").')

            parsed = parse_markdown_file(str(file))
            metadata = parsed["metadata"]

            if not metadata.get("title") or not str(metadata.get("title")).strip():
                errors.append('Campo obrigatório "title" está ausente ou vazio.')

            has_author = bool(metadata.get("author") and str(metadata.get("author")).strip())
            has_authors = bool(
                metadata.get("authors")
                and isinstance(metadata.get("authors"), list)
                and metadata.get("authors")
            )
            if not has_author and not has_authors:
                errors.append('Campo de autoria obrigatório ("author" ou "authors") ausente ou vazio.')

            summary = metadata.get("summary") or metadata.get("sumary")
            if not summary or not str(summary).strip():
                errors.append('Resumo ("summary" ou "sumary") ausente ou vazio.')
            elif metadata.get("sumary"):
                warnings.append('Encontrado erro de digitação no campo "sumary". Recomenda-se renomear para "summary".')

            if not metadata.get("date"):
                errors.append('Campo obrigatório "date" ausente.')
            else:
                ts = parse_date_to_timestamp(metadata.get("date"))
                if not ts:
                    errors.append(f'Formato de data inválido: "{metadata.get("date")}". Use YYYY-MM-DD ou DD-MM-YYYY.')

            license_ = metadata.get("license") or metadata.get("licence")
            if not license_ or not str(license_).strip():
                errors.append('Campo de licença obrigatório ("license" ou "licence") ausente ou vazio.')
            elif metadata.get("licence"):
                warnings.append('Chave de licença escrita como "licence". Recomenda-se padronizar para "license".')

            pages = metadata.get("pages")
            if not pages or not str(pages).strip():
                errors.append('Campo obrigatório "pages" está ausente ou vazio.')

            # Validação estrita de categorias canônicas
            if "category" in metadata and "categories" not in metadata:
                warnings.append('Uso da chave obsoleta "category". Padronize para "categories".')
                cat_val = [metadata.get("category")] if isinstance(metadata.get("category"), str) else metadata.get("category")
            else:
                cat_val = metadata.get("categories")

            cat_errors = validate_categories(cat_val)
            errors.extend(cat_errors)

            if not metadata.get("doi") and not metadata.get("DOI"):
                warnings.append('Campo recomendado "DOI" está ausente.')
            if not metadata.get("journal"):
                warnings.append('Campo administrativo "journal" está ausente.')


            if not (covers_dir / "mobile" / f"{base_name}.webp").exists():
                warnings.append(f"Imagem de capa mobile correspondente não localizada em assets/covers/mobile/{base_name}.webp.")

            raw_pdf = raw_dir / f"{base_name}.pdf"
            if not raw_pdf.exists() and not any(raw_dir.glob(f"{base_name}.*")):
                warnings.append(f"Arquivo de fonte original não localizado em assets/data/raw/{base_name}.pdf.")

        except Exception as e:
            errors.append(f"Falha crítica ao ler/processar arquivo: {e}")

        if errors or warnings:
            print(f"📄 Artigo: {rel_path}")
            if errors:
                invalid_count += 1
                total_errors += len(errors)
                for err in errors:
                    print(f"  ❌ [ERRO] {err}")
            if warnings:
                total_warnings += len(warnings)
                for warn in warnings:
                    print(f"  ⚠️ [ALERTA] {warn}")
            print("")

    print("-" * 50)
    print(f"📊 Resumo da Validação de Artigos:")
    print(f"   - Artigos Verificados: {len(files)}")
    print(f"   - Artigos com Erros Fatais: {invalid_count}")
    print(f"   - Total de Erros: {total_errors}")
    print(f"   - Total de Alertas: {total_warnings}\n")

    if invalid_count > 0:
        print("❌ Falha na validação de artigos! Corrija os erros listados.")
        return False
    else:
        print("✅ Validação de artigos concluída com sucesso! Todos os artigos estão aptos.")
        return True


def validate_books(base_dir: str) -> bool:
    """Valida formato, metadados e categorias dos e-books e volumes."""
    print("📚 Iniciando validação de formato e metadados dos e-books...\n")
    books_dir = Path(base_dir) / "content" / "books"
    covers_dir = Path(base_dir) / "assets" / "covers"

    if not books_dir.exists():
        print(f"❌ Diretório de livros não encontrado em: {books_dir}")
        return False

    invalid_count = 0
    total_errors = 0
    total_warnings = 0

    files = [Path(p) for p in get_files_recursively(books_dir)]

    for file in files:
        errors: List[str] = []
        warnings: List[str] = []
        base_name = file.stem
        rel_path = file.relative_to(books_dir).as_posix()

        try:
            with open(file, "r", encoding="utf-8") as f:
                content = f.read()

            if not content.startswith("---"):
                errors.append('O arquivo não inicia com delimitadores de metadados ("---").')

            parsed = parse_markdown_file(str(file))
            metadata = parsed["metadata"]

            if not metadata.get("title") or not str(metadata.get("title")).strip():
                errors.append('Campo obrigatório "title" está ausente ou vazio.')

            has_author = bool(metadata.get("author") and str(metadata.get("author")).strip())
            has_authors = bool(
                metadata.get("authors")
                and isinstance(metadata.get("authors"), list)
                and metadata.get("authors")
            )
            if not has_author and not has_authors:
                errors.append('Campo de autoria obrigatório ("author" ou "authors") ausente ou vazio.')

            summary = metadata.get("summary") or metadata.get("sumary")
            if not summary or not str(summary).strip():
                errors.append('Resumo ("summary" ou "sumary") ausente ou vazio.')

            if not metadata.get("date"):
                errors.append('Campo obrigatório "date" ausente.')

            license_ = metadata.get("license") or metadata.get("licence")
            if not license_ or not str(license_).strip():
                errors.append('Campo de licença obrigatório ("license" ou "licence") ausente ou vazio.')

            # Validação estrita de categorias canônicas
            if "category" in metadata and "categories" not in metadata:
                warnings.append('Uso da chave obsoleta "category". Padronize para "categories".')
                cat_val = [metadata.get("category")] if isinstance(metadata.get("category"), str) else metadata.get("category")
            else:
                cat_val = metadata.get("categories")

            cat_errors = validate_categories(cat_val)
            errors.extend(cat_errors)

            if not (covers_dir / "mobile" / f"{base_name}.webp").exists():
                warnings.append(f"Imagem de capa mobile correspondente não localizada em assets/covers/mobile/{base_name}.webp.")

        except Exception as e:
            errors.append(f"Falha crítica ao ler/processar arquivo: {e}")

        if errors or warnings:
            print(f"📚 E-book: {rel_path}")
            if errors:
                invalid_count += 1
                total_errors += len(errors)
                for err in errors:
                    print(f"  ❌ [ERRO] {err}")
            if warnings:
                total_warnings += len(warnings)
                for warn in warnings:
                    print(f"  ⚠️ [ALERTA] {warn}")
            print("")

    print("-" * 50)
    print(f"📊 Resumo da Validação de E-books:")
    print(f"   - Livros Verificados: {len(files)}")
    print(f"   - Livros com Erros Fatais: {invalid_count}")
    print(f"   - Total de Erros: {total_errors}")
    print(f"   - Total de Alertas: {total_warnings}\n")

    if invalid_count > 0:
        print("❌ Falha na validação de e-books! Corrija os erros listados.")
        return False
    else:
        print("✅ Validação de e-books concluída com sucesso! Todos os e-books estão aptos.")
        return True


def validate_all(base_dir: str) -> bool:
    """Valida artigos e e-books."""
    articles_ok = validate_articles(base_dir)
    print("\n" + "=" * 50 + "\n")
    books_ok = validate_books(base_dir)
    return articles_ok and books_ok
