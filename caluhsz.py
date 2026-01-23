import RPi.GPIO as GPIO
import time

def calibrate_sensor():
    """Place sensor at known distances and find calibration factor"""
    TRIG = 23
    ECHO = 24
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(TRIG, GPIO.OUT)
    GPIO.setup(ECHO, GPIO.IN)
    GPIO.output(TRIG, False)
    time.sleep(2)
    
    def get_raw_distance():
        GPIO.output(TRIG, True)
        time.sleep(0.00001)
        GPIO.output(TRIG, False)
        
        pulse_start = None
        pulse_end = None
        timeout = time.time() + 0.1
        
        while GPIO.input(ECHO) == 0:
            pulse_start = time.time()
            if time.time() > timeout:
                return None
        
        while GPIO.input(ECHO) == 1:
            pulse_end = time.time()
            if time.time() > timeout:
                return None
        
        if pulse_start is None or pulse_end is None:
            return None
        
        pulse_duration = pulse_end - pulse_start
        return pulse_duration * 17150
    
    print("Kalibráció - Helyezd a szenzort ismert távolságra...")
    print("15 cm-re helyezve, nyomj Entert:")
    input()
    
    samples = []
    for _ in range(10):
        dist = get_raw_distance()
        if dist:
            samples.append(dist)
        time.sleep(0.1)
    
    avg_measured = sum(samples) / len(samples)
    actual_distance = 15  # cm
    
    calibration_factor = actual_distance / avg_measured
    print(f"Mért átlag: {avg_measured:.1f} cm")
    print(f"Valós távolság: {actual_distance} cm")
    print(f"Kalibráció faktor: {calibration_factor:.4f}")
    print(f"Használd ezt a kódban: calibration_factor = {calibration_factor:.4f}")
    
    GPIO.cleanup()

calibrate_sensor()