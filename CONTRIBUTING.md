# Contribuir a F5 RiskAI

## Flujo de trabajo con Git

### Ramas principales

| Rama | Propósito |
|---|---|
| `main` | Versión estable y lista para producción. Solo se actualiza mediante merge desde `develop` cuando hay una versión funcional completa. |
| `develop` | Rama de integración donde se agrupan todas las features antes de pasar a `main`. Es la rama base para crear nuevas features. |
| `feature/*` | Rama temporal donde se desarrolla una funcionalidad concreta. Se crea desde `develop` y se fusiona de vuelta a `develop` cuando está lista. |

### Flujo

```
main
 └── develop
      ├── feature/data-cleaning
      ├── feature/eda
      ├── feature/baseline-model
      ├── feature/api
      └── feature/frontend
```

### Nomenclatura de ramas

```
feature/<descripción-corta-en-kebab-case>
```

Ejemplos:

- `feature/data-cleaning`
- `feature/eda`
- `feature/baseline-model`
- `feature/api`
- `feature/frontend`

### Convenciones de commits

Cada commit debe seguir el formato:

```
<tipo>: <descripción corta>
```

| Tipo | Uso |
|---|---|
| `feat:` | Nueva funcionalidad |
| `fix:` | Corrección de un bug o error |
| `docs:` | Cambios en documentación |
| `refactor:` | Reestructuración de código sin cambiar funcionalidad |
| `test:` | Añadir o modificar tests |
| `chore:` | Tareas de mantenimiento (configuración, dependencias, etc.) |

### Ejemplos de commits

```
feat: add initial data loading pipeline
fix: correct column name mismatch in dataset
docs: add project structure documentation
refactor: extract preprocessing into separate module
test: add unit tests for data validation
chore: update requirements.txt with pandas version
```
