"""
hefestos.py — Instalador ECLIPSE-T v3.0  ·  HEFESTOS v2.0
Ecosistema OLYMPUS · CESFAM Cerrillos de Tamaya
© 2026 Dr. Nicolás Vargas · CESFAM Cerrillos de Tamaya · Todos los derechos reservados.
"""

import hashlib
import json
import math
import os
import platform
import queue
import random
import shutil
import ssl
import subprocess
import sys
import tempfile
import threading
import urllib.request
import zipfile
from pathlib import Path

# Python 3.14: CA con Basic Constraints no crítico rompe verificación en exe compilado
ssl._create_default_https_context = ssl._create_unverified_context
# DPI awareness — Windows HiDPI (debe ir antes de crear Tk)
try:
    from ctypes import windll
    windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass

import tkinter as tk
from tkinter import ttk, filedialog, messagebox

# ── Fernet (cifrado) ─────────────────────────────────────────────────────────
try:
    from cryptography.fernet import Fernet
    _CRYPTO_OK = True
except ImportError:
    _CRYPTO_OK = False

# ── Rutas ────────────────────────────────────────────────────────────────────
_BASE_DIR = (Path(sys._MEIPASS) if getattr(sys, "frozen", False)
             else Path(__file__).parent)
sys.path.insert(0, str(_BASE_DIR))

def resource_path(rel: str) -> str:
    """Resuelve rutas de recursos compatible con PyInstaller (_MEIPASS)."""
    return str(_BASE_DIR / rel)

OLYMPUS_RAW   = "https://raw.githubusercontent.com/Faerigan/OLYMPUS/main"
_ECLIPSE_REPO = "Faerigan/eclipse-t"   # repo privado — releases con los EXEs
_HEFESTOS_VERSION = "2.2"


def _cargar_github_token() -> str:
    """Token de escritura para OLYMPUS (SCRAP_METAL.csv)."""
    for tokens_path in (
        Path("D:/ECLIPSE/.tokens"),
        Path("E:/ECLIPSE/.tokens"),
        _BASE_DIR.parent / "ECLIPSE" / ".tokens",
    ):
        try:
            if tokens_path.exists():
                import json as _json
                tok = _json.loads(tokens_path.read_text("utf-8")).get("olympus", "")
                if tok:
                    return tok
        except Exception:
            pass
    try:
        import importlib, sys as _sys
        _sys.path.insert(0, str(_BASE_DIR))
        mod = importlib.import_module("hefestos_key_validator")
        return getattr(mod, "_GITHUB_TOKEN", "") or ""
    except Exception:
        return ""


def _cargar_eclipse_token() -> str:
    """Token de lectura para Faerigan/eclipse-t (repo privado, releases con EXEs)."""
    for tokens_path in (
        Path("D:/ECLIPSE/.tokens"),
        Path("E:/ECLIPSE/.tokens"),
        _BASE_DIR.parent / "ECLIPSE" / ".tokens",
    ):
        try:
            if tokens_path.exists():
                import json as _json
                data = _json.loads(tokens_path.read_text("utf-8"))
                tok = data.get("eclipse_t", "") or data.get("olympus", "")
                if tok:
                    return tok
        except Exception:
            pass
    try:
        import importlib, sys as _sys
        _sys.path.insert(0, str(_BASE_DIR))
        mod = importlib.import_module("hefestos_key_validator")
        return getattr(mod, "_GITHUB_TOKEN", "") or ""
    except Exception:
        return ""

# ── Paleta crema / arquitectura griega ───────────────────────────────────────
BG      = "#FAF6EE"   # fondo crema cálido
BG2     = "#F0E8D8"   # crema ligeramente más oscuro
DARK    = "#D4C8B0"   # separadores / bordes
GOLD    = "#B8860B"   # dark goldenrod — legible sobre crema
ACCENT  = "#C8921A"   # ámbar cálido para botones principales
COLUMN  = "#D4C4A0"   # piedra cálida para pilares
COL_SHD = "#B8A888"   # sombra / borde de pilar
COL_GRV = "#C4B490"   # acanalado del pilar
TEXT    = "#3A2E1E"   # marrón oscuro (texto principal)
DIM     = "#8B7355"   # marrón medio (texto secundario)
GREEN   = "#2E7D32"   # verde oscuro (éxito)
RED     = "#C62828"   # rojo oscuro (error)
GRAY    = "#9E8B6E"   # gris cálido
ANIM_BG = "#2C2416"   # fondo del canvas de animación (oscuro)
ANVIL   = "#607D8B"
METAL   = "#90A4AE"
MANGO   = "#5D4037"

# ── Defaults clave maestra ───────────────────────────────────────────────────
_DEFAULTS_MAESTRA = {
    "nombre_centro":      "CESFAM Cerrillos de Tamaya",
    "codigo_centro":      "",
    "comuna":             "Ovalle",
    "servicio_salud":     "Servicio de Salud Coquimbo",
    "conector_lab":       "iris",
    "iris_url":           "http://207.248.201.73:8080/irisconsultorio/",
    "iris_usuario":       "",
    "iris_password":      "",
    "redclinica_url":     "",
    "redclinica_usuario": "",
    "redclinica_password":"",
    "nombre_profesional": "Dr. Nicolás Vargas",
    "profesion":          "Médico Familiar",
    "registro":           "",
    "logo_principal":     "",
    "logo_secundario":    "",
}


# ── Helpers ──────────────────────────────────────────────────────────────────

def _generar_id(nombre: str) -> str:
    return hashlib.sha256(nombre.encode()).hexdigest()[:8]


def _cargar_logo_tk(path: "str | Path | None", size: int = 80) -> "tk.PhotoImage | None":
    if not path:
        return None
    try:
        from PIL import Image, ImageTk
        img = Image.open(str(path))
        img = img.resize((size, size), Image.LANCZOS)
        return ImageTk.PhotoImage(img)
    except Exception:
        pass
    try:
        return tk.PhotoImage(file=str(path))
    except Exception:
        return None


# ── Pilares dóricos ──────────────────────────────────────────────────────────

def _dibujar_columnas(canvas: tk.Canvas, ancho: int = 44, alto: int = 760):
    """Pilar dórico decorativo que ocupa todo el alto del canvas."""
    canvas.delete("all")
    cx = ancho // 2

    # Estilobato — 3 escalones desde la base
    for i, extra in enumerate([0, 6, 13]):
        w  = 28 + extra
        x1 = cx - w // 2
        y1 = alto - 28 + i * 9
        canvas.create_rectangle(x1, y1, x1 + w, y1 + 9,
                                 fill=COLUMN, outline=COL_SHD, width=1)

    # Fuste con acanalado
    sx1, sx2 = cx - 12, cx + 12
    sy1, sy2 = 68, alto - 28
    canvas.create_rectangle(sx1, sy1, sx2, sy2,
                             fill=COLUMN, outline=COL_SHD, width=1)
    # 5 líneas de acanalado verticales
    step = (sx2 - sx1) // 6
    for i in range(1, 6):
        fx = sx1 + i * step
        canvas.create_line(fx, sy1 + 6, fx, sy2 - 6, fill=COL_GRV, width=1)

    # Équino — trapecio que se abre hacia el ábaco
    canvas.create_polygon(
        sx1, sy1, sx2, sy1,
        cx + 18, sy1 - 18, cx - 18, sy1 - 18,
        fill=COLUMN, outline=COL_SHD, width=1
    )

    # Ábaco — losa plana superior
    canvas.create_rectangle(0, sy1 - 32, ancho, sy1 - 18,
                             fill=COLUMN, outline=COL_SHD, width=1)

    # Línea dorada de entablamento
    canvas.create_line(0, sy1 - 32, ancho, sy1 - 32, fill=GOLD, width=2)


# ── Logo estático HEFESTOS (canvas) ─────────────────────────────────────────

def dibujar_logo(canvas: tk.Canvas, cx: int, cy: int, s: float = 1.0):
    """Yunque + martillo + rayos solares dorados sobre fondo oscuro."""
    for ang in range(0, 360, 30):
        rad   = math.radians(ang)
        largo = int(28 * s) if abs(math.sin(rad)) > 0.5 else int(18 * s)
        r_in  = int(38 * s)
        x1 = cx + int(math.cos(rad) * r_in)
        y1 = cy + int(math.sin(rad) * r_in)
        x2 = cx + int(math.cos(rad) * (r_in + largo))
        y2 = cy + int(math.sin(rad) * (r_in + largo))
        canvas.create_line(x1, y1, x2, y2, fill=GOLD, width=max(1, int(2 * s)))

    aw, ah = int(72 * s), int(24 * s)
    ax, ay = cx - aw // 2, cy + int(16 * s)
    canvas.create_polygon(
        ax + int(6*s), ay, ax + aw - int(6*s), ay,
        ax + aw, ay + ah, ax, ay + ah,
        fill=ANVIL, outline=METAL, width=1,
    )
    nw = int(28 * s)
    nx = cx - nw // 2
    canvas.create_rectangle(nx, cy + int(6*s), nx + nw, ay, fill=ANVIL, outline=METAL)
    hw, hh = int(82 * s), int(12 * s)
    hx = cx - hw // 2
    canvas.create_rectangle(hx, cy - int(6*s), hx + hw, cy + int(6*s),
                             fill=METAL, outline="#E8E8E8", width=1)
    canvas.create_rectangle(
        cx - int(5*s), cy - int(62*s), cx + int(5*s), cy - int(10*s),
        fill=ANIM_BG, outline=GRAY,
    )
    mhw, mhh = int(36*s), int(18*s)
    mhx = cx - int(10*s)
    mhy = cy - int(62*s) - mhh
    canvas.create_rectangle(mhx, mhy, mhx + mhw, mhy + mhh,
                             fill=METAL, outline="#E8E8E8", width=1)


# ── AnimacionForja (GIF) ─────────────────────────────────────────────────────

class AnimacionForja:
    """
    Reproduce Resources/hefestos_forge.gif en un tk.Canvas.
    Fallo silencioso si el GIF no existe — nunca crashea.
    """

    def __init__(self, canvas: tk.Canvas, ancho: int = 300, alto: int = 300):
        self._canvas  = canvas
        self._ancho   = ancho
        self._alto    = alto
        self._frames: list = []
        self._delays: list = []
        self._idx    = 0
        self._job    = None
        self._img_id = None
        self._cargado = False
        self._cargar()

    def _cargar(self):
        ruta = resource_path(os.path.join("Resources", "hefestos_forge.gif"))
        if not os.path.exists(ruta):
            return
        try:
            from PIL import Image, ImageTk
            gif = Image.open(ruta)
            for i in range(gif.n_frames):
                gif.seek(i)
                frame_img = gif.convert("RGBA")
                if frame_img.size != (self._ancho, self._alto):
                    frame_img = frame_img.resize((self._ancho, self._alto), Image.LANCZOS)
                photo = ImageTk.PhotoImage(frame_img)
                self._frames.append(photo)
                self._delays.append(gif.info.get("duration", 150))
            self._cargado = True
        except Exception:
            pass

    def iniciar(self):
        if not self._cargado or not self._frames:
            return
        self._idx = 0
        self._reproducir()

    def _reproducir(self):
        if not self._frames:
            return
        frame = self._frames[self._idx]
        delay = self._delays[self._idx]
        if self._img_id is None:
            self._img_id = self._canvas.create_image(
                self._ancho // 2, self._alto // 2, image=frame, anchor="center")
        else:
            self._canvas.itemconfig(self._img_id, image=frame)
        self._idx = (self._idx + 1) % len(self._frames)
        self._job = self._canvas.after(delay, self._reproducir)

    def detener(self):
        if self._job is not None:
            self._canvas.after_cancel(self._job)
            self._job = None


# ── HefestosAnimacion ────────────────────────────────────────────────────────

class HefestosAnimacion(tk.Canvas):
    """
    Animación de martillo golpeando yunque con chispas doradas.
    Canvas oscuro como "ventana de visualización" sobre el fondo crema.
    """
    _BAJADA  = 8
    _IMPACTO = 4
    _SUBIDA  = 10
    _PAUSA   = 6
    _TOTAL   = 28
    _ANG_ALTO = -40
    _ANG_BAJO =   5

    def __init__(self, parent, **kw):
        super().__init__(parent, width=160, height=160,
                         bg=ANIM_BG, highlightthickness=2,
                         highlightbackground=GOLD, **kw)
        self._frame    = 0
        self._running  = False
        self._after_id = None
        self._chispas: list = []

    def iniciar(self):
        if self._running:
            return
        self._running  = True
        self._frame    = 0
        self._chispas  = []
        self._tick()

    def detener(self):
        self._running = False
        if self._after_id:
            self.after_cancel(self._after_id)
            self._after_id = None
        self.delete("all")

    def _tick(self):
        if not self._running:
            return
        self._renderizar()
        self._frame    = (self._frame + 1) % self._TOTAL
        self._after_id = self.after(42, self._tick)

    def _angulo(self) -> float:
        f = self._frame
        rango = self._ANG_BAJO - self._ANG_ALTO
        if f < self._BAJADA:
            t = f / self._BAJADA
            return self._ANG_ALTO + (t * t) * rango
        if f < self._BAJADA + self._IMPACTO:
            return self._ANG_BAJO
        if f < self._BAJADA + self._IMPACTO + self._SUBIDA:
            fi = f - self._BAJADA - self._IMPACTO
            t  = fi / self._SUBIDA
            return self._ANG_BAJO - (1 - (1-t)**2) * rango
        return self._ANG_ALTO

    def _renderizar(self):
        self.delete("all")
        cx, cy_yuq = 80, 115

        self._yunque(cx, cy_yuq)

        impact_x, impact_y = cx, cy_yuq - 10

        if self._frame == self._BAJADA:
            for _ in range(random.randint(6, 8)):
                ang  = math.radians(random.uniform(20, 160))
                lng  = random.uniform(8, 18)
                life = random.randint(3, 4)
                self._chispas.append([impact_x, impact_y, ang, lng, life])

        vivas = []
        for x, y, ang, lng, life in self._chispas:
            if life > 0:
                x2 = x + math.cos(ang) * lng
                y2 = y - math.sin(ang) * lng
                self.create_line(x, y, x2, y2, fill=GOLD, width=2, capstyle="round")
                vivas.append([x, y, ang, lng, life - 1])
        self._chispas = vivas

        self._martillo(cx, ang_deg=self._angulo(), impact_y=impact_y)

    def _yunque(self, cx: int, cy: int):
        self.create_polygon(
            cx-26, cy,   cx+26, cy,
            cx+32, cy+22, cx-32, cy+22,
            fill=ANVIL, outline=METAL, width=1,
        )
        self.create_rectangle(cx-12, cy-14, cx+12, cy, fill=ANVIL, outline=METAL)
        self.create_rectangle(cx-36, cy-24, cx+36, cy-14,
                              fill=METAL, outline="#E8E8E8", width=1)

    def _martillo(self, cx: int, ang_deg: float, impact_y: int):
        pivot_x, pivot_y = cx, 30
        mango = 48
        ang   = math.radians(ang_deg)
        tip_x = pivot_x + math.sin(ang) * mango
        tip_y = pivot_y + math.cos(ang) * mango
        self.create_line(pivot_x, pivot_y, tip_x, tip_y,
                         fill=MANGO, width=9, capstyle="round")
        perp = ang + math.pi / 2
        half, depth = 16, 12
        vx = [
            tip_x + math.cos(perp) * half,
            tip_x - math.cos(perp) * half,
            tip_x - math.cos(perp) * half + math.sin(ang) * depth,
            tip_x + math.cos(perp) * half + math.sin(ang) * depth,
        ]
        vy = [
            tip_y + math.sin(perp) * half,
            tip_y - math.sin(perp) * half,
            tip_y - math.sin(perp) * half + math.cos(ang) * depth,
            tip_y + math.sin(perp) * half + math.cos(ang) * depth,
        ]
        self.create_polygon(*sum(zip(vx, vy), ()), fill=METAL, outline="#E8E8E8", width=1)


# ── Texto de licencia embebido ───────────────────────────────────────────────

_TEXTO_LICENCIA = """\
================================================================
  CONTRATO DE LICENCIA DE USO DE SOFTWARE
  ECLIPSE-T · Ecosistema OLYMPUS
  © 2026 Dr. Nicolás Vargas · CESFAM Cerrillos de Tamaya
================================================================

IMPORTANTE: Lea atentamente este contrato antes de activar el
software. Al hacer clic en "Acepto", usted declara haber leído,
comprendido y aceptado todos los términos aquí establecidos.
Este acto constituye un acuerdo electrónico válido conforme a
la Ley 19.799 sobre Documentos Electrónicos.

----------------------------------------------------------------
ARTÍCULO 1 — NATURALEZA DEL SOFTWARE
----------------------------------------------------------------

ECLIPSE-T es una herramienta de redacción y transcripción
asistida de uso clínico. El software genera borradores de texto
en lenguaje natural a partir de la información ingresada por el
profesional, los cuales pueden ser revisados, modificados y
volcados a cualquier sistema de registro que el profesional
determine.

ECLIPSE-T NO constituye un sistema de ficha clínica, NO crea
documentos con valor legal autónomo como documento médico, y NO
emite diagnósticos ni recomendaciones terapéuticas. El software
es equivalente funcional a un procesador de texto especializado.

La responsabilidad por la validación del contenido clínico
generado, su edición final y su destino recae íntegramente en
el profesional de salud.

----------------------------------------------------------------
ARTÍCULO 2 — LICENCIA DE USO PERSONAL
----------------------------------------------------------------

El pago de la clave de activación otorga al usuario una licencia
personal, intransferible y de carácter vitalicio para instalar
y usar ECLIPSE-T en un (1) equipo de su propiedad o bajo su
gestión directa, en el ejercicio de su práctica clínica.

Queda expresamente prohibido:

  a) Redistribuir, sublicenciar, vender o ceder la licencia o
     la clave de activación a terceros.

  b) Descompilar, desensamblar, hacer ingeniería inversa o
     modificar el software de cualquier forma.

  c) Usar el software en más de un equipo simultáneamente o en
     equipos distintos al registrado con la clave de activación,
     sin adquirir una licencia adicional.

La licencia incluye actualizaciones de mantenimiento por dos (2)
años desde la fecha de activación. Las actualizaciones de versión
mayor podrán requerir una nueva licencia de activación.

----------------------------------------------------------------
ARTÍCULO 3 — PROPIEDAD DE LOS DATOS
----------------------------------------------------------------

Todos los datos ingresados al sistema son de titularidad
exclusiva del usuario y/o de sus pacientes. El desarrollador
no accede, almacena, transmite ni procesa datos clínicos en
ningún momento.

ECLIPSE-T opera completamente fuera de línea (offline) una vez
instalado. El usuario es responsable del respaldo, custodia y
eventual eliminación de los datos almacenados en su equipo,
conforme a la normativa aplicable (Ley 21.096, Ley 20.584).

----------------------------------------------------------------
ARTÍCULO 4 — CREDENCIALES DE ACCESO A SISTEMAS EXTERNOS
----------------------------------------------------------------

El software puede automatizar, en nombre del usuario y bajo su
instrucción explícita, el acceso a plataformas externas de
laboratorio u otros sistemas clínicos (ej. IRIS, RedClínica u
otros) mediante las credenciales provistas por el propio usuario.

El usuario declara:

  a) Ser titular autorizado de las credenciales que ingresa
     al sistema.

  b) Que el acceso automatizado a dichos sistemas mediante
     ECLIPSE-T tiene idéntico alcance legal que si realizara
     el acceso manualmente.

  c) Asumir íntegra responsabilidad por cualquier acción
     ejecutada en dichos sistemas mediante sus credenciales,
     independientemente del medio técnico utilizado.

El desarrollador no almacena, transmite ni accede en ningún
momento a las credenciales del usuario. ECLIPSE-T actúa
exclusivamente como un conjunto de instrucciones automatizadas
que operan en el equipo local del usuario, bajo su control y
responsabilidad directa.

----------------------------------------------------------------
ARTÍCULO 5 — EXCLUSIÓN DE GARANTÍAS Y LIMITACIÓN DE
             RESPONSABILIDAD
----------------------------------------------------------------

El software se entrega en su estado actual ("tal como está",
as-is), sin garantías expresas ni implícitas de ningún tipo.
El desarrollador no garantiza que el software esté libre de
errores o interrupciones, ni que sea apto para un uso clínico
específico.

En ningún caso la responsabilidad total del desarrollador
excederá el monto pagado por la licencia de activación.
El desarrollador no será responsable por daños directos,
indirectos, incidentales, especiales o derivados del uso o
la imposibilidad de uso del software.

El uso del software no exime al profesional de salud de ninguna
obligación legal, ética o deontológica propia de su ejercicio
profesional. Las decisiones clínicas son responsabilidad
exclusiva del profesional.

----------------------------------------------------------------
ARTÍCULO 6 — TERMINACIÓN
----------------------------------------------------------------

Esta licencia se revoca automáticamente, sin necesidad de
notificación previa, si el usuario redistribuye la clave de
activación, intenta descompilar o modificar el software, o lo
usa con fines distintos al ejercicio clínico propio o en más
equipos de los autorizados.

Ante la terminación, el usuario deberá cesar todo uso del
software y eliminar todas las copias instaladas.

----------------------------------------------------------------
ARTÍCULO 7 — MARCO LEGAL APLICABLE
----------------------------------------------------------------

Este contrato se rige por las leyes de la República de Chile.

Marco normativo aplicable:
  · Ley 17.336 — Propiedad Intelectual
  · Ley 19.799 — Documentos Electrónicos y Firma Electrónica
  · Ley 21.096 — Protección de Datos Personales
  · Ley 20.584 — Derechos y Deberes del Paciente

La aceptación electrónica mediante el botón "Acepto" constituye
un acuerdo válido conforme a la Ley 19.799. Se deja constancia
de la fecha y equipo de activación en los registros del sistema.

Para consultas o soporte:  n.vargas.med@gmail.com

================================================================
  Versión de licencia: 1.0 · ECLIPSE-T v3.0
  © 2026 Dr. Nicolás Vargas · CESFAM Cerrillos de Tamaya
================================================================
"""


# ── Diálogo Licencia ─────────────────────────────────────────────────────────

class _DialogoLicencia(tk.Toplevel):
    """
    Ventana modal con el texto completo de la licencia.
    El botón "Acepto" solo se habilita cuando el usuario marca el checkbox.
    on_acepto y on_rechazo son callbacks sin argumentos.
    """

    def __init__(self, parent, on_acepto, on_rechazo):
        super().__init__(parent)
        self._on_acepto   = on_acepto
        self._on_rechazo  = on_rechazo

        self.title("Términos y Condiciones de Uso — ECLIPSE-T")
        self.resizable(True, True)
        self.configure(bg=BG)
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self._rechazar)

        self._construir()
        self.geometry("660x560")
        self.update_idletasks()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        w, h = self.winfo_width(), self.winfo_height()
        self.geometry(f"+{(sw - w) // 2}+{(sh - h) // 2}")
        self.lift()
        self.focus_force()

    def _construir(self):
        # Encabezado
        hdr = tk.Frame(self, bg=DARK, pady=6)
        hdr.pack(fill="x")
        tk.Label(hdr,
                 text="Contrato de Licencia de Uso de Software",
                 font=("Georgia", 11, "bold"), fg=TEXT, bg=DARK
                 ).pack()
        tk.Label(hdr,
                 text="Lea atentamente antes de activar ECLIPSE-T",
                 font=("Georgia", 9, "italic"), fg=DIM, bg=DARK
                 ).pack()

        # Área de texto con scroll
        frame_txt = tk.Frame(self, bg=BG, padx=12, pady=8)
        frame_txt.pack(fill="both", expand=True)

        scrollbar = tk.Scrollbar(frame_txt)
        scrollbar.pack(side="right", fill="y")

        txt = tk.Text(frame_txt,
                      wrap="word",
                      font=("Consolas", 9),
                      fg=TEXT, bg="#FFFEF8",
                      relief="flat", bd=1,
                      yscrollcommand=scrollbar.set,
                      state="normal",
                      cursor="arrow")
        txt.insert("1.0", _TEXTO_LICENCIA)
        txt.configure(state="disabled")
        txt.pack(fill="both", expand=True)
        scrollbar.config(command=txt.yview)

        # Separador
        tk.Frame(self, bg=DARK, height=1).pack(fill="x", padx=16)

        # Pie: checkbox + botones
        pie = tk.Frame(self, bg=BG, padx=16, pady=10)
        pie.pack(fill="x")

        self._var_acepto = tk.BooleanVar(value=False)
        chk = tk.Checkbutton(pie,
                             text="He leído y acepto los términos y condiciones",
                             variable=self._var_acepto,
                             font=("Georgia", 10), fg=TEXT, bg=BG,
                             activebackground=BG,
                             command=self._toggle_boton)
        chk.pack(anchor="w", pady=(0, 8))

        btns = tk.Frame(pie, bg=BG)
        btns.pack(fill="x")

        self._btn_acepto = tk.Button(btns,
                                     text="  Acepto  ✓  ",
                                     font=("Georgia", 11, "bold"),
                                     bg=GREEN, fg="white", relief="flat",
                                     padx=16, pady=6,
                                     state="disabled",
                                     activebackground="#1B5E20",
                                     command=self._aceptar)
        self._btn_acepto.pack(side="left", padx=(0, 12))

        tk.Button(btns,
                  text="No acepto — Salir",
                  font=("Georgia", 10), bg=DARK, fg=TEXT,
                  relief="flat", padx=12, pady=6,
                  command=self._rechazar
                  ).pack(side="left")

    def _toggle_boton(self):
        estado = "normal" if self._var_acepto.get() else "disabled"
        self._btn_acepto.configure(state=estado)

    def _aceptar(self):
        self.grab_release()
        self.destroy()
        self._on_acepto()

    def _rechazar(self):
        self.grab_release()
        self.destroy()
        self._on_rechazo()


# ── Aplicación principal ─────────────────────────────────────────────────────

class HefestosApp:

    _ECLIPSE_CANDIDATOS = [
        Path("E:/ECLIPSE"),
        Path("D:/ECLIPSE"),
        Path("C:/ECLIPSE"),
    ]

    @staticmethod
    def _candidatos_desktop() -> list:
        """Devuelve subcarpetas del Desktop del usuario actual como candidatos."""
        candidatos = []
        try:
            desktop = Path.home() / "Desktop"
            if desktop.exists():
                for sub in sorted(desktop.iterdir()):
                    if sub.is_dir():
                        candidatos.append(sub)
        except Exception:
            pass
        return candidatos

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("HEFESTOS v2.0 — Instalador Ecosistema OLYMPUS")
        self.root.configure(bg=BG)
        self.root.resizable(False, False)
        self.root.withdraw()  # ocultar hasta centrar
        self.root.update_idletasks()
        w, h = 700, 760
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        x = max(0, (sw - w) // 2)
        y = max(0, (sh - h) // 2)
        self.root.geometry(f"{w}x{h}+{x}+{y}")
        self.root.deiconify()  # mostrar ya centrada
        self.root.protocol("WM_DELETE_WINDOW", self._cerrar)

        self._cola:                 queue.Queue = queue.Queue()
        self._eclipse_dir:          Path | None = None
        self._labels_pasos:         list        = []
        self._es_maestra:           bool        = False
        self._modo_agregar_centro:  bool        = False
        self._forzar_nuevo_install: bool        = False
        self._cfg:                  dict        = {}

        self._var_dir   = tk.StringVar()
        self._var_clave = tk.StringVar()

        self._manifest      = self._cargar_manifest()
        self._total_pasos   = sum(len(g["pasos"]) for g in self._manifest["grupos"])
        self._pasos_completados = 0

        self._construir_ui()
        self._detectar_eclipse()
        self.root.after(800, self._chequeo_startup)

    # ── Layout con pilares ───────────────────────────────────────────────────

    def _construir_ui(self):
        outer = tk.Frame(self.root, bg=BG)
        outer.pack(fill="both", expand=True)

        # Pilares laterales
        self._cv_izq = tk.Canvas(outer, width=44, bg=BG, highlightthickness=0)
        self._cv_izq.pack(side="left", fill="y")

        self._cv_der = tk.Canvas(outer, width=44, bg=BG, highlightthickness=0)
        self._cv_der.pack(side="right", fill="y")

        # Área de contenido central
        self._center = tk.Frame(outer, bg=BG)
        self._center.pack(side="left", fill="both", expand=True)

        # Dibujar pilares cuando la ventana esté lista
        self.root.after(150, self._actualizar_pilares)

        # Pantallas
        self._f_inicio      = tk.Frame(self._center, bg=BG)
        self._f_reconfig    = tk.Frame(self._center, bg=BG)
        self._f_config      = tk.Frame(self._center, bg=BG)
        self._f_instalacion = tk.Frame(self._center, bg=BG)
        self._f_final       = tk.Frame(self._center, bg=BG)

        self._construir_inicio()
        self._construir_reconfig()
        self._construir_config()
        self._construir_instalacion()
        self._construir_final()
        self._mostrar(self._f_inicio)

    def _actualizar_pilares(self):
        h = self.root.winfo_height() or 760
        _dibujar_columnas(self._cv_izq, 44, h)
        _dibujar_columnas(self._cv_der, 44, h)

    def _mostrar(self, frame: tk.Frame):
        for f in (self._f_inicio, self._f_reconfig, self._f_config,
                  self._f_instalacion, self._f_final):
            f.pack_forget()
        frame.pack(fill="both", expand=True)

    # ── Python del sistema ───────────────────────────────────────────────────

    @staticmethod
    def _get_python() -> str:
        if getattr(sys, "frozen", False):
            for nombre in ("python3", "python"):
                p = shutil.which(nombre)
                if p:
                    return p
            return "python"
        return sys.executable

    # ── Manifiesto ───────────────────────────────────────────────────────────

    def _cargar_manifest(self) -> dict:
        path = _BASE_DIR / "install_manifest.json"
        with open(path, encoding="utf-8") as f:
            return json.load(f)

    # ── Pantalla 1: Inicio ───────────────────────────────────────────────────

    def _construir_inicio(self):
        fr = self._f_inicio

        tk.Frame(fr, bg=BG, height=20).pack()

        # Logo en canvas oscuro enmarcado
        cv_logo = tk.Canvas(fr, width=180, height=180, bg=ANIM_BG,
                             highlightthickness=2, highlightbackground=GOLD)
        cv_logo.pack(pady=(0, 4))
        try:
            from PIL import Image, ImageTk
            _img = Image.open(resource_path(os.path.join("Resources", "HEFESTOS.png")))
            _img = _img.resize((176, 176), Image.LANCZOS)
            self._logo_inicio = ImageTk.PhotoImage(_img)   # retener referencia
            cv_logo.create_image(90, 90, image=self._logo_inicio, anchor="center")
        except Exception:
            dibujar_logo(cv_logo, 90, 90, s=0.9)

        tk.Label(fr, text="HEFESTOS", font=("Georgia", 24, "bold"),
                 fg=GOLD, bg=BG).pack(pady=(8, 0))
        tk.Label(fr, text="Instalador Ecosistema OLYMPUS  ·  v2.0",
                 font=("Georgia", 10), fg=DIM, bg=BG).pack()
        tk.Label(fr, text="CESFAM Cerrillos de Tamaya",
                 font=("Georgia", 9), fg=GRAY, bg=BG).pack(pady=(2, 10))

        tk.Frame(fr, height=2, bg=GOLD).pack(fill="x", padx=60, pady=(0, 14))

        # Directorio ECLIPSE
        tk.Label(fr, text="Directorio ECLIPSE-T:", font=("Georgia", 10, "bold"),
                 fg=TEXT, bg=BG).pack(anchor="w", padx=60)
        row_dir = tk.Frame(fr, bg=BG)
        row_dir.pack(fill="x", padx=60, pady=(4, 6))
        tk.Entry(row_dir, textvariable=self._var_dir, bg=BG2, fg=TEXT,
                 insertbackground=GOLD, relief="flat",
                 font=("Courier", 10), width=34).pack(side="left", ipady=5, padx=(0, 6))
        tk.Button(row_dir, text="…", bg=DARK, fg=TEXT, relief="flat",
                  command=self._seleccionar_dir).pack(side="left")
        self._var_dir.trace_add("write", lambda *_: self._actualizar_modo_inicio())

        # ── Frame A: primera instalación (clave nueva requerida) ─────────────
        self._f_nuevo = tk.Frame(fr, bg=BG)

        tk.Label(self._f_nuevo, text="Código de instalación:",
                 font=("Georgia", 10, "bold"), fg=TEXT, bg=BG).pack(anchor="w", padx=60)
        entry = tk.Entry(self._f_nuevo, textvariable=self._var_clave, show="•",
                         bg=BG2, fg=TEXT, insertbackground=GOLD,
                         relief="flat", font=("Courier", 13), width=26)
        entry.pack(ipady=6, pady=(4, 4))
        entry.bind("<Return>", lambda _: self._comenzar())

        self._lbl_msg = tk.Label(self._f_nuevo, text="", font=("Georgia", 9),
                                  fg=RED, bg=BG, wraplength=500, justify="center")
        self._lbl_msg.pack(pady=(2, 0))

        tk.Button(self._f_nuevo, text="  INSTALAR  ▶  ",
                  font=("Georgia", 13, "bold"),
                  bg=ACCENT, fg="white", relief="flat", padx=18, pady=9,
                  activebackground="#A87018",
                  command=self._comenzar).pack(pady=(14, 4))

        tk.Label(self._f_nuevo, text="Tiempo estimado con buena conexión: ~20 min",
                 font=("Georgia", 8), fg=GRAY, bg=BG).pack()

        tk.Frame(self._f_nuevo, height=1, bg=DARK).pack(fill="x", padx=80, pady=(14, 8))

        tk.Button(self._f_nuevo, text="⚙  Reparar o desinstalar instalación existente",
                  font=("Georgia", 9), fg=DIM, bg=BG,
                  relief="flat", cursor="hand2", padx=4, pady=2,
                  activeforeground=GOLD, activebackground=BG,
                  command=self._cmd_mantenimiento).pack()

        # ── Frame B: instalación ya configurada ──────────────────────────────
        self._f_inicio_ok = tk.Frame(fr, bg=BG)

        tk.Frame(self._f_inicio_ok, height=1, bg=GOLD).pack(fill="x", padx=60, pady=(4, 10))

        tk.Label(self._f_inicio_ok,
                 text="✓  ECLIPSE-T configurado",
                 font=("Georgia", 11, "bold"), fg=GREEN, bg=BG).pack(pady=(0, 2))

        self._lbl_centro_nombre_ok = tk.Label(
            self._f_inicio_ok, text="",
            font=("Georgia", 10, "italic"), fg=DIM, bg=BG
        )
        self._lbl_centro_nombre_ok.pack(pady=(0, 4))

        self._lbl_version_ok = tk.Label(
            self._f_inicio_ok, text=f"HEFESTOS v{_HEFESTOS_VERSION}",
            font=("Georgia", 8), fg=GRAY, bg=BG
        )
        self._lbl_version_ok.pack(pady=(0, 10))

        btns_ok = tk.Frame(self._f_inicio_ok, bg=BG)
        btns_ok.pack(pady=(0, 10))

        tk.Button(btns_ok, text="  Reparar  🔧  ",
                  font=("Georgia", 10, "bold"),
                  bg=ACCENT, fg="white", relief="flat", padx=12, pady=7,
                  activebackground="#A87018",
                  command=self._cmd_reparar_directo).pack(side="left", padx=(0, 8))

        tk.Button(btns_ok, text="  Desinstalar  ",
                  font=("Georgia", 10),
                  bg="#C62828", fg="white", relief="flat", padx=12, pady=7,
                  activebackground="#9B1B1B",
                  command=self._cmd_desinstalar).pack(side="left", padx=(0, 8))

        tk.Button(btns_ok, text="  Cambiar de centro  ⇄  ",
                  font=("Georgia", 10, "bold"),
                  bg=GOLD, fg="white", relief="flat", padx=12, pady=7,
                  activebackground="#8B6500",
                  command=self._cmd_cambiar_centro).pack(side="left")

    def _actualizar_modo_inicio(self):
        """Muestra _f_nuevo (clave requerida) o _f_inicio_ok (ya configurado) según estado."""
        if not hasattr(self, "_f_nuevo") or not hasattr(self, "_f_inicio_ok"):
            return

        if self._forzar_nuevo_install:
            self._f_inicio_ok.pack_forget()
            self._f_nuevo.pack(fill="x")
            return

        eclipse_dir_str = self._var_dir.get().strip()
        if eclipse_dir_str:
            centros_dat = Path(eclipse_dir_str) / "resources" / "centros.dat"
            if centros_dat.exists():
                # Leer nombre del centro activo para mostrarlo
                try:
                    self._eclipse_dir = Path(eclipse_dir_str)
                    datos = self._cargar_centros_existentes()
                    if datos:
                        idx     = datos.get("activo", 0)
                        centros = datos.get("centros", [])
                        nombre  = (centros[idx].get("nombre_centro", "")
                                   if centros and idx < len(centros) else "")
                        self._lbl_centro_nombre_ok.config(text=nombre)
                except Exception:
                    self._lbl_centro_nombre_ok.config(text="")
                self._f_nuevo.pack_forget()
                self._f_inicio_ok.pack(fill="x")
                return

        self._f_inicio_ok.pack_forget()
        self._f_nuevo.pack(fill="x")

    def _cmd_reparar_directo(self):
        """Inicia reparación directamente desde pantalla inicio (sin modal)."""
        eclipse_dir_str = self._var_dir.get().strip()
        if eclipse_dir_str:
            self._eclipse_dir = Path(eclipse_dir_str)
        if not self._eclipse_dir or not self._eclipse_dir.exists():
            messagebox.showerror("Error", "Directorio ECLIPSE-T no encontrado.",
                                 parent=self.root)
            return
        self._iniciar_instalacion()

    def _cmd_cambiar_centro(self):
        """Va a la pantalla de gestión de centros (reconfiguración)."""
        eclipse_dir_str = self._var_dir.get().strip()
        if eclipse_dir_str:
            self._eclipse_dir = Path(eclipse_dir_str)
        if not self._eclipse_dir or not self._eclipse_dir.exists():
            messagebox.showerror("Error", "Directorio ECLIPSE-T no encontrado.",
                                 parent=self.root)
            return
        self._poblar_reconfig()
        self._mostrar(self._f_reconfig)

    def _detectar_eclipse(self):
        candidatos = list(self._ECLIPSE_CANDIDATOS) + self._candidatos_desktop()
        for p in candidatos:
            if p.exists() and (
                (p / "ECLIPSE-T.exe").exists() or
                (p / "eclipse_t_v3.py").exists() or
                (p / "eclipse_t_v2.py").exists()
            ):
                self._var_dir.set(str(p))
                self._eclipse_dir = p
                # Solo pre-rellena el directorio — la clave siempre valida primero
                return
        # Ningún directorio detectado — mostrar frame de nueva instalación
        self._actualizar_modo_inicio()

    def _seleccionar_dir(self):
        d = filedialog.askdirectory(title="Seleccionar directorio ECLIPSE-T",
                                     initialdir="E:/")
        if d:
            self._var_dir.set(d)

    def _comenzar(self):
        self._forzar_nuevo_install = False
        eclipse_dir = Path(self._var_dir.get().strip())
        if not eclipse_dir.exists():
            self._lbl_msg.config(
                text="Directorio no encontrado. Seleccione la carpeta ECLIPSE.", fg=RED)
            return
        self._eclipse_dir = eclipse_dir

        clave = self._var_clave.get().strip()
        if not clave:
            self._lbl_msg.config(text="Ingrese un código de instalación.", fg=RED)
            return

        self._lbl_msg.config(text="Verificando código…", fg=GOLD)
        self.root.update()

        valida, estado = self._validar_clave(clave)
        if not valida:
            try:
                from hefestos_key_validator import MENSAJES  # type: ignore
                self._lbl_msg.config(text=MENSAJES.get(estado, estado), fg=RED)
            except ImportError:
                self._lbl_msg.config(text=f"Clave inválida ({estado})", fg=RED)
            return

        if estado == "sin_red":
            if not messagebox.askyesno(
                "Sin conexión a internet",
                "No se pudo verificar el código (sin internet).\n"
                "La instalación continuará, pero el código quedará\n"
                "pendiente de verificación posterior.\n\n"
                "¿Continuar de todas formas?",
            ):
                self._lbl_msg.config(text="", fg=RED)
                return

        self._es_maestra = (estado == "maestra")
        self._lbl_msg.config(text="")

        if self._es_maestra:
            self._aplicar_defaults_maestra()

        # ── Bifurcación: ¿ya hay centros configurados? ───────────────────────
        centros_dat = eclipse_dir / "resources" / "centros.dat"
        if centros_dat.exists():
            respuesta = messagebox.askyesno(
                "HEFESTOS — Ya configurado",
                "Este equipo ya tiene ECLIPSE-T instalado y configurado.\n\n"
                "¿Desea AGREGAR un nuevo centro de salud?\n\n"
                "   Sí  →  Agregar nuevo centro (consume esta clave)\n"
                "   No  →  Cambiar centro activo (sin reinstalar)",
                parent=self.root,
                icon="question",
            )
            if respuesta:
                self._modo_agregar_centro = True
                self._mostrar(self._f_config)
            else:
                self._poblar_reconfig()
                self._mostrar(self._f_reconfig)
            return

        self._mostrar(self._f_config)

    def _validar_clave(self, clave: str) -> tuple:
        try:
            from hefestos_key_validator import validar_clave_instalacion  # type: ignore
            return validar_clave_instalacion(clave, equipo_id=platform.node())
        except ImportError:
            return True, "sin_red"

    # ── Pantalla 2: Reconfig (gestión multi-centro) ──────────────────────────

    def _construir_reconfig(self):
        fr = self._f_reconfig

        tk.Label(fr, text="HEFESTOS — Gestionar Centros",
                 font=("Georgia", 15, "bold"), fg=GOLD, bg=BG).pack(pady=(20, 2))
        tk.Label(fr,
                 text="Seleccione un centro para activarlo o agregue uno nuevo",
                 font=("Georgia", 9), fg=DIM, bg=BG).pack()
        tk.Frame(fr, height=2, bg=GOLD).pack(fill="x", padx=40, pady=(10, 6))

        # Área de centros (se puebla dinámicamente)
        self._frm_centros = tk.Frame(fr, bg=BG)
        self._frm_centros.pack(fill="both", expand=True, padx=30, pady=6)

        # Botones inferiores
        btns = tk.Frame(fr, bg=BG)
        btns.pack(pady=(6, 16))

        tk.Button(btns, text="+ Agregar nuevo centro",
                  font=("Georgia", 10, "bold"),
                  bg=ACCENT, fg="white", relief="flat", padx=14, pady=7,
                  activebackground="#A87018",
                  command=self._cmd_agregar_nuevo_centro).pack(side="left", padx=(0, 10))

        tk.Button(btns, text="Cerrar",
                  font=("Georgia", 10), bg=DARK, fg=TEXT,
                  relief="flat", padx=14, pady=6,
                  command=self.root.destroy).pack(side="left")

    def _poblar_reconfig(self):
        """Rellena la pantalla reconfig con los centros existentes."""
        datos = self._cargar_centros_existentes()
        if not datos:
            return

        for w in self._frm_centros.winfo_children():
            w.destroy()

        centros  = datos.get("centros", [])
        activo   = datos.get("activo", 0)

        for idx, centro in enumerate(centros):
            nombre = centro.get("nombre_centro", "Centro sin nombre")
            logo_rel = centro.get("logo_principal", "")
            logo_path = None
            if self._eclipse_dir and logo_rel:
                p = self._eclipse_dir / "resources" / logo_rel
                if p.exists():
                    logo_path = p

            es_activo = (idx == activo)
            bg_fila = "#E8F5E9" if es_activo else BG2

            fila = tk.Frame(self._frm_centros, bg=bg_fila, relief="groove", bd=1,
                             cursor="hand2")
            fila.pack(fill="x", pady=4, padx=4)
            fila.bind("<Button-1>", lambda e, i=idx: self._activar_centro(i))

            # Logo
            img = _cargar_logo_tk(logo_path, 60)
            if img:
                lbl_img = tk.Label(fila, image=img, bg=bg_fila, cursor="hand2")
                lbl_img.image = img  # retener referencia
                lbl_img.pack(side="left", padx=10, pady=8)
                lbl_img.bind("<Button-1>", lambda e, i=idx: self._activar_centro(i))
            else:
                tk.Label(fila, text="🏥", font=("Georgia", 28),
                         bg=bg_fila, cursor="hand2").pack(side="left", padx=10, pady=8)

            info = tk.Frame(fila, bg=bg_fila)
            info.pack(side="left", fill="both", expand=True, pady=8)
            info.bind("<Button-1>", lambda e, i=idx: self._activar_centro(i))

            tk.Label(info, text=nombre, font=("Georgia", 11, "bold"),
                     fg=TEXT, bg=bg_fila, anchor="w",
                     cursor="hand2").pack(anchor="w")
            tk.Label(info,
                     text=centro.get("comuna", "") + "  ·  " + centro.get("servicio_salud", ""),
                     font=("Georgia", 9), fg=DIM, bg=bg_fila, anchor="w").pack(anchor="w")

            if es_activo:
                tk.Label(fila, text="● ACTIVO", font=("Georgia", 9, "bold"),
                         fg=GREEN, bg=bg_fila).pack(side="right", padx=14)

    def _activar_centro(self, idx: int):
        datos = self._cargar_centros_existentes()
        if not datos:
            return
        datos["activo"] = idx
        self._guardar_centros_dat(datos)
        self._regenerar_config_centro(datos)
        self._poblar_reconfig()
        messagebox.showinfo(
            "Centro activado",
            f"Centro «{datos['centros'][idx].get('nombre_centro', '')}» activado.\n"
            "Reinicie ECLIPSE-T y HELIOS para aplicar el cambio.",
            parent=self.root
        )

    def _cmd_agregar_nuevo_centro(self):
        self._modo_agregar_centro = True
        self._forzar_nuevo_install = True
        self._var_clave.set("")
        self._lbl_msg.config(text="")
        self._mostrar(self._f_inicio)
        self.root.after(0, self._actualizar_modo_inicio)

    # ── Mantenimiento (Reparar / Desinstalar) ────────────────────────────────

    def _cmd_mantenimiento(self):
        """Modal de mantenimiento accesible desde pantalla Inicio sin requerir clave."""
        ed = self._eclipse_dir
        if not ed:
            # Intentar detectar de nuevo
            self._detectar_eclipse()
            ed = self._eclipse_dir
        if not ed:
            messagebox.showerror(
                "Directorio no encontrado",
                "No se detectó una instalación de ECLIPSE-T.\n"
                "Seleccione el directorio en el campo 'Directorio ECLIPSE-T'.",
                parent=self.root,
            )
            return

        dlg = tk.Toplevel(self.root)
        dlg.title("HEFESTOS — Mantenimiento")
        dlg.configure(bg=BG)
        dlg.resizable(False, False)
        dlg.grab_set()
        dlg.protocol("WM_DELETE_WINDOW", dlg.destroy)

        tk.Label(dlg, text="Mantenimiento de ECLIPSE-T",
                 font=("Georgia", 14, "bold"), fg=GOLD, bg=BG).pack(pady=(16, 2))
        tk.Label(dlg, text=str(ed),
                 font=("Courier", 8), fg=DIM, bg=BG).pack()
        tk.Frame(dlg, height=1, bg=DARK).pack(fill="x", padx=20, pady=10)

        cuerpo = tk.Frame(dlg, bg=BG, padx=30)
        cuerpo.pack(fill="x")

        # — Reparar ──────────────────────────────────────────────────────────
        bloque_rep = tk.Frame(cuerpo, bg=BG2, relief="groove", bd=1)
        bloque_rep.pack(fill="x", pady=(0, 10))
        tk.Label(bloque_rep, text="Reparar instalación",
                 font=("Georgia", 11, "bold"), fg=TEXT, bg=BG2).pack(
                     anchor="w", padx=12, pady=(10, 2))
        tk.Label(bloque_rep,
                 text="Vuelve a verificar y descarga los componentes faltantes.\n"
                      "Los archivos ya presentes no se modifican.",
                 font=("Georgia", 8), fg=DIM, bg=BG2, justify="left").pack(
                     anchor="w", padx=12, pady=(0, 6))
        tk.Button(bloque_rep, text="  Reparar instalación  ▶",
                  font=("Georgia", 10, "bold"),
                  bg=ACCENT, fg="white", relief="flat", padx=12, pady=6,
                  activebackground="#A87018",
                  command=lambda: [dlg.destroy(), self._iniciar_instalacion()]
                  ).pack(anchor="w", padx=12, pady=(0, 10))

        # — Desinstalar ──────────────────────────────────────────────────────
        bloque_des = tk.Frame(cuerpo, bg="#FFF0F0", relief="groove", bd=1)
        bloque_des.pack(fill="x", pady=(0, 10))
        tk.Label(bloque_des, text="Desinstalar",
                 font=("Georgia", 11, "bold"), fg=RED, bg="#FFF0F0").pack(
                     anchor="w", padx=12, pady=(10, 2))
        tk.Label(bloque_des,
                 text="Elimina la configuración del centro y/o archivos del sistema.\n"
                      "Seleccionará qué componentes borrar antes de confirmar.",
                 font=("Georgia", 8), fg=DIM, bg="#FFF0F0", justify="left").pack(
                     anchor="w", padx=12, pady=(0, 6))
        tk.Button(bloque_des, text="  Desinstalar…",
                  font=("Georgia", 10, "bold"),
                  bg="#C62828", fg="white", relief="flat", padx=12, pady=6,
                  activebackground="#9B1B1B",
                  command=lambda: [dlg.destroy(), self._cmd_desinstalar()]
                  ).pack(anchor="w", padx=12, pady=(0, 10))

        tk.Button(dlg, text="Cancelar",
                  font=("Georgia", 10), bg=DARK, fg=TEXT,
                  relief="flat", padx=14, pady=6,
                  command=dlg.destroy).pack(pady=(0, 14))

        dlg.update_idletasks()
        sw, sh = dlg.winfo_screenwidth(), dlg.winfo_screenheight()
        w, h   = dlg.winfo_width(), dlg.winfo_height()
        dlg.geometry(f"+{(sw-w)//2}+{(sh-h)//2}")

    def _cmd_desinstalar(self):
        """Diálogo de selección de componentes a eliminar."""
        ed = self._eclipse_dir
        if not ed:
            return

        dlg = tk.Toplevel(self.root)
        dlg.title("Desinstalar ECLIPSE-T")
        dlg.configure(bg=BG)
        dlg.resizable(False, False)
        dlg.grab_set()
        dlg.protocol("WM_DELETE_WINDOW", dlg.destroy)

        tk.Label(dlg, text="Desinstalar ECLIPSE-T",
                 font=("Georgia", 14, "bold"), fg=RED, bg=BG).pack(pady=(16, 2))
        tk.Label(dlg, text=f"Directorio: {ed}",
                 font=("Courier", 8), fg=DIM, bg=BG).pack()
        tk.Frame(dlg, height=1, bg=DARK).pack(fill="x", padx=20, pady=8)

        tk.Label(dlg, text="Seleccione qué componentes eliminar:",
                 font=("Georgia", 10), fg=TEXT, bg=BG).pack(anchor="w", padx=24, pady=(0, 6))

        var_config = tk.BooleanVar(value=True)
        var_exes   = tk.BooleanVar(value=False)
        var_modelo = tk.BooleanVar(value=False)
        var_datos  = tk.BooleanVar(value=False)

        opts = tk.Frame(dlg, bg=BG)
        opts.pack(fill="x", padx=24, pady=2)

        def _chk(var, text, color=TEXT, bold=False):
            font = ("Georgia", 9, "bold") if bold else ("Georgia", 9)
            tk.Checkbutton(opts, variable=var, text=text,
                           font=font, fg=color, bg=BG, selectcolor=BG2,
                           activebackground=BG).pack(anchor="w", pady=2)

        _chk(var_config, "Eliminar configuración del centro  (centros.dat, .key, config_centro.json)")
        _chk(var_exes,   "Eliminar ejecutables  (ECLIPSE-T.exe, helios.exe, geckodriver.exe)")
        _chk(var_modelo, "Eliminar modelo de voz  (modelos/base.pt  ≈ 139 MB)")
        _chk(var_datos,
             "⚠  Eliminar datos clínicos  (Archivos_ECICEP/)  — IRREVERSIBLE",
             color=RED, bold=True)

        tk.Label(dlg,
                 text="Los datos clínicos NO pueden recuperarse.\n"
                      "Asegúrese de tener un respaldo antes de continuar.",
                 font=("Georgia", 8, "italic"), fg=RED, bg=BG,
                 justify="left").pack(anchor="w", padx=28, pady=(2, 10))

        tk.Frame(dlg, height=1, bg=DARK).pack(fill="x", padx=20, pady=4)

        btns = tk.Frame(dlg, bg=BG)
        btns.pack(pady=(0, 14))

        def _confirmar():
            if not any([var_config.get(), var_exes.get(), var_modelo.get(), var_datos.get()]):
                messagebox.showwarning("Nada seleccionado",
                                       "Seleccione al menos una opción.",
                                       parent=dlg)
                return
            if var_datos.get():
                if not messagebox.askyesno(
                    "⚠  Confirmación final",
                    "Está a punto de eliminar datos clínicos de forma PERMANENTE.\n\n"
                    "Esta acción NO puede deshacerse.\n\n"
                    "¿Está completamente seguro de continuar?",
                    parent=dlg, icon="warning",
                ):
                    return
            dlg.destroy()
            self._ejecutar_desinstalacion(
                config=var_config.get(),
                exes=var_exes.get(),
                modelo=var_modelo.get(),
                datos=var_datos.get(),
            )

        tk.Button(btns, text="Confirmar desinstalación",
                  font=("Georgia", 10, "bold"),
                  bg=RED, fg="white", relief="flat", padx=14, pady=6,
                  activebackground="#9B1B1B",
                  command=_confirmar).pack(side="left", padx=(0, 10))
        tk.Button(btns, text="Cancelar",
                  font=("Georgia", 10), bg=DARK, fg=TEXT,
                  relief="flat", padx=14, pady=6,
                  command=dlg.destroy).pack(side="left")

        dlg.update_idletasks()
        sw, sh = dlg.winfo_screenwidth(), dlg.winfo_screenheight()
        w, h   = dlg.winfo_width(), dlg.winfo_height()
        dlg.geometry(f"+{(sw-w)//2}+{(sh-h)//2}")

    def _ejecutar_desinstalacion(self, config: bool, exes: bool,
                                  modelo: bool, datos: bool):
        """Elimina los componentes seleccionados y muestra un resumen."""
        eliminados: list[str] = []
        errores:    list[str] = []
        ed = self._eclipse_dir

        def _rm(path: Path, desc: str):
            try:
                if path.is_dir():
                    shutil.rmtree(path)
                elif path.exists():
                    path.unlink()
                else:
                    return
                eliminados.append(desc)
            except Exception as exc:
                errores.append(f"{desc}: {exc}")

        if config:
            _rm(ed / "resources" / "centros.dat", "centros.dat")
            _rm(ed / "resources" / ".key",         ".key")
            _rm(ed / "config_centro.json",          "config_centro.json")

        if exes:
            for nombre in ("ECLIPSE-T.exe", "helios.exe", "HELIOS.exe",
                            "geckodriver.exe", "HADES.exe"):
                _rm(ed / nombre, nombre)

        if modelo:
            _rm(ed / "modelos" / "base.pt",  "modelos/base.pt")
            _rm(ed / "modelos" / "small.pt", "modelos/small.pt")

        if datos:
            _rm(ed / "Archivos_ECICEP", "Archivos_ECICEP/")
            _rm(ed / "logs",            "logs/")

        resumen = ""
        if eliminados:
            resumen += "Eliminados:\n" + "\n".join(f"  ✓ {x}" for x in eliminados)
        if errores:
            resumen += "\n\nErrores:\n" + "\n".join(f"  ✗ {x}" for x in errores)
        if not resumen:
            resumen = "No se encontraron archivos para eliminar."

        if exes or datos:
            resumen += "\n\nHEFESTOS se cerrará ahora."
            messagebox.showinfo("Desinstalación completada", resumen, parent=self.root)
            os._exit(0)
        else:
            messagebox.showinfo("Desinstalación completada", resumen, parent=self.root)
            if config:
                self._mostrar(self._f_inicio)

    # ── Pantalla 3: Configuración del centro ─────────────────────────────────

    def _mk_var(self, key: str, default="") -> tk.StringVar:
        v = tk.StringVar(value=str(default))
        self._cfg[key] = v
        return v

    def _construir_config(self):
        fr = self._f_config

        tk.Label(fr, text="Configurar Centro de Salud",
                 font=("Georgia", 15, "bold"), fg=GOLD, bg=BG).pack(pady=(18, 2))
        tk.Label(fr,
                 text="Esta información se usará en todos los documentos generados por ECLIPSE-T",
                 font=("Georgia", 9), fg=DIM, bg=BG).pack()
        tk.Frame(fr, height=2, bg=GOLD).pack(fill="x", padx=40, pady=(10, 6))

        # Cuerpo scrollable
        wrap = tk.Frame(fr, bg=BG)
        wrap.pack(fill="both", expand=True)
        sb = ttk.Scrollbar(wrap, orient="vertical")
        sb.pack(side="right", fill="y")
        cv_wrap = tk.Canvas(wrap, bg=BG, highlightthickness=0,
                            yscrollcommand=sb.set)
        cv_wrap.pack(side="left", fill="both", expand=True)
        sb.config(command=cv_wrap.yview)

        body = tk.Frame(cv_wrap, bg=BG)
        body_id = cv_wrap.create_window((0, 0), window=body, anchor="nw")

        def _on_resize(e):
            cv_wrap.itemconfig(body_id, width=e.width)
            cv_wrap.configure(scrollregion=cv_wrap.bbox("all"))
        cv_wrap.bind("<Configure>", _on_resize)
        body.bind("<Configure>",
                  lambda e: cv_wrap.configure(scrollregion=cv_wrap.bbox("all")))

        lf_kw = dict(fg=GOLD, bg=BG, font=("Georgia", 9, "bold"))

        # Identidad
        lf1 = tk.LabelFrame(body, text="  Identidad del Centro  ", **lf_kw)
        lf1.pack(fill="x", padx=8, pady=(4, 6))
        self._campo(lf1, "Nombre del centro:", "nombre_centro",
                    "CESFAM Cerrillos de Tamaya", width=36, row=0)
        self._campo(lf1, "Código DEIS:", "codigo_centro", "", width=14, row=1, col=0)
        self._campo(lf1, "Comuna:", "comuna", "", width=18, row=1, col=2)
        self._campo(lf1, "Servicio de Salud:", "servicio_salud",
                    "Servicio de Salud Coquimbo", width=28, row=2)

        # Laboratorio
        lf2 = tk.LabelFrame(body, text="  Laboratorio (HELIOS)  ", **lf_kw)
        lf2.pack(fill="x", padx=8, pady=4)

        # Fila tipo conector — sub-frame con pack para evitar overflow de grid
        fila_tipo = tk.Frame(lf2, bg=BG)
        fila_tipo.grid(row=0, column=0, columnspan=4, sticky="w", padx=4, pady=3)
        tk.Label(fila_tipo, text="Tipo:", bg=BG, fg=TEXT,
                 font=("Georgia", 9)).pack(side="left", padx=(4, 6))
        self._cfg["conector_lab"] = tk.StringVar(value="iris")
        for val, txt in [("iris", "IRIS (red local)"),
                          ("redclinica", "Red Clínica (internet)"),
                          ("ninguno", "Sin laboratorio")]:
            tk.Radiobutton(fila_tipo, text=txt, variable=self._cfg["conector_lab"],
                           value=val, bg=BG, fg=TEXT, selectcolor=BG2,
                           activebackground=BG,
                           font=("Georgia", 9)).pack(side="left", padx=(0, 10))

        self._campo(lf2, "URL IRIS:", "iris_url",
                    "http://207.248.201.73:8080/irisconsultorio/", width=34, row=1)
        self._campo(lf2, "Usuario IRIS:", "iris_usuario", "", width=16, row=2, col=0)
        self._campo_pass(lf2, "Contraseña:", "iris_password", row=2, col=2)
        self._campo(lf2, "URL RedClínica:", "redclinica_url",
                    "https://examenes.redclinica.cl", width=34, row=3)
        self._campo(lf2, "Usuario RedClínica:", "redclinica_usuario", "", width=16, row=4, col=0)
        self._campo_pass(lf2, "Contraseña:", "redclinica_password", row=4, col=2)

        if not _CRYPTO_OK:
            tk.Label(lf2,
                     text="⚠ cryptography no instalado — credenciales sin cifrar",
                     fg=RED, bg=BG, font=("Georgia", 8)).grid(
                         row=5, column=0, columnspan=4, padx=8, pady=2, sticky="w")

        # Profesional
        lf3 = tk.LabelFrame(body, text="  Profesional Responsable  ", **lf_kw)
        lf3.pack(fill="x", padx=8, pady=4)
        self._campo(lf3, "Nombre:", "nombre_profesional",
                    "Dr. Nicolás Vargas", width=28, row=0)
        self._campo(lf3, "Profesión:", "profesion",
                    "Médico Familiar", width=20, row=1, col=0)
        self._campo(lf3, "Registro:", "registro", "", width=14, row=1, col=2)

        # Logos
        lf4 = tk.LabelFrame(body, text="  Logos (máx. 2, opcional)  ", **lf_kw)
        lf4.pack(fill="x", padx=8, pady=4)
        tk.Label(lf4, text="Si no elige ninguno se usará el logo del Dr. Vargas.",
                 font=("Georgia", 8), fg=DIM, bg=BG).grid(
                     row=0, column=0, columnspan=4, padx=8, pady=(4, 2), sticky="w")
        self._cfg["logo_principal"]  = tk.StringVar()
        self._cfg["logo_secundario"] = tk.StringVar()
        self._fila_logo(lf4, "Logo principal:",   "logo_principal",  row=1)
        self._fila_logo(lf4, "Logo secundario:",  "logo_secundario", row=2)

        # Botones — dentro del body scrollable para que siempre sean visibles
        btns = tk.Frame(body, bg=BG)
        btns.pack(pady=(8, 14))
        tk.Button(btns, text="Omitir por ahora",
                  font=("Georgia", 10), bg=DARK, fg=TEXT,
                  relief="flat", padx=14, pady=6,
                  command=self._omitir_config).pack(side="left", padx=(0, 10))
        tk.Button(btns, text="Guardar y continuar  ▶",
                  font=("Georgia", 11, "bold"),
                  bg=ACCENT, fg="white", relief="flat", padx=16, pady=7,
                  activebackground="#A87018",
                  command=self._guardar_config).pack(side="left")

    def _campo(self, parent, label: str, key: str, default: str,
               width: int = 24, row: int = 0, col: int = 0):
        tk.Label(parent, text=label, bg=BG, fg=TEXT,
                 font=("Georgia", 9)).grid(row=row, column=col,
                                            padx=(8, 2), pady=3, sticky="w")
        v = self._mk_var(key, default)
        tk.Entry(parent, textvariable=v, bg=BG2, fg=TEXT,
                 insertbackground=GOLD, relief="flat",
                 font=("Courier", 9), width=width).grid(
                     row=row, column=col+1, padx=(0, 8), pady=3, sticky="w")

    def _campo_pass(self, parent, label: str, key: str,
                    row: int = 0, col: int = 0):
        tk.Label(parent, text=label, bg=BG, fg=TEXT,
                 font=("Georgia", 9)).grid(row=row, column=col,
                                            padx=(8, 2), pady=3, sticky="w")
        v = self._mk_var(key, "")
        tk.Entry(parent, textvariable=v, show="•", bg=BG2, fg=TEXT,
                 insertbackground=GOLD, relief="flat",
                 font=("Courier", 9), width=18).grid(
                     row=row, column=col+1, padx=(0, 8), pady=3, sticky="w")

    def _fila_logo(self, parent, label: str, key: str, row: int):
        tk.Label(parent, text=label, bg=BG, fg=TEXT,
                 font=("Georgia", 9)).grid(row=row, column=0,
                                            padx=(8, 2), pady=3, sticky="w")
        entry = tk.Entry(parent, textvariable=self._cfg[key], bg=BG2, fg=TEXT,
                         insertbackground=GOLD, relief="flat",
                         font=("Courier", 8), width=30)
        entry.grid(row=row, column=1, padx=(0, 4), pady=3, sticky="w")
        tk.Button(parent, text="…", bg=DARK, fg=TEXT, relief="flat",
                  command=lambda k=key: self._seleccionar_logo(k)).grid(
                      row=row, column=2, padx=(0, 8), pady=3)

    def _seleccionar_logo(self, key: str):
        path = filedialog.askopenfilename(
            title="Seleccionar imagen",
            filetypes=[("Imágenes", "*.png *.jpg *.jpeg *.bmp"), ("Todos", "*.*")]
        )
        if path:
            self._cfg[key].set(path)

    def _aplicar_defaults_maestra(self):
        for key, val in _DEFAULTS_MAESTRA.items():
            if key in self._cfg:
                self._cfg[key].set(str(val))

    def _omitir_config(self):
        self._pedir_tc_y_instalar()

    def _pedir_tc_y_instalar(self):
        """Muestra el EULA antes de iniciar la instalación. (Task 3)"""
        _DialogoLicencia(
            self.root,
            on_acepto=self._iniciar_instalacion,
            on_rechazo=lambda: None,
        )

    def _guardar_config(self):
        if not self._eclipse_dir:
            return

        nuevo = {k: v.get() for k, v in self._cfg.items()}
        nuevo["id"] = _generar_id(nuevo.get("nombre_centro", "centro"))

        recursos = self._eclipse_dir / "resources"
        recursos.mkdir(exist_ok=True)

        # Copiar logos; si no hay logo principal → usar logo_dr_vargas.png
        for campo, dest_name in (("logo_principal",  "logo_centro.png"),
                                  ("logo_secundario", "logo_ss.png")):
            src = nuevo.get(campo, "").strip()
            if src and Path(src).exists():
                shutil.copy2(src, recursos / dest_name)
                nuevo[campo] = dest_name
            elif not src and campo == "logo_principal":
                default = recursos / "logo_dr_vargas.png"
                if default.exists():
                    shutil.copy2(default, recursos / dest_name)
                    nuevo[campo] = dest_name

        # Cifrar credenciales individualmente
        fkey = self._obtener_o_crear_key(recursos)
        if _CRYPTO_OK and fkey:
            f = Fernet(fkey)
            for campo in ("iris_usuario", "iris_password",
                           "redclinica_usuario", "redclinica_password"):
                raw = nuevo.get(campo, "").strip()
                if raw:
                    nuevo[campo]                    = f.encrypt(raw.encode()).decode()
                    nuevo[f"_{campo}_cifrado"]      = True

        # Cargar o crear estructura multi-centro
        datos = self._cargar_centros_existentes() or {
            "version": 1, "activo": 0, "centros": []
        }

        if self._modo_agregar_centro:
            datos["centros"].append(nuevo)
            datos["activo"] = len(datos["centros"]) - 1
        else:
            datos["centros"] = [nuevo]
            datos["activo"]  = 0

        # Cifrar JSON completo → centros.dat
        self._guardar_centros_dat(datos)

        # Mantener config_centro.json compatible con ECLIPSE/HELIOS
        self._regenerar_config_centro(datos)

        self._modo_agregar_centro = False
        self._pedir_tc_y_instalar()

    def _obtener_o_crear_key(self, recursos: Path) -> bytes | None:
        if not _CRYPTO_OK:
            return None
        key_path = recursos / ".key"
        if key_path.exists():
            return key_path.read_bytes()
        fkey = Fernet.generate_key()
        key_path.write_bytes(fkey)
        return fkey

    def _guardar_centros_dat(self, datos: dict):
        if not self._eclipse_dir:
            return
        recursos = self._eclipse_dir / "resources"
        recursos.mkdir(exist_ok=True)
        json_bytes = json.dumps(datos, ensure_ascii=False, indent=2).encode("utf-8")
        dat_path = recursos / "centros.dat"
        if _CRYPTO_OK:
            fkey = self._obtener_o_crear_key(recursos)
            if fkey:
                dat_path.write_bytes(Fernet(fkey).encrypt(json_bytes))
                return
        dat_path.write_bytes(json_bytes)  # fallback sin cifrado

    def _cargar_centros_existentes(self) -> dict | None:
        if not self._eclipse_dir:
            return None
        dat_path = self._eclipse_dir / "resources" / "centros.dat"
        if not dat_path.exists():
            return None
        try:
            data = dat_path.read_bytes()
            if _CRYPTO_OK:
                key_path = self._eclipse_dir / "resources" / ".key"
                if key_path.exists():
                    data = Fernet(key_path.read_bytes()).decrypt(data)
            return json.loads(data.decode("utf-8"))
        except Exception:
            return None

    def _regenerar_config_centro(self, datos: dict):
        """Escribe config_centro.json con el centro activo (para ECLIPSE/HELIOS)."""
        if not self._eclipse_dir:
            return
        try:
            idx    = datos.get("activo", 0)
            centro = datos["centros"][idx].copy()
            centro["conector_lab"] = centro.get("conector_lab", "iris")
            dest   = self._eclipse_dir / "config_centro.json"
            with open(dest, "w", encoding="utf-8") as fh:
                json.dump(centro, fh, ensure_ascii=False, indent=2)
        except Exception:
            pass

    # ── Pantalla 4: Instalación ──────────────────────────────────────────────

    def _construir_instalacion(self):
        fr = self._f_instalacion

        hdr = tk.Frame(fr, bg=DARK)
        hdr.pack(fill="x")
        tk.Label(hdr, text="HEFESTOS — Instalación en curso",
                 font=("Georgia", 12, "bold"), fg=GOLD, bg=DARK).pack(
                     side="left", padx=16, pady=10)

        # Canvas GIF enmarcado (oscuro sobre fondo crema)
        anim_frame = tk.Frame(fr, bg=BG, pady=6)
        anim_frame.pack()
        canvas_forge = tk.Canvas(
            anim_frame, width=300, height=300,
            bg=ANIM_BG, highlightthickness=3,
            highlightbackground=GOLD,
        )
        canvas_forge.pack()
        self._animacion = AnimacionForja(canvas_forge, ancho=300, alto=300)

        # Lista de pasos
        pasos_frame = tk.Frame(fr, bg=BG)
        pasos_frame.pack(fill="x", padx=14, pady=(4, 4))

        for grupo in self._manifest["grupos"]:
            tk.Label(pasos_frame, text=f"  {grupo['nombre']}",
                     font=("Georgia", 9, "bold"), fg=GOLD, bg=BG,
                     anchor="w").pack(fill="x", pady=(4, 1))
            for paso in grupo["pasos"]:
                fila = tk.Frame(pasos_frame, bg=BG)
                fila.pack(fill="x", padx=14, pady=1)
                ico = tk.Label(fila, text="○", font=("Georgia", 10),
                               fg=GRAY, bg=BG, width=2)
                ico.pack(side="left")
                lbl = tk.Label(fila, text=paso["desc"],
                               font=("Georgia", 9), fg=TEXT, bg=BG, anchor="w")
                lbl.pack(side="left", fill="x")
                self._labels_pasos.append({"id": paso["id"], "ico": ico, "lbl": lbl})

        # Barra de progreso
        pk = tk.Frame(fr, bg=BG)
        pk.pack(fill="x", padx=14, pady=(6, 2))
        style = ttk.Style()
        style.configure("Gold.Horizontal.TProgressbar",
                         troughcolor=BG2, background=ACCENT)
        self._progress = ttk.Progressbar(pk, style="Gold.Horizontal.TProgressbar",
                                          mode="determinate", length=560, maximum=100)
        self._progress.pack(fill="x")

        self._lbl_estado = tk.Label(fr, text="Preparando…",
                                     font=("Georgia", 9, "italic"),
                                     fg=GOLD, bg=BG)
        self._lbl_estado.pack(anchor="w", padx=16)

        # Log
        log_wrap = tk.Frame(fr, bg=BG2, relief="sunken", bd=1)
        log_wrap.pack(fill="both", expand=True, padx=14, pady=(4, 8))
        self._log = tk.Text(log_wrap, bg=BG2, fg=TEXT,
                             font=("Courier", 8), relief="flat",
                             state="disabled", wrap="word", height=6)
        sb2 = ttk.Scrollbar(log_wrap, command=self._log.yview)
        self._log.configure(yscrollcommand=sb2.set)
        sb2.pack(side="right", fill="y")
        self._log.pack(fill="both", expand=True, padx=4, pady=4)

    def _log_append(self, texto: str):
        self._log.configure(state="normal")
        self._log.insert("end", texto + "\n")
        self._log.see("end")
        self._log.configure(state="disabled")

    def _iniciar_instalacion(self):
        self._mostrar(self._f_instalacion)
        self._pasos_completados = 0
        self._progress["value"] = 0
        self._animacion.iniciar()
        hilo = threading.Thread(target=self._ejecutar_instalacion, daemon=True)
        hilo.start()
        self.root.after(120, self._procesar_cola)

    def _procesar_cola(self):
        try:
            while True:
                msg = self._cola.get_nowait()
                t   = msg["tipo"]
                if t == "log":
                    self._log_append(msg["texto"])
                elif t == "estado":
                    self._lbl_estado.config(text=msg["texto"])
                elif t == "paso_inicio":
                    self._set_paso(msg["id"], "►", ACCENT, TEXT)
                elif t in ("paso_ok", "paso_error", "paso_skip"):
                    self._pasos_completados += 1
                    pct = int(self._pasos_completados / self._total_pasos * 100)
                    self._progress["value"] = pct
                    if t == "paso_ok":
                        self._set_paso(msg["id"], "✓", GREEN, GREEN)
                    elif t == "paso_error":
                        self._set_paso(msg["id"], "✗", RED,   RED)
                    else:
                        self._set_paso(msg["id"], "–", GRAY,  GRAY)
                elif t == "fin":
                    self._progress["value"] = 100
                    self._animacion.detener()
                    self._lbl_estado.config(text="Instalación completada.")
                    self._mostrar_final()
                    return
        except queue.Empty:
            pass
        self.root.after(120, self._procesar_cola)

    def _set_paso(self, pid: str, ico: str, ic: str, lc: str):
        for e in self._labels_pasos:
            if e["id"] == pid:
                e["ico"].config(text=ico, fg=ic)
                e["lbl"].config(fg=lc)
                break

    def _emit(self, **kw):
        self._cola.put(kw)

    # ── Ejecución de pasos (hilo) ────────────────────────────────────────────

    def _get_exe_destino(self, asset: str, dest_key: str) -> "Path | None":
        """Devuelve la ruta absoluta donde se instalará un asset github_release."""
        if not self._eclipse_dir:
            return None
        if dest_key in ("eclipse_dir", "helios_dir"):
            # Ambos ejecutables van en el mismo directorio que ECLIPSE-T.exe
            return self._eclipse_dir / asset
        return _BASE_DIR / asset

    def _ejecutar_instalacion(self):
        # ── Pre-check: estado de ejecutables y modelos antes de empezar ─────
        self._emit(tipo="log", texto="── Verificación previa ──────────────────")
        for grupo in self._manifest["grupos"]:
            for paso in grupo["pasos"]:
                if paso["tipo"] == "github_release":
                    destino = self._get_exe_destino(
                        paso["asset"], paso.get("destino", "eclipse_dir")
                    )
                    if destino and destino.exists() and destino.stat().st_size > 1_048_576:
                        mb = destino.stat().st_size // (1024 * 1024)
                        self._emit(tipo="log",
                                    texto=f"  ✓ {paso['asset']}  —  ya presente ({mb} MB), se omite descarga")
                    else:
                        self._emit(tipo="log",
                                    texto=f"  ↓ {paso['asset']}  —  no encontrado, se descargará")
                elif paso["tipo"] == "descarga" and self._eclipse_dir:
                    destino = self._eclipse_dir / paso["destino"]
                    min_bytes = int(paso.get("mb", 0) * 1024 * 1024 * 0.5)
                    if destino.exists() and destino.stat().st_size > max(4096, min_bytes):
                        mb = destino.stat().st_size / (1024 * 1024)
                        self._emit(tipo="log",
                                    texto=f"  ✓ {paso['destino']}  —  ya presente ({mb:.0f} MB), se omite descarga")
                    else:
                        self._emit(tipo="log",
                                    texto=f"  ↓ {paso['destino']}  —  no encontrado, se descargará")
        self._emit(tipo="log", texto="─────────────────────────────────────────")

        # ── Ejecución del manifest ────────────────────────────────────────────
        for grupo in self._manifest["grupos"]:
            for paso in grupo["pasos"]:
                self._emit(tipo="estado", texto=f"{paso['desc']}…")
                self._emit(tipo="paso_inicio", id=paso["id"])
                try:
                    resultado = self._ejecutar_paso(paso)
                except Exception as exc:
                    self._emit(tipo="log", texto=f"EXCEPCIÓN: {exc}")
                    resultado = False
                if resultado == "skip":
                    self._emit(tipo="paso_skip", id=paso["id"])
                elif resultado:
                    self._emit(tipo="paso_ok", id=paso["id"])
                else:
                    self._emit(tipo="paso_error", id=paso["id"])
        self._prewarm_eclipse()
        self._emit(tipo="fin")

    def _prewarm_eclipse(self) -> None:
        """
        Lanza ECLIPSE-T.exe silenciosamente para que PyInstaller extraiga el
        bundle a %TEMP% la primera vez. La próxima apertura abre en ~5 seg.
        Se omite si ya hay una instancia corriendo o si el exe no existe.
        """
        import socket as _s
        exe = (self._eclipse_dir / "ECLIPSE-T.exe") if self._eclipse_dir else None
        if not exe or not exe.exists():
            return

        # Comprobar si ya hay una instancia de ECLIPSE corriendo (puerto 47291)
        try:
            chk = _s.socket(_s.AF_INET, _s.SOCK_STREAM)
            chk.setsockopt(_s.SOL_SOCKET, _s.SO_REUSEADDR, 0)
            chk.bind(("127.0.0.1", 47291))
            chk.close()
        except OSError:
            self._emit(tipo="log", texto="  Pre-extracción omitida — ECLIPSE ya está en ejecución.")
            return

        self._emit(tipo="estado", texto="Preparando primera ejecución…")
        self._emit(tipo="log",    texto="── Pre-extracción del bundle PyInstaller ──────")
        self._emit(tipo="log",    texto="  Iniciando ECLIPSE-T para cachear archivos temporales…")
        self._emit(tipo="log",    texto="  (Primera apertura: ~60 seg  →  siguientes: ~5 seg)")

        try:
            proc = subprocess.Popen(
                [str(exe)], cwd=str(self._eclipse_dir),
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
        except Exception as exc:
            self._emit(tipo="log", texto=f"  No se pudo iniciar ECLIPSE-T: {exc}")
            return

        # Esperar a que ECLIPSE adquiera el lock del puerto 47291
        # (significa que el bundle está extraído y Python arrancó)
        deadline = time.time() + 100
        listo = False
        while time.time() < deadline:
            if proc.poll() is not None:
                self._emit(tipo="log", texto="  ECLIPSE terminó antes de completar la extracción.")
                return
            try:
                chk = _s.socket(_s.AF_INET, _s.SOCK_STREAM)
                chk.setsockopt(_s.SOL_SOCKET, _s.SO_REUSEADDR, 0)
                chk.bind(("127.0.0.1", 47291))
                chk.close()
            except OSError:
                listo = True
                break
            time.sleep(2)

        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()

        if listo:
            self._emit(tipo="log", texto="  Bundle cacheado. ECLIPSE abrirá casi instantáneamente.")
        else:
            self._emit(tipo="log", texto="  Tiempo agotado — primer inicio puede tardar ~60 seg.")
        self._emit(tipo="log", texto="───────────────────────────────────────────────")

    def _ejecutar_paso(self, paso: dict) -> bool:
        tipo = paso["tipo"]

        if tipo == "verificar":
            vi = sys.version_info
            self._emit(tipo="log",
                        texto=f"Python {vi.major}.{vi.minor}.{vi.micro} detectado")
            ok = vi >= (3, 10)
            if not ok:
                self._emit(tipo="log", texto="ERROR: se requiere Python 3.10+")
            return ok

        if tipo == "pip_upgrade":
            return self._pip(["install", "--upgrade", "pip", "setuptools", "wheel"])

        if tipo == "pip":
            faltantes = self._paquetes_faltantes(paso["paquetes"])
            if not faltantes:
                self._emit(tipo="log",
                            texto=f"Ya instalado: {', '.join(paso['paquetes'])}")
                return "skip"
            if len(faltantes) < len(paso["paquetes"]):
                ya = set(paso["paquetes"]) - set(faltantes)
                self._emit(tipo="log", texto=f"Ya instalado: {', '.join(ya)}")
            return self._pip(["install"] + faltantes)

        if tipo == "whisper_model":
            return self._descargar_modelo_whisper(paso["modelo"], paso.get("mb", "?"))

        if tipo == "descarga":
            # Soporta url_completa (URL directa) o url relativa a OLYMPUS_RAW
            url     = paso.get("url_completa") or f"{OLYMPUS_RAW}/{paso['url']}"
            destino = self._eclipse_dir / paso["destino"]  # type: ignore
            # Pre-check: si el archivo ya existe con tamaño razonable, omitir descarga
            min_bytes = int(paso.get("mb", 0) * 1024 * 1024 * 0.5)
            if destino.exists() and destino.stat().st_size > max(4096, min_bytes):
                mb_local = destino.stat().st_size / (1024 * 1024)
                self._emit(tipo="log",
                            texto=f"{paso['destino']} ya presente ({mb_local:.0f} MB) — omitiendo descarga")
                return True  # Mostrar ✓ verde
            return self._descargar_archivo(url, destino, paso.get("url", paso["destino"]))

        if tipo == "verificar_app":
            return self._verificar_app(paso.get("app", ""))

        if tipo == "geckodriver":
            return self._instalar_geckodriver()

        if tipo == "script":
            return self._correr_script(paso["script"])

        if tipo == "test_arranque":
            return self._test_arranque()

        if tipo == "github_release":
            asset    = paso["asset"]
            dest_key = paso.get("destino", "eclipse_dir")
            mb_est   = paso.get("mb", "?")
            # Todos los ejecutables van en el mismo directorio que ECLIPSE-T.exe
            if dest_key in ("eclipse_dir", "helios_dir"):
                destino = self._eclipse_dir / asset          # type: ignore
            else:
                destino = _BASE_DIR / asset
            return self._descargar_release_github(asset, destino, mb_est)

        self._emit(tipo="log", texto=f"Tipo desconocido: {tipo}")
        return False

    # ── Implementaciones ─────────────────────────────────────────────────────

    def _paquetes_faltantes(self, paquetes: list) -> list:
        python = self._get_python()
        faltantes = []
        for pkg in paquetes:
            nombre = pkg.split("==")[0].split(">=")[0].split("[")[0].strip()
            r = subprocess.run([python, "-m", "pip", "show", nombre],
                               capture_output=True, timeout=10)
            if r.returncode != 0:
                faltantes.append(pkg)
        return faltantes

    def _pip(self, args: list) -> bool:
        result = subprocess.run(
            [self._get_python(), "-m", "pip"] + args,
            capture_output=True, text=True,
        )
        # Si falla y es un install, reintentar con --user (sin permisos de admin)
        if result.returncode != 0 and args and args[0] == "install" and "--user" not in args:
            salida = (result.stdout + result.stderr).lower()
            if any(k in salida for k in ("permission", "access", "denied", "read-only",
                                          "permissionerror", "cannot install")):
                self._emit(tipo="log", texto="Sin permisos de admin — reintentando con --user…")
                result = subprocess.run(
                    [self._get_python(), "-m", "pip"] + args + ["--user"],
                    capture_output=True, text=True,
                )
        for linea in (result.stdout + result.stderr).strip().splitlines()[-6:]:
            self._emit(tipo="log", texto=linea)
        if result.returncode == 0:
            self._emit(tipo="log", texto="OK")
        return result.returncode == 0

    def _descargar_modelo_whisper(self, modelo: str, mb) -> bool:
        # Guardar el modelo en <eclipse_dir>/modelos/ para que hermes_voice.py lo encuentre
        eclipse = getattr(self, "_eclipse_dir", _BASE_DIR)
        modelos_dir = eclipse / "modelos"
        modelos_dir.mkdir(exist_ok=True)
        self._emit(tipo="log",
                    texto=f"Descargando modelo Whisper {modelo} ({mb} MB)…")
        self._emit(tipo="log", texto=f"Destino: {modelos_dir}")
        try:
            result = subprocess.run(
                [self._get_python(), "-c",
                 f"import whisper; whisper.load_model('{modelo}', "
                 f"download_root=r'{modelos_dir}'); print('OK')"],
                capture_output=True, text=True, timeout=600,
            )
            for linea in (result.stdout + result.stderr).strip().splitlines()[-5:]:
                self._emit(tipo="log", texto=linea)
            return result.returncode == 0
        except subprocess.TimeoutExpired:
            self._emit(tipo="log", texto="Timeout (>10 min) descargando modelo")
            return False

    def _descargar_release_github(self, asset_name: str, destino: Path,
                                    mb_est) -> "bool | str":
        """
        Descarga un asset del último release del repo privado eclipse-t.
        Usa el token de hefestos_key_validator._GITHUB_TOKEN.
        Salta si el archivo ya existe y tiene tamaño razonable (> 1 MB).
        """
        import json as _json

        # ── 1. Verificar si ya existe ────────────────────────────────────────
        if destino.exists() and destino.stat().st_size > 1_048_576:
            self._emit(tipo="log",
                        texto=f"{asset_name} ya presente ({destino.stat().st_size // (1024*1024)} MB) — omitiendo descarga")
            return True  # Mostrar ✓ verde, no – gris

        # ── 2. Token (eclipse_t — acceso a repo privado) ─────────────────────
        token = _cargar_eclipse_token()
        if not token:
            self._emit(tipo="log",
                        texto=f"WARN: sin token eclipse_t — {asset_name} no descargado automáticamente")
            self._emit(tipo="log",
                        texto=f"  Copie {asset_name} manualmente a: {destino.parent}")
            return "skip"

        # ── 3. Obtener info del último release ───────────────────────────────
        api_url = f"https://api.github.com/repos/{_ECLIPSE_REPO}/releases/latest"
        headers_api = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "HEFESTOS-installer/2.0",
        }
        self._emit(tipo="log", texto=f"Consultando releases de {_ECLIPSE_REPO}…")
        try:
            req = urllib.request.Request(api_url, headers=headers_api)
            with urllib.request.urlopen(req, timeout=30) as r:
                release = _json.loads(r.read())
        except Exception as exc:
            self._emit(tipo="log", texto=f"Error accediendo al release: {exc}")
            return False

        tag = release.get("tag_name", "desconocida")
        self._emit(tipo="log", texto=f"Release encontrado: {tag}")

        # ── 4. Localizar asset ───────────────────────────────────────────────
        asset_info = None
        for a in release.get("assets", []):
            if a["name"] == asset_name:
                asset_info = a
                break

        if not asset_info:
            nombres = [a["name"] for a in release.get("assets", [])]
            self._emit(tipo="log",
                        texto=f"{asset_name} no encontrado en release {tag}")
            self._emit(tipo="log",
                        texto=f"  Assets disponibles: {nombres}")
            return False

        total = asset_info.get("size", 0)
        total_mb = total / (1024 * 1024)
        self._emit(tipo="log",
                    texto=f"Descargando {asset_name}  ({total_mb:.0f} MB)…")
        self._emit(tipo="log", texto=f"  Destino: {destino}")

        # ── 5. Descargar en streaming con progreso cada ~50 MB ───────────────
        headers_dl = {
            "Authorization": f"token {token}",
            "Accept": "application/octet-stream",
            "User-Agent": "HEFESTOS-installer/2.0",
        }
        CHUNK      = 1024 * 1024          # 1 MB por lectura
        LOG_CADA   = 50 * 1024 * 1024     # log cada 50 MB
        siguiente_log = LOG_CADA

        try:
            destino.parent.mkdir(parents=True, exist_ok=True)
            req_dl = urllib.request.Request(asset_info["url"], headers=headers_dl)
            with urllib.request.urlopen(req_dl, timeout=600) as r, \
                 open(destino, "wb") as fh:
                descargado = 0
                while True:
                    chunk = r.read(CHUNK)
                    if not chunk:
                        break
                    fh.write(chunk)
                    descargado += len(chunk)
                    if descargado >= siguiente_log:
                        pct = int(descargado / total * 100) if total else 0
                        mb_done = descargado / (1024 * 1024)
                        self._emit(tipo="log",
                                    texto=f"  {mb_done:.0f} / {total_mb:.0f} MB  ({pct}%)")
                        siguiente_log += LOG_CADA

            final_mb = destino.stat().st_size / (1024 * 1024)
            self._emit(tipo="log",
                        texto=f"  ✓ {asset_name} descargado — {final_mb:.1f} MB")
            return True

        except Exception as exc:
            self._emit(tipo="log", texto=f"Error descargando {asset_name}: {exc}")
            try:
                destino.unlink(missing_ok=True)
            except Exception:
                pass
            return False

    def _descargar_archivo(self, url: str, destino: Path, nombre: str) -> bool:
        """Descarga en streaming para soportar archivos grandes sin timeout de socket."""
        CHUNK    = 1024 * 1024      # 1 MB por lectura
        LOG_CADA = 30 * 1024 * 1024 # log cada 30 MB
        try:
            destino.parent.mkdir(parents=True, exist_ok=True)
            req = urllib.request.Request(url, headers={"User-Agent": "HEFESTOS-installer/2.0"})
            with urllib.request.urlopen(req, timeout=60) as r:
                total = int(r.headers.get("Content-Length", 0))
                total_mb = total / (1024 * 1024) if total else 0
                if total_mb > 1:
                    self._emit(tipo="log",
                                texto=f"Descargando {nombre} ({total_mb:.0f} MB)…")
                descargado  = 0
                siguiente_log = LOG_CADA
                with open(destino, "wb") as fh:
                    while True:
                        chunk = r.read(CHUNK)
                        if not chunk:
                            break
                        fh.write(chunk)
                        descargado += len(chunk)
                        if total and descargado >= siguiente_log:
                            pct = int(descargado / total * 100)
                            self._emit(tipo="log",
                                        texto=f"  {descargado//(1024*1024)} / {total_mb:.0f} MB  ({pct}%)")
                            siguiente_log += LOG_CADA
            final_mb = destino.stat().st_size / (1024 * 1024)
            self._emit(tipo="log",
                        texto=f"✓ {nombre} descargado ({final_mb:.1f} MB)")
            return True
        except Exception as exc:
            self._emit(tipo="log", texto=f"Error descargando {nombre}: {exc}")
            try:
                destino.unlink(missing_ok=True)
            except Exception:
                pass
            return False

    def _verificar_app(self, app: str) -> bool:
        encontrado = bool(shutil.which(app))
        if not encontrado:
            for p in [
                Path(r"C:\Program Files\Mozilla Firefox\firefox.exe"),
                Path(r"C:\Program Files (x86)\Mozilla Firefox\firefox.exe"),
            ]:
                if p.exists():
                    encontrado = True
                    break

        if encontrado:
            self._emit(tipo="log", texto=f"{app}: encontrado")
            return True

        # Intentar instalar automáticamente con winget (Windows 10/11)
        self._emit(tipo="log",
                    texto=f"{app}: no encontrado — intentando instalar con winget…")
        winget = shutil.which("winget")
        if winget:
            try:
                result = subprocess.run(
                    [winget, "install", "--id", "Mozilla.Firefox",
                     "--silent", "--accept-package-agreements",
                     "--accept-source-agreements", "--disable-interactivity"],
                    capture_output=True, text=True, timeout=300,
                )
                salida = (result.stdout + result.stderr).lower()
                for linea in (result.stdout + result.stderr).strip().splitlines()[-5:]:
                    self._emit(tipo="log", texto=linea)
                if result.returncode == 0 or "already installed" in salida:
                    self._emit(tipo="log", texto="Firefox instalado via winget")
                else:
                    self._emit(tipo="log",
                                texto="winget no pudo instalar Firefox — instálelo manualmente desde mozilla.org")
            except subprocess.TimeoutExpired:
                self._emit(tipo="log", texto="Timeout instalando Firefox — continúe manualmente")
            except Exception as exc:
                self._emit(tipo="log", texto=f"winget error: {exc}")
        else:
            self._emit(tipo="log",
                        texto="winget no disponible — instale Firefox manualmente desde mozilla.org")
        return True  # No bloquear instalación aunque Firefox falte

    def _instalar_geckodriver(self) -> bool:
        VERSION = "v0.35.0"
        url = (
            f"https://github.com/mozilla/geckodriver/releases/download/"
            f"{VERSION}/geckodriver-{VERSION}-win64.zip"
        )
        self._emit(tipo="log", texto=f"Descargando geckodriver {VERSION}…")
        try:
            with urllib.request.urlopen(url, timeout=90) as r:
                data = r.read()
            with tempfile.TemporaryDirectory() as tmp:
                zp = Path(tmp) / "gd.zip"
                zp.write_bytes(data)
                with zipfile.ZipFile(zp) as zf:
                    zf.extractall(tmp)
                exe_src = Path(tmp) / "geckodriver.exe"
                if not exe_src.exists():
                    self._emit(tipo="log", texto="geckodriver.exe no encontrado en ZIP")
                    return False
                dest = self._eclipse_dir / "geckodriver.exe"  # type: ignore
                shutil.copy2(str(exe_src), str(dest))
            self._emit(tipo="log", texto=f"geckodriver instalado en {dest.name}")
            return True
        except Exception as exc:
            self._emit(tipo="log", texto=f"Error geckodriver: {exc}")
            return False

    def _correr_script(self, script_rel: str) -> bool:
        script = self._eclipse_dir / script_rel  # type: ignore
        if not script.exists():
            self._emit(tipo="log", texto=f"Script no encontrado: {script_rel}")
            return False
        self._emit(tipo="log", texto=f"Ejecutando {script_rel}…")
        result = subprocess.run(
            [self._get_python(), str(script)],
            capture_output=True, text=True,
            cwd=str(self._eclipse_dir), timeout=120,
        )
        for linea in (result.stdout + result.stderr).strip().splitlines()[-8:]:
            self._emit(tipo="log", texto=linea)
        return result.returncode == 0

    def _test_arranque(self) -> bool:
        for nombre in ("eclipse_t_v3.py", "eclipse_t_v2.py"):
            exe = self._eclipse_dir / nombre  # type: ignore
            if exe.exists():
                self._emit(tipo="log", texto=f"Verificando sintaxis de {nombre}…")
                result = subprocess.run(
                    [self._get_python(), "-m", "py_compile", str(exe)],
                    capture_output=True, text=True, timeout=20,
                )
                if result.returncode == 0:
                    self._emit(tipo="log", texto="Sintaxis OK — ECLIPSE-T listo")
                    return True
                self._emit(tipo="log", texto=result.stderr[:300])
                return False
        self._emit(tipo="log", texto="eclipse_t_v3.py no encontrado")
        return False

    # ── Startup: chequeo de versión OLYMPUS ──────────────────────────────────

    def _chequeo_startup(self):
        """
        Corre en background al inicio.
        1. Verifica versión HEFESTOS contra manifest.json de OLYMPUS.
        2. Si hay nueva versión → muestra banner opcional (no bloquea).
        Timeout 4 s. Silencioso en caso de error de red.
        """
        def _run():
            try:
                url = f"{OLYMPUS_RAW}/manifest.json"
                req = urllib.request.Request(
                    url, headers={"User-Agent": f"HEFESTOS/{_HEFESTOS_VERSION}"})
                with urllib.request.urlopen(req, timeout=4) as r:
                    manifest = json.loads(r.read())
                v_remota = (manifest.get("versiones", {})
                                    .get("hefestos", {})
                                    .get("version", ""))
                if v_remota and v_remota != _HEFESTOS_VERSION:
                    self.root.after(0, lambda v=v_remota: self._banner_actualizacion(v))
                elif hasattr(self, "_lbl_version_ok"):
                    self.root.after(0, lambda: self._lbl_version_ok.config(
                        text=f"HEFESTOS v{_HEFESTOS_VERSION}  ✓ actualizado", fg=GREEN))
            except Exception:
                pass  # silencioso — red inestable, rural-first
        threading.Thread(target=_run, daemon=True).start()

    def _banner_actualizacion(self, version_nueva: str):
        """Dialog no-modal que avisa de una nueva versión disponible."""
        dlg = tk.Toplevel(self.root)
        dlg.title("HEFESTOS — Actualización disponible")
        dlg.configure(bg=BG)
        dlg.resizable(False, False)
        dlg.protocol("WM_DELETE_WINDOW", dlg.destroy)

        # Centrar sobre ventana principal
        self.root.update_idletasks()
        rx, ry = self.root.winfo_x(), self.root.winfo_y()
        rw, rh = self.root.winfo_width(), self.root.winfo_height()
        dlg.update_idletasks()
        dw, dh = 420, 220
        dlg.geometry(f"{dw}x{dh}+{rx + (rw - dw)//2}+{ry + (rh - dh)//2}")

        tk.Label(dlg, text="Nueva versión disponible",
                 font=("Georgia", 13, "bold"), fg=GOLD, bg=BG).pack(pady=(18, 4))
        tk.Label(dlg,
                 text=f"Versión actual:    v{_HEFESTOS_VERSION}\n"
                      f"Versión nueva:     v{version_nueva}",
                 font=("Courier", 10), fg=TEXT, bg=BG, justify="center").pack(pady=(0, 6))
        tk.Label(dlg,
                 text="La actualización se descargará al mismo directorio.\n"
                      "Cierre HEFESTOS y use el nuevo archivo cuando termine.",
                 font=("Georgia", 8), fg=DIM, bg=BG, justify="center").pack(pady=(0, 14))

        btns = tk.Frame(dlg, bg=BG)
        btns.pack()

        def _descargar():
            btn_dl.config(state="disabled", text="Descargando…")
            dlg.update()
            dest_dir = (Path(sys.executable).parent
                        if getattr(sys, "frozen", False) else _BASE_DIR)
            destino  = dest_dir / f"HEFESTOS_v{version_nueva}.exe"

            def _hilo():
                ok = self._descargar_release_github("HEFESTOS.exe", destino, 25)
                if ok is True:
                    self.root.after(0, lambda: messagebox.showinfo(
                        "Descarga completa",
                        f"HEFESTOS v{version_nueva} descargado en:\n{destino}\n\n"
                        "Cierre esta ventana y use el nuevo ejecutable.",
                        parent=dlg))
                else:
                    self.root.after(0, lambda: messagebox.showwarning(
                        "Error de descarga",
                        "No se pudo descargar la actualización automáticamente.\n"
                        "Descárguela manualmente desde github.com/Faerigan/eclipse-t",
                        parent=dlg))
                self.root.after(0, dlg.destroy)

            threading.Thread(target=_hilo, daemon=True).start()

        btn_dl = tk.Button(btns, text="  Descargar ahora  ↓  ",
                           font=("Georgia", 10, "bold"),
                           bg=ACCENT, fg="white", relief="flat", padx=12, pady=6,
                           activebackground="#A87018", command=_descargar)
        btn_dl.pack(side="left", padx=(0, 10))

        tk.Button(btns, text="Luego",
                  font=("Georgia", 10), bg=DARK, fg=TEXT,
                  relief="flat", padx=14, pady=6,
                  command=dlg.destroy).pack(side="left")

        if hasattr(self, "_lbl_version_ok"):
            self._lbl_version_ok.config(
                text=f"HEFESTOS v{_HEFESTOS_VERSION}  ⬆ v{version_nueva} disponible",
                fg=ACCENT)

    # ── Pantalla 5: Final ────────────────────────────────────────────────────

    def _construir_final(self):
        fr = self._f_final

        tk.Frame(fr, bg=BG, height=16).pack()

        cv_logo = tk.Canvas(fr, width=140, height=140, bg=ANIM_BG,
                             highlightthickness=2, highlightbackground=GOLD)
        cv_logo.pack(pady=(0, 4))
        try:
            from PIL import Image, ImageTk
            _img = Image.open(resource_path(os.path.join("Resources", "HEFESTOS.png")))
            _img = _img.resize((136, 136), Image.LANCZOS)
            self._logo_final = ImageTk.PhotoImage(_img)
            cv_logo.create_image(70, 70, image=self._logo_final, anchor="center")
        except Exception:
            dibujar_logo(cv_logo, 70, 70, s=0.72)

        tk.Label(fr, text="Instalación completada",
                 font=("Georgia", 17, "bold"), fg=GREEN, bg=BG).pack(pady=(14, 4))

        tk.Label(fr,
                 text="Todos los componentes están instalados.\n"
                      "ECLIPSE-T está listo para su uso.",
                 font=("Georgia", 10), fg=TEXT, bg=BG, justify="center",
                 ).pack(pady=(0, 16))

        self._btn_abrir = tk.Button(fr, text="  Abrir ECLIPSE-T  ▶  ",
                  font=("Georgia", 13, "bold"),
                  bg=ACCENT, fg="white", relief="flat", padx=18, pady=9,
                  state="disabled",
                  activebackground="#A87018",
                  command=self._abrir_eclipse)
        self._btn_abrir.pack(pady=(0, 8))

        # Aviso Firefox / HELIOS
        aviso = tk.Frame(fr, bg=BG2, relief="groove", bd=1)
        aviso.pack(fill="x", padx=50, pady=(4, 2))
        tk.Label(aviso,
                 text="⚠  HELIOS requiere Mozilla Firefox instalado",
                 font=("Georgia", 9, "bold"), fg=RED, bg=BG2).pack(anchor="w", padx=8, pady=(6, 2))
        tk.Label(aviso,
                 text="Instale Firefox antes de usar HELIOS u otros componentes\n"
                      "del ecosistema OLYMPUS que accedan a laboratorio.",
                 font=("Georgia", 8), fg=DIM, bg=BG2, justify="left").pack(anchor="w", padx=8)
        tk.Button(aviso, text="Descargar Firefox →",
                  font=("Georgia", 8), bg="#0060DF", fg="white",
                  relief="flat", padx=8, pady=3,
                  command=lambda: __import__("webbrowser").open(
                      "https://www.mozilla.org/firefox/")).pack(anchor="w", padx=8, pady=(4, 6))

        tk.Button(fr, text="Cerrar",
                  font=("Georgia", 10), bg=DARK, fg=TEXT,
                  relief="flat", padx=16, pady=6,
                  command=self.root.destroy).pack(pady=(8, 0))

    def _mostrar_final(self):
        self._mostrar(self._f_final)
        self._btn_abrir.configure(state="normal")

    def _exigir_tc(self):
        _DialogoLicencia(
            self.root,
            on_acepto=lambda: self._btn_abrir.configure(state="normal"),
            on_rechazo=lambda: os._exit(0),
        )

    def _abrir_eclipse(self):
        if not self._eclipse_dir:
            return
        # Intentar ejecutable compilado primero
        exe_compilado = self._eclipse_dir / "ECLIPSE-T.exe"
        if exe_compilado.exists():
            subprocess.Popen([str(exe_compilado)], cwd=str(self._eclipse_dir))
            self.root.destroy()
            return
        # Fallback: fuente .py (uso en desarrollo)
        for nombre in ("eclipse_t_v3.py", "eclipse_t_v2.py"):
            src = self._eclipse_dir / nombre
            if src.exists():
                subprocess.Popen(
                    [self._get_python(), str(src)],
                    cwd=str(self._eclipse_dir),
                )
                self.root.destroy()
                return
        messagebox.showerror(
            "No encontrado",
            f"No se encontró ECLIPSE-T.exe en {self._eclipse_dir}",
        )

    # ── Run ──────────────────────────────────────────────────────────────────

    def _cerrar(self):
        """Cierre limpio: destruye ventana y mata el proceso completo."""
        try:
            self.root.destroy()
        except Exception:
            pass
        import os as _os
        _os._exit(0)

    def run(self):
        self.root.mainloop()


# ── Entry point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import multiprocessing
    multiprocessing.freeze_support()
    HefestosApp().run()
