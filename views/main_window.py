import customtkinter as ctk
from tkinter import ttk, messagebox
from controllers.library_controller import LibraryController
from models.entities import AUTHOR_FIELDS, PUBLISHER_FIELDS, USER_FIELDS, BOOK_FIELDS
from datetime import date

ctk.set_appearance_mode("system")
ctk.set_default_color_theme("blue")
class BibliotecaApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("AcaBiblioteca | Gestión bibliotecaria")
        self.geometry("1120x720"); self.minsize(900,600)
        self.controller=LibraryController()
        header=ctk.CTkFrame(self); header.pack(fill="x",padx=16,pady=(16,8))
        ctk.CTkLabel(header,text="AcaBiblioteca",font=ctk.CTkFont(size=25,weight="bold")).pack(side="left",padx=14,pady=12)
        ctk.CTkLabel(header,text="Administración de biblioteca · Python + MySQL",text_color="gray").pack(side="right",padx=14)
        self.tabs=ctk.CTkTabview(self); self.tabs.pack(fill="both",expand=True,padx=16,pady=8)
        for name in ["Libros","Autores","Editoriales","Usuarios","Préstamos"]: self.tabs.add(name)
        self.build_crud("Libros",BOOK_FIELDS)
        self.build_crud("Autores",AUTHOR_FIELDS)
        self.build_crud("Editoriales",PUBLISHER_FIELDS)
        self.build_crud("Usuarios",USER_FIELDS)
        self.build_loans()
        footer=ctk.CTkLabel(self,text="AcaBiblioteca · Datos locales en MySQL",text_color="gray")
        footer.pack(pady=(0,8))
    def build_crud(self, table, fields):
        frame=self.tabs.tab(table)
        top=ctk.CTkFrame(frame); top.pack(fill="x",padx=10,pady=10)
        ctk.CTkLabel(top,text=f"Gestión de {table.lower()}",font=ctk.CTkFont(size=18,weight="bold")).pack(side="left",padx=10)
        if table=="Libros":
            self.isbn_search=ctk.CTkEntry(top,placeholder_text="Buscar por ISBN",width=180)
            self.isbn_search.pack(side="right",padx=4)
            ctk.CTkButton(top,text="Buscar ISBN",command=self.search_book,width=100).pack(side="right",padx=4)
        cols=("key",)+tuple(fields.keys())
        tree=ttk.Treeview(frame,columns=cols,show="headings",height=14)
        tree.pack(fill="both",expand=True,padx=10,pady=8)
        for col in cols:
            tree.heading(col,text=col); tree.column(col,width=130,anchor="w")
        setattr(self,f"tree_{table}",tree)
        buttons=ctk.CTkFrame(frame); buttons.pack(fill="x",padx=10,pady=8)
        ctk.CTkButton(buttons,text="Nuevo / Registrar",command=lambda:self.edit_record(table,fields,None,None)).pack(side="left",padx=5,pady=8)
        ctk.CTkButton(buttons,text="Editar seleccionado",command=lambda:self.edit_selected(table,fields)).pack(side="left",padx=5)
        ctk.CTkButton(buttons,text="Eliminar seleccionado",fg_color="#a33",hover_color="#822",command=lambda:self.delete_selected(table)).pack(side="left",padx=5)
        ctk.CTkButton(buttons,text="Actualizar listado",command=lambda:self.refresh(table)).pack(side="right",padx=5)
        self.refresh(table)
    def refresh(self, table):
        tree=getattr(self,f"tree_{table}")
        tree.delete(*tree.get_children())
        try:
            rows=self.controller.list_rows(table)
            key={"Libros":"ISBN","Autores":"IdAutor","Editoriales":"IdEditorial","Usuarios":"IdUsuario"}[table]
            for row in rows:
                vals=[row.get(key,"")]
                vals += [row.get(c,"") for c in tree["columns"][1:]]
                tree.insert("", "end", values=vals)
        except Exception as exc: messagebox.showerror("Error de base de datos",str(exc))
    def selected(self, table):
        tree=getattr(self,f"tree_{table}")
        selection=tree.selection()
        if not selection: messagebox.showwarning("Selección requerida","Seleccione un registro en la tabla."); return None
        return tree.item(selection[0],"values")
    def edit_selected(self, table, fields):
        values=self.selected(table)
        if values is None:return
        key=values[0]
        row={c:values[i+1] for i,c in enumerate(fields)}
        self.edit_record(table,fields,row,key)
    def edit_record(self, table, fields, row, key_value):
        if table == "Libros":
            self.edit_book_record(row, key_value)
            return
        dialog=ctk.CTkToplevel(self); dialog.title("Registro · "+table); dialog.geometry("480x560"); dialog.grab_set()
        entries={}
        ctk.CTkLabel(dialog,text=("Editar" if row else "Registrar")+" · "+table,font=ctk.CTkFont(size=20,weight="bold")).pack(pady=12)
        body=ctk.CTkScrollableFrame(dialog); body.pack(fill="both",expand=True,padx=12,pady=8)
        for field,(label,kind) in fields.items():
            ctk.CTkLabel(body,text=label).pack(anchor="w",padx=8,pady=(8,2))
            ent=ctk.CTkEntry(body); ent.pack(fill="x",padx=8)
            if row and field in row: ent.insert(0,str(row[field]))
            entries[field]=ent
        def save():
            vals={}
            for field,(label,kind) in fields.items():
                value=entries[field].get().strip()
                if not value: messagebox.showwarning("Validación",f"El campo {label} es obligatorio.",parent=dialog);return
                if kind=="int":
                    try: value=int(value)
                    except ValueError: messagebox.showwarning("Validación",f"{label} debe ser entero.",parent=dialog);return
                    if field=="Existencias" and value<0: messagebox.showwarning("Validación","Existencias no puede ser negativo.",parent=dialog);return
                if kind=="date":
                    try: date.fromisoformat(value)
                    except ValueError: messagebox.showwarning("Validación","Fecha con formato YYYY-MM-DD.",parent=dialog);return
                vals[field]=value
            try:
                self.controller.save(table,vals,key_value)
                dialog.destroy();self.refresh(table)
                messagebox.showinfo("AcaBiblioteca","Registro guardado correctamente.")
            except Exception as exc: messagebox.showerror("No se pudo guardar",str(exc),parent=dialog)
        ctk.CTkButton(dialog,text="Guardar",command=save).pack(pady=12)
    def edit_book_record(self, row=None, key_value=None):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Registro de libros")
        dialog.geometry("520x750")
        dialog.grab_set()

        body = ctk.CTkScrollableFrame(dialog)
        body.pack(fill="both", expand=True, padx=12, pady=12)

        ctk.CTkLabel(
            body,
            text="Registrar libro" if row is None else "Editar libro",
            font=ctk.CTkFont(size=20, weight="bold")
        ).pack(pady=12)

        entries = {}

        def add_field(label, key, value=""):
            ctk.CTkLabel(body, text=label).pack(anchor="w", padx=8, pady=(8, 2))
            entry = ctk.CTkEntry(body)
            entry.pack(fill="x", padx=8)
            entry.insert(0, str(value or ""))
            entries[key] = entry

        add_field("ISBN", "ISBN", row.get("ISBN", "") if row else "")
        add_field("Título", "Titulo", row.get("Titulo", "") if row else "")
        add_field("Categoría", "Categoria", row.get("Categoria", "") if row else "")
        add_field("Año", "Anio", row.get("Anio", "") if row else "")
        add_field("Existencias", "Existencias", row.get("Existencias", 0) if row else 0)

        try:
            authors = self.controller.list_choices("Autores")
            publishers = self.controller.list_choices("Editoriales")
        except Exception as exc:
            messagebox.showerror("Error", str(exc), parent=dialog)
            dialog.destroy()
            return

        author_map = {str(name): int(identifier) for identifier, name in authors}
        publisher_map = {str(name): int(identifier) for identifier, name in publishers}

        ctk.CTkLabel(body, text="Seleccionar autor existente").pack(
            anchor="w", padx=8, pady=(12, 2)
        )

        author_names = [""] + list(author_map.keys())
        author_box = ctk.CTkComboBox(body, values=author_names)
        author_box.pack(fill="x", padx=8)
        author_box.set(row.get("Autor", "") if row else "")

        ctk.CTkLabel(body, text="O registrar un autor nuevo").pack(
            anchor="w", padx=8, pady=(12, 2)
        )

        add_field("Nombre del autor", "NuevoNombreAutor")
        add_field("Apellido del autor", "NuevoApellidoAutor")

        ctk.CTkLabel(body, text="Seleccionar editorial existente").pack(
            anchor="w", padx=8, pady=(12, 2)
        )

        publisher_names = [""] + list(publisher_map.keys())
        publisher_box = ctk.CTkComboBox(body, values=publisher_names)
        publisher_box.pack(fill="x", padx=8)
        publisher_box.set(row.get("Editorial", "") if row else "")

        ctk.CTkLabel(body, text="O registrar una editorial nueva").pack(
            anchor="w", padx=8, pady=(12, 2)
        )

        add_field("Nombre de la editorial", "NuevaEditorial")

        def save():
            try:
                isbn = entries["ISBN"].get().strip()
                titulo = entries["Titulo"].get().strip()
                categoria = entries["Categoria"].get().strip()

                if not isbn or not titulo or not categoria:
                    messagebox.showwarning(
                        "Validación",
                        "ISBN, título y categoría son obligatorios.",
                        parent=dialog
                    )
                    return

                anio = int(entries["Anio"].get().strip())
                existencias = int(entries["Existencias"].get().strip())

                if anio <= 0 or existencias < 0:
                    raise ValueError("Año o existencias no válidos.")

                nuevo_nombre = entries["NuevoNombreAutor"].get().strip()
                nuevo_apellido = entries["NuevoApellidoAutor"].get().strip()
                autor_seleccionado = author_box.get().strip()

                if nuevo_nombre:
                    id_autor = self.controller.save(
                        "Autores",
                        {
                            "Nombre": nuevo_nombre,
                            "Apellido": nuevo_apellido
                        }
                    )
                elif autor_seleccionado in author_map:
                    id_autor = author_map[autor_seleccionado]
                else:
                    messagebox.showwarning(
                        "Autor",
                        "Selecciona un autor o registra uno nuevo.",
                        parent=dialog
                    )
                    return

                nueva_editorial = entries["NuevaEditorial"].get().strip()
                editorial_seleccionada = publisher_box.get().strip()

                if nueva_editorial:
                    id_editorial = self.controller.save(
                        "Editoriales",
                        {"Nombre": nueva_editorial}
                    )
                elif editorial_seleccionada in publisher_map:
                    id_editorial = publisher_map[editorial_seleccionada]
                else:
                    messagebox.showwarning(
                        "Editorial",
                        "Selecciona una editorial o registra una nueva.",
                        parent=dialog
                    )
                    return

                values = {
                    "ISBN": isbn,
                    "Titulo": titulo,
                    "IdAutor": id_autor,
                    "IdEditorial": id_editorial,
                    "Categoria": categoria,
                    "Anio": anio,
                    "Existencias": existencias
                }

                self.controller.save("Libros", values, key_value)

                dialog.destroy()
                self.refresh("Libros")

                messagebox.showinfo(
                    "AcaBiblioteca",
                    "Libro guardado correctamente."
                )

            except ValueError as exc:
                messagebox.showwarning("Validación", str(exc), parent=dialog)
            except Exception as exc:
                messagebox.showerror("Error al guardar", str(exc), parent=dialog)

        ctk.CTkButton(
            body,
            text="Guardar libro",
            command=save
        ).pack(pady=18)
    def delete_selected(self, table):
        values = self.selected(table)
        if values is None:
            return
    def search_book(self):
        isbn=self.isbn_search.get().strip()
        if not isbn: messagebox.showwarning("ISBN","Ingrese el ISBN a buscar.");return
        try:
            row=self.controller.search_isbn(isbn)
            if not row: messagebox.showinfo("Búsqueda","No se encontró un libro con ese ISBN.");return
            messagebox.showinfo("Libro encontrado","\n".join(f"{k}: {v}" for k,v in row.items()))
        except Exception as exc: messagebox.showerror("Error",str(exc))
    def build_loans(self):
        frame=self.tabs.tab("Préstamos")
        ctk.CTkLabel(frame,text="Préstamos y devoluciones",font=ctk.CTkFont(size=19,weight="bold")).pack(anchor="w",padx=12,pady=12)
        form=ctk.CTkFrame(frame);form.pack(fill="x",padx=12,pady=8)
        self.loan_user=ctk.CTkEntry(form,placeholder_text="ID usuario");self.loan_user.pack(side="left",padx=8,pady=10)
        self.loan_isbn=ctk.CTkEntry(form,placeholder_text="ISBN libro");self.loan_isbn.pack(side="left",padx=8)
        self.loan_due=ctk.CTkEntry(form,placeholder_text="Vencimiento YYYY-MM-DD");self.loan_due.pack(side="left",padx=8)
        ctk.CTkButton(form,text="Registrar préstamo",command=self.create_loan).pack(side="left",padx=8)
        self.loan_tree=ttk.Treeview(frame,columns=("ID","Libro","Usuario","Prestamo","Vence","Devuelto","Estado"),show="headings",height=15)
        self.loan_tree.pack(fill="both",expand=True,padx=12,pady=8)
        for c in self.loan_tree["columns"]:self.loan_tree.heading(c,text=c);self.loan_tree.column(c,width=125)
        buttons=ctk.CTkFrame(frame);buttons.pack(fill="x",padx=12,pady=8)
        ctk.CTkButton(buttons,text="Registrar devolución",command=self.return_selected).pack(side="left",padx=5)
        ctk.CTkButton(buttons,text="Actualizar",command=self.refresh_loans).pack(side="right",padx=5)
        self.refresh_loans()
    def refresh_loans(self):
        self.loan_tree.delete(*self.loan_tree.get_children())
        try:
            for r in self.controller.list_loans():
                self.loan_tree.insert("","end",values=(r["IdPrestamo"],r["Titulo"],r["Nombre"]+" "+r["Apellido"],r["FechaPrestamo"],r["FechaVencimiento"],r["FechaDevolucion"] or "",r["Estado"]))
        except Exception as exc:messagebox.showerror("Préstamos",str(exc))
    def create_loan(self):
        try:
            user=int(self.loan_user.get().strip()); isbn=self.loan_isbn.get().strip()
            due=date.fromisoformat(self.loan_due.get().strip())
            self.controller.loan_book(user,isbn,due.isoformat())
            messagebox.showinfo("Préstamo","Préstamo registrado y existencias actualizadas.")
            self.refresh_loans();self.refresh("Libros")
        except Exception as exc:messagebox.showerror("No se pudo registrar",str(exc))
    def return_selected(self):
        sel=self.loan_tree.selection()
        if not sel:messagebox.showwarning("Selección","Seleccione un préstamo.");return
        loan_id=self.loan_tree.item(sel[0],"values")[0]
        try:
            self.controller.return_loan(int(loan_id))
            messagebox.showinfo("Devolución","Devolución registrada y existencias restituidas.")
            self.refresh_loans();self.refresh("Libros")
        except Exception as exc:messagebox.showerror("Devolución",str(exc))
