import pandas as pd
import os
import joblib
import numpy as np
def predecir_tiempo_espera(nuevo_paciente, df_base, carpeta_modelos="modelos_triaje"):
    nivel_triage = nuevo_paciente.get('Nivel_Triage')
    if not nivel_triage:
        return None
    nombre_archivo = f"{carpeta_modelos}/mejor_modelo_triaje_{nivel_triage}.pkl"
    if os.path.exists(nombre_archivo):
        modelo, columnas = joblib.load(nombre_archivo)
        X_nuevo = pd.DataFrame([nuevo_paciente])[list(columnas)]
        prediccion = modelo.predict(X_nuevo)[0]
        return round(prediccion, 1)
    media_triaje = df_base[df_base["Nivel_Triage"] == nivel_triage]["TiempoEspera"].mean()
    if np.isnan(media_triaje):
        media_triaje = df_base["TiempoEspera"].mean()
    return round(media_triaje, 1)
