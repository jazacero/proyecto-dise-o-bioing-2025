import pandas as pd
import numpy as np
import os
import joblib
from xgboost import XGBRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.preprocessing import LabelEncoder

# --- CONFIGURACIÓN ---
DATASET = "historico_atenciones.csv"      # Cambia el nombre si tu archivo se llama distinto
CARPETA_MODELOS = "modelos_triaje"
os.makedirs(CARPETA_MODELOS, exist_ok=True)

# --- 1. Cargar y limpiar datos ---
df = pd.read_csv(DATASET, encoding="utf-8")

# Convertir fechas a datetime
df['HoraIngreso'] = pd.to_datetime(df['HoraIngreso'], errors='coerce')
df['HoraAtencion'] = pd.to_datetime(df['HoraAtencion'], errors='coerce')

# Calcular tiempo de espera si está en texto
if df['TiempoEspera'].dtype == object:
    # Intenta convertir a numérico, si falla, calcula
    try:
        df['TiempoEspera'] = pd.to_numeric(df['TiempoEspera'], errors='coerce')
    except:
        df['TiempoEspera'] = (df['HoraAtencion'] - df['HoraIngreso']).dt.total_seconds() / 60

# Quitar filas sin tiempo de espera o triage
df = df.dropna(subset=['TiempoEspera', 'Nivel_Triage'])

# --- 2. Procesar variables categóricas ---

# Codificar Nivel_Triage como numérico (I-V)
triage_map = {'I': 1, 'II': 2, 'III': 3, 'IV': 4, 'V': 5}
df['Triage_Code'] = df['Nivel_Triage'].map(triage_map)

# Codificar 'Dia' como número de día de la semana
dias_letras = ['L', 'MA', 'MI', 'JU', 'VI', 'SA', 'DO']
df['Dia_Num'] = df['Dia'].apply(lambda x: dias_letras.index(x) if x in dias_letras else np.nan)

# Variables de hora y mes
df['Hora'] = df['HoraIngreso'].dt.hour
df['Mes'] = df['Mes'].astype(int)

# Rellenar faltantes numéricos (si existen)
for col in ['MedicosTurno', 'EnfermerosTurno', 'EspecialistasTurno', 'PacientesEnCola']:
    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)

# --- 3. Selección de variables ---
features = [
    'Triage_Code',      # Codificación de triage (importante para dividir luego)
    'Hora',
    'Mes',
    'Dia_Num',
    'MedicosTurno',
    'EnfermerosTurno',
    'EspecialistasTurno',
    'PacientesEnCola'
]
X_all = df[features]
y_all = df['TiempoEspera']

# --- 4. Entrenamiento y evaluación por nivel de triage ---
resultados = []

for nivel_str, nivel_num in triage_map.items():
    print(f"\nEntrenando para Triage {nivel_str}...")
    # Subconjunto solo de ese triage
    sub = df[df['Triage_Code'] == nivel_num].copy()
    if len(sub) < 10:
        print(f"  No hay suficientes muestras para este triage. Saltando.")
        continue
    X = sub[[
        'Hora', 'Mes', 'Dia_Num',
        'MedicosTurno', 'EnfermerosTurno', 'EspecialistasTurno', 'PacientesEnCola'
    ]]
    y = sub['TiempoEspera']

    # Train/Test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    # Entrenar modelo XGBoost
    modelo = XGBRegressor(
        n_estimators=200,
        max_depth=7,
        learning_rate=0.05,
        subsample=0.8,
        random_state=42,
        objective='reg:squarederror'
    )
    modelo.fit(X_train, y_train)

    # Predicciones y métricas
    y_pred = modelo.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)

    print(f"  MAE: {mae:.2f} min | R²: {r2:.2f}")

    # Guardar modelo entrenado
    joblib.dump((modelo, X.columns), f"{CARPETA_MODELOS}/modelo_triaje_{nivel_str}.pkl")
    resultados.append((nivel_str, mae, r2))

# --- 5. Mostrar resultados finales ---
print("\nResumen métricas por nivel de triage:")
for nivel, mae, r2 in resultados:
    print(f" Triage {nivel}: MAE={mae:.2f} min | R²={r2:.2f}")

# --- 6. (Opcional) Visualización general ---
try:
    import matplotlib.pyplot as plt
    import seaborn as sns
    plt.figure(figsize=(8,6))
    for nivel_str, nivel_num in triage_map.items():
        sub = df[df['Triage_Code'] == nivel_num]
        if len(sub) > 0:
            plt.hist(sub['TiempoEspera'], bins=25, alpha=0.4, label=f"Triage {nivel_str}")
    plt.xlabel("Tiempo de espera (min)")
    plt.ylabel("Cantidad de pacientes")
    plt.title("Distribución tiempo de espera por nivel de triage")
    plt.legend()
    plt.show()
except ImportError:
    pass  # Si no tienes matplotlib, solo ignora esto

