import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
from datetime import datetime
import csv
import database as database
import logic as logic
import matplotlib
matplotlib.use('TkAgg')
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt

class EcoGestApp:
    def __init__(self, root):
        self.root = root
        self.root.title("EcoGest - Gestion Financière")
        self.root.geometry("1300x850") # Un peu plus large pour les budgets
        
        style = ttk.Style()
        style.theme_use('clam')
        
        # Styles visuels pour les barres de progression
        style.configure("green.Horizontal.TProgressbar", background='#4caf50')
        style.configure("red.Horizontal.TProgressbar", background='#f44336')

        # Variable pour la checkbox "Inclure non validées"
        self.var_show_all = tk.BooleanVar(value=False) 
        
        # --- ONGLETS ---
        self.tabs = ttk.Notebook(self.root)
        self.tabs.pack(expand=1, fill="both")

        # 1. INBOX
        self.tab_inbox = ttk.Frame(self.tabs)
        self.tabs.add(self.tab_inbox, text="À Valider")
        self.setup_inbox_tab()

        # 2. HISTORIQUE
        self.tab_history = ttk.Frame(self.tabs)
        self.tabs.add(self.tab_history, text="Historique")
        self.setup_history_tab()

        # 3. STATS
        self.tab_stats = ttk.Frame(self.tabs)
        self.tabs.add(self.tab_stats, text="Statistiques")
        self.setup_stats_tab()
        
        # 4. CONFIG
        self.tab_config = ttk.Frame(self.tabs)
        self.tabs.add(self.tab_config, text="Configuration")
        self.setup_config_tab()

        # Initialisation
        self.update_year_filter()
        self.refresh_data()

    # =========================================================================
    # ONGLET 1 : INBOX
    # =========================================================================
    def setup_inbox_tab(self):
        toolbar = ttk.Frame(self.tab_inbox, padding=10)
        toolbar.pack(fill="x")
        
        btn_import = ttk.Button(toolbar, text="Importer CSV", command=self.import_csv)
        btn_import.pack(side="left", padx=5)
        
        self.btn_validate_all = ttk.Button(toolbar, text="Tout Valider", command=self.validate_all_action)
        self.btn_validate_all.pack(side="right", padx=5)
        
        self.lbl_inbox_count = ttk.Label(toolbar, text="0 transactions en attente", foreground="red", font=("Arial", 10, "bold"))
        self.lbl_inbox_count.pack(side="right", padx=10)

        columns = ("ID", "Date", "Libellé", "Montant", "Catégorie", "Note")
        self.tree_inbox = ttk.Treeview(self.tab_inbox, columns=columns, show="headings")
        
        self.tree_inbox.heading("ID", text="#")
        self.tree_inbox.column("ID", width=40, stretch=False)
        self.tree_inbox.heading("Date", text="Date")
        self.tree_inbox.column("Date", width=90)
        self.tree_inbox.heading("Libellé", text="Libellé")
        self.tree_inbox.column("Libellé", width=350)
        self.tree_inbox.heading("Montant", text="Montant")
        self.tree_inbox.column("Montant", width=90, anchor="e")
        self.tree_inbox.heading("Catégorie", text="Catégorie")
        self.tree_inbox.column("Catégorie", width=120)
        self.tree_inbox.heading("Note", text="Note")
        self.tree_inbox.column("Note", width=150)
        
        self.tree_inbox.pack(expand=True, fill="both", padx=10, pady=5)
        
        # Suppression touche clavier
        self.tree_inbox.bind("<Delete>", lambda e: self.delete_transaction_action(self.tree_inbox))
        
        self.menu_inbox = tk.Menu(self.root, tearoff=0)
        self.menu_inbox.add_command(label="Modifier / Corriger", command=lambda: self.open_edit_modal(self.tree_inbox))
        self.menu_inbox.add_command(label="⚡️ Créer une Règle", command=lambda: self.open_quick_rule_modal(self.tree_inbox))
        self.menu_inbox.add_separator()
        self.menu_inbox.add_command(label="Valider", command=self.validate_single_action)
        self.menu_inbox.add_command(label="Supprimer", command=lambda: self.delete_transaction_action(self.tree_inbox))
        
        self.tree_inbox.bind("<Button-3>", lambda e: self.show_context_menu(e, self.tree_inbox, self.menu_inbox))
        self.tree_inbox.bind("<Double-1>", lambda e: self.open_edit_modal(self.tree_inbox))

    # =========================================================================
    # ONGLET 2 : HISTORIQUE
    # =========================================================================
    def setup_history_tab(self):
        filter_frame = ttk.Frame(self.tab_history, padding=10)
        filter_frame.pack(fill="x")
        
        self.combo_year = ttk.Combobox(filter_frame, width=6, state="readonly")
        self.combo_year.pack(side="left", padx=5)
        self.combo_year.bind("<<ComboboxSelected>>", self.refresh_data)
        
        self.combo_month = ttk.Combobox(filter_frame, width=5, state="readonly", values=["Tous"] + [f"{i:02d}" for i in range(1, 13)])
        self.combo_month.current(0)
        self.combo_month.pack(side="left", padx=5)
        self.combo_month.bind("<<ComboboxSelected>>", self.refresh_data)
        
        self.entry_search = ttk.Entry(filter_frame, width=20)
        self.entry_search.pack(side="left", padx=10)
        self.entry_search.bind("<Return>", self.refresh_data)
        ttk.Button(filter_frame, text="Chercher", width=10, command=self.refresh_data).pack(side="left")

        # CHECKBOX
        chk = ttk.Checkbutton(filter_frame, text="Inclure non validées", variable=self.var_show_all, command=self.refresh_data)
        chk.pack(side="left", padx=15)

        self.lbl_kpi = ttk.Label(filter_frame, text="Solde : 0€", font=("Arial", 10, "bold"))
        self.lbl_kpi.pack(side="right", padx=10)

        columns = ("ID", "Date", "Libellé", "Montant", "Catégorie", "Status")
        self.tree_history = ttk.Treeview(self.tab_history, columns=columns, show="headings")
        for col in columns: 
            self.tree_history.heading(col, text=col)
            if col == "Libellé": self.tree_history.column(col, width=300)
            else: self.tree_history.column(col, width=100)
            
        self.tree_history.pack(expand=True, fill="both", padx=10, pady=5)
        
        # Suppression touche clavier
        self.tree_history.bind("<Delete>", lambda e: self.delete_transaction_action(self.tree_history))
        
        self.tree_history.tag_configure("expense", foreground="red")
        self.tree_history.tag_configure("income", foreground="green")

        self.menu_history = tk.Menu(self.root, tearoff=0)
        self.menu_history.add_command(label="Modifier Détails", command=lambda: self.open_edit_modal(self.tree_history))
        self.menu_history.add_command(label="⚡️ Créer une Règle", command=lambda: self.open_quick_rule_modal(self.tree_history))
        self.menu_history.add_separator()
        self.menu_history.add_command(label="Supprimer", command=lambda: self.delete_transaction_action(self.tree_history))

        self.tree_history.bind("<Button-3>", lambda e: self.show_context_menu(e, self.tree_history, self.menu_history))
        self.tree_history.bind("<Double-1>", lambda e: self.open_edit_modal(self.tree_history))

    # =========================================================================
    # ONGLET 3 : STATS
    # =========================================================================
    def setup_stats_tab(self):
        paned = ttk.PanedWindow(self.tab_stats, orient="horizontal")
        paned.pack(fill="both", expand=True, padx=10, pady=10)

        self.left_frame = ttk.Frame(paned)
        paned.add(self.left_frame, weight=3) # Plus d'espace pour le graph
        
        ctrl_frame = ttk.Frame(self.left_frame)
        ctrl_frame.pack(fill="x", pady=5)
        
        self.combo_chart_type = ttk.Combobox(ctrl_frame, values=["Dépenses", "Revenus"], state="readonly", width=10)
        self.combo_chart_type.current(0)
        self.combo_chart_type.pack(side="left", padx=5)
        self.combo_chart_type.bind("<<ComboboxSelected>>", lambda e: self.update_chart())
        
        # --- MENU CHOIX GRAPHIQUE ---
        self.combo_viz_style = ttk.Combobox(ctrl_frame, values=["Bulles", "Chronologie", "Pourcentages"], state="readonly", width=12)
        self.combo_viz_style.current(2) # Pourcentages par défaut
        self.combo_viz_style.pack(side="left", padx=5)
        self.combo_viz_style.bind("<<ComboboxSelected>>", lambda e: self.update_chart())

        # --- BOUTON PRÉVISION ---
        ttk.Button(ctrl_frame, text="Prévision Trésorerie", command=self.show_forecast_modal).pack(side="right", padx=5)

        self.chart_container = tk.Frame(self.left_frame)
        self.chart_container.pack(fill="both", expand=True)
        
        self.right_frame = ttk.Frame(paned, relief="sunken", padding=10)
        paned.add(self.right_frame, weight=1)
        
        ttk.Label(self.right_frame, text="Budgets", font=("Arial", 12, "bold")).pack(pady=10)
        ttk.Button(self.right_frame, text="Définir un Budget", command=self.set_budget_action).pack()
        
        self.budget_container = ttk.Frame(self.right_frame)
        self.budget_container.pack(fill="both", expand=True, pady=10)

    # =========================================================================
    # ONGLET 4 : CONFIGURATION (CATEGORIES & REGLES)
    # =========================================================================
    def setup_config_tab(self):
        paned = ttk.PanedWindow(self.tab_config, orient="horizontal")
        paned.pack(fill="both", expand=True, padx=10, pady=10)

        # --- GAUCHE : GESTION DES CATÉGORIES ---
        frame_cats = ttk.LabelFrame(paned, text="Gestion des Catégories", padding=10)
        paned.add(frame_cats, weight=1)

        self.list_cats = tk.Listbox(frame_cats, height=15)
        self.list_cats.pack(fill="both", expand=True, pady=5)
        
        btn_frame = ttk.Frame(frame_cats)
        btn_frame.pack(fill="x", pady=5)
        
        ttk.Button(btn_frame, text="Ajouter", command=self.add_category_action).pack(side="left", fill="x", expand=True, padx=2)
        ttk.Button(btn_frame, text="Renommer", command=self.rename_category_action).pack(side="left", fill="x", expand=True, padx=2)
        ttk.Button(btn_frame, text="Supprimer", command=self.delete_category_action).pack(side="left", fill="x", expand=True, padx=2)

        # --- DROITE : RÈGLES AUTOMATIQUES ---
        frame_rules = ttk.LabelFrame(paned, text="Règles d'Import", padding=10)
        paned.add(frame_rules, weight=1)
        
        f_add = ttk.Frame(frame_rules)
        f_add.pack(fill="x", pady=5)
        
        ttk.Label(f_add, text="Si Libellé contient :").pack(anchor="w")
        self.entry_rule_kw = ttk.Entry(f_add)
        self.entry_rule_kw.pack(fill="x", pady=2)
        
        ttk.Label(f_add, text="Alors Catégorie :").pack(anchor="w", pady=(5,0))
        self.combo_rule_cat = ttk.Combobox(f_add, postcommand=self.update_cat_combo)
        self.combo_rule_cat.pack(fill="x", pady=2)
        
        ttk.Button(f_add, text="Ajouter la règle", command=self.add_rule_action).pack(pady=5, fill="x")
        
        ttk.Separator(frame_rules, orient='horizontal').pack(fill='x', pady=10)
        
        self.list_rules = tk.Listbox(frame_rules, height=10)
        self.list_rules.pack(fill="both", expand=True, pady=5)
        ttk.Button(frame_rules, text="Supprimer la règle sélectionnée", command=self.delete_rule_action).pack(fill="x")

    # =========================================================================
    # LOGIQUE PRINCIPALE & REFRESH
    # =========================================================================

    def import_csv(self):
        file_path = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv")])
        if file_path:
            success, msg = logic.import_csv_file(file_path)
            if success:
                messagebox.showinfo("Import", msg)
                self.refresh_data()
            else:
                messagebox.showerror("Erreur", msg)

    def refresh_data(self, event=None):
        """Met à jour toute l'interface."""
        
        # 0. Récupération des filtres
        status_filter = None if self.var_show_all.get() else "VALIDEE"
        y = self.combo_year.get()
        m = self.combo_month.get()
        s = self.entry_search.get()

        # 1. Refresh INBOX
        for item in self.tree_inbox.get_children(): self.tree_inbox.delete(item)
        inbox_rows = database.get_transactions(status="A_TRAITER")
        self.lbl_inbox_count.config(text=f"{len(inbox_rows)} transactions à valider")
        for row in inbox_rows:
            display = (row[0], row[1], row[2], f"{row[3]:.2f} €", row[4], row[6])
            self.tree_inbox.insert("", "end", values=display)

        # 2. Refresh HISTORIQUE
        for item in self.tree_history.get_children(): self.tree_history.delete(item)
        history_rows = database.get_transactions(status=status_filter, year=y, month=m, search=s)
        
        for row in history_rows:
            tag = "expense" if row[3] < 0 else "income"
            status_display = row[5]
            if status_display == "A_TRAITER": status_display = "EN ATTENTE"
            display = (row[0], row[1], row[2], f"{row[3]:.2f} €", row[4], status_display)
            self.tree_history.insert("", "end", values=display, tags=(tag,))

        # KPIs
        inc, exp, bal = database.get_summary_stats(year=y, month=m, search_query=s, status_filter=status_filter)
        self.lbl_kpi.config(text=f"Solde : {bal:.2f} €", foreground="green" if bal >= 0 else "red")

        # 3. Refresh Stats
        self.update_chart()
        
        # 4. Refresh Listes
        self.list_rules.delete(0, tk.END)
        for kw, cat in database.get_rules().items():
            self.list_rules.insert(tk.END, f"{kw} -> {cat}")
            
        self.refresh_categories_list()

    def refresh_categories_list(self):
        """Met à jour la liste visuelle des catégories."""
        self.list_cats.delete(0, tk.END)
        cats = database.list_categories()
        for cat in cats:
            self.list_cats.insert(tk.END, cat)

    def update_cat_combo(self):
        cats = database.list_categories()
        try:
            self.combo_rule_cat['values'] = cats
        except: pass
        return cats

    # =========================================================================
    # ACTIONS CATEGORIES (CRUD)
    # =========================================================================

    def add_category_action(self):
        new_name = simpledialog.askstring("Nouvelle Catégorie", "Nom de la catégorie :")
        if new_name:
            if database.add_category(new_name):
                self.refresh_data()
                messagebox.showinfo("Information", f"Catégorie '{new_name}' créée.")
            else:
                messagebox.showerror("Erreur", "Cette catégorie existe déjà.")

    def rename_category_action(self):
        sel = self.list_cats.curselection()
        if not sel: return
        old_name = self.list_cats.get(sel[0])
        
        new_name = simpledialog.askstring("Renommer", f"Renommer '{old_name}' en :", initialvalue=old_name)
        if new_name and new_name != old_name:
            if database.rename_category(old_name, new_name):
                self.refresh_data()
                messagebox.showinfo("Information", "Catégorie renommée et transactions mises à jour.")
            else:
                messagebox.showerror("Erreur", "Impossible de renommer (nom déjà pris ?).")

    def delete_category_action(self):
        sel = self.list_cats.curselection()
        if not sel: return
        cat_name = self.list_cats.get(sel[0])
        
        if cat_name == "Autre":
            messagebox.showwarning("Interdit", "La catégorie 'Autre' ne peut pas être supprimée.")
            return

        usage_count = database.get_category_usage(cat_name)
        
        if usage_count > 0:
            msg = f"La catégorie '{cat_name}' est utilisée par {usage_count} transactions.\n"\
                  f"Veuillez choisir une nouvelle catégorie pour ces transactions avant de supprimer."
            
            win = tk.Toplevel(self.root)
            win.title("Recatégorisation requise")
            win.geometry("400x200")
            win.transient(self.root)
            win.grab_set()
            
            ttk.Label(win, text=msg, wraplength=380, justify="center").pack(pady=20)
            
            cats = database.list_categories()
            if cat_name in cats: cats.remove(cat_name)
            
            combo_dest = ttk.Combobox(win, values=cats, state="readonly")
            combo_dest.pack(pady=5)
            if cats: combo_dest.current(0)
            
            def confirm_migration():
                target_cat = combo_dest.get()
                if not target_cat: return
                
                database.reassign_category_transactions(cat_name, target_cat)
                database.delete_category(cat_name)
                
                win.destroy()
                self.refresh_data()
                messagebox.showinfo("Information", f"Transactions déplacées vers '{target_cat}' et '{cat_name}' supprimée.")
            
            ttk.Button(win, text="Migrer et Supprimer", command=confirm_migration).pack(pady=10)
            
        else:
            if messagebox.askyesno("Confirmation", f"Supprimer la catégorie vide '{cat_name}' ?"):
                database.delete_category(cat_name)
                self.refresh_data()

    # =========================================================================
    # ACTIONS TRANSACTIONS & RÈGLES
    # =========================================================================

    def show_context_menu(self, event, tree, menu):
        item = tree.identify_row(event.y)
        if item:
            tree.selection_set(item)
            menu.post(event.x_root, event.y_root)

    def validate_single_action(self):
        sel = self.tree_inbox.selection()
        if not sel: return
        t_id = self.tree_inbox.item(sel[0])['values'][0]
        database.validate_transaction(t_id)
        self.refresh_data()

    def validate_all_action(self):
        all_items = self.tree_inbox.get_children()
        if not all_items: return
        
        ids = [self.tree_inbox.item(item)['values'][0] for item in all_items]
        if messagebox.askyesno("Valider", f"Valider ces {len(ids)} transactions ?"):
            database.validate_all_transactions(ids)
            self.refresh_data()
            self.tabs.select(self.tab_history)

    def open_edit_modal(self, tree):
        sel = tree.selection()
        if not sel: return
        
        # On récupère l'ID
        t_id = tree.item(sel[0])['values'][0]
        data = database.get_transaction_by_id(t_id)
        
        if not data:
            messagebox.showerror("Erreur", "Transaction introuvable.")
            return
            
        # Extraction des données
        current_date = data[1]
        current_label = data[2]
        current_amount = data[3]
        current_cat = data[4]
        current_status = data[5]
        current_note = data[6]

        win = tk.Toplevel(self.root)
        win.title(f"Modifier Transaction #{t_id}")
        win.geometry("450x550")
        win.transient(self.root)
        win.grab_set()

        # 1. DATE
        ttk.Label(win, text="Date (AAAA-MM-JJ) :").pack(pady=(15, 5))
        e_date = ttk.Entry(win, width=30)
        e_date.insert(0, current_date if current_date else "")
        e_date.pack()

        # 2. LIBELLÉ
        ttk.Label(win, text="Libellé :").pack(pady=5)
        e_label = ttk.Entry(win, width=50)
        e_label.insert(0, current_label if current_label else "")
        e_label.pack()

        # 3. MONTANT
        ttk.Label(win, text="Montant (€) :").pack(pady=5)
        e_amount = ttk.Entry(win, width=20)
        e_amount.insert(0, str(current_amount) if current_amount is not None else "0.0")
        e_amount.pack()

        # 4. CATÉGORIE
        ttk.Label(win, text="Catégorie :").pack(pady=5)
        cats = database.list_categories()
        e_cat = ttk.Combobox(win, values=cats, state="readonly", width=28)
        
        if current_cat:
            e_cat.set(current_cat)
        else:
            e_cat.set('') 
            
        e_cat.pack()

        # 5. NOTE
        ttk.Label(win, text="Note (Optionnel) :").pack(pady=5)
        e_note = ttk.Entry(win, width=50)
        if current_note: e_note.insert(0, current_note)
        e_note.pack()

        # 6. STATUT
        ttk.Label(win, text="Statut :").pack(pady=5)
        e_status = ttk.Entry(win, width=20)
        e_status.insert(0, current_status if current_status else "A_TRAITER")
        e_status.config(state="readonly")
        e_status.pack()

        def save_changes():
            new_date = e_date.get().strip()
            # Validation Date Simple
            try:
                datetime.strptime(new_date, '%Y-%m-%d')
            except ValueError:
                messagebox.showerror("Erreur", "Format de date invalide.\nUtilisez AAAA-MM-JJ", parent=win)
                return

            # Validation Montant
            try:
                val = e_amount.get().replace(',', '.')
                new_amount = float(val)
            except ValueError:
                messagebox.showerror("Erreur", "Montant invalide.", parent=win)
                return

            new_cat = e_cat.get()
            if not new_cat:
                messagebox.showwarning("Attention", "Veuillez choisir une catégorie.", parent=win)
                return

            # Sauvegarde en base
            database.update_transaction_fields(
                t_id, 
                new_date, 
                e_label.get().strip(), 
                new_amount, 
                new_cat, 
                e_note.get().strip(), 
                current_status
            )
            
            self.refresh_data()
            win.destroy()
            messagebox.showinfo("Succès", "Modification enregistrée.")

        ttk.Button(win, text="Enregistrer", command=save_changes).pack(pady=20)

    def delete_transaction_action(self, tree):
        sel = tree.selection()
        if not sel: return
        t_id = tree.item(sel[0])['values'][0]
        if messagebox.askyesno("Supprimer", "Voulez-vous vraiment supprimer cette ligne ?"):
            database.delete_transaction(t_id)
            self.refresh_data()

    def add_rule_action(self):
        kw = self.entry_rule_kw.get()
        cat = self.combo_rule_cat.get()
        if kw and cat:
            database.add_rule(kw, cat)
            self.refresh_data()
            self.entry_rule_kw.delete(0, tk.END)
            self.combo_rule_cat.set('')

    def delete_rule_action(self):
        sel = self.list_rules.curselection()
        if sel:
            txt = self.list_rules.get(sel[0])
            kw = txt.split(" -> ")[0]
            database.delete_rule_by_keyword(kw)
            self.refresh_data()

    # =========================================================================
    # STATS & BUDGETS & PREVISION
    # =========================================================================
    
    def update_chart(self, event=None):
        """Met à jour les graphiques (Titres en Français)."""
        
        # Nettoyage de la zone graphique
        for w in self.chart_container.winfo_children(): w.destroy()
        
        # 1. CONFIGURATION & VARIABLES
        viz = self.combo_viz_style.get()
        if viz == "Camembert": viz = "Bulles"
        if viz == "Bâtons": viz = "Chronologie"

        # On récupère le type technique pour la base de données ("expense" ou "income")
        raw_type = self.combo_chart_type.get() # "Dépenses" ou "Revenus"
        dtype = "expense" if raw_type == "Dépenses" else "income"
        
        # On garde le nom en français pour l'affichage du titre
        display_name = raw_type 

        y = self.combo_year.get()
        m = self.combo_month.get()
        status_filter = None if self.var_show_all.get() else "VALIDEE"
        
        # --- Gestion de la colonne de droite (Budgets) ---
        cat_data = database.get_stats_by_category(year=y, month=m, transaction_type="expense", status_filter=status_filter)
        multiplier = 12 if m == "Tous" else 1
        
        if dtype == "expense":
            self.update_budgets_view(cat_data, multiplier)
        else:
            for w in self.budget_container.winfo_children(): w.destroy()
            ttk.Label(self.budget_container, text="Budgets disponibles\nuniquement pour les dépenses", 
                      justify="center", foreground="gray", wraplength=150).pack(pady=20)

        # 2. PRÉPARATION DU GRAPHIQUE
        fig = Figure(figsize=(5, 4), dpi=100, facecolor='white')
        ax = fig.add_subplot(111)
        ax.set_facecolor('white')

        # --- MODE 1 : BULLES ---
        if viz == "Bulles":
            if dtype == "income":
                data = database.get_stats_by_category(year=y, month=m, transaction_type="income", status_filter=status_filter)
            else:
                data = cat_data

            # Filtre les petits montants
            data = [d for d in data if d[1] > 0.01]

            if data:
                data.sort(key=lambda x: x[1], reverse=True)
                labels = [d[0] for d in data]
                values = [d[1] for d in data]
                max_val = max(values)
                
                # Taille des bulles
                min_size, max_size = 1500, 5000
                sizes = [min_size + ((v/max_val)**0.5 * (max_size-min_size)) for v in values]

                # Calcul grille
                nb_items = len(data)
                if nb_items == 2: cols = 2
                elif nb_items == 4: cols = 2
                else: cols = 3 if nb_items >= 3 else 1

                x_coords = []
                y_coords = []
                for i in range(nb_items):
                    x_coords.append(i % cols)
                    y_coords.append(-(i // cols))

                ax.scatter(x_coords, y_coords, s=sizes, alpha=0.5, c=range(nb_items), cmap='viridis', edgecolors='gray')
                
                # Texte dans les bulles
                for i, txt in enumerate(labels):
                    disp_txt = txt[:9]+"." if len(txt)>10 else txt
                    ax.annotate(f"{disp_txt}\n{values[i]:.0f}€", 
                                (x_coords[i], y_coords[i]), 
                                ha='center', va='center', 
                                fontsize=8, weight='bold', color='black')

                ax.axis('off')
                # --- TITRE CORRIGÉ ---
                ax.set_title(f"Répartition {display_name}", color='black', fontsize=12, fontweight='bold')
                
                # Marges
                ax.set_xlim(-0.6, cols - 0.4)
                nb_rows = (nb_items + cols - 1) // cols
                ax.set_ylim(-nb_rows + 0.4, 0.6)

            else:
                ax.text(0.5, 0.5, "AUCUNE DONNÉE", ha='center', color='red')
                ax.axis('off')

        # --- MODE 2 : POURCENTAGES (BARRES) ---
        elif viz == "Pourcentages":
            if dtype == "income":
                data = database.get_stats_by_category(year=y, month=m, transaction_type="income", status_filter=status_filter)
            else:
                data = cat_data
            
            data = [d for d in data if d[1] > 0]

            if data:
                data.sort(key=lambda x: x[1], reverse=True)
                cats = [d[0] for d in data]
                amounts = [d[1] for d in data]
                total = sum(amounts) if amounts else 1
                percents = [(a / total) * 100 for a in amounts]
                
                bars = ax.bar(cats, percents, color='#f44336' if dtype == "expense" else '#4caf50')
                
                for bar in bars:
                    height = bar.get_height()
                    if height > 3:
                        ax.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                                f'{height:.0f}%', ha='center', va='bottom', fontsize=8, fontweight='bold')
                
                # --- TITRE CORRIGÉ ---
                ax.set_title(f"Répartition {display_name}", color='black', pad=15, fontsize=12, fontweight='bold')
                
                ax.set_ylabel("%")
                plt.setp(ax.get_xticklabels(), rotation=45, ha="right")
                ax.spines['top'].set_visible(False)
                ax.spines['right'].set_visible(False)
                fig.subplots_adjust(bottom=0.3)
            else:
                ax.text(0.5, 0.5, "AUCUNE DONNÉE", ha='center', color='red')
                ax.axis('off')

        # --- MODE 3 : CHRONOLOGIE ---
        else:
            if not y or y == "Tous":
                ax.text(0.5, 0.5, "Sélectionnez une année précise", ha='center', color='black')
                ax.axis('off')
            else:
                monthly_data = database.get_monthly_totals(y, dtype, status_filter=status_filter)
                months = ["J","F","M","A","M","J","J","A","S","O","N","D"]
                ax.bar(months, monthly_data, color='skyblue' if dtype == "income" else 'salmon')
                
                # --- TITRE CORRIGÉ ---
                ax.set_title(f"Évolution {display_name} sur {y}", color='black', fontsize=12, fontweight='bold')
                
                ax.spines['top'].set_visible(False)
                ax.spines['right'].set_visible(False)
                
        self.canvas = FigureCanvasTkAgg(fig, master=self.chart_container)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

    def update_budgets_view(self, data, multiplier):
        for w in self.budget_container.winfo_children(): w.destroy()
        
        budgets = database.get_all_budgets()
        expenses = {d[0]: d[1] for d in data} if data else {}
        
        if multiplier > 1:
            ttk.Label(self.budget_container, text=f"Calcul sur {multiplier} mois (Annuel)", font=("Arial", 11, "italic")).pack(pady=(0, 10))
            
        if not budgets:
             ttk.Label(self.budget_container, text="Aucun budget défini.\nCliquez sur 'Définir un Budget'.", justify="center", foreground="gray", font=("Arial", 10)).pack(pady=20)
             return

        # Le petit texte d'aide un peu plus grand aussi
        ttk.Label(self.budget_container, text="Cliquez sur un budget pour le modifier", font=("Arial", 9), foreground="gray").pack(pady=(0, 10))

        for cat, limit in budgets.items():
            spent = expenses.get(cat, 0)
            total_limit = limit * multiplier
            pct = (spent / total_limit * 100) if total_limit else 0
            
            # On aère un peu plus les blocs (pady=4 au lieu de 2)
            f = ttk.Frame(self.budget_container, padding=5, relief="flat")
            f.pack(fill="x", pady=4)
            
            f.bind("<Enter>", lambda e, frame=f: frame.config(relief="raised"))
            f.bind("<Leave>", lambda e, frame=f: frame.config(relief="flat"))
            
            label_text = f"{cat}: {spent:.0f} / {total_limit:.0f} €"
            
            # --- MODIFICATION ICI : Police plus grande (11) ---
            lbl = ttk.Label(f, text=label_text, font=("Arial", 11))
            lbl.pack(anchor="w")
            
            style_name = "red.Horizontal.TProgressbar" if spent > total_limit else "green.Horizontal.TProgressbar"
            pb = ttk.Progressbar(f, value=min(pct, 100), style=style_name)
            pb.pack(fill="x", pady=(2, 0)) # Un peu d'espace entre le texte et la barre
            
            # Callbacks cliquables
            callback = lambda e, c=cat, l=limit: self.open_budget_options(c, l)
            f.bind("<Button-1>", callback)
            lbl.bind("<Button-1>", callback)
            pb.bind("<Button-1>", callback)

    def open_quick_rule_modal(self, tree):
        """Ouvre une fenêtre pour créer une règle rapidement depuis une transaction."""
        sel = tree.selection()
        if not sel: return
        
        # Récupération des infos de la ligne sélectionnée
        # values = [id, date, label, amount, category, ...]
        values = tree.item(sel[0])['values']
        current_label = values[2]  # Le libellé complet
        current_cat = values[4]    # La catégorie actuelle

        if not current_cat:
            messagebox.showwarning("Attention", "Veuillez d'abord attribuer une catégorie à cette transaction.")
            return

        # --- FENÊTRE MODALE ---
        win = tk.Toplevel(self.root)
        win.title("⚡️ Créer une Règle Rapide")
        win.geometry("400x250")
        win.configure(bg='white')
        win.transient(self.root)
        win.grab_set()
        
        # Centrage
        win.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - 200
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - 125
        win.geometry(f"+{x}+{y}")

        frame = tk.Frame(win, bg='white', padx=20, pady=20)
        frame.pack(fill="both", expand=True)

        # Instructions
        tk.Label(frame, text="Si le libellé contient :", font=("Arial", 10, "bold"), bg='white').pack(anchor="w")
        
        # Champ Mot-clé (Pré-rempli mais éditable)
        # On essaie de deviner un mot clé "propre" (ex: on prend les 2 premiers mots)
        # Mais l'utilisateur pourra le changer.
        suggested_keyword = " ".join(current_label.split()[:2]) 
        
        e_keyword = ttk.Entry(frame, font=("Arial", 11))
        e_keyword.insert(0, suggested_keyword)
        e_keyword.pack(fill="x", pady=(5, 15))
        e_keyword.select_range(0, tk.END) # Sélectionne le texte pour faciliter la modif
        e_keyword.focus()

        tk.Label(frame, text="Alors mettre la catégorie :", font=("Arial", 10, "bold"), bg='white').pack(anchor="w")
        
        # Liste Catégories
        cats = database.list_categories()
        combo_cat = ttk.Combobox(frame, values=cats, state="readonly", font=("Arial", 11))
        combo_cat.set(current_cat)
        combo_cat.pack(fill="x", pady=(5, 20))

        def save_rule():
            kw = e_keyword.get().strip()
            cat = combo_cat.get()
            
            if not kw or not cat: return
            
            # Ajout en base
            database.add_rule(kw, cat)
            
            # Refresh
            self.refresh_data()
            win.destroy()
            messagebox.showinfo("Succès", f"Règle ajoutée !\nTout ce qui contient '{kw}' ira dans '{cat}'.")

        # Bouton
        ttk.Button(frame, text="Créer la règle", command=save_rule, default="active").pack(fill="x", pady=5)
        win.bind('<Return>', lambda e: save_rule())

    def open_budget_options(self, category, current_amount):
        """Ouvre une fenêtre propre (fond blanc) pour modifier ou supprimer un budget."""
        win = tk.Toplevel(self.root)
        win.title(f"Budget : {category}")
        win.geometry("320x260")
        win.transient(self.root)
        win.grab_set()
        
        # 1. DESIGN : On force le fond blanc pour toute la fenêtre
        win.configure(bg='white')
        
        # Centrage
        win.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - 160
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - 130
        win.geometry(f"+{x}+{y}")

        # Conteneur principal avec marges internes (padding)
        main_frame = tk.Frame(win, bg='white', padx=20, pady=20)
        main_frame.pack(fill="both", expand=True)

        # 2. CONTENU
        # Titre en Gros
        tk.Label(main_frame, text=category, font=("Arial", 14, "bold"), 
                 bg='white', fg='#333').pack(pady=(0, 5))
        
        # Sous-titre
        tk.Label(main_frame, text=f"Actuel : {current_amount:.0f} €", font=("Arial", 10), 
                 bg='white', fg='gray').pack(pady=(0, 20))
        
        # Champ de saisie
        tk.Label(main_frame, text="Nouvel objectif mensuel (€) :", 
                 font=("Arial", 10, "bold"), bg='white', anchor="w").pack(fill="x")
        
        e_amount = ttk.Entry(main_frame, font=("Arial", 12))
        e_amount.insert(0, str(int(current_amount)))
        e_amount.pack(fill="x", pady=(5, 20))
        e_amount.focus()

        # 3. LOGIQUE (inchangée)
        def do_update():
            try:
                new_val = float(e_amount.get().replace(',', '.'))
                database.set_budget(category, new_val)
                self.refresh_data()
                win.destroy()
                messagebox.showinfo("Succès", "Budget mis à jour.")
            except ValueError:
                messagebox.showerror("Erreur", "Montant invalide.")

        def do_delete():
            # Petite confirmation stylée
            if messagebox.askyesno("Suppression", f"Voulez-vous vraiment supprimer\nle budget '{category}' ?"):
                database.delete_budget(category)
                self.refresh_data()
                win.destroy()

        # 4. BOUTONS
        # On met les boutons dans un cadre blanc en bas
        btn_frame = tk.Frame(main_frame, bg='white')
        btn_frame.pack(fill="x")
        
        # Bouton Supprimer (Rouge/Attention - style simple)
        # Sur Mac, ttk.Button est le mieux pour rester natif
        ttk.Button(btn_frame, text="Supprimer", command=do_delete).pack(side="left", expand=True)
        
        # Bouton Valider (Normal)
        # On utilise un Frame vide au milieu pour espacer
        tk.Frame(btn_frame, bg='white', width=10).pack(side="left")
        
        # On peut mettre le bouton Valider en "default" pour qu'il soit bleu (sur mac)
        btn_save = ttk.Button(btn_frame, text="Enregistrer", command=do_update, default="active")
        btn_save.pack(side="right", expand=True)
        
        # Permet de valider avec la touche Entrée
        win.bind('<Return>', lambda e: do_update())
    def set_budget_action(self):
        win = tk.Toplevel(self.root)
        win.title("Définir un Budget Mensuel")
        win.geometry("300x200")
        win.transient(self.root)
        win.grab_set()
        
        win.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - 150
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - 100
        win.geometry(f"+{x}+{y}")

        ttk.Label(win, text="Choisir la catégorie :").pack(pady=(20, 5))
        
        cats = database.list_categories()
        combo_cat = ttk.Combobox(win, values=cats, state="readonly", width=25)
        combo_cat.pack()
        if cats: combo_cat.current(0)

        ttk.Label(win, text="Budget mensuel (€) :").pack(pady=(10, 5))
        entry_amount = ttk.Entry(win, width=15)
        entry_amount.pack()
        entry_amount.focus()

        def save():
            cat = combo_cat.get()
            amount_str = entry_amount.get().strip().replace(',', '.')
            if not cat:
                messagebox.showwarning("Erreur", "Veuillez choisir une catégorie.", parent=win)
                return
            try:
                amount = float(amount_str)
                database.set_budget(cat, amount)
                self.refresh_data()
                win.destroy()
            except ValueError:
                messagebox.showerror("Erreur", "Montant invalide.", parent=win)

        ttk.Button(win, text="Enregistrer", command=save).pack(pady=20)
        win.bind('<Return>', lambda e: save())

    def show_forecast_modal(self):
        history = database.get_monthly_balance_history(12) 
        if not history or len(history) < 3:
            messagebox.showinfo("Information", "Pas assez de données pour une prévision (min 3 mois).")
            return

        months = [h[0] for h in history]
        balances = [h[1] for h in history]

        projections = logic.calculate_trend(balances)
        
        win = tk.Toplevel(self.root)
        win.title("Prévision de Trésorerie (3 mois)")
        win.geometry("600x450")
        
        fig = Figure(figsize=(6, 4), dpi=100)
        ax = fig.add_subplot(111)
        
        x_hist = range(len(balances))
        ax.plot(x_hist, balances, marker='o', linestyle='-', color='blue', label='Réel')
        
        last_real_x = x_hist[-1]
        last_real_val = balances[-1]
        
        x_proj = [last_real_x] + [last_real_x + i for i in range(1, 4)]
        y_proj = [last_real_val] + projections
        
        ax.plot(x_proj, y_proj, marker='x', linestyle='--', color='red', label='Tendance')
        
        ax.axhline(0, color='black', linewidth=0.8, linestyle=':')
        
        ax.set_title("Projection du Solde Net Mensuel")
        ax.set_ylabel("Solde (€)")
        ax.set_xticks(list(x_hist) + list(x_proj[1:]))
        
        labels = [m[5:] for m in months] + ["+1 M", "+2 M", "+3 M"] 
        ax.set_xticklabels(labels, rotation=45)
        
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        canvas = FigureCanvasTkAgg(fig, master=win)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        
        disclaimer = "Note : Estimation basée sur une régression linéaire des 12 derniers mois.\n"\
                     "Ne prend pas en compte les événements exceptionnels futurs."
        lbl = tk.Label(win, text=disclaimer, fg="#555", font=("Arial", 9, "italic"), justify="center", pady=10)
        lbl.pack(side="bottom")

    def update_year_filter(self):
        years = database.get_years_available()
        self.combo_year['values'] = ["Tous"] + years
        if years: self.combo_year.current(0)
        else: self.combo_year.set("Tous")