import requests
import re
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

# Configurações de Performance
BASE_URL = "https://fenix.tecnico.ulisboa.pt/api/fenix/v1"
ANO = "2025/2026"
OUTPUT_FILE = "planeamento_ist_detalhado_2026.csv"
MAX_THREADS = 25 

session = requests.Session()

def limpar_texto(texto):
    """Remove quebras de linha e limpa vírgulas para não corromper o CSV."""
    if not texto: return ""
    # Remove tags HTML se existirem, substitui novas linhas por espaço e limpa vírgulas
    texto_limpo = re.sub('<[^<]+?>', '', texto)
    return texto_limpo.replace('\n', ' ').replace('\r', ' ').replace(',', ';').strip()

def get_json(endpoint, params=None):
    try:
        r = session.get(f"{BASE_URL}/{endpoint}", params=params, timeout=15)
        return r.json() if r.status_code == 200 else None
    except: return None

def processar_detalhes_uc(uc_info):
    uc_id = uc_info['id']
    dados_base = get_json(f"courses/{uc_id}")
    if not dados_base: return None
    
    # Extração das novas colunas solicitadas
    metodo_avaliacao = limpar_texto(dados_base.get('evaluationMethod', ''))
    programa = limpar_texto(dados_base.get('program', ''))
    
    url = dados_base.get('url', '')
    alunos = dados_base.get('numberOfAttendingStudents', '0')
    profs = " | ".join([t.get('name', '') for t in dados_base.get('teachers', [])]).replace(",", ";")
    
    # Lógica de Período (P3, P4 ou Semestral)
    horario = get_json(f"courses/{uc_id}/schedule")
    periodo = "2º Semestre"
    if horario:
        datas_aulas = []
        for shift in horario.get('shifts', []):
            for lesson in shift.get('lessons', []):
                l_start = lesson.get('start', '')
                if l_start:
                    try:
                        datas_aulas.append(datetime.strptime(l_start.split(' ')[0], '%Y-%m-%d'))
                    except: continue
        if datas_aulas:
            d_min, d_max = min(datas_aulas), max(datas_aulas)
            divisor = datetime(2026, 4, 10)
            if d_min < divisor and d_max > divisor: periodo = "Semestral"
            elif d_max <= divisor: periodo = "P3"
            else: periodo = "P4"

    return {
        "curso_ref": uc_info['curso_ref'],
        "id": uc_id,
        "nome": uc_info['name'].replace(",", ";"),
        "ects": uc_info.get('credits', '0'),
        "periodo": periodo,
        "metodo_avaliacao": metodo_avaliacao,
        "programa": programa,
        "num_alunos": alunos,
        "docentes": profs,
        "url": url
    }

def main():
    print(f"[*] A iniciar extração profunda (com Programa e Avaliação) para {ANO}...")
    
    dados_degrees = get_json("degrees", {"academicTerm": ANO})
    if not dados_degrees: return

    cursos_alvo = [d for d in dados_degrees if "Alameda" in str(d.get('campus', '')) and "Bachelor" not in str(d.get('typeName', ''))]
    
    todas_ucs_meta = []
    for curso in cursos_alvo:
        cadeiras = get_json(f"degrees/{curso['id']}/courses", {"academicTerm": ANO})
        if cadeiras:
            for c in cadeiras:
                if "2" in str(c.get('academicTerm', '')):
                    todas_ucs_meta.append({
                        'id': c['id'], 
                        'name': c['name'], 
                        'credits': c.get('credits', '0'), 
                        'curso_ref': curso['acronym']
                    })

    print(f"[*] A processar {len(todas_ucs_meta)} entradas...")
    
    with open(OUTPUT_FILE, "w", encoding="utf-8-sig") as f:
        # Cabeçalho atualizado
        f.write("sigla_curso_ref,id_cadeira,nome_cadeira,ects,periodo,metodo_avaliacao,programa,num_alunos,docentes,url_curso\n")
        
        with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
            resultados = list(executor.map(processar_detalhes_uc, todas_ucs_meta))
            
            for res in resultados:
                if res:
                    linha = f"{res['curso_ref']},{res['id']},{res['nome']},{res['ects']},{res['periodo']},{res['metodo_avaliacao']},{res['programa']},{res['num_alunos']},{res['docentes']},{res['url']}\n"
                    f.write(linha)

    print(f"\n[OK] Extração completa! Ficheiro: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()