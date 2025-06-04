# configuracion.py
import json
import os
class ConfiguracionTiempos:
    def __init__(self, modo="OPS"):
        """
        Inicializa los tiempos por nivel de triaje.
        :param modo: "OPS" para tiempos estándar o "Personalizado" si el admin define los tiempos.
        """
        if modo == "OPS":
            self.tiempos = {
                'I': 5,    # minutos
                'II': 15,
                'III': 60,
                'IV': 120,
                'V': 240
            }
        else:
            self.tiempos = {}  # El administrador debe definirlos luego

    def definir_tiempo(self, nivel_triaje, minutos):
        """
        Permite al administrador configurar el tiempo para un nivel específico.
        """
        if nivel_triaje in ['I', 'II', 'III', 'IV', 'V']:
            self.tiempos[nivel_triaje] = minutos
        else:
            raise ValueError("Nivel de triaje no válido. Use I, II, III, IV o V.")

    def obtener_tiempo_limite(self, nivel_triaje):
        """
        Devuelve el tiempo máximo de espera permitido para el nivel dado.
        """
        return self.tiempos.get(nivel_triaje, None)

    def mostrar_configuracion(self):

        return self.tiempos
    
    def guardar_tiempos_personalizados(self, archivo="tiempos_personalizados.json"):
        with open(archivo, "w", encoding="utf-8") as f:
            json.dump(self.tiempos, f)

    def cargar_tiempos_personalizados(self, archivo="tiempos_personalizados.json"):
        if os.path.exists(archivo):
            with open(archivo, "r", encoding="utf-8") as f:
                self.tiempos = json.load(f)
            return True
        return False

