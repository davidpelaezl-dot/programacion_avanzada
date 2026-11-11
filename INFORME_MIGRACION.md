# Informe de migración y pruebas — AcaBiblioteca

## Fuente auditada
ZIP `AcaBiblioteca-main.zip`, archivos fuente C# y diseñadores.

## Funcionalidades fuente
- Libros: cargar listado, consultar autores/editoriales para combos, buscar ISBN, registrar, editar, eliminar, validar campos obligatorios, año y existencias enteras.
- Navegación: Inicio, Libros, Usuarios, Autores, Editoriales, Préstamos y Reportes.
- Formularios de autores/editoriales/usuarios/préstamos/reportes: vacío en el código fuente.
- Conexión fuente: SQL Server local `.\SQL2022`, base `AcaBiblioteca`, Windows Integrated Security.

## Relaciones identificadas
`Libros.IdAutor` referencia `Autores.IdAutor`.
`Libros.IdEditorial` referencia `Editoriales.IdEditorial`.
Las referencias fueron deducidas directamente de las consultas y columnas en `FrmLibros.cs`. El ZIP no suministra DDL que permita verificar restricciones físicas de SQL Server.

## Migrado / desarrollado
- CRUD de libros y búsqueda exacta por ISBN.
- CRUD de autores, editoriales y usuarios, ampliado sobre formularios fuente vacíos.
- Prestamos y devolución, con transacción y actualización de inventario, ampliado sobre formulario vacío.
- UI Tkinter CustomTkinter con pestañas.
- MySQL InnoDB/utf8mb4, consultas parametrizadas y config separada.
- Reportes: no implementados (no había definición source).

## Pruebas
- Compilación/sintaxis de módulos Python: realizada automáticamente al empaquetar.
- Integración MySQL, creación de schema en servidor, y pruebas funcionales UI: pendientes; no se afirma éxito.
- Casos que deben ejecutar: connection, schema, CRUD authors/publishers/books/users, ISBN, constraints, loan, return, stock decrement/increment, duplicate return, delete with foreign-key dependency.

## Supuestos técnicos
Los campos Documento, Correo, Telefono de Usuarios; y estructura Prestamos con estado/fechas/ID son modelados para completar módulos nuevos. No son datos comprobados en el origen. El identificador de libro se mantiene ISBN conforme al código fuente.
