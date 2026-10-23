import brian.motors as motors
import brian.pilot as pilot
import brian.audio as audio

motor_left = motors.EV3LargeMotor(motors.MotorPort.A)
motor_right = motors.EV3LargeMotor(motors.MotorPort.B)


p = pilot.Pilot(motor_left, motor_right, 160, 42)
mm = p.distance_travelled_mm()
angle = 90
p.turn(0, int(angle * 1.85))
audio.play_tone(3000, 200000)
audio.play_tone(200, 2000)
