# Manual del Auditor Presupuestal

> Documento técnico de auditoría: explica para CADA rubro de ingreso y gasto
> cómo el software calcula el valor, con su fundamento legal y la ruta de código.
> Permite al auditor verificar que el sistema esté hallando todo correctamente.

**Municipio de Puerto López — Vigencia Fiscal 2027 — Categoría 5**

---

## A. INGRESOS — ANEXO 1

### A1. Impuesto Predial Unificado (1.1.01.01.200)

#### A1.1 Predial Urbano Vigencia Actual (PUVA)
- **Código rubro:** `1.1.01.01.200.01.01`
- **Norma:** Ley 44/1990 art. 1; Acuerdo Municipal Estatuto Tributario.
- **Cálculo:**
  ```
  Para cada categoría predial (UV, UC, UI, UEF):
    Σ(avalúo_catastral × tarifa_por_mil ÷ 1000) × % eficiencia × factor_crecimiento
  ```
- **Parámetros usados:** `pct_eficiencia_recaudo`, `pct_crecimiento_viviendas`, `valor_uvt`
- **Tabla fuente:** `ContribuyentePredial`, `TarifaPredial`
- **Función:** `ingresos.utils.calcular_predial(vigencia, 'urbano')`
- **Resultado actual:** $2,963,674,384

#### A1.2 Predial Urbano Vigencias Anteriores (PUAN)
- **Código rubro:** `1.1.01.01.200.01.02`
- **Norma:** Ley 1066/2006 art. 12 (recuperación cartera).
- **Cálculo:**
  ```
  Σ cartera_vigencia × (pct_cartera_base ÷ 100) × (pct_cartera_urbano ÷ 100)
  ```
- **Parámetros:** `pct_cartera_base`, `pct_cartera_urbano`
- **Tabla fuente:** `CarteraVigenciaAnterior`
- **Función:** `calcular_predial_vigencias_anteriores(vigencia, 'urbano')`
- **Resultado actual:** $1,652,609,247

#### A1.3 Predial Rural Vigencia Actual (PRVA)
- Idem A1.1 con categorías rurales (RU, RA, PE, PNE).
- **Resultado actual:** $13,410,863,619

#### A1.4 Predial Rural Vigencias Anteriores (PRAN)
- Idem A1.2 con `pct_cartera_rural`.
- **Resultado actual:** $6,610,436,987

#### A1.5 Sobretasa Ambiental Urbano (1.1.01.01.014.01)
- **Norma:** Ley 99/1993 art. 44 (15% predial urbano para CAR).
- **Método:** IPC sobre recaudo año anterior.

### A2. Impuesto de Industria y Comercio (ICA)

#### A2.1 ICA Industrial (ICAI)
- **Código rubro:** Industrial — código por estatuto municipal
- **Norma:** Ley 14/1983 arts. 32-40; Ley 1819/2016 art. 343.
- **Cálculo:**
  ```
  Por cada contribuyente:
    ingresos_proyectados = ingresos_brutos × (1 + tasa_pib_nominal)
    impuesto = ingresos_proyectados × tarifa_por_mil ÷ 1000
  Total = Σ impuesto de todos los contribuyentes Industriales
  ```
- **Parámetros:** `tasa_pib_nominal`
- **Función:** `calcular_ica(vigencia)`
- **Resultado actual:** $14,868,000

#### A2.2 ICA Comercial (ICAC) — $64,782,000
#### A2.3 ICA Servicios (ICAS) — $32,072,400

#### A2.4 Avisos y Tableros (AT)
- **Norma:** Ley 14/1983 art. 37.
- **Cálculo:** `Total_ICA × 0.15`
- **Resultado actual:** $18,351,360

### A3. Sobretasas y Otros Tributarios (Método IPC)

22 rubros usan método IPC. Fórmula común:
```
valor_apropiacion = recaudo_vigencia_anterior × (1 + tasa_ipc)
```

| Rubro | Concepto | Norma | Resultado |
|---|---|---|---:|
| 1.1.01.02.109 | Sobretasa Gasolina | Ley 488/1998 art. 117 | $3,547M |
| 1.3.5.1.1.01.02.212 | Sobretasa Bomberil | Ley 322/1996; Ley 1575/2012 | $786M |
| 1.1.01.02.211 | Alumbrado Público | Ley 1819/2016 art. 350 | $6,448M |
| 1.1.01.02.203 | Circulación y Tránsito | Ley 14/1983 art. 49 | $13M |
| 1.1.01.02.202 | Publicidad Exterior | Ley 140/1994 art. 14 | $0 |
| 1.1.01.02.204 | Delineación | Decreto-Ley 1333/1986 art. 233 | $0 |
| 1.1.02.01.005.64.02 | Contribución Sector Eléctrico | Ley 1819/2016 art. 191 | $174M |
| 1.1.02.03.001.* | Sanciones y multas | Régimen Tributario Territorial | varios |
| 1.1.02.03.002.* | Intereses moratorios | Ley 1066/2006 | varios |
| 1.3.3.1.1.02.01.005.59 | Contribución obras públicas | Ley 1106/2006 art. 6 | $129M |

### A4. Impuesto de Transporte por Oleoductos (1.1.01.02.214)

- **Norma:** Ley 141/1994 art. 26; Decreto 1747/1995.
- **Método:** Promedio últimos 3 años (OLEO).
- **Cálculo:**
  ```
  valor_apropiacion = (recaudo_n3 + recaudo_n2 + recaudo_n1) / 3
  ```
- **Parámetros:** `recaudo_oleoductos_anio_n3`, `n2`, `n1`
- **Resultado actual:** $14,107,935,272

### A5. Estampillas (Método EST)

#### A5.1 Base Estampillas
- **Norma:** Acuerdo Municipal; Decreto 1068/2015.
- **Cálculo:**
  ```
  Base = (POAI − Gasto SEV NC) × % pagos sin SGR
       + (SGR − Gasto SEV SGR) × % pagos SGR
       + Reservas + Cuentas x Pagar + Superávit
  ```
- **Parámetros:** `poai_total_inversion`, `gasto_sev_ppto_nc`, `sgr_presupuesto`, `gasto_sev_sgr`, `pct_pagos_sin_sgr`, `pct_pagos_sgr`, `reservas_presupuestales_nc`, `cuentas_por_pagar_nc`, `superavit_fiscal`

#### A5.2 Distribución 80/20 cada estampilla
- **Norma:** Ley 100/1993 art. 47 (20% al FONPET).
- **Cálculo:**
  ```
  Proyección_total = Base × tarifa_estatuto
  Despacho 80% = Proyección × pct_pagos_despacho
  FONPET 20%  = Proyección × pct_pagos_pensiones
  ```
- **Resultado actual:** $6,301,300,000 total

---

## B. GASTOS — ANEXO 2

### B1. Transferencia al Concejo Municipal (Método OCC)

- **Códigos:** Sección 01 (Concejo) — Rubro 2.1.1.01 y demás
- **Norma:** Ley 136/1994 art. 66; Ley 617/2000 art. 10; Ley 1368/2009; Ley 1551/2012.
- **Cálculo:**
  ```
  Vr Honorarios   = valor_sesion × (ses_ord + ses_extra) × num_concejales
                  = 328,554 × (80+40) × 13
                  = 512,544,934
  % ICLD Adicional = ICLD × pct_icld_adicional_concejo
                  = 26,478,285,205 × 0.015
                  = 397,174,278
  TOTAL CONCEJO   = 909,719,204
  ```
- **Función:** `TablaConcejoPersoneria.calcular_transferencia_concejo()`

### B2. Transferencia a la Personería (Método OCP)

- **Códigos:** Sección 02 (Personería)
- **Norma:** Ley 136/1994 arts. 178-180; **Ley 2461/2025** (progresión cat 5/6); Ley 617/2000.
- **Cálculo (cat 5, vig 2027):**
  ```
  SMLV = 240 (Ley 2461 progresión)
  SMLMV = $1,859,461 (Variables Macro)
  TOTAL PERSONERÍA = 240 × $1,859,461 = $446,270,666
  ```
- **Función:** `TablaConcejoPersoneria.calcular_transferencia_personeria()`

### B3. Planta de Personal (Método CPS)

- **Códigos:** Rubro `2.1.1.01` de cada sección
- **Tabla fuente:** `CostoPersonal`

#### B3.1 Salario Anual
```
salario_anual = salario_basico_mensual × 12
```

#### B3.2 Prestaciones Sociales

| Concepto | Norma | Fórmula |
|---|---|---|
| Prima de Servicios | CST art. 306; Ley 1788/2016 | `sal_anual × 0.0833` |
| Prima de Navidad | Ley 41/1975; Dto 1042/1978 art. 32 | `sal_anual × 0.0833` |
| Vacaciones | Ley 4/1992; Dto 1042/1978 art. 8 | `sal_anual × 0.0417` |
| Prima Vacaciones | Dto 1042/1978 art. 24 | `sal_anual × 0.0417` |
| Cesantías | Ley 50/1990 art. 99 | `sal_anual × 0.0833` |
| Intereses Cesantías | Ley 52/1975 art. 1 | `cesantias × 0.12` |
| Bonif. Servicios Prestados | Dto 1042/1978 art. 45 | `sal_basico × 0.50` |
| Bonif. Recreación | Dto 451/1984 | `sal_anual × 0.0139` |

#### B3.3 Aportes Seguridad Social (Ley 100/1993)

| Concepto | Tarifa | Cálculo |
|---|---:|---|
| Pensión | 12% | `sal_anual × 0.12` |
| Salud | 8.5% | `sal_anual × 0.085` |
| ARL | 0.522% (clase I) | `sal_anual × 0.00522` |

#### B3.4 Aportes Parafiscales (Ley 21/1982)

| Concepto | Tarifa | Cálculo |
|---|---:|---|
| SENA | 2% | `sal_anual × 0.02` |
| ICBF | 3% | `sal_anual × 0.03` |
| Caja Compensación | 4% | `sal_anual × 0.04` |
| ESAP | 0.5% | `sal_anual × 0.005` |
| Escuelas Industriales | 1% | `sal_anual × 0.01` |

#### B3.5 Subsidio de Transporte (Ley 15/1959)

```
si salario_basico_mensual ≤ 2 × SMLMV:
    subsidio_anual = subsidio_transporte_mensual × 12
sino:
    subsidio_anual = 0
```

#### B3.6 Costo Total Anual del Cargo

```
costo_total = (sal_anual
            + Σ prestaciones
            + Σ aportes_ss
            + Σ parafiscales
            + subsidio_transporte) × cantidad
```

#### B3.7 Recálculo Recursivo

Al cambiar **CUALQUIER parámetro** en `/parametros/` o en `/gastos/plantas-personal/`:
1. Se ejecuta `_regenerar_costo_personal(params)`
2. Cada `CostoPersonal` regenera sus 19 campos desde los % de Parámetros
3. `costo_total_anual_override` = suma de todos los componentes
4. `recalcular_rubros_metodo(vigencia)` propaga al rubro `2.1.1.01` de cada sección
5. Anexo 2 muestra los nuevos totales

### B4. Pensionados (Método PEN)

- **Código:** Sección 09 → Rubro de Mesadas Pensionales
- **Norma:** Ley 100/1993 art. 14.
- **Cálculo:**
  ```
  mesada_actual = mesada_anterior × (1 + pct_incremento_pensionados)
  total_anual   = mesada_actual × 14
  ```
- **Parámetros:** `pct_incremento_pensionados` (= IPC del año anterior)
- **Resultado actual:** $241,208,230

### B5. Servicio de Deuda (Métodos DCAP, DINT, DTOT)

- **Códigos:** Sección 03 → `2.2.2.01.02.002.02.03-02` (capital), `2.2.2.02.02.002.02.03-02` (intereses)
- **Norma:** Ley 358/1997; Decreto 696/1998.

#### B5.1 Capital (DCAP)
```
capital_anual = Σ AmortizacionPagare.capital_principal (vigencia_pago = año)
```

#### B5.2 Intereses (DINT)
```
intereses_anual = Σ AmortizacionPagare.intereses (vigencia_pago = año)
```

#### B5.3 Intereses TCR
```
intereses_tcr = intereses × tcr_deuda
              = intereses × 0.921
```

#### B5.4 Total Servicio Deuda (DTOT)
```
total = capital_anual + intereses_anual + intereses_tcr
```

- **Tabla fuente:** `AmortizacionPagare` (40 cuotas trimestrales para 2026-2036)
- **Resultado 2027:** DCAP=$0 (período gracia), DINT=$2,475M

### B6. Indicadores Ley 617/2000

| Indicador | Norma | % Máximo cat 5 |
|---|---|---:|
| Gastos Funcionamiento / ICLD | Ley 617 art. 6 | 75% |
| Concejo / ICLD | Ley 617 art. 10 | 1.5% |
| Personería / ICLD | Ley 617 art. 10 | 220 SMLV |

Configurable en `pct_limite_funcionamiento_ley617`.

### B7. Indicadores Ley 358/1997 (Capacidad Endeudamiento)

| Indicador | Cálculo | Máximo |
|---|---|---:|
| Solvencia | `intereses / ahorro_operacional` | 40% |
| Sostenibilidad | `saldo_deuda / ingresos_corrientes` | 80% |

Configurables en `pct_limite_intereses_ley358`, `pct_limite_saldo_deuda_ley358`.

---

## C. CADENA RECURSIVA DE RECÁLCULO

```
USUARIO modifica parámetro en /parametros/ o /variables-macro/
        │
        ▼
parametros_view.POST() o variables_macro_view.POST()
        │
        ├──► calcular_todos_ingresos(vigencia)
        │       └──► Recalcula Predial, ICA, IPC, POAI, Estampillas, Oleoductos
        │
        ├──► _regenerar_costo_personal(params)
        │       └──► Para cada CostoPersonal regenera 19 campos desde % de ley
        │
        ├──► recalcular_rubros_metodo(vigencia)
        │       ├──► CPS: suma CostoPersonal por sección
        │       ├──► PEN: suma pensionados sección 09
        │       ├──► DCAP/DINT: suma AmortizacionPagare
        │       ├──► OCC: TablaConcejoPersoneria.calcular_transferencia_concejo
        │       └──► OCP: TablaConcejoPersoneria.calcular_transferencia_personeria
        │
        └──► Propaga títulos (calcular_hijos para nivel descendente)
        │
        ▼
Reportes Anexo 1, Anexo 2, Dashboard, Tabla Concejo/Personería actualizados
```

---

## D. CHECKLIST AUDITORÍA

- [ ] Parámetros del Sistema reflejan decretos vigentes (SMLMV, IPC, % aportes).
- [ ] `VariableMacro` tiene datos para los años necesarios (vigencia-1, vigencia, vigencia+1).
- [ ] `TablaConcejoPersoneria` para todas las categorías (0-6) con valores legales.
- [ ] `PersoneriaSMLVProgresion` para vigencia activa y la próxima (Ley 2461/2025).
- [ ] Planta de personal cargada (`CostoPersonal`) para cada sección activa.
- [ ] Amortización del pagaré cargada (`AmortizacionPagare`) para los años de vigencia.
- [ ] Pensionados cargados (`es_pensionado=True`) con mesada año anterior + % incremento.
- [ ] Indicadores Ley 617 y Ley 358 dentro de límites legales.
- [ ] Total rubros HOJA = Total Anexo 1 / Anexo 2.
- [ ] Códigos OCC, OCP, CPS, PEN, DCAP, DINT, IPC, EST, OLEO, PUVA, etc. asignados a los rubros correctos.

---

*Documento técnico-jurídico para uso del Auditor Presupuestal — Municipio de Puerto López.*
