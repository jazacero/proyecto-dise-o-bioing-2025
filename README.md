
# Plataforma Inteligente para la Gestión Prioritaria y Predicción de Tiempos de Espera en Urgencias Hospitalarias

## Descripción del proyecto

Esta plataforma fue desarrollada como proyecto académico para la materia **Proyecto de Diseño en Bioingeniería** en la Pontificia Universidad Javeriana, primer semestre de 2025. El objetivo principal es optimizar la atención en servicios de urgencias hospitalarias, mediante la priorización inteligente de pacientes y la predicción dinámica de los tiempos de espera, utilizando algoritmos avanzados de gestión de colas, alertas clínicas automatizadas y modelos de machine learning. La solución está diseñada para apoyar al personal de salud en la toma de decisiones, reducir los tiempos de espera para los pacientes más críticos y mejorar la eficiencia, seguridad y equidad en la gestión de urgencias, adaptándose a la normativa colombiana y las necesidades reales de los hospitales.

## Funcionalidades principales

- **Gestión dinámica de colas y priorización de pacientes:** Algoritmo que garantiza la atención prioritaria de los pacientes más urgentes (niveles I, II y III), reorganizando la cola en tiempo real y minimizando los incumplimientos regulatorios.
- **Notificaciones y alertas de reevaluación:** Generación automática de alertas visuales tipo semáforo y sugerencias de reevaluación clínica, tanto por proximidad a los límites de espera como por detección de signos vitales críticos.
- **Módulo de predicción de tiempos de espera:** Integración de modelos de machine learning (XGBoost) para estimar el tiempo de espera de cada paciente según variables contextuales y clínicas.
- **Interfaz gráfica intuitiva:** Sistema basado en Tkinter para el registro, edición y monitoreo en tiempo real de pacientes, personal y tiempos de atención, con paneles de administración y personalización.
- **Dashboard de estadísticas y métricas:** Visualización detallada del flujo de pacientes, cumplimiento de tiempos críticos, análisis de picos de demanda y generación automática de métricas históricas y alertas de gestión.

## Estructura del proyecto

- `Interfaz.py` - Lógica de la interfaz gráfica y conexión con los demás módulos.
- `cola_triage.py` - Algoritmo de gestión de colas y priorización.
- `paciente.py` / `personal.py` - Clases principales del sistema.
- `configuracion.py` - Módulo para la configuración dinámica de los tiempos de atención.
- `utils.py` - Funciones utilitarias para alertas, cálculos y colores.
- `dashboard_gestion.py` - Dashboard interactivo y generación de estadísticas.
- `ml_predictor.py` / `entrenar_modelo_triaje.py` - Entrenamiento y despliegue de modelos predictivos de tiempos de espera.
- `main.py` - Script de arranque del sistema.

## Requisitos

- Python 3.8+
- Pandas, Numpy, Tkinter, Matplotlib, XGBoost, Scikit-learn

Se pueden instalar las dependencias principales con:

```bash
pip install pandas numpy matplotlib xgboost scikit-learn
```

## Ejecución

Para iniciar la plataforma, se puede ejecutar con:

```bash
python main.py
```


