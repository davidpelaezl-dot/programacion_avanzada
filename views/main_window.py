import customtkinter as ctk
from tkinter import ttk, messagebox, filedialog
from controllers.library_controller import LibraryController
from controllers import validators
from models.entities import AUTHOR_FIELDS, PUBLISHER_FIELDS, USER_FIELDS, BOOK_FIELDS
from datetime import date, datetime
from pathlib import Path
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
        for name in ["Libros", "Autores", "Editoriales", "Usuarios", "Préstamos", "Reportes"]:
            self.tabs.add(name)
        self.build_crud("Libros",BOOK_FIELDS)
        self.build_crud("Autores",AUTHOR_FIELDS)
        self.build_crud("Editoriales",PUBLISHER_FIELDS)
        self.build_crud("Usuarios",USER_FIELDS)
        self.build_loans()
        self.build_reports()
    def refresh_reports(self):
        for widget in self.report_content.winfo_children():
            widget.destroy()

        try:
            reports = self.controller.get_reports()

            # Inventario
            inventory = reports["inventario"]
            ctk.CTkLabel(
                self.report_content,
                text="INVENTARIO",
                font=ctk.CTkFont(size=17, weight="bold")
            ).pack(anchor="w", padx=10, pady=(10, 5))

            inventory_frame = ctk.CTkFrame(self.report_content)
            inventory_frame.pack(fill="x", padx=10, pady=5)

            inventory_items = [
                ("Libros registrados", inventory["total_libros"]),
                ("Existencias totales", inventory["existencias_totales"]),
                ("Libros agotados", inventory["agotados"] or 0)
            ]

            for label, value in inventory_items:
                ctk.CTkLabel(
                    inventory_frame,
                    text=f"{label}: {value}",
                    font=ctk.CTkFont(size=15)
                ).pack(anchor="w", padx=12, pady=5)

            # Préstamos
            loans = reports["prestamos"]
            ctk.CTkLabel(
                self.report_content,
                text="PRÉSTAMOS",
                font=ctk.CTkFont(size=17, weight="bold")
            ).pack(anchor="w", padx=10, pady=(15, 5))

            loans_frame = ctk.CTkFrame(self.report_content)
            loans_frame.pack(fill="x", padx=10, pady=5)

            loan_items = [
                ("Total de préstamos", loans["total"] or 0),
                ("Préstamos activos", loans["activos"] or 0),
                ("Préstamos devueltos", loans["devueltos"] or 0),
                ("Préstamos vencidos", reports["vencidos"]["vencidos"])
            ]

            for label, value in loan_items:
                ctk.CTkLabel(
                    loans_frame,
                    text=f"{label}: {value}",
                    font=ctk.CTkFont(size=15)
                ).pack(anchor="w", padx=12, pady=5)

            # Catálogo
            ctk.CTkLabel(
                self.report_content,
                text="CATÁLOGO DE LIBROS",
                font=ctk.CTkFont(size=17, weight="bold")
            ).pack(anchor="w", padx=10, pady=(15, 5))

            columns = (
                "ISBN", "Título", "Autor", "Editorial",
                "Categoría", "Año", "Existencias"
            )

            tree = ttk.Treeview(
                self.report_content,
                columns=columns,
                show="headings",
                height=8
            )
            tree.pack(fill="both", expand=True, padx=10, pady=8)

            for column in columns:
                tree.heading(column, text=column)
                tree.column(column, width=120, anchor="center")

            for book in reports["catalogo"]:
                tree.insert(
                    "",
                    "end",
                    values=(
                        book["ISBN"],
                        book["Titulo"],
                        book["Autor"],
                        book["Editorial"],
                        book["Categoria"],
                        book["Anio"],
                        book["Existencias"]
                    )
                )

        except Exception as exc:
            messagebox.showerror("Error en reportes", str(exc))
        self.refresh_report_history()
        footer=ctk.CTkLabel(self,text="AcaBiblioteca · Datos locales en MySQL",text_color="gray")
        footer.pack(pady=(0,8))
    def refresh_report_history(self):
        self.saved_reports_tree = None
        ctk.CTkLabel(
            self.report_content,
            text="HISTORIAL DE INFORMES",
            font=ctk.CTkFont(size=17, weight="bold")
        ).pack(anchor="w", padx=10, pady=(20, 5))

        try:
            reports = self.controller.list_saved_reports()
        except Exception as exc:
            ctk.CTkLabel(
                self.report_content,
                text=f"No se pudo consultar el historial: {exc}",
                text_color="#d66"
            ).pack(anchor="w", padx=10, pady=5)
            return

        if not reports:
            ctk.CTkLabel(
                self.report_content,
                text="Todavía no hay informes guardados en el historial."
            ).pack(anchor="w", padx=10, pady=5)
            return

        history_frame = ctk.CTkFrame(self.report_content)
        history_frame.pack(fill="x", padx=10, pady=5)

        columns = ("ID", "Nombre", "Tipo", "Fecha de generación")
        self.saved_reports_tree = ttk.Treeview(
            history_frame,
            columns=columns,
            show="headings",
            height=6
        )

        widths = {
            "ID": 55,
            "Nombre": 230,
            "Tipo": 120,
            "Fecha de generación": 180
        }

        for column in columns:
            self.saved_reports_tree.heading(column, text=column)
            self.saved_reports_tree.column(
                column,
                width=widths[column],
                anchor="center"
            )

        self.saved_reports_tree.pack(fill="x", padx=8, pady=8)

        for report in reports:
            self.saved_reports_tree.insert(
                "",
                "end",
                values=(
                    report["IdReporte"],
                    report["NombreReporte"],
                    report["TipoReporte"],
                    report["FechaGeneracion"]
                )
            )

        self.saved_reports_tree.bind(
            "<Double-1>",
            lambda event: self.view_saved_report()
        )

    def choose_saved_report(self, report_type):
        report_types = {
            "Informe inventario": "Inventario",
            "Informe préstamo": "Préstamos",
            "Informe devolución": "Devoluciones"
        }
        report_type = report_types.get(report_type, report_type)

        try:
            reports = [
                report
                for report in self.controller.list_saved_reports()
                if report["TipoReporte"] == report_type
            ]
        except Exception as exc:
            messagebox.showerror(
                "Error de consulta",
                f"No se pudieron cargar los informes: {exc}"
            )
            return

        if not reports:
            messagebox.showinfo(
                "Sin informes",
                f"No hay informes guardados de tipo {report_type}."
            )
            return

        win = ctk.CTkToplevel(self)
        win.title(f"Seleccionar informe | {report_type}")
        win.geometry("720x420")
        win.transient(self)
        win.grab_set()

        ctk.CTkLabel(
            win,
            text=f"Informes guardados de {report_type}",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(anchor="w", padx=12, pady=12)

        columns = ("ID", "Nombre", "Fecha de generación")
        tree = ttk.Treeview(
            win,
            columns=columns,
            show="headings",
            height=10
        )

        tree.heading("ID", text="ID")
        tree.heading("Nombre", text="Nombre del informe")
        tree.heading("Fecha de generación", text="Fecha de generación")

        tree.column("ID", width=60, anchor="center")
        tree.column("Nombre", width=300)
        tree.column("Fecha de generación", width=200, anchor="center")

        tree.pack(fill="both", expand=True, padx=12, pady=8)

        for report in reports:
            tree.insert(
                "",
                "end",
                values=(
                    report["IdReporte"],
                    report["NombreReporte"],
                    report["FechaGeneracion"]
                )
            )

        def consultar():
            seleccion = tree.selection()

            if not seleccion:
                messagebox.showwarning(
                    "Selección requerida",
                    "Selecciona el informe que deseas consultar.",
                    parent=win
                )
                return

            report_id = tree.item(seleccion[0], "values")[0]
            win.destroy()
            self.view_saved_report(report_id)

        botones = ctk.CTkFrame(win)
        botones.pack(fill="x", padx=12, pady=10)

        ctk.CTkButton(
            botones,
            text="Consultar informe",
            command=consultar
        ).pack(side="left", padx=8, pady=8)

        ctk.CTkButton(
            botones,
            text="Cerrar",
            command=win.destroy
        ).pack(side="right", padx=8, pady=8)

        tree.bind("<Double-1>", lambda event: consultar())

    def view_saved_report(self, report_id=None):
        if report_id is None:
            if (
                self.saved_reports_tree is None
                or not self.saved_reports_tree.winfo_exists()
            ):
                messagebox.showwarning(
                    "Historial vacío",
                    "Todavía no hay informes disponibles para consultar."
                )
                return

            seleccion = self.saved_reports_tree.selection()

            if not seleccion:
                messagebox.showwarning(
                    "Selección requerida",
                    "Seleccione un informe del historial."
                )
                return

            report_id = self.saved_reports_tree.item(
                seleccion[0], "values"
            )[0]

        try:
            report = self.controller.get_saved_report(int(report_id))

            if report is None:
                messagebox.showerror(
                    "Informe no encontrado",
                    "El informe seleccionado ya no existe en la base de datos."
                )
                self.refresh_reports()
                return

        except Exception as exc:
            messagebox.showerror("Error al consultar el informe", str(exc))
            return

        win = ctk.CTkToplevel(self)
        win.title(f"Historial | {report['NombreReporte']}")
        win.geometry("780x620")
        win.transient(self)

        ruta = report.get("RutaArchivo") or "No se registró una ruta de archivo."

        ctk.CTkLabel(
            win,
            text=(
                f"Tipo: {report['TipoReporte']}    "
                f"Fecha: {report['FechaGeneracion']}\\n"
                f"Archivo: {ruta}"
            ),
            justify="left",
            wraplength=740
        ).pack(anchor="w", padx=12, pady=10)

        textbox = ctk.CTkTextbox(
            win,
            wrap="none",
            font=ctk.CTkFont(family="monospace", size=13)
        )
        textbox.pack(fill="both", expand=True, padx=12, pady=6)
        textbox.insert("1.0", report["Contenido"] or "")
        textbox.configure(state="disabled")

        ctk.CTkButton(
            win,
            text="Cerrar",
            command=win.destroy
        ).pack(anchor="e", padx=12, pady=10)

    def build_crud(self, table, fields):
        frame=self.tabs.tab(table)
        top=ctk.CTkFrame(frame); top.pack(fill="x",padx=10,pady=10)
        ctk.CTkLabel(top,text=f"Gestión de {table.lower()}",font=ctk.CTkFont(size=18,weight="bold")).pack(side="left",padx=10)
        if table=="Libros":
            self.isbn_search=ctk.CTkEntry(top,placeholder_text="Buscar por ISBN",width=180)
            self.isbn_search.pack(side="right",padx=4)
            self.isbn_search.bind("<KeyRelease>", self.update_book_isbn_suggestions)
            ctk.CTkButton(top,text="Buscar ISBN",command=self.search_book,width=100).pack(side="right",padx=4)
            self.isbn_suggestions=ctk.CTkFrame(frame)
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
    def validar_registro(self, table, vals):
        """Aplica las validaciones de formato según la tabla (lanza ValueError)."""
        limpio = dict(vals)
        if table == "Usuarios":
            limpio["Nombre"] = validators.texto(vals["Nombre"], "Nombre", 100)
            limpio["Apellido"] = validators.texto(vals["Apellido"], "Apellido", 100)
            limpio["Documento"] = validators.documento(vals["Documento"])
            limpio["Correo"] = validators.correo(vals["Correo"])
            limpio["Telefono"] = validators.telefono(vals["Telefono"])
        elif table == "Autores":
            limpio["Nombre"] = validators.texto(vals["Nombre"], "Nombre", 100)
            limpio["Apellido"] = validators.texto(vals["Apellido"], "Apellido", 100)
        elif table == "Editoriales":
            limpio["Nombre"] = validators.texto(vals["Nombre"], "Nombre", 160)
        return limpio

    def mensaje_error_bd(self, exc, table):
        """Convierte errores frecuentes de MySQL en mensajes comprensibles."""
        codigo = getattr(exc, "errno", None)
        mensaje = str(exc).lower()

        if codigo == 1062:
            if table == "Libros":
                return "Ya existe un libro registrado con ese ISBN."

            if table == "Usuarios":
                if "documento" in mensaje:
                    return "Ya existe un usuario registrado con ese documento."
                if "correo" in mensaje:
                    return "Ya existe un usuario registrado con ese correo."
                return "El documento o correo ya está registrado."

            if table == "Editoriales":
                return "Ya existe una editorial registrada con ese nombre."

            if table == "Autores":
                return "Ya existe un registro de autor con esos datos."

            return "Ya existe un registro con esos datos."

        if codigo == 1452:
            return (
                "No se puede guardar el registro porque uno de los datos "
                "relacionados no existe. Verifica el autor, la editorial "
                "o el usuario seleccionado."
            )

        if codigo == 1048:
            return "Falta un dato obligatorio. Revisa los campos del formulario."

        return f"No se pudo completar la operación. Detalle técnico: {exc}"

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
                vals=self.validar_registro(table,vals)
            except ValueError as exc:
                messagebox.showwarning("Validación",str(exc),parent=dialog);return
            try:
                self.controller.save(table,vals,key_value)
                dialog.destroy();self.refresh(table)
                messagebox.showinfo("AcaBiblioteca","Registro guardado correctamente.")
            except Exception as exc:
                mensaje = self.mensaje_error_bd(exc, table)
                messagebox.showerror("No se pudo guardar", mensaje, parent=dialog)
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

        def add_field(label, key, value="", parent=None):
            container = parent if parent is not None else body
            ctk.CTkLabel(container, text=label).pack(anchor="w", padx=8, pady=(8, 2))
            entry = ctk.CTkEntry(container)
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

        ctk.CTkLabel(body, text="Autor").pack(
            anchor="w", padx=8, pady=(12, 2)
        )

        author_names = [""] + list(author_map.keys()) + ["Crear nuevo"]
        author_new_frame = ctk.CTkFrame(body, fg_color="transparent")

        def on_author_change(choice):
            if choice == "Crear nuevo":
                author_new_frame.pack(fill="x", padx=4, pady=4)
            else:
                author_new_frame.pack_forget()

        author_box = ctk.CTkComboBox(
            body,
            values=author_names,
            command=on_author_change
        )
        author_box.pack(fill="x", padx=8)
        author_box.set(row.get("Autor", "") if row else "")

        add_field("Nombre del autor", "NuevoNombreAutor", parent=author_new_frame)
        add_field("Apellido del autor", "NuevoApellidoAutor", parent=author_new_frame)
        author_new_frame.pack_forget()

        ctk.CTkLabel(body, text="Editorial").pack(
            anchor="w", padx=8, pady=(12, 2)
        )

        publisher_names = [""] + list(publisher_map.keys()) + ["Crear nuevo"]
        publisher_new_frame = ctk.CTkFrame(body, fg_color="transparent")

        def on_publisher_change(choice):
            if choice == "Crear nuevo":
                publisher_new_frame.pack(fill="x", padx=4, pady=4)
            else:
                publisher_new_frame.pack_forget()

        publisher_box = ctk.CTkComboBox(
            body,
            values=publisher_names,
            command=on_publisher_change
        )
        publisher_box.pack(fill="x", padx=8)
        publisher_box.set(row.get("Editorial", "") if row else "")

        add_field(
            "Nombre de la editorial",
            "NuevaEditorial",
            parent=publisher_new_frame
        )
        publisher_new_frame.pack_forget()

        def save():
            try:
                isbn = validators.isbn(entries["ISBN"].get())
                titulo = validators.texto(
                    entries["Titulo"].get(), "Título", 240
                )
                categoria = validators.texto(
                    entries["Categoria"].get(), "Categoría", 100
                )
                anio = validators.anio(entries["Anio"].get())
                existencias = validators.existencias(
                    entries["Existencias"].get()
                )

                autor_seleccionado = author_box.get().strip()
                nuevo_autor = None

                if autor_seleccionado == "Crear nuevo":
                    nuevo_nombre = validators.texto(
                        entries["NuevoNombreAutor"].get(), "Nombre del autor", 100
                    )
                    nuevo_apellido = validators.texto(
                        entries["NuevoApellidoAutor"].get(), "Apellido del autor", 100
                    )
                    nuevo_autor = {
                        "Nombre": nuevo_nombre,
                        "Apellido": nuevo_apellido
                    }
                    id_autor = None

                elif autor_seleccionado in author_map:
                    id_autor = author_map[autor_seleccionado]

                else:
                    messagebox.showwarning(
                        "Autor",
                        "Selecciona un autor o elige Crear nuevo.",
                        parent=dialog
                    )
                    return

                editorial_seleccionada = publisher_box.get().strip()
                nueva_editorial = None

                if editorial_seleccionada == "Crear nuevo":
                    nueva_editorial = validators.texto(
                        entries["NuevaEditorial"].get(), "Editorial", 160
                    )
                    id_editorial = None

                elif editorial_seleccionada in publisher_map:
                    id_editorial = publisher_map[editorial_seleccionada]

                else:
                    messagebox.showwarning(
                        "Editorial",
                        "Selecciona una editorial o elige Crear nuevo.",
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

                self.controller.save_book_with_relations(
                    values,
                    new_author=nuevo_autor,
                    new_publisher=nueva_editorial,
                    key_value=key_value
                )

                dialog.destroy()
                self.refresh("Libros")

                messagebox.showinfo(
                    "AcaBiblioteca",
                    "Libro guardado correctamente."
                )

            except ValueError as exc:
                messagebox.showwarning("Validación", str(exc), parent=dialog)
            except Exception as exc:
                mensaje = self.mensaje_error_bd(exc, "Libros")
                messagebox.showerror("Error al guardar", mensaje, parent=dialog)

        ctk.CTkButton(
            body,
            text="Guardar libro",
            command=save
        ).pack(pady=18)
    def delete_selected(self, table):
        values = self.selected(table)
        if values is None:
            return

        key_value = values[0]

        try:
            info = self.controller.deletion_info(table, key_value)
        except Exception as exc:
            messagebox.showerror("Error al eliminar", str(exc))
            return

        # Autores y editoriales con libros asociados: no se eliminan
        if info["libros"] > 0:
            messagebox.showwarning(
                "No se puede eliminar",
                f"'{info['descripcion']}' tiene {info['libros']} libro(s) asociado(s).\n"
                "Elimine o reasigne esos libros primero."
            )
            return

        prestamos = info["prestamos"]
        activos = info["activos"]
        exige_texto = activos > 0

        dialog = ctk.CTkToplevel(self)
        dialog.title("Autorización para eliminar")
        dialog.geometry("480x360")
        dialog.grab_set()

        ctk.CTkLabel(
            dialog,
            text="Confirmar eliminación",
            font=ctk.CTkFont(size=20, weight="bold")
        ).pack(pady=(16, 8))

        detalle = f"Se eliminará de {table}:\n{info['descripcion']}\n\n"
        if prestamos > 0:
            detalle += (
                f"También se eliminarán {prestamos} préstamo(s) asociado(s), "
                f"de los cuales {activos} siguen en estado 'Prestado'.\n"
            )
        else:
            detalle += "No tiene préstamos asociados.\n"
        detalle += (
            "\nEsta acción no se puede deshacer. "
            "Quedará un registro en el historial de eliminaciones."
        )

        ctk.CTkLabel(
            dialog,
            text=detalle,
            wraplength=420,
            justify="left"
        ).pack(padx=20, pady=8)

        entrada = None
        if exige_texto:
            ctk.CTkLabel(
                dialog,
                text="Para autorizar, escriba ELIMINAR:"
            ).pack(pady=(8, 2))
            entrada = ctk.CTkEntry(dialog, width=200)
            entrada.pack()

        botones = ctk.CTkFrame(dialog, fg_color="transparent")
        botones.pack(pady=16)

        def confirmar():
            dialog.destroy()
            try:
                self.controller.delete(table, key_value)
                self.refresh(table)
                try:
                    # Los préstamos pudieron cambiar por la cascada
                    if table in ("Libros", "Usuarios"):
                        self.refresh_loans()
                except Exception:
                    pass
                messagebox.showinfo(
                    "AcaBiblioteca",
                    "Registro eliminado correctamente."
                )
            except Exception as exc:
                messagebox.showerror("Error al eliminar", str(exc))

        ctk.CTkButton(
            botones,
            text="Cancelar",
            command=dialog.destroy
        ).pack(side="left", padx=8)

        boton_eliminar = ctk.CTkButton(
            botones,
            text="Eliminar",
            fg_color="#b3261e",
            hover_color="#8c1d18",
            command=confirmar,
            state=("disabled" if exige_texto else "normal")
        )
        boton_eliminar.pack(side="left", padx=8)

        if exige_texto:
            def validar(event=None):
                if entrada.get().strip() == "ELIMINAR":
                    boton_eliminar.configure(state="normal")
                else:
                    boton_eliminar.configure(state="disabled")
            entrada.bind("<KeyRelease>", validar)

    def update_book_isbn_suggestions(self, event=None):
        isbn = self.isbn_search.get().strip()

        for widget in self.isbn_suggestions.winfo_children():
            widget.destroy()

        if not isbn:
            self.isbn_suggestions.pack_forget()
            return

        try:
            resultados = self.controller.search_isbn(isbn)

            if not resultados:
                self.isbn_suggestions.pack_forget()
                return

            for libro in resultados[:8]:
                isbn_libro = str(libro["ISBN"])
                titulo = libro["Titulo"]

                ctk.CTkButton(
                    self.isbn_suggestions,
                    text=f"{isbn_libro} — {titulo}",
                    anchor="w",
                    command=lambda valor=isbn_libro: self.select_book_isbn(valor)
                ).pack(fill="x", padx=5, pady=2)

            self.isbn_suggestions.pack(
                fill="x",
                padx=10,
                pady=(0, 5),
                before=self.tree_Libros
            )

        except Exception as exc:
            self.isbn_suggestions.pack_forget()
            messagebox.showerror("Búsqueda ISBN", str(exc))

    def select_book_isbn(self, isbn):
        self.isbn_search.delete(0, "end")
        self.isbn_search.insert(0, isbn)
        self.isbn_suggestions.pack_forget()

    def search_book(self):
        isbn = self.isbn_search.get().strip()

        if not isbn:
            messagebox.showwarning("ISBN", "Ingrese el ISBN a buscar.")
            return

        try:
            resultados = self.controller.search_isbn(isbn)

            if not resultados:
                messagebox.showinfo(
                    "Búsqueda",
                    "No se encontraron libros con ese ISBN."
                )
                return

            dialog = ctk.CTkToplevel(self)
            dialog.title("Resultados de búsqueda")
            dialog.geometry("650x420")
            dialog.grab_set()

            ctk.CTkLabel(
                dialog,
                text=f"Libros encontrados: {len(resultados)}",
                font=ctk.CTkFont(size=18, weight="bold")
            ).pack(pady=12)

            tree = ttk.Treeview(
                dialog,
                columns=("ISBN", "Titulo"),
                show="headings",
                height=12
            )
            tree.heading("ISBN", text="ISBN")
            tree.heading("Titulo", text="Título")
            tree.column("ISBN", width=150, anchor="center")
            tree.column("Titulo", width=430, anchor="w")
            tree.pack(fill="both", expand=True, padx=15, pady=10)

            for libro in resultados:
                tree.insert(
                    "",
                    "end",
                    values=(libro["ISBN"], libro["Titulo"])
                )

            def select_result():
                seleccion = tree.selection()

                if not seleccion:
                    messagebox.showwarning(
                        "Selección requerida",
                        "Seleccione un libro.",
                        parent=dialog
                    )
                    return

                selected_isbn = tree.item(
                    seleccion[0], "values"
                )[0]

                main_tree = self.tree_Libros
                for item in main_tree.get_children():
                    values = main_tree.item(item, "values")

                    if values and str(values[0]) == str(selected_isbn):
                        main_tree.selection_set(item)
                        main_tree.focus(item)
                        main_tree.see(item)

                        self.isbn_search.delete(0, "end")
                        self.isbn_search.insert(0, selected_isbn)
                        self.isbn_suggestions.pack_forget()

                        dialog.destroy()
                        return

                messagebox.showerror(
                    "Libro no encontrado",
                    "El libro no aparece en el listado principal.",
                    parent=dialog
                )

            def edit_result():
                seleccion = tree.selection()

                if not seleccion:
                    messagebox.showwarning(
                        "Selección requerida",
                        "Seleccione un libro para editar.",
                        parent=dialog
                    )
                    return

                selected_isbn = tree.item(
                    seleccion[0], "values"
                )[0]

                libros = self.controller.list_rows("Libros")
                row = next(
                    (libro for libro in libros
                     if str(libro["ISBN"]) == str(selected_isbn)),
                    None
                )

                if row is None:
                    messagebox.showerror(
                        "Búsqueda",
                        "El libro ya no se encuentra en la base de datos.",
                        parent=dialog
                    )
                    return

                dialog.destroy()
                self.edit_record(
                    "Libros",
                    BOOK_FIELDS,
                    row,
                    selected_isbn
                )

            buttons = ctk.CTkFrame(dialog)
            buttons.pack(fill="x", padx=15, pady=12)

            ctk.CTkButton(
                buttons,
                text="Seleccionar",
                command=select_result
            ).pack(side="left", padx=8, pady=8)

            ctk.CTkButton(
                buttons,
                text="Editar",
                command=edit_result
            ).pack(side="left", padx=8, pady=8)

            ctk.CTkButton(
                buttons,
                text="Cerrar",
                command=dialog.destroy
            ).pack(side="right", padx=8, pady=8)

            tree.bind("<Double-1>", lambda event: edit_result())

        except Exception as exc:
            messagebox.showerror("Error de búsqueda", str(exc))

    def build_loans(self):
        frame=self.tabs.tab("Préstamos")
        ctk.CTkLabel(frame,text="Préstamos y devoluciones",font=ctk.CTkFont(size=19,weight="bold")).pack(anchor="w",padx=12,pady=12)
        form=ctk.CTkFrame(frame);form.pack(fill="x",padx=12,pady=8)
        self.loan_user=ctk.CTkEntry(form,placeholder_text="ID usuario");self.loan_user.pack(side="left",padx=8,pady=10)
        self.loan_isbn=ctk.CTkEntry(form,placeholder_text="ISBN libro")
        self.loan_isbn.pack(side="left",padx=8)
        self.loan_isbn.bind("<KeyRelease>", self.update_loan_isbn_suggestions)
        self.loan_due=ctk.CTkEntry(form,placeholder_text="Vencimiento YYYY-MM-DD");self.loan_due.pack(side="left",padx=8)
        self.loan_suggestions=ctk.CTkFrame(frame)
        ctk.CTkButton(form,text="Registrar préstamo",command=self.create_loan).pack(side="left",padx=8)
        self.loan_tree=ttk.Treeview(frame,columns=("ID","Libro","Usuario","Prestamo","Vence","Devuelto","Estado"),show="headings",height=15)
        self.loan_tree.pack(fill="both",expand=True,padx=12,pady=8)
        for c in self.loan_tree["columns"]:self.loan_tree.heading(c,text=c);self.loan_tree.column(c,width=125)
        buttons=ctk.CTkFrame(frame);buttons.pack(fill="x",padx=12,pady=8)
        ctk.CTkButton(buttons,text="Registrar devolución",command=self.return_selected).pack(side="left",padx=5)
        self.refresh_loans()
    def update_loan_isbn_suggestions(self, event=None):
        isbn = self.loan_isbn.get().strip()

        for widget in self.loan_suggestions.winfo_children():
            widget.destroy()

        if not isbn:
            self.loan_suggestions.pack_forget()
            return

        try:
            resultados = self.controller.search_isbn(isbn)

            if not resultados:
                self.loan_suggestions.pack_forget()
                return

            for libro in resultados[:8]:
                isbn_libro = str(libro["ISBN"])
                titulo = libro["Titulo"]

                ctk.CTkButton(
                    self.loan_suggestions,
                    text=f"{isbn_libro} — {titulo}",
                    anchor="w",
                    command=lambda valor=isbn_libro: self.select_loan_isbn(valor)
                ).pack(fill="x", padx=5, pady=2)

            self.loan_suggestions.pack(
                fill="x",
                padx=12,
                pady=(0, 5),
                before=self.loan_tree
            )

        except Exception as exc:
            self.loan_suggestions.pack_forget()
            messagebox.showerror("Búsqueda ISBN", str(exc))

    def select_loan_isbn(self, isbn):
        self.loan_isbn.delete(0, "end")
        self.loan_isbn.insert(0, isbn)
        self.loan_suggestions.pack_forget()
        self.loan_due.focus_set()

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

    def build_reports(self):
        frame = self.tabs.tab("Reportes")

        ctk.CTkLabel(
            frame,
            text="Panel de reportes",
            font=ctk.CTkFont(size=21, weight="bold")
        ).pack(anchor="w", padx=12, pady=12)

        ctk.CTkLabel(
            frame,
            text="Consulta el estado general de la biblioteca y genera informes en TXT.",
            text_color="gray"
        ).pack(anchor="w", padx=12)

        buttons = ctk.CTkFrame(frame)
        buttons.pack(fill="x", padx=12, pady=12)

        ctk.CTkButton(
            buttons,
            text="Generar / Actualizar reportes",
            command=self.refresh_reports
        ).pack(side="left", padx=8, pady=8)

        self.report_type = ctk.StringVar(value="Informe inventario")

        ctk.CTkOptionMenu(
            buttons,
            variable=self.report_type,
            values=[
                "Informe inventario",
                "Informe préstamo",
                "Informe devolución"
            ],
            width=220
        ).pack(side="left", padx=8, pady=8)

        ctk.CTkButton(
            buttons,
            text="Generar informe TXT",
            command=self.generate_txt_report
        ).pack(side="left", padx=8, pady=8)

        self.consult_report_type = ctk.StringVar(value="Consultar informe")

        ctk.CTkOptionMenu(
            buttons,
            variable=self.consult_report_type,
            values=[
                "Informe inventario",
                "Informe préstamo",
                "Informe devolución"
            ],
            command=self.choose_saved_report,
            width=220
        ).pack(side="left", padx=8, pady=8)

        self.report_content = ctk.CTkScrollableFrame(frame)
        self.report_content.pack(fill="both", expand=True, padx=12, pady=8)

        self.refresh_reports()

    def generate_txt_report(self):
        report_types = {
            "Informe inventario": "Inventario",
            "Informe préstamo": "Préstamos",
            "Informe devolución": "Devoluciones"
        }
        report_type = report_types.get(
            self.report_type.get(),
            self.report_type.get()
        )
        try:
            report_name, content = self.controller.build_report(report_type)
        except Exception as exc:
            messagebox.showerror("Error al generar informe", str(exc))
            return
        self.show_report_preview(report_type, report_name, content)

    def show_report_preview(self, report_type, report_name, content):
        win = ctk.CTkToplevel(self)
        win.title(f"Vista previa | {report_name}")
        win.geometry("780x620")
        win.transient(self)

        textbox = ctk.CTkTextbox(win, wrap="none", font=ctk.CTkFont(family="monospace", size=13))
        textbox.pack(fill="both", expand=True, padx=12, pady=(12, 6))
        textbox.insert("1.0", content)
        textbox.configure(state="disabled")

        buttons = ctk.CTkFrame(win)
        buttons.pack(fill="x", padx=12, pady=(0, 12))
        ctk.CTkButton(
            buttons,
            text="Guardar TXT y en historial",
            command=lambda: self.save_report_file(win, report_type, report_name, content)
        ).pack(side="left", padx=8, pady=8)
        ctk.CTkButton(
            buttons,
            text="Cerrar",
            fg_color="gray",
            command=win.destroy
        ).pack(side="right", padx=8, pady=8)

    def save_report_file(self, win, report_type, report_name, content):
        slugs = {"Inventario": "inventario", "Préstamos": "prestamos", "Devoluciones": "devoluciones"}
        filename = f"informe_{slugs[report_type]}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

        carpeta_informes = Path(__file__).resolve().parent.parent / "informes"
        carpeta_informes.mkdir(exist_ok=True)
        path = str(carpeta_informes / filename)

        try:
            with open(path, "w", encoding="utf-8") as file:
                file.write(content)
        except Exception as exc:
            messagebox.showerror("Error al guardar el archivo", str(exc), parent=win)
            return

        try:
            report_id = self.controller.save_report(report_name, report_type, content, path)
        except Exception as exc:
            messagebox.showwarning(
                "Archivo guardado, historial no",
                f"El TXT se guardó en:\n{path}\n\nPero no se pudo guardar en MySQL:\n{exc}",
                parent=win
            )
            return

        messagebox.showinfo(
            "Informe guardado",
            f"TXT guardado en:\n{path}\n\nRegistrado en el historial con el número {report_id}.",
            parent=self
        )
        if win.winfo_exists():
            win.destroy()
