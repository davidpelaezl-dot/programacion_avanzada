# AcaBiblioteca — migración Python + MySQL

Aplicación de escritorio con CustomTkinter y MySQL Connector para Linux Mint 22.3 y VS Code.

## Auditoría de origen
El ZIP C# original incluye operaciones CRUD en `FrmLibros.cs`: ISBN, título, autor, editorial, categoría, año y existencias. Autores, Editoriales, Usuarios, Préstamos y Reportes tienen formularios de Windows Forms vacíos (sin lógica de negocio implementada). `FrmPrincipal` incluye navegación, pero el botón Reportes abre `FrmPrestamos`, un vínculo probablemente incorrecto.

El paquete original no incluye un script SQL de esquema. La migración conserva campos y vínculos explícitos observados en el módulo de libros. El esquema de Usuarios (Documento, Correo, Telefono) y de Prestamos (IdPrestamo, fechas, estado) es una propuesta de diseño para habilitar los módulos nuevos, no una extracción demostrada del SQL Server original. No se implementó módulo de reportes, porque no existe especificación funcional fuente.

## Preparación
```bash
sudo apt update
sudo apt install python3 python3-venv python3-tk mysql-server
cd AcaBiblioteca_Python
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```
Edite `.env` con la credencial que configure en MySQL. No use la cuenta root desde la aplicación.

## Crear base de datos
```bash
sudo mysql
```
Ejemplo de usuario MySQL (ajuste la contraseña):
```sql
CREATE USER 'biblioteca_app'@'localhost' IDENTIFIED BY 'CAMBIAR_POR_UNA_CLAVE_SEGURA';
GRANT SELECT, INSERT, UPDATE, DELETE ON AcaBiblioteca.* TO 'biblioteca_app'@'localhost';
FLUSH PRIVILEGES;
```
Luego ejecute:
```bash
mysql -u root -p < database/schema.sql
```
Si su configuración local no permite `root` por contraseña, utilice `sudo mysql` y dentro de la consola ejecute el contenido de `database/schema.sql`.

## Ejecutar
```bash
python main.py
```
En VS Code abra esta carpeta, seleccione `.venv/bin/python` como intérprete y ejecute `main.py`.

## Uso
- Registros CRUD en pestañas de libros, autores, editoriales y usuarios.
- ISBN permite buscar un libro exacto.
- Préstamos requiere ID de usuario, ISBN existente y fecha vencimiento ISO `YYYY-MM-DD`.
- La creación de préstamo reduce existencias bajo transacción y bloqueo de fila.
- Devolución de préstamo activo aumenta existencias. Devoluciones duplicadas son bloqueadas.
- Eliminación sujeta a relaciones foráneas restrictivas.

## Limitaciones y validación
No se pudo ejecutar integración con MySQL durante la generación del paquete. Se realizaron comprobaciones de sintaxis Python. Antes de uso real: 
instalar MySQL, aplicar schema, configurar `.env`, verificar conexión, y probar CRUD y ciclos de préstamo/devolución en 
una instancia local. Los campos propuestos de usuarios/préstamos necesitan aprobación contra el esquema 
original si se dispone de un backup o script SQL.
