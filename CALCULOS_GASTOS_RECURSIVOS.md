# Cálculos Recursivos de Gastos — Fundamento Legal y Fórmulas

> Documento técnico-jurídico que explica cómo cada concepto de gasto se calcula
> automáticamente desde los parámetros del sistema. **Todos los valores son
> recursivos**: cambia un % en `Parámetros del Sistema` → se propaga al instante
> a `CostoPersonal` → a `RubroGasto` (Anexo 2) → al Dashboard.

---

## VARIABLES BASE (entradas del usuario)

| Variable | Fuente | Norma |
|---|---|---|
| `salario_basico` (mensual) | Plantas de Personal | Decreto Salarial Anual |
| `cantidad` (núm. cargos) | Plantas de Personal | Planta aprobada por Acuerdo Municipal |
| `salario_anual` | = `salario_basico × 12` | — |

---

## 1. PRESTACIONES SOCIALES

### 1.1 Prima de Servicios
- **Norma:** Código Sustantivo del Trabajo (CST) art. 306; Ley 1788/2016 (servidores públicos).
- **Concepto:** 1 mes de salario al año (15 días en junio + 15 días en diciembre).
- **Fórmula:**
  ```
  prima_servicios_anual = salario_anual × pct_prima_servicios
                        = salario_anual × 0.0833
  ```
- **Default:** 8.33% = 1/12 = 1 mes/año.

### 1.2 Prima de Navidad
- **Norma:** Ley 41/1975; Decreto 1042/1978 art. 32.
- **Concepto:** 1 mes de salario al año, pagada en diciembre.
- **Fórmula:**
  ```
  prima_navidad_anual = salario_anual × pct_prima_navidad
                      = salario_anual × 0.0833
  ```

### 1.3 Vacaciones
- **Norma:** Ley 4/1992; Decreto 1042/1978 art. 8.
- **Concepto:** 15 días hábiles de descanso remunerado al año.
- **Fórmula:**
  ```
  vacaciones_anual = salario_anual × (15/360)
                   = salario_anual × 0.0417
  ```

### 1.4 Prima de Vacaciones
- **Norma:** Decreto 1042/1978 art. 24.
- **Concepto:** 15 días salariales adicionales al disfrutar vacaciones.
- **Fórmula:**
  ```
  prima_vacaciones_anual = salario_anual × pct_prima_vacaciones
                         = salario_anual × 0.0417
  ```

### 1.5 Cesantías
- **Norma:** Ley 50/1990 art. 99; Ley 1064/2006.
- **Concepto:** 1 mes de salario por año de servicios.
- **Fórmula:**
  ```
  cesantias_anual = salario_anual × pct_cesantias
                  = salario_anual × 0.0833
  ```

### 1.6 Intereses sobre Cesantías
- **Norma:** Ley 52/1975 art. 1.
- **Concepto:** 12% anual sobre el valor de las cesantías.
- **Fórmula:**
  ```
  intereses_cesantias_anual = cesantias_anual × pct_intereses_cesantias
                            = cesantias_anual × 0.12
  ```

### 1.7 Bonificación por Servicios Prestados
- **Norma:** Decreto 1042/1978 art. 45; Decreto 1101/2025 (ajuste).
- **Concepto:** Pago anual entre 35% y 50% del salario mensual, según rango salarial.
- **Fórmula:**
  ```
  bonif_servicios_anual = salario_basico × pct_bonif_servicios_prestados
                        = salario_basico × 0.50    # (una vez al año)
  ```

### 1.8 Bonificación de Recreación
- **Norma:** Decreto 451/1984; Ley 100/1993 art. 50.
- **Concepto:** 2 días de salario para recreación durante vacaciones.
- **Fórmula:**
  ```
  bonif_recreacion_anual = salario_anual × pct_bonif_recreacion
                         = salario_anual × 0.0139    # ≈ 5/360
  ```

**Total Prestaciones Sociales anuales:**
```
total_prestaciones = prima_servicios + prima_navidad + vacaciones +
                     prima_vacaciones + cesantias + intereses_cesantias +
                     bonif_servicios + bonif_recreacion
```

---

## 2. APORTES SEGURIDAD SOCIAL (Ley 100/1993)

### 2.1 Aporte a Pensión — Empleador
- **Norma:** Ley 100/1993 art. 22; Ley 797/2003.
- **% Empleador:** 12% del IBC (Ingreso Base de Cotización).
- **Fórmula:**
  ```
  aporte_pension_anual = salario_anual × pct_aporte_pension
                       = salario_anual × 0.12
  ```

### 2.2 Aporte a Salud — Empleador
- **Norma:** Ley 100/1993 art. 204; Ley 1607/2012.
- **% Empleador:** 8.5% del IBC.
- **Fórmula:**
  ```
  aporte_salud_anual = salario_anual × pct_aporte_salud
                     = salario_anual × 0.085
  ```

### 2.3 Aporte ARL (Riesgos Laborales)
- **Norma:** Decreto 1295/1994; Decreto 1772/1994.
- **Tarifa por clase de riesgo:**
  - Clase I: 0.522% (administrativos)
  - Clase II: 1.044%
  - Clase III: 2.436%
  - Clase IV: 4.350%
  - Clase V: 6.960%
- **Fórmula:**
  ```
  aporte_arl_anual = salario_anual × pct_aporte_arl
                   = salario_anual × 0.00522    # (clase I default)
  ```

**Total Aportes Seguridad Social anuales:**
```
total_aportes_seg_social = aporte_pension + aporte_salud + aporte_arl
```

---

## 3. APORTES PARAFISCALES (Ley 21/1982)

### 3.1 SENA
- **Norma:** Ley 21/1982 art. 7; Ley 119/1994.
- **Tarifa:** 2% del salario.
- **Fórmula:** `salario_anual × 0.02`

### 3.2 ICBF
- **Norma:** Ley 7/1979 art. 2; Ley 27/1974.
- **Tarifa:** 3% del salario.
- **Fórmula:** `salario_anual × 0.03`

### 3.3 Caja de Compensación Familiar
- **Norma:** Ley 21/1982 art. 7.
- **Tarifa:** 4% del salario.
- **Fórmula:** `salario_anual × 0.04`

### 3.4 ESAP (Escuela Superior de Administración Pública)
- **Norma:** Ley 21/1982 art. 7 (solo entidades del orden territorial).
- **Tarifa:** 0.5% del salario.
- **Fórmula:** `salario_anual × 0.005`

### 3.5 Escuelas Industriales e Institutos Técnicos
- **Norma:** Ley 21/1982 art. 7.
- **Tarifa:** 1% del salario.
- **Fórmula:** `salario_anual × 0.01`

**Total Parafiscales anuales:** ~10.5% del salario anual.

---

## 4. SUBSIDIO DE TRANSPORTE

- **Norma:** Ley 15/1959; Decreto SMLMV anual.
- **Aplicabilidad:** Empleados con salario ≤ 2 SMLMV.
- **Fórmula:**
  ```
  if salario_basico <= 2 × SMLMV:
      subsidio_transporte_anual = subsidio_transporte_mensual × 12
  else:
      subsidio_transporte_anual = 0
  ```

---

## 5. COSTO TOTAL ANUAL POR CARGO

```
costo_total_anual_cargo = salario_anual
                        + total_prestaciones
                        + total_aportes_seguridad_social
                        + total_parafiscales
                        + subsidio_transporte_anual
                        ─────────────────────────────────
                        × cantidad (núm. cargos del mismo perfil)
```

**Factor estimado:** Para una secretaria de salario ~$2,3M mensuales:
- Salario anual base: $28M
- + Prestaciones (~37%): $10.4M
- + Aportes SS (~21%): $5.9M
- + Parafiscales (~10.5%): $2.9M
- **= ~$47M anuales** (factor ~1.68×)

---

## 6. PROYECCIÓN ENTRE AÑOS (Recursivo)

### 6.1 Incremento Salarial Anual
```
salario_basico_actual = salario_basico_anterior × (1 + pct_incremento)
```
Donde `pct_incremento` se lee de `pct_incremento_salarial` por defecto (Decreto Salarial anual del Gobierno Nacional).

**Editable por cargo** en Plantas de Personal: cada empleado puede tener su propio % (escalafón, mérito, ajuste por equidad).

### 6.2 SMLMV por Año
Almacenado en `VariableMacro` tipo `SMLV`. Consulta dinámica por año:
- 2026: $1,750,905
- 2027: $1,859,461 (= 2026 × 1.062)
- 2028: $1,933,839 (= 2027 × 1.040)

### 6.3 IPC por Año
Almacenado en `VariableMacro` tipo `IPC`. Afecta:
- Rubros de ingreso con método `IPC` (sobretasas, multas, intereses)
- Incremento mesada pensionados (Ley 100/1993 art. 14)

---

## 7. PENSIONADOS (Ley 100/1993)

### 7.1 Incremento de Mesada
- **Norma:** Ley 100/1993 art. 14.
- **Concepto:** La mesada pensional se incrementa anualmente con el IPC del año anterior.
- **Fórmula:**
  ```
  mesada_actual = mesada_anterior × (1 + pct_incremento_pensionados)
  ```
  Donde `pct_incremento_pensionados` se sincroniza con el IPC.

### 7.2 Mesadas Anuales
- **Norma:** Ley 100/1993 (12 mesadas + prima junio + prima diciembre = 14).
- **Fórmula:**
  ```
  total_mesadas_anuales = mesada_actual × 14
  ```

---

## 8. SERVICIO DE DEUDA (Ley 358/1997)

### 8.1 Tasa de Cobertura de Riesgo (TCR)
- **Norma:** Ley 358/1997 art. 4; Decreto 696/1998.
- **Concepto:** Factor que cubre el riesgo de tasa de interés en operaciones de crédito interno.
- **Fórmula:**
  ```
  intereses_tcr = intereses × tcr_deuda
                = intereses × 0.921
  total_servicio_deuda = capital + intereses + intereses_tcr
  ```

### 8.2 Capacidad de Pago (Indicadores Ley 358)
- **Solvencia:** `intereses / ahorro_operacional ≤ 40%` (`pct_limite_intereses_ley358`)
- **Sostenibilidad:** `saldo_deuda / ingresos_corrientes ≤ 80%` (`pct_limite_saldo_deuda_ley358`)

---

## 9. LÍMITES LEY 617/2000 (% sobre ICLD)

| Categoría | % Funcionamiento | % Concejo | % Personería |
|---|---:|---:|---:|
| Especial | 50% | 0.6% | 1.6% |
| 1ª | 55% | 0.7% | 1.7% |
| 2ª | 60% | 0.8% | 2.2% |
| 3ª | 60% | 1.0% | 400 SMLV |
| 4ª | 75% | 1.2% | 330 SMLV |
| **5ª** | **75%** | **1.5%** | **210-260 SMLV (Ley 2461)** |
| 6ª | 80% | 1.5% | 200-250 SMLV (Ley 2461) |

---

## 10. CADENA RECURSIVA (resumen)

```
ParametrosSistema (% pension, salud, ARL, primas, etc.)
        │
        ▼
[Botón "Recalcular desde Parámetros" o "Guardar"]
        │
        ▼
CostoPersonal (regenera prima_navidad, aportes_salud, etc.)
        │
        ▼
costo_total_anual = sum(salario_anual + prestaciones + aportes + parafiscales)
        │
        ▼
RubroGasto método CPS suma todos los CostoPersonal de la sección
        │
        ▼
Anexo 2 muestra el total por unidad ejecutora
        │
        ▼
Dashboard refleja el total presupuesto de gastos
```

**Toda la cadena se ejecuta automáticamente al guardar Parámetros del Sistema o
Plantas de Personal.**

---

*Documento técnico-jurídico para la Secretaría de Hacienda Municipal — Vigencia 2027.*
