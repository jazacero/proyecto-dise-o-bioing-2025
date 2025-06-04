import heapq
from datetime import datetime

class GestorColas:
    def __init__(self, tiempos_limite):
        """
        tiempos_limite: dict {'I': 0, 'II': 30, 'III': 60, 'IV': 120, 'V': 240}
        """
        self.tiempos_limite = tiempos_limite
        self.cola = []  # (prioridad_tuple, contador, paciente)
        self.contador = 0

    def prioridad_paciente(self, paciente):
        
        t_espera = paciente.tiempo_espera()
        t_limite = self.tiempos_limite.get(paciente.nivel_triaje, 9999)
        nivel_num = {"I": 0, "II": 1, "III": 2, "IV": 3, "V": 4}[paciente.nivel_triaje]  # menor es más urgente
        exceso = t_espera - t_limite  # positivo = ya excedió, negativo = aún está a tiempo

        # 1. Nivel de triage
        # 2. Ya excedió (0=ya excedió, 1=no ha excedido)
        # 3. Si ya excedió: más excedido (-exceso) es más urgente (más negativo)
        #    Si no ha excedido: menor margen (t_limite-t_espera) es más urgente
        # 4. Orden de llegada

        if exceso >= 0:
            # Ya excedió el tiempo: más negativo (-exceso) más urgente
            criterio = (nivel_num, 0, -exceso, self.contador)
        else:
            # No ha excedido: menor margen, más urgente
            criterio = (nivel_num, 1, t_limite - t_espera, self.contador)
        return criterio

    def agregar_paciente(self, paciente):
        prioridad = self.prioridad_paciente(paciente)
        heapq.heappush(self.cola, (prioridad, self.contador, paciente))
        self.contador += 1

    def siguiente_paciente(self):
        # Recalcular prioridades antes de atender
        self.reevaluar_cola()
        if self.cola:
            _, _, paciente = heapq.heappop(self.cola)
            paciente.registrar_atencion(datetime.now())
            return paciente
        return None

    def obtener_paciente_por_indice(self, index):
        if 0 <= index < len(self.cola):
            return self.cola[index][2]
        return None

    def eliminar_paciente(self, paciente_objetivo):
        self.cola = [
            (prioridad, contador, p) for prioridad, contador, p in self.cola
            if p != paciente_objetivo
        ]
        heapq.heapify(self.cola)

    def reevaluar_cola(self):
        nueva_cola = []
        for _, _, paciente in self.cola:
            prioridad = self.prioridad_paciente(paciente)
            nueva_cola.append((prioridad, self.contador, paciente))
            self.contador += 1
        self.cola = nueva_cola
        heapq.heapify(self.cola)
