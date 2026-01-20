import sqlite3
from datetime import datetime

DB_NAME = "ecogest.db"

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    migrate_db()

def migrate_db():
    """Initialise la DB et injecte un PACK MASSIF de règles intelligentes."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # 1. Création tables principales
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT,
        label TEXT,
        amount REAL,
        category TEXT,
        status TEXT DEFAULT 'A_TRAITER',
        note TEXT DEFAULT '',
        fingerprint TEXT UNIQUE
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS rules (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        keyword TEXT UNIQUE,
        category TEXT
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS budgets (
        category TEXT PRIMARY KEY,
        amount REAL
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL
    )
    ''')
    
    # 2. Catégories par défaut
    defaults = [
        "Alimentation", "Transport", "Logement", "Abonnements", 
        "Loisirs", "Santé", "Revenus", "Autre", "Shopping", 
        "Restaurant", "Banque & Frais", "Impôts & Taxes", "Sport", 
        "Vacances", "Cadeaux", "Animaux", "Enfants"
    ]
    for cat in defaults:
        cursor.execute("INSERT OR IGNORE INTO categories (name) VALUES (?)", (cat,))
    
    # Récupérer les catégories existantes des transactions pour ne pas les perdre
    cursor.execute('INSERT OR IGNORE INTO categories (name) SELECT DISTINCT category FROM transactions WHERE category IS NOT NULL')
    
    # --- 3. LE PACK ULTIME DE RÈGLES (200+ Règles) ---
    smart_rules = [
        # --- ALIMENTATION (Supermarchés & Épicerie) ---
        ("CARREFOUR", "Alimentation"), ("LECLERC", "Alimentation"), 
        ("AUCHAN", "Alimentation"), ("LIDL", "Alimentation"), 
        ("INTERMARCHE", "Alimentation"), ("MONOPRIX", "Alimentation"), 
        ("FRANPRIX", "Alimentation"), ("ALDI", "Alimentation"),
        ("PICARD", "Alimentation"), ("GRAND FRAIS", "Alimentation"),
        ("SYSTEME U", "Alimentation"), ("SUPER U", "Alimentation"),
        ("HYPER U", "Alimentation"), ("CORA", "Alimentation"),
        ("CASINO", "Alimentation"), ("GEANT", "Alimentation"),
        ("BIOCOOP", "Alimentation"), ("NATURALIA", "Alimentation"),
        ("CHRONODRIVE", "Alimentation"), ("BOULANGERIE", "Alimentation"),
        ("PATISSERIE", "Alimentation"), ("BOUCHERIE", "Alimentation"),
        ("POISSONNERIE", "Alimentation"), ("MARCHE", "Alimentation"),
        
        # --- RESTAURANT & FAST FOOD ---
        ("MCDONALDS", "Restaurant"), ("MC DO", "Restaurant"),
        ("BURGER KING", "Restaurant"), ("KFC", "Restaurant"), 
        ("QUICK", "Restaurant"), ("DOMINOS", "Restaurant"), 
        ("PIZZA HUT", "Restaurant"), ("SUBWAY", "Restaurant"),
        ("O TACOS", "Restaurant"), ("BIG FERNAND", "Restaurant"),
        ("SUSHI SHOP", "Restaurant"), ("PLANET SUSHI", "Restaurant"),
        ("UBER EATS", "Restaurant"), ("DELIVEROO", "Restaurant"), 
        ("JUST EAT", "Restaurant"), ("STARBUCKS", "Restaurant"), 
        ("COLUMBUS", "Restaurant"), ("PAUL", "Restaurant"),
        ("BRIOCHE DOREE", "Restaurant"), ("PRET A MANGER", "Restaurant"),
        ("RESTO", "Restaurant"), ("BISTROT", "Restaurant"),
        ("BRASSERIE", "Restaurant"), ("BAR", "Restaurant"),
        ("PUB", "Restaurant"), ("CAFE", "Restaurant"),
        
        # --- TRANSPORT ---
        ("SNCF", "Transport"), ("RATP", "Transport"), ("TICKET", "Transport"),
        ("OUIGO", "Transport"), ("TRAINLINE", "Transport"),
        ("UBER", "Transport"), ("BOLT", "Transport"), ("HEETCH", "Transport"),
        ("TAXI", "Transport"), ("BLABLACAR", "Transport"),
        ("TOTAL", "Transport"), ("ESSO", "Transport"), ("SHELL", "Transport"),
        ("BP", "Transport"), ("AVIA", "Transport"), ("STATION", "Transport"),
        ("PEAGE", "Transport"), ("VINCI AUTOROUTES", "Transport"),
        ("SANEF", "Transport"), ("APRR", "Transport"),
        ("PARKING", "Transport"), ("INDIGO", "Transport"),
        ("LIME", "Transport"), ("BIRD", "Transport"), ("VELIB", "Transport"),
        ("AIR FRANCE", "Transport"), ("EASYJET", "Transport"),
        ("RYANAIR", "Transport"), ("TRANSAVIA", "Transport"),
        ("NORAUTO", "Transport"), ("FEU VERT", "Transport"),
        ("MIDAS", "Transport"), ("CARGLASS", "Transport"),
        
        # --- LOGEMENT & MAISON ---
        ("EDF", "Logement"), ("ENGIE", "Logement"), ("TOTAL ENERGIES", "Logement"),
        ("ENI", "Logement"), ("EAU", "Logement"), ("VEOLIA", "Logement"),
        ("SUEZ", "Logement"), ("LOYER", "Logement"), ("SYNDIC", "Logement"),
        ("FONCIA", "Logement"), ("NEXITY", "Logement"),
        ("LEROY MERLIN", "Logement"), ("CASTORAMA", "Logement"), 
        ("BRICO DEPOT", "Logement"), ("MR BRICOLAGE", "Logement"),
        ("IKEA", "Logement"), ("ALINEA", "Logement"), 
        ("MAISONS DU MONDE", "Logement"), ("CONFORAMA", "Logement"),
        ("BUT", "Logement"), ("ACTION", "Logement"), ("GIFI", "Logement"),
        ("HEMA", "Logement"), ("LA FOIR FOUILL", "Logement"),
        
        # --- ABONNEMENTS (Téléphone, Internet, Streaming) ---
        ("NETFLIX", "Abonnements"), ("SPOTIFY", "Abonnements"), 
        ("DEEZER", "Abonnements"), ("APPLE MUSIC", "Abonnements"),
        ("AMAZON PRIME", "Abonnements"), ("DISNEY", "Abonnements"),
        ("CANAL", "Abonnements"), ("OCS", "Abonnements"),
        ("YOUTUBE", "Abonnements"), ("TWITCH", "Abonnements"),
        ("FREE MOBILE", "Abonnements"), ("ORANGE", "Abonnements"), 
        ("BOUYGUES", "Abonnements"), ("SFR", "Abonnements"), 
        ("SOSH", "Abonnements"), ("RED BY SFR", "Abonnements"),
        ("ICLOUD", "Abonnements"), ("GOOGLE STORAGE", "Abonnements"),
        ("MICROSOFT", "Abonnements"), ("ADOBE", "Abonnements"),
        ("NORDVPN", "Abonnements"), ("CHATGPT", "Abonnements"),
        
        # --- SHOPPING & VÊTEMENTS ---
        ("AMAZON", "Shopping"), ("CDISCOUNT", "Shopping"),
        ("ZALANDO", "Shopping"), ("ASOS", "Shopping"), ("SHEIN", "Shopping"),
        ("VINTED", "Shopping"), ("LEBONCOIN", "Shopping"),
        ("ZARA", "Shopping"), ("H&M", "Shopping"), ("UNIQLO", "Shopping"),
        ("MANGO", "Shopping"), ("PRIMARK", "Shopping"), ("KIABI", "Shopping"),
        ("GEMO", "Shopping"), ("LA HALLE", "Shopping"),
        ("ETAM", "Shopping"), ("CELIO", "Shopping"), ("JULES", "Shopping"),
        ("NIKE", "Shopping"), ("ADIDAS", "Shopping"), ("JD SPORTS", "Shopping"),
        ("COURIR", "Shopping"), ("FOOT LOCKER", "Shopping"),
        ("SEPHORA", "Shopping"), ("MARIONNAUD", "Shopping"),
        ("YVES ROCHER", "Shopping"), ("NOCIBE", "Shopping"),
        
        # --- LOISIRS & TECH ---
        ("FNAC", "Loisirs"), ("DARTY", "Loisirs"), ("BOULANGER", "Loisirs"),
        ("LDLC", "Loisirs"), ("MATERIEL.NET", "Loisirs"),
        ("APPLE STORE", "Loisirs"), ("CULTURA", "Loisirs"),
        ("DECATHLON", "Sport"), ("INTERSPORT", "Sport"), ("GO SPORT", "Sport"),
        ("BASIC FIT", "Sport"), ("FITNESS PARK", "Sport"),
        ("CINEMA", "Loisirs"), ("UGC", "Loisirs"), ("GAUMONT", "Loisirs"),
        ("PATHE", "Loisirs"), ("CGR", "Loisirs"),
        ("STEAM", "Loisirs"), ("PLAYSTATION", "Loisirs"), 
        ("XBOX", "Loisirs"), ("NINTENDO", "Loisirs"),
        ("BLIZZARD", "Loisirs"), ("UBISOFT", "Loisirs"),
        
        # --- SANTÉ ---
        ("PHARMACIE", "Santé"), ("DOCTOLIB", "Santé"), ("QARE", "Santé"),
        ("ALAN", "Santé"), ("MUTUELLE", "Santé"), ("HARMONIE", "Santé"),
        ("MGEN", "Santé"), ("MACIF", "Santé"), ("MAIF", "Santé"),
        ("AXA", "Santé"), ("ALLIANZ", "Santé"),
        ("MEDECIN", "Santé"), ("DENTISTE", "Santé"), ("OPHTALMO", "Santé"),
        ("HOPITAL", "Santé"), ("CLINIQUE", "Santé"), ("LABO", "Santé"),
        ("OPTICIEN", "Santé"), ("KRYS", "Santé"), ("AFFLELOU", "Santé"),
        
        # --- BANQUE & FRAIS ---
        ("COTISATION", "Banque & Frais"), ("AGIOS", "Banque & Frais"),
        ("COMMISSION", "Banque & Frais"), ("FRAIS", "Banque & Frais"),
        ("INTERETS", "Banque & Frais"), ("PRELEVEMENT", "Banque & Frais"),
        ("RETRAIT", "Banque & Frais"),
        
        # --- REVENUS ---
        ("SALAIRE", "Revenus"), ("VIREMENT", "Revenus"),
        ("CAF", "Revenus"), ("CPAM", "Revenus"), ("POLE EMPLOI", "Revenus"),
        ("FRANCE TRAVAIL", "Revenus"), ("REMBOURSEMENT", "Revenus"),
        ("IMPOTS", "Impôts & Taxes"), ("DGFIP", "Impôts & Taxes"),
        
        # --- VACANCES ---
        ("AIRBNB", "Vacances"), ("BOOKING", "Vacances"),
        ("HOTEL", "Vacances"), ("CAMPING", "Vacances")
    ]
    
    cursor.executemany("INSERT OR IGNORE INTO rules (keyword, category) VALUES (?, ?)", smart_rules)
    
    conn.commit()
    conn.close()

# =============================================================================
# GESTION DES TRANSACTIONS
# =============================================================================

def add_transaction(date, label, amount, category=None, note="", status="A_TRAITER", fingerprint=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO transactions (date, label, amount, category, note, status, fingerprint) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (date, label, amount, category, note, status, fingerprint)
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def transaction_exists(fingerprint):
    """Vérifie si une transaction avec cette empreinte existe déjà."""
    conn = get_db_connection()
    row = conn.execute("SELECT id FROM transactions WHERE fingerprint = ?", (fingerprint,)).fetchone()
    conn.close()
    return row is not None

def get_transactions(status=None, year=None, month=None, search=None):
    conn = get_db_connection()
    query = "SELECT * FROM transactions WHERE 1=1"
    params = []
    
    if status:
        query += " AND status = ?"
        params.append(status)
        
    if year and year != "Tous":
        query += " AND strftime('%Y', date) = ?"
        params.append(year)
        
    if month and month != "Tous":
        query += " AND strftime('%m', date) = ?"
        params.append(month)
        
    if search:
        query += " AND (label LIKE ? OR category LIKE ? OR note LIKE ?)"
        wildcard = f"%{search}%"
        params.extend([wildcard, wildcard, wildcard])
        
    query += " ORDER BY date DESC, id DESC"
    
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return rows

def get_transaction_by_id(t_id):
    conn = get_db_connection()
    row = conn.execute("SELECT * FROM transactions WHERE id = ?", (t_id,)).fetchone()
    conn.close()
    return row

def update_transaction_fields(t_id, date, label, amount, category, note, status):
    conn = get_db_connection()
    conn.execute(
        "UPDATE transactions SET date=?, label=?, amount=?, category=?, note=?, status=? WHERE id=?",
        (date, label, amount, category, note, status, t_id)
    )
    conn.commit()
    conn.close()

def validate_transaction(t_id):
    conn = get_db_connection()
    conn.execute("UPDATE transactions SET status='VALIDEE' WHERE id=?", (t_id,))
    conn.commit()
    conn.close()

def validate_all_transactions(ids):
    conn = get_db_connection()
    conn.executemany("UPDATE transactions SET status='VALIDEE' WHERE id=?", [(i,) for i in ids])
    conn.commit()
    conn.close()

def delete_transaction(t_id):
    conn = get_db_connection()
    conn.execute("DELETE FROM transactions WHERE id = ?", (t_id,))
    conn.commit()
    conn.close()

# =============================================================================
# GESTION DES RÈGLES
# =============================================================================

def get_rules():
    conn = get_db_connection()
    rows = conn.execute("SELECT keyword, category FROM rules").fetchall()
    conn.close()
    return {row["keyword"]: row["category"] for row in rows}

def add_rule(keyword, category):
    conn = get_db_connection()
    try:
        conn.execute("INSERT INTO rules (keyword, category) VALUES (?, ?)", (keyword.upper(), category))
        conn.commit()
    except:
        pass
    conn.close()

def delete_rule_by_keyword(keyword):
    conn = get_db_connection()
    conn.execute("DELETE FROM rules WHERE keyword = ?", (keyword,))
    conn.commit()
    conn.close()

# =============================================================================
# GESTION DES CATÉGORIES
# =============================================================================

def list_categories():
    conn = get_db_connection()
    rows = conn.execute("SELECT name FROM categories ORDER BY name").fetchall()
    conn.close()
    return [r['name'] for r in rows]

def add_category(name):
    conn = get_db_connection()
    try:
        conn.execute("INSERT INTO categories (name) VALUES (?)", (name,))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        conn.close()
        return False

def rename_category(old_name, new_name):
    conn = get_db_connection()
    try:
        conn.execute("UPDATE categories SET name = ? WHERE name = ?", (new_name, old_name))
        conn.execute("UPDATE transactions SET category = ? WHERE category = ?", (new_name, old_name))
        conn.execute("UPDATE rules SET category = ? WHERE category = ?", (new_name, old_name))
        conn.execute("UPDATE budgets SET category = ? WHERE category = ?", (new_name, old_name))
        conn.commit()
        conn.close()
        return True
    except:
        conn.close()
        return False

def delete_category(name):
    conn = get_db_connection()
    conn.execute("DELETE FROM categories WHERE name = ?", (name,))
    conn.commit()
    conn.close()

def get_category_usage(category_name):
    conn = get_db_connection()
    count = conn.execute("SELECT COUNT(*) FROM transactions WHERE category = ?", (category_name,)).fetchone()[0]
    conn.close()
    return count

def reassign_category_transactions(old_category, new_category):
    conn = get_db_connection()
    conn.execute("UPDATE transactions SET category = ? WHERE category = ?", (new_category, old_category))
    conn.commit()
    conn.close()

# =============================================================================
# STATISTIQUES & BUDGETS
# =============================================================================

def get_years_available():
    conn = get_db_connection()
    rows = conn.execute("SELECT DISTINCT strftime('%Y', date) as y FROM transactions ORDER BY y DESC").fetchall()
    conn.close()
    return [r['y'] for r in rows]

def get_summary_stats(year=None, month=None, search_query=None, status_filter=None):
    query = "SELECT amount FROM transactions WHERE 1=1"
    params = []
    
    if status_filter:
        query += " AND status = ?"
        params.append(status_filter)
    if year and year != "Tous":
        query += " AND strftime('%Y', date) = ?"
        params.append(year)
    if month and month != "Tous":
        query += " AND strftime('%m', date) = ?"
        params.append(month)
    if search_query:
        query += " AND (label LIKE ? OR category LIKE ?)"
        wildcard = f"%{search_query}%"
        params.extend([wildcard, wildcard, wildcard])
        
    conn = get_db_connection()
    rows = conn.execute(query, params).fetchall()
    conn.close()
    
    income = sum(r['amount'] for r in rows if r['amount'] > 0)
    expenses = sum(r['amount'] for r in rows if r['amount'] < 0)
    balance = income + expenses
    return income, expenses, balance

def get_stats_by_category(year=None, month=None, transaction_type="expense", status_filter=None):
    operator = "<" if transaction_type == "expense" else ">"
    query = f"SELECT category, SUM(amount) as total FROM transactions WHERE amount {operator} 0"
    params = []
    
    if status_filter:
        query += " AND status = ?"
        params.append(status_filter)
    if year and year != "Tous":
        query += " AND strftime('%Y', date) = ?"
        params.append(year)
    if month and month != "Tous":
        query += " AND strftime('%m', date) = ?"
        params.append(month)
        
    query += " GROUP BY category ORDER BY total ASC" if transaction_type=="expense" else " GROUP BY category ORDER BY total DESC"
    
    conn = get_db_connection()
    rows = conn.execute(query, params).fetchall()
    conn.close()
    
    return [(r['category'] if r['category'] else 'Sans Catégorie', abs(r['total'])) for r in rows]

def get_monthly_totals(year, transaction_type="expense", status_filter=None):
    operator = "<" if transaction_type == "expense" else ">"
    conn = get_db_connection()
    
    status_sql = "AND status = ?" if status_filter else ""
    params = [year]
    if status_filter: params.append(status_filter)
    
    sql = f'''
        SELECT strftime('%m', date) as m, SUM(amount) as total
        FROM transactions
        WHERE strftime('%Y', date) = ? AND amount {operator} 0 {status_sql}
        GROUP BY m
    '''
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    
    data = {f"{i:02d}": 0.0 for i in range(1, 13)}
    for r in rows:
        data[r['m']] = abs(r['total'])
        
    return list(data.values())

def get_all_budgets():
    conn = get_db_connection()
    rows = conn.execute("SELECT category, amount FROM budgets").fetchall()
    conn.close()
    return {row['category']: row['amount'] for row in rows}

def set_budget(category, amount):
    conn = get_db_connection()
    conn.execute("INSERT OR REPLACE INTO budgets (category, amount) VALUES (?, ?)", (category, amount))
    conn.commit()
    conn.close()

def get_monthly_balance_history(limit=12):
    """Récupère le solde net (Recettes - Dépenses) des derniers mois."""
    conn = get_db_connection()
    
    # On groupe par mois (YYYY-MM) et on somme tout
    query = '''
        SELECT strftime('%Y-%m', date) as m, SUM(amount)
        FROM transactions 
        WHERE status = 'VALIDEE'
        GROUP BY m
        ORDER BY m DESC
        LIMIT ?
    '''
    rows = conn.execute(query, (limit,)).fetchall()
    conn.close()
    
    return rows[::-1]

# Auto-initialisation si on lance ce fichier directement
if __name__ == "__main__":
    init_db()
    print("Database initialized.")