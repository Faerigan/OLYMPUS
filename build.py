#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HEFESTOS — Script de compilacion
Ecosistema OLYMPUS · CESFAM Cerrillos de Tamaya

Uso:
    python build.py           # compilar HEFESTOS.exe
    python build.py --clean   # limpiar build/ y dist/
    python build.py --check   # verificar dependencias sin compilar

Requisitos:
    pip install pyinstaller pillow cryptography

Resultado:
    dist/HEFESTOS.exe  (~15-20 MB)
"""

import sys
import os
import subprocess
import shutil
import argparse
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).resolve().parent
SPEC_FILE    = PROJECT_ROOT / "HEFESTOS.spec"
ENTRY_POINT  = PROJECT_ROOT / "hefestos.py"
ICO          = PROJECT_ROOT / "Resources" / "HEFESTOS.ico"


class C:
    OK   = "\033[92m"; ERR  = "\033[91m"; WARN = "\033[93m"
    INFO = "\033[96m"; BOLD = "\033[1m";  RST  = "\033[0m"

def ok(m):   print(f"  {C.OK}✔{C.RST}  {m}")
def err(m):  print(f"  {C.ERR}✘{C.RST}  {m}")
def warn(m): print(f"  {C.WARN}⚠{C.RST}  {m}")
def info(m): print(f"  {C.INFO}ℹ{C.RST}  {m}")
def titulo(m):
    print(f"\n{C.BOLD}{m}{C.RST}")
    print("  " + "─" * 50)


def verificar() -> bool:
    titulo("Verificando dependencias")
    todo_ok = True
    for nombre, modulo, pip in [
        ("PyInstaller", "PyInstaller", "pyinstaller"),
        ("Pillow",      "PIL",         "Pillow"),
        ("cryptography","cryptography","cryptography"),
    ]:
        try:
            m = __import__(modulo)
            ver = getattr(m, "__version__", "ok")
            ok(f"{nombre} {ver}")
        except ImportError:
            err(f"{nombre} no instalado — pip install {pip}")
            todo_ok = False

    titulo("Verificando archivos")
    requeridos = [
        "hefestos.py", "hefestos_key_validator.py",
        "install_manifest.json",
        "Resources/HEFESTOS.png", "Resources/HEFESTOS.ico",
    ]
    for rel in requeridos:
        p = PROJECT_ROOT / rel
        if p.exists():
            ok(rel)
        else:
            err(f"{rel}  ← FALTA")
            todo_ok = False

    return todo_ok


def limpiar():
    titulo("Limpiando build/ y dist/")
    for d in ("build", "dist", "__pycache__"):
        p = PROJECT_ROOT / d
        if p.exists():
            shutil.rmtree(p)
            ok(f"Eliminado: {d}/")
    for pc in PROJECT_ROOT.rglob("__pycache__"):
        shutil.rmtree(pc, ignore_errors=True)


def _parchear_hook_distutils():
    """Workaround Python 3.12+ distutils cycle en PyInstaller."""
    if sys.version_info < (3, 12):
        return (None, None)
    try:
        import importlib.util
        spec = importlib.util.find_spec("PyInstaller")
        if not spec:
            return (None, None)
        hook = Path(spec.origin).parent / "hooks" / "pre_safe_import_module" / "hook-distutils.py"
        if not hook.exists():
            return (None, None)
        original = hook.read_text(encoding="utf-8")
        noop = "def pre_safe_import_module(api): pass  # patched by build.py\n"
        try:
            hook.write_text(noop, encoding="utf-8")
        except PermissionError:
            bak = hook.with_suffix(".py.bak")
            if bak.exists():
                bak.unlink()
            hook.rename(bak)
            hook.write_text(noop, encoding="utf-8")
            original = bak.read_text(encoding="utf-8")
        warn(f"Python {sys.version_info.major}.{sys.version_info.minor}: hook-distutils.py desactivado temporalmente")
        return (hook, original)
    except Exception as e:
        warn(f"No se pudo parchear hook-distutils: {e}")
        return (None, None)


def _restaurar_hook(estado):
    hook, original = estado
    if not hook or not original:
        return
    try:
        bak = hook.with_suffix(".py.bak")
        if bak.exists():
            hook.unlink(missing_ok=True)
            bak.rename(hook)
        else:
            hook.write_text(original, encoding="utf-8")
        info("hook-distutils.py restaurado")
    except Exception as e:
        warn(f"No se pudo restaurar hook-distutils: {e}")


def compilar() -> bool:
    titulo("Compilando HEFESTOS.exe")

    cmd = [
        sys.executable, "-m", "PyInstaller",
        str(SPEC_FILE),
        "--noconfirm", "--clean",
    ]

    info(f"pyinstaller {SPEC_FILE.name} --noconfirm --clean")

    hook_estado = _parchear_hook_distutils()
    inicio = datetime.now()
    try:
        proc = subprocess.Popen(
            cmd, cwd=str(PROJECT_ROOT),
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, encoding="utf-8", errors="replace",
        )
        for linea in proc.stdout:
            print(linea, end="", flush=True)
        codigo = proc.wait()
    except FileNotFoundError:
        err("PyInstaller no encontrado — pip install pyinstaller")
        _restaurar_hook(hook_estado)
        return False
    finally:
        _restaurar_hook(hook_estado)

    duracion = (datetime.now() - inicio).seconds
    print()
    if codigo != 0:
        err(f"PyInstaller terminó con error (código {codigo})")
        return False

    exe = PROJECT_ROOT / "dist" / "HEFESTOS.exe"
    if exe.exists():
        size_mb = exe.stat().st_size / (1024 * 1024)
        ok(f"HEFESTOS.exe generado en {duracion}s  ({size_mb:.1f} MB)")
        ok(str(exe))
        return True
    err("El ejecutable no fue creado")
    return False


def main():
    if sys.platform == "win32":
        os.system("")
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="HEFESTOS — Compilador")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--clean", action="store_true")
    args = parser.parse_args()

    print(f"\n{C.BOLD}{'='*52}{C.RST}")
    print(f"{C.BOLD}  HEFESTOS — Compilación · {datetime.now():%d.%m.%Y %H:%M}{C.RST}")
    print(f"{C.BOLD}{'='*52}{C.RST}\n")

    os.chdir(PROJECT_ROOT)

    if args.clean:
        limpiar()
        return

    ok_deps = verificar()
    if args.check:
        if ok_deps:
            ok("Todo listo para compilar — ejecute: python build.py")
        else:
            err("Corrija los errores antes de compilar")
        return

    if not ok_deps:
        err("No se puede compilar — corrija los errores")
        sys.exit(1)

    limpiar()
    exito = compilar()
    print()
    if exito:
        print(f"{C.OK}{C.BOLD}  COMPILACIÓN EXITOSA{C.RST}")
        print("  Distribuya solo: dist/HEFESTOS.exe")
    else:
        print(f"{C.ERR}{C.BOLD}  COMPILACIÓN FALLIDA{C.RST}")
        print("  Ejecute: python build.py --debug para más detalle")
    sys.exit(0 if exito else 1)


if __name__ == "__main__":
    main()
