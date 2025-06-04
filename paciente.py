from datetime import datetime

class Paciente:
    def __init__(self, nombre, nivel_triaje, edad=None, sexo=None, id_paciente=None,
                 signos_vitales=None, ingreso=None, hora_atencion=None):
        self.id_paciente = id_paciente
        self.nombre = nombre
        self.edad = edad
        self.sexo = sexo
        self.nivel_triaje = nivel_triaje
        self.signos_vitales = signos_vitales or {}  
        self.ingreso = ingreso if ingreso else datetime.now()
        self.hora_atencion = hora_atencion  # ← se usa para registro real
        self.hora_atencion_simulada = None  # ← se mantiene para simulación
        self.reevaluaciones = 0

    def tiempo_espera(self, ahora=None):
        ahora = ahora or datetime.now()
        return (ahora - self.ingreso).total_seconds() / 60

    def registrar_atencion(self, ahora=None):
        ahora = ahora or datetime.now()
        self.hora_atencion = ahora  # ← hora real de atención
        self.hora_atencion_simulada = ahora  # ← opcionalmente también como simulada

    def agregar_reevaluacion(self):
        self.reevaluaciones += 1

    def to_dict(self):
        return {
            "nombre": self.nombre,
            "nivel_triaje": self.nivel_triaje,
            "edad": self.edad,
            "sexo": self.sexo,
            "id_paciente": self.id_paciente,
            "signos_vitales": self.signos_vitales,
            "hora_ingreso": self.ingreso.isoformat(),
            "hora_atencion": self.hora_atencion.isoformat() if self.hora_atencion else None
        }

    def __str__(self):
        return f"{self.nombre} (Triage {self.nivel_triaje}) - Espera: {round(self.tiempo_espera(), 1)} min - Reeval: {self.reevaluaciones}"
