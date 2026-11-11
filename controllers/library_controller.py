from config.database import get_connection
from datetime import datetime
from controllers import validators

TABLES = {
    "Autores": ("Autores", "IdAutor", ["Nombre", "Apellido"]),
    "Editoriales": ("Editoriales", "IdEditorial", ["Nombre"]),
    "Usuarios": ("Usuarios", "IdUsuario", ["Nombre","Apellido","Documento","Correo","Telefono"]),
    "Libros": ("Libros", "ISBN", ["ISBN","Titulo","IdAutor","IdEditorial","Categoria","Anio","Existencias"]),
}
class LibraryController:
    def list_rows(self, table):
        conn=get_connection()
        try:
            cur=conn.cursor()
            if table=="Libros":
                cur.execute("""SELECT l.ISBN,l.Titulo,CONCAT(a.Nombre,' ',a.Apellido) AS Autor,e.Nombre AS Editorial,
                    l.Categoria,l.Anio,l.Existencias,l.IdAutor,l.IdEditorial
                    FROM Libros l JOIN Autores a ON a.IdAutor=l.IdAutor
                    JOIN Editoriales e ON e.IdEditorial=l.IdEditorial ORDER BY l.Titulo""")
            else:
                cur.execute(f"SELECT * FROM `{table}` ORDER BY 1")
            cols=[d[0] for d in cur.description]
            return [dict(zip(cols,row)) for row in cur.fetchall()]
        finally: conn.close()
    def save(self, table, values, key_value=None):
        name, key, fields = TABLES[table]
        conn = get_connection()

        try:
            cur = conn.cursor()

            if key_value is None:
                columns = ", ".join(f"`{f}`" for f in fields)
                marks = ", ".join(["%s"] * len(fields))

                cur.execute(
                    f"INSERT INTO `{name}` ({columns}) VALUES ({marks})",
                    tuple(values[f] for f in fields)
                )

            else:
                update_fields = fields if table == "Libros" else [
                    f for f in fields if f != key
                ]

                sets = ", ".join(f"`{f}`=%s" for f in update_fields)
                params = [values[f] for f in update_fields] + [key_value]

                cur.execute(
                    f"UPDATE `{name}` SET {sets} WHERE `{key}`=%s",
                    tuple(params)
                )

                if cur.rowcount == 0:
                    raise ValueError("No se encontró el registro que se desea actualizar.")

            conn.commit()

            if key_value is None:
                return cur.lastrowid

            return values[key] if table == "Libros" else key_value

        except Exception:
            conn.rollback()
            raise

        finally:
            conn.close()

    def save_book_with_relations(
        self, values, new_author=None, new_publisher=None, key_value=None
    ):
        """Guarda autor, editorial y libro en una sola transacción MySQL."""
        conn = get_connection()

        try:
            conn.start_transaction()
            cur = conn.cursor()

            values = dict(values)

            if new_author is not None:
                cur.execute(
                    "INSERT INTO Autores (Nombre, Apellido) VALUES (%s, %s)",
                    (new_author["Nombre"], new_author["Apellido"])
                )
                values["IdAutor"] = cur.lastrowid

            if new_publisher is not None:
                cur.execute(
                    "INSERT INTO Editoriales (Nombre) VALUES (%s)",
                    (new_publisher,)
                )
                values["IdEditorial"] = cur.lastrowid

            name, key, fields = TABLES["Libros"]

            if key_value is None:
                columns = ", ".join(f"`{f}`" for f in fields)
                marks = ", ".join(["%s"] * len(fields))

                cur.execute(
                    f"INSERT INTO `{name}` ({columns}) VALUES ({marks})",
                    tuple(values[f] for f in fields)
                )
            else:
                sets = ", ".join(f"`{f}`=%s" for f in fields)
                params = [values[f] for f in fields] + [key_value]

                cur.execute(
                    f"UPDATE `{name}` SET {sets} WHERE `{key}`=%s",
                    tuple(params)
                )

                if cur.rowcount == 0:
                    raise ValueError(
                        "No se encontró el libro que se desea actualizar."
                    )

            conn.commit()
            return values["ISBN"]

        except Exception:
            conn.rollback()
            raise

        finally:
            conn.close()

    def _describir_registro(self, cur, table, key_value):
        consultas = {
            "Libros": "SELECT Titulo FROM Libros WHERE ISBN=%s",
            "Usuarios": "SELECT CONCAT(Nombre,' ',Apellido) FROM Usuarios WHERE IdUsuario=%s",
            "Autores": "SELECT CONCAT(Nombre,' ',Apellido) FROM Autores WHERE IdAutor=%s",
            "Editoriales": "SELECT Nombre FROM Editoriales WHERE IdEditorial=%s",
        }
        cur.execute(consultas[table], (key_value,))
        fila = cur.fetchone()
        if not fila:
            raise ValueError("No se encontró el registro que se desea eliminar.")
        return fila[0]

    def _contar_dependencias(self, cur, table, key_value):
        """Devuelve (préstamos totales, préstamos activos, libros asociados)."""
        prestamos = activos = libros = 0
        if table == "Libros":
            cur.execute(
                "SELECT COUNT(*), COALESCE(SUM(Estado='Prestado'),0) FROM Prestamos WHERE ISBN=%s",
                (key_value,))
            fila = cur.fetchone()
            prestamos, activos = int(fila[0]), int(fila[1])
        elif table == "Usuarios":
            cur.execute(
                "SELECT COUNT(*), COALESCE(SUM(Estado='Prestado'),0) FROM Prestamos WHERE IdUsuario=%s",
                (key_value,))
            fila = cur.fetchone()
            prestamos, activos = int(fila[0]), int(fila[1])
        elif table == "Autores":
            cur.execute("SELECT COUNT(*) FROM Libros WHERE IdAutor=%s", (key_value,))
            libros = int(cur.fetchone()[0])
        elif table == "Editoriales":
            cur.execute("SELECT COUNT(*) FROM Libros WHERE IdEditorial=%s", (key_value,))
            libros = int(cur.fetchone()[0])
        return prestamos, activos, libros

    def deletion_info(self, table, key_value):
        """Informa qué se eliminaría, sin borrar nada."""
        conn = get_connection()
        try:
            cur = conn.cursor()
            descripcion = self._describir_registro(cur, table, key_value)
            prestamos, activos, libros = self._contar_dependencias(cur, table, key_value)
            return {
                "descripcion": descripcion,
                "prestamos": prestamos,
                "activos": activos,
                "libros": libros,
            }
        finally:
            conn.close()

    def delete(self, table, key_value):
        name, key, _ = TABLES[table]
        conn = get_connection()
        try:
            conn.start_transaction()
            cur = conn.cursor()
            descripcion = self._describir_registro(cur, table, key_value)
            prestamos, activos, libros = self._contar_dependencias(cur, table, key_value)
            if libros > 0:
                raise ValueError(
                    f"No se puede eliminar '{descripcion}': tiene {libros} libro(s) asociado(s). "
                    "Elimine o reasigne esos libros primero."
                )
            cur.execute(
                "INSERT INTO RegistroEliminaciones "
                "(TablaAfectada, ClaveRegistro, Descripcion, PrestamosEliminados) "
                "VALUES (%s,%s,%s,%s)",
                (table, str(key_value), str(descripcion)[:255], prestamos)
            )
            cur.execute(f"DELETE FROM `{name}` WHERE `{key}`=%s", (key_value,))
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def search_isbn(self, isbn):
        conn = get_connection()
        try:
            cur = conn.cursor(dictionary=True)
            cur.execute(
                """
                SELECT ISBN, Titulo
                FROM Libros
                WHERE ISBN LIKE %s
                ORDER BY ISBN
                """,
                (f"%{isbn.strip()}%",)
            )
            return cur.fetchall()
        finally:
            conn.close()

    def list_choices(self, table):
        conn=get_connection()
        try:
            cur=conn.cursor()
            if table=="Autores": cur.execute("SELECT IdAutor, CONCAT(Nombre,' ',Apellido) FROM Autores ORDER BY Nombre")
            elif table=="Editoriales": cur.execute("SELECT IdEditorial,Nombre FROM Editoriales ORDER BY Nombre")
            elif table=="Libros": cur.execute("SELECT ISBN,Titulo FROM Libros ORDER BY Titulo")
            elif table=="Usuarios": cur.execute("SELECT IdUsuario,CONCAT(Nombre,' ',Apellido) FROM Usuarios ORDER BY Nombre")
            return cur.fetchall()
        finally: conn.close()
    def loan_book(self, user_id, isbn, due_date):
        due_date = validators.fecha_vencimiento(due_date)
        conn=get_connection()
        try:
            conn.start_transaction()
            cur=conn.cursor()
            cur.execute("SELECT Existencias FROM Libros WHERE ISBN=%s FOR UPDATE",(isbn,))
            row=cur.fetchone()
            if not row: raise ValueError("No existe el libro seleccionado.")
            if row[0] < 1: raise ValueError("No hay existencias disponibles.")
            cur.execute("UPDATE Libros SET Existencias=Existencias-1 WHERE ISBN=%s",(isbn,))
            cur.execute("""INSERT INTO Prestamos (ISBN,IdUsuario,FechaPrestamo,FechaVencimiento,Estado)
                VALUES (%s,%s,CURDATE(),%s,'Prestado')""",(isbn,user_id,due_date))
            conn.commit()
        except Exception:
            conn.rollback(); raise
        finally: conn.close()
    def return_loan(self, loan_id):
        conn=get_connection()
        try:
            conn.start_transaction()
            cur=conn.cursor()
            cur.execute("SELECT ISBN,Estado FROM Prestamos WHERE IdPrestamo=%s FOR UPDATE",(loan_id,))
            row=cur.fetchone()
            if not row: raise ValueError("Préstamo no encontrado.")
            if row[1]=="Devuelto": raise ValueError("Este préstamo ya fue devuelto.")
            cur.execute("UPDATE Prestamos SET Estado='Devuelto',FechaDevolucion=CURDATE() WHERE IdPrestamo=%s",(loan_id,))
            cur.execute("UPDATE Libros SET Existencias=Existencias+1 WHERE ISBN=%s",(row[0],))
            conn.commit()
        except Exception:
            conn.rollback(); raise
        finally: conn.close()
    def list_loans(self):
        conn = get_connection()
        try:
            cur = conn.cursor(dictionary=True)
            cur.execute("""
                SELECT
                    p.IdPrestamo,
                    l.Titulo,
                    l.ISBN,
                    u.Nombre,
                    u.Apellido,
                    u.Correo,
                    u.Telefono,
                    p.FechaPrestamo,
                    p.FechaVencimiento,
                    p.FechaDevolucion,
                    p.Estado,
                    p.IdUsuario
                FROM Prestamos p
                JOIN Libros l ON l.ISBN = p.ISBN
                JOIN Usuarios u ON u.IdUsuario = p.IdUsuario
                ORDER BY p.IdPrestamo DESC
            """)
            return cur.fetchall()
        finally:
            conn.close()
    def get_reports(self):
        conn = get_connection()
        try:
            cur = conn.cursor(dictionary=True)
            reports = {}

            # Resumen del inventario
            cur.execute("""
                SELECT
                    COUNT(*) AS total_libros,
                    COALESCE(SUM(Existencias), 0) AS existencias_totales,
                    (SELECT COUNT(*) FROM Autores) AS total_autores,
                    (SELECT COUNT(*) FROM Editoriales) AS total_editoriales,
                    SUM(CASE WHEN Existencias = 0 THEN 1 ELSE 0 END) AS agotados
                FROM Libros
            """)
            reports["inventario"] = cur.fetchone()

            # Resumen de préstamos
            cur.execute("""
                SELECT
                    COUNT(*) AS total,
                    SUM(CASE WHEN Estado = 'Prestado' THEN 1 ELSE 0 END) AS activos,
                    SUM(CASE WHEN Estado = 'Devuelto' THEN 1 ELSE 0 END) AS devueltos
                FROM Prestamos
            """)
            reports["prestamos"] = cur.fetchone()

            # Préstamos vencidos
            cur.execute("""
                SELECT COUNT(*) AS vencidos
                FROM Prestamos
                WHERE Estado = 'Prestado'
                AND FechaVencimiento < CURDATE()
            """)
            reports["vencidos"] = cur.fetchone()

            # Catálogo de libros
            cur.execute("""
                SELECT
                    l.ISBN,
                    l.Titulo,
                    CONCAT(a.Nombre, ' ', a.Apellido) AS Autor,
                    e.Nombre AS Editorial,
                    l.Categoria,
                    l.Anio,
                    l.Existencias
                FROM Libros l
                INNER JOIN Autores a ON a.IdAutor = l.IdAutor
                INNER JOIN Editoriales e ON e.IdEditorial = l.IdEditorial
                ORDER BY l.Titulo
            """)
            reports["catalogo"] = cur.fetchall()

            return reports

        finally:
            conn.close()

    # ---------- Informes ----------
    def list_loans_by_state(self, estado):
        conn = get_connection()
        try:
            cur = conn.cursor(dictionary=True)
            cur.execute("""
                SELECT
                    p.IdPrestamo,
                    l.Titulo,
                    l.ISBN,
                    u.Nombre,
                    u.Apellido,
                    u.Correo,
                    u.Telefono,
                    p.FechaPrestamo,
                    p.FechaVencimiento,
                    p.FechaDevolucion,
                    p.Estado,
                    p.IdUsuario
                FROM Prestamos p
                JOIN Libros l ON l.ISBN = p.ISBN
                JOIN Usuarios u ON u.IdUsuario = p.IdUsuario
                WHERE p.Estado = %s
                ORDER BY p.IdPrestamo DESC
            """, (estado,))
            return cur.fetchall()
        finally:
            conn.close()

    def build_report(self, report_type):
        names = {
            "Inventario": "Informe de inventario",
            "Préstamos": "Informe de préstamos",
            "Devoluciones": "Informe de devoluciones",
        }
        if report_type not in names:
            raise ValueError(f"Tipo de informe no válido: {report_type}")

        report_name = names[report_type]
        generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        lines = [
            "ACABIBLIOTECA",
            "=" * 60,
            f"Nombre del reporte: {report_name}",
            f"Fecha de generación: {generated_at}",
            "=" * 60,
            "",
        ]

        if report_type == "Inventario":
            data = self.get_reports()
            inv = data["inventario"]
            lines.extend([
                "INFORME GENERAL DE INVENTARIO",
                "-" * 60,
                f"Cantidad de libros registrados: {inv['total_libros']}",
                f"Cantidad total de ejemplares: {inv['existencias_totales']}",
                f"Cantidad de autores: {inv['total_autores']}",
                f"Cantidad de editoriales: {inv['total_editoriales']}",
                f"Libros agotados: {inv['agotados'] or 0}",
                "",
                "DETALLE DEL CATÁLOGO",
                "-" * 60,
            ])
            for book in data["catalogo"]:
                lines.extend([
                    f"ISBN: {book['ISBN']}",
                    f"Título: {book['Titulo']}",
                    f"Autor: {book['Autor']}",
                    f"Editorial: {book['Editorial']}",
                    f"Categoría: {book['Categoria']}",
                    f"Año: {book['Anio']}",
                    f"Existencias: {book['Existencias']}",
                    "-" * 40,
                ])
        else:
            estado = "Prestado" if report_type == "Préstamos" else "Devuelto"
            loans = self.list_loans_by_state(estado)
            lines.extend([
                report_name.upper(),
                "-" * 60,
                f"Total de registros: {len(loans)}",
                "",
            ])
            if not loans:
                lines.append(f"No existen registros con estado {estado}.")
            for loan in loans:
                lines.extend([
                    f"ID del préstamo: {loan['IdPrestamo']}",
                    f"Libro: {loan['Titulo']}",
                    f"ISBN: {loan['ISBN']}",
                    f"Usuario: {loan['Nombre']} {loan['Apellido']}",
                    f"ID del usuario: {loan['IdUsuario']}",
                    f"Correo: {loan['Correo'] or 'No registrado'}",
                    f"Teléfono: {loan['Telefono'] or 'No registrado'}",
                    f"Fecha del préstamo: {loan['FechaPrestamo']}",
                ])
                if report_type == "Préstamos":
                    lines.append(f"Fecha de vencimiento: {loan['FechaVencimiento']}")
                else:
                    lines.append(f"Fecha de devolución: {loan['FechaDevolucion']}")
                lines.extend([f"Estado: {loan['Estado']}", "-" * 50])

        return report_name, "\n".join(lines)

    def save_report(self, report_name, report_type, content, file_path=None):
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO Reportes (NombreReporte, TipoReporte, Contenido, RutaArchivo) "
                "VALUES (%s, %s, %s, %s)",
                (report_name, report_type, content, file_path),
            )
            conn.commit()
            return cur.lastrowid
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def list_saved_reports(self):
        conn = get_connection()
        try:
            cur = conn.cursor(dictionary=True)
            cur.execute("""
                SELECT IdReporte, NombreReporte, TipoReporte, FechaGeneracion, RutaArchivo
                FROM Reportes
                ORDER BY IdReporte DESC
            """)
            return cur.fetchall()
        finally:
            conn.close()

    def get_saved_report(self, report_id):
        conn = get_connection()
        try:
            cur = conn.cursor(dictionary=True)
            cur.execute("SELECT * FROM Reportes WHERE IdReporte = %s", (report_id,))
            return cur.fetchone()
        finally:
            conn.close()
