"""Interactive terminal interface with arrow-key navigation, inline dictionary definitions, and persistent ignore caching."""

from __future__ import annotations

import shutil
import sys
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from scripts.spellchecker.definition_lookup import DefinitionLookup
from scripts.spellchecker.dictionary import DictionaryManager
from scripts.spellchecker.engine import ReviewEngine
from scripts.spellchecker.keyboard import KeyReader
from scripts.spellchecker.matcher import CasePreserver
from scripts.spellchecker.models import FileReviewResult, ReviewAction, ReviewMatch


class Colors:
    """ANSI color codes for terminal formatting."""
    HEADER = "\033[95m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    MAGENTA = "\033[95m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    UNDERLINE = "\033[4m"
    REVERSE = "\033[7m"
    ENDC = "\033[0m"


class InteractiveReviewUI:
    """Handles rich terminal display, interactive review workflow, and inline dictionary lookups."""

    def __init__(
        self,
        engine: Optional[ReviewEngine] = None,
        def_lookup: Optional[DefinitionLookup] = None,
    ) -> None:
        self.engine = engine or ReviewEngine()
        self.def_lookup = def_lookup or DefinitionLookup()

    def run(
        self,
        filepath: Path | str,
        output_path: Optional[Path | str] = None,
        create_backup: bool = False,
    ) -> FileReviewResult:
        """Runs the interactive spellcheck review loop on a file."""
        src_path = Path(filepath)
        dest_path = Path(output_path) if output_path else src_path

        if not src_path.is_file():
            print(f"{Colors.RED}❌ Erro: Arquivo '{src_path}' não encontrado.{Colors.ENDC}")
            return FileReviewResult(filepath=src_path, output_filepath=dest_path)

        with open(src_path, "r", encoding="utf-8") as f:
            raw_content = f.read()

        matches = self.engine.scan_text(raw_content)
        result = FileReviewResult(filepath=src_path, output_filepath=dest_path, total_found=len(matches), matches=matches)

        if not matches:
            print(f"\n{Colors.GREEN}✨ Nenhuma ocorrência de erro ou arcaísmo encontrada em '{src_path.name}'. Tudo limpo!{Colors.ENDC}\n")
            if dest_path != src_path:
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src_path, dest_path)
                print(f"{Colors.DIM}Arquivo copiado para destino: {dest_path}{Colors.ENDC}")
            return result

        print(f"\n{Colors.HEADER}{Colors.BOLD}╔══════════════════════════════════════════════════════════════════════╗{Colors.ENDC}")
        print(f"{Colors.HEADER}{Colors.BOLD}║           Revisão Editorial e Ortográfica (OpenSciMD)                ║{Colors.ENDC}")
        print(f"{Colors.HEADER}{Colors.BOLD}╚══════════════════════════════════════════════════════════════════════╝{Colors.ENDC}")
        print(f"📄 Arquivo Original: {Colors.CYAN}{src_path}{Colors.ENDC}")
        if dest_path != src_path:
            print(f"💾 Arquivo de Saída:  {Colors.GREEN}{dest_path}{Colors.ENDC} {Colors.DIM}(preserva original){Colors.ENDC}")
        print(f"🔍 Ocorrências detectadas: {Colors.YELLOW}{Colors.BOLD}{len(matches)}{Colors.ENDC}\n")

        replacements: List[Tuple[int, int, str]] = []
        replace_all_dict: Dict[str, str] = {}
        session_ignore_keys: Set[str] = set()

        # Undo history stack: (match_idx, replacement_tuple, replace_all_dict, session_ignore_keys)
        history: List[Tuple[int, Tuple[int, int, str] | None, Dict[str, str], Set[str]]] = []

        match_idx = 0
        total_matches = len(matches)

        try:
            while match_idx < total_matches:
                match = matches[match_idx]
                key = match.dict_key.lower()

                # Check if ignored persistently or in session
                if self.engine.dict_manager.is_ignored(key) or key in session_ignore_keys:
                    match_idx += 1
                    continue

                # Check if this word was set to replace-all
                if key in replace_all_dict:
                    chosen_replacement = CasePreserver.preserve_case(match.original_text, replace_all_dict[key])
                    replacements.append((match.start, match.end, chosen_replacement))
                    match.applied_replacement = chosen_replacement
                    match_idx += 1
                    continue

                # Run interactive prompt loop for this match
                action, chosen_text = self._handle_interactive_match(match, match_idx + 1, total_matches)

                if action == ReviewAction.QUIT:
                    print(f"\n{Colors.YELLOW}⚠️  Revisão interrompida pelo usuário.{Colors.ENDC}")
                    if replacements:
                        print(f"Deseja salvar as {len(replacements)} modificações realizadas até agora? [{Colors.GREEN}s{Colors.ENDC}/{Colors.RED}n{Colors.ENDC}]")
                        confirm = input("> ").strip().lower()
                        if confirm == "s":
                            break
                        else:
                            print(f"{Colors.YELLOW}Modificações descartadas.{Colors.ENDC}")
                            return result
                    else:
                        print(f"{Colors.YELLOW}Nenhuma alteração a salvar.{Colors.ENDC}")
                        return result

                elif action == ReviewAction.UNDO:
                    if not history:
                        print(f"{Colors.YELLOW}Nenhuma ação anterior para desfazer.{Colors.ENDC}")
                        continue
                    prev_idx, prev_repl, prev_rep_dict, prev_ign_all = history.pop()
                    if prev_repl and prev_repl in replacements:
                        replacements.remove(prev_repl)
                    replace_all_dict = prev_rep_dict
                    session_ignore_keys = prev_ign_all
                    match_idx = prev_idx
                    print(f"{Colors.CYAN}↺ Desfeito! Retornando à ocorrência anterior.{Colors.ENDC}")
                    continue

                elif action == ReviewAction.DELETE_FROM_DICT:
                    self.engine.dict_manager.remove_entry(key)
                    self.engine.dict_manager.add_ignored(key)
                    self.engine.reload()
                    session_ignore_keys.add(key)
                    print(f"{Colors.RED}🗑️  '{key}' removido do dicionário e adicionado à lista de ignoradas permanentemente.{Colors.ENDC}")
                    history.append((match_idx, None, dict(replace_all_dict), set(session_ignore_keys)))
                    match_idx += 1

                elif action == ReviewAction.REPLACE:
                    selected = chosen_text or match.suggested_text
                    repl = (match.start, match.end, selected)
                    replacements.append(repl)
                    match.applied_replacement = selected
                    history.append((match_idx, repl, dict(replace_all_dict), set(session_ignore_keys)))
                    match_idx += 1

                elif action == ReviewAction.SKIP:
                    # Skip this occurrence in session
                    session_ignore_keys.add(key)
                    history.append((match_idx, None, dict(replace_all_dict), set(session_ignore_keys)))
                    match_idx += 1

                elif action == ReviewAction.REPLACE_ALL:
                    selected = chosen_text or match.suggested_text
                    replace_all_dict[key] = selected
                    repl = (match.start, match.end, selected)
                    replacements.append(repl)
                    match.applied_replacement = selected
                    history.append((match_idx, repl, dict(replace_all_dict), set(session_ignore_keys)))

                    # Prompt to save to personal dictionary
                    print(f"Deseja memorizar '{key}' -> '{selected.lower()}' no dicionário pessoal para todos os próximos livros? [{Colors.GREEN}s{Colors.ENDC}/{Colors.RED}n{Colors.ENDC}]")
                    save_perm = input("> ").strip().lower()
                    if save_perm == "s":
                        self.engine.dict_manager.add_entry(key, selected.lower())
                        self.engine.reload()
                        print(f"{Colors.GREEN}✅ Dicionário pessoal atualizado permanentemente!{Colors.ENDC}")

                    match_idx += 1

                elif action == ReviewAction.IGNORE_ALL:
                    # Persistently ignore this word so it never appears again in any book
                    session_ignore_keys.add(key)
                    self.engine.dict_manager.add_ignored(key)
                    self.engine.reload()
                    print(f"{Colors.DIM}🔒 '{key}' adicionado à lista de palavras ignoradas permanentemente (scripts/data/dicionario_ignorado.json).{Colors.ENDC}")
                    history.append((match_idx, None, dict(replace_all_dict), set(session_ignore_keys)))
                    match_idx += 1

                elif action == ReviewAction.EDIT:
                    if chosen_text:
                        final_repl = CasePreserver.preserve_case(match.original_text, chosen_text)
                        repl = (match.start, match.end, final_repl)
                        replacements.append(repl)
                        match.applied_replacement = final_repl
                        history.append((match_idx, repl, dict(replace_all_dict), set(session_ignore_keys)))
                        
                        print(f"Salvar '{key}' -> '{chosen_text.lower()}' no dicionário pessoal permanentemente? [{Colors.GREEN}s{Colors.ENDC}/{Colors.RED}n{Colors.ENDC}]")
                        save_confirm = input("> ").strip().lower()
                        if save_confirm == "s":
                            self.engine.dict_manager.add_entry(key, chosen_text.lower())
                            self.engine.reload()
                            print(f"{Colors.GREEN}✅ Dicionário pessoal atualizado!{Colors.ENDC}")
                    match_idx += 1

        except KeyboardInterrupt:
            print(f"\n\n{Colors.YELLOW}⚠️  Operação interrompida (Ctrl+C).{Colors.ENDC}")
            if replacements:
                print(f"Deseja salvar as {len(replacements)} modificações já realizadas? [{Colors.GREEN}s{Colors.ENDC}/{Colors.RED}n{Colors.ENDC}]")
                try:
                    save_choice = input("> ").strip().lower()
                    if save_choice != "s":
                        print(f"{Colors.YELLOW}Modificações descartadas.{Colors.ENDC}")
                        return result
                except (KeyboardInterrupt, EOFError):
                    print(f"\n{Colors.YELLOW}Operação cancelada. Nenhuma alteração foi salva.{Colors.ENDC}")
                    return result
            else:
                return result

        if not replacements:
            print(f"\n{Colors.YELLOW}Nenhuma substituição foi confirmada.{Colors.ENDC}\n")
            result.total_skipped = total_matches
            if dest_path != src_path:
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src_path, dest_path)
            return result

        # Backup if modifying in-place and requested
        if dest_path == src_path and create_backup:
            backup_file = src_path.with_suffix(src_path.suffix + ".bak")
            shutil.copy2(src_path, backup_file)
            print(f"{Colors.DIM}Backup criado em: {backup_file}{Colors.ENDC}")

        # Apply replacements and write to destination
        updated_content = self.engine.apply_replacements(raw_content, replacements)
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        with open(dest_path, "w", encoding="utf-8") as f:
            f.write(updated_content)

        result.total_replaced = len(replacements)
        result.total_skipped = total_matches - len(replacements)
        result.modified = True

        print(f"\n{Colors.GREEN}{Colors.BOLD}✅ Revisão concluída! {len(replacements)} substituições aplicadas em '{dest_path.name}'.{Colors.ENDC}\n")
        return result

    def _handle_interactive_match(
        self,
        match: ReviewMatch,
        current: int,
        total: int,
    ) -> Tuple[ReviewAction, Optional[str]]:
        """Handles match display, arrow key selection, and definition lookup."""
        suggestions = match.suggestions if match.suggestions else [match.suggested_text]
        selected_idx = 0

        while True:
            # Render match display
            self._display_match_with_cursor(match, current, total, suggestions, selected_idx)

            # Read single keypress
            try:
                key = KeyReader.read_key()
            except KeyboardInterrupt:
                raise

            # 1. Navigation with Arrow keys
            if key in (KeyReader.KEY_UP, KeyReader.KEY_LEFT):
                selected_idx = (selected_idx - 1) % len(suggestions)
                continue
            elif key in (KeyReader.KEY_DOWN, KeyReader.KEY_RIGHT, KeyReader.KEY_TAB):
                selected_idx = (selected_idx + 1) % len(suggestions)
                continue

            # 2. Enter / Space / 's' -> apply selected suggestion
            elif key in (KeyReader.KEY_ENTER, " ", "s", "S"):
                return ReviewAction.REPLACE, suggestions[selected_idx]

            # 3. Direct number keys 1, 2, 3, 4 -> apply specific suggestion
            elif key.isdigit():
                num_idx = int(key) - 1
                if 0 <= num_idx < len(suggestions):
                    return ReviewAction.REPLACE, suggestions[num_idx]
                continue

            # 4. 't' -> replace all with currently selected suggestion
            elif key in ("t", "T"):
                return ReviewAction.REPLACE_ALL, suggestions[selected_idx]

            # 5. 'n' -> skip this match
            elif key in ("n", "N"):
                return ReviewAction.SKIP, None

            # 6. 'i' -> ignore all and save to persistent ignore list
            elif key in ("i", "I"):
                return ReviewAction.IGNORE_ALL, None

            # 7. '?' or 'd' -> Inline dictionary definition lookup
            elif key in ("?", "d", "D"):
                self._show_inline_definition(match.original_text, suggestions[selected_idx])
                continue

            # 8. 'e' -> Custom Edit
            elif key in ("e", "E"):
                print()
                try:
                    custom = input(f"Digite o termo correto para '{match.original_text}': ").strip()
                    if custom:
                        return ReviewAction.EDIT, custom
                    else:
                        print(f"{Colors.YELLOW}Edição cancelada.{Colors.ENDC}")
                        continue
                except EOFError:
                    return ReviewAction.SKIP, None

            # 9. 'u' -> Undo
            elif key in ("u", "U", KeyReader.KEY_BACKSPACE):
                return ReviewAction.UNDO, None

            # 10. 'q' -> Quit
            elif key in ("q", "Q", KeyReader.KEY_ESC):
                return ReviewAction.QUIT, None

    def _display_match_with_cursor(
        self,
        match: ReviewMatch,
        current: int,
        total: int,
        suggestions: List[str],
        selected_idx: int,
    ) -> None:
        """Renders match and interactive suggestions with visual cursor."""
        highlighted = f"{Colors.RED}{Colors.BOLD}{match.original_text}{Colors.ENDC}"
        badge = f"{Colors.CYAN}[Dicionário Curado]{Colors.ENDC}" if match.source == "dictionary" else f"{Colors.MAGENTA}[Hunspell pt_BR]{Colors.ENDC}"

        print("─" * 72)
        print(f"{Colors.BLUE}{Colors.BOLD}[{current}/{total}]{Colors.ENDC} {Colors.CYAN}Linha {match.line_number}:{match.column_number}{Colors.ENDC}  {badge}")
        print(f"{Colors.DIM}Contexto:{Colors.ENDC} ...{match.context_before}{highlighted}{match.context_after}...")

        # Render selectable suggestions
        sugg_boxes = []
        for i, s in enumerate(suggestions[:4]):
            if i == selected_idx:
                sugg_boxes.append(f"{Colors.GREEN}{Colors.BOLD}► [{i+1}] {s} (selecionado){Colors.ENDC}")
            else:
                sugg_boxes.append(f"{Colors.DIM}[{i+1}] {s}{Colors.ENDC}")

        print(f"Sugestões: {'  '.join(sugg_boxes)}")
        current_choice = suggestions[selected_idx]
        print(f"Substituir {highlighted} por {Colors.GREEN}{Colors.BOLD}{current_choice}{Colors.ENDC}?")
        
        # Shortcut bar
        bar = (
            f"Teclas: "
            f"[{Colors.GREEN}Enter/s{Colors.ENDC}] Aplicar ({current_choice}) │ "
            f"[{Colors.GREEN}t{Colors.ENDC}] Todas no livro │ "
            f"[{Colors.CYAN}↑/↓{Colors.ENDC}] Escolher │ "
            f"[{Colors.YELLOW}?{Colors.ENDC}] Dicionário │ "
            f"[{Colors.RED}n{Colors.ENDC}] Pular │ "
            f"[{Colors.RED}i{Colors.ENDC}] Ignorar definitivo │ "
            f"[{Colors.YELLOW}e{Colors.ENDC}] Editar │ "
            f"[{Colors.CYAN}u{Colors.ENDC}] Undo │ "
            f"[{Colors.BLUE}q{Colors.ENDC}] Sair"
        )
        print(f"{bar}")

    def _show_inline_definition(self, original_word: str, target_word: str) -> None:
        """Displays inline dictionary definition panel without losing review state."""
        print(f"\n{Colors.HEADER}{Colors.BOLD}📖 Consultando Dicionário da Língua Portuguesa...{Colors.ENDC}")

        # Lookup target word or original word
        entry = self.def_lookup.get_definition(target_word) or self.def_lookup.get_definition(original_word)

        print(f"\n{Colors.CYAN}{'═' * 65}{Colors.ENDC}")
        if entry:
            word_title = entry.get("word", target_word).capitalize()
            gram_class = entry.get("class", "")
            meaning = entry.get("meaning", "")
            etymology = entry.get("etymology", "")
            notes = entry.get("notes", "")

            print(f"📚 {Colors.BOLD}{word_title}{Colors.ENDC} {Colors.DIM}({gram_class}){Colors.ENDC}")
            if notes:
                print(f"{Colors.YELLOW}ℹ️  {notes}{Colors.ENDC}")
            print(f"\n{meaning}")
            if etymology:
                print(f"\n{Colors.DIM}{etymology}{Colors.ENDC}")
        else:
            print(f"{Colors.YELLOW}Nenhuma definição encontrada nos verbetes para '{target_word}' ou '{original_word}'.{Colors.ENDC}")

        print(f"{Colors.CYAN}{'═' * 65}{Colors.ENDC}")
        print(f"{Colors.DIM}Pressione qualquer tecla para retornar à revisão...{Colors.ENDC}")
        KeyReader.read_key()
        print()
