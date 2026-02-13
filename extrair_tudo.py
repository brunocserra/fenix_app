import requests
from concurrent.futures import ThreadPoolExecutor

BASE_URL = "https://fenix.tecnico.ulisboa.pt/api/fenix/v1"
ANO = "2024/2025"
OUTPUT_FILE = "todos_mestrados_ist_p3.csv"

def get_json(endpoint, params=None):
    try:
        r = requests.get(f"{BASE_URL}/{endpoint}", params=params, timeout=15)
        return r.json() if r.status_code == 200 else None
    except: return None

def processar_curso(curso):
    sigla = curso.get('acronym', 'N/A')
    c_id = curso.get('id')
    nome_curso = curso.get('name', 'N/A')
    res_list = []
    
    cadeiras = get_json(f"degrees/{c_id}/courses", {"academicTerm": ANO})
    
    if cadeiras:
        for cad in cadeiras:
            term = cad.get('academicTerm', 'N/A')
            # Filtro para manter o ficheiro focado no 2º Semestre/P3
            if "2º Semestre" in term or "2º semestre" in term:
                nome_cad = cad.get('name', 'N/A').replace("'", "").replace(",", ";")
                # Formatação: pelicas e vírgulas
                linha = f"'{nome_curso}','{sigla}','{cad.get('id')}','{nome_cad}','{cad.get('credits','0')}','{term}'"
                res_list.append(linha)
    return res_list

def main():
    print(f"[*] A obter graus para {ANO}...")
    dados = get_json("degrees", {"academicTerm": ANO})
    
    if not dados:
        print("[!] Erro: API offline.")
        return

    mestrados = [d for d in dados if "Alameda" in str(d.get('campus', '')) and "Bachelor" not in str(d.get('typeName', ''))]

    print(f"[*] A processar {len(mestrados)} cursos...")

    # O segredo para o Excel está no encoding='utf-8-sig'
    with open(OUTPUT_FILE, "w", encoding="utf-8-sig") as f:
        f.write("'nome_curso','sigla','id_cadeira','nome_cadeira','ects','periodo'\n")
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            for lista in executor.map(processar_curso, mestrados):
                if lista:
                    for linha in lista:
                        f.write(linha + "\n")
                        f.flush()

    print(f"\n[OK] Ficheiro gerado com acentos corrigidos: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()