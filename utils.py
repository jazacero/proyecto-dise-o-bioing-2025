from datetime import datetime

def verificar_alerta_tiempo(paciente, tiempos_limite):
    """
    Verifica si el paciente ha superado el tiempo límite de espera.
    """
    tiempo_espera = paciente.tiempo_espera()
    max_espera = tiempos_limite.get(paciente.nivel_triaje, 999)
    return tiempo_espera > max_espera

def generar_alerta(paciente, tiempos_limite):
    """
    Devuelve un mensaje de alerta si el paciente ha superado su tiempo límite.
    """
    if verificar_alerta_tiempo(paciente, tiempos_limite):
        return f"ALERTA: Paciente {paciente.nombre} (Triage {paciente.nivel_triaje}) ha superado el tiempo límite de espera."
    return None

def sugerir_reevaluacion(paciente, tiempos_limite):
    """
    Sugiere reevaluar al paciente si ha superado su tiempo de espera.
    """
    if verificar_alerta_tiempo(paciente, tiempos_limite):
        return f"Reevaluación sugerida para {paciente.nombre} (Triage {paciente.nivel_triaje})."
    return None

def calcular_cumplimiento(pacientes_atendidos, tiempos_limite):
    """
    Calcula el porcentaje de pacientes atendidos dentro del tiempo límite por nivel de triaje.
    """
    resultados = {}
    triaje_total = {}

    for paciente in pacientes_atendidos:
        nivel = paciente.nivel_triaje
        if nivel not in resultados:
            resultados[nivel] = 0
            triaje_total[nivel] = 0

        triaje_total[nivel] += 1
        if paciente.tiempo_espera() <= tiempos_limite.get(nivel, 999):
            resultados[nivel] += 1

    cumplimiento = {
        nivel: round((resultados[nivel] / triaje_total[nivel]) * 100, 2)
        for nivel in resultados
    }
    return cumplimiento

def estimar_tiempo_restante(paciente, tiempos_limite):
    """
    Estima cuánto tiempo queda antes de que se incumpla el tiempo de triaje.
    """
    tiempo_espera = paciente.tiempo_espera()
    tiempo_max = tiempos_limite.get(paciente.nivel_triaje, 999)
    restante = tiempo_max - tiempo_espera
    return max(0, round(restante, 2))  # en minutos

def estado_alerta(paciente, tiempos_limite):
    """
    Retorna el estado de alerta (verde, amarillo o rojo) según el porcentaje del tiempo cumplido.
    """
    tiempo_espera = paciente.tiempo_espera()
    tiempo_max = tiempos_limite.get(paciente.nivel_triaje, 999)

    if tiempo_espera > tiempo_max:
        return "rojo"
    elif tiempo_espera > 0.7 * tiempo_max:
        return "amarillo"
    else:
        return "verde"
