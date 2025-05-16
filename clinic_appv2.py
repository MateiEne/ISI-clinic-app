# --- START OF FILE clinic_app_modern.py ---

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import json # Pentru a lucra cu fisiere JSON
from jsonschema import validate, exceptions as json_schema_exceptions # Pentru a valida JSON cu o schema
from lxml import etree # Librarie puternica pentru a lucra cu fisiere XML, XSD (schema XML) si XSLT (transformare XML)
import os # Pentru a lucra cu cai de fisiere (nume fisier, etc.)
import webbrowser # Pentru a deschide fisiere HTML in browser
import traceback # Pentru afisarea erorilor detaliate
import re # Adaugat pentru extragerea ID-ului medicului din Combobox

# --- Nume Fisiere Implicite ---
DEFAULT_XML = "consultatii.xml"
DEFAULT_XSD = "consultatii.xsd"
DEFAULT_JSON = "consultatii.json"
DEFAULT_JSON_SCHEMA = "consultatii.schema.json"
DEFAULT_XSL = "consultatii.xsl"
HTML_OUTPUT = "consultatii_output.html"

# --- Constante pentru Stil Modern ---
FONT_FAMILY = "Segoe UI"
FONT_SIZE_NORMAL = 10
FONT_SIZE_HEADER = 12

COLOR_BACKGROUND = "#F4F6F6"  # Fundal general mai deschis
COLOR_FRAME_BG = "#EAECEE"    # Fundal pentru cadre
COLOR_TEXT = "#2C3E50"        # Text principal (albastru inchis/gri)
COLOR_ACCENT = "#3498DB"      # Albastru pentru accente (butoane, selectii)
COLOR_ACCENT_HOVER = "#2980B9" # Albastru mai inchis pentru hover
COLOR_BUTTON_TEXT = "#FFFFFF" # Text alb pentru butoane
COLOR_DISABLED_FG = "#95A5A6" # Text pentru elemente dezactivate
COLOR_DISABLED_BG = "#BDC3C7" # Fundal pentru butoane dezactivate

COLOR_TREEVIEW_HEADER_BG = "#D5DBDB"
COLOR_TREEVIEW_EVEN_ROW = "#FEFEFE" # Aproape alb
COLOR_TREEVIEW_ODD_ROW = "#F2F4F4"  # Gri foarte deschis

class ClinicApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Evidenta Consultatii Clinica - Modern")
        self.root.geometry("1100x850") # Dimensiune usor marita pentru noul stil
        self.root.configure(bg=COLOR_BACKGROUND)

        self.xml_tree = None
        self.json_data = None
        self.xml_file_path = DEFAULT_XML
        self.json_file_path = DEFAULT_JSON

        self.setup_styles() # Seteaza stilurile ttk
        self.create_widgets()

    def setup_styles(self):
        # Functie pentru a configura stilurile ttk pentru un aspect modern
        style = ttk.Style()
        style.theme_use('clam') # 'clam', 'alt', 'default', 'classic'

        # Stiluri Globale
        style.configure(".", background=COLOR_FRAME_BG, foreground=COLOR_TEXT, font=(FONT_FAMILY, FONT_SIZE_NORMAL))
        style.configure("TFrame", background=COLOR_FRAME_BG)
        style.configure("TLabel", background=COLOR_FRAME_BG, foreground=COLOR_TEXT, font=(FONT_FAMILY, FONT_SIZE_NORMAL))
        style.configure("TEntry", fieldbackground=COLOR_BUTTON_TEXT, foreground=COLOR_TEXT, insertcolor=COLOR_TEXT, font=(FONT_FAMILY, FONT_SIZE_NORMAL))
        style.configure("TCombobox", fieldbackground=COLOR_BUTTON_TEXT, foreground=COLOR_TEXT, font=(FONT_FAMILY, FONT_SIZE_NORMAL))
        style.map("TCombobox",
                    fieldbackground=[('readonly', COLOR_BUTTON_TEXT)],
                    selectbackground=[('readonly', COLOR_ACCENT)],
                    selectforeground=[('readonly', COLOR_BUTTON_TEXT)])

        # Stiluri pentru Butoane
        style.configure("TButton",
                        background=COLOR_ACCENT,
                        foreground=COLOR_BUTTON_TEXT,
                        font=(FONT_FAMILY, FONT_SIZE_NORMAL, "bold"),
                        padding=(10, 5),
                        relief="flat",
                        borderwidth=0)
        style.map("TButton",
                  background=[('active', COLOR_ACCENT_HOVER), ('disabled', COLOR_DISABLED_BG)],
                  foreground=[('disabled', COLOR_DISABLED_FG)])

        # Stil pentru Butoane "Accent" (ex: Salvare)
        style.configure("Accent.TButton", background="#2ECC71", foreground=COLOR_BUTTON_TEXT) # Verde pentru salvare
        style.map("Accent.TButton", background=[('active', "#27AE60")])

        # Stil pentru Notebook (Tab-uri)
        style.configure("TNotebook", background=COLOR_BACKGROUND, borderwidth=0)
        style.configure("TNotebook.Tab",
                        background=COLOR_FRAME_BG,
                        foreground=COLOR_TEXT,
                        font=(FONT_FAMILY, FONT_SIZE_NORMAL),
                        padding=(10, 5),
                        relief="flat",
                        borderwidth=0)
        style.map("TNotebook.Tab",
                  background=[('selected', COLOR_ACCENT), ('active', COLOR_ACCENT_HOVER)],
                  foreground=[('selected', COLOR_BUTTON_TEXT), ('active', COLOR_BUTTON_TEXT)])

        # Stil pentru Treeview
        style.configure("Treeview.Heading",
                        background=COLOR_TREEVIEW_HEADER_BG,
                        foreground=COLOR_TEXT,
                        font=(FONT_FAMILY, FONT_SIZE_NORMAL, "bold"),
                        relief="flat",
                        padding=5)
        style.map("Treeview.Heading", background=[('active', COLOR_ACCENT_HOVER), ('pressed', COLOR_ACCENT)])

        style.configure("Treeview",
                        background=COLOR_BUTTON_TEXT, # Fundalul general al listei
                        fieldbackground=COLOR_BUTTON_TEXT, # Fundalul campurilor individuale
                        foreground=COLOR_TEXT,
                        rowheight=28, # Inaltime rand mai mare
                        font=(FONT_FAMILY, FONT_SIZE_NORMAL))
        style.map("Treeview",
                  background=[('selected', COLOR_ACCENT)],
                  foreground=[('selected', COLOR_BUTTON_TEXT)])

        # Stil pentru LabelFrame
        style.configure("TLabelframe", background=COLOR_FRAME_BG, bordercolor=COLOR_ACCENT, borderwidth=1, relief="solid")
        style.configure("TLabelframe.Label",
                        background=COLOR_FRAME_BG,
                        foreground=COLOR_ACCENT, # Culoare accent pentru titlul LabelFrame
                        font=(FONT_FAMILY, FONT_SIZE_HEADER, "bold"))

        # Stil pentru Status Label
        style.configure("Status.TLabel",
                        background=COLOR_FRAME_BG,
                        foreground=COLOR_TEXT,
                        font=(FONT_FAMILY, FONT_SIZE_NORMAL -1),
                        padding=8,
                        anchor="w",
                        relief="flat",
                        borderwidth=0)

    def create_widgets(self):
        self.paned_window = ttk.PanedWindow(self.root, orient=tk.VERTICAL)
        self.paned_window.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        # --- Cadru Superior pentru Controale --- 
        # Am adaugat un cadru intermediar pentru a centra butoanele mai bine
        top_controls_container = ttk.Frame(self.paned_window, padding="10") # Foloseste stilul implicit TFrame
        self.paned_window.add(top_controls_container, weight=0)

        self.controls_frame = ttk.Frame(top_controls_container) # Fara padding specific aici, se va centra
        self.controls_frame.pack(pady=10)

        # --- Butoane de Control --- 
        # Le asezam intr-un grid mai compact
        self.load_xml_button = ttk.Button(self.controls_frame, text="Incarca XML", command=self.load_xml)
        self.load_xml_button.grid(row=0, column=0, padx=8, pady=8, sticky="ew")
        self.validate_xsd_button = ttk.Button(self.controls_frame, text="Valideaza XML (XSD)", command=self.validate_xsd, state=tk.DISABLED)
        self.validate_xsd_button.grid(row=0, column=1, padx=8, pady=8, sticky="ew")
        self.show_xslt_button = ttk.Button(self.controls_frame, text="Afiseaza (XSLT)", command=self.display_xslt, state=tk.DISABLED)
        self.show_xslt_button.grid(row=0, column=2, padx=8, pady=8, sticky="ew")
        
        self.load_json_button = ttk.Button(self.controls_frame, text="Incarca JSON", command=self.load_json)
        self.load_json_button.grid(row=1, column=0, padx=8, pady=8, sticky="ew")
        self.validate_json_button = ttk.Button(self.controls_frame, text="Valideaza JSON", command=self.validate_json_schema, state=tk.DISABLED)
        self.validate_json_button.grid(row=1, column=1, padx=8, pady=8, sticky="ew")
        self.save_changes_button = ttk.Button(self.controls_frame, text="Salveaza Modificari", command=self.save_changes, state=tk.DISABLED, style="Accent.TButton") # Stil special
        self.save_changes_button.grid(row=1, column=2, padx=8, pady=8, sticky="ew")

        # --- Notebook (Tab-uri) pentru afisarea datelor ---
        self.notebook_frame = ttk.Frame(self.paned_window, padding="0") # Fara padding exterior, il are notebook-ul
        self.paned_window.add(self.notebook_frame, weight=1)

        self.notebook = ttk.Notebook(self.notebook_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=(10,0)) # Spatiu deasupra notebook-ului

        # Creare tab-uri si Treeview-uri pentru fiecare categorie
        self.pacienti_tree = self.create_category_treeview("Pacienti",
            {"#0": ("ID Pacient", 150), "col1": ("Nume", 150), "col2": ("Prenume", 150), "col3": ("Data Nasterii", 120), "col4": ("Telefon", 120)}
        )
        self.medici_tree = self.create_category_treeview("Medici",
            {"#0": ("ID Medic", 150), "col1": ("Nume", 150), "col2": ("Prenume", 150), "col3": ("Specializare", 180)}
        )
        self.consultatii_tree = self.create_category_treeview("Consultatii",
            {"#0": ("ID Consultatie", 120), "col1": ("Data", 100), "col2": ("Ora", 80), "col3": ("ID Pacient", 100), "col4": ("ID Medic", 100), "col5": ("Simptome", 200), "col6": ("Diagnostic", 250), "col7": ("Tratament", 250)}
        )

        # --- Frame-ul de Jos pentru CRUD si Status ---
        self.bottom_frame = ttk.Frame(self.paned_window, padding="10")
        self.paned_window.add(self.bottom_frame, weight=0)

        crud_frame = ttk.LabelFrame(self.bottom_frame, text="Operatii Date (In-Memory)", padding="15")
        crud_frame.pack(fill=tk.X, pady=(0, 10))

        # Randul 0: Cautare Consultatie
        ttk.Label(crud_frame, text="Cauta ID Consultatie:").grid(row=0, column=0, padx=5, pady=8, sticky="w")
        self.search_entry = ttk.Entry(crud_frame, width=20)
        self.search_entry.grid(row=0, column=1, padx=5, pady=8, sticky="ew")
        self.search_button = ttk.Button(crud_frame, text="Cauta", command=self.search_consultation, state=tk.DISABLED)
        self.search_button.grid(row=0, column=2, padx=5, pady=8, sticky="ew")

        # Randul 1: Operatii Consultatii
        self.add_button = ttk.Button(crud_frame, text="Adauga Consultatie Noua", command=self.add_consultation_dialog, state=tk.DISABLED)
        self.add_button.grid(row=1, column=0, columnspan=2, padx=5, pady=8, sticky="ew")
        self.delete_button = ttk.Button(crud_frame, text="Sterge Consultatia Selectata", command=self.delete_consultation, state=tk.DISABLED)
        self.delete_button.grid(row=1, column=2, padx=5, pady=8, sticky="ew")

        # Randul 2: Operatii Medici
        self.add_medic_button = ttk.Button(crud_frame, text="Adauga Medic Nou", command=self.add_medic_dialog, state=tk.DISABLED)
        self.add_medic_button.grid(row=2, column=0, columnspan=3, padx=5, pady=8, sticky="ew")

        crud_frame.columnconfigure(0, weight=1)
        crud_frame.columnconfigure(1, weight=1)
        crud_frame.columnconfigure(2, weight=1)

        self.status_label = ttk.Label(self.bottom_frame, text="Status: Asteptare incarcare fisier...", style="Status.TLabel")
        self.status_label.pack(fill=tk.X, side=tk.BOTTOM, pady=(5,0))

    def create_category_treeview(self, tab_name, columns_config):
        tab_frame = ttk.Frame(self.notebook, padding="10") # Padding in interiorul tab-ului
        self.notebook.add(tab_frame, text=tab_name)

        tree = ttk.Treeview(tab_frame, style="Treeview") # Aplica stilul Treeview
        
        # Adauga tag-uri pentru culori alternante ale randurilor
        tree.tag_configure('oddrow', background=COLOR_TREEVIEW_ODD_ROW, foreground=COLOR_TEXT)
        tree.tag_configure('evenrow', background=COLOR_TREEVIEW_EVEN_ROW, foreground=COLOR_TEXT)
        
        tree_cols = [key for key in columns_config if key != "#0"]
        tree["columns"] = tuple(tree_cols)

        col_info = columns_config.get("#0", ("ID", 100))
        tree.heading("#0", text=col_info[0])
        tree.column("#0", anchor=tk.W, width=col_info[1], stretch=tk.NO)

        for col_id in tree_cols:
            col_info = columns_config[col_id]
            tree.heading(col_id, text=col_info[0])
            tree.column(col_id, anchor=tk.W, width=col_info[1], stretch=tk.YES)

        # Scrollbar-uri stilizate implicit de tema ttk
        tree_ysb = ttk.Scrollbar(tab_frame, orient=tk.VERTICAL, command=tree.yview)
        tree_xsb = ttk.Scrollbar(tab_frame, orient=tk.HORIZONTAL, command=tree.xview)
        tree.configure(yscrollcommand=tree_ysb.set, xscrollcommand=tree_xsb.set)
        
        tree_ysb.pack(side=tk.RIGHT, fill=tk.Y)
        tree_xsb.pack(side=tk.BOTTOM, fill=tk.X)
        tree.pack(fill=tk.BOTH, expand=True)
        
        return tree

    # --- Gestiunea Fisierelor ---
    def load_xml(self):
        self.clear_all_displays() 
        filepath = filedialog.askopenfilename(
            title="Selecteaza fisier XML",
            filetypes=[("XML Files", "*.xml"), ("All Files", "*.*")],
            initialfile=self.xml_file_path
        )
        if not filepath:
            self.update_status("Incarcare XML anulata.")
            return
        try:
            parser = etree.XMLParser(remove_blank_text=True)
            self.xml_tree = etree.parse(filepath, parser)
            self.xml_file_path = filepath
            self.json_data = None 
            self.populate_all_trees_from_xml() 
            self.update_status(f"Fisier XML incarcat: {os.path.basename(filepath)}")
            self.validate_xsd_button.config(state=tk.NORMAL)
            self.show_xslt_button.config(state=tk.NORMAL)
            self.validate_json_button.config(state=tk.DISABLED)
            self.search_button.config(state=tk.NORMAL)
            self.add_button.config(state=tk.NORMAL)
            self.delete_button.config(state=tk.NORMAL)
            self.add_medic_button.config(state=tk.NORMAL)
            self.save_changes_button.config(state=tk.NORMAL)
        except etree.XMLSyntaxError as e:
            messagebox.showerror("Eroare Parsare XML", f"Eroare la parsarea XML:\n{e}")
            self.xml_tree = None
            self.update_status("Eroare la incarcare XML.")
        except FileNotFoundError:
            messagebox.showerror("Eroare Fisier", f"Fisierul XML nu a fost gasit:\n{filepath}")
            self.xml_tree = None
            self.update_status("Eroare la incarcare XML.")
        except Exception as e:
             messagebox.showerror("Eroare Necunoscuta", f"A aparut o eroare la incarcarea XML:\n{e}")
             self.xml_tree = None
             self.update_status("Eroare la incarcare XML.")

    def load_json(self):
        self.clear_all_displays()
        filepath = filedialog.askopenfilename(
            title="Selecteaza fisier JSON",
            filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")],
             initialfile=self.json_file_path
        )
        if not filepath:
            self.update_status("Incarcare JSON anulata.")
            return
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                self.json_data = json.load(f)
            self.json_file_path = filepath
            self.xml_tree = None 
            self.populate_all_trees_from_json() 
            self.update_status(f"Fisier JSON incarcat: {os.path.basename(filepath)}")
            self.validate_json_button.config(state=tk.NORMAL)
            self.validate_xsd_button.config(state=tk.DISABLED)
            self.show_xslt_button.config(state=tk.DISABLED)
            self.search_button.config(state=tk.NORMAL)
            self.add_button.config(state=tk.NORMAL)
            self.delete_button.config(state=tk.NORMAL)
            self.add_medic_button.config(state=tk.NORMAL)
            self.save_changes_button.config(state=tk.NORMAL)
        except json.JSONDecodeError as e:
            messagebox.showerror("Eroare Parsare JSON", f"Eroare la parsarea JSON:\n{e}")
            self.json_data = None
            self.update_status("Eroare la incarcare JSON.")
        except FileNotFoundError:
            messagebox.showerror("Eroare Fisier", f"Fisierul JSON nu a fost gasit:\n{filepath}")
            self.json_data = None
            self.update_status("Eroare la incarcare JSON.")
        except Exception as e:
             messagebox.showerror("Eroare Necunoscuta", f"A aparut o eroare la incarcarea JSON:\n{e}")
             self.json_data = None
             self.update_status("Eroare la incarcare JSON.")

    def save_changes(self):
        if self.xml_tree is not None and self.xml_file_path:
            try:
                self.xml_tree.write(self.xml_file_path, pretty_print=True, xml_declaration=True, encoding='UTF-8')
                self.update_status(f"Modificari salvate in {os.path.basename(self.xml_file_path)}")
                messagebox.showinfo("Salvare XML", "Modificarile XML au fost salvate cu succes.")
            except Exception as e:
                messagebox.showerror("Eroare Salvare XML", f"Nu s-a putut salva fisierul XML:\n{e}")
                self.update_status("Eroare la salvare XML.")
        elif self.json_data is not None and self.json_file_path:
            try:
                with open(self.json_file_path, 'w', encoding='utf-8') as f:
                    json.dump(self.json_data, f, indent=2, ensure_ascii=False)
                self.update_status(f"Modificari salvate in {os.path.basename(self.json_file_path)}")
                messagebox.showinfo("Salvare JSON", "Modificarile JSON au fost salvate cu succes.")
            except Exception as e:
                messagebox.showerror("Eroare Salvare JSON", f"Nu s-a putut salva fisierul JSON:\n{e}")
                self.update_status("Eroare la salvare JSON.")
        else:
             messagebox.showwarning("Salvare Imposibila", "Niciun fisier XML sau JSON nu este incarcat pentru a salva.")
             self.update_status("Salvare esuata - niciun fisier incarcat.")

    # --- Afisare/Populare Treeview-uri ---
    def clear_tree_items(self, tree_widget):
        for item in tree_widget.get_children():
            tree_widget.delete(item)

    def clear_all_displays(self):
        self.clear_tree_items(self.pacienti_tree)
        self.clear_tree_items(self.medici_tree)
        self.clear_tree_items(self.consultatii_tree)
        
        self.xml_tree = None
        self.json_data = None
        self.validate_xsd_button.config(state=tk.DISABLED)
        self.show_xslt_button.config(state=tk.DISABLED)
        self.validate_json_button.config(state=tk.DISABLED)
        self.search_button.config(state=tk.DISABLED)
        self.add_button.config(state=tk.DISABLED)
        self.delete_button.config(state=tk.DISABLED)
        self.add_medic_button.config(state=tk.DISABLED)
        self.save_changes_button.config(state=tk.DISABLED)
        self.update_status("Afisaj curatat.")

    def populate_all_trees_from_xml(self):
        if self.xml_tree is None: return
        root_element = self.xml_tree.getroot()
        if root_element is None or root_element.tag != 'Clinica':
            messagebox.showwarning("XML Invalid", "Elementul radacina <Clinica> nu a fost gasit.")
            return

        self.clear_tree_items(self.pacienti_tree)
        count = 0 # Contor pentru a alterna culorile randurilor
        for pacient in root_element.xpath('//Pacient'):
            pid = pacient.get('id', 'N/A')
            nume = pacient.findtext('Nume', default='')
            prenume = pacient.findtext('Prenume', default='')
            dn = pacient.findtext('DataNasterii', default='')
            tel = pacient.findtext('Telefon', default='')
            tag = 'evenrow' if count % 2 == 0 else 'oddrow' # Aplica tag-ul corespunzator
            self.pacienti_tree.insert("", tk.END, text=pid, values=(nume, prenume, dn, tel), tags=(tag,))
            count +=1

        self.clear_tree_items(self.medici_tree)
        count = 0
        for medic in root_element.xpath('//Medic'):
            mid = medic.get('id', 'N/A')
            nume = medic.findtext('Nume', default='')
            prenume = medic.findtext('Prenume', default='')
            spec = medic.findtext('Specializare', default='')
            tag = 'evenrow' if count % 2 == 0 else 'oddrow'
            self.medici_tree.insert("", tk.END, text=mid, values=(nume, prenume, spec), tags=(tag,))
            count +=1

        self.clear_tree_items(self.consultatii_tree)
        count = 0
        for consult in root_element.xpath('//Consultatie'):
            cid = consult.get('id_consultatie', 'N/A')
            pid_ref = consult.get('id_pacient_ref', 'N/A')
            mid_ref = consult.get('id_medic_ref', 'N/A')
            data = consult.findtext('Data', default='')
            ora = consult.findtext('Ora', default='')
            simptome = consult.findtext('Simptome', default='')
            diag_cod = consult.xpath('./Diagnostic/CodICD10/text()')[0] if consult.xpath('./Diagnostic/CodICD10/text()') else ''
            diag_desc = consult.xpath('./Diagnostic/Descriere/text()')[0] if consult.xpath('./Diagnostic/Descriere/text()') else ''
            diag_str = f"{diag_cod}: {diag_desc}" if diag_cod or diag_desc else ""
            trat_ind = consult.xpath('./Tratament/Indicatii/text()')[0] if consult.xpath('./Tratament/Indicatii/text()') else ''
            meds = [f"{med.get('nume', '')}({med.get('doza', 'N/A')})" for med in consult.xpath('./Tratament/Medicamente/Medicament')]
            trat_str = f"Indicatii: {trat_ind}" + (f" | Meds: {', '.join(meds)}" if meds else "")
            tag = 'evenrow' if count % 2 == 0 else 'oddrow'
            self.consultatii_tree.insert("", tk.END, iid=cid, text=cid, values=(data, ora, pid_ref, mid_ref, simptome, diag_str, trat_str), tags=(tag,))
            count +=1

    def populate_all_trees_from_json(self):
        if self.json_data is None or 'clinica' not in self.json_data:
            messagebox.showwarning("JSON Invalid", "Structura JSON invalida sau cheia 'clinica' lipseste.")
            return
        clinica_data = self.json_data['clinica']

        self.clear_tree_items(self.pacienti_tree)
        count = 0
        for pacient in clinica_data.get('pacienti', []):
            pid = pacient.get('id', 'N/A')
            nume = pacient.get('nume', '')
            prenume = pacient.get('prenume', '')
            dn = pacient.get('dataNasterii', '')
            tel = pacient.get('telefon', '')
            tag = 'evenrow' if count % 2 == 0 else 'oddrow'
            self.pacienti_tree.insert("", tk.END, text=pid, values=(nume, prenume, dn, tel), tags=(tag,))
            count += 1

        self.clear_tree_items(self.medici_tree)
        count = 0
        for medic in clinica_data.get('medici', []):
            mid = medic.get('id', 'N/A')
            nume = medic.get('nume', '')
            prenume = medic.get('prenume', '')
            spec = medic.get('specializare', '')
            tag = 'evenrow' if count % 2 == 0 else 'oddrow'
            self.medici_tree.insert("", tk.END, text=mid, values=(nume, prenume, spec), tags=(tag,))
            count += 1

        self.clear_tree_items(self.consultatii_tree)
        count = 0
        for consult in clinica_data.get('consultatii', []):
            cid = consult.get('id_consultatie', 'N/A')
            pid_ref = consult.get('id_pacient_ref', 'N/A')
            mid_ref = consult.get('id_medic_ref', 'N/A')
            data = consult.get('data', '')
            ora = consult.get('ora', '')
            simptome = consult.get('simptome', '')
            diag = consult.get('diagnostic', {})
            diag_cod = diag.get('codICD10', '')
            diag_desc = diag.get('descriere', '')
            diag_str = f"{diag_cod}: {diag_desc}" if diag_cod or diag_desc else ""
            trat = consult.get('tratament', {})
            trat_ind = trat.get('indicatii', '')
            meds_list = trat.get('medicamente', [])
            meds = [f"{med.get('nume', '')}({med.get('doza', 'N/A')})" for med in meds_list]
            trat_str = f"Indicatii: {trat_ind}" + (f" | Meds: {', '.join(meds)}" if meds else "")
            tag = 'evenrow' if count % 2 == 0 else 'oddrow'
            self.consultatii_tree.insert("", tk.END, iid=cid, text=cid, values=(data, ora, pid_ref, mid_ref, simptome, diag_str, trat_str), tags=(tag,))
            count += 1

    # --- Validare ---
    def validate_xsd(self):
        if self.xml_tree is None:
            messagebox.showwarning("Validare Imposibila", "Niciun fisier XML nu este incarcat.")
            return
        xsd_path = DEFAULT_XSD
        if not os.path.exists(xsd_path):
             xsd_path_ask = filedialog.askopenfilename(
                title="Selecteaza fisier XSD", filetypes=[("XSD Schema Files", "*.xsd"), ("All Files", "*.*")], initialfile=DEFAULT_XSD)
             if not xsd_path_ask:
                 self.update_status("Validare XSD anulata - schema lipsa.")
                 return
             xsd_path = xsd_path_ask
        try:
            xmlschema_doc = etree.parse(xsd_path)
            xmlschema = etree.XMLSchema(xmlschema_doc)
            xmlschema.assertValid(self.xml_tree)
            messagebox.showinfo("Validare XSD", "Fisierul XML este valid conform schemei XSD.")
            self.update_status("XML Valid (XSD).")
        except etree.XMLSchemaParseError as e:
            messagebox.showerror("Eroare Schema XSD", f"Schema XSD este invalida sau nu a putut fi parsata:\n{e}")
            self.update_status("Eroare la parsarea schemei XSD.")
        except etree.DocumentInvalid as e:
            messagebox.showerror("Validare XSD Esuata", f"Fisierul XML NU este valid:\n{e}")
            self.update_status("XML Invalid (XSD).")
        except FileNotFoundError:
             messagebox.showerror("Eroare Fisier", f"Fisierul XSD nu a fost gasit:\n{xsd_path}")
             self.update_status("Validare XSD esuata - schema lipsa.")
        except Exception as e:
            messagebox.showerror("Eroare Necunoscuta", f"A aparut o eroare la validarea XSD:\n{e}")
            self.update_status("Eroare validare XSD.")

    def validate_json_schema(self):
        if self.json_data is None:
            messagebox.showwarning("Validare Imposibila", "Niciun fisier JSON nu este incarcat.")
            return
        schema_path = DEFAULT_JSON_SCHEMA
        if not os.path.exists(schema_path):
            schema_path_ask = filedialog.askopenfilename(
                title="Selecteaza fisier JSON Schema", filetypes=[("JSON Schema Files", "*.json"), ("All Files", "*.*")], initialfile=DEFAULT_JSON_SCHEMA)
            if not schema_path_ask:
                self.update_status("Validare JSON anulata - schema lipsa.")
                return
            schema_path = schema_path_ask
        try:
            with open(schema_path, 'r', encoding='utf-8') as f_schema:
                schema = json.load(f_schema)
            validate(instance=self.json_data, schema=schema)
            messagebox.showinfo("Validare JSON Schema", "Fisierul JSON este valid conform schemei.")
            self.update_status("JSON Valid (Schema).")
        except json_schema_exceptions.ValidationError as e:
            error_details = f"Mesaj: {e.message}\nCale: {list(e.path)}\nSchema: {e.schema_path}"
            messagebox.showerror("Validare JSON Esuata", f"Fiierul JSON NU este valid:\n{error_details}")
            self.update_status("JSON Invalid (Schema).")
        except json.JSONDecodeError as e:
             messagebox.showerror("Eroare Schema JSON", f"Schema JSON este invalida sau nu a putut fi parsata:\n{e}")
             self.update_status("Eroare la parsarea schemei JSON.")
        except FileNotFoundError:
             messagebox.showerror("Eroare Fisier", f"Fisierul JSON Schema nu a fost gasit:\n{schema_path}")
             self.update_status("Validare JSON esuata - schema lipsa.")
        except Exception as e:
            messagebox.showerror("Eroare Necunoscuta", f"A aparut o eroare la validarea JSON:\n{e}")
            self.update_status("Eroare validare JSON.")

    # --- Transformare XSLT ---
    def display_xslt(self):
        if self.xml_tree is None:
            messagebox.showwarning("Transformare Imposibila", "Niciun fisier XML nu este incarcat.")
            return
        xsl_path = DEFAULT_XSL
        if not os.path.exists(xsl_path):
             xsl_path_ask = filedialog.askopenfilename(
                title="Selecteaza fisier XSLT", filetypes=[("XSLT Stylesheet Files", "*.xsl;*.xslt"), ("All Files", "*.*")], initialfile=DEFAULT_XSL)
             if not xsl_path_ask:
                 self.update_status("Transformare XSLT anulata - fisier lipsa.")
                 return
             xsl_path = xsl_path_ask
        try:
            xslt_doc = etree.parse(xsl_path)
            transformer = etree.XSLT(xslt_doc)
            html_result_tree = transformer(self.xml_tree)
            html_content = etree.tostring(html_result_tree, pretty_print=True, method="html", encoding='UTF-8').decode('utf-8')
            with open(HTML_OUTPUT, 'w', encoding='utf-8') as f:
                f.write(html_content)
            webbrowser.open(f'file://{os.path.realpath(HTML_OUTPUT)}')
            self.update_status(f"Rezultat XSLT salvat in {HTML_OUTPUT} si deschis.")
        except etree.XSLTParseError as e:
             messagebox.showerror("Eroare XSLT", f"Fisierul XSLT este invalid sau nu a putut fi parsat:\n{e}")
             self.update_status("Eroare la parsarea XSLT.")
        except etree.XSLTApplyError as e:
             messagebox.showerror("Eroare Aplicare XSLT", f"Eroare la aplicarea transformarii XSLT:\n{e}")
             self.update_status("Eroare la aplicarea XSLT.")
        except FileNotFoundError:
             messagebox.showerror("Eroare Fisier", f"Fisierul XSLT nu a fost gasit:\n{xsl_path}")
             self.update_status("Transformare XSLT esuata - fisier lipsa.")
        except Exception as e:
            messagebox.showerror("Eroare Necunoscuta", f"A aparut o eroare la transformarea XSLT:\n{e}")
            self.update_status("Eroare transformare XSLT.")

    # --- Operatii CRUD ---
    def find_next_consultation_id(self):
        max_id_num = 0
        if self.xml_tree is not None:
            ids = self.xml_tree.xpath('//Consultatie/@id_consultatie')
            for id_val in ids:
                try: num = int(id_val[1:]); max_id_num = max(max_id_num, num)
                except ValueError: continue
        elif self.json_data is not None:
             consultations = self.json_data.get('clinica', {}).get('consultatii', [])
             for consult in consultations:
                 id_val = consult.get('id_consultatie')
                 if id_val and id_val.startswith('C'):
                    try: num = int(id_val[1:]); max_id_num = max(max_id_num, num)
                    except ValueError: continue
        return f"C{max_id_num + 1:03d}"

    def find_next_medic_id(self):
        max_id_num = 0
        if self.xml_tree is not None:
            ids = self.xml_tree.xpath('//Medic/@id')
            for id_val in ids:
                if id_val.startswith('M'):
                    try:
                        num = int(id_val[1:])
                        max_id_num = max(max_id_num, num)
                    except ValueError:
                        continue
        elif self.json_data is not None:
            medici_list = self.json_data.get('clinica', {}).get('medici', [])
            for medic in medici_list:
                id_val = medic.get('id')
                if id_val and id_val.startswith('M'):
                    try:
                        num = int(id_val[1:])
                        max_id_num = max(max_id_num, num)
                    except ValueError:
                        continue
        return f"M{max_id_num + 1:03d}"

    def get_medic_choices(self):
        medic_choices = []
        if self.xml_tree is not None:
            root_element = self.xml_tree.getroot()
            if root_element is not None:
                for medic in root_element.xpath('//Medic'):
                    mid = medic.get('id', 'N/A')
                    nume = medic.findtext('Nume', default='')
                    prenume = medic.findtext('Prenume', default='')
                    if mid != 'N/A' and (nume or prenume):
                        medic_choices.append(f"{nume} {prenume} ({mid})")
        elif self.json_data is not None:
            clinica_data = self.json_data.get('clinica', {})
            for medic in clinica_data.get('medici', []):
                mid = medic.get('id', 'N/A')
                nume = medic.get('nume', '')
                prenume = medic.get('prenume', '')
                if mid != 'N/A' and (nume or prenume):
                    medic_choices.append(f"{nume} {prenume} ({mid})")
        
        if not medic_choices:
            return ["Niciun medic disponibil"]
        return sorted(medic_choices)

    def _create_form_dialog(self, title, field_definitions, next_id_label_text, next_id_value, submit_command_text, submit_callback):
        # Functie helper generica pentru crearea dialogurilor de formular
        dialog = tk.Toplevel(self.root)
        dialog.title(title)
        dialog.configure(bg=COLOR_BACKGROUND) # Aplica fundalul si la Toplevel
        dialog.transient(self.root); dialog.grab_set()
        dialog.resizable(False, False) # Impiedica redimensionarea dialogului

        form_frame = ttk.Frame(dialog, padding="20") # Padding generos in jurul formularului
        form_frame.pack(fill=tk.BOTH, expand=True)

        entries = {} # Dictionar pentru a stoca widget-urile de input
        current_row = 0
        # Mapeaza cheia de date la textul etichetei pentru mesaje de eroare mai bune
        label_map = {item[1]: item[0] for item in field_definitions} # item[1] is key_name, item[0] is label_text

        # Parcurge definitiile campurilor si creeaza widget-urile corespunzatoare
        for label_text, key_name, widget_type, options in field_definitions:
            ttk.Label(form_frame, text=label_text).grid(row=current_row, column=0, sticky="w", padx=5, pady=8) # Pady marit
            if widget_type == "entry":
                entry = ttk.Entry(form_frame, width=40) # Latime mai mare
                entry.grid(row=current_row, column=1, padx=5, pady=8, sticky="ew")
                entries[key_name] = entry
            elif widget_type == "combobox": # Cazul special pentru Combobox (medici)
                choices_func = options.get("get_choices_func")
                choices = choices_func() if choices_func else ["Eroare la incarcare"]
                
                combobox = ttk.Combobox(form_frame, width=38, values=choices, state="readonly") # Latime ajustata
                # Seteaza prima optiune valida, altfel placeholder-ul din lista
                if choices and choices[0] not in ["Niciun medic disponibil", "Eroare la incarcare", "Optiuni indisponibile"]:
                    combobox.current(0) 
                else:
                    combobox.set(choices[0] if choices else "Optiuni indisponibile")
                combobox.grid(row=current_row, column=1, padx=5, pady=8, sticky="ew")
                entries[key_name] = combobox 
            current_row += 1
        
        form_frame.columnconfigure(1, weight=1) # Permite extinderea coloanei cu widget-uri

        # Afiseaza ID-ul generat automat, daca este cazul
        if next_id_label_text and next_id_value:
            ttk.Label(form_frame, text=next_id_label_text).grid(row=current_row, column=0, sticky="w", padx=5, pady=8)
            ttk.Label(form_frame, text=next_id_value).grid(row=current_row, column=1, sticky="w", padx=5, pady=8)
            current_row += 1

        # Functie interna pentru submit, apelata de buton
        def on_submit_internal():
            new_data = {}
            valid_submission = True # Flag pentru a verifica validitatea tuturor datelor

            # Extrage datele din widget-uri si valideaza campurile obligatorii
            for key, widget in entries.items():
                value = widget.get().strip()
                is_problematic_choice = False # Flag pentru selectii invalide in Combobox

                if isinstance(widget, ttk.Combobox): # Daca este un Combobox
                    problematic_values = ["Niciun medic disponibil", "Eroare la incarcare", "Optiuni indisponibile"]
                    if value in problematic_values or not value: # Daca valoarea e goala sau problematica
                        is_problematic_choice = True
                
                # Verifica daca un camp (altul decat combobox) e gol SAU daca selectia din combobox e problematica
                if (not value and not isinstance(widget, ttk.Combobox)) or is_problematic_choice:
                    field_label_raw = label_map.get(key, key.replace('_', ' ').title())
                    field_label = field_label_raw.replace(":", "") # Elimina ':' din eticheta
                    messagebox.showerror("Date Incomplete/Invalide", f"Campul/Selectia '{field_label}' este obligatoriu/a si trebuie sa fie valid/a!", parent=dialog)
                    valid_submission = False; break # Opreste procesarea
                
                # Proceseaza valoarea daca este valida
                if isinstance(widget, ttk.Combobox) and key == "id_medic": # Specific pentru ID Medic
                    # Extrage ID-ul medicului (ex: M001) din textul afisat (ex: Nume Prenume (M001))
                    match = re.search(r'\((M\d+)\)$', value) # Cauta (M<numar>) la sfarsitul string-ului
                    if not match:
                        messagebox.showerror("ID Medic Invalid", f"Formatul medicului ('{value}') este invalid. Nu s-a putut extrage ID-ul.", parent=dialog)
                        valid_submission = False; break
                    new_data[key] = match.group(1) # Adauga ID-ul extras (ex: "M001")
                else:
                    new_data[key] = value # Adauga valoarea direct pentru celelalte campuri
            
            if valid_submission: # Daca toate datele sunt ok
                submit_callback(next_id_value, new_data, dialog) # Apeleaza functia de callback cu datele si referinta la dialog

        # Cadru pentru butonul de submit, pentru aliniere mai buna
        button_frame = ttk.Frame(form_frame) 
        button_frame.grid(row=current_row, column=0, columnspan=2, pady=(20,0)) # Spatiu deasupra butonului
        submit_button = ttk.Button(button_frame, text=submit_command_text, command=on_submit_internal, style="Accent.TButton")
        submit_button.pack() # Centrat in button_frame

        dialog.update_idletasks() # Asigura calcularea corecta a dimensiunilor widget-urilor
        # Centrarea dialogului pe fereastra principala
        x_root = self.root.winfo_x()
        y_root = self.root.winfo_y()
        width_root = self.root.winfo_width()
        height_root = self.root.winfo_height()
        
        width_dialog = dialog.winfo_width()
        height_dialog = dialog.winfo_height()

        x_dialog = x_root + (width_root // 2) - (width_dialog // 2)
        y_dialog = y_root + (height_root // 2) - (height_dialog // 2)
        
        dialog.geometry(f"+{x_dialog}+{y_dialog}")

        dialog.wait_window() # Asteapta inchiderea dialogului

    def add_consultation_dialog(self):
        if self.xml_tree is None and self.json_data is None:
             messagebox.showwarning("Adaugare Imposibila", "Niciun fisier incarcat.")
             return

        field_definitions = [
            ("ID Pacient (Pxxx):", "id_pacient", "entry", {}),
            ("Medic:", "id_medic", "combobox", {"get_choices_func": self.get_medic_choices}),
            ("Data (YYYY-MM-DD):", "data_consultatie", "entry", {}),
            ("Ora (HH:MM:SS):", "ora_consultatie", "entry", {}),
            ("Simptome:", "simptome", "entry", {}),
            ("Diagnostic Cod (ICD10):", "diagnostic_cod", "entry", {}),
            ("Diagnostic Descriere:", "diagnostic_descriere", "entry", {}),
            ("Tratament Indicatii:", "tratament_indicatii", "entry", {})
        ]
        next_id = self.find_next_consultation_id()

        # Functia de callback specifica pentru adaugarea consultatiei
        def submit_consultation_callback(consult_id, data, dialog_ref):
            # Validari specifice pentru consultatie (dupa validarile generice din _create_form_dialog)
            if not data["id_pacient"].startswith("P"):
                 messagebox.showerror("ID Invalid", "ID Pacient trebuie sa inceapa cu P.", parent=dialog_ref)
                 return
            # Validarea ID Medic (Mxxx) se face deja in _create_form_dialog la extragerea din Combobox
            try: # Validare format data YYYY-MM-DD
                parts = data["data_consultatie"].split('-')
                if len(parts) != 3 or not (len(parts[0]) == 4 and len(parts[1]) == 2 and len(parts[2]) == 2): raise ValueError
                for part in parts: int(part) # Verifica daca sunt numere
            except ValueError:
                messagebox.showerror("Format Data Invalid", "Formatul datei trebuie sa fie YYYY-MM-DD.", parent=dialog_ref)
                return
            try: # Validare format ora HH:MM:SS
                parts = data["ora_consultatie"].split(':')
                if len(parts) != 3 or not (len(parts[0]) == 2 and len(parts[1]) == 2 and len(parts[2]) == 2): raise ValueError
                for part in parts: int(part) # Verifica daca sunt numere
            except ValueError:
                messagebox.showerror("Format Ora Invalid", "Formatul orei trebuie sa fie HH:MM:SS.", parent=dialog_ref)
                return
            
            self.add_consultation_data(consult_id, data) # Adauga datele
            dialog_ref.destroy() # Inchide dialogul

        self._create_form_dialog(
            title="Adauga Consultatie Noua",
            field_definitions=field_definitions,
            next_id_label_text="ID Consultatie (Automat):",
            next_id_value=next_id,
            submit_command_text="Adauga Consultatie",
            submit_callback=submit_consultation_callback
        )

    def add_consultation_data(self, consult_id, data):
        try:
            if self.xml_tree is not None:
                consultatii_parent = self.xml_tree.find('.//Consultatii') 
                if consultatii_parent is None: 
                    messagebox.showerror("Eroare Structura XML", "Elementul <Consultatii> nu a fost gasit.")
                    return
                new_consult = etree.SubElement(consultatii_parent, "Consultatie",
                                                id_consultatie=consult_id, 
                                                id_pacient_ref=data["id_pacient"], 
                                                id_medic_ref=data["id_medic"])
                etree.SubElement(new_consult, "Data").text = data["data_consultatie"]
                etree.SubElement(new_consult, "Ora").text = data["ora_consultatie"]
                etree.SubElement(new_consult, "Simptome").text = data["simptome"]
                diag = etree.SubElement(new_consult, "Diagnostic")
                etree.SubElement(diag, "CodICD10").text = data["diagnostic_cod"]
                etree.SubElement(diag, "Descriere").text = data["diagnostic_descriere"]
                trat = etree.SubElement(new_consult, "Tratament")
                etree.SubElement(trat, "Indicatii").text = data["tratament_indicatii"]
                self.populate_all_trees_from_xml() 
                self.update_status(f"Consultatie {consult_id} adaugata (in memorie).")
            elif self.json_data is not None:
                 consultatii_list = self.json_data.get('clinica', {}).get('consultatii')
                 if consultatii_list is None: 
                     messagebox.showerror("Eroare Structura JSON", "Lista 'consultatii' nu a fost gasita.")
                     return
                 new_consult_dict = {
                    "id_consultatie": consult_id, 
                    "id_pacient_ref": data["id_pacient"], 
                    "id_medic_ref": data["id_medic"],
                    "data": data["data_consultatie"], 
                    "ora": data["ora_consultatie"], 
                    "simptome": data["simptome"],
                    "diagnostic": {"codICD10": data["diagnostic_cod"], "descriere": data["diagnostic_descriere"]},
                    "tratament": {"indicatii": data["tratament_indicatii"], "medicamente": []} 
                 }
                 consultatii_list.append(new_consult_dict) 
                 self.populate_all_trees_from_json() 
                 self.update_status(f"Consultatie {consult_id} adaugata (in memorie).")
            self.save_changes_button.config(state=tk.NORMAL) 
        except Exception as e:
            print(f"Eroare detaliata in add_consultation_data: {traceback.format_exc()}")
            messagebox.showerror("Eroare Adaugare", f"A aparut o eroare la adaugarea consultatiei:\n{e}")
            self.update_status("Eroare la adaugare consultatie.")

    def add_medic_dialog(self):
        if self.xml_tree is None and self.json_data is None:
            messagebox.showwarning("Adaugare Imposibila", "Niciun fisier incarcat pentru a adauga un medic.")
            return

        field_definitions = [
            ("Nume:", "nume_medic", "entry", {}),
            ("Prenume:", "prenume_medic", "entry", {}),
            ("Specializare:", "specializare_medic", "entry", {})
        ]
        next_id = self.find_next_medic_id()

        # Functia de callback specifica pentru adaugarea medicului
        def submit_medic_callback(medic_id, data, dialog_ref):
            # Aici se pot adauga validari specifice pentru medic, daca este necesar,
            # in afara de verificarea campurilor goale care se face in _create_form_dialog.
            self.add_medic_data(medic_id, data) # Adauga datele medicului
            dialog_ref.destroy() # Inchide dialogul
        
        self._create_form_dialog(
            title="Adauga Medic Nou",
            field_definitions=field_definitions,
            next_id_label_text="ID Medic (Automat):",
            next_id_value=next_id,
            submit_command_text="Adauga Medic",
            submit_callback=submit_medic_callback
        )

    def add_medic_data(self, medic_id, data):
        try:
            if self.xml_tree is not None:
                root_element = self.xml_tree.getroot()
                medici_parent = root_element.find('Medici')
                if medici_parent is None: # Daca <Medici> nu exista, il cream
                    medici_parent = etree.Element("Medici")
                    # Incearca sa-l insereze intr-o pozitie logica
                    pacienti_el = root_element.find('Pacienti')
                    consultatii_el = root_element.find('Consultatii')
                    if consultatii_el is not None: consultatii_el.addprevious(medici_parent)
                    elif pacienti_el is not None: pacienti_el.addnext(medici_parent)
                    else: root_element.append(medici_parent) # Adauga la sfarsit daca celelalte nu exista

                new_medic = etree.SubElement(medici_parent, "Medic", id=medic_id)
                etree.SubElement(new_medic, "Nume").text = data["nume_medic"]
                etree.SubElement(new_medic, "Prenume").text = data["prenume_medic"]
                etree.SubElement(new_medic, "Specializare").text = data["specializare_medic"]
                self.populate_all_trees_from_xml()
                self.update_status(f"Medic {medic_id} ({data['nume_medic']} {data['prenume_medic']}) adaugat.")

            elif self.json_data is not None:
                clinica_data = self.json_data.get('clinica')
                if clinica_data is None: # Ar trebui sa existe daca fisierul e incarcat
                    messagebox.showerror("Eroare Structura JSON", "Cheia 'clinica' lipseste.")
                    return
                if 'medici' not in clinica_data: clinica_data['medici'] = [] # Creeaza lista daca nu exista
                medici_list = clinica_data['medici']
                new_medic_dict = {
                    "id": medic_id,
                    "nume": data["nume_medic"],
                    "prenume": data["prenume_medic"],
                    "specializare": data["specializare_medic"]
                }
                medici_list.append(new_medic_dict)
                self.populate_all_trees_from_json()
                self.update_status(f"Medic {medic_id} ({data['nume_medic']} {data['prenume_medic']}) adaugat.")
            
            self.save_changes_button.config(state=tk.NORMAL)
        except Exception as e:
            print(f"Eroare detaliata in add_medic_data: {traceback.format_exc()}")
            messagebox.showerror("Eroare Adaugare Medic", f"A aparut o eroare la adaugarea medicului:\n{e}")
            self.update_status("Eroare la adaugare medic.")

    def search_consultation(self):
        search_id = self.search_entry.get().strip()
        if not search_id:
            messagebox.showwarning("Cautare", "Introduceti un ID de consultatie (ex: C001).")
            return
        if not self.consultatii_tree.exists(search_id): 
            messagebox.showinfo("Cautare", f"Consultatia cu ID '{search_id}' nu a fost gasita.")
            self.update_status(f"Consultatia {search_id} nu a fost gasita.")
            return
        self.notebook.select(self.consultatii_tree.master) 
        self.consultatii_tree.selection_set(search_id) 
        self.consultatii_tree.focus(search_id) 
        self.consultatii_tree.see(search_id) 
        self.update_status(f"Consultatia {search_id} gasita si selectata.")

    def delete_consultation(self):
        selected_items = self.consultatii_tree.selection() 
        if not selected_items:
            messagebox.showwarning("Stergere", "Selectati o consultatie din tabelul 'Consultatii' pentru a o sterge.")
            return
        
        consult_id_to_delete = selected_items[0] 
        if not messagebox.askyesno("Confirmare Stergere", f"Sigur doriti sa stergeti consultatia {consult_id_to_delete}?", parent=self.root):
             return
        
        deleted_successfully = False
        try:
            if self.xml_tree is not None:
                consult_elements = self.xml_tree.xpath(f'//Consultatie[@id_consultatie="{consult_id_to_delete}"]')
                if consult_elements:
                    consult_elements[0].getparent().remove(consult_elements[0])
                    deleted_successfully = True
                else: messagebox.showerror("Eroare Interna", f"Elementul XML pentru consultatia {consult_id_to_delete} nu a putut fi gasit.")
            elif self.json_data is not None:
                 consultatii_list = self.json_data.get('clinica', {}).get('consultatii')
                 if consultatii_list is not None:
                    initial_len = len(consultatii_list)
                    self.json_data['clinica']['consultatii'] = [c for c in consultatii_list if c.get('id_consultatie') != consult_id_to_delete]
                    if len(self.json_data['clinica']['consultatii']) < initial_len: deleted_successfully = True
                    else: messagebox.showerror("Eroare Interna", f"Dictionarul JSON pentru {consult_id_to_delete} nu a putut fi gasit.")
            
            if deleted_successfully:
                 self.consultatii_tree.delete(consult_id_to_delete) 
                 self.update_status(f"Consultatia {consult_id_to_delete} a fost stearsa.")
                 self.save_changes_button.config(state=tk.NORMAL) 
            else: self.update_status(f"Stergerea consultatiei {consult_id_to_delete} a esuat.")
        except Exception as e:
             print(f"Eroare detaliata in delete_consultation: {traceback.format_exc()}")
             messagebox.showerror("Eroare Stergere", f"A aparut o eroare la stergerea consultatiei:\n{e}")
             self.update_status("Eroare la stergere consultatie.")

    def update_status(self, message):
        self.status_label.config(text=f"Status: {message}")

if __name__ == "__main__":
    root = tk.Tk()
    app = ClinicApp(root)
    root.mainloop()

# --- END OF FILE clinic_app_modern.py ---