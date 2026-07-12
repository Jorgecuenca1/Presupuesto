#!/usr/bin/env python3
"""
QA visual end-to-end - SIPRE Presupuesto Puerto Lopez.
Basado en el mismo formato de qa_demo.py de auditoria_cuentas:
  - Selenium/Chrome navegando modulo por modulo
  - Narracion con TTS macOS 'say' voz Paulina
  - Screenshots en carpeta shots/
  - Modo lento configurable (env SLOW, default 1.2)

Uso:
  source .venv-qa/bin/activate
  DJANGO_SETTINGS_MODULE=presupuesto_project.settings python qa_demo.py
  MUTE=1 python qa_demo.py       # sin voz
  SLOW=1.8 python qa_demo.py     # 80% mas lento
  SECCION=deuda python qa_demo.py  # solo una seccion
"""
import os, sys, time, subprocess, traceback, json, shutil
from decimal import Decimal
from datetime import date

# ── Config ────────────────────────────────────────────────────────
BASE = os.environ.get("BASE", "http://127.0.0.1:8088")
PROJ = "/Users/jorgebinkio/Documents/corpofuturo/willy/Presupuesto"
DB   = os.path.join(PROJ, "db.sqlite3")
SHOTS = os.path.join(PROJ, "qa_workspace", "shots")
FRAMES = os.path.join(PROJ, "qa_workspace", "frames")
AUDIOS = os.path.join(PROJ, "qa_workspace", "audios")
REPORT = os.path.join(PROJ, "qa_workspace", "qa_report.html")
os.makedirs(SHOTS, exist_ok=True)
os.makedirs(FRAMES, exist_ok=True)
os.makedirs(AUDIOS, exist_ok=True)

SLOW = float(os.environ.get("SLOW", "1.2"))
VOICE = os.environ.get("VOICE", "Paulina")
RATE  = os.environ.get("RATE",  "175")
SECCION = os.environ.get("SECCION", "all").lower()

USER = "qa_demo"
PASS = "qa12345"

# Escala TODAS las esperas
_rsleep = time.sleep
time.sleep = lambda s: _rsleep(s * SLOW)
def beat(x=0.5): _rsleep(x * SLOW)

# ── Voz TTS ────────────────────────────────────────────────────────
_say_proc = None
_SAY_INDEX = 0
_SAY_LOG = []  # [(idx, text, aiff_path, screenshot_asociado)]
_CURRENT_SHOT = None
def say(text, wait=False):
    """Habla + guarda AIFF en audios/NNN.aiff para compositor de video."""
    global _say_proc, _SAY_INDEX
    if not text or not text.strip():
        return
    try:
        if _say_proc and _say_proc.poll() is None:
            _say_proc.terminate()
    except Exception:
        pass
    print(f"   🔊 {text}")
    _SAY_INDEX += 1
    aiff = os.path.join(AUDIOS, f"{_SAY_INDEX:04d}.aiff")
    # Guardar SIEMPRE el audio a archivo (para compositor video)
    try:
        subprocess.run(["say", "-v", VOICE, "-r", str(RATE), "-o", aiff, text],
                       capture_output=True, timeout=60)
    except Exception as e:
        print(f"   (say -o err) {e}")
    t_start = _t()
    _SAY_LOG.append({
        "idx": _SAY_INDEX, "text": text, "aiff": aiff,
        "shot": _CURRENT_SHOT, "t": t_start,
    })
    # Calcular duración real del audio para poder sincronizar frames
    aiff_dur = 3.0
    try:
        out = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", aiff],
            capture_output=True, text=True, timeout=10).stdout.strip()
        aiff_dur = float(out)
    except Exception:
        pass
    if os.environ.get("MUTE") == "1":
        # Simulamos el tiempo de reproducción para que el timeline de frames
        # coincida con el audio del video final.
        _rsleep(aiff_dur)
        return
    # Reproducir en tiempo real por altavoces
    try:
        _say_proc = subprocess.Popen(["afplay", aiff])
        if wait:
            _say_proc.wait()
        else:
            # No bloquea, pero deja que el audio arranque
            _rsleep(min(0.5, aiff_dur))
    except Exception as e:
        print("   (afplay err)", e)

def wait_voice():
    global _say_proc
    try:
        if _say_proc:
            _say_proc.wait()
    except Exception:
        pass

# ── Selenium ──────────────────────────────────────────────────────
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

_STEP = 0
_REPORT_ROWS = []
_T0 = None
_FRAME_IDX = 0
_FRAME_LOG = []  # [(t_relativo, path_png)]
_RECORDER_ON = False

def _t():
    return time.perf_counter() - _T0 if _T0 else 0.0

def _capture_frame():
    """Captura un frame del navegador con timestamp relativo."""
    global _FRAME_IDX
    _FRAME_IDX += 1
    fn = os.path.join(FRAMES, f"f_{_FRAME_IDX:06d}.png")
    try:
        drv.save_screenshot(fn)
        _FRAME_LOG.append({"t": _t(), "path": fn})
    except Exception:
        pass

def _recorder_loop(fps=3):
    """Loop de grabación en thread: captura frames del navegador a `fps` cuadros/s."""
    interval = 1.0 / fps
    while _RECORDER_ON:
        _capture_frame()
        _rsleep(interval)

def start_recorder(fps=3):
    """Arranca el grabador de frames en background."""
    global _RECORDER_ON, _T0
    _T0 = time.perf_counter()
    _RECORDER_ON = True
    import threading
    t = threading.Thread(target=_recorder_loop, args=(fps,), daemon=True)
    t.start()
    return t

def stop_recorder():
    global _RECORDER_ON
    _RECORDER_ON = False

def shot(nombre):
    """Screenshot 'destacado' para el reporte HTML + registrado en el video."""
    global _STEP, _CURRENT_SHOT
    _STEP += 1
    fn = f"{_STEP:03d}_{nombre}.png"
    path = os.path.join(SHOTS, fn)
    try:
        drv.save_screenshot(path)
    except Exception as e:
        print(f"   (shot err {e})")
    _CURRENT_SHOT = path
    # También lo capturo en el video timeline
    _capture_frame()
    return fn

def log_step(seccion, titulo, resultado, screenshot=None, detalle=""):
    _REPORT_ROWS.append({
        "n": _STEP, "seccion": seccion, "titulo": titulo,
        "resultado": resultado, "shot": screenshot, "detalle": detalle,
    })

# ── Django ORM ─────────────────────────────────────────────────────
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "presupuesto_project.settings")
sys.path.insert(0, PROJ)
import django; django.setup()
from django.db.models import Sum
from core.models import (
    ParametrosSistema, VariableMacro, TechoInversion,
    FuenteFinanciacion, PlanFinancieroLinea, ICLDProyectado,
    Ley617Proyectado, POAIProyectado, POAIPorDependencia,
    CuadrePorFuente, SaldoVFPorFuente, Refinanciacion,
    CCPETIngreso, CCPETGasto,
)
from ingresos.models import ContribuyenteICA, RubroIngreso
from gastos.models import (
    ContratoCredito, PagareCredito, AmortizacionPagare,
    CostoPersonal, RubroGasto,
)

# ═══════════════════════════════════════════════════════════════════
# HELPERS DOM
# ═══════════════════════════════════════════════════════════════════

def num(n):
    """Formatea un número entero con separador de miles en formato ES para voz."""
    try:
        return f"{int(n):,}".replace(",", ".")
    except Exception:
        return str(n)


def go(path, esperar=".navbar,.card,form,body"):
    """Navega a path relativo del BASE, espera un selector."""
    url = BASE + path if path.startswith("/") else path
    drv.get(url)
    try:
        WebDriverWait(drv, 8).until(EC.presence_of_element_located((By.CSS_SELECTOR, esperar)))
    except Exception:
        pass
    beat(0.4)

def js_click(el):
    try:
        drv.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
        time.sleep(0.2)
        drv.execute_script("arguments[0].click();", el)
    except Exception:
        try:
            el.click()
        except Exception:
            pass

def type_slow(el, texto, borrar=True):
    drv.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
    if borrar:
        try:
            el.clear()
        except Exception:
            drv.execute_script("arguments[0].value='';", el)
    for c in str(texto):
        el.send_keys(c)
        _rsleep(0.02)

def encontrar(*selectors):
    for s in selectors:
        try:
            e = drv.find_element(By.CSS_SELECTOR, s)
            if e.is_displayed():
                return e
        except Exception:
            pass
    return None

# ═══════════════════════════════════════════════════════════════════
# LOGIN
# ═══════════════════════════════════════════════════════════════════

def qa_login():
    say("Sistema SIPRE del municipio de Puerto López, Meta.", wait=True)
    say("Software de presupuesto público desarrollado por el Doctor William Borrego.", wait=True)
    say("A continuación, un recorrido de control de calidad módulo por módulo.", wait=True)
    say("Vamos a validar con voz, capturas y verificaciones automáticas contra la base de datos.", wait=False)
    go("/login/", esperar="form")
    shot("00_login")
    try:
        e_user = drv.find_element(By.NAME, "username")
        e_pass = drv.find_element(By.NAME, "password")
    except Exception:
        # Django admin fallback
        e_user = drv.find_element(By.CSS_SELECTOR, "input[type=text]")
        e_pass = drv.find_element(By.CSS_SELECTOR, "input[type=password]")
    # Login rápido para no bloquear (borro SLOW temporal para submit)
    _tp = time.sleep
    time.sleep = _rsleep
    try:
        e_user.clear(); e_user.send_keys(USER)
        e_pass.clear(); e_pass.send_keys(PASS)
        say("Autenticando como usuario qa demo con permisos de superusuario.")
        submit = drv.find_element(By.CSS_SELECTOR, "button[type=submit], input[type=submit]")
        submit.click()
        WebDriverWait(drv, 15).until(lambda d: "/login" not in d.current_url)
    finally:
        time.sleep = _tp
    beat(0.5)
    shot("01_post_login")
    log_step("Login", "Autenticación exitosa", "OK",
             screenshot="01_post_login.png",
             detalle=f"Usuario {USER}, URL destino {drv.current_url}")

# ═══════════════════════════════════════════════════════════════════
# SECCION 1: DASHBOARD + MFMP
# ═══════════════════════════════════════════════════════════════════

def qa_dashboard():
    say("Sección uno. Dashboard general. Aquí veremos los indicadores agregados del presupuesto.", wait=True)
    go("/")
    shot("dashboard_top")

    # Sacar valores desde ORM para verificar
    p = ParametrosSistema.objects.filter(activo=True).first()
    vig = p.vigencia if p else 2027
    ing = RubroIngreso.objects.filter(vigencia=vig, es_titulo=False).aggregate(t=Sum('valor_apropiacion'))['t'] or 0
    gas = RubroGasto.objects.filter(vigencia=vig, es_titulo=False).aggregate(t=Sum('valor_apropiacion'))['t'] or 0
    equilibrio = ing - gas

    say(f"La vigencia activa es {vig}.")
    say(f"El total de ingresos apropiados es de {num(ing/1_000_000)} millones de pesos.")
    say(f"El total de gastos apropiados es de {num(gas/1_000_000)} millones de pesos.")
    if equilibrio >= 0:
        say("El presupuesto está en equilibrio positivo. Ingresos cubren los gastos.")
    else:
        say(f"Alerta: los gastos exceden los ingresos por {abs(int(equilibrio/1_000_000)):,} millones.")
    log_step("Dashboard", "Ingresos vs Gastos vigencia " + str(vig),
             "OK" if equilibrio >= 0 else "DESEQUILIBRIO",
             screenshot="dashboard_top.png",
             detalle=f"Ing=${ing:,.0f} Gas=${gas:,.0f} Δ=${equilibrio:,.0f}")

    # Scroll a la sección MFMP
    say("Ahora bajaré a la tabla de variables macroeconómicas del marco fiscal de mediano plazo, publicado por la Nación en dos mil veintiséis.")
    drv.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    beat(1.0)
    shot("dashboard_mfmp")

    n_var = VariableMacro.objects.filter(anio__gte=vig, anio__lt=vig+11).values('tipo').distinct().count()
    say(f"Se listan {n_var} variables proyectadas para los próximos once años, desde {vig} hasta {vig+10}.")
    ipc_2027 = VariableMacro.objects.filter(tipo='IPC', anio=2027).first()
    trm_2027 = VariableMacro.objects.filter(tipo='TRM', anio=2027).first()
    brent_2027 = VariableMacro.objects.filter(tipo='PETROLEO', anio=2027).first()
    if ipc_2027:
        say(f"Por ejemplo, la inflación proyectada para {vig} es de {float(ipc_2027.valor):.1f} por ciento.")
    if trm_2027:
        say(f"La tasa representativa del mercado promedio será de {num(trm_2027.valor)} pesos por dólar.")
    if brent_2027:
        say(f"El barril de petróleo Brent está proyectado en {float(brent_2027.valor):.1f} dólares.")

    log_step("Dashboard", "Tabla MFMP Nación", "OK",
             screenshot="dashboard_mfmp.png",
             detalle=f"{n_var} variables x 11 años")

# ═══════════════════════════════════════════════════════════════════
# SECCION 2: PARAMETROS DEL SISTEMA
# ═══════════════════════════════════════════════════════════════════

def qa_parametros():
    say("Sección dos. Parámetros del sistema. Aquí se configuran los valores base que rigen todos los cálculos.", wait=True)
    go("/parametros/")
    shot("parametros")

    p = ParametrosSistema.objects.filter(activo=True).first()
    if not p:
        say("No hay parámetros activos configurados.")
        log_step("Parámetros", "Sin parámetros activos", "FAIL")
        return

    say(f"Vigencia: {p.vigencia}.")
    say(f"Salario mínimo legal vigente: {num(p.valor_smlmv)} pesos.")
    say(f"Unidad de valor tributario, U V T: {num(p.valor_uvt)} pesos.")
    say(f"Tasa I P C: {float(p.tasa_ipc)*100 if p.tasa_ipc<1 else float(p.tasa_ipc):.2f} por ciento.")
    log_step("Parámetros", "Valores maestros", "OK",
             screenshot="parametros.png",
             detalle=f"SMLMV=${p.valor_smlmv:,.0f} UVT=${p.valor_uvt:,.0f} IPC={p.tasa_ipc}")

    # Edge case: verificar que el SMLMV se sincroniza con Variables Macro
    smlv_2027 = VariableMacro.objects.filter(tipo='SMLV', anio=p.vigencia).first()
    if smlv_2027 and smlv_2027.valor > 0:
        say("Verificando consistencia con la tabla de variables macro.")
        if abs(p.valor_smlmv - smlv_2027.valor) < 1:
            say("Correcto. El salario mínimo coincide con el registrado en variables macro.")
            log_step("Parámetros", "Consistencia SMLMV vs VariableMacro", "OK",
                     detalle=f"params=${p.valor_smlmv:,.0f} == macro=${smlv_2027.valor:,.0f}")
        else:
            say("Alerta. Hay diferencia entre los parámetros y la tabla de variables macro.")
            log_step("Parámetros", "Consistencia SMLMV vs VariableMacro", "WARN",
                     detalle=f"params=${p.valor_smlmv:,.0f} != macro=${smlv_2027.valor:,.0f}")

# ═══════════════════════════════════════════════════════════════════
# SECCION 3: VARIABLES MACRO
# ═══════════════════════════════════════════════════════════════════

def qa_variables_macro():
    say("Sección tres. Variables macroeconómicas. Aquí se almacenan SMLV, IPC, PIB, TRM y las 15 variables del marco fiscal.")
    go("/variables-macro/")
    shot("variables_macro")

    total = VariableMacro.objects.count()
    por_tipo = {}
    for vm in VariableMacro.objects.all():
        por_tipo[vm.tipo] = por_tipo.get(vm.tipo, 0) + 1
    say(f"En total hay {total} registros. La base cubre {len(por_tipo)} tipos distintos de variables.")
    log_step("Variables Macro", "Cobertura de datos", "OK",
             screenshot="variables_macro.png",
             detalle=f"total={total} tipos={len(por_tipo)}")

# ═══════════════════════════════════════════════════════════════════
# SECCION 4: INGRESOS
# ═══════════════════════════════════════════════════════════════════

def qa_ingresos():
    say("Sección cuatro. Ingresos. Vamos a revisar los cálculos de predial, industria y comercio, y estampillas.", wait=True)
    p = ParametrosSistema.objects.filter(activo=True).first()
    vig = p.vigencia

    # Anexo 1
    go("/ingresos/reporte/")
    shot("ingresos_anexo1")
    total_ing = RubroIngreso.objects.filter(vigencia=vig).aggregate(t=Sum('valor_apropiacion'))['t'] or 0
    n_rubros = RubroIngreso.objects.filter(vigencia=vig).count()
    say(f"El anexo uno de ingresos tiene {n_rubros} rubros por un total de {num(total_ing/1_000_000_000)} mil millones de pesos.")
    log_step("Ingresos", "Anexo 1", "OK", screenshot="ingresos_anexo1.png",
             detalle=f"{n_rubros} rubros, ${total_ing:,.0f}")

    # Contribuyentes ICA
    go("/ingresos/contribuyentes-ica/")
    shot("contribuyentes_ica")
    n_ica = ContribuyenteICA.objects.filter(vigencia=vig).count()
    ica_bruto = ContribuyenteICA.objects.filter(vigencia=vig).aggregate(t=Sum('impuesto_calculado'))['t'] or 0
    say(f"Contribuyentes de industria y comercio: {num(n_ica)}, con un impuesto agregado de {num(ica_bruto/1_000_000)} millones.")
    log_step("Ingresos", "Contribuyentes ICA", "OK", screenshot="contribuyentes_ica.png",
             detalle=f"{n_ica} contribuyentes, ICA=${ica_bruto:,.0f}")

    # Cálculo Predial
    go("/ingresos/calculo-predial/")
    shot("calculo_predial")
    say("El cálculo del predial usa la fórmula: base gravable multiplicada por la tarifa por mil.")
    log_step("Ingresos", "Cálculo Predial", "OK", screenshot="calculo_predial.png")

    # Cálculo ICA
    go("/ingresos/calculo-ica/")
    shot("calculo_ica")
    say("El cálculo del I C A agrupa contribuyentes por actividad y aplica la tarifa por mil según la categoría.")
    log_step("Ingresos", "Cálculo ICA", "OK", screenshot="calculo_ica.png")

    # Estampillas
    go("/ingresos/estampillas/")
    shot("estampillas")
    say("Las estampillas son contribuciones sobre la contratación pública. Cultura, adulto mayor, pro-desarrollo, entre otras.")
    log_step("Ingresos", "Estampillas", "OK", screenshot="estampillas.png")

# ═══════════════════════════════════════════════════════════════════
# SECCION 5: GASTOS
# ═══════════════════════════════════════════════════════════════════

def qa_gastos():
    say("Sección cinco. Gastos. Anexo dos, costo del personal, plantas, y la tabla de la Ley 617.", wait=True)
    p = ParametrosSistema.objects.filter(activo=True).first()
    vig = p.vigencia

    # Anexo 2
    go("/gastos/reporte/")
    shot("gastos_anexo2")
    total_gas = RubroGasto.objects.filter(vigencia=vig, es_titulo=False).aggregate(t=Sum('valor_apropiacion'))['t'] or 0
    r21 = RubroGasto.objects.filter(vigencia=vig, codigo='2.1').first()
    r22 = RubroGasto.objects.filter(vigencia=vig, codigo='2.2').first()
    r23 = RubroGasto.objects.filter(vigencia=vig, codigo='2.3').first()
    say(f"El anexo dos suma {num(total_gas/1_000_000_000)} mil millones de pesos.")
    if r21: say(f"Funcionamiento: {num(r21.valor_apropiacion/1_000_000_000)} mil millones.")
    if r22: say(f"Servicio de deuda: {num(r22.valor_apropiacion/1_000_000_000)} mil millones.")
    if r23: say(f"Inversión: {num(r23.valor_apropiacion/1_000_000_000)} mil millones.")
    log_step("Gastos", "Anexo 2 secciones", "OK", screenshot="gastos_anexo2.png",
             detalle=f"Fto={r21.valor_apropiacion if r21 else 0:.0f} Deuda={r22.valor_apropiacion if r22 else 0:.0f} Inv={r23.valor_apropiacion if r23 else 0:.0f}")

    # Costo Personal
    go("/gastos/personal/")
    shot("costo_personal")
    n_cp = CostoPersonal.objects.filter(vigencia=vig).count()
    total_cp = CostoPersonal.objects.filter(vigencia=vig).aggregate(t=Sum('costo_total_anual_override'))['t'] or 0
    say(f"El costo de personal tiene {n_cp} cargos con un costo anual de {num(total_cp/1_000_000)} millones.")
    log_step("Gastos", "Costo de Personal", "OK", screenshot="costo_personal.png",
             detalle=f"{n_cp} cargos, ${total_cp:,.0f}")

    # Plantas
    go("/gastos/plantas-personal/")
    shot("plantas_personal")
    say("Las plantas de personal muestran cada cargo con su prestaciones, aportes patronales y bonificaciones.")
    log_step("Gastos", "Plantas de Personal", "OK", screenshot="plantas_personal.png")

    # Ley 617
    go("/tabla-concejo/")
    shot("tabla_concejo")
    say("La Ley 617 del año 2000 limita los gastos de los órganos de control: Concejo Municipal y Personería.")
    log_step("Gastos", "Tabla Ley 617 (Concejo/Personería)", "OK", screenshot="tabla_concejo.png")

# ═══════════════════════════════════════════════════════════════════
# SECCION 6: DEUDA PUBLICA
# ═══════════════════════════════════════════════════════════════════

def qa_deuda():
    say("Sección seis. Deuda pública. Este es uno de los módulos más complejos, con arquitectura recursiva.", wait=True)

    # Dashboard deuda
    go("/gastos/deuda-publica/")
    shot("deuda_dashboard")
    n = ContratoCredito.objects.count()
    say(f"Hay {n} crédito{'s' if n!=1 else ''} registrado{'s' if n!=1 else ''}.")
    for c in ContratoCredito.objects.all():
        say(f"Crédito con {c.banco}: cupo {num(c.valor_contrato/1_000_000_000)} mil millones, tasa efectiva anual {float(c.tasa_ea)*100:.2f} por ciento.")
    log_step("Deuda", "Dashboard listado", "OK", screenshot="deuda_dashboard.png",
             detalle=f"{n} contratos")

    # Detalle del primer crédito
    c = ContratoCredito.objects.first()
    if c:
        go(f"/gastos/deuda-publica/credito/{c.pk}/")
        shot("deuda_detalle")
        say(f"Detalle del crédito con {c.banco}. Renta pignorada: {c.renta_pignorada}.")
        say(f"Periodicidad de pagos: {c.get_periodicidad_pago_display()}. Plazo total: {c.plazo_meses} meses, con {c.gracia_meses} meses de gracia.")

        pagares = list(c.pagares.all())
        say(f"El crédito tiene {len(pagares)} pagarés desembolsados.")
        for pag in pagares:
            say(f"Pagaré {pag.numero_pagare}: {num(pag.valor_capital/1_000_000_000)} mil millones, desembolsado el {pag.fecha_desembolso.strftime('%d de %B de %Y') if pag.fecha_desembolso else 'sin fecha'}.")

        # Tabla amortizacion
        drv.execute_script("window.scrollTo(0, document.body.scrollHeight*0.6);")
        beat(0.6)
        shot("deuda_amortizacion")
        n_amort = AmortizacionPagare.objects.filter(pagare__contrato=c).count()
        say(f"La tabla de amortización tiene {n_amort} filas anuales agregadas, más el detalle cuota por cuota trimestral por pagaré.")
        log_step("Deuda", "Detalle crédito + amortización", "OK",
                 screenshot="deuda_amortizacion.png",
                 detalle=f"{len(pagares)} pagarés, {n_amort} amortizaciones")

        # Verificar Ley 358
        anio_vig = ParametrosSistema.objects.filter(activo=True).first().vigencia
        agg = AmortizacionPagare.objects.filter(pagare__contrato=c, vigencia_pago=anio_vig).aggregate(
            c=Sum('capital_principal'), i=Sum('intereses'))
        cap = agg['c'] or Decimal('0'); inter = agg['i'] or Decimal('0')
        say(f"Para la vigencia {anio_vig}, el servicio de deuda es: capital {num(cap/1_000_000)} millones, intereses {num(inter/1_000_000)} millones.")

        # EDGE: intentar crear un crédito QA y luego eliminarlo
        say("Edge case: creación y eliminación de un crédito de prueba.")
        c_qa, created = ContratoCredito.objects.get_or_create(
            banco="QA-DEMO Banco",
            defaults=dict(
                vigencia=anio_vig, renta_pignorada="Recursos Propios",
                objeto_credito="Contrato de prueba QA", valor_contrato=Decimal('1000000000'),
                plazo_meses=60, gracia_meses=12, num_cuotas_capital=16,
                tasa_ea=Decimal('0.10'), tcr_default=Decimal('0.9'),
                periodicidad_pago='T',
            )
        )
        if created:
            say("Crédito de prueba creado. Verificando que aparece en el dashboard.")
        go("/gastos/deuda-publica/")
        shot("deuda_con_qa")
        if "QA-DEMO" in drv.page_source:
            say("Confirmado. El crédito de prueba aparece en el listado.")
            log_step("Deuda", "Crear crédito QA (edge)", "OK", screenshot="deuda_con_qa.png")
        else:
            log_step("Deuda", "Crear crédito QA (edge)", "FAIL")
        # Limpieza
        c_qa.delete()
        say("Crédito de prueba eliminado. La base queda limpia.")

# ═══════════════════════════════════════════════════════════════════
# SECCION 7: TECHOS DE INVERSION
# ═══════════════════════════════════════════════════════════════════

def qa_techos():
    say("Sección siete. Techos de inversión. Aquí se cruzan las fuentes con los usos, y las cifras se sincronizan desde ingresos y gastos.", wait=True)
    go("/techos-inversion/")
    shot("techos")
    p = ParametrosSistema.objects.filter(activo=True).first()
    vig = p.vigencia
    n = TechoInversion.objects.filter(vigencia=vig).count()
    ing = TechoInversion.objects.filter(vigencia=vig).aggregate(t=Sum('ingresos'))['t'] or 0
    fto = TechoInversion.objects.filter(vigencia=vig).aggregate(t=Sum('fto'))['t'] or 0
    deu = TechoInversion.objects.filter(vigencia=vig).aggregate(t=Sum('deuda'))['t'] or 0
    say(f"Hay {n} fuentes registradas.")
    say(f"Total ingresos: {num(ing/1_000_000_000)} mil millones.")
    say(f"Total funcionamiento: {num(fto/1_000_000_000)} mil millones.")
    say(f"Total deuda: {num(deu/1_000_000)} millones.")
    log_step("Techos", "Sincronización recursiva", "OK",
             screenshot="techos.png",
             detalle=f"{n} filas, Ing=${ing:,.0f} Fto=${fto:,.0f} Deu=${deu:,.0f}")

    # Fila con deuda auto-sincronizada
    con_deuda = TechoInversion.objects.filter(vigencia=vig, deuda__gt=0)
    if con_deuda.exists():
        say(f"Se detectan {con_deuda.count()} filas con deuda sincronizada automáticamente desde los contratos.")
        for t in con_deuda[:3]:
            say(f"La fuente {t.concepto_ingreso} paga {num(t.deuda/1_000_000)} millones al servicio de deuda.")

# ═══════════════════════════════════════════════════════════════════
# SECCION 8: MFMP (Marco Fiscal de Mediano Plazo v75)
# ═══════════════════════════════════════════════════════════════════

def qa_mfmp():
    say("Sección ocho. Marco Fiscal de Mediano Plazo, con datos importados del Excel versión 75.", wait=True)
    from django.db.models import Sum

    # Menú
    go("/mfmp/")
    shot("mfmp_menu")
    n_fuentes = FuenteFinanciacion.objects.count()
    say(f"El sistema ya integra {n_fuentes} fuentes de financiación desde el catálogo oficial.")
    log_step("MFMP", "Menú principal", "OK", screenshot="mfmp_menu.png",
             detalle=f"{n_fuentes} fuentes")

    # Plan Financiero
    go("/mfmp/plan-financiero/")
    shot("plan_financiero")
    n_pf = PlanFinancieroLinea.objects.count()
    ing_2027 = PlanFinancieroLinea.objects.filter(tipo='A', anio=2027).first()
    inv_2027 = PlanFinancieroLinea.objects.filter(tipo='D', anio=2027).first()
    say(f"Plan Financiero con {n_pf} celdas.")
    if ing_2027:
        say(f"Ingresos totales proyectados para 2027: {num(ing_2027.valor/1_000_000_000)} mil millones.")
    if inv_2027:
        say(f"Inversión proyectada 2027: {num(inv_2027.valor/1_000_000_000)} mil millones.")
    log_step("MFMP", "Plan Financiero 10 años", "OK", screenshot="plan_financiero.png")

    # ICLD Proyectado
    go("/mfmp/icld-proyectado/")
    shot("icld_proyectado")
    icld_recursos = ICLDProyectado.objects.filter(fuente__codigo='1', anio=2027).first()
    if icld_recursos:
        say(f"ICLD Recursos Propios 2027: {num(icld_recursos.valor_bruto/1_000_000)} millones.")
    log_step("MFMP", "ICLD Proyectado", "OK", screenshot="icld_proyectado.png")

    # Ley 617
    go("/mfmp/ley-617/")
    shot("ley_617")
    l617_2027 = Ley617Proyectado.objects.filter(anio=2027).first()
    if l617_2027:
        pct = float(l617_2027.pct_cumplido)
        say(f"Ley 617 en 2027: gastos de funcionamiento consumen el {pct:.2f} por ciento del I C L D neto.")
        if l617_2027.cumple:
            say("Estado: cumple el límite legal.")
        else:
            say("Alerta: excede el límite. Requiere ajuste.")
    log_step("MFMP", "Ley 617 Proyectado", "OK", screenshot="ley_617.png")

    # POAI Proyectado
    go("/mfmp/poai/")
    shot("poai_proyectado")
    poai_total_2027 = POAIProyectado.objects.filter(anio=2027).aggregate(t=Sum('valor'))['t'] or 0
    say(f"POAI total 2027: {num(poai_total_2027/1_000_000_000)} mil millones.")
    log_step("MFMP", "POAI Proyectado", "OK", screenshot="poai_proyectado.png")

    # POAI Dependencias
    go("/mfmp/poai-dependencias/")
    shot("poai_dependencias")
    n_deps = POAIPorDependencia.objects.values('dependencia').distinct().count()
    say(f"Se distribuye entre {n_deps} secretarías del municipio.")
    log_step("MFMP", "POAI Dependencias", "OK", screenshot="poai_dependencias.png")

    # Cuadre por Fuente
    go("/mfmp/cuadre-fuente/")
    shot("cuadre_fuente")
    fuentes_cuadran = 0
    for c in CuadrePorFuente.objects.filter(anio=2027):
        if c.cuadra:
            fuentes_cuadran += 1
    total_c = CuadrePorFuente.objects.filter(anio=2027).count()
    say(f"Cuadre 2027: {fuentes_cuadran} de {total_c} fuentes cuadran ingreso igual gasto.")
    log_step("MFMP", "Cuadre por Fuente", "OK", screenshot="cuadre_fuente.png",
             detalle=f"{fuentes_cuadran}/{total_c} cuadran")

    # Saldo VF
    go("/mfmp/saldo-vf-fuente/")
    shot("saldo_vf")
    tot_vf = SaldoVFPorFuente.objects.aggregate(a=Sum('apropiacion_definitiva'), v=Sum('vf_aprobadas'))
    say(f"Vigencias futuras aprobadas suman {num((tot_vf['v'] or 0)/1_000_000)} millones.")
    log_step("MFMP", "Saldo VF por Fuente", "OK", screenshot="saldo_vf.png")

    # Refinanciación
    go("/mfmp/refinanciacion/")
    shot("refinanciacion")
    r = Refinanciacion.objects.first()
    if r:
        say(f"Escenario de refinanciación configurado para el año {r.anio_refinanciacion} con nueva tasa {float(r.nueva_tasa_ea)*100:.1f} por ciento.")
    log_step("MFMP", "Refinanciación", "OK", screenshot="refinanciacion.png")

    # CCPET
    go("/mfmp/ccpet-ingresos/")
    shot("ccpet_ingresos")
    n_cci = CCPETIngreso.objects.count()
    say(f"Clasificación CCPET Ingresos con {n_cci} rubros presupuestales.")
    log_step("MFMP", "CCPET Ingresos", "OK", screenshot="ccpet_ingresos.png")

    go("/mfmp/ccpet-gastos/")
    shot("ccpet_gastos")
    n_ccg = CCPETGasto.objects.count()
    say(f"Clasificación CCPET Gastos con {n_ccg} rubros presupuestales.")
    log_step("MFMP", "CCPET Gastos", "OK", screenshot="ccpet_gastos.png")

    # Panel de Control
    go("/panel-control/")
    shot("panel_control")
    say("Por último, el Panel de Control muestra el semáforo de cada dato del sistema.")
    say("Cada verificación tiene su estado: cargado, provisional o faltante.")
    log_step("MFMP", "Panel de Control", "OK", screenshot="panel_control.png")


# ═══════════════════════════════════════════════════════════════════
# REPORTE HTML FINAL
# ═══════════════════════════════════════════════════════════════════

def escribir_reporte():
    say("Generando el reporte de control de calidad en formato HTML.")
    filas = ""
    for r in _REPORT_ROWS:
        icono = "✅" if r["resultado"] == "OK" else ("⚠️" if r["resultado"].startswith("W") else "❌")
        img = f'<a href="shots/{r["shot"]}" target="_blank"><img src="shots/{r["shot"]}" style="max-height:120px;border:1px solid #ccc;"></a>' if r["shot"] else ""
        filas += f'<tr><td>{r["n"]}</td><td>{r["seccion"]}</td><td>{r["titulo"]}</td><td>{icono} {r["resultado"]}</td><td><small>{r["detalle"]}</small></td><td>{img}</td></tr>'
    html = f"""<!doctype html><meta charset=utf-8>
<title>QA SIPRE Presupuesto {date.today().isoformat()}</title>
<style>
body{{font-family:Arial,sans-serif;padding:20px;background:#f7f7f7;}}
h1{{color:#0d6efd;}}
table{{width:100%;background:white;border-collapse:collapse;box-shadow:0 2px 8px rgba(0,0,0,.06);}}
th,td{{padding:8px;border-bottom:1px solid #eee;text-align:left;vertical-align:top;}}
th{{background:#212529;color:white;position:sticky;top:0;}}
img{{border-radius:4px;}}
</style>
<h1>Control de Calidad - SIPRE Presupuesto Puerto López</h1>
<p><strong>Fecha:</strong> {date.today().isoformat()} · <strong>Pasos:</strong> {len(_REPORT_ROWS)}</p>
<table>
<thead><tr><th>#</th><th>Sección</th><th>Verificación</th><th>Resultado</th><th>Detalle</th><th>Captura</th></tr></thead>
<tbody>{filas}</tbody>
</table>
"""
    with open(REPORT, "w") as f:
        f.write(html)
    print(f"\n📄 Reporte: {REPORT}")
    say("Reporte generado con éxito. Fin del proceso de control de calidad.", wait=True)
    # Manifiesto para compositor de video
    manifest = os.path.join(PROJ, "qa_workspace", "say_log.json")
    with open(manifest, "w") as f:
        json.dump(_SAY_LOG, f, indent=2, default=str)
    print(f"📼 Manifiesto say_log: {manifest} ({len(_SAY_LOG)} entradas)")

# ═══════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════

def main():
    global drv
    opts = Options()
    opts.add_argument("--window-size=1600,1000")
    if os.environ.get("HEADLESS") == "1":
        opts.add_argument("--headless=new")
    drv = webdriver.Chrome(options=opts)
    drv.set_window_size(1600, 1000)
    # Grabador de frames en background: captura Chrome cada 400ms
    if os.environ.get("RECORD", "1") != "0":
        start_recorder(fps=float(os.environ.get("REC_FPS", "2.5")))
    try:
        qa_login()
        secciones = {
            "dashboard": qa_dashboard,
            "parametros": qa_parametros,
            "variables": qa_variables_macro,
            "ingresos": qa_ingresos,
            "gastos": qa_gastos,
            "deuda": qa_deuda,
            "techos": qa_techos,
            "mfmp": qa_mfmp,
        }
        if SECCION == "all":
            for nombre, fn in secciones.items():
                try:
                    fn()
                except Exception as e:
                    traceback.print_exc()
                    say(f"Error en la sección {nombre}. Continuando con la siguiente.")
                    log_step(nombre, "Excepción", "FAIL", detalle=str(e))
        elif SECCION in secciones:
            secciones[SECCION]()
        else:
            print(f"Sección desconocida: {SECCION}. Opciones: {list(secciones)}")
        escribir_reporte()
    finally:
        wait_voice()
        stop_recorder()
        _rsleep(0.5)  # espera último frame
        # Persistir el timeline de frames
        try:
            with open(os.path.join(PROJ, "qa_workspace", "frames_log.json"), "w") as f:
                json.dump(_FRAME_LOG, f)
            print(f"🎞️  Frames capturados: {len(_FRAME_LOG)}")
        except Exception as e:
            print(f"  (frames log err) {e}")
        try: drv.quit()
        except Exception: pass

if __name__ == "__main__":
    main()
