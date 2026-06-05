# Fundamento Legal de los Cálculos Presupuestales

> Documento explicativo de cada método de cálculo automático implementado en
> el sistema, con el sustento jurídico colombiano vigente.
> Municipio de Puerto López — categoría 5 (quinta) — Vigencia 2026.

Este documento sirve como **memoria técnica administrativa** equivalente a la
que prepararía un funcionario de la Secretaría de Hacienda Municipal al
sustentar la proyección de ingresos y gastos del presupuesto anual.

---

## Marco General

| Norma | Materia |
|---|---|
| **Constitución Política, arts. 287, 313, 339, 345-352** | Autonomía territorial, ciclo presupuestal |
| **Decreto 111 de 1996** (Estatuto Orgánico del Presupuesto) | Principios y procedimiento presupuestal |
| **Ley 152 de 1994** | Ley Orgánica del Plan de Desarrollo (POAI) |
| **Ley 617 de 2000** | Saneamiento fiscal y límites de gastos |
| **Ley 715 de 2001** y reformas (Acto Leg. 04/2007, Ley 1176/2007) | Sistema General de Participaciones |
| **Ley 819 de 2003** | Responsabilidad y transparencia fiscal — Marco Fiscal de Mediano Plazo |
| **Ley 1551 de 2012** | Categorización municipal |
| **Decreto 1068 de 2015 (DUR Hacienda)** | Reglamentación del presupuesto |

Principio rector: **Principio de Programación Integral** (Art. 38 Dto. 111/1996):
> "Todo programa presupuestal deberá contemplar simultáneamente los gastos de
> inversión y de funcionamiento que las exigencias técnicas y administrativas
> demanden como necesarios para su ejecución y operación".

---

## INGRESOS

### 1. Impuesto Predial Unificado — Métodos PUVA / PUAN / PRVA / PRAN

**Fundamento:**
- **Ley 44 de 1990**, art. 1: creación del Impuesto Predial Unificado.
- **Ley 1430 de 2010**, art. 23: actualización catastral.
- **Acuerdo Municipal de Puerto López** (Estatuto Tributario Municipal): tarifas por rango UVT y categoría predial.
- **Ley 1066 de 2006**: gestión de cartera y recuperación de vigencias anteriores.

**Fórmula implementada** (`ingresos/utils.py:calcular_predial`):

```
Para cada categoría (UV, UC, UI, UEF, RU, PE, PNE, UNUE, UNEU, UNNU):
  Recaudo potencial = Σ(avalúo × tarifa_por_mil / 1000)
  Proyección       = Recaudo potencial × % Eficiencia Recaudo × Factor crecimiento
```

- **% Eficiencia Recaudo**: parámetro editable (`pct_eficiencia_recaudo`). Refleja el promedio histórico de cobro real sobre el potencial (concepto "cultura de pago"). Justificación: Art. 3° Ley 819/2003 — proyección creíble respaldada en histórico.
- **Factor crecimiento viviendas** (sólo categoría UV — Urbano Vivienda): `1 + pct_crecimiento_viviendas`. Recoge el efecto del crecimiento poblacional/edilicio (Acuerdo Municipal).

**Vigencias anteriores (cartera)**:
```
Proyección = Cartera × (% Base / 100) × (% Urbano|Rural / 100)
```
Sustento: Ley 1066/2006, Art. 12 — recuperación gradual basada en histórico de pagos.

### 2. Impuesto de Industria y Comercio (ICA) — Métodos ICAI / ICAC / ICAS

**Fundamento:**
- **Ley 14 de 1983**, arts. 32-40: ICA.
- **Ley 1819 de 2016**, art. 343: territorialidad del ICA.
- **Acuerdo Municipal**: tarifas por código de actividad (industrial, comercial, servicios).

**Fórmula**:
```
Ingresos proyectados (por contribuyente) = Ingresos brutos × (1 + tasa_pib_nominal)
Impuesto calculado = Ingresos proyectados × tarifa_por_mil / 1000
```

El factor `(1 + PIB nominal)` proyecta el crecimiento de la base gravable.
Sustento: Marco Fiscal de Mediano Plazo (Ley 819/2003, art. 5) — supuestos macroeconómicos.

### 3. Avisos y Tableros (AT) — 15% del ICA

**Fundamento:**
- **Ley 14 de 1983**, art. 37: complementario de ICA.
- Tarifa fija del **15%** del valor del ICA.

### 4. Sobretasas, multas, sanciones, intereses — Método IPC

**Fundamento general:**
- **Art. 38 Decreto 111/1996** (Principio de Programación Integral): proyección debe ser consistente con histórico ajustado.
- **Ley 819/2003, art. 4**: Marco Fiscal — supuestos de inflación (IPC) del Banco de la República.

**Rubros que aplican IPC en este sistema y su sustento específico:**

| Rubro | Norma | IPC justificación |
|---|---|---|
| Sobretasa ambiental | Ley 99/1993 art. 44 | Crece con la base predial → IPC |
| Sobretasa a la gasolina | Ley 488/1998 art. 117; Ley 681/2001 | Recaudo se proyecta vía histórico ajustado por IPC |
| Sobretasa bomberil | Ley 322/1996 art. 2; Ley 1575/2012 | Idem (acuerdo municipal) |
| Publicidad exterior visual | Ley 140/1994 art. 14 | Acuerdo municipal — IPC |
| Circulación y tránsito | Ley 14/1983 art. 49 | IPC sobre histórico |
| Delineación urbana | Decreto-Ley 1333/1986 art. 233 | IPC |
| Alumbrado público | Ley 1819/2016 art. 350-353 | Crece con consumo → IPC |
| Cigarrillos (departamental cedida) | Ley 1819/2016 art. 211 | IPC |
| Contribución Sector Eléctrico | Ley 1819/2016 art. 191 | IPC |
| Estratificación | Ley 142/1994 art. 11.7 | IPC |
| Multas, sanciones, intereses moratorios | Régimen Tributario Territorial; Ley 1066/2006 | Proyección por IPC (no son tributos, son accesorios) |
| Contribución especial sobre contratos | Ley 1106/2006 art. 6; Ley 1738/2014 | 5% sobre valor contratos públicos — IPC |
| Multas Código Nacional de Seguridad y Convivencia | Ley 1801/2016 | IPC |

**Fórmula**:
```
valor_apropiacion = recaudo_vigencia_anterior × (1 + tasa_ipc)
```

`recaudo_vigencia_anterior` se backfilleó como `valor_actual / (1 + tasa_ipc)`
para preservar el valor inicial. A partir de allí, cualquier cambio en
`tasa_ipc` (parametros del sistema) propaga al recalcular.

### 5. Impuesto de Transporte por Oleoductos — Método OLEO (promedio 3 años)

**Fundamento:**
- **Ley 141 de 1994** art. 26: Impuesto de Transporte por Oleoductos y Gasoductos a favor de los municipios productores.
- **Decreto 1747/1995** reglamentación.
- **Ley 1530/2012** (SGR) — destinación.

**Justificación del método del promedio 3 años:**
La base gravable es el volumen real transportado, altamente volátil. El
**Manual de Programación Presupuestal del DNP** y la práctica generalizada
en municipios productores recomienda **proyectar por promedio simple de los
últimos 3 años** para neutralizar picos coyunturales (precio internacional,
declaratoria de fuerza mayor, paros, etc.) en lugar de ajustar por IPC.

**Fórmula**:
```
valor_apropiacion = (recaudo_n3 + recaudo_n2 + recaudo_n1) / 3
```

### 6. Estampillas (Procultura, Adulto Mayor, etc.) — Método EST

**Fundamento:**
- **Ley 397/1997** art. 38 (Procultura).
- **Ley 1276/2009** (Adulto Mayor).
- **Ley 100/1993** art. 47: **20% al FONPET** (Fondo de Pensiones).
- **Decreto 1068/2015** art. 2.12.1.1.4: distribución 80%/20%.
- **Acuerdo Municipal**: definición de tarifa y rubros pignorados.

**Fórmula**:
```
Base estampillas = (POAI − Gasto SEV NC) × % pagos sin SGR
                 + (SGR − Gasto SEV SGR) × % pagos SGR
                 + Reservas + Cuentas x Pagar + Superávit
Proyección estampilla = Base × tarifa estatuto tributario
Distribución:
  80% → Despacho/Secretarías (codigo_rubro de la estampilla)
  20% → Fondo Pensiones (1.3.6.x) — Art. 47 Ley 100/1993
```

### 7. SGP — Método ICN (no usado actualmente, listo para activar)

**Fundamento:**
- **Ley 715 de 2001** y Acto Legislativo 04 de 2007.
- **Ley 1176 de 2007**.

**Fórmula**:
```
valor = recaudo_vigencia_anterior × (1 + tasa_icn)
```
Donde `tasa_icn` = tasa de crecimiento de los Ingresos Corrientes de la Nación
proyectada por el DNP / Min. Hacienda (Conpes Social).

---

## GASTOS — ANEXO 6 ÓRGANOS DE CONTROL

### 8. Transferencia al Concejo Municipal — Método OCC

**Fundamento:**
- **Ley 136 de 1994** art. 66: honorarios de los concejales.
- **Ley 617 de 2000** art. 10: límite máximo de gastos de los concejos.
- **Ley 1368 de 2009**: modifica art. 66 Ley 136 — valor de los honorarios.
- **Ley 1551 de 2012** art. 20: número de sesiones según categoría.

**Fórmula implementada** (`core/models.py:calcular_transferencia_concejo`):
```
Vr Honorarios       = valor_sesion × (sesiones_ord + sesiones_extra) × num_concejales
% ICLD Adicional    = ICLD × pct_icld_adicional_concejo
Total Transferencia = Vr Honorarios + % ICLD Adicional
```

**Parámetros por categoría municipal (Ley 1551/2012 y 1368/2009):**

| Categoría | Sesiones Ord | Sesiones Ext | Concejales | Valor sesión* |
|---|---|---|---|---|
| Especial | 150 | 40 | 19 | $757.771 |
| 1ª | 150 | 40 | 17 | $717.999 |
| 2ª | 150 | 40 | 15 | $518.983 |
| 3ª | 80 | 40 | 15 | $416.306 |
| 4ª | 80 | 40 | 13 | $348.256 |
| **5ª (Puerto López)** | **80** | **40** | **13** | **$348.256** |
| 6ª | 80 | 40 | 13 | $348.256 |

\* Valor 2026 actualizado por SMLDV vigente.

**Porcentaje adicional ICLD (1.5%)**: corresponde al concepto de
financiación adicional reglamentado por **Decreto 1955/2024** (sustituye
parágrafos de Ley 617) para gastos de funcionamiento del Concejo más allá
de los honorarios.

### 9. Transferencia a la Personería Municipal — Método OCP

**Fundamento:**
- **Ley 136 de 1994** arts. 178 y 180: organización y gastos de la Personería.
- **Ley 617 de 2000** art. 10: límite máximo.
- **Ley 1551 de 2012** art. 35: financiación según categoría.
- **Ley 2461 de 2025**: incremento progresivo de SMLV para Personerías en cat. 5 y 6.
- **Ley 2422 de 2024**: ajustes complementarios.

**Fórmula** (varía por categoría):

| Categoría | Fórmula | Norma |
|---|---|---|
| Especial | ICLD × 1.6% | Ley 617/2000 art. 10 |
| 1ª | ICLD × 1.7% | Ley 617/2000 art. 10 |
| 2ª | ICLD × 2.2% | Ley 617/2000 art. 10 |
| 3ª | 400 SMLV | Ley 617/2000 art. 10 / Ley 1551/2012 |
| 4ª | 330 SMLV | Ley 617/2000 art. 10 / Ley 1551/2012 |
| **5ª (Puerto López)** | **SMLV de la progresión Ley 2461/2025 × SMLMV** | **Ley 2461/2025** |
| 6ª | 0 SMLV | Ley 617/2000 art. 10 (asumido por presupuesto municipal global) |

**Progresión Ley 2461 de 2025 (categoría 5):**
| Vigencia | SMLV |
|---|---|
| 2025 | 210 |
| **2026** | **220** |
| 2027 | 230 |
| 2028 | 240 |
| 2029 | 250 |

Justificación legal: la Ley 2461 estableció el incremento gradual de la
financiación de las Personerías de municipios de 5ª y 6ª categoría para
fortalecer la defensa de los derechos humanos en estos territorios,
empezando en 2025 con 210 SMLV y subiendo 10 SMLV por año hasta 2029.

**Cálculo para Puerto López vigencia 2026:**
```
220 SMLV × $1.750.905 (SMLMV 2026) = $385.199.100
```

---

## GASTOS — SERVICIO DE LA DEUDA

### 10. Capital de Banca Comercial — Método DCAP
### 11. Intereses de Banca Comercial — Método DINT
### 12. Total Deuda — Método DTOT (capital + intereses + TCR)

**Fundamento:**
- **Ley 358 de 1997** y Ley 1483/2011: endeudamiento territorial — capacidad de pago.
- **Decreto 696/1998**.
- **Acuerdo Municipal** que aprueba el contrato de empréstito y su plan de amortización.

**Fórmula**:
```
DCAP = Σ AmortizacionPagare.capital_principal (vigencia)
DINT = Σ AmortizacionPagare.intereses        (vigencia)
DTOT = DCAP + DINT + Σ AmortizacionPagare.intereses_tcr
```

Los valores se cargan automáticamente desde la tabla de amortización del
pagaré asociado al ContratoCredito. Cuando no hay amortizaciones cargadas
para la vigencia, el monto queda en $0 (el método sigue aplicándose, pero
con base cero; al cargar el pagaré se actualiza).

**Asignación actual** (`fix_metodos_gastos.py`):
- `2.2.2.01.02.002.02.03-02 Banca comercial` → DCAP
- `2.2.2.02.02.002.02.03-02 Banca comercial` → DINT

---

## GASTOS — PERSONAL

### 13. Costo Personal por Sección — Método CPS
### 14. Pensionados — Método PEN

**Fundamento:**
- **Decreto 1083 de 2015** (Función Pública): planta de personal.
- **Decreto Salarial Anual** (incremento salarial mínimo).
- **Ley 100 de 1993** y reformas: seguridad social.
- **Ley 4 de 1992**: régimen salarial.

**Fórmula**:
```
CPS = Σ CostoPersonal.costo_total_anual (es_pensionado=False, mismo seccion_id)
PEN = Σ CostoPersonal.costo_total_anual (es_pensionado=True, vigencia)
```

Esto reemplaza el monto manual del rubro por la suma exacta de planta
cargada en `CostoPersonal`. Cuando no hay personal cargado, el monto queda
en $0 hasta que se importe la planta.

---

## RUBROS QUE NO SE PROYECTAN POR REGLA AUTOMÁTICA (MAN)

Los siguientes conceptos **NO** se proyectan automáticamente porque tienen
fuentes externas de información o son asignaciones discrecionales:

| Concepto | Razón legal |
|---|---|
| SGP Educación, Salud, Agua, Libre Inversión, Cultura, Deporte | Asignados por **CONPES Social** y Resolución del Min. Hacienda. Valores fijos por vigencia. |
| Régimen Subsidiado, Rentas Cedidas | Resolución Min. Salud / Min. Hacienda. |
| Coljuegos S.S.F. / C.S.F. | Distribución por Resolución Coljuegos. |
| Cuotas partes pensionales / FONPET | Liquidación por Min. Hacienda. |
| Banca comercial (cupo de crédito) | Acuerdo Municipal que aprueba el empréstito. |
| Cancelación de Reservas, Superávit Fiscal, Reintegros | Cierre fiscal del año anterior — valor real. |
| Aportes Nación (CONPES alimentación, aseguramiento) | Documento CONPES vigente. |

Para todos estos se conserva el valor que digite manualmente la
Secretaría de Hacienda (`metodo_calculo = MAN`), porque ninguna fórmula
genérica puede sustituir la fuente oficial.

---

## Resumen ejecutivo

| Método | Norma principal | % ingresos automáticos |
|---|---|---|
| Predial | Ley 44/1990, Ley 1066/2006 | 24,6 B (≈17,8%) |
| ICA + AT | Ley 14/1983, Ley 1819/2016 | 130 M (≈0,1%) |
| IPC (sobretasas, multas, intereses) | Dto. 111/1996 art. 38, Ley 819/2003 | 26,4 B (≈19,1%) |
| Estampillas (EST) | Ley 397/1997, Ley 1276/2009, Ley 100/1993 art. 47 | 6,3 B (≈4,5%) |
| Oleoductos (OLEO) | Ley 141/1994 | 14,1 B (≈10,2%) |
| **Total proyectado automáticamente** | | **≈51,6%** |

El resto (SGP, Regímenes especiales, Banca, etc.) son valores manuales por
disposición legal expresa que requieren fuente externa oficial.

---

*Documento generado como soporte técnico-jurídico para la Secretaría de
Hacienda del Municipio de Puerto López — Vigencia Fiscal 2026.*
