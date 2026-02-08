import json

# Carica il file JSON
with open('glossario.json', 'r', encoding='utf-8') as file:
    data = json.load(file)

# Ordina i termini in modo case-insensitive (ignora maiuscole/minuscole)
data['terms'] = sorted(data['terms'], key=lambda x: x['term'].lower())

# Salva il file JSON ordinato
with open('glossario_ordinato.json', 'w', encoding='utf-8') as file:
    json.dump(data, file, ensure_ascii=False, indent=2)

print("Glossario ordinato e salvato come 'glossario_ordinato.json'")