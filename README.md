# OLYMPUS — Ecosistema Clínico CESFAM

> Repositorio público de actualizaciones para el ecosistema OLYMPUS.
> **No contiene código fuente ni datos de pacientes.**

---

## Componentes del ecosistema

| Nombre | Rol | Estado |
|--------|-----|--------|
| **ECLIPSE-T** | Aplicación principal de registros clínicos | v3.0 estable |
| **HERMES** | Transcripción de voz offline (Whisper) | v3.0 estable |
| **HELIOS** | Historial de laboratorio desde IRIS / RedClínica | v1.0 estable |
| **HEFESTOS** | Instalador con asistente visual | v2.0 estable |

---

## Instalación rápida

1. Copie `ECLIPSE-T.exe`, `helios.exe` y `HEFESTOS.exe` a una carpeta local (p. ej. `C:\Users\<usuario>\Desktop\APPS ECICEP`).
2. Ejecute `HEFESTOS.exe`.
3. Ingrese la carpeta y el código de activación.
4. HEFESTOS descarga automáticamente el modelo de voz HERMES y geckodriver.
5. Al finalizar acepte los Términos y Condiciones y haga clic en **Abrir ECLIPSE-T**.

> **Sin Python requerido** en el equipo destino para usar los `.exe`.

---

## Requisitos previos (solo si ejecuta desde código fuente `.py`)

Si en lugar de los ejecutables está corriendo directamente los archivos `.py`,
necesitará Python instalado previamente. Puede instalarlo con **winget**
(viene preinstalado en Windows 10 v1809+ y Windows 11):

```
winget install Python.Python.3.11
```

Luego instale las dependencias:

```
pip install openai-whisper sounddevice rapidfuzz cryptography selenium pypdf pillow
```

> Los ejecutables `.exe` ya incluyen todas estas dependencias, no es necesario pip.

---

## Firefox — requerido para HELIOS

HELIOS usa Selenium + Firefox para acceder a los sistemas de laboratorio (IRIS, RedClínica).

**HEFESTOS intenta instalar Firefox automáticamente** con winget. Si falla:

```
winget install Mozilla.Firefox
```

O descárguelo manualmente desde **mozilla.org**.

> Si Firefox no está instalado, ECLIPSE-T funciona normalmente pero HELIOS no puede
> consultar el laboratorio.

---

## Modelo de voz HERMES (base.pt)

HERMES requiere el modelo Whisper `base.pt` (~139 MB) en la carpeta `modelos/`
dentro del directorio de ECLIPSE-T. HEFESTOS lo descarga automáticamente.

Si la descarga falla, puede obtenerlo manualmente:

```
python -c "import whisper; whisper.load_model('base', download_root='<ruta_eclipse>/modelos/')"
```

O descárguelo directamente desde:
`https://openaipublic.azureedge.net/main/whisper/models/ed3a0b6b1c0edf879ad9b11b1af5a0e6ab5db9205f891f668f8b0e6c6326e34e/base.pt`

Guárdelo como `<directorio_eclipse>/modelos/base.pt`.

---

## Archivos de actualización

### `manifest.json`
Versión actual de cada componente. ECLIPSE-T lo consulta al iniciar (si hay red).

### `hermes/hermes_vocab.json`
Vocabulario médico para mejorar el reconocimiento de Whisper.
Incluye fármacos, diagnósticos y términos del CESFAM.
Se actualiza con cada ciclo de refinamiento clínico.

### `hermes/hermes_glossary_patch.json`
Parches de triggers para HERMES (aditivos, no reemplazan el glosario local).

### `hefestos/install_manifest.json`
Instrucciones de instalación que HEFESTOS lee para instalar todos los componentes.

### `eclipse/cie10_updates.csv`
Actualizaciones al catálogo CIE-10 local de ECLIPSE-T.

---

## Uso

**ECLIPSE-T** consulta este repositorio silenciosamente al iniciar para:
- Verificar si hay actualización de vocabulario HERMES disponible
- Descargar el parche si la versión local es anterior

**HEFESTOS** lee `hefestos/install_manifest.json` para:
- Instalar todos los componentes en el orden correcto
- Descargar el modelo Whisper (`base.pt`) y geckodriver
- Instalar Firefox si no está presente (via winget)

---

## Privacidad

Este repositorio **no contiene**:
- Datos de pacientes
- Registros clínicos
- Código fuente de la aplicación
- Logs de uso

Solo contiene vocabulario médico genérico y manifiestos de instalación.

---

## CESFAM Cerrillos de Tamaya — Dr. Nicolás Vargas
*Uso exclusivo para profesionales de salud certificados.*
