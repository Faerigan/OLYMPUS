#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FRAGMENTO DE INTEGRACIÓN — hefestos_forge.gif en hefestos.py
════════════════════════════════════════════════════════════
Insertar en hefestos.py según las instrucciones indicadas.
Compatible con PyInstaller (_MEIPASS) y ejecución directa.
"""

# ── 1. IMPORTS ADICIONALES (agregar junto a los imports existentes) ──────────
import sys
import os
from PIL import Image, ImageTk   # Pillow ya es dependencia de hefestos.py

# ── 2. FUNCIÓN resource_path (agregar una sola vez, nivel módulo) ────────────
def resource_path(rel: str) -> str:
    """
    Resuelve rutas de recursos compatibles con PyInstaller.
    - En producción (.exe): usa sys._MEIPASS (carpeta temporal del bundle)
    - En desarrollo: usa la carpeta del script
    """
    if hasattr(sys, "_MEIPASS"):
        base = sys._MEIPASS
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, rel)

# ── 3. CLASE AnimacionForja ──────────────────────────────────────────────────
class AnimacionForja:
    """
    Reproduce hefestos_forge.gif en un tk.Canvas de Tkinter.

    Uso típico dentro de _f_instalacion (pantalla de instalación):

        self._anim = AnimacionForja(canvas, ancho=300, alto=300)
        self._anim.iniciar()
        # ... cuando termina la instalación:
        self._anim.detener()

    El canvas debe tener background="#2C2416" (ANIM_BG).
    """

    def __init__(self, canvas, ancho: int = 300, alto: int = 300):
        self._canvas  = canvas
        self._ancho   = ancho
        self._alto    = alto
        self._frames  = []       # lista de ImageTk.PhotoImage
        self._delays  = []       # duración en ms por frame
        self._idx     = 0        # frame actual
        self._job     = None     # referencia al after() para cancelar
        self._img_id  = None     # id del objeto canvas
        self._cargado = False
        self._cargar()

    def _cargar(self):
        """Carga el GIF y extrae todos los frames con sus duraciones."""
        ruta = resource_path(os.path.join("Resources", "hefestos_forge.gif"))
        if not os.path.exists(ruta):
            # Fallo silencioso: sin animación, sin crash
            print(f"[AnimacionForja] GIF no encontrado: {ruta}")
            return

        try:
            gif = Image.open(ruta)
            for i in range(gif.n_frames):
                gif.seek(i)
                frame_img = gif.convert("RGBA")
                # Redimensionar si el canvas tiene tamaño distinto
                if frame_img.size != (self._ancho, self._alto):
                    frame_img = frame_img.resize(
                        (self._ancho, self._alto),
                        Image.LANCZOS
                    )
                # CRÍTICO: mantener referencia o Python recolecta el objeto
                photo = ImageTk.PhotoImage(frame_img)
                self._frames.append(photo)
                self._delays.append(gif.info.get("duration", 150))
            self._cargado = True
        except Exception as e:
            print(f"[AnimacionForja] Error al cargar GIF: {e}")

    def iniciar(self):
        """Inicia el loop de animación."""
        if not self._cargado or not self._frames:
            return
        self._idx = 0
        self._reproducir()

    def _reproducir(self):
        """Avanza un frame y programa el siguiente."""
        if not self._frames:
            return
        frame = self._frames[self._idx]
        delay = self._delays[self._idx]

        if self._img_id is None:
            # Primera vez: crear el objeto en el canvas centrado
            self._img_id = self._canvas.create_image(
                self._ancho // 2,
                self._alto  // 2,
                image=frame,
                anchor="center"
            )
        else:
            self._canvas.itemconfig(self._img_id, image=frame)

        self._idx = (self._idx + 1) % len(self._frames)
        self._job = self._canvas.after(delay, self._reproducir)

    def detener(self):
        """Cancela el loop. Llamar antes de destruir el canvas."""
        if self._job is not None:
            self._canvas.after_cancel(self._job)
            self._job = None


# ── 4. INTEGRACIÓN EN _construir_f_instalacion ──────────────────────────────
#
# Dentro del método que construye la pantalla de instalación, agregar el canvas
# oscuro y conectar AnimacionForja. Ejemplo de implementación:
#
#   def _construir_f_instalacion(self):
#       self._f_instalacion = tk.Frame(self._frame_centro, bg=BG)
#
#       # Canvas oscuro con borde dorado (según spec TAREA 1)
#       canvas_forge = tk.Canvas(
#           self._f_instalacion,
#           width=300, height=300,
#           bg="#2C2416",          # ANIM_BG
#           highlightthickness=3,
#           highlightbackground="#B8860B",   # GOLD
#       )
#       canvas_forge.pack(pady=(20, 10))
#
#       # Arrancar animación
#       self._anim_forja = AnimacionForja(canvas_forge, ancho=300, alto=300)
#       self._anim_forja.iniciar()
#
#       # Etiqueta de estado (se actualiza desde el hilo de instalación)
#       self._lbl_estado = tk.Label(
#           self._f_instalacion,
#           text="Preparando instalación...",
#           bg=BG, fg=TEXT,
#           font=("Segoe UI", 10)
#       )
#       self._lbl_estado.pack()
#
#   def _mostrar_final(self):
#       # Detener animación antes de cambiar pantalla
#       if hasattr(self, "_anim_forja"):
#           self._anim_forja.detener()
#       # ... resto del código de finalización
