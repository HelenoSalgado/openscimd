"""Módulo para delegação e execução remota de OCR e extração pesada no Google Colab.

Utiliza a CLI oficial `google-colab-cli` e o `mineru-kit` puro com aceleração por GPU (Google AI Pro).
Todo o transporte de dados (PDF e resultados) é estritamente comprimido em .tar.gz.
Apenas os artefatos essenciais (.md, .json e imagens) são transferidos de volta.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import tarfile
import tempfile
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

DEFAULT_SESSION = os.getenv("COLAB_SESSION_NAME", "openscimd-worker")
DEFAULT_GPU = os.getenv("COLAB_GPU_TYPE", "T4")
DEFAULT_AUTO_STOP = os.getenv("COLAB_AUTO_STOP", "true").lower() in ("true", "1", "yes")


class ColabRunnerError(Exception):
    """Exceção customizada para erros na execução remota do Colab."""


def check_colab_cli() -> None:
    """Verifica se o comando `colab` está instalado e acessível no sistema."""
    if not shutil.which("colab"):
        raise ColabRunnerError(
            "O comando 'colab' não foi encontrado no PATH. Instale com: uv tool install google-colab-cli"
        )


def run_cmd(
    cmd: list[str], check: bool = True, capture_output: bool = True, timeout: int | None = None
) -> subprocess.CompletedProcess[str]:
    """Executa comando em subprocesso com tratamento padronizado."""
    try:
        return subprocess.run(
            cmd,
            check=check,
            capture_output=capture_output,
            text=True,
            timeout=timeout,
        )
    except subprocess.CalledProcessError as err:
        stderr_msg = err.stderr.strip() if err.stderr else ""
        stdout_msg = err.stdout.strip() if err.stdout else ""
        raise ColabRunnerError(
            f"Falha ao executar {' '.join(cmd)} (código {err.returncode}):\n{stderr_msg or stdout_msg}"
        ) from err


def is_session_active(session_name: str) -> bool:
    """Verifica se a sessão informada já está ativa no Google Colab."""
    res = run_cmd(["colab", "status", "-s", session_name], check=False)
    if res.returncode != 0:
        return False
    output = (res.stdout + res.stderr).lower()
    return "not found" not in output and "error" not in output


def ensure_session(session_name: str = DEFAULT_SESSION, gpu_type: str = DEFAULT_GPU) -> None:
    """Garante que a sessão remota no Colab esteja criada e ativa com a GPU especificada."""
    check_colab_cli()
    if is_session_active(session_name):
        return

    print(f"[*] Provisionando nova VM efêmera no Google Colab com GPU {gpu_type} (Sessão: {session_name})...")
    res = run_cmd(
        ["colab", "new", "--gpu", gpu_type, "-s", session_name],
        check=False,
        timeout=180,
    )
    if res.returncode != 0:
        raise ColabRunnerError(
            f"Erro ao provisionar sessão no Colab. Certifique-se de estar autenticado com 'colab auth login'.\n"
            f"Detalhes: {res.stderr or res.stdout}"
        )
    print(f"[+] Sessão '{session_name}' provisionada com sucesso.")


def stop_session(session_name: str = DEFAULT_SESSION) -> None:
    """Encerra a sessão do Colab para liberar os recursos e créditos."""
    print(f"[*] Encerrando sessão '{session_name}' no Google Colab...")
    run_cmd(["colab", "stop", "-s", session_name], check=False)
    print(f"[+] Sessão '{session_name}' finalizada.")


def package_file(file_path: Path, temp_dir: Path) -> Path:
    """Compacta o arquivo PDF em um pacote .tar.gz para economia de banda."""
    if not file_path.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {file_path}")

    tar_path = temp_dir / f"{file_path.stem}_input.tar.gz"
    with tarfile.open(tar_path, "w:gz") as tar:
        tar.add(file_path, arcname=file_path.name)
    return tar_path


def execute_remote_extraction(
    pdf_path: Path,
    output_dir: Path,
    session_name: str = DEFAULT_SESSION,
    gpu_type: str = DEFAULT_GPU,
    lang: str = "latin",
    keep_alive: bool = False,
) -> Path:
    """Orquestra a extração remota completa com compressão de tráfego e aceleração de GPU."""
    ensure_session(session_name=session_name, gpu_type=gpu_type)

    with tempfile.TemporaryDirectory() as tmp_str:
        tmp_dir = Path(tmp_str)
        pdf_tar = package_file(pdf_path, tmp_dir)

        print(f"[*] Enviando PDF compactado ({pdf_tar.stat().st_size // 1024} KB) para a VM remota...")
        run_cmd(["colab", "upload", "-s", session_name, str(pdf_tar), "/content/input_bundle.tar.gz"])

        # Script remoto de execução com mineru-kit puro
        bootstrap_script = f"""set -e
mkdir -p /content/work_input /content/raw_output /content/clean_output

# 1. Descompactar o PDF
tar -xzf /content/input_bundle.tar.gz -C /content/work_input

# 2. Garantir instalação do mineru
which mineru-kit >/dev/null 2>&1 || pip install -q mineru

# 3. Execução do MinerU puro com aceleração GPU
echo "[*] Disparando mineru-kit na GPU..."
mineru-kit parse "/content/work_input/{pdf_path.name}" -o /content/raw_output --pages all --format markdown

# 4. Filtrar estritamente o essencial (.md, .json e imagens, excluindo layouts em PDF)
cd /content/raw_output
find . -type f \\( -name "*.md" -o -name "*.json" \\) -exec cp --parents {{}} /content/clean_output/ \\;
find . -type d -name "images" -exec cp -r --parents {{}} /content/clean_output/ \\; 2>/dev/null || true

# 5. Compactar apenas os artefatos limpos
cd /content/clean_output
tar -czf /content/output_bundle.tar.gz *
"""

        print("[*] Executando extração pura com MinerU na GPU do Colab (aguarde alguns instantes)...")
        script_path = tmp_dir / "remote_job.sh"
        script_path.write_text(bootstrap_script, encoding="utf-8")
        run_cmd(["colab", "upload", "-s", session_name, str(script_path), "/content/remote_job.sh"])

        # Executa no Colab com SSH
        run_cmd(
            ["colab", "ssh", "-s", session_name, "--", "bash", "/content/remote_job.sh"],
            capture_output=False,
            timeout=1800,
        )

        print("[*] Baixando artefatos essenciais compactados da VM remota...")
        local_output_tar = tmp_dir / "output_bundle.tar.gz"
        run_cmd(["colab", "download", "-s", session_name, "/content/output_bundle.tar.gz", str(local_output_tar)])

        # Descompactar na pasta de saída local (data/draft/)
        output_dir.mkdir(parents=True, exist_ok=True)
        print(f"[*] Descompactando resultado limpo em: {output_dir}")
        with tarfile.open(local_output_tar, "r:gz") as tar:
            tar.extractall(path=output_dir)

    # Gerenciamento de ciclo de vida
    if not keep_alive and DEFAULT_AUTO_STOP:
        stop_session(session_name)
    else:
        print(f"[i] Sessão '{session_name}' mantida ativa (--keep-alive).")

    # Localizar o arquivo Markdown gerado
    md_candidates = list(output_dir.glob(f"**/{pdf_path.stem}.md"))
    if not md_candidates:
        md_candidates = [f for f in output_dir.glob("**/*.md") if pdf_path.stem.lower() in f.stem.lower()]

    if not md_candidates:
        raise ColabRunnerError(
            f"O arquivo Markdown esperado para '{pdf_path.stem}' não foi encontrado em {output_dir}. "
            "A inferência pode ter falhado na VM remota."
        )

    target_md = md_candidates[0]
    print(f"✅ Extração remota com MinerU puro concluída com sucesso: {target_md}")
    return target_md
