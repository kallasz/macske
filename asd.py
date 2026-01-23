import RPi.GPIO as GPIO
import time
import statistics
import asyncio

TRIG = 23
ECHO = 24
GPIO.setmode(GPIO.BCM)
GPIO.setup(TRIG, GPIO.OUT)
GPIO.setup(ECHO, GPIO.IN)
GPIO.output(TRIG, False)
time.sleep(2)
def get_distance():
    # Trigger pulse
    GPIO.output(TRIG, True)
    time.sleep(0.00001)
    GPIO.output(TRIG, False)
    # Echo start
    while GPIO.input(ECHO) == 0:
        pulse_start = time.time()
    # Echo end
    while GPIO.input(ECHO) == 1:
        pulse_end = time.time()
    pulse_duration = pulse_end - pulse_start
    distance = pulse_duration * 17150  # cm
    distance = round(distance, 1)
    return distance
def filter_outliers(samples, max_deviation=30):
    """Remove outliers that differ significantly from median"""
    print(samples.__str__())
    median = sorted(samples)[len(samples) // 2]
    filtered = [x for x in samples if abs(x - median) <= max_deviation]
    return filtered if filtered else samples
last_distance = 0
start_time = time.time()
samples = []
try:
    while True:
        time.sleep(0.1)
        try:
            distance = get_distance()
            if distance is not None:
                samples.append(distance)
            if time.time() - start_time >= 1.0:
                if len(samples) > 0:
                    # Filter outliers before averaging
                    filtered_samples = filter_outliers(samples, max_deviation=10)
                    if len(filtered_samples) > 0:
                        avg_distance = sum(filtered_samples) / len(filtered_samples)
                        avg_distance = round(avg_distance, 1)
                        if abs(last_distance - avg_distance) >= 5:
                            print(f"Átlagolt távolság: {avg_distance} cm (outliers szűrve: {len(samples) - len(filtered_samples)})")
                            last_distance = avg_distance
                    else:
                        print("Minden érték outlier volt")
                samples = []
                start_time = time.time()
        except Exception as e:
          print(e)
except KeyboardInterrupt:
  GPIO.cleanup()
