class PersonalMedico:
    """
    Clase que representa al personal médico disponible en el sistema.

    Atributos:
        id_personal (str): Identificador único del personal.
        nombre (str): Nombre del profesional de la salud.
        especialidad (str): Especialidad médica del personal.
        turno (str): Turno de trabajo (mañana, tarde, noche).
        disponible (bool): Indica si el médico está disponible en el momento.
    """

    def __init__(self, id_personal, nombre, especialidad, turno):
        self.id_personal = id_personal
        self.nombre = nombre
        self.especialidad = especialidad
        self.turno = turno
        self.disponible = True  # Por defecto al iniciar el sistema

    def asignar_turno(self, nuevo_turno):
        self.turno = nuevo_turno

    def cambiar_estado(self, estado):
        """
        Cambia la disponibilidad del personal médico.
        Args:
            estado (bool): True si está disponible, False si no.
        """
        self.disponible = estado

    def obtener_info(self):
        return {
            "id": self.id_personal,
            "nombre": self.nombre,
            "especialidad": self.especialidad,
            "turno": self.turno,
            "disponible": self.disponible
        }
