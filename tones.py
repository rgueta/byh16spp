import math

import utime


class Beeper:
    def __init__(self, pin, default_volume=30000):
        self.pin = pin
        self.default_volume = default_volume
        self.notes = {
            # Octava 3
            "C3": 131,
            "C#3": 139,
            "D3": 147,
            "D#3": 156,
            "E3": 165,
            "F3": 175,
            "F#3": 185,
            "G3": 196,
            "G#3": 208,
            "A3": 220,
            "A#3": 233,
            "B3": 247,
            # Octava 4 (base)
            "C4": 262,
            "C#4": 277,
            "D4": 294,
            "D#4": 311,
            "E4": 330,
            "F4": 349,
            "F#4": 370,
            "G4": 392,
            "G#4": 415,
            "A4": 440,
            "A#4": 466,
            "B4": 494,
            # Octava 5
            "C5": 523,
            "C#5": 554,
            "D5": 587,
            "D#5": 622,
            "E5": 659,
            "F5": 698,
            "F#5": 740,
            "G5": 784,
            "G#5": 831,
            "A5": 880,
            "A#5": 932,
            "B5": 988,
            # Octava 6
            "C6": 1047,
            "D6": 1175,
            "E6": 1319,
            "F6": 1397,
            "G6": 1568,
            "A6": 1760,
            "B6": 1976,
            # Efectos
            "SILENCE": 0,
            "CLICK": 2000,
        }

    def tone(self, frequency, duration, volume=None, fade=False):
        """Genera un tono con volumen configurable y opción de fade"""
        if frequency == 0 or frequency is None:
            utime.sleep_ms(duration)
            return

        volume = volume if volume is not None else self.default_volume

        if fade and duration > 50:
            # Fade in y out para tonos suaves
            steps = min(20, duration // 10)
            step_duration = duration // (2 * steps)

            # Fade in
            for i in range(steps):
                vol = int(volume * (i / steps))
                self.pin.freq(frequency)
                self.pin.duty_u16(vol)
                utime.sleep_ms(step_duration)

            # Fade out
            for i in range(steps, 0, -1):
                vol = int(volume * (i / steps))
                self.pin.freq(frequency)
                self.pin.duty_u16(vol)
                utime.sleep_ms(step_duration)
        else:
            self.pin.freq(frequency)
            self.pin.duty_u16(volume)
            utime.sleep_ms(duration)

        self.pin.duty_u16(0)

    def chord(self, frequencies, duration, volume=None):
        """Toca múltiples frecuencias simultáneamente (acorde básico)"""
        # Nota: Para acordes reales se necesitaría múltiples PWM
        # Esta es una simulación tocando las notas rápidamente
        volume = volume if volume is not None else self.default_volume
        step = duration // len(frequencies)

        for freq in frequencies:
            self.tone(freq, step, volume)

    def melody(self, melody_list):
        """Toca una melodía: lista de (frecuencia, duración, volumen_opcional)"""
        for item in melody_list:
            if len(item) == 2:
                freq, duration = item
                self.tone(freq, duration)
            else:
                freq, duration, volume = item
                self.tone(freq, duration, volume)
            utime.sleep_ms(20)  # pequeña pausa entre notas

    # ============ MELODÍAS PRE-DEFINIDAS ============

    def power_on(self):
        """Tono de encendido - alegre y ascendente"""
        melody = [
            ("E5", 150, 45000),
            ("G5", 150, 45000),
            ("B5", 150, 45000),
            ("E6", 300, 50000),
        ]
        for note, duration, vol in melody:
            self.tone(self.notes[note], duration, vol)
        utime.sleep_ms(50)

    def success(self):
        """Éxito - melodía corta y alegre (Super Mario coin)"""
        melody = [
            ("E6", 100, 55000),
            ("E6", 50, 55000),
            ("E6", 50, 55000),
            ("C6", 100, 50000),
            ("E6", 150, 55000),
            ("G6", 250, 60000),
        ]
        for note, duration, vol in melody:
            self.tone(self.notes[note], duration, vol)
            utime.sleep_ms(20)

    def success_short(self):
        """Éxito versión corta"""
        melody = [("E6", 80, 50000), ("C6", 80, 45000), ("G5", 150, 40000)]
        for note, duration, vol in melody:
            self.tone(self.notes[note], duration, vol)

    def error(self):
        """Error - sonido grave descendente"""
        melody = [("C5", 200, 50000), ("G4", 200, 45000), ("E4", 300, 40000)]
        for note, duration, vol in melody:
            self.tone(self.notes[note], duration, vol)

    def error_short(self):
        """Error versión corta (bip)"""
        self.tone(self.notes["C4"], 400, 35000, fade=True)

    def warning(self):
        """Advertencia - sonido intermitente grave"""
        for _ in range(3):
            self.tone(self.notes["A4"], 150, 40000)
            utime.sleep_ms(100)
        self.tone(self.notes["G4"], 150, 40000)

    def notification(self):
        """Notificación suave"""
        self.tone(self.notes["A5"], 100, 25000, fade=True)
        utime.sleep_ms(50)
        self.tone(self.notes["E5"], 100, 25000, fade=True)

    def button_click(self):
        """Click de botón - respuesta táctil"""
        self.tone(self.notes["C6"], 30, 20000)

    def door_open(self):
        """Puerta abierta - sonido ascendente alegre"""
        melody = [("A5", 100, 40000), ("C6", 100, 45000), ("E6", 150, 50000)]
        for note, duration, vol in melody:
            self.tone(self.notes[note], duration, vol)
            utime.sleep_ms(30)

    def door_close(self):
        """Puerta cerrada - sonido descendente"""
        melody = [("E6", 100, 45000), ("C6", 100, 40000), ("A5", 150, 35000)]
        for note, duration, vol in melody:
            self.tone(self.notes[note], duration, vol)
            utime.sleep_ms(30)

    def alarm(self):
        """Alarma - sonido de emergencia"""
        for _ in range(5):
            self.tone(self.notes["E6"], 100, 50000)
            utime.sleep_ms(50)
            self.tone(self.notes["C6"], 100, 50000)
            utime.sleep_ms(50)

    def scan(self):
        """Escanendo - efecto láser (para NFC/códigos)"""
        frequencies = [880, 1175, 1568, 2093, 2637]  # A5, D6, G6, C7, E7
        for freq in frequencies:
            self.tone(freq, 50, 30000, fade=True)
            utime.sleep_ms(30)

    def beep(self, count=1, duration=100, frequency=2000):
        """Bip genérico configurable"""
        for _ in range(count):
            self.tone(frequency, duration, 35000)
            if count > 1:
                utime.sleep_ms(50)

    def melody_initial(self):
        """Melodía inicial (similar a tu 'initial') pero mejorada"""
        melody = [
            (self.notes["F#5"], 200, 45000),  # 1440? ~ F#6? mejor F#5
            (self.notes["D5"], 200, 45000),  # 1150? ~ D6? mejor D5
            (self.notes["F#5"], 200, 45000),  # 1440 de nuevo
            (self.notes["A5"], 300, 50000),  # toque final
        ]
        for freq, duration, vol in melody:
            self.tone(freq, duration, vol)
            utime.sleep_ms(30)

    def melody_fail(self):
        """Sonido de fallo mejorado"""
        # Descendente triste
        melody = [
            (self.notes["E4"], 300, 35000),  # 300ms
            (self.notes["C4"], 300, 30000),  # descenso
            (self.notes["G3"], 400, 25000),  # final grave
        ]
        for freq, duration, vol in melody:
            self.tone(freq, duration, vol, fade=True)
            utime.sleep_ms(50)


# ============ FUNCIONES COMPATIBLES CON TU CÓDIGO EXISTENTE ============

# Inicialización global
beeper = None


def init_buzzer(pin, default_volume=30000):
    """Inicializa el sistema de tonos"""
    global beeper
    beeper = Beeper(pin, default_volume)
    return beeper


# Funciones compatibles con tu código anterior
def tone(pin, frequency, duration):
    """FUNCIÓN ORIGINAL - Mantenida para compatibilidad"""
    pin.freq(frequency)
    pin.duty_u16(30000)  # volumen ajustado
    utime.sleep_ms(duration)
    pin.duty_u16(0)


def song(name, buzzer_pin=None):
    """FUNCIÓN ORIGINAL - Mejorada con nuevas melodías"""
    # Si se inicializó el sistema mejorado, usarlo
    global beeper
    if beeper and beeper.pin == buzzer_pin:
        if name == "initial":
            beeper.melody_initial()
        elif name == "fail":
            beeper.melody_fail()
        elif name == "ok":
            beeper.success_short()
        elif name == "success":
            beeper.success()
        elif name == "error":
            beeper.error()
        elif name == "warning":
            beeper.warning()
        elif name == "click":
            beeper.button_click()
        elif name == "scan":
            beeper.scan()
        elif name == "alarm":
            beeper.alarm()
        elif name == "door_open":
            beeper.door_open()
        elif name == "door_close":
            beeper.door_close()
        elif name == "notification":
            beeper.notification()
        elif name == "power_on":
            beeper.power_on()
        else:
            # Comportamiento original
            if name == "initial":
                tone(buzzer_pin, 1440, 300)
                tone(buzzer_pin, 1150, 300)
                tone(buzzer_pin, 1440, 300)
            elif name == "fail":
                tone(buzzer_pin, 100, 500)
            elif name == "ok":
                tone(buzzer_pin, 1100, 200)
                tone(buzzer_pin, 1500, 200)
    else:
        # Fallback al comportamiento original
        if name == "initial":
            tone(buzzer_pin, 1440, 300)
            tone(buzzer_pin, 1150, 300)
            tone(buzzer_pin, 1440, 300)
        elif name == "fail":
            tone(buzzer_pin, 100, 500)
        elif name == "ok":
            tone(buzzer_pin, 1100, 200)
            tone(buzzer_pin, 1500, 200)
