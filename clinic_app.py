# --- START OF FILE clinic_app.py ---

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

        # --- Butoane de Control ---
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

        # --- Frame-ul de Jos pentru CRUD si Status ---
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

        tree = ttk.Treeview(tab_frame)
        
        # Definirea coloanelor pe baza configuratiei primite
        tree_cols = [key for key in columns_config if key != "#0"]
        tree["columns"] = tuple(tree_cols)

        col_info = columns_config.get("#0", ("ID", 100))
        tree.heading("#0", text=col_info[0])
        tree.column("#0", anchor=tk.W, width=col_info[1], stretch=tk.NO)

        for col_id in tree_cols:
            col_info = columns_config[col_id]
            tree.heading(col_id, text=col_info[0])
            tree.column(col_id, anchor=tk.W, width=col_info[1], stretch=tk.YES)

        tree_ysb = ttk.Scrollbar(tab_frame, orient=tk.VERTICAL, command=tree.yview)
        tree_xsb = ttk.Scrollbar(tab_frame, orient=tk.HORIZONTAL, command=tree.xview)
        tree.configure(yscrollcommand=tree_ysb.set, xscrollcommand=tree_xsb.set)
        
        tree_ysb.pack(side=tk.RIGHT, fill=tk.Y)
        tree_xsb.pack(side=tk.BOTTOM, fill=tk.X)
        tree.pack(fill=tk.BOTH, expand=True)
        
        return tree

    # --- Gestiunea Fisierelor ---
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
            self.json_data = None # Reseteaza datele JSON daca se incarca XML
            self.populate_all_trees_from_xml() # Populeaza toate Treeview-urile
            self.update_status(f"Fisier XML incarcat: {os.path.basename(filepath)}")
            # Activeaza/dezactiveaza butoanele corespunzatoare
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
            self.xml_tree = None # Reseteaza arborele XML daca se incarca JSON
            self.populate_all_trees_from_json() # Populeaza toate Treeview-urile
            self.update_status(f"Fisier JSON incarcat: {os.path.basename(filepath)}")
            # Activeaza/dezactiveaza butoanele corespunzatoare
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
        
        # Reseteaza datele si starea butoanelor
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

    # --- Operatii CRUD (pentru Consultatii) ---
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

    def get_medic_choices(self):
        # Functie helper pentru a obtine lista de medici formatata pentru Combobox
        medic_choices = []
        if self.xml_tree is not None:
            root_element = self.xml_tree.getroot()
            if root_element is not None:
                # Itereaza prin elementele Medic din XML
                for medic in root_element.xpath('//Medic'):
                    mid = medic.get('id', 'N/A')
                    nume = medic.findtext('Nume', default='')
                    prenume = medic.findtext('Prenume', default='')
                    if mid != 'N/A' and (nume or prenume): # Asigura ca medicul are ID si nume/prenume
                        medic_choices.append(f"{nume} {prenume} ({mid})")
        elif self.json_data is not None:
            clinica_data = self.json_data.get('clinica', {})
            # Itereaza prin dictionarele medicilor din JSON
            for medic in clinica_data.get('medici', []):
                mid = medic.get('id', 'N/A')
                nume = medic.get('nume', '')
                prenume = medic.get('prenume', '')
                if mid != 'N/A' and (nume or prenume): # Asigura ca medicul are ID si nume/prenume
                    medic_choices.append(f"{nume} {prenume} ({mid})")
        
        if not medic_choices:
            # Daca nu sunt medici, returneaza o lista cu un placeholder specific
            return ["Niciun medic disponibil"]
        return sorted(medic_choices) # Returneaza lista sortata alfabetic

    def add_consultation_dialog(self):
        if self.xml_tree is None and self.json_data is None:
             messagebox.showwarning("Adaugare Imposibila", "Niciun fisier incarcat.")
             return

        dialog = tk.Toplevel(self.root)
        dialog.title("Adauga Consultatie Noua")
        dialog.geometry("450x500") # Dimensiune ajustata pentru dialog
        dialog.transient(self.root); dialog.grab_set()
        form_frame = ttk.Frame(dialog, padding="10"); form_frame.pack(fill=tk.BOTH, expand=True)

        # Definim campurile, tipurile lor (entry/combobox) si optiunile specifice
        # Format: (Textul etichetei, cheia pentru dictionarul de date, tipul widget-ului, dictionar de optiuni)
        field_definitions = [
            ("ID Pacient (Pxxx):", "id_pacient", "entry", {}),
            ("Medic:", "id_medic", "combobox", {"get_choices_func": self.get_medic_choices}), # Campul medic este acum un combobox
            ("Data (YYYY-MM-DD):", "data_consultatie", "entry", {}),
            ("Ora (HH:MM:SS):", "ora_consultatie", "entry", {}),
            ("Simptome:", "simptome", "entry", {}),
            ("Diagnostic Cod (ICD10):", "diagnostic_cod", "entry", {}),
            ("Diagnostic Descriere:", "diagnostic_descriere", "entry", {}),
            ("Tratament Indicatii:", "tratament_indicatii", "entry", {})
        ]
        entries = {} # Va stoca widget-urile de input (Entry, Combobox)
        current_row = 0
        
        # Mapeaza cheia de date la textul etichetei pentru mesaje de eroare mai bune
        label_map = {item[1]: item[0] for item in field_definitions}

        # Parcurge definitiile campurilor si creeaza widget-urile corespunzatoare
        for label_text, key_name, widget_type, options in field_definitions:
            ttk.Label(form_frame, text=label_text).grid(row=current_row, column=0, sticky="w", padx=5, pady=3)
            if widget_type == "entry":
                entry = ttk.Entry(form_frame, width=35)
                entry.grid(row=current_row, column=1, padx=5, pady=3)
                entries[key_name] = entry
            elif widget_type == "combobox": # Cazul special pentru Combobox (medici)
                choices_func = options.get("get_choices_func")
                choices = choices_func() if choices_func else ["Eroare: Nu s-au putut incarca optiunile"]
                
                combobox = ttk.Combobox(form_frame, width=33, values=choices, state="readonly")
                if choices: # Verifica daca lista de optiuni nu e goala
                    # Seteaza prima optiune valida, altfel placeholder-ul din lista
                    if choices[0] not in ["Niciun medic disponibil", "Eroare: Nu s-au putut incarca optiunile", "Optiuni indisponibile"]:
                        combobox.current(0) # Selecteaza primul element daca e valid
                    else:
                        combobox.set(choices[0]) # Seteaza placeholder-ul (ex: "Niciun medic disponibil")
                else: # Daca lista e goala din vreun motiv neasteptat
                    combobox.set("Optiuni indisponibile") # Placeholder pentru caz de eroare
                
                combobox.grid(row=current_row, column=1, padx=5, pady=3)
                entries[key_name] = combobox # Stocheaza referinta la Combobox
            current_row += 1

        next_id = self.find_next_consultation_id() # Genereaza ID-ul urmatoarei consultatii
        ttk.Label(form_frame, text=f"ID Consultatie (Automat):").grid(row=current_row, column=0, sticky="w", padx=5, pady=3)
        ttk.Label(form_frame, text=next_id).grid(row=current_row, column=1, sticky="w", padx=5, pady=3)
        current_row += 1

        def submit():
            new_data = {}
            valid_submission = True # Flag pentru a verifica validitatea tuturor datelor

            # Extrage datele din widget-uri si valideaza campurile obligatorii
            for key, widget in entries.items():
                value = widget.get().strip()
                is_problematic_choice = False # Flag pentru selectii invalide in Combobox

                if key == "id_medic": # Verificare speciala pentru Combobox-ul medicilor
                    problematic_values = ["Niciun medic disponibil", "Eroare: Nu s-au putut incarca optiunile", "Optiuni indisponibile"]
                    if value in problematic_values or not value:
                        is_problematic_choice = True
                
                # Verifica daca un camp (altul decat medic) e gol sau daca selectia medicului e problematica
                if (not value and key != "id_medic") or is_problematic_choice:
                    field_label_raw = label_map.get(key, key.replace('_', ' ').title())
                    field_label = field_label_raw.replace(":", "") # Elimina ':' din eticheta
                    if key == "id_medic" and is_problematic_choice:
                        messagebox.showerror("Selectie Invalida", f"Va rugam selectati un {field_label.lower()} valid.", parent=dialog)
                    else:
                        messagebox.showerror("Date Incomplete", f"Campul '{field_label}' este obligatoriu!", parent=dialog)
                    valid_submission = False; break # Opreste procesarea daca un camp e invalid
                
                # Proceseaza valoarea daca este valida
                if key == "id_medic": # Daca este campul medicului (din Combobox)
                    selected_medic_display = value
                    # Extrage ID-ul medicului (ex: M001) din textul afisat (ex: Nume Prenume (M001))
                    match = re.search(r'\((\w+)\)$', selected_medic_display) # Cauta (ID) la sfarsitul string-ului
                    if not match:
                        messagebox.showerror("ID Medic Invalid", f"Formatul medicului ('{selected_medic_display}') este invalid. Nu s-a putut extrage ID-ul.", parent=dialog)
                        valid_submission = False; break
                    new_data[key] = match.group(1) # Adauga ID-ul extras (ex: "M001")
                else:
                    new_data[key] = value # Adauga valoarea direct pentru celelalte campuri de tip 'entry'

            if not valid_submission: return # Nu continua daca au fost erori de validare

            # Validari specifice de format pentru datele extrase
            if not new_data["id_pacient"].startswith("P"):
                 messagebox.showerror("ID Invalid", "ID Pacient trebuie sa inceapa cu P.", parent=dialog)
                 return
            if not new_data["id_medic"].startswith("M"): # Verifica ID-ul medicului extras
                 messagebox.showerror("ID Medic Invalid", "ID-ul medicului extras nu incepe cu 'M'. Eroare interna.", parent=dialog)
                 return
            try: # Validare format data YYYY-MM-DD
                parts = new_data["data_consultatie"].split('-')
                if len(parts) != 3 or not (len(parts[0]) == 4 and len(parts[1]) == 2 and len(parts[2]) == 2): raise ValueError
                for part in parts: int(part) # Verifica daca sunt numere
            except ValueError:
                messagebox.showerror("Format Data Invalid", "Formatul datei trebuie sa fie YYYY-MM-DD.", parent=dialog)
                return
            try: # Validare format ora HH:MM:SS
                parts = new_data["ora_consultatie"].split(':')
                if len(parts) != 3 or not (len(parts[0]) == 2 and len(parts[1]) == 2 and len(parts[2]) == 2): raise ValueError
                for part in parts: int(part) # Verifica daca sunt numere
            except ValueError:
                messagebox.showerror("Format Ora Invalid", "Formatul orei trebuie sa fie HH:MM:SS.", parent=dialog)
                return
            
            # Daca toate validarile trec, adauga consultatia
            self.add_consultation_data(next_id, new_data)
            dialog.destroy() # Inchide dialogul dupa adaugare

        submit_button = ttk.Button(form_frame, text="Adauga", command=submit)
        submit_button.grid(row=current_row, column=0, columnspan=2, pady=15)
        dialog.wait_window()

    def add_consultation_data(self, consult_id, data):
        try:
            if self.xml_tree is not None:
                consultatii_parent = self.xml_tree.find('.//Consultatii') # Gaseste elementul parinte <Consultatii>
                if consultatii_parent is None: 
                    messagebox.showerror("Eroare Structura XML", "Elementul <Consultatii> nu a fost gasit.")
                    return
                # Creeaza noul element <Consultatie> si subelementele sale
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
                # Pot fi adaugate si medicamente aici daca se extinde formularul
                # etree.SubElement(trat, "Medicamente") 
                self.populate_all_trees_from_xml() # Reimprospateaza toate tabelele
                self.update_status(f"Consultatie {consult_id} adaugata (in memorie).")
            elif self.json_data is not None:
                 consultatii_list = self.json_data.get('clinica', {}).get('consultatii')
                 if consultatii_list is None: 
                     messagebox.showerror("Eroare Structura JSON", "Lista 'consultatii' nu a fost gasita.")
                     return
                 # Creeaza noul dictionar pentru consultatie
                 new_consult_dict = {
                    "id_consultatie": consult_id, 
                    "id_pacient_ref": data["id_pacient"], 
                    "id_medic_ref": data["id_medic"],
                    "data": data["data_consultatie"], 
                    "ora": data["ora_consultatie"], 
                    "simptome": data["simptome"],
                    "diagnostic": {"codICD10": data["diagnostic_cod"], "descriere": data["diagnostic_descriere"]},
                    "tratament": {"indicatii": data["tratament_indicatii"], "medicamente": []} # Lista goala pentru medicamente
                 }
                 consultatii_list.append(new_consult_dict) # Adauga la lista de consultatii
                 self.populate_all_trees_from_json() # Reimprospateaza toate tabelele
                 self.update_status(f"Consultatie {consult_id} adaugata (in memorie).")
            self.save_changes_button.config(state=tk.NORMAL) # Activeaza butonul de salvare
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
        self.consultatii_tree.selection_set(search_id) # Selecteaza item-ul
        self.consultatii_tree.focus(search_id) # Seteaza focusul pe item
        self.consultatii_tree.see(search_id) # Asigura vizibilitatea item-ului
        self.update_status(f"Consultatia {search_id} gasita si selectata.")

    def delete_consultation(self):
        # Stergerea se face din Treeview-ul de Consultatii
        selected_items = self.consultatii_tree.selection() # Obtine item-ul selectat
        if not selected_items:
            messagebox.showwarning("Stergere", "Selectati o consultatie din tabelul 'Consultatii' pentru a o sterge.")
            return
        
        consult_id_to_delete = selected_items[0] # Presupunem o singura selectie
        if not messagebox.askyesno("Confirmare Stergere", f"Sigur doriti sa stergeti consultatia {consult_id_to_delete}?", parent=self.root):
             return
        
        deleted_successfully = False
        try:
            if self.xml_tree is not None:
                # Gaseste elementul XML corespunzator si il sterge
                consult_element_xpath = f'//Consultatie[@id_consultatie="{consult_id_to_delete}"]'
                consult_elements = self.xml_tree.xpath(consult_element_xpath)
                if consult_elements:
                    consult_elements[0].getparent().remove(consult_elements[0])
                    deleted_successfully = True
                else: 
                    messagebox.showerror("Eroare Interna", f"Elementul XML pentru consultatia {consult_id_to_delete} nu a putut fi gasit pentru stergere.")
            elif self.json_data is not None:
                 consultatii_list = self.json_data.get('clinica', {}).get('consultatii')
                 if consultatii_list is not None:
                    initial_len = len(consultatii_list)
                    # Reconstruieste lista de consultatii fara elementul de sters
                    self.json_data['clinica']['consultatii'] = [c for c in consultatii_list if c.get('id_consultatie') != consult_id_to_delete]
                    if len(self.json_data['clinica']['consultatii']) < initial_len:
                        deleted_successfully = True
                    else:
                        messagebox.showerror("Eroare Interna", f"Dictionarul JSON pentru consultatia {consult_id_to_delete} nu a putut fi gasit pentru stergere.")
            
            if deleted_successfully:
                 self.consultatii_tree.delete(consult_id_to_delete) # Sterge si din Treeview-ul specific
                 self.update_status(f"Consultatia {consult_id_to_delete} a fost stearsa (din memorie).")
                 self.save_changes_button.config(state=tk.NORMAL) # Activeaza butonul de salvare
            else: 
                # Acest mesaj ar putea fi redundant daca erorile interne sunt afisate deja
                self.update_status(f"Stergerea consultatiei {consult_id_to_delete} a esuat (nu a fost gasita in datele sursa).")
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