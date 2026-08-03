import sys
import re

def to_superscript(num_str):
    """Converte uma string de números para seus equivalentes sobrescritos."""
    superscript_map = str.maketrans("0123456789", "⁰¹²³⁴⁵⁶⁷⁸⁹")
    return num_str.translate(superscript_map)

def process_file(input_path, output_path):
    """Lê o arquivo de entrada, converte números no início de linha e escreve na saída."""
    with open(input_path, 'r', encoding='utf-8') as f_in:
        lines = f_in.readlines()
        
    with open(output_path, 'w', encoding='utf-8') as f_out:
        for line in lines:
            # Procura por números no início da linha, opcionalmente seguidos por um ponto e espaços
            match = re.match(r'^(\d+)\.\s*(.*)', line)
            if match:
                num_str = match.group(1)
                rest_of_line = match.group(2)
                super_num = to_superscript(num_str)
                # Escreve o número sobrescrito seguido do resto da linha
                f_out.write(f"{super_num} {rest_of_line}\n")
            else:
                f_out.write(line)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Uso: python converter_versiculos.py <arquivo_entrada> <arquivo_saida>")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    print(f"Lendo de: {input_file}")
    process_file(input_file, output_file)
    print(f"Conversão concluída. Escrito em: {output_file}")
