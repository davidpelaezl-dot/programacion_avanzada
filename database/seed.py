"""
Generador de datos ficticios para AcaBiblioteca.
Utiliza Faker (es_CO) y la conexión existente de config.database.

Uso:
    python -m database.seed
    python -m database.seed --reset --confirmar BORRAR_DATOS
    python -m database.seed --help
"""

import argparse
import random
from datetime import date, timedelta
from uuid import uuid4

from faker import Faker

from config.database import get_connection


fake = Faker("es_CO")
rng = random.Random()


CATEGORIAS = [
    "Novela",
    "Ciencia ficción",
    "Historia",
    "Tecnología",
    "Informática",
    "Filosofía",
    "Educación",
    "Psicología",
    "Literatura",
    "Ciencia",
    "Desarrollo personal",
    "Arte",
]

TIPOS_REPORTE = ["Inventario", "Préstamos", "Devoluciones"]


def generar_isbn():
    """Genera un ISBN-13 con dígito de control válido."""
    base = "978" + "".join(str(rng.randint(0, 9)) for _ in range(9))
    suma = sum(
        int(digito) * (1 if posicion % 2 == 0 else 3)
        for posicion, digito in enumerate(base)
    )
    control = (10 - suma % 10) % 10
    return base + str(control)


def generar_documento(documentos_usados):
    while True:
        documento = str(rng.randint(1000000000, 9999999999))
        if documento not in documentos_usados:
            documentos_usados.add(documento)
            return documento


def generar_correo(correos_usados):
    while True:
        correo = f"{uuid4().hex[:12]}@ejemplo.com"
        if correo not in correos_usados:
            correos_usados.add(correo)
            return correo


def generar_editorial(editoriales_usadas):
    while True:
        nombre = f"Editorial {fake.company()}"
        if nombre not in editoriales_usadas:
            editoriales_usadas.add(nombre)
            return nombre


def limpiar_datos(cursor):
    """Elimina registros sin modificar tablas ni relaciones."""
    tablas = [
        "Prestamos",
        "Libros",
        "Usuarios",
        "Autores",
        "Editoriales",
        "Reportes",
        "RegistroEliminaciones",
    ]

    for tabla in tablas:
        cursor.execute(f"DELETE FROM `{tabla}`")
        print(f"Registros anteriores eliminados: {tabla}")


def crear_autores(cursor, cantidad):
    ids = []

    for _ in range(cantidad):
        cursor.execute(
            """
            INSERT INTO Autores (Nombre, Apellido)
            VALUES (%s, %s)
            """,
            (fake.first_name(), fake.last_name()),
        )
        ids.append(cursor.lastrowid)

    return ids


def crear_editoriales(cursor, cantidad):
    cursor.execute("SELECT Nombre FROM Editoriales")
    usadas = {fila[0] for fila in cursor.fetchall()}

    ids = []

    for _ in range(cantidad):
        nombre = generar_editorial(usadas)

        cursor.execute(
            "INSERT INTO Editoriales (Nombre) VALUES (%s)",
            (nombre,),
        )
        ids.append(cursor.lastrowid)

    return ids


def crear_usuarios(cursor, cantidad):
    cursor.execute("SELECT Documento FROM Usuarios")
    documentos = {fila[0] for fila in cursor.fetchall()}

    cursor.execute("SELECT Correo FROM Usuarios")
    correos = {fila[0] for fila in cursor.fetchall()}

    ids = []

    for _ in range(cantidad):
        nombre = fake.first_name()
        apellido = fake.last_name()

        cursor.execute(
            """
            INSERT INTO Usuarios
                (Nombre, Apellido, Documento, Correo, Telefono)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (
                nombre,
                apellido,
                generar_documento(documentos),
                generar_correo(correos),
                "+57" + fake.numerify(text="##########"),
            ),
        )
        ids.append(cursor.lastrowid)

    return ids


def crear_libros(cursor, cantidad, autores, editoriales):
    cursor.execute("SELECT ISBN FROM Libros")
    isbns_usados = {fila[0] for fila in cursor.fetchall()}

    libros = []

    for _ in range(cantidad):
        while True:
            isbn = generar_isbn()
            if isbn not in isbns_usados:
                isbns_usados.add(isbn)
                break

        titulo = f"{fake.catch_phrase()} {fake.word()}"
        titulo = titulo[:240]

        existencias = rng.randint(3, 10)

        cursor.execute(
            """
            INSERT INTO Libros
                (ISBN, Titulo, IdAutor, IdEditorial,
                 Categoria, Anio, Existencias)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (
                isbn,
                titulo,
                rng.choice(autores),
                rng.choice(editoriales),
                rng.choice(CATEGORIAS),
                rng.randint(1950, date.today().year),
                existencias,
            ),
        )

        libros.append({
            "isbn": isbn,
            "disponibles": existencias,
        })

    return libros


def crear_prestamos(cursor, cantidad, usuarios, libros):
    if cantidad and (not usuarios or not libros):
        raise ValueError(
            "Para generar préstamos necesitas usuarios y libros."
        )

    creados = 0
    activos = 0
    devueltos = 0
    hoy = date.today()

    for _ in range(cantidad):
        estado = "Devuelto" if rng.random() < 0.65 else "Prestado"

        if estado == "Prestado":
            disponibles = [libro for libro in libros if libro["disponibles"] > 0]

            if not disponibles:
                raise ValueError(
                    "No hay existencias suficientes para los préstamos activos. "
                    "Aumenta la cantidad de libros o reduce los préstamos."
                )

            libro = rng.choice(disponibles)
            libro["disponibles"] -= 1
            fecha_prestamo = hoy - timedelta(days=rng.randint(1, 365))
            fecha_vencimiento = fecha_prestamo + timedelta(days=14)
            fecha_devolucion = None
            activos += 1

        else:
            libro = rng.choice(libros)
            fecha_prestamo = hoy - timedelta(days=rng.randint(10, 365))
            fecha_vencimiento = fecha_prestamo + timedelta(days=14)

            max_dias = max(1, (hoy - fecha_prestamo).days)
            fecha_devolucion = fecha_prestamo + timedelta(
                days=rng.randint(1, max_dias)
            )
            devueltos += 1

        cursor.execute(
            """
            INSERT INTO Prestamos
                (ISBN, IdUsuario, FechaPrestamo,
                 FechaVencimiento, FechaDevolucion, Estado)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (
                libro["isbn"],
                rng.choice(usuarios),
                fecha_prestamo,
                fecha_vencimiento,
                fecha_devolucion,
                estado,
            ),
        )
        creados += 1

    # Guardar existencias disponibles después de los préstamos activos.
    for libro in libros:
        cursor.execute(
            "UPDATE Libros SET Existencias = %s WHERE ISBN = %s",
            (libro["disponibles"], libro["isbn"]),
        )

    return creados, activos, devueltos


def crear_reportes(cursor, cantidad):
    for numero in range(1, cantidad + 1):
        tipo = TIPOS_REPORTE[(numero - 1) % len(TIPOS_REPORTE)]

        contenido = (
            f"REPORTE FICTICIO DE {tipo.upper()}\n\n"
            f"Generado automáticamente para pruebas de AcaBiblioteca.\n"
            f"Fecha de generación: {date.today().isoformat()}\n"
            "Los datos de este documento son ficticios.\n"
        )

        cursor.execute(
            """
            INSERT INTO Reportes
                (NombreReporte, TipoReporte, Contenido, RutaArchivo)
            VALUES (%s, %s, %s, NULL)
            """,
            (
                f"Reporte de prueba {numero} - {tipo}",
                tipo,
                contenido,
            ),
        )


def generar_datos(args):
    conexion = None
    cursor = None

    try:
        conexion = get_connection()
        conexion.start_transaction()
        cursor = conexion.cursor()

        if args.reset:
            limpiar_datos(cursor)

        print("\nGenerando datos ficticios...\n")

        autores = crear_autores(cursor, args.autores)
        editoriales = crear_editoriales(cursor, args.editoriales)
        usuarios = crear_usuarios(cursor, args.usuarios)
        libros = crear_libros(
            cursor, args.libros, autores, editoriales
        )

        prestamos, activos, devueltos = crear_prestamos(
            cursor, args.prestamos, usuarios, libros
        )

        crear_reportes(cursor, args.reportes)

        # No se inventan registros históricos de eliminaciones.
        registros_eliminaciones = 0

        conexion.commit()

        print("\n" + "=" * 45)
        print("GENERACIÓN COMPLETADA CORRECTAMENTE")
        print("=" * 45)
        print(f"Autores:                 {len(autores)}")
        print(f"Editoriales:             {len(editoriales)}")
        print(f"Usuarios:                 {len(usuarios)}")
        print(f"Libros:                   {len(libros)}")
        print(f"Préstamos:                {prestamos}")
        print(f"  - Activos:              {activos}")
        print(f"  - Devueltos:            {devueltos}")
        print(f"Reportes:                 {args.reportes}")
        print(f"RegistroEliminaciones:    {registros_eliminaciones}")
        print("=" * 45)

    except Exception:
        if conexion:
            conexion.rollback()
        print("\nERROR: No se completó la operación.")
        print("Se ejecutó rollback; no se guardaron los cambios.")
        raise

    finally:
        if cursor:
            cursor.close()
        if conexion:
            conexion.close()


def main():
    parser = argparse.ArgumentParser(
        description="Generador Faker para AcaBiblioteca."
    )

    parser.add_argument("--autores", type=int, default=30)
    parser.add_argument("--editoriales", type=int, default=15)
    parser.add_argument("--usuarios", type=int, default=100)
    parser.add_argument("--libros", type=int, default=150)
    parser.add_argument("--prestamos", type=int, default=100)
    parser.add_argument("--reportes", type=int, default=6)

    parser.add_argument(
        "--reset",
        action="store_true",
        help="Eliminar los registros anteriores antes de generar.",
    )
    parser.add_argument(
        "--confirmar",
        default="",
        help="Confirmación obligatoria: BORRAR_DATOS.",
    )

    args = parser.parse_args()

    cantidades = [
        args.autores,
        args.editoriales,
        args.usuarios,
        args.libros,
        args.prestamos,
        args.reportes,
    ]

    if any(cantidad < 0 for cantidad in cantidades):
        parser.error("Las cantidades no pueden ser negativas.")

    if args.prestamos and (
        args.usuarios == 0
        or args.libros == 0
        or args.autores == 0
        or args.editoriales == 0
    ):
        parser.error(
            "Para generar préstamos necesitas autores, editoriales, "
            "libros y usuarios."
        )

    if args.reset and args.confirmar != "BORRAR_DATOS":
        parser.error(
            "Para reiniciar la base de datos debes agregar "
            "--confirmar BORRAR_DATOS."
        )

    generar_datos(args)


if __name__ == "__main__":
    main()
