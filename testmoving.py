import brian.motors as motors
from time import sleep

CM_NA_OTACKU = 13.3  # Kolik cm ujede robot pri 1 otacce motoru

OTACKY_NA_360 = 6.0  # Kolik otacek motoru je potreba k otoceni o 360 stupnu

SMER_LEVY = -1   # dopredu = -1, dozadu = 1
SMER_PRAVY = -1  # dopredu = -1, dozadu = 1

RYCHLOST_JIZDA = 620     # stupne/s (reálný limit motoru B je asi 650; vyšší hodnota nic nepřidá)
RYCHLOST_OTACENI = 200   # stupne/s
RYCHLOST_CELISTI = 450   # stupne/s (stredni motor max 1560)

# --- Regulace primeho smeru jizdy ---
KP = 8.0               # sila korekce: (stupne/s) na 1 stupen rozdilu poloh
MAX_KOREKCE = 0.3      # korekce nikdy nepresahne 30 % aktualni rychlosti
MIN_RYCHLOST = 100     # rychlost na zacatku a na konci jizdy (stupne/s)
ROZJEZD_STUPNE = 200   # na kolika stupnich otocky se robot rozjizdi
BRZDENI_STUPNE = 300   # na kolika stupnich otocky pred cilem zpomaluje
PERIODA = 0.01         # jak casto se regulace pocita (s)
LOGOVAT = True         # po jizde vypise rozdil poloh motoru (pro ladeni)


motor_l = motors.EV3LargeMotor(motors.MotorPort.B)
motor_r = motors.EV3LargeMotor(motors.MotorPort.C)
celisti = motors.EV3MediumMotor(motors.MotorPort.A)
motor_l.wait_until_ready()
motor_r.wait_until_ready()
celisti.wait_until_ready()


def pasy_rotuj(uhel_l, uhel_r, rychlost):
    """Spusti oba pasy najednou a pocka, az oba dojedou (pro otaceni na miste)."""
    motor_l.rotate(uhel_l, rychlost, 0)
    motor_r.rotate(uhel_r, rychlost, 0)
    motor_l.wait_until_done()
    motor_r.wait_until_done()
    motor_l.brake()
    motor_r.brake()
    sleep(0.3)


def jed_cm(cm):
    """Kladne cm = dopredu, zaporne = dozadu.
    Plynula jizda bez zastavovani. Kazdy motor ma vlastni cil a zabrzdi,
    az kdyz sam ujede celou vzdalenost -> na konci neni zadne vychyleni."""
    smer = 1 if cm >= 0 else -1
    cil = abs(cm) / CM_NA_OTACKU * 360   # cilovy uhel kazdeho motoru (kladny)

    motor_l.reset_angle(0)
    motor_r.reset_angle(0)
    hotovo_l = False
    hotovo_r = False
    log = []

    while True:
        # ujete stupne, kladne = ve smeru jizdy
        ujeto_l = motor_l.current_angle() * SMER_LEVY * smer
        ujeto_r = motor_r.current_angle() * SMER_PRAVY * smer

        if not hotovo_l and ujeto_l >= cil:
            motor_l.brake()
            hotovo_l = True
        if not hotovo_r and ujeto_r >= cil:
            motor_r.brake()
            hotovo_r = True
        if hotovo_l and hotovo_r:
            break

        prumer = (ujeto_l + ujeto_r) / 2.0
        zbyva = max(0.0, cil - prumer)

        # zakladni rychlost: plynuly rozjezd a zpomaleni pred cilem
        rozjezd = min(1.0, max(0.0, prumer / ROZJEZD_STUPNE))
        brzdeni = min(1.0, zbyva / BRZDENI_STUPNE)
        v = MIN_RYCHLOST + (RYCHLOST_JIZDA - MIN_RYCHLOST) * min(rozjezd, brzdeni)

        # korekce: zpomaluje se jen ten motor, ktery je napred
        chyba = ujeto_l - ujeto_r          # > 0 = levy je napred
        korekce = min(abs(KP * chyba), MAX_KOREKCE * v)
        v_l = v - korekce if chyba > 0 else v
        v_r = v - korekce if chyba < 0 else v

        if LOGOVAT:
            log.append((int(prumer), int(chyba), int(v)))

        if not hotovo_l:
            motor_l.run_at_speed(int(v_l * SMER_LEVY * smer))
        if not hotovo_r:
            motor_r.run_at_speed(int(v_r * SMER_PRAVY * smer))
        sleep(PERIODA)

    sleep(0.3)

    if LOGOVAT:
        print('cil', int(cil), 'konec L/R', motor_l.current_angle() * SMER_LEVY * smer,
              motor_r.current_angle() * SMER_PRAVY * smer)
        print('ujeto, chyba(L-R), rychlost')
        for i in range(0, len(log), 10):
            print(log[i])


def otoc_stupne(stupne):
    """Kladne stupne = doprava na miste, zaporne = doleva."""
    uhel = int(stupne * OTACKY_NA_360)  # (stupne/360) * otacky * 360
    pasy_rotuj(uhel * SMER_LEVY, -uhel * SMER_PRAVY, RYCHLOST_OTACENI)


# když se motor točí dozadu, tak se čelisti otevřou
def zavrit_prsty():
    celisti.rotate(-600, RYCHLOST_CELISTI)  # směr je relativně zbytečný, bohatě stačí minus


def skladani():
    celisti.rotate(-270, RYCHLOST_CELISTI)


def otevrit_stack():
    celisti.rotate(530, RYCHLOST_CELISTI)


# ---------------- PROGRAM ----------------
# Celisti musi byt na zacatku ZAVRENE.

# Test primeho smeru: jed 200 cm a koukni se, kam robot ujel.
jed_cm(200)