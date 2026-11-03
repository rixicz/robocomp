import brian.motors as motors
from time import sleep

CM_NA_OTACKU = 13 # Kolik cm ujede robot pri 1 otacce motoru

OTACKY_NA_360 = 6.0 # Kolik otacek motoru je potreba k otoceni o 360 stupnu

SMER_LEVY = -1 # dopredu = -1, dozadu = 1
SMER_PRAVY = -1 # dopredu = -1, dozadu = 1

RYCHLOST_JIZDA = 300     # stupne/s (velky motor max 1050)
RYCHLOST_OTACENI = 200   # stupne/s
RYCHLOST_CELISTI = 450   # stupne/s (stredni motor max 1560)
OTEVRENI_CELISTI = -180     # o kolik stupnu motoru se celisti otevrou
ZAVRENI_CELISTI = 500          # klidně tam dát overkill těch otáček, u toho robota se stává, že, když jede, tak se mu čelisti trochu otevřou

motor_l = motors.EV3LargeMotor(motors.MotorPort.B)
motor_r = motors.EV3LargeMotor(motors.MotorPort.C)
celisti = motors.EV3MediumMotor(motors.MotorPort.A)
motor_l.wait_until_ready()
motor_r.wait_until_ready()
celisti.wait_until_ready()


def pasy_rotuj(uhel_l, uhel_r, rychlost):
    """Spusti oba pasy najednou a pocka, az oba dojedou."""
    motor_l.rotate(uhel_l, rychlost, 0) 
    motor_r.rotate(uhel_r, rychlost, 0) # tady možná bude potřeba něco měnit, protože při 2 metrech jízdy se vozidlo nepatrně vychýlí doprava
    motor_l.wait_until_done()
    motor_r.wait_until_done()
    motor_l.brake()
    motor_r.brake()
    sleep(0.3)


def jed_cm(cm):
    """Kladne cm = dopredu, zaporne = dozadu."""
    uhel = int(cm / CM_NA_OTACKU * 360)
    pasy_rotuj(uhel * SMER_LEVY, uhel * SMER_PRAVY, RYCHLOST_JIZDA)


def otoc_stupne(stupne):
    """Kladne stupne = doprava na miste, zaporne = doleva."""
    uhel = int(stupne * OTACKY_NA_360)  # (stupne/360) * otacky * 360
    pasy_rotuj(uhel * SMER_LEVY, -uhel * SMER_PRAVY, RYCHLOST_OTACENI)

# když se motor točí dozadu, tak se čelisti otevřou
def otevri_celisti():
    celisti.rotate(OTEVRENI_CELISTI, RYCHLOST_CELISTI) # směr je relativně zbytečný bohatě stačí minus


def zavri_celisti():
    celisti.rotate(ZAVRENI_CELISTI, RYCHLOST_CELISTI)


# ---------------- PROGRAM ----------------
# Celisti musi byt na zacatku ZAVRENE.
print("Start za 3 s")
sleep(3)

try:
    jed_cm(200)
    jed_cm(-200)


finally:
    motor_l.brake()
    motor_r.brake()
    celisti.brake()