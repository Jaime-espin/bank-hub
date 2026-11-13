# Bank-Hub — Roadmap y Visión del Proyecto

Documento de referencia para el diseño, evolución y prioridades del proyecto.

---

## 1. Visión y Propósito

> *"El objetivo de este proyecto es que cuando yo conecte mis cuentas reales, pueda visualizar toda mi información con facilidad para ver de una vista toda mi liquidez. También ver mis estadísticas de a dónde está yendo mi dinero, de qué forma está repartido mi saldo (cuánto en depósitos, cuánto en fondos y cuánta rentabilidad he obtenido). Al final es tener toda la información en un mismo lugar."*

Bank-Hub no busca ser una app comercial. Es un **agregador y centro de mando financiero personal**, privado y local, enfocado en mostrar con precisión el patrimonio neto real.

> **Nota sobre el desarrollo:** El foco de este proyecto está puesto al 100% en la lógica de negocio y **backend** (Python, Flask, SQLite, arquitectura en capas, seguridad de claves e integración de APIs bancarias reguladas). El diseño de interfaz y maquetación de frontend (HTML/CSS) ha sido apoyado con IA, ya que el aprendizaje de frontend no es una prioridad en este proyecto.

---

## 2. El Problema a Resolver (La gran diferencia con otras apps)

En muchas aplicaciones de finanzas personales (Fintonic, Wallet, etc.):
- Cuando mueves dinero de tu cuenta corriente a tu cuenta de inversión (MyInvestor, Indexa, Trade Republic...) o contratas un depósito, **la app lo registra como un "gasto"**.
- Como consecuencia, el dinero "desaparece" de tu saldo visual y las estadísticas de ahorro mensual quedan completamente falseadas.

### Principio de diseño de Bank-Hub:
1. **Una transferencia entre mis cuentas o una aportación a fondos/depósitos NO es un gasto.** Es un traspaso de patrimonio de un bolsillo a otro.
2. **Gasto real** es solo el dinero que sale fuera de mi patrimonio (facturas, compras, suscripciones, ocio).
3. **Ahorro real mensual:**
   $$\text{Ahorro Real} = \text{Ingresos Reales} - \text{Gastos Reales}$$
   Y a partir de ahí, visualizar a qué destino se ha ido ese ahorro: cuánto a liquidez, cuánto a depósitos y cuánto a fondos de inversión.

---

## 3. Modelo de Patrimonio: ¿Cómo está repartido mi saldo?

Para ver con claridad la distribución del dinero, las cuentas y activos se clasifican en tres bloques:

```
┌─────────────────────────────────────────────────────────────────┐
│                        PATRIMONIO TOTAL                         │
├───────────────────┬───────────────────────┬─────────────────────┤
│ 1. LIQUIDEZ       │ 2. DEPÓSITOS / CRÉDITO │ 3. INVERSIONES      │
│ Dinero disponible │ Ahorro o cuentas      │ Dinero en fondos de │
│ en cuentas para   │ vinculadas a tarjeta. │ inversión / acciones│
│ el día a día.     │                       │ + rentabilidad.     │
└───────────────────┴───────────────────────┴─────────────────────┘
```

---

## 4. Fases de Desarrollo y Estado

```
[ FASE 1: Modelo de Datos y Tipificación de Saldo ] ──► COMPLETADA
  │
  ▼
[ FASE 2: Dashboard de Liquidez y Movimientos ] ──────► COMPLETADA
  │
  ▼
[ FASE 3: Analítica y Categorías ] ──────────────────► EN CURSO (Primer hito: Gasolina)
  │
  ▼
[ FASE 4: Múltiples Bancos ] ───────────► SIGUIENTE PASO
```

---

### Fase 1: Estructuración y Modelo de Datos (Backend) — ✅ COMPLETADA
- [x] **Tipos de cuenta:** Columna `tipo_cuenta` en la tabla `cuentas` (`corriente`, `ahorros`, `inversion`) con validación y preservación en sincronizaciones.
- [x] **Enfoque 100% automatizado:** Cuentas gestionadas directamente por API bancaria (descartado el ingreso manual de saldos).
- [x] **Detección de transferencias internas:** Conciliación automática por movimiento espejo (`conciliar_movimiento_espejo`). Comprobado y verificado con 12 traspasos reales entre cuentas.

---

### Fase 2: Dashboard de Liquidez y Movimientos (Visual) — ✅ COMPLETADA
- [x] **Tarjetas superiores de Patrimonio y Liquidez:** Total neto global, liquidez corriente y ahorro/tarjeta.
- [x] **Página dedicada de Movimientos (`/movimientos`):** Histórico completo separado del Dashboard principal.
- [x] **Buscador y filtros dinámicos:** Búsqueda por texto (concepto/tienda), filtro por cuenta, por tipo de movimiento y por categoría.
- [x] **Interfaz moderna y badges:** Badges de colores para ingresos (verde), gastos (rojo) y transferencias internas (azul).
- [ ] *(Opcional / Pospuesto)* Gráfico interactivo de reparto porcentual (donut) tras conectar todas las entidades.

---

### Fase 3: Estadísticas de Flujo y Analítica — EN CURSO
- [x] **Categorización automática por reglas:** Módulo `services/categorizacion.py` con detección de gastos por palabras clave.
- [x] **Detección de gasto en Gasolina:** Tarjeta en el Dashboard con el gasto total en combustible y filtrado específico en movimientos.
- [ ] **Métricas mensuales:** Desglose de ingresos vs gastos por mes y tasa de ahorro mensual real.
- [ ] **Ampliación de categorías:** Añadir más reglas de gasto conforme sea necesario (supermercado, suscripciones, etc.).

---

### Fase 4: Múltiples Bancos e Infraestructura — EN CURSO
- [x] **Transición a bancos reales:** Conexión con banca real española en producción, habilitando SSL/HTTPS local (`cert.pem`, `key.pem`) bajo normativa PSD2.
- [x] **Privacidad del código:** Eliminadas referencias hardcodeadas a entidades bancarias; configuración 100% aislada en `config.json` (ignorado en Git).
- [ ] **Soporte Multi-banco:** Conectar simultáneamente la segunda entidad.
- [ ] **Servidor local permanente:** Despliegue en red doméstica (mini-PC o Raspberry Pi).
