"""Validaciones reutilizables para los formularios de AcaBiblioteca."""
import re
from datetime import date


def texto(valor, etiqueta, maximo):
    """Texto obligatorio, sin espacios sobrantes y con longitud máxima."""
    valor = (valor or "").strip()
    if not valor:
        raise ValueError(f"El campo {etiqueta} es obligatorio.")
    if len(valor) > maximo:
        raise ValueError(f"{etiqueta} no puede superar {maximo} caracteres.")
    return valor


def correo(valor):
    valor = texto(valor, "Correo", 180)
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", valor):
        raise ValueError("El correo no tiene un formato válido (ejemplo: nombre@dominio.com).")
    return valor


def documento(valor):
    valor = texto(valor, "Documento", 40)
    if not re.fullmatch(r"\d{5,15}", valor):
        raise ValueError("El documento debe tener solo dígitos (entre 5 y 15).")
    return valor


def telefono(valor):
    valor = texto(valor, "Teléfono", 40)
    if not re.fullmatch(r"\+?\d{7,15}", valor):
        raise ValueError("El teléfono debe tener solo dígitos (entre 7 y 15), con + opcional al inicio.")
    return valor


def isbn(valor):
    valor = texto(valor, "ISBN", 20)
    if not re.fullmatch(r"\d[\d-]{1,18}[\dXx]", valor):
        raise ValueError("El ISBN debe tener entre 3 y 20 caracteres: dígitos y guiones (X al final).")
    return valor


def anio(valor):
    try:
        numero = int(str(valor).strip())
    except ValueError:
        raise ValueError("El año debe ser un número entero.")
    actual = date.today().year
    if not 1000 <= numero <= actual:
        raise ValueError(f"El año debe estar entre 1000 y {actual}.")
    return numero



def fecha_vencimiento(valor):
    """Valida que la fecha de vencimiento no sea anterior a hoy."""
    try:
        fecha = date.fromisoformat(str(valor).strip())
    except ValueError:
        raise ValueError("La fecha de vencimiento debe tener el formato AAAA-MM-DD.")

    if fecha < date.today():
        raise ValueError("La fecha de vencimiento no puede ser anterior a la fecha actual.")

    return fecha

def existencias(valor):
    try:
        numero = int(str(valor).strip())
    except ValueError:
        raise ValueError("Las existencias deben ser un número entero.")
    if numero < 0:
        raise ValueError("Las existencias no pueden ser negativas.")
    return numero
