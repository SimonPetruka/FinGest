import csv
import hashlib
from datetime import datetime
import database

# =============================================================================
# GESTION IMPORT CSV
# =============================================================================

def generate_fingerprint(date, amount, label):
    """Crée une signature unique pour éviter les doublons."""
    raw = f"{date}{amount}{label}".strip().upper()
    return hashlib.md5(raw.encode('utf-8')).hexdigest()

def clean_amount(amount_str):
    """Transforme '1 200,50' ou '-12.50' en float."""
    # On remplace la virgule par un point
    clean = amount_str.replace(',', '.')
    # On enlève les espaces insécables ou normaux
    clean = clean.replace(' ', '').replace('\xa0', '')
    try:
        return float(clean)
    except ValueError:
        return None

def parse_date(date_str):
    """Tente de comprendre plusieurs formats de date bancaires."""
    formats = [
        '%d/%m/%Y',   # 25/12/2023
        '%Y-%m-%d',   # 2023-12-25
        '%d-%m-%Y',   # 25-12-2023
        '%d/%m/%y'    # 25/12/23
    ]
    for fmt in formats:
        try:
            dt = datetime.strptime(date_str, fmt)
            return dt.strftime('%Y-%m-%d') # Format standard SQL
        except ValueError:
            continue
    return None

def import_csv_file(file_path):
    added_count = 0
    duplicate_count = 0
    errors = 0
    
    # Charger les règles en mémoire une seule fois (Optimisation)
    rules = database.get_rules()

    try:
        # Détection automatique du séparateur (virgule ou point-virgule)
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            first_line = f.readline()
            dialect = csv.Sniffer().sniff(first_line)
            f.seek(0)
            
            reader = csv.reader(f, dialect)
            
            # On saute l'en-tête
            try:
                header = next(reader)
            except StopIteration:
                return False, "Fichier vide."

            for row in reader:
                if not row: continue # Ligne vide
                
                # Adaptation selon les colonnes de ton CSV
                # On suppose l'ordre standard : Date ; Libellé ; Montant
                # Si ton fichier est différent, change les indices [0], [1], [2]
                if len(row) < 3:
                    errors += 1
                    continue
                
                raw_date = row[0]
                raw_label = row[1]
                raw_amount = row[2]
                
                final_date = parse_date(raw_date)
                final_amount = clean_amount(raw_amount)
                final_label = raw_label.strip()

                if not final_date or final_amount is None:
                    errors += 1
                    continue

                # 1. Génération de l'empreinte unique
                fingerprint = generate_fingerprint(final_date, final_amount, final_label)

                # 2. Vérification doublon (CORRIGÉ ICI)
                if database.transaction_exists(fingerprint):
                    duplicate_count += 1
                    continue

                # 3. Application des règles (Auto-catégorisation)
                category = None
                label_upper = final_label.upper()
                
                # On cherche si un mot-clé est dans le libellé
                for keyword, cat in rules.items():
                    if keyword in label_upper:
                        category = cat
                        break
                
                # 4. Ajout en base
                database.add_transaction(
                    date=final_date,
                    label=final_label,
                    amount=final_amount,
                    category=category,
                    fingerprint=fingerprint
                )
                added_count += 1

        msg = f"Import terminé !\n✅ Ajoutés : {added_count}\n♻️ Doublons ignorés : {duplicate_count}\n⚠️ Erreurs format : {errors}"
        return True, msg

    except Exception as e:
        return False, f"Erreur critique lors de l'import : {str(e)}"

# =============================================================================
# MATHS & PRÉVISIONS
# =============================================================================

def calculate_trend(values):
    """
    Calcule une régression linéaire simple (Moindres Carrés).
    Entrée : Liste de valeurs [y1, y2, y3...] (ex: soldes des mois passés)
    Sortie : Liste des 3 prochaines valeurs prévues.
    """
    n = len(values)
    if n < 2:
        return [0, 0, 0] # Pas assez de données

    # X = [0, 1, 2...] (Les mois)
    x = list(range(n))
    y = values

    # Moyennes
    mean_x = sum(x) / n
    mean_y = sum(y) / n

    # Calcul pente (a) et ordonnée à l'origine (b) -> y = ax + b
    numerator = sum((xi - mean_x) * (yi - mean_y) for xi, yi in zip(x, y))
    denominator = sum((xi - mean_x) ** 2 for xi in x)

    if denominator == 0:
        slope = 0
    else:
        slope = numerator / denominator

    intercept = mean_y - (slope * mean_x)

    # Prévision pour n+1, n+2, n+3
    predictions = []
    for i in range(1, 4):
        next_x = n - 1 + i # On continue l'échelle de temps
        pred_y = (slope * next_x) + intercept
        predictions.append(pred_y)

    return predictions