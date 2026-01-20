import tkinter as tk
from ui import EcoGestApp
from database import init_db

def main():
    print("--- Démarrage de l'application ---")
    
    # 1. CRUCIAL : On crée les tables (transactions, rules) AVANT tout le reste
    init_db()
    print("Base de données initialisée.")

    # 2. On lance l'interface graphique
    root = tk.Tk()
    
    # Force la fenêtre au premier plan (astuce Mac)
    root.lift()
    root.attributes('-topmost',True)
    root.after_idle(root.attributes,'-topmost',False)
    
    app = EcoGestApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()