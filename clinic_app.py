#--- START OF FILE clinic_app.py ---

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import json # Pentru a lucra cu fisiere JSON
from jsonschema import validate, exceptions as json_schema_exceptions # Pentru a valida JSON cu o schema
from lxml import etree # Librarie puternica pentru a lucra cu fisiere XML, XSD (schema XML) si XSLT (transformare XML)
import os # Pentru a lucra cu cai de fisiere (nume fisier, etc.)
import webbrowser # Pentru a deschide fisiere HTML in browser
import traceback # Pentru afisarea erorilor detaliate

#--- Nume Fisiere Implicite ---
DEFAULT_XML = "consultatii.xml"
DEFAULT_XSD = "consultatii.xsd"
DEFAULT_JSON = "consultatii.json"
DEFAULT_JSON_SCHEMA = "consultatii.schema.json"
DEFAULT_XSL = "consultatii.xsl"
HTML_OUTPUT = "consultatii_output.html"

class ClinicApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Evidenta Consultatii Clinica")
        self.root.geometry("1000x750") # Am marit putin fereastra
    
        self.xml_tree = None
        self.json_data = None
        self.xml_file_path = DEFAULT_XML
        self.json_file_path = DEFAULT_JSON

        self.create_widgets()

    def create_widgets(self):
        self.paned_window = ttk.PanedWindow(self.root, orient=tk.VERTICAL)
        self.paned_window.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.controls_frame = ttk.Frame(self.paned_window, padding="10")
        self.paned_window.add(self.controls_frame, weight=0)

        # --- Butoane de Control (Identice ca inainte) ---
        self.load_xml_button = ttk.Button(self.controls_frame, text="Incarca XML", command=self.load_xml)
        self.load_xml_button.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        self.validate_xsd_button = ttk.Button(self.controls_frame, text="Valideaza XML (XSD)", command=self.validate_xsd, state=tk.DISABLED)
        self.validate_xsd_button.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        self.show_xslt_button = ttk.Button(self.controls_frame, text="Afiseaza Tabel (XSLT)", command=self.display_xslt, state=tk.DISABLED)
        self.show_xslt_button.grid(row=0, column=2, padx=5, pady=5, sticky="ew")
        self.load_json_button = ttk.Button(self.controls_frame, text="Incarca JSON", command=self.load_json)
        self.load_json_button.grid(row=1, column=0, padx=5, pady=5, sticky="ew")
        self.validate_json_button = ttk.Button(self.controls_frame, text="Valideaza JSON (Schema)", command=self.validate_json_schema, state=tk.DISABLED)
        self.validate_json_button.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        self.save_changes_button = ttk.Button(self.controls_frame, text="Salveaza Modificari", command=self.save_changes, state=tk.DISABLED)
        self.save_changes_button.grid(row=1, column=2, padx=5, pady=5, sticky="ew")

        # --- Notebook (Tab-uri) pentru afisarea datelor ---
        self.notebook_frame = ttk.Frame(self.paned_window, padding="5")
        self.paned_window.add(self.notebook_frame, weight=1)

        self.notebook = ttk.Notebook(self.notebook_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Creare tab-uri si Treeview-uri pentru fiecare categorie
        self.pacienti_tree = self.create_category_treeview("Pacienti",
            {"#0": ("ID Pacient", 150), "col1": ("Nume", 120), "col2": ("Prenume", 120), "col3": ("Data Nasterii", 100), "col4": ("Telefon", 100)}
        )
        self.medici_tree = self.create_category_treeview("Medici",
            {"#0": ("ID Medic", 150), "col1": ("Nume", 120), "col2": ("Prenume", 120), "col3": ("Specializare", 150)}
        )
        self.consultatii_tree = self.create_category_treeview("Consultatii",
            {"#0": ("ID Consultatie", 120), "col1": ("Data", 100), "col2": ("Ora", 80), "col3": ("ID Pacient", 100), "col4": ("ID Medic", 100), "col5": ("Simptome", 150), "col6": ("Diagnostic", 200), "col7": ("Tratament", 200)}
        )

        # --- Frame-ul de Jos pentru CRUD si Status (Identic ca inainte, dar CRUD e pt Consultatii) ---
        self.bottom_frame = ttk.Frame(self.paned_window, padding="10")
        self.paned_window.add(self.bottom_frame, weight=0)

        crud_frame = ttk.LabelFrame(self.bottom_frame, text="Operatii Consultatii (In-Memory)", padding="10")
        crud_frame.pack(fill=tk.X, pady=(0, 5))

        ttk.Label(crud_frame, text="Cauta ID Consultatie:").grid(row=0, column=0, padx=5, pady=2, sticky="w")
        self.search_entry = ttk.Entry(crud_frame, width=15)
        self.search_entry.grid(row=0, column=1, padx=5, pady=2)
        self.search_button = ttk.Button(crud_frame, text="Cauta", command=self.search_consultation, state=tk.DISABLED)
        self.search_button.grid(row=0, column=2, padx=5, pady=2)

        self.add_button = ttk.Button(crud_frame, text="Adauga Consultatie Noua", command=self.add_consultation_dialog, state=tk.DISABLED)
        self.add_button.grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky="ew")
        self.delete_button = ttk.Button(crud_frame, text="Sterge Consultatia Selectata", command=self.delete_consultation, state=tk.DISABLED)
        self.delete_button.grid(row=1, column=2, padx=5, pady=5, sticky="ew")

        self.status_label = ttk.Label(self.bottom_frame, text="Status: Asteptare incarcare fisier...", relief=tk.SUNKEN, anchor=tk.W)
        self.status_label.pack(fill=tk.X, side=tk.BOTTOM, pady=(5,0))

    def create_category_treeview(self, tab_name, columns_config):
        # Functie helper pentru a crea un tab si un Treeview in interior
        tab_frame = ttk.Frame(self.notebook, padding="5")
        self.notebook.add(tab_frame, text=tab_name)

        tree = ttk.Treeview(tab_frame) # Nu mai folosim `show="tree headings"` aici, fiecare e un tabel plat
        
        # Definirea coloanelor pe baza configuratiei primite
        # `columns_config` este un dictionar de forma:
        # {'id_intern_col': ('Nume Afisat Col', LatimeCol), ...}
        # '#0' este pentru prima coloana (cea cu iid-ul)
        
        tree_cols = [key for key in columns_config if key != "#0"]
        tree["columns"] = tuple(tree_cols)

        col_info = columns_config.get("#0", ("ID", 100))
        tree.heading("#0", text=col_info[0])
        tree.column("#0", anchor=tk.W, width=col_info[1], stretch=tk.NO)

        for col_id in tree_cols:
            col_info = columns_config[col_id]
            tree.heading(col_id, text=col_info[0])
            tree.column(col_id, anchor=tk.W, width=col_info[1], stretch=tk.YES) # stretch=YES permite redimensionarea

        tree_ysb = ttk.Scrollbar(tab_frame, orient=tk.VERTICAL, command=tree.yview)
        tree_xsb = ttk.Scrollbar(tab_frame, orient=tk.HORIZONTAL, command=tree.xview)
        tree.configure(yscrollcommand=tree_ysb.set, xscrollcommand=tree_xsb.set)
        
        tree_ysb.pack(side=tk.RIGHT, fill=tk.Y)
        tree_xsb.pack(side=tk.BOTTOM, fill=tk.X)
        tree.pack(fill=tk.BOTH, expand=True)
        
        return tree # Returneaza instanta Treeview creata

    # --- Gestiunea Fisierelor (load_xml, load_json, save_changes - majoritar identice) ---
    def load_xml(self):
        self.clear_all_displays() # Goleste toate Treeview-urile
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
            self.populate_all_trees_from_xml() # Populeaza toate Treeview-urile
            self.update_status(f"Fisier XML incarcat: {os.path.basename(filepath)}")
            self.validate_xsd_button.config(state=tk.NORMAL)
            self.show_xslt_button.config(state=tk.NORMAL)
            self.validate_json_button.config(state=tk.DISABLED)
            self.search_button.config(state=tk.NORMAL)
            self.add_button.config(state=tk.NORMAL)
            self.delete_button.config(state=tk.NORMAL)
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
            self.populate_all_trees_from_json() # Populeaza toate Treeview-urile
            self.update_status(f"Fisier JSON incarcat: {os.path.basename(filepath)}")
            self.validate_json_button.config(state=tk.NORMAL)
            self.validate_xsd_button.config(state=tk.DISABLED)
            self.show_xslt_button.config(state=tk.DISABLED)
            self.search_button.config(state=tk.NORMAL)
            self.add_button.config(state=tk.NORMAL)
            self.delete_button.config(state=tk.NORMAL)
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
        # Functia de salvare ramane la fel, modifica self.xml_tree sau self.json_data
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
        # Goleste itemii dintr-un Treeview specific
        for item in tree_widget.get_children():
            tree_widget.delete(item)

    def clear_all_displays(self):
        # Goleste toate Treeview-urile si reseteaza starea
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
        self.save_changes_button.config(state=tk.DISABLED)
        self.update_status("Afisaj curatat.")

    def populate_all_trees_from_xml(self):
        # Populeaza fiecare Treeview cu datele corespunzatoare din XML
        if self.xml_tree is None: return
        root_element = self.xml_tree.getroot()
        if root_element is None or root_element.tag != 'Clinica':
            messagebox.showwarning("XML Invalid", "Elementul radacina <Clinica> nu a fost gasit.")
            return

        # Populeaza Pacienti
        self.clear_tree_items(self.pacienti_tree)
        for pacient in root_element.xpath('//Pacient'):
            pid = pacient.get('id', 'N/A')
            nume = pacient.findtext('Nume', default='')
            prenume = pacient.findtext('Prenume', default='')
            dn = pacient.findtext('DataNasterii', default='')
            tel = pacient.findtext('Telefon', default='')
            self.pacienti_tree.insert("", tk.END, text=pid, values=(nume, prenume, dn, tel))

        # Populeaza Medici
        self.clear_tree_items(self.medici_tree)
        for medic in root_element.xpath('//Medic'):
            mid = medic.get('id', 'N/A')
            nume = medic.findtext('Nume', default='')
            prenume = medic.findtext('Prenume', default='')
            spec = medic.findtext('Specializare', default='')
            self.medici_tree.insert("", tk.END, text=mid, values=(nume, prenume, spec))

        # Populeaza Consultatii
        self.clear_tree_items(self.consultatii_tree)
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
            # Folosim cid ca iid pentru a putea sterge/cauta consultatii
            self.consultatii_tree.insert("", tk.END, iid=cid, text=cid, values=(data, ora, pid_ref, mid_ref, simptome, diag_str, trat_str))

    def populate_all_trees_from_json(self):
        # Populeaza fiecare Treeview cu datele corespunzatoare din JSON
        if self.json_data is None or 'clinica' not in self.json_data:
            messagebox.showwarning("JSON Invalid", "Structura JSON invalida sau cheia 'clinica' lipseste.")
            return
        clinica_data = self.json_data['clinica']

        # Populeaza Pacienti
        self.clear_tree_items(self.pacienti_tree)
        for pacient in clinica_data.get('pacienti', []):
            pid = pacient.get('id', 'N/A')
            nume = pacient.get('nume', '')
            prenume = pacient.get('prenume', '')
            dn = pacient.get('dataNasterii', '')
            tel = pacient.get('telefon', '')
            self.pacienti_tree.insert("", tk.END, text=pid, values=(nume, prenume, dn, tel))

        # Populeaza Medici
        self.clear_tree_items(self.medici_tree)
        for medic in clinica_data.get('medici', []):
            mid = medic.get('id', 'N/A')
            nume = medic.get('nume', '')
            prenume = medic.get('prenume', '')
            spec = medic.get('specializare', '')
            self.medici_tree.insert("", tk.END, text=mid, values=(nume, prenume, spec))

        # Populeaza Consultatii
        self.clear_tree_items(self.consultatii_tree)
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
            self.consultatii_tree.insert("", tk.END, iid=cid, text=cid, values=(data, ora, pid_ref, mid_ref, simptome, diag_str, trat_str))

    # --- Validare (Identica) ---
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

    # --- Transformare XSLT (Identica) ---
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

    # --- Operatii CRUD (Raman axate pe Consultatii pentru simplitate) ---
    def find_next_consultation_id(self): # Identica
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

    def add_consultation_dialog(self): # Identica cu versiunea corectata anterior
        if self.xml_tree is None and self.json_data is None:
            messagebox.showwarning("Adaugare Imposibila", "Niciun fisier incarcat.")
            return
        dialog = tk.Toplevel(self.root)
        dialog.title("Adauga Consultatie Noua")
        dialog.geometry("400x450")
        dialog.transient(self.root); dialog.grab_set()
        form_frame = ttk.Frame(dialog, padding="10"); form_frame.pack(fill=tk.BOTH, expand=True)
        field_definitions = [
            ("ID Pacient (Pxxx):", "id_pacient"), ("ID Medic (Mxxx):", "id_medic"),
            ("Data (YYYY-MM-DD):", "data_consultatie"), ("Ora (HH:MM:SS):", "ora_consultatie"),
            ("Simptome:", "simptome"), ("Diagnostic Cod (ICD10):", "diagnostic_cod"),
            ("Diagnostic Descriere:", "diagnostic_descriere"), ("Tratament Indicatii:", "tratament_indicatii")
        ]
        entries = {}
        for i, (label_text, key_name) in enumerate(field_definitions):
            ttk.Label(form_frame, text=label_text).grid(row=i, column=0, sticky="w", padx=5, pady=3)
            entry = ttk.Entry(form_frame, width=35); entry.grid(row=i, column=1, padx=5, pady=3)
            entries[key_name] = entry
        next_id = self.find_next_consultation_id()
        ttk.Label(form_frame, text=f"ID Consultatie (Automat):").grid(row=len(field_definitions), column=0, sticky="w", padx=5, pady=3)
        ttk.Label(form_frame, text=next_id).grid(row=len(field_definitions), column=1, sticky="w", padx=5, pady=3)
        def submit():
            new_data = {key: widget.get().strip() for key, widget in entries.items()}
            required_keys = ["id_pacient", "id_medic", "data_consultatie", "ora_consultatie", "simptome", "diagnostic_cod", "diagnostic_descriere", "tratament_indicatii"]
            for req_key in required_keys:
                if not new_data.get(req_key):
                    messagebox.showerror("Date Incomplete", f"Campul '{req_key.replace('_', ' ').title()}' este obligatoriu!", parent=dialog)
                    return
            if not new_data["id_pacient"].startswith("P") or not new_data["id_medic"].startswith("M"):
                messagebox.showerror("ID Invalid", "ID Pacient trebuie sa inceapa cu P, ID Medic cu M.", parent=dialog)
                return
            if len(new_data["data_consultatie"].split('-')) != 3: # Validare simpla data
                messagebox.showerror("Format Data Invalid", "Formatul datei trebuie sa fie YYYY-MM-DD.", parent=dialog)
                return
            if len(new_data["ora_consultatie"].split(':')) != 3: # Validare simpla ora
                messagebox.showerror("Format Ora Invalid", "Formatul orei trebuie sa fie HH:MM:SS.", parent=dialog)
                return
            self.add_consultation_data(next_id, new_data)
            dialog.destroy()
        submit_button = ttk.Button(form_frame, text="Adauga", command=submit)
        submit_button.grid(row=len(field_definitions) + 1, column=0, columnspan=2, pady=15)
        dialog.wait_window()

    def add_consultation_data(self, consult_id, data): # Identica
        try:
            if self.xml_tree is not None:
                consultatii_parent = self.xml_tree.find('.//Consultatii')
                if consultatii_parent is None: messagebox.showerror("Eroare Structura XML", "Elementul <Consultatii> nu a fost gasit."); return
                new_consult = etree.SubElement(consultatii_parent, "Consultatie",
                                                id_consultatie=consult_id, id_pacient_ref=data["id_pacient"], id_medic_ref=data["id_medic"])
                etree.SubElement(new_consult, "Data").text = data["data_consultatie"]
                etree.SubElement(new_consult, "Ora").text = data["ora_consultatie"]
                etree.SubElement(new_consult, "Simptome").text = data["simptome"]
                diag = etree.SubElement(new_consult, "Diagnostic"); etree.SubElement(diag, "CodICD10").text = data["diagnostic_cod"]; etree.SubElement(diag, "Descriere").text = data["diagnostic_descriere"]
                trat = etree.SubElement(new_consult, "Tratament"); etree.SubElement(trat, "Indicatii").text = data["tratament_indicatii"]
                self.populate_all_trees_from_xml() # Reimprospateaza toate tabelele
                self.update_status(f"Consultatie {consult_id} adaugata (in memorie).")
            elif self.json_data is not None:
                consultatii_list = self.json_data.get('clinica', {}).get('consultatii')
                if consultatii_list is None: messagebox.showerror("Eroare Structura JSON", "Lista 'consultatii' nu a fost gasita."); return
                new_consult_dict = {
                    "id_consultatie": consult_id, "id_pacient_ref": data["id_pacient"], "id_medic_ref": data["id_medic"],
                    "data": data["data_consultatie"], "ora": data["ora_consultatie"], "simptome": data["simptome"],
                    "diagnostic": {"codICD10": data["diagnostic_cod"], "descriere": data["diagnostic_descriere"]},
                    "tratament": {"indicatii": data["tratament_indicatii"], "medicamente": []}
                }
                consultatii_list.append(new_consult_dict)
                self.populate_all_trees_from_json() # Reimprospateaza toate tabelele
                self.update_status(f"Consultatie {consult_id} adaugata (in memorie).")
            self.save_changes_button.config(state=tk.NORMAL)
        except Exception as e:
            print(f"Eroare detaliata in add_consultation_data: {traceback.format_exc()}")
            messagebox.showerror("Eroare Adaugare", f"A aparut o eroare la adaugarea consultatiei:\n{e}")
            self.update_status("Eroare la adaugare consultatie.")

    def search_consultation(self):
        # Cautarea se face in Treeview-ul de Consultatii
        search_id = self.search_entry.get().strip()
        if not search_id:
            messagebox.showwarning("Cautare", "Introduceti un ID de consultatie (ex: C001).")
            return
        if not self.consultatii_tree.exists(search_id): # Verifica in tree-ul de consultatii
            messagebox.showinfo("Cautare", f"Consultatia cu ID '{search_id}' nu a fost gasita.")
            self.update_status(f"Consultatia {search_id} nu a fost gasita.")
            return
        self.notebook.select(self.consultatii_tree.master) # Comuta la tab-ul de consultatii
        self.consultatii_tree.selection_set(search_id)
        self.consultatii_tree.focus(search_id)
        self.consultatii_tree.see(search_id)
        self.update_status(f"Consultatia {search_id} gasita si selectata.")

    def delete_consultation(self):
        # Stergerea se face din Treeview-ul de Consultatii
        # Verifica daca tabul de consultatii este activ pentru a lua selectia corecta (optional, dar bun UX)
        # Sau, mai simplu, luam selectia doar din consultatii_tree
        selected_items = self.consultatii_tree.selection()
        if not selected_items:
            messagebox.showwarning("Stergere", "Selectati o consultatie din tabelul 'Consultatii' pentru a o sterge.")
            return
        consult_id_to_delete = selected_items[0] # Presupunem o singura selectie
        if not messagebox.askyesno("Confirmare Stergere", f"Sigur doriti sa stergeti consultatia {consult_id_to_delete}?", parent=self.root):
            return
        deleted = False
        try:
            if self.xml_tree is not None:
                consult_element_xpath_result = self.xml_tree.xpath(f'//Consultatie[@id_consultatie="{consult_id_to_delete}"]')
                if consult_element_xpath_result:
                    consult_element_xpath_result[0].getparent().remove(consult_element_xpath_result[0])
                    deleted = True
                else: messagebox.showerror("Eroare Interna", f"Elementul XML pentru {consult_id_to_delete} nu a putut fi gasit.")
            elif self.json_data is not None:
                consultatii_list = self.json_data.get('clinica', {}).get('consultatii')
                if consultatii_list is not None:
                    initial_len = len(consultatii_list)
                    self.json_data['clinica']['consultatii'] = [c for c in consultatii_list if c.get('id_consultatie') != consult_id_to_delete]
                    if len(self.json_data['clinica']['consultatii']) < initial_len: deleted = True
                    else: messagebox.showerror("Eroare Interna", f"Dictionarul JSON pentru {consult_id_to_delete} nu a putut fi gasit.")
            if deleted:
                self.consultatii_tree.delete(consult_id_to_delete) # Sterge din Treeview-ul specific
                self.update_status(f"Consultatia {consult_id_to_delete} a fost stearsa (din memorie).")
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