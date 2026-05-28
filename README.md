# OLYMPUS — Ecosistema Clínico CESFAM

> Repositorio público de actualizaciones para el ecosistema OLYMPUS.
> **No contiene código fuente ni datos de pacientes.**

---

## Componentes del ecosistema

| Nombre | Rol | Estado |
|--------|-----|--------|
| **ECLIPSE-T** | Aplicación principal de registros clínicos | v3.0 estable |
| **HERMES** | Transcripción de voz offline (Whisper) | v3.0 estable |
| **HELIOS** | Historial de laboratorio desde IRIS | v1.0 estable |
| **HEFESTOS** | Instalador con asistente visual | v1.0 estable |

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
- Descargar los modelos Whisper y geckodriver

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
