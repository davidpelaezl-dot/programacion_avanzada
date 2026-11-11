# Mapeo basado en nombres confirmados del código original y propuestas documentadas.
BOOK_FIELDS = {
    "ISBN": ("ISBN", "text"),
    "Titulo": ("Título", "text"),
    "Autor": ("Autor", "text"),
    "Editorial": ("Editorial", "text"),
    "Categoria": ("Categoría", "text"),
    "Anio": ("Año", "int"),
    "Existencias": ("Existencias", "int"),
}

AUTHOR_FIELDS = {
    "Nombre": ("Nombre", "text"),
    "Apellido": ("Apellido", "text")
}

PUBLISHER_FIELDS = {
    "Nombre": ("Nombre", "text")
}

USER_FIELDS = {
    "Nombre": ("Nombre", "text"),
    "Apellido": ("Apellido", "text"),
    "Documento": ("Documento", "text"),
    "Correo": ("Correo", "text"),
    "Telefono": ("Teléfono", "text"),
}

LOAN_FIELDS = {
    "IdLibro": ("Libro (ID)", "int"),
    "IdUsuario": ("Usuario (ID)", "int"),
    "FechaPrestamo": ("Fecha préstamo (YYYY-MM-DD)", "date"),
    "FechaVencimiento": ("Fecha vencimiento (YYYY-MM-DD)", "date"),
}
