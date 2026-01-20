import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
from datetime import datetime
import csv
import database
import logic
import matplotlib
matplotlib.use('TkAgg')
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class EcoGestApp:
    def __init__(self, root):
        self.root = root
        self.root.title("EcoGest - Gestion Financière")
        self.root.geometry("1200x850")
        
        style = ttk.Style()
        style.theme_use('clam')
        
        # Styles visuels
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
        paned.add(self.left_frame, weight=1)
        
        ctrl_frame = ttk.Frame(self.left_frame)
        ctrl_frame.pack(fill="x", pady=5)
        
        self.combo_chart_type = ttk.Combobox(ctrl_frame, values=["Dépenses", "Revenus"], state="readonly", width=10)
        self.combo_chart_type.current(0)
        self.combo_chart_type.pack(side="left", padx=5)
        self.combo_chart_type.bind("<<ComboboxSelected>>", lambda e: self.update_chart())
        
        self.combo_viz_style = ttk.Combobox(ctrl_frame, values=["Camembert", "Bâtons"], state="readonly", width=10)
        self.combo_viz_style.current(0)
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
        
        t_id = tree.item(sel[0])['values'][0]
        data = database.get_transaction_by_id(t_id)
        if not data:
            messagebox.showerror("Erreur", "Transaction introuvable.")
            return
            
        current_date, current_label, current_amount, current_cat, current_status, current_note = data[1], data[2], data[3], data[4], data[5], data[6]

        win = tk.Toplevel(self.root)
        win.title(f"Modifier Transaction #{t_id}")
        win.geometry("450x500")
        win.transient(self.root)
        win.grab_set()

        ttk.Label(win, text="Date (AAAA-MM-JJ) :").pack(pady=(15, 5))
        e_date = ttk.Entry(win, width=30)
        e_date.insert(0, current_date)
        e_date.pack()

        ttk.Label(win, text="Libellé :").pack(pady=5)
        e_label = ttk.Entry(win, width=50)
        e_label.insert(0, current_label)
        e_label.pack()

        ttk.Label(win, text="Montant (€) :").pack(pady=5)
        e_amount = ttk.Entry(win, width=20)
        e_amount.insert(0, str(current_amount))
        e_amount.pack()

        ttk.Label(win, text="Catégorie :").pack(pady=5)
        cats = database.list_categories()
        e_cat = ttk.Combobox(win, values=cats, state="readonly", width=28)
        e_cat.set(current_cat)
        e_cat.pack()

        ttk.Label(win, text="Note (Optionnel) :").pack(pady=5)
        e_note = ttk.Entry(win, width=50)
        if current_note: e_note.insert(0, current_note)
        e_note.pack()

        ttk.Label(win, text="Statut :").pack(pady=5)
        e_status = ttk.Entry(win, width=20)
        e_status.insert(0, current_status)
        e_status.config(state="readonly")
        e_status.pack()

        def save_changes():
            new_date = e_date.get().strip()
            try:
                datetime.strptime(new_date, '%Y-%m-%d')
            except ValueError:
                messagebox.showerror("Erreur", "Format de date invalide.\nUtilisez AAAA-MM-JJ")
                return

            try:
                new_amount = float(e_amount.get().replace(',', '.'))
            except ValueError:
                messagebox.showerror("Erreur", "Montant invalide.")
                return

            new_cat = e_cat.get()
            if not new_cat:
                messagebox.showwarning("Attention", "La catégorie est vide.")
                return

            database.update_transaction_fields(
                t_id, new_date, e_label.get().strip(), new_amount, new_cat, e_note.get().strip(), current_status
            )
            
            self.refresh_data()
            win.destroy()
            messagebox.showinfo("Information", "Modification enregistrée.")

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
        """Met à jour les graphiques et les budgets."""
        
        # Nettoyage
        for w in self.chart_container.winfo_children(): w.destroy()
        
        # 1. Lecture de l'état actuel de l'interface
        viz = self.combo_viz_style.get()
        dtype = "expense" if self.combo_chart_type.get() == "Dépenses" else "income"
        y = self.combo_year.get()
        m = self.combo_month.get()
        
        # Filtre de statut
        status_filter = None if self.var_show_all.get() else "VALIDEE"
        
        # Logique Multiplicateur Budgétaire
        if m == "Tous":
            multiplier = 12
        else:
            multiplier = 1
        
        # 2. Création du graphique
        fig = Figure(figsize=(5, 4), dpi=100)
        ax = fig.add_subplot(111)
        
        if viz == "Camembert":
            data = database.get_stats_by_category(year=y, month=m, transaction_type=dtype, status_filter=status_filter)
            
            # Mise à jour des budgets (on utilise les données brutes pour les jauges)
            if dtype == "expense": 
                self.update_budgets_view(data, multiplier)
            else:
                for w in self.budget_container.winfo_children(): w.destroy()
                ttk.Label(self.budget_container, text="Budgets disponibles\npour les dépenses", justify="center", foreground="gray").pack(pady=20)
            
            if data:
                # --- AFFICHAGE COMPLET SANS REGROUPEMENT ---
                # On trie pour avoir les plus gros en premier
                data.sort(key=lambda x: x[1], reverse=True)
                
                labels = [d[0] for d in data]
                values = [d[1] for d in data]

                # Fonction intelligente pour masquer le texte si < 2%
                def smart_autopct(pct):
                    return '%1.1f%%' % pct if pct > 2 else ''
                
                ax.pie(values, labels=labels, autopct=smart_autopct, startangle=90, pctdistance=0.85)
                ax.set_title(f"Répartition {dtype}")
            else:
                ax.text(0.5, 0.5, "Pas de données", ha='center')
        else:
            # Histogramme
            if not y or y == "Tous":
                ax.text(0.5, 0.5, "Choisir une année\npour l'évolution", ha='center')
            else:
                data = database.get_monthly_totals(y, dtype, status_filter=status_filter)
                months = ["J","F","M","A","M","J","J","A","S","O","N","D"]
                ax.bar(months, data, color='skyblue' if dtype == "income" else 'salmon')
                ax.set_title(f"Évolution {dtype} en {y}")
                
        self.canvas = FigureCanvasTkAgg(fig, master=self.chart_container)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

    def update_budgets_view(self, data, multiplier):
        for w in self.budget_container.winfo_children(): w.destroy()
        budgets = database.get_all_budgets()
        expenses = {d[0]: d[1] for d in data} if data else {}
        
        if multiplier > 1:
            ttk.Label(self.budget_container, text=f"Calcul sur {multiplier} mois (Annuel)", font=("Arial", 11, "italic")).pack(pady=(0, 10))
            
        for cat, limit in budgets.items():
            spent = expenses.get(cat, 0)
            total_limit = limit * multiplier
            pct = (spent / total_limit * 100) if total_limit else 0
            
            f = ttk.Frame(self.budget_container, padding=5)
            f.pack(fill="x")
            
            ttk.Label(f, text=f"{cat}: {spent:.0f} / {total_limit:.0f} €").pack(anchor="w")
            
            style = "red.Horizontal.TProgressbar" if spent > total_limit else "green.Horizontal.TProgressbar"
            ttk.Progressbar(f, value=min(pct, 100), style=style).pack(fill="x")

    def set_budget_action(self):
        # Création d'une fenêtre modale personnalisée
        win = tk.Toplevel(self.root)
        win.title("Définir un Budget Mensuel")
        win.geometry("300x200")
        win.transient(self.root)
        win.grab_set()
        
        # Centrer la fenêtre
        win.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - 150
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - 100
        win.geometry(f"+{x}+{y}")

        # 1. Liste déroulante des Catégories
        ttk.Label(win, text="Choisir la catégorie :").pack(pady=(20, 5))
        
        cats = database.list_categories()
        combo_cat = ttk.Combobox(win, values=cats, state="readonly", width=25)
        combo_cat.pack()
        if cats: combo_cat.current(0)

        # 2. Champ Montant
        ttk.Label(win, text="Budget mensuel (€) :").pack(pady=(10, 5))
        entry_amount = ttk.Entry(win, width=15)
        entry_amount.pack()
        entry_amount.focus()

        # 3. Fonction de sauvegarde
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

        # 4. Bouton Valider
        ttk.Button(win, text="Enregistrer", command=save).pack(pady=20)
        
        win.bind('<Return>', lambda e: save())

    def show_forecast_modal(self):
        # 1. Récupération des données
        history = database.get_monthly_balance_history(12) 
        if not history or len(history) < 3:
            messagebox.showinfo("Information", "Pas assez de données pour une prévision (min 3 mois).")
            return

        months = [h[0] for h in history]
        balances = [h[1] for h in history]

        # 2. Calcul mathématique
        projections = logic.calculate_trend(balances)
        
        # 3. Création de la fenêtre
        win = tk.Toplevel(self.root)
        win.title("Prévision de Trésorerie (3 mois)")
        win.geometry("600x450")
        
        # 4. Graphique
        fig = Figure(figsize=(6, 4), dpi=100)
        ax = fig.add_subplot(111)
        
        # Données Historiques
        x_hist = range(len(balances))
        ax.plot(x_hist, balances, marker='o', linestyle='-', color='blue', label='Réel')
        
        # Données Projetées (On relie le dernier point réel au premier projeté)
        last_real_x = x_hist[-1]
        last_real_val = balances[-1]
        
        x_proj = [last_real_x] + [last_real_x + i for i in range(1, 4)]
        y_proj = [last_real_val] + projections
        
        ax.plot(x_proj, y_proj, marker='x', linestyle='--', color='red', label='Tendance')
        
        # Ligne Zéro
        ax.axhline(0, color='black', linewidth=0.8, linestyle=':')
        
        ax.set_title("Projection du Solde Net Mensuel")
        ax.set_ylabel("Solde (€)")
        ax.set_xticks(list(x_hist) + list(x_proj[1:]))
        
        # Labels axe X
        labels = [m[5:] for m in months] + ["+1 M", "+2 M", "+3 M"] 
        ax.set_xticklabels(labels, rotation=45)
        
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        canvas = FigureCanvasTkAgg(fig, master=win)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        
        # 5. Disclaimer
        disclaimer = "Note : Estimation basée sur une régression linéaire des 12 derniers mois.\n"\
                     "Ne prend pas en compte les événements exceptionnels futurs."
        lbl = tk.Label(win, text=disclaimer, fg="#555", font=("Arial", 9, "italic"), justify="center", pady=10)
        lbl.pack(side="bottom")

    def update_year_filter(self):
        years = database.get_years_available()
        self.combo_year['values'] = ["Tous"] + years
        if years: self.combo_year.current(0)
        else: self.combo_year.set("Tous")