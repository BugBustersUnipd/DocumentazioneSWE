import re

def sort_glossary(file_path):
    # Leggi il file
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Pattern per catturare una sezione completa (lettera)
    section_pattern = re.compile(r'(\\section\{([A-Z])\}.*?)(?=\\section\{|\Z)', re.DOTALL)
    
    # Trova tutte le sezioni
    sections = section_pattern.findall(content)
    
    if not sections:
        print("Nessuna sezione trovata")
        return content
    
    # Ordina le sezioni in base alla lettera
    sections_sorted = sorted(sections, key=lambda x: x[1])  # x[1] è la lettera
    
    # Per ogni sezione, ordina le sottosezioni
    sorted_sections_content = []
    
    for section_content, section_letter in sections_sorted:
        # Pattern per catturare le sottosezioni all'interno di una sezione
        subsection_pattern = re.compile(r'(\\subsection\{.*?\}.*?)(?=\\subsection\{|$)', re.DOTALL)
        
        # Trova tutte le sottosezioni
        subsections = subsection_pattern.findall(section_content)
        
        if subsections:
            # Estrai i nomi delle sottosezioni per l'ordinamento
            subsection_names = []
            for sub in subsections:
                # Estrai il nome dalla sottosezione
                name_match = re.search(r'\\subsection\{(.*?)\}', sub)
                if name_match:
                    subsection_names.append((name_match.group(1), sub))
            
            # Ordina le sottosezioni in base al nome
            subsection_names_sorted = sorted(subsection_names, key=lambda x: x[0].lower())
            
            # Ricostruisci la sezione con le sottosezioni ordinate
            sorted_subsections = [sub for _, sub in subsection_names_sorted]
            sorted_section = f"\\section{{{section_letter}}}\n\n" + "\n".join(sorted_subsections)
            sorted_sections_content.append(sorted_section)
        else:
            sorted_sections_content.append(section_content)
    
    # Separa il contenuto prima e dopo le sezioni
    first_section_match = re.search(r'\\section\{', content)
    if first_section_match:
        start_idx = first_section_match.start()
        preamble = content[:start_idx]
        # Il resto è già stato processato
    else:
        preamble = content
        return content
    
    # Ricostruisci il contenuto
    new_content = preamble + "\n\n".join(sorted_sections_content)
    
    return new_content

def main():
    input_file = "Glossario.tex"
    output_file = "Glossario_ordinato.tex"
    
    try:
        sorted_content = sort_glossary(input_file)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(sorted_content)
        
        print(f"Glossario ordinato salvato in: {output_file}")
        
        # Controlla se ci sono duplicati
        with open(output_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Cerca duplicati nelle sottosezioni
        subsection_pattern = re.compile(r'\\subsection\{(.*?)\}', re.DOTALL)
        all_subsections = subsection_pattern.findall(content)
        
        duplicates = {}
        for subsection in all_subsections:
            duplicates[subsection] = duplicates.get(subsubsection, 0) + 1
        
        dup_found = False
        for subsection, count in duplicates.items():
            if count > 1:
                print(f"Attenzione: '{subsection}' appare {count} volte")
                dup_found = True
        
        if not dup_found:
            print("Nessun duplicato trovato.")
            
    except FileNotFoundError:
        print(f"Errore: File '{input_file}' non trovato.")
    except Exception as e:
        print(f"Errore durante l'elaborazione: {str(e)}")

if __name__ == "__main__":
    main()