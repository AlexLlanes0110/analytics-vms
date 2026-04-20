# Seguridad

## Objetivo

Definir reglas mínimas para evitar que el repositorio contenga datos sensibles o artefactos operativos reales.

---

## Regla principal

**GitHub solo contiene documentación, código y ejemplos dummy.**

No debe contener:

- IPs reales
- usuarios reales
- passwords reales
- CSV reales
- outputs reales
- evidencia
- logs con secretos
- inventario operativo sensible

---

## Qué sí va al repo

Contenido permitido:

- código fuente
- documentación
- ejemplos dummy en `examples/`
- CSV de ejemplo anonimizados
- outputs dummy para demo/documentación

Ejemplos:

- `examples/vms_input_dummy_repo.csv`
- `examples/vms_output_dummy_detailed_example.csv`
- `examples/vms_output_dummy_summary_by_site_example.csv`

---

## Qué no va al repo

Contenido prohibido en GitHub:

- inventario real
- CSV con IPs reales
- resultados reales de health check
- usuarios y passwords
- evidencia (`frames`, capturas, logs operativos)
- archivos temporales de laboratorio
- exports locales de pruebas

---

## Layout local permitido

Rutas locales válidas:

```text
.local/
├─ vms_input_real_local.csv
├─ evidence/
└─ output/
```

### Ejemplos reales que deben permanecer solo en local

- `.local/vms_input_real_local.csv`
- `.local/evidence/<run_id>/<camera_name>/probe.txt`
- `.local/evidence/<run_id>/<camera_name>/detect.txt`
- `.local/evidence/<run_id>/<camera_name>/frames/frame_01.jpg`
- `.local/output/<run_id>/vms_output_real_detailed.csv`
- `.local/output/<run_id>/vms_output_real_summary_by_site.csv`

---

## Separación recomendada de carpetas

### Público / repo

```text
examples/
docs/
src/
README.md
```

### Local / privado

```text
.local/
```

---

## Credenciales

### Recomendación principal

Usar:

- `credential_id` y resolver credenciales fuera del repo mediante:
  - variables de entorno
  - secret store
  - archivo local no versionado
  - configuración local privada

### Campo temporal de laboratorio

Se permite `username` y `password` **solo para pruebas locales**.

Reglas:

- nunca se suben a Git
- nunca se dejan en `examples/`
- nunca se incluyen en documentación pública
- nunca se dejan visibles en logs o capturas compartidas

---

## Logs y evidencia

Cualquier log o evidencia debe cumplir:

- redactar credenciales
- no exponer tokens
- no exponer URL completas con auth embebida
- no subirse a GitHub

Esto aplica a:

- `probe.txt`
- `detect.txt`
- stderr de herramientas
- capturas de consola
- evidencias JPG
- reportes reales

---

## Limpieza operativa

Para laboratorio y operación local, se recomienda que cada nueva corrida:

- conserve `.local/vms_input_real_local.csv`
- limpie el contenido de `.local/evidence/`
- limpie el contenido de `.local/output/`
- recree estructura limpia para la nueva ejecución

### Motivo

- evitar acumulación innecesaria de artefactos
- evitar confusión entre corridas viejas y nuevas
- reducir uso de disco

### Regla de seguridad

La limpieza debe aplicarse solo a `evidence/` y `output/`, nunca al inventario real de entrada salvo que el operador lo decida explícitamente.

---

## Archivos dummy

Todo archivo dummy debe:

- estar anonimizado
- no contener IPs reales
- no contener credenciales reales
- no reutilizar nombres sensibles innecesarios
- servir solo como ejemplo de contrato/formato

---

## Git hygiene

Antes de hacer commit:

1. ejecutar `git status`
2. confirmar que no aparezcan archivos de `.local/`
3. confirmar que `examples/` solo contiene dummy
4. confirmar que no haya evidencia real ni outputs reales en staging

Si algo sensible fue agregado accidentalmente al índice, removerlo con:

```bash
git rm --cached <archivo>
```

o para una carpeta:

```bash
git rm --cached -r .local
```

---

## `.gitignore`

El repositorio debe ignorar como mínimo:

- `.local/`
- `.env`
- `*.local.csv`
- `*.real.csv`
- `*_real*.csv`

Si más adelante aparecen rutas operativas adicionales, también deben quedar ignoradas.

---

## Regla de revisión final

Antes de push o PR, verificar:

- ¿hay IPs reales?
- ¿hay usuarios/passwords?
- ¿hay outputs reales?
- ¿hay evidencia?
- ¿hay logs sensibles?
- ¿hay capturas que muestren credenciales?

Si la respuesta es sí para cualquiera, **no se sube**.

---

## Principio operativo

**Dummy al repo, real fuera del repo.**