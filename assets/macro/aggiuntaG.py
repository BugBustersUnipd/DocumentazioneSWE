# Aggiunge \G (senza parentesi) subito dopo i termini del glossario.
# - legge glossario come lista di {"term": "...", "definition": "..."} partendo dal Json
# - chiede all'utente il file .tex da modificare
# - case-insensitive
# - tenta di coprire singolare/plurale e piccole variazioni di finale
# - non duplica se \G è già presente vicino al termine

import json
import re
import sys
from pathlib import Path

def load_glossary_terms(glossary_path):
    with open(glossary_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    terms = []
    if isinstance(data, dict) and "terms" in data:
        # Il glossario ha una chiave "terms" con l'array
        for entry in data["terms"]:
            if isinstance(entry, dict) and "term" in entry:
                terms.append(entry["term"])
    elif isinstance(data, list):
        # Fallback: se è direttamente una lista
        for entry in data:
            if isinstance(entry, dict) and "term" in entry:
                terms.append(entry["term"])
    return terms

def add_G_suffix(tex_text, glossary_terms):
    # Ordiniamo i termini per lunghezza decrescente per evitare sovrapposizioni ("rete" vs "reti locali")
    glossary_terms = sorted(glossary_terms, key=lambda s: len(s), reverse=True)

    for term in glossary_terms:
        if not term or term.strip() == "":
            continue
        
        # Salta i termini che non contengono spazi (sono parole singole)
        if ' ' not in term:
            continue
            
        base = re.escape(term)

        # Pattern: term come parola completa (supporta anche termini multi-parola).
        # Accettiamo vincoli di confine parola o apostrofo prima/dopo per casi come "l'aggregazione".
        pattern = re.compile(
            rf"(?<!\\G)(?:(?<=\b)|(?<=['’]))({base}(?:[aeiou]?[sx]?)?)(?:(?=\b)|(?=['’]))",
            flags=re.IGNORECASE
        )

        def repl(m):
            start, end = m.start(1), m.end(1)
            # Controllo contestuale nella stringa corrente per evitare duplicazioni:
            # se subito dopo il match (con eventuali spazi corti) c'è già \G => non fare nulla
            after_segment = tex_text[end:end+6]  # 6 è sufficiente per rilevare "\G"
            if re.match(r'^\s*\\G', after_segment):
                return m.group(0)  # già presente, salta

            # se appena prima (fino a qualche carattere) c'è \G{ ... } che include il termine, salta
            before_segment = tex_text[max(0, start-10):start]
            if "\\G" in before_segment:
                # se troviamo '\G' molto vicino a sinistra, assumiamo che il termine sia già marcato
                return m.group(0)

            # altrimenti aggiungi \G subito dopo il termine (senza spazi)
            return m.group(0) + r'\G'

        # Usiamo sub su tex_text aggiornandolo ogni volta (attenzione agli offset già gestiti da re.sub)
        tex_text = pattern.sub(repl, tex_text)

    return tex_text

def main():
    # Percorso fisso per il glossario
    glossary_path = Path(__file__).parent.parent.parent / "SITO" / "glossario.json"
    
    if not glossary_path.exists():
        print("❌ Errore: glossario non trovato al percorso:", glossary_path)
        sys.exit(1)
    
    # Chiedi all'utente quale file modificare
    print("📖 Script per aggiungere \\G ai termini del glossario")
    print(f"📚 Glossario caricato da: {glossary_path}")
    print()
    
    while True:
        tex_file = input("Inserisci il percorso del file .tex da modificare (relativo alla radice del progetto): ").strip()
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
            print("   CANDIDATURA/SCELTA CAPITOLATO/Resoconto_capitolati.tex")
            continue
            
        if tex_path.suffix.lower() != '.tex':
            print("❌ Il file deve avere estensione .tex")
            continue
            
        break
    
    print(f"📄 File selezionato: {tex_path}")
    
    # Conferma
    conferma = input("⚠️  Vuoi procedere con la modifica del file? (s/N): ").strip().lower()
    if conferma not in ['s', 'si', 'sì', 'y', 'yes']:
        print("❌ Operazione annullata.")
        return
    
    # Carica e processa
    try:
        tex_text = tex_path.read_text(encoding="utf-8")
        terms = load_glossary_terms(glossary_path)
        
        print(f"🔍 Trovati {len(terms)} termini nel glossario")
        
        updated = add_G_suffix(tex_text, terms)
        
        # Conta le modifiche
        modifiche = updated.count('\\G') - tex_text.count('\\G')
        
        # Salva il file
        tex_path.write_text(updated, encoding="utf-8")
        
        print("✅ Modifiche completate!")
        print(f"📊 Aggiunti {modifiche} marcatori \\G")
        print(f"💾 File salvato: {tex_path}")
        
    except Exception as e:
        print(f"❌ Errore durante l'elaborazione: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
