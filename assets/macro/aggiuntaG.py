# Aggiunge \G{} subito dopo i termini del glossario.
# Versione migliorata che:
# - Gestisce sia termini singoli che multi-parola
# - Rimuove contenuto tra parentesi dai termini
# - Evita duplicazioni
# - Gestisce plurali base (aggiunta di 's')

import json
import re
import sys
from pathlib import Path

def load_glossary_terms(glossary_path):
    """Carica i termini dal glossario JSON"""
    with open(glossary_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    terms = []
    if isinstance(data, dict) and "terms" in data:
        for entry in data["terms"]:
            if isinstance(entry, dict) and "term" in entry:
                terms.append(entry["term"])
    elif isinstance(data, list):
        for entry in data:
            if isinstance(entry, dict) and "term" in entry:
                terms.append(entry["term"])
    return terms

def clean_term(term):
    """Rimuove parentesi e contenuto tra parentesi dal termine"""
    # "AI (Artificial Intelligence)" -> "AI"
    cleaned = re.sub(r'\s*\([^)]*\)', '', term).strip()
    return cleaned

def add_G_suffix(tex_text, glossary_terms):
    """Aggiunge \G dopo ogni occorrenza dei termini del glossario"""
    
    # Prepara i termini puliti
    processed_terms = []
    for term in glossary_terms:
        if not term or term.strip() == "":
            continue
        clean = clean_term(term)
        if clean:
            processed_terms.append(clean)
    
    # Rimuovi duplicati e ordina per lunghezza decrescente
    # (i termini più lunghi devono essere processati prima per evitare conflitti)
    processed_terms = sorted(set(processed_terms), key=lambda s: len(s), reverse=True)
    
    print(f"🔍 Processando {len(processed_terms)} termini unici...")
    
    modifiche = 0
    
    for term in processed_terms:
        # Escape caratteri speciali per regex
        base = re.escape(term)
        
        # Pattern che matcha:
        # - Il termine esatto (case-insensitive)
        # - Con opzionale 's' alla fine per plurali semplici
        # - Come parola completa (\b = word boundary)
        # - NON già seguito da \G{}
        pattern = re.compile(
            rf'\b({base})s?\b(?!\s*\\G\{{\}})',
            flags=re.IGNORECASE
        )
        
        matches = list(pattern.finditer(tex_text))
        
        if matches:
            # Processa i match dall'ultimo al primo per non invalidare gli indici
            for match in reversed(matches):
                matched_text = match.group(0)
                start_pos = match.start()
                end_pos = match.end()
                
                # Controlla contesto prima del match
                before_context = tex_text[max(0, start_pos-20):start_pos]
                
                # Controlla contesto dopo il match
                after_context = tex_text[end_pos:min(len(tex_text), end_pos+10)]
                
                # Salta se già c'è \G{} nelle immediate vicinanze
                if '\\G{' in before_context[-10:] or '\\G{' in after_context[:5]:
                    continue
                
                # Salta se siamo dentro un comando LaTeX tipo \newcommand, \def, ecc.
                if re.search(r'\\[a-zA-Z]+\s*{[^}]*$', before_context):
                    continue
                
                # Salta se siamo in un URL o path
                if re.search(r'(https?://|\\url\{|\\path\{)[^\s}]*$', before_context):
                    continue
                
                # Inserisci \G{} subito dopo il termine
                tex_text = tex_text[:end_pos] + r'\G{}' + tex_text[end_pos:]
                modifiche += 1
    
    print(f"✅ Aggiunti {modifiche} marcatori \\G{{}}")
    return tex_text

def main():
    # Percorso fisso per il glossario
    glossary_path = Path(__file__).parent.parent.parent / "SITO" / "glossario.json"
    
    if not glossary_path.exists():
        print("❌ Errore: glossario non trovato al percorso:", glossary_path)
        sys.exit(1)
    
    # Chiedi all'utente quale file modificare
    print("=" * 60)
    print("📖 Script per aggiungere \\G{{}} ai termini del glossario")
    print("=" * 60)
    print(f"📚 Glossario: {glossary_path.name}")
    print()
    
    while True:
        tex_file = input("📄 Inserisci il percorso del file .tex (relativo alla radice): ").strip()
        if not tex_file:
            print("❌ Percorso vuoto. Riprova.")
            continue
            
        # Se il percorso è relativo, assumi che sia relativo alla radice del progetto
        if not Path(tex_file).is_absolute():
            tex_path = Path(__file__).parent.parent.parent / tex_file
        else:
            tex_path = Path(tex_file)
            
        if not tex_path.exists():
            print(f"❌ File non trovato: {tex_path}")
            print("💡 Esempi di percorsi validi:")
            print("   RTB/NORME DI PROGETTO/Norme di Progetto.tex")
            print("   RTB/VERBALI/INTERNI/VI_12-11-25/VI_12-11-25.tex")
            continue
            
        if tex_path.suffix.lower() != '.tex':
            print("❌ Il file deve avere estensione .tex")
            continue
            
        break
    
    print(f"\n📄 File selezionato: {tex_path.relative_to(tex_path.parent.parent.parent)}")
    
    # Conferma
    print()
    conferma = input("⚠️  Vuoi procedere con la modifica? (s/N): ").strip().lower()
    if conferma not in ['s', 'si', 'sì', 'y', 'yes']:
        print("❌ Operazione annullata.")
        return
    
    print("\n" + "=" * 60)
    
    # Carica e processa
    try:
        print("📖 Lettura file...")
        tex_text = tex_path.read_text(encoding="utf-8")
        original_G_count = tex_text.count('\\G{}')
        
        print("📚 Caricamento glossario...")
        terms = load_glossary_terms(glossary_path)
        print(f"✅ Caricati {len(terms)} termini dal glossario")
        
        print("\n🔄 Elaborazione in corso...")
        updated = add_G_suffix(tex_text, terms)
        
        # Conta le modifiche effettive
        new_G_count = updated.count('\\G{}')
        modifiche = new_G_count - original_G_count
        
        if modifiche > 0:
            # Salva il file
            tex_path.write_text(updated, encoding="utf-8")
            print(f"\n✅ File modificato con successo!")
            print(f"📊 Marcatori \\G{{}} prima: {original_G_count}")
            print(f"📊 Marcatori \\G{{}} dopo: {new_G_count}")
            print(f"📊 Nuovi marcatori: {modifiche}")
        else:
            print("\n✅ Nessuna modifica necessaria (tutti i termini sono già marcati)")
        
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Errore durante l'elaborazione: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
