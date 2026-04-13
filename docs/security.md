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

- `examples/cameras.input.example.csv`
- `examples/results.detailed.example.csv`
- `examples/results.summary.example.csv`

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

Ejemplos de rutas locales válidas:

- `.local/cameras.input.real.csv`
- `.local/results.detailed.real.csv`
- `.local/results.summary.real.csv`
- `data/`
- `.evidence/`

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
data/
.evidence/
```

---

## Credenciales

### Recomendación principal

Usar:

- `credential_id`

y resolver credenciales fuera del repo mediante:

- variables de entorno
- secret store
- archivo local no versionado
- configuración local privada

### Campo temporal de laboratorio

Se permite `username` y `password` **solo para pruebas locales**.

Reglas:

- nunca se suben a Git
- nunca se dejan en `examples/`
- nunca se incluyen en capturas o logs públicos

---

## Logs y evidencia

Cualquier log o evidencia debe cumplir:

- redactar credenciales
- no exponer tokens
- no exponer URL completas con auth embebida
- no subirse a GitHub

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
2. confirmar que no aparezcan archivos de `.local/`, `data/` o `.evidence/`
3. confirmar que `examples/` solo contiene dummy

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
- `data/`
- `.evidence/`
- `.env`
- `*.local.csv`

Y puede reforzarse con patrones adicionales como:

- `*.real.csv`
- `*_real*.csv`

---

## Regla de revisión final

Antes de push o PR, verificar:

- ¿hay IPs reales?
- ¿hay usuarios/passwords?
- ¿hay outputs reales?
- ¿hay evidencia?
- ¿hay logs sensibles?

Si la respuesta es sí para cualquiera, **no se sube**.

---

## Principio operativo

**Dummy al repo, real fuera del repo.**