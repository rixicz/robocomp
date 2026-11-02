import brian.motors as motors
from time import sleep

CM_NA_OTACKU = 10.0 # Kolik cm ujede robot pri 1 otacce motoru

OTACKY_NA_360 = 6.0 # Kolik otacek motoru je potreba k otoceni o 360 stupnu

SMER_LEVY = -1 # dopredu = -1, dozadu = 1
SMER_PRAVY = -1 # dopredu = -1, dozadu = 1
SMER_CELISTI = 1 # otevrit = 1, zavrit = -1

RYCHLOST_JIZDA = 300     # stupne/s (velky motor max 1050)
RYCHLOST_OTACENI = 200   # stupne/s
RYCHLOST_CELISTI = 150   # stupne/s (stredni motor max 1560)
UHEL_CELISTI = 90        # o kolik stupnu motoru se celisti otevrou


motor_l = motors.EV3LargeMotor(motors.MotorPort.B)
motor_r = motors.EV3LargeMotor(motors.MotorPort.C)
celisti = motors.EV3MediumMotor(motors.MotorPort.A)
motor_l.wait_until_ready()
motor_r.wait_until_ready()
celisti.wait_until_ready()


def pasy_rotuj(uhel_l, uhel_r, rychlost):
    """Spusti oba pasy najednou a pocka, az oba dojedou."""
    motor_l.rotate(uhel_l, rychlost, 0) 
    motor_r.rotate(uhel_r, rychlost, 0)
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


def otevri_celisti():
    celisti.rotate(UHEL_CELISTI * SMER_CELISTI, RYCHLOST_CELISTI)


def zavri_celisti():
    celisti.rotate(-UHEL_CELISTI * SMER_CELISTI, RYCHLOST_CELISTI)


# ---------------- PROGRAM ----------------
# Celisti musi byt na zacatku ZAVRENE.
print("Start za 3 s")
sleep(3)

try:
    print("1: Dopredu 20 cm")
    jed_cm(20)

    print("2: Dozadu 20 cm")
    jed_cm(-20)

    print("3: Doprava 90")
    otoc_stupne(90)

    print("4: Doleva 90")
    otoc_stupne(-90)

    print("5: Celisti otevrit")
    otevri_celisti()
    sleep(0.5)

    print("6: Celisti zavrit")
    zavri_celisti()

    print("Hotovo")
finally:
    motor_l.brake()
    motor_r.brake()
    celisti.brake()