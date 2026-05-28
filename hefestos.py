"""
hefestos.py — Instalador ECLIPSE-T v3.0
HEFESTOS · Ecosistema OLYMPUS · CESFAM Cerrillos de Tamaya

Compila como: pyinstaller --onefile --windowed --name HEFESTOS hefestos.py
"""

import json
import math
import platform
import queue
import random
import shutil
import subprocess
import sys
import tempfile
import threading
import urllib.request
import zipfile
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

# ── Fernet (cifrado credenciales IRIS) ───────────────────────────────────────
try:
    from cryptography.fernet import Fernet
    _CRYPTO_OK = True
except ImportError:
    _CRYPTO_OK = False

# ── Rutas ────────────────────────────────────────────────────────────────────

_BASE_DIR = Path(__file__).parent          # D:\HEFESTOS
sys.path.insert(0, str(_BASE_DIR))

OLYMPUS_RAW = "https://raw.githubusercontent.com/Faerigan/OLYMPUS/main"

# ── Colores ──────────────────────────────────────────────────────────────────

BG    = "#1A1A2E"
DARK  = "#0F0F1E"
GOLD  = "#F5A623"
LIGHT = "#E8E8E8"
GREEN = "#4CAF50"
RED   = "#F44336"
GRAY  = "#555577"
ANVIL = "#607D8B"
METAL = "#90A4AE"
MANGO = "#5D4037"

# ── Defaults para clave maestra ──────────────────────────────────────────────

_DEFAULTS_MAESTRA = {
    "nombre_centro":      "CESFAM Cerrillos de Tamaya",
    "codigo_centro":      "",
    "comuna":             "Ovalle",
    "servicio_salud":     "Servicio de Salud Coquimbo",
    "iris_url":           "http://207.248.201.73:8080/irisconsultorio/",
    "iris_usuario":       "",
    "iris_password":      "",
    "iris_habilitado":    True,
    "nombre_profesional": "Dr. Nicolás Vargas",
    "profesion":          "Médico Familiar",
    "registro":           "",
    "logo_principal":     "",
    "logo_secundario":    "",
}


# ── Canvas estático: logo HEFESTOS ───────────────────────────────────────────

def dibujar_logo(canvas: tk.Canvas, cx: int, cy: int, s: float = 1.0):
    """Yunque + martillo + rayos solares dorados (estático)."""
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
                             fill=METAL, outline=LIGHT, width=1)
    canvas.create_rectangle(
        cx - int(5*s), cy - int(62*s), cx + int(5*s), cy - int(10*s),
        fill=DARK, outline=GRAY,
    )
    mhw, mhh = int(36*s), int(18*s)
    mhx = cx - int(10*s)
    mhy = cy - int(62*s) - mhh
    canvas.create_rectangle(mhx, mhy, mhx + mhw, mhy + mhh,
                             fill=METAL, outline=LIGHT, width=1)


# ── HefestosAnimacion ────────────────────────────────────────────────────────

class HefestosAnimacion(tk.Canvas):
    """
    Animación de martillo golpeando yunque con chispas doradas.
    Ciclo: 8 bajada (ease-in) + 4 impacto+chispas + 10 subida (ease-out) + 6 pausa.
    24 fps → after(42, ...).
    """
    _BAJADA  = 8
    _IMPACTO = 4
    _SUBIDA  = 10
    _PAUSA   = 6
    _TOTAL   = 28   # sum of above

    # Angulo del martillo: -40° (arriba) → +5° (impacto)
    _ANG_ALTO = -40
    _ANG_BAJO =   5

    def __init__(self, parent, **kw):
        super().__init__(parent, width=160, height=160,
                         bg=BG, highlightthickness=0, **kw)
        self._frame    = 0
        self._running  = False
        self._after_id = None
        self._chispas: list[list] = []   # [x, y, ang_rad, lng, frames_left]

    # ── Control ──────────────────────────────────────────────────────────────

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

    # ── Loop ─────────────────────────────────────────────────────────────────

    def _tick(self):
        if not self._running:
            return
        self._renderizar()
        self._frame    = (self._frame + 1) % self._TOTAL
        self._after_id = self.after(42, self._tick)

    def _angulo(self) -> float:
        """Retorna ángulo del martillo en grados según frame actual."""
        f = self._frame
        rango = self._ANG_BAJO - self._ANG_ALTO   # 45°

        if f < self._BAJADA:
            t = f / self._BAJADA
            return self._ANG_ALTO + (t * t) * rango          # ease-in

        if f < self._BAJADA + self._IMPACTO:
            return self._ANG_BAJO                             # impacto

        if f < self._BAJADA + self._IMPACTO + self._SUBIDA:
            fi = f - self._BAJADA - self._IMPACTO
            t  = fi / self._SUBIDA
            return self._ANG_BAJO - (1 - (1-t)**2) * rango   # ease-out

        return self._ANG_ALTO                                 # pausa

    def _renderizar(self):
        self.delete("all")
        cx, cy_yuq = 80, 115   # centro X, tope del yunque Y

        # ── Yunque ───────────────────────────────────────────────────────────
        self._yunque(cx, cy_yuq)

        # ── Punto de impacto ─────────────────────────────────────────────────
        impact_x, impact_y = cx, cy_yuq - 10

        # ── Generar chispas al primer frame de impacto ───────────────────────
        if self._frame == self._BAJADA:
            n = random.randint(6, 8)
            for _ in range(n):
                ang = math.radians(random.uniform(20, 160))
                lng = random.uniform(8, 18)
                life = random.randint(3, 4)
                self._chispas.append([impact_x, impact_y, ang, lng, life])

        # ── Dibujar chispas activas ──────────────────────────────────────────
        vivas = []
        for x, y, ang, lng, life in self._chispas:
            if life > 0:
                x2 = x + math.cos(ang) * lng
                y2 = y - math.sin(ang) * lng   # arriba en canvas
                self.create_line(x, y, x2, y2, fill=GOLD,
                                 width=2, capstyle="round")
                vivas.append([x, y, ang, lng, life - 1])
        self._chispas = vivas

        # ── Martillo ─────────────────────────────────────────────────────────
        self._martillo(cx, ang_deg=self._angulo(), impact_y=impact_y)

    def _yunque(self, cx: int, cy: int):
        # Trapecio base
        self.create_polygon(
            cx-26, cy,   cx+26, cy,
            cx+32, cy+22, cx-32, cy+22,
            fill=ANVIL, outline=METAL, width=1,
        )
        # Cuello
        self.create_rectangle(cx-12, cy-14, cx+12, cy, fill=ANVIL, outline=METAL)
        # Cabeza plana (top)
        self.create_rectangle(cx-36, cy-24, cx+36, cy-14,
                              fill=METAL, outline=LIGHT, width=1)

    def _martillo(self, cx: int, ang_deg: float, impact_y: int):
        pivot_x = cx
        pivot_y = 30       # punto de pivote (agarre)
        mango   = 48       # largo del mango
        ang     = math.radians(ang_deg)

        # Extremo inferior del mango (donde va la cabeza)
        tip_x = pivot_x + math.sin(ang) * mango
        tip_y = pivot_y + math.cos(ang) * mango

        # Mango
        self.create_line(pivot_x, pivot_y, tip_x, tip_y,
                         fill=MANGO, width=9, capstyle="round")

        # Cabeza del martillo (perpendicular al mango en el extremo)
        perp  = ang + math.pi / 2
        half  = 16   # semiancho de la cabeza
        depth = 12   # profundidad de la cabeza

        # 4 vértices del rectángulo de la cabeza
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
        coords = sum(zip(vx, vy), ())
        self.create_polygon(*coords, fill=METAL, outline=LIGHT, width=1)


# ── App principal ────────────────────────────────────────────────────────────

class HefestosApp:

    _ECLIPSE_CANDIDATOS = [
        Path("D:/ECLIPSE"),
        Path("E:/ECLIPSE"),
        Path("C:/ECLIPSE"),
    ]

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("HEFESTOS — Instalador ECLIPSE-T v3.0")
        self.root.configure(bg=BG)
        self.root.resizable(False, False)
        self.root.geometry("620x740")

        self._cola:         queue.Queue = queue.Queue()
        self._eclipse_dir:  Path | None = None
        self._labels_pasos: list[dict]  = []
        self._es_maestra:   bool        = False

        self._manifest = self._cargar_manifest()
        self._total_pasos = sum(
            len(g["pasos"]) for g in self._manifest["grupos"]
        )
        self._pasos_completados = 0

        self._var_dir        = tk.StringVar()
        self._var_clave      = tk.StringVar()

        # Config vars
        self._cfg: dict[str, tk.Variable] = {}

        self._construir_ui()
        self._detectar_eclipse()

    # ── Manifiesto ───────────────────────────────────────────────────────────

    def _cargar_manifest(self) -> dict:
        path = _BASE_DIR / "install_manifest.json"
        with open(path, encoding="utf-8") as f:
            return json.load(f)

    # ── Construcción UI ──────────────────────────────────────────────────────

    def _construir_ui(self):
        self._f_inicio      = tk.Frame(self.root, bg=BG)
        self._f_config      = tk.Frame(self.root, bg=BG)
        self._f_instalacion = tk.Frame(self.root, bg=BG)
        self._f_final       = tk.Frame(self.root, bg=BG)

        self._construir_inicio()
        self._construir_config()
        self._construir_instalacion()
        self._construir_final()
        self._mostrar(self._f_inicio)

    def _mostrar(self, frame: tk.Frame):
        for f in (self._f_inicio, self._f_config,
                  self._f_instalacion, self._f_final):
            f.pack_forget()
        frame.pack(fill="both", expand=True)

    # ── Pantalla 1: Inicio ───────────────────────────────────────────────────

    def _construir_inicio(self):
        fr = self._f_inicio

        cv = tk.Canvas(fr, width=200, height=200, bg=BG, highlightthickness=0)
        cv.pack(pady=(24, 0))
        dibujar_logo(cv, 100, 100, s=1.0)

        tk.Label(fr, text="HEFESTOS", font=("Helvetica", 24, "bold"),
                 fg=GOLD, bg=BG).pack(pady=(6, 0))
        tk.Label(fr, text="Instalador Ecosistema OLYMPUS  ·  v1.0",
                 font=("Helvetica", 10), fg=LIGHT, bg=BG).pack()
        tk.Label(fr, text="CESFAM Cerrillos de Tamaya",
                 font=("Helvetica", 9), fg=GRAY, bg=BG).pack(pady=(2, 16))

        tk.Frame(fr, height=1, bg=GOLD).pack(fill="x", padx=44, pady=(0, 16))

        tk.Label(fr, text="Directorio ECLIPSE-T:", font=("Helvetica", 10, "bold"),
                 fg=LIGHT, bg=BG).pack(anchor="w", padx=48)
        row_dir = tk.Frame(fr, bg=BG)
        row_dir.pack(fill="x", padx=48, pady=(4, 12))
        tk.Entry(row_dir, textvariable=self._var_dir, bg=DARK, fg=LIGHT,
                 insertbackground=GOLD, relief="flat",
                 font=("Courier", 10), width=36).pack(side="left",
                                                       ipady=5, padx=(0, 6))
        tk.Button(row_dir, text="…", bg=GRAY, fg=LIGHT, relief="flat",
                  command=self._seleccionar_dir).pack(side="left")

        tk.Label(fr, text="Codigo de instalacion:", font=("Helvetica", 10, "bold"),
                 fg=LIGHT, bg=BG).pack(anchor="w", padx=48)
        entry = tk.Entry(fr, textvariable=self._var_clave, show="•",
                         bg=DARK, fg=LIGHT, insertbackground=GOLD,
                         relief="flat", font=("Courier", 13), width=28)
        entry.pack(ipady=6, pady=(4, 4))
        entry.bind("<Return>", lambda _: self._comenzar())

        self._lbl_msg = tk.Label(fr, text="", font=("Helvetica", 9),
                                  fg=RED, bg=BG, wraplength=480, justify="center")
        self._lbl_msg.pack(pady=(2, 0))

        tk.Button(fr, text="  INSTALAR  ▶  ",
                  font=("Helvetica", 13, "bold"),
                  bg=GOLD, fg=DARK, relief="flat", padx=18, pady=9,
                  activebackground="#D4891A",
                  command=self._comenzar).pack(pady=(16, 6))

        tk.Label(fr, text="Tiempo estimado con buena conexion: ~20 min",
                 font=("Helvetica", 8), fg=GRAY, bg=BG).pack()

    def _detectar_eclipse(self):
        for p in self._ECLIPSE_CANDIDATOS:
            if p.exists() and (
                (p / "eclipse_t_v3.py").exists() or
                (p / "eclipse_t_v2.py").exists()
            ):
                self._var_dir.set(str(p))
                return

    def _seleccionar_dir(self):
        d = filedialog.askdirectory(title="Seleccionar directorio ECLIPSE-T",
                                     initialdir="D:/")
        if d:
            self._var_dir.set(d)

    def _comenzar(self):
        eclipse_dir = Path(self._var_dir.get().strip())
        if not eclipse_dir.exists():
            self._lbl_msg.config(
                text="Directorio no encontrado. Seleccione la carpeta ECLIPSE.", fg=RED)
            return
        self._eclipse_dir = eclipse_dir

        clave = self._var_clave.get().strip()
        if not clave:
            self._lbl_msg.config(text="Ingrese un codigo de instalacion.", fg=RED)
            return

        self._lbl_msg.config(text="Verificando codigo…", fg=GOLD)
        self.root.update()

        valida, estado = self._validar_clave(clave)
        if not valida:
            try:
                from hefestos_key_validator import MENSAJES  # type: ignore
                self._lbl_msg.config(text=MENSAJES.get(estado, estado), fg=RED)
            except ImportError:
                self._lbl_msg.config(text=f"Clave invalida ({estado})", fg=RED)
            return

        if estado == "sin_red":
            if not messagebox.askyesno(
                "Sin conexion a internet",
                "No se pudo verificar el codigo (sin internet).\n"
                "La instalacion continuara, pero el codigo quedara\n"
                "pendiente de verificacion posterior.\n\n"
                "¿Continuar de todas formas?",
            ):
                self._lbl_msg.config(text="", fg=RED)
                return

        self._es_maestra = (estado == "maestra")
        self._lbl_msg.config(text="")

        # Pasar a config antes de instalar
        if self._es_maestra:
            self._aplicar_defaults_maestra()
        self._mostrar(self._f_config)

    def _validar_clave(self, clave: str) -> tuple[bool, str]:
        try:
            from hefestos_key_validator import validar_clave_instalacion  # type: ignore
            return validar_clave_instalacion(clave, equipo_id=platform.node())
        except ImportError:
            return True, "sin_red"

    # ── Pantalla 2: Configuración del centro ─────────────────────────────────

    def _mk_var(self, key: str, default="") -> tk.StringVar:
        v = tk.StringVar(value=str(default))
        self._cfg[key] = v
        return v

    def _construir_config(self):
        fr = self._f_config

        # Header
        tk.Label(fr, text="Configurar Centro de Salud",
                 font=("Helvetica", 15, "bold"), fg=GOLD, bg=BG).pack(pady=(20, 2))
        tk.Label(fr,
                 text="Esta informacion se usara en todos los documentos generados por ECLIPSE-T",
                 font=("Helvetica", 9), fg=LIGHT, bg=BG).pack()
        tk.Frame(fr, height=1, bg=GOLD).pack(fill="x", padx=30, pady=(10, 6))

        # Scrollable body
        canvas_wrap = tk.Canvas(fr, bg=BG, highlightthickness=0)
        sb = ttk.Scrollbar(fr, orient="vertical", command=canvas_wrap.yview)
        canvas_wrap.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        canvas_wrap.pack(fill="both", expand=True, padx=(12, 0))

        body = tk.Frame(canvas_wrap, bg=BG)
        body_id = canvas_wrap.create_window((0, 0), window=body, anchor="nw")

        def _on_resize(e):
            canvas_wrap.itemconfig(body_id, width=e.width)
        canvas_wrap.bind("<Configure>", _on_resize)
        body.bind("<Configure>",
                  lambda e: canvas_wrap.configure(
                      scrollregion=canvas_wrap.bbox("all")))

        pad = dict(padx=12, pady=3, sticky="w")

        # ── Identidad ────────────────────────────────────────────────────────
        lf1 = tk.LabelFrame(body, text="  Identidad del Centro  ",
                             fg=GOLD, bg=BG, font=("Helvetica", 9, "bold"))
        lf1.pack(fill="x", padx=8, pady=(4, 6))

        self._campo(lf1, "Nombre del centro:", "nombre_centro",
                    "CESFAM Cerrillos de Tamaya", width=38, row=0)
        self._campo(lf1, "Codigo DEIS:", "codigo_centro", "", width=14, row=1, col=0)
        self._campo(lf1, "Comuna:", "comuna", "", width=18, row=1, col=2)
        self._campo(lf1, "Servicio de Salud:", "servicio_salud",
                    "Servicio de Salud Coquimbo", width=30, row=2)

        # ── IRIS ─────────────────────────────────────────────────────────────
        lf2 = tk.LabelFrame(body, text="  Acceso Laboratorio (HELIOS/IRIS)  ",
                             fg=GOLD, bg=BG, font=("Helvetica", 9, "bold"))
        lf2.pack(fill="x", padx=8, pady=4)

        self._campo(lf2, "URL IRIS:", "iris_url",
                    "http://207.248.201.73:8080/irisconsultorio/", width=46, row=0)

        self._cfg["iris_habilitado"] = tk.BooleanVar(value=True)
        tk.Checkbutton(lf2, text="IRIS habilitado",
                       variable=self._cfg["iris_habilitado"],
                       bg=BG, fg=LIGHT, selectcolor=DARK,
                       activebackground=BG).grid(row=0, column=2,
                                                  padx=6, pady=2, sticky="w")

        self._campo(lf2, "Usuario:", "iris_usuario", "", width=20, row=1, col=0)
        self._campo_pass(lf2, "Contrasena:", "iris_password", row=1, col=2)

        if not _CRYPTO_OK:
            tk.Label(lf2,
                     text="⚠ cryptography no instalado — credenciales sin cifrar",
                     fg="#FFD700", bg=BG, font=("Helvetica", 8)).grid(
                         row=2, column=0, columnspan=4, **pad)

        # ── Profesional ──────────────────────────────────────────────────────
        lf3 = tk.LabelFrame(body, text="  Profesional Responsable  ",
                             fg=GOLD, bg=BG, font=("Helvetica", 9, "bold"))
        lf3.pack(fill="x", padx=8, pady=4)

        self._campo(lf3, "Nombre:", "nombre_profesional",
                    "Dr. Nicolas Vargas", width=30, row=0)
        self._campo(lf3, "Profesion:", "profesion",
                    "Medico Familiar", width=20, row=1, col=0)
        self._campo(lf3, "Registro:", "registro", "", width=14, row=1, col=2)

        # ── Logos ────────────────────────────────────────────────────────────
        lf4 = tk.LabelFrame(body, text="  Logos (opcional)  ",
                             fg=GOLD, bg=BG, font=("Helvetica", 9, "bold"))
        lf4.pack(fill="x", padx=8, pady=4)

        self._cfg["logo_principal"]  = tk.StringVar()
        self._cfg["logo_secundario"] = tk.StringVar()

        self._fila_logo(lf4, "Logo principal:",   "logo_principal",  row=0)
        self._fila_logo(lf4, "Logo secundario:", "logo_secundario", row=1)

        # ── Botones ──────────────────────────────────────────────────────────
        btns = tk.Frame(fr, bg=BG)
        btns.pack(pady=(8, 16))
        tk.Button(btns, text="Omitir por ahora",
                  font=("Helvetica", 10), bg=GRAY, fg=LIGHT,
                  relief="flat", padx=14, pady=6,
                  command=self._omitir_config).pack(side="left", padx=(0, 12))
        tk.Button(btns, text="Guardar y continuar  ▶",
                  font=("Helvetica", 11, "bold"),
                  bg=GOLD, fg=DARK, relief="flat", padx=16, pady=7,
                  activebackground="#D4891A",
                  command=self._guardar_config).pack(side="left")

    def _campo(self, parent, label: str, key: str, default: str,
               width: int = 24, row: int = 0, col: int = 0):
        tk.Label(parent, text=label, bg=BG, fg=LIGHT,
                 font=("Helvetica", 9)).grid(row=row, column=col,
                                              padx=(8, 2), pady=3, sticky="w")
        v = self._mk_var(key, default)
        tk.Entry(parent, textvariable=v, bg=DARK, fg=LIGHT,
                 insertbackground=GOLD, relief="flat",
                 font=("Courier", 9), width=width).grid(
                     row=row, column=col+1, padx=(0, 8), pady=3, sticky="w")

    def _campo_pass(self, parent, label: str, key: str,
                    row: int = 0, col: int = 0):
        tk.Label(parent, text=label, bg=BG, fg=LIGHT,
                 font=("Helvetica", 9)).grid(row=row, column=col,
                                              padx=(8, 2), pady=3, sticky="w")
        v = self._mk_var(key, "")
        tk.Entry(parent, textvariable=v, show="•", bg=DARK, fg=LIGHT,
                 insertbackground=GOLD, relief="flat",
                 font=("Courier", 9), width=20).grid(
                     row=row, column=col+1, padx=(0, 8), pady=3, sticky="w")

    def _fila_logo(self, parent, label: str, key: str, row: int):
        tk.Label(parent, text=label, bg=BG, fg=LIGHT,
                 font=("Helvetica", 9)).grid(row=row, column=0,
                                              padx=(8, 2), pady=3, sticky="w")
        entry = tk.Entry(parent, textvariable=self._cfg[key], bg=DARK, fg=LIGHT,
                         insertbackground=GOLD, relief="flat",
                         font=("Courier", 8), width=34)
        entry.grid(row=row, column=1, padx=(0, 4), pady=3, sticky="w")
        tk.Button(parent, text="…", bg=GRAY, fg=LIGHT, relief="flat",
                  command=lambda k=key: self._seleccionar_logo(k)).grid(
                      row=row, column=2, padx=(0, 8), pady=3)

    def _seleccionar_logo(self, key: str):
        path = filedialog.askopenfilename(
            title="Seleccionar imagen",
            filetypes=[("Imagenes", "*.png *.jpg *.jpeg *.bmp"), ("Todos", "*.*")]
        )
        if path:
            self._cfg[key].set(path)

    def _aplicar_defaults_maestra(self):
        """Pre-rellena la config con los valores del CESFAM al usar clave maestra."""
        for key, val in _DEFAULTS_MAESTRA.items():
            if key in self._cfg:
                if isinstance(self._cfg[key], tk.BooleanVar):
                    self._cfg[key].set(bool(val))
                else:
                    self._cfg[key].set(str(val))

    def _omitir_config(self):
        self._iniciar_instalacion()

    def _guardar_config(self):
        if not self._eclipse_dir:
            return

        config = {k: (v.get() if not isinstance(v, tk.BooleanVar) else v.get())
                  for k, v in self._cfg.items()}

        # Generar/cargar clave Fernet y cifrar credenciales IRIS
        key_path = self._eclipse_dir / "data" / ".key"
        if _CRYPTO_OK:
            key_path.parent.mkdir(parents=True, exist_ok=True)
            if key_path.exists():
                fkey = key_path.read_bytes()
            else:
                fkey = Fernet.generate_key()
                key_path.write_bytes(fkey)
            f = Fernet(fkey)
            for campo in ("iris_usuario", "iris_password"):
                raw = config.get(campo, "")
                if raw:
                    config[campo] = f.encrypt(raw.encode()).decode()
                    config[f"_{campo}_cifrado"] = True

        # Copiar logos
        recursos = self._eclipse_dir / "resources"
        recursos.mkdir(exist_ok=True)
        for campo, dest_name in (("logo_principal",  "logo_centro.png"),
                                  ("logo_secundario", "logo_ss.png")):
            src = config.get(campo, "")
            if src and Path(src).exists():
                shutil.copy2(src, recursos / dest_name)
                config[campo] = str(recursos / dest_name)

        dest = self._eclipse_dir / "config_centro.json"
        with open(dest, "w", encoding="utf-8") as f_out:
            json.dump(config, f_out, ensure_ascii=False, indent=2)

        self._iniciar_instalacion()

    # ── Pantalla 3: Instalación ──────────────────────────────────────────────

    def _construir_instalacion(self):
        fr = self._f_instalacion

        # Header compacto
        hdr = tk.Frame(fr, bg=DARK)
        hdr.pack(fill="x")
        tk.Label(hdr, text="HEFESTOS — Instalacion en curso",
                 font=("Helvetica", 12, "bold"), fg=GOLD, bg=DARK).pack(
                     side="left", padx=16, pady=10)

        # Animación centrada
        anim_frame = tk.Frame(fr, bg=BG)
        anim_frame.pack(pady=(8, 4))
        self._animacion = HefestosAnimacion(anim_frame)
        self._animacion.pack()

        # Lista de pasos
        pasos_frame = tk.Frame(fr, bg=BG)
        pasos_frame.pack(fill="x", padx=18, pady=(4, 4))

        for grupo in self._manifest["grupos"]:
            tk.Label(pasos_frame, text=f"  {grupo['nombre']}",
                     font=("Helvetica", 9, "bold"), fg=GOLD, bg=BG,
                     anchor="w").pack(fill="x", pady=(4, 1))
            for paso in grupo["pasos"]:
                fila = tk.Frame(pasos_frame, bg=BG)
                fila.pack(fill="x", padx=14, pady=1)
                ico = tk.Label(fila, text="○", font=("Helvetica", 10),
                               fg=GRAY, bg=BG, width=2)
                ico.pack(side="left")
                lbl = tk.Label(fila, text=paso["desc"],
                               font=("Helvetica", 9), fg=LIGHT, bg=BG, anchor="w")
                lbl.pack(side="left", fill="x")
                self._labels_pasos.append({"id": paso["id"], "ico": ico, "lbl": lbl})

        # Barra de progreso
        pk = tk.Frame(fr, bg=BG)
        pk.pack(fill="x", padx=18, pady=(6, 2))
        self._progress = ttk.Progressbar(pk, mode="determinate",
                                          length=580, maximum=100)
        self._progress.pack(fill="x")

        self._lbl_estado = tk.Label(fr, text="Preparando…",
                                     font=("Helvetica", 9, "italic"),
                                     fg=GOLD, bg=BG)
        self._lbl_estado.pack(anchor="w", padx=20)

        # Log
        log_wrap = tk.Frame(fr, bg=DARK)
        log_wrap.pack(fill="both", expand=True, padx=18, pady=(6, 12))
        self._log = tk.Text(log_wrap, bg=DARK, fg="#AAFFAA",
                             font=("Courier", 8), relief="flat",
                             state="disabled", wrap="word", height=7)
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
                    self._set_paso(msg["id"], "►", GOLD, GOLD)

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
                    self._lbl_estado.config(text="Instalacion completada.")
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

    def _ejecutar_instalacion(self):
        for grupo in self._manifest["grupos"]:
            for paso in grupo["pasos"]:
                self._emit(tipo="estado", texto=f"{paso['desc']}…")
                self._emit(tipo="paso_inicio", id=paso["id"])
                try:
                    ok = self._ejecutar_paso(paso)
                except Exception as exc:
                    self._emit(tipo="log", texto=f"EXCEPCION: {exc}")
                    ok = False
                self._emit(tipo="paso_ok" if ok else "paso_error", id=paso["id"])

        self._emit(tipo="fin")

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
            return self._pip(["install"] + paso["paquetes"])

        if tipo == "whisper_model":
            return self._descargar_modelo_whisper(paso["modelo"], paso.get("mb", "?"))

        if tipo == "descarga":
            url     = f"{OLYMPUS_RAW}/{paso['url']}"
            destino = self._eclipse_dir / paso["destino"]   # type: ignore
            return self._descargar_archivo(url, destino, paso["url"])

        if tipo == "verificar_app":
            return self._verificar_app(paso.get("app", ""))

        if tipo == "geckodriver":
            return self._instalar_geckodriver()

        if tipo == "script":
            return self._correr_script(paso["script"])

        if tipo == "test_arranque":
            return self._test_arranque()

        self._emit(tipo="log", texto=f"Tipo desconocido: {tipo}")
        return False

    # ── Implementaciones ─────────────────────────────────────────────────────

    def _pip(self, args: list[str]) -> bool:
        result = subprocess.run(
            [sys.executable, "-m", "pip"] + args,
            capture_output=True, text=True,
        )
        for linea in (result.stdout + result.stderr).strip().splitlines()[-6:]:
            self._emit(tipo="log", texto=linea)
        if result.returncode == 0:
            self._emit(tipo="log", texto="OK")
        return result.returncode == 0

    def _descargar_modelo_whisper(self, modelo: str, mb) -> bool:
        self._emit(tipo="log",
                    texto=f"Descargando modelo Whisper {modelo} ({mb} MB)…")
        try:
            result = subprocess.run(
                [sys.executable, "-c",
                 f"import whisper; whisper.load_model('{modelo}'); print('OK')"],
                capture_output=True, text=True, timeout=600,
            )
            for linea in (result.stdout + result.stderr).strip().splitlines()[-5:]:
                self._emit(tipo="log", texto=linea)
            return result.returncode == 0
        except subprocess.TimeoutExpired:
            self._emit(tipo="log", texto="Timeout (>10 min) descargando modelo")
            return False

    def _descargar_archivo(self, url: str, destino: Path, nombre: str) -> bool:
        try:
            destino.parent.mkdir(parents=True, exist_ok=True)
            with urllib.request.urlopen(url, timeout=20) as r:
                data = r.read()
            destino.write_bytes(data)
            self._emit(tipo="log",
                        texto=f"{nombre} descargado ({len(data):,} bytes)")
            return True
        except Exception as exc:
            self._emit(tipo="log", texto=f"Error descargando {nombre}: {exc}")
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
        estado = "encontrado" if encontrado else "NO encontrado (HELIOS no disponible)"
        self._emit(tipo="log", texto=f"{app}: {estado}")
        return True

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
                dest = self._eclipse_dir / "geckodriver.exe"   # type: ignore
                shutil.copy2(str(exe_src), str(dest))
            self._emit(tipo="log", texto=f"geckodriver instalado en {dest.name}")
            return True
        except Exception as exc:
            self._emit(tipo="log", texto=f"Error geckodriver: {exc}")
            return False

    def _correr_script(self, script_rel: str) -> bool:
        script = self._eclipse_dir / script_rel   # type: ignore
        if not script.exists():
            self._emit(tipo="log", texto=f"Script no encontrado: {script_rel}")
            return False
        self._emit(tipo="log", texto=f"Ejecutando {script_rel}…")
        result = subprocess.run(
            [sys.executable, str(script)],
            capture_output=True, text=True,
            cwd=str(self._eclipse_dir), timeout=120,
        )
        for linea in (result.stdout + result.stderr).strip().splitlines()[-8:]:
            self._emit(tipo="log", texto=linea)
        return result.returncode == 0

    def _test_arranque(self) -> bool:
        for nombre in ("eclipse_t_v3.py", "eclipse_t_v2.py"):
            exe = self._eclipse_dir / nombre   # type: ignore
            if exe.exists():
                self._emit(tipo="log", texto=f"Verificando sintaxis de {nombre}…")
                result = subprocess.run(
                    [sys.executable, "-m", "py_compile", str(exe)],
                    capture_output=True, text=True, timeout=20,
                )
                if result.returncode == 0:
                    self._emit(tipo="log", texto="Sintaxis OK — ECLIPSE-T listo")
                    return True
                self._emit(tipo="log", texto=result.stderr[:300])
                return False
        self._emit(tipo="log",
                    texto="eclipse_t_v2.py / eclipse_t_v3.py no encontrado")
        return False

    # ── Pantalla 4: Final ────────────────────────────────────────────────────

    def _construir_final(self):
        fr = self._f_final

        tk.Frame(fr, height=40, bg=BG).pack()

        cv = tk.Canvas(fr, width=160, height=160, bg=BG, highlightthickness=0)
        cv.pack()
        dibujar_logo(cv, 80, 80, s=0.8)

        self._lbl_fin_titulo = tk.Label(
            fr, text="Instalacion completada",
            font=("Helvetica", 17, "bold"), fg=GREEN, bg=BG,
        )
        self._lbl_fin_titulo.pack(pady=(16, 6))

        self._lbl_fin_detalle = tk.Label(
            fr,
            text="Todos los componentes estan instalados.\n"
                 "ECLIPSE-T esta listo para su uso.",
            font=("Helvetica", 10), fg=LIGHT, bg=BG, justify="center",
        )
        self._lbl_fin_detalle.pack(pady=(0, 20))

        # Botón principal
        tk.Button(
            fr, text="  Abrir ECLIPSE-T  ▶  ",
            font=("Helvetica", 14, "bold"),
            bg=GOLD, fg=DARK, relief="flat", padx=20, pady=10,
            activebackground="#D4891A",
            command=self._abrir_eclipse,
        ).pack(pady=(0, 10))

        # Separador
        tk.Frame(fr, height=1, bg=GRAY).pack(fill="x", padx=80, pady=(10, 10))

        # Botón compilar EXE
        self._lbl_rebuild = tk.Label(
            fr,
            text="Opcional: compilar ECLIPSE-T.exe (~26 min)",
            font=("Helvetica", 9), fg=GRAY, bg=BG,
        )
        self._lbl_rebuild.pack()

        self._btn_rebuild = tk.Button(
            fr, text="Compilar ECLIPSE-T.exe",
            font=("Helvetica", 10), bg=DARK, fg=GOLD,
            relief="flat", padx=14, pady=5,
            command=self._iniciar_rebuild,
        )
        self._btn_rebuild.pack(pady=(4, 6))

        self._lbl_rebuild_estado = tk.Label(
            fr, text="", font=("Helvetica", 9, "italic"),
            fg=GOLD, bg=BG,
        )
        self._lbl_rebuild_estado.pack()

        tk.Button(
            fr, text="Cerrar",
            font=("Helvetica", 10), bg=GRAY, fg=LIGHT,
            relief="flat", padx=16, pady=6,
            command=self.root.destroy,
        ).pack(pady=(10, 0))

    def _mostrar_final(self):
        self._mostrar(self._f_final)

    def _abrir_eclipse(self):
        if not self._eclipse_dir:
            return
        for nombre in ("eclipse_t_v3.py", "eclipse_t_v2.py"):
            exe = self._eclipse_dir / nombre
            if exe.exists():
                subprocess.Popen(
                    [sys.executable, str(exe)],
                    cwd=str(self._eclipse_dir),
                )
                self.root.destroy()
                return
        messagebox.showerror(
            "No encontrado",
            f"No se encontro eclipse_t_v2.py ni eclipse_t_v3.py\nen {self._eclipse_dir}",
        )

    # ── Rebuild EXE ──────────────────────────────────────────────────────────

    def _iniciar_rebuild(self):
        if not self._eclipse_dir:
            return
        build_py = self._eclipse_dir / "build.py"
        if not build_py.exists():
            messagebox.showerror("Error", f"build.py no encontrado en {self._eclipse_dir}")
            return

        self._btn_rebuild.config(state="disabled", text="Compilando…")
        self._lbl_rebuild_estado.config(
            text="Compilando ECLIPSE-T.exe (~26 min) — no cerrar la ventana", fg=GOLD)

        threading.Thread(
            target=self._correr_rebuild,
            args=(build_py,),
            daemon=True,
        ).start()

    def _correr_rebuild(self, build_py: Path):
        try:
            result = subprocess.run(
                [sys.executable, str(build_py)],
                capture_output=True, text=True,
                cwd=str(self._eclipse_dir),
                timeout=2400,   # 40 min max
            )
            if result.returncode == 0:
                self.root.after(0, self._rebuild_ok)
            else:
                stderr = result.stderr[-400:] if result.stderr else ""
                self.root.after(0, lambda: self._rebuild_error(stderr))
        except subprocess.TimeoutExpired:
            self.root.after(0, lambda: self._rebuild_error("Timeout (>40 min)"))
        except Exception as exc:
            self.root.after(0, lambda: self._rebuild_error(str(exc)))

    def _rebuild_ok(self):
        self._btn_rebuild.config(state="disabled", text="EXE compilado ✓", bg=GREEN)
        self._lbl_rebuild_estado.config(
            text="ECLIPSE-T.exe generado en dist/", fg=GREEN)

    def _rebuild_error(self, msg: str):
        self._btn_rebuild.config(state="normal", text="Reintentar compilacion")
        self._lbl_rebuild_estado.config(
            text=f"Error en compilacion: {msg[:80]}", fg=RED)

    # ── Run ──────────────────────────────────────────────────────────────────

    def run(self):
        self.root.mainloop()


# ── Entry point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import multiprocessing
    multiprocessing.freeze_support()
    HefestosApp().run()
