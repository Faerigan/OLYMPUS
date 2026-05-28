"""
hefestos.py — Instalador ECLIPSE-T v3.0
HEFESTOS · Ecosistema OLYMPUS · CESFAM Cerrillos de Tamaya

Compila como: pyinstaller --onefile --windowed --name HEFESTOS hefestos.py
"""

import math
import json
import platform
import queue
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

# ── Rutas ────────────────────────────────────────────────────────────────────

_BASE_DIR = Path(__file__).parent          # D:\HEFESTOS
sys.path.insert(0, str(_BASE_DIR))        # permite importar hefestos_key_validator

OLYMPUS_RAW = "https://raw.githubusercontent.com/Faerigan/OLYMPUS/main"

# ── Colores ──────────────────────────────────────────────────────────────────

BG    = "#1A1A2E"
DARK  = "#0F0F1E"
GOLD  = "#F5A623"
LIGHT = "#E8E8E8"
GREEN = "#4CAF50"
RED   = "#F44336"
GRAY  = "#555577"
ANVIL = "#4A4A5A"
METAL = "#8A8A9A"


# ── Canvas: logo HEFESTOS ────────────────────────────────────────────────────

def dibujar_logo(canvas: tk.Canvas, cx: int, cy: int, s: float = 1.0):
    """Yunque + martillo + rayos solares dorados."""

    # Rayos (divergen desde el punto central)
    for ang in range(0, 360, 30):
        rad   = math.radians(ang)
        largo = int(28 * s) if abs(math.sin(rad)) > 0.5 else int(18 * s)
        r_in  = int(38 * s)
        r_out = r_in + largo
        x1 = cx + int(math.cos(rad) * r_in)
        y1 = cy + int(math.sin(rad) * r_in)
        x2 = cx + int(math.cos(rad) * r_out)
        y2 = cy + int(math.sin(rad) * r_out)
        canvas.create_line(x1, y1, x2, y2, fill=GOLD, width=max(1, int(2 * s)))

    # Base yunque (trapecio)
    aw, ah = int(72 * s), int(24 * s)
    ax, ay = cx - aw // 2, cy + int(16 * s)
    canvas.create_polygon(
        ax + int(6*s), ay,
        ax + aw - int(6*s), ay,
        ax + aw, ay + ah,
        ax, ay + ah,
        fill=ANVIL, outline=METAL, width=1,
    )
    # Cuello yunque
    nw = int(28 * s)
    nx = cx - nw // 2
    canvas.create_rectangle(nx, cy + int(6*s), nx + nw, ay,
                             fill=ANVIL, outline=METAL)
    # Cabeza yunque (plana, metálica)
    hw, hh = int(82 * s), int(12 * s)
    hx = cx - hw // 2
    canvas.create_rectangle(hx, cy - int(6*s), hx + hw, cy + int(6*s),
                             fill=METAL, outline=LIGHT, width=1)

    # Mango martillo (diagonal levemente)
    canvas.create_rectangle(
        cx - int(5*s), cy - int(62*s),
        cx + int(5*s), cy - int(10*s),
        fill=DARK, outline=GRAY,
    )
    # Cabeza martillo
    mhw, mhh = int(36*s), int(18*s)
    mhx = cx - int(10*s)
    mhy = cy - int(62*s) - mhh
    canvas.create_rectangle(mhx, mhy, mhx + mhw, mhy + mhh,
                             fill=METAL, outline=LIGHT, width=1)


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
        self.root.geometry("620x720")

        self._cola:        queue.Queue = queue.Queue()
        self._eclipse_dir: Path | None = None
        self._labels_pasos: list[dict] = []

        self._manifest = self._cargar_manifest()
        self._total_pasos = sum(
            len(g["pasos"]) for g in self._manifest["grupos"]
        )
        self._pasos_completados = 0

        self._var_dir   = tk.StringVar()
        self._var_clave = tk.StringVar()

        self._construir_ui()
        self._detectar_eclipse()

    # ── Carga de manifiesto ──────────────────────────────────────────────────

    def _cargar_manifest(self) -> dict:
        path = _BASE_DIR / "install_manifest.json"
        with open(path, encoding="utf-8") as f:
            return json.load(f)

    # ── Construccion UI ──────────────────────────────────────────────────────

    def _construir_ui(self):
        self._f_inicio      = tk.Frame(self.root, bg=BG)
        self._f_instalacion = tk.Frame(self.root, bg=BG)
        self._f_final       = tk.Frame(self.root, bg=BG)

        self._construir_inicio()
        self._construir_instalacion()
        self._construir_final()
        self._mostrar(self._f_inicio)

    def _mostrar(self, frame: tk.Frame):
        for f in (self._f_inicio, self._f_instalacion, self._f_final):
            f.pack_forget()
        frame.pack(fill="both", expand=True)

    # ── Pantalla 1: Inicio ───────────────────────────────────────────────────

    def _construir_inicio(self):
        fr = self._f_inicio

        # Logo
        cv = tk.Canvas(fr, width=200, height=200, bg=BG, highlightthickness=0)
        cv.pack(pady=(28, 0))
        dibujar_logo(cv, 100, 100, s=1.0)

        tk.Label(fr, text="HEFESTOS", font=("Helvetica", 24, "bold"),
                 fg=GOLD, bg=BG).pack(pady=(6, 0))
        tk.Label(fr, text="Instalador Ecosistema OLYMPUS  ·  v1.0",
                 font=("Helvetica", 10), fg=LIGHT, bg=BG).pack()
        tk.Label(fr, text="CESFAM Cerrillos de Tamaya",
                 font=("Helvetica", 9), fg=GRAY, bg=BG).pack(pady=(2, 18))

        tk.Frame(fr, height=1, bg=GOLD).pack(fill="x", padx=44, pady=(0, 18))

        # Directorio ECLIPSE-T
        tk.Label(fr, text="Directorio ECLIPSE-T:", font=("Helvetica", 10, "bold"),
                 fg=LIGHT, bg=BG).pack(anchor="w", padx=48)
        row_dir = tk.Frame(fr, bg=BG)
        row_dir.pack(fill="x", padx=48, pady=(4, 14))
        tk.Entry(row_dir, textvariable=self._var_dir, bg=DARK, fg=LIGHT,
                 insertbackground=GOLD, relief="flat",
                 font=("Courier", 10), width=36).pack(side="left",
                                                       ipady=5, padx=(0, 6))
        tk.Button(row_dir, text="…", bg=GRAY, fg=LIGHT, relief="flat",
                  command=self._seleccionar_dir).pack(side="left")

        # Clave
        tk.Label(fr, text="Codigo de instalacion:", font=("Helvetica", 10, "bold"),
                 fg=LIGHT, bg=BG).pack(anchor="w", padx=48)
        entry_clave = tk.Entry(fr, textvariable=self._var_clave, show="•",
                               bg=DARK, fg=LIGHT, insertbackground=GOLD,
                               relief="flat", font=("Courier", 13), width=28)
        entry_clave.pack(ipady=6, pady=(4, 4))
        entry_clave.bind("<Return>", lambda _: self._comenzar())

        self._lbl_msg = tk.Label(fr, text="", font=("Helvetica", 9),
                                  fg=RED, bg=BG, wraplength=480, justify="center")
        self._lbl_msg.pack(pady=(2, 0))

        # Botón principal
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
        # Validar directorio
        eclipse_dir = Path(self._var_dir.get().strip())
        if not eclipse_dir.exists():
            self._lbl_msg.config(
                text="Directorio no encontrado. Seleccione la carpeta ECLIPSE.", fg=RED)
            return
        self._eclipse_dir = eclipse_dir

        # Validar clave
        clave = self._var_clave.get().strip()
        if not clave:
            self._lbl_msg.config(text="Ingrese un codigo de instalacion.", fg=RED)
            return

        self._lbl_msg.config(text="Verificando codigo…", fg=GOLD)
        self.root.update()

        valida, estado = self._validar_clave(clave)
        if not valida:
            from hefestos_key_validator import MENSAJES  # type: ignore
            self._lbl_msg.config(text=MENSAJES.get(estado, estado), fg=RED)
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

        self._lbl_msg.config(text="")
        self._iniciar_instalacion()

    def _validar_clave(self, clave: str) -> tuple[bool, str]:
        try:
            from hefestos_key_validator import validar_clave_instalacion  # type: ignore
            return validar_clave_instalacion(clave, equipo_id=platform.node())
        except ImportError:
            return True, "sin_red"

    # ── Pantalla 2: Instalación ──────────────────────────────────────────────

    def _construir_instalacion(self):
        fr = self._f_instalacion

        # Header compacto
        hdr = tk.Frame(fr, bg=DARK)
        hdr.pack(fill="x")
        cv_s = tk.Canvas(hdr, width=54, height=54, bg=DARK, highlightthickness=0)
        cv_s.pack(side="left", padx=(10, 0), pady=6)
        dibujar_logo(cv_s, 27, 27, s=0.3)
        tk.Label(hdr, text="HEFESTOS — Instalacion en curso",
                 font=("Helvetica", 12, "bold"), fg=GOLD, bg=DARK).pack(
                     side="left", padx=10)

        # Lista de pasos (todos los grupos)
        scroll_outer = tk.Frame(fr, bg=BG)
        scroll_outer.pack(fill="x", padx=18, pady=(10, 4))

        for grupo in self._manifest["grupos"]:
            tk.Label(scroll_outer, text=f"  {grupo['nombre']}",
                     font=("Helvetica", 9, "bold"), fg=GOLD, bg=BG,
                     anchor="w").pack(fill="x", pady=(6, 1))
            for paso in grupo["pasos"]:
                fila = tk.Frame(scroll_outer, bg=BG)
                fila.pack(fill="x", padx=14, pady=1)
                ico = tk.Label(fila, text="○", font=("Helvetica", 10),
                               fg=GRAY, bg=BG, width=2)
                ico.pack(side="left")
                lbl = tk.Label(fila, text=paso["desc"],
                               font=("Helvetica", 9), fg=LIGHT, bg=BG,
                               anchor="w")
                lbl.pack(side="left", fill="x")
                self._labels_pasos.append({"id": paso["id"], "ico": ico, "lbl": lbl})

        # Barra de progreso
        pk = tk.Frame(fr, bg=BG)
        pk.pack(fill="x", padx=18, pady=(8, 2))
        tk.Label(pk, text="Progreso total:", font=("Helvetica", 9),
                 fg=LIGHT, bg=BG).pack(anchor="w")
        self._progress = ttk.Progressbar(pk, mode="determinate",
                                          length=580, maximum=100)
        self._progress.pack(fill="x", pady=(2, 0))

        self._lbl_estado = tk.Label(fr, text="Preparando…",
                                     font=("Helvetica", 9, "italic"),
                                     fg=GOLD, bg=BG)
        self._lbl_estado.pack(anchor="w", padx=20, pady=(2, 0))

        # Log
        tk.Label(fr, text="Detalle:", font=("Helvetica", 9, "bold"),
                 fg=LIGHT, bg=BG).pack(anchor="w", padx=20, pady=(8, 2))
        log_wrap = tk.Frame(fr, bg=DARK)
        log_wrap.pack(fill="both", expand=True, padx=18, pady=(0, 14))
        self._log = tk.Text(log_wrap, bg=DARK, fg="#AAFFAA",
                             font=("Courier", 8), relief="flat",
                             state="disabled", wrap="word", height=9)
        sb = ttk.Scrollbar(log_wrap, command=self._log.yview)
        self._log.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
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
                        self._set_paso(msg["id"], "✗", RED, RED)
                    else:
                        self._set_paso(msg["id"], "–", GRAY, GRAY)

                elif t == "fin":
                    self._progress["value"] = 100
                    self._lbl_estado.config(text="Instalacion completada.")
                    self._mostrar_final()
                    return  # detener polling

        except queue.Empty:
            pass

        self.root.after(120, self._procesar_cola)

    def _set_paso(self, pid: str, ico: str, ico_color: str, lbl_color: str):
        for entry in self._labels_pasos:
            if entry["id"] == pid:
                entry["ico"].config(text=ico, fg=ico_color)
                entry["lbl"].config(fg=lbl_color)
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
            destino = self._eclipse_dir / paso["destino"]  # type: ignore[operator]
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

    # ── Implementacion de cada tipo ──────────────────────────────────────────

    def _pip(self, args: list[str]) -> bool:
        result = subprocess.run(
            [sys.executable, "-m", "pip"] + args,
            capture_output=True, text=True,
        )
        salida = (result.stdout + result.stderr).strip()
        for linea in salida.splitlines()[-6:]:
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
            salida = (result.stdout + result.stderr).strip()
            for linea in salida.splitlines()[-5:]:
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
            rutas = [
                Path(r"C:\Program Files\Mozilla Firefox\firefox.exe"),
                Path(r"C:\Program Files (x86)\Mozilla Firefox\firefox.exe"),
            ]
            encontrado = any(p.exists() for p in rutas)
        estado = "encontrado" if encontrado else "NO encontrado (HELIOS no disponible)"
        self._emit(tipo="log", texto=f"{app}: {estado}")
        return True  # no bloquea la instalacion

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
                exe_origen = Path(tmp) / "geckodriver.exe"
                if not exe_origen.exists():
                    self._emit(tipo="log", texto="geckodriver.exe no encontrado en ZIP")
                    return False
                destino = self._eclipse_dir / "geckodriver.exe"  # type: ignore[operator]
                shutil.copy2(str(exe_origen), str(destino))
            self._emit(tipo="log", texto=f"geckodriver instalado en {destino.name}")
            return True
        except Exception as exc:
            self._emit(tipo="log", texto=f"Error geckodriver: {exc}")
            return False

    def _correr_script(self, script_rel: str) -> bool:
        script = self._eclipse_dir / script_rel  # type: ignore[operator]
        if not script.exists():
            self._emit(tipo="log", texto=f"Script no encontrado: {script_rel}")
            return False
        self._emit(tipo="log", texto=f"Ejecutando {script_rel}…")
        result = subprocess.run(
            [sys.executable, str(script)],
            capture_output=True, text=True,
            cwd=str(self._eclipse_dir),
            timeout=120,
        )
        salida = (result.stdout + result.stderr).strip()
        for linea in salida.splitlines()[-8:]:
            self._emit(tipo="log", texto=linea)
        return result.returncode == 0

    def _test_arranque(self) -> bool:
        for nombre in ("eclipse_t_v3.py", "eclipse_t_v2.py"):
            exe = self._eclipse_dir / nombre  # type: ignore[operator]
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

    # ── Pantalla 3: Final ────────────────────────────────────────────────────

    def _construir_final(self):
        fr = self._f_final

        tk.Frame(fr, height=50, bg=BG).pack()

        cv = tk.Canvas(fr, width=170, height=170, bg=BG, highlightthickness=0)
        cv.pack()
        dibujar_logo(cv, 85, 85, s=0.86)

        self._lbl_fin_titulo = tk.Label(
            fr, text="Instalacion completada",
            font=("Helvetica", 17, "bold"), fg=GREEN, bg=BG,
        )
        self._lbl_fin_titulo.pack(pady=(18, 6))

        self._lbl_fin_detalle = tk.Label(
            fr,
            text="Todos los componentes estan instalados.\n"
                 "ECLIPSE-T esta listo para su uso.",
            font=("Helvetica", 10), fg=LIGHT, bg=BG, justify="center",
        )
        self._lbl_fin_detalle.pack(pady=(0, 32))

        tk.Button(
            fr, text="  Abrir ECLIPSE-T  ▶  ",
            font=("Helvetica", 14, "bold"),
            bg=GOLD, fg=DARK, relief="flat", padx=20, pady=10,
            activebackground="#D4891A",
            command=self._abrir_eclipse,
        ).pack(pady=(0, 12))

        tk.Button(
            fr, text="Cerrar",
            font=("Helvetica", 10), bg=GRAY, fg=LIGHT,
            relief="flat", padx=16, pady=6,
            command=self.root.destroy,
        ).pack()

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
            "No se encontro eclipse_t_v2.py ni eclipse_t_v3.py\n"
            f"en {self._eclipse_dir}",
        )

    # ── Run ──────────────────────────────────────────────────────────────────

    def run(self):
        self.root.mainloop()


# ── Entry point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import multiprocessing
    multiprocessing.freeze_support()
    HefestosApp().run()
