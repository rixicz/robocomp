import brian.motors as motors
import brian.sensors as sensors
from time import sleep, time

CM_NA_OTACKU = 13.3  # Kolik cm ujede robot pri 1 otacce motoru

SMER_LEVY = -1   # dopredu = -1, dozadu = 1
SMER_PRAVY = -1  # dopredu = -1, dozadu = 1

RYCHLOST_JIZDA = 620     # stupne/s (realny limit motoru B je asi 650)
RYCHLOST_CELISTI = 450   # stupne/s (stredni motor max 1560)

# --- Jizda ---
MIN_RYCHLOST = 100     # rychlost na zacatku a na konci jizdy (stupne/s)
ROZJEZD_STUPNE = 200   # na kolika stupnich otocky se robot rozjizdi
BRZDENI_STUPNE = 300   # na kolika stupnich otocky pred cilem zpomaluje
PERIODA = 0.01         # jak casto se regulace pocita (s)
LOGOVAT = True         # po jizde vypise ladici data

# --- Drzeni smeru podle gyra (pri jizde) ---
KP_SMER = 10.0         # (stupne/s) na 1 stupen odchylky smeru; pri kmitani snizit
MAX_KOREKCE = 0.3      # korekce nikdy nepresahne 30 % aktualni rychlosti

# --- Otaceni podle gyra ---
GYRO_KP = 4.0            # (stupne/s) na 1 stupen chyby
GYRO_MAX = 250           # max rychlost otaceni (stupne/s)
GYRO_MIN = 40            # min rychlost, aby se pasy vubec rozjely
GYRO_TOLERANCE = 1       # povolena chyba ve stupnich
GYRO_TIMEOUT = 6.0       # max doba jednoho pokusu o otoceni (s)


motor_l = motors.EV3LargeMotor(motors.MotorPort.B)
motor_r = motors.EV3LargeMotor(motors.MotorPort.C)
celisti = motors.EV3MediumMotor(motors.MotorPort.A)
motor_l.wait_until_ready()
motor_r.wait_until_ready()
celisti.wait_until_ready()

gyro = sensors.EV3.GyroSensorEV3(sensors.SensorPort.S1)
gyro.wait_until_ready()

_posledni_uhel = 0
SMER_CIL = 0     # cilovy smer robota (stupne, kladne = doprava)


def uhel_gyro():
    """Vraci uhel tak, ze kladne = doprava. Ignoruje ojedinele nulove chybne cteni."""
    global _posledni_uhel
    a = -gyro.angle()
    if a == 0 and abs(_posledni_uhel) > 10:
        # skok z velke hodnoty rovnou na 0 je podezrely -> precti znovu
        for _ in range(3):
            sleep(0.005)
            a = -gyro.angle()
            if a != 0:
                break
        else:
            a = _posledni_uhel      # porad nula -> pouzij posledni dobrou hodnotu
    _posledni_uhel = a
    return a


def nuluj_smer():
    """Aktualni smer robota prohlasi za cilovy (zavolej na zacatku programu)."""
    global SMER_CIL
    SMER_CIL = uhel_gyro()


def pasy_rychlost(v):
    """v > 0 = otaceni doprava na miste, v < 0 = doleva."""
    motor_l.run_at_speed(int(v * SMER_LEVY))
    motor_r.run_at_speed(int(-v * SMER_PRAVY))


def zastav():
    motor_l.brake()
    motor_r.brake()


def otoc_gyro(stupne):
    """Presne otoceni podle gyra. Kladne = doprava, zaporne = doleva.
    Otaci se k absolutnimu cili (SMER_CIL + stupne), takze se chyby nescitaji."""
    global SMER_CIL
    SMER_CIL += stupne

    for pokus in range(3):                       # max 3 dorovnani
        t0 = time()
        while time() - t0 < GYRO_TIMEOUT:
            chyba = SMER_CIL - uhel_gyro()
            if abs(chyba) <= GYRO_TOLERANCE:
                break
            v = GYRO_KP * chyba
            v = max(min(v, GYRO_MAX), -GYRO_MAX)
            if abs(v) < GYRO_MIN:
                v = GYRO_MIN if v > 0 else -GYRO_MIN
            pasy_rychlost(v)
            sleep(0.01)
        zastav()
        sleep(0.3)                               # nech robota dojet
        if abs(SMER_CIL - uhel_gyro()) <= GYRO_TOLERANCE:
            break


def jed_cm(cm):
    """Kladne cm = dopredu, zaporne = dozadu.
    Plynula jizda, smer se drzi podle gyra (SMER_CIL).
    Konci, az prumer obou pasu ujede celou vzdalenost."""
    smer = 1 if cm >= 0 else -1
    cil = abs(cm) / CM_NA_OTACKU * 360   # cilovy uhel kazdeho motoru (kladny)

    motor_l.reset_angle(0)
    motor_r.reset_angle(0)
    log = []

    while True:
        # ujete stupne, kladne = ve smeru jizdy
        ujeto_l = motor_l.current_angle() * SMER_LEVY * smer
        ujeto_r = motor_r.current_angle() * SMER_PRAVY * smer
        prumer = (ujeto_l + ujeto_r) / 2.0

        if prumer >= cil:
            break

        zbyva = cil - prumer

        # zakladni rychlost: plynuly rozjezd a zpomaleni pred cilem
        rozjezd = min(1.0, max(0.0, prumer / ROZJEZD_STUPNE))
        brzdeni = min(1.0, zbyva / BRZDENI_STUPNE)
        v = MIN_RYCHLOST + (RYCHLOST_JIZDA - MIN_RYCHLOST) * min(rozjezd, brzdeni)

        # korekce smeru: chyba_smeru > 0 = robot se stocil doprava
        chyba_smeru = uhel_gyro() - SMER_CIL
        korekce = min(abs(KP_SMER * chyba_smeru), MAX_KOREKCE * v)
        # pri couvani se smysl korekce obraci, proto nasobime 'smer'
        potreba = smer * chyba_smeru
        v_l = v - korekce if potreba > 0 else v    # zpomal levy pas -> zatoc doleva
        v_r = v - korekce if potreba < 0 else v    # zpomal pravy pas -> zatoc doprava

        if LOGOVAT:
            log.append((int(prumer), int(chyba_smeru), int(v)))

        motor_l.run_at_speed(int(v_l * SMER_LEVY * smer))
        motor_r.run_at_speed(int(v_r * SMER_PRAVY * smer))
        sleep(PERIODA)

    zastav()
    sleep(0.3)

    if LOGOVAT:
        print('cil', int(cil), 'konec L/R',
              motor_l.current_angle() * SMER_LEVY * smer,
              motor_r.current_angle() * SMER_PRAVY * smer)
        print('odchylka smeru na konci:', uhel_gyro() - SMER_CIL, 'stupnu')
        print('(ujeto, chyba_smeru, rychlost)')
        for i in range(0, len(log), 10):
            print(log[i])


# když se motor točí dozadu, tak se čelisti otevřou
def zavrit_prsty():
    celisti.rotate(-600, RYCHLOST_CELISTI)  # směr je relativně zbytečný, bohatě stačí minus


def skladani():
    celisti.rotate(-270, RYCHLOST_CELISTI)


def otevrit_stack():
    celisti.rotate(530, RYCHLOST_CELISTI)


# ---------------- PROGRAM ----------------
# Celisti musi byt na zacatku ZAVRENE.
# Prvni 3 s s robotem nehybej (ustaleni gyra).

sleep(3)
nuluj_smer()

print('--- jizda rovne 100 cm ---')
jed_cm(100)

print('--- otoceni o 180 ---')
otoc_gyro(180)
print('odchylka od ciloveho smeru:', uhel_gyro() - SMER_CIL, 'stupnu')

print('--- jizda zpet 100 cm ---')
jed_cm(100)

otoc_gyro(180)
print('hotovo, odchylka od ciloveho smeru:', uhel_gyro() - SMER_CIL, 'stupnu')