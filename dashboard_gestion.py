import tkinter as tk
from tkinter import ttk
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from configuracion import ConfiguracionTiempos

def abrir_dashboard_gestion(ventana_padre, cfg_tiempos):
    ventana = tk.Toplevel(ventana_padre)
    ventana.title("Dashboard de Gestión")
    ventana.geometry("1700x1000")

    try:
        df = pd.read_csv("historico_atenciones.csv", encoding="utf-8")
    except Exception:
        ttk.Label(ventana, text="No hay datos históricos para mostrar.").pack()
        return
    if df.empty:
        ttk.Label(ventana, text="No hay datos históricos para mostrar.").pack()
        return

    df['HoraIngreso'] = pd.to_datetime(df['HoraIngreso'], errors='coerce')
    df['HoraAtencion'] = pd.to_datetime(df['HoraAtencion'], errors='coerce')
    df = df.dropna(subset=['HoraIngreso'])

    # FILTROS DEPENDIENTES 
    filtro_frame = ttk.Frame(ventana)
    filtro_frame.pack(fill="x", pady=8)

    años = sorted(df['HoraIngreso'].dt.year.dropna().unique())
    año_var = tk.StringVar(value="Todos")
    meses_var = tk.StringVar(value="Todos")
    dias_var = tk.StringVar(value="Todos")

    def actualizar_filtros(*args):
        año_sel = año_var.get()
        mes_sel = meses_var.get()
        dia_sel = dias_var.get()

        # Actualiza meses según el año seleccionado
        if año_sel == "Todos":
            meses = sorted(df['HoraIngreso'].dt.month.dropna().unique())
        else:
            meses = sorted(df[df['HoraIngreso'].dt.year == int(año_sel)]['HoraIngreso'].dt.month.dropna().unique())
        mes_combo['values'] = ["Todos"] + [str(m) for m in meses]
        if mes_sel not in mes_combo['values']:
            meses_var.set("Todos")

        # Filtrar días según año y mes
        if año_sel == "Todos" and meses_var.get() == "Todos":
            dias = sorted(df['HoraIngreso'].dt.date.unique())
        elif año_sel != "Todos" and meses_var.get() == "Todos":
            dias = sorted(df[df['HoraIngreso'].dt.year == int(año_sel)]['HoraIngreso'].dt.date.unique())
        elif año_sel != "Todos" and meses_var.get() != "Todos":
            dias = sorted(df[
                (df['HoraIngreso'].dt.year == int(año_sel)) &
                (df['HoraIngreso'].dt.month == int(meses_var.get()))
            ]['HoraIngreso'].dt.date.unique())
        else:
            dias = sorted(df['HoraIngreso'].dt.date.unique())
        dia_combo['values'] = ["Todos"] + [str(d) for d in dias]
        if dia_sel not in dia_combo['values']:
            dias_var.set("Todos")

        # Si seleccionas un día, fuerza año y mes correctos
        if dias_var.get() != "Todos":
            try:
                fecha_sel = pd.to_datetime(dias_var.get())
                año_var.set(str(fecha_sel.year))
                meses_var.set(str(fecha_sel.month))
            except Exception:
                pass

    ttk.Label(filtro_frame, text="Año:").pack(side="left")
    año_combo = ttk.Combobox(filtro_frame, values=["Todos"] + [str(a) for a in años], textvariable=año_var, width=7, state="readonly")
    año_combo.pack(side="left", padx=5)
    ttk.Label(filtro_frame, text="Mes:").pack(side="left")
    mes_combo = ttk.Combobox(filtro_frame, values=["Todos"], textvariable=meses_var, width=7, state="readonly")
    mes_combo.pack(side="left", padx=5)
    ttk.Label(filtro_frame, text="Día:").pack(side="left")
    dia_combo = ttk.Combobox(filtro_frame, values=["Todos"], textvariable=dias_var, width=12, state="readonly")
    dia_combo.pack(side="left", padx=5)
    ttk.Button(filtro_frame, text="Actualizar", command=lambda: actualizar_dashboard()).pack(side="left", padx=8)
    ttk.Button(filtro_frame, text="Volver", command=ventana.destroy).pack(side="right", padx=10)

    año_var.trace('w', actualizar_filtros)
    meses_var.trace('w', actualizar_filtros)

    # DASHBOARD CON SCROLL 
    dashboard_frame = ttk.Frame(ventana)
    dashboard_frame.pack(fill="both", expand=True)
    dashboard_canvas = tk.Canvas(dashboard_frame)
    scrollbar = ttk.Scrollbar(dashboard_frame, orient="vertical", command=dashboard_canvas.yview)
    scrollable_frame = ttk.Frame(dashboard_canvas)
    scrollable_frame.bind(
        "<Configure>",
        lambda e: dashboard_canvas.configure(
            scrollregion=dashboard_canvas.bbox("all")
        )
    )

    dashboard_canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    dashboard_canvas.configure(yscrollcommand=scrollbar.set)
    dashboard_canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    def actualizar_dashboard():
        for widget in scrollable_frame.winfo_children():
            widget.destroy()

        # Filtrado de DataFrame según filtros seleccionados
        año = año_var.get()
        mes = meses_var.get()
        dia = dias_var.get()
        df_filtro = df.copy()

        # Si seleccionas un día, fuerza el filtro de año y mes a ese día específico
        if dia != "Todos":
            try:
                fecha_sel = pd.to_datetime(dia)
                año = str(fecha_sel.year)
                mes = str(fecha_sel.month)
                año_var.set(año)
                meses_var.set(mes)
                df_filtro = df_filtro[
                    (df_filtro['HoraIngreso'].dt.year == int(año)) &
                    (df_filtro['HoraIngreso'].dt.month == int(mes)) &
                    (df_filtro['HoraIngreso'].dt.date.astype(str) == dia)
                ]
            except Exception:
                df_filtro = df_filtro[df_filtro['HoraIngreso'].dt.date.astype(str) == dia]
        else:
            if año != "Todos":
                df_filtro = df_filtro[df_filtro['HoraIngreso'].dt.year == int(año)]
            if mes != "Todos":
                df_filtro = df_filtro[df_filtro['HoraIngreso'].dt.month == int(mes)]

        # ================== ALERTAS AUTOMÁTICAS ==================
        frame_alerta = ttk.LabelFrame(scrollable_frame, text="Alertas y recomendaciones")
        frame_alerta.pack(fill="x", padx=8, pady=8)
        alertas = []
        tiempos_criticos = cfg_tiempos.mostrar_configuracion()
        niveles = ['I', 'II', 'III', 'IV', 'V']
        for nivel in niveles:
            datos = df_filtro[df_filtro['Nivel_Triage'] == nivel]['TiempoEspera'].dropna()
            t_critico = tiempos_criticos.get(nivel, {"I": 5, "II": 15, "III": 60, "IV": 120, "V": 240}[nivel])
            if not datos.empty:
                cumplimiento = 100 * np.mean(datos <= t_critico)
                if cumplimiento < 50:
                    alertas.append(f"¡Cuidado! El nivel {nivel} incumple más del 50% de las veces en este periodo ({cumplimiento:.1f}% de cumplimiento).")
        if año != "Todos" and mes == "Todos":
            año_actual = int(año)
            pacientes_actual = len(df_filtro)
            df_ant = df[df['HoraIngreso'].dt.year == (año_actual - 1)]
            pacientes_ant = len(df_ant)
            if pacientes_ant > 0:
                dif = pacientes_actual - pacientes_ant
                pct = 100 * dif / pacientes_ant
                if abs(pct) > 10:
                    if pct > 0:
                        alertas.append(f"El flujo de pacientes creció un {pct:.1f}% respecto al año anterior.")
                    else:
                        alertas.append(f"El flujo de pacientes cayó un {abs(pct):.1f}% respecto al año anterior.")
        if año != "Todos" and mes != "Todos" and dia == "Todos":
            año_actual = int(año)
            mes_actual = int(mes)
            pacientes_actual = len(df_filtro)
            if mes_actual > 1:
                df_ant = df[(df['HoraIngreso'].dt.year == año_actual) & (df['HoraIngreso'].dt.month == (mes_actual-1))]
            else:
                df_ant = df[(df['HoraIngreso'].dt.year == (año_actual-1)) & (df['HoraIngreso'].dt.month == 12)]
            pacientes_ant = len(df_ant)
            if pacientes_ant > 0:
                dif = pacientes_actual - pacientes_ant
                pct = 100 * dif / pacientes_ant
                if abs(pct) > 10:
                    if pct > 0:
                        alertas.append(f"El flujo de pacientes creció un {pct:.1f}% respecto al mes anterior.")
                    else:
                        alertas.append(f"El flujo de pacientes cayó un {abs(pct):.1f}% respecto al mes anterior.")
        if año != "Todos" and mes != "Todos" and dia == "Todos":
            año_actual = int(año)
            total_ano = len(df[df['HoraIngreso'].dt.year == año_actual])
            pacientes_actual = len(df_filtro)
            promedio_mensual = total_ano / 12 if total_ano > 0 else 0
            if pacientes_actual > promedio_mensual * 1.15:
                alertas.append(f"¡Atención! Este mes tuvo un flujo de pacientes superior al promedio anual ({pacientes_actual} vs {promedio_mensual:.0f}).")
        if alertas:
            for alerta in alertas:
                ttk.Label(frame_alerta, text=alerta, foreground="#c00", font=("Arial", 11)).pack(anchor="w")
        else:
            ttk.Label(frame_alerta, text="No hay alertas relevantes para este periodo.", font=("Arial", 11)).pack(anchor="w")

        # --- Métricas y gráficos contextuales ---
        frame_metricas = ttk.LabelFrame(scrollable_frame, text="Resumen de Pacientes")
        frame_metricas.pack(fill="x", padx=8, pady=8)

        total_pacientes = len(df_filtro)
        edades = df_filtro['Edad'].dropna()
        sexo = df_filtro['Sexo'].dropna()
        ttk.Label(frame_metricas, text=f"Pacientes en periodo seleccionado: {total_pacientes}").pack(side="left", padx=15)
        if not edades.empty:
            ttk.Label(frame_metricas, text=f"Edad promedio: {np.mean(edades):.1f}").pack(side="left", padx=15)
        if not sexo.empty:
            pct_f = (sexo == 'F').mean() * 100
            pct_m = (sexo == 'M').mean() * 100
            ttk.Label(frame_metricas, text=f"% Mujeres: {pct_f:.1f} | % Hombres: {pct_m:.1f}").pack(side="left", padx=15)

        # --- Cumplimiento por triage ---
        frame_cumplimiento = ttk.LabelFrame(scrollable_frame, text="Triage: medianas y cumplimiento de tiempos")
        frame_cumplimiento.pack(fill="x", padx=8, pady=5)
        texto = ""
        for nivel in niveles:
            datos = df_filtro[df_filtro['Nivel_Triage'] == nivel]['TiempoEspera'].dropna()
            t_critico = tiempos_criticos.get(nivel)
            if t_critico is None:
                t_critico = {"I": 5, "II": 15, "III": 60, "IV": 120, "V": 240}[nivel]
            if datos.empty:
                resumen = "Sin datos"
            else:
                mediana = np.median(datos)
                p90 = np.percentile(datos, 90)
                p95 = np.percentile(datos, 95)
                cumplimiento = 100 * np.mean(datos <= t_critico)
                resumen = (
                    f"Mediana: {mediana:.1f} min | p90: {p90:.1f} | p95: {p95:.1f} | "
                    f"Cumplimiento de tiempos críticos: {cumplimiento:.1f}% (≤{t_critico} min)"
                )
            texto += f"Triage {nivel}: {resumen}\n"
        ttk.Label(frame_cumplimiento, text=texto, anchor="w", justify="left").pack(anchor="w")

        # ================== GRÁFICOS PRINCIPALES ==================
        graficos_frame = ttk.Frame(scrollable_frame)
        graficos_frame.pack(fill="both", expand=True)

        # ==== BOX PLOT TIEMPOS DE ESPERA POR NIVEL DE TRIAGE ====
        if not df_filtro.empty and 'Nivel_Triage' in df_filtro.columns:
            fig_box, ax_box = plt.subplots(figsize=(4,2.1))
            sns.boxplot(
                data=df_filtro,
                x="Nivel_Triage",
                y="TiempoEspera",
                order=['I','II','III','IV','V'],
                palette="Set3",
                hue="Nivel_Triage",
                legend=False,
                showfliers=True
            )
            ax_box.set_title("Boxplot tiempos de espera por triage")
            ax_box.set_xlabel("Nivel de Triage")
            ax_box.set_ylabel("Tiempo de espera (min)")
            plt.tight_layout()
            canvas_box = FigureCanvasTkAgg(fig_box, master=graficos_frame)
            canvas_box.draw()
            canvas_box.get_tk_widget().grid(row=1, column=0, padx=5, pady=8)
            plt.close(fig_box)

        # ========== GRÁFICOS DEPENDIENDO DEL FILTRO ==========
        if dia != "Todos":
            # Solo día: SOLO muestra la barra de distribución por horas de ese día (NO heatmap)
            fig_hora, ax_hora = plt.subplots(figsize=(5,2))
            conteo_hora = df_filtro.groupby(df_filtro['HoraIngreso'].dt.hour)['ID'].count()
            conteo_hora.plot(kind="bar", ax=ax_hora, color="#4E79A7")
            ax_hora.set_title(f"Pacientes por hora ({dia})")
            ax_hora.set_xlabel("Hora")
            ax_hora.set_ylabel("N° pacientes")
            plt.tight_layout()
            canvas_hora = FigureCanvasTkAgg(fig_hora, master=graficos_frame)
            canvas_hora.draw()
            canvas_hora.get_tk_widget().grid(row=0, column=0, padx=5, pady=8)
            plt.close(fig_hora)
        elif año == "Todos":
            # Pacientes por año y heatmap global
            fig_año, ax_año = plt.subplots(figsize=(3.6,2))
            conteo_ano = df_filtro.groupby(df_filtro['HoraIngreso'].dt.year)['ID'].count()
            conteo_ano.plot(kind="bar", ax=ax_año, color="#4E79A7")
            ax_año.set_title("Pacientes por año")
            ax_año.set_xlabel("Año")
            ax_año.set_ylabel("N° pacientes")
            plt.tight_layout()
            canvas_año = FigureCanvasTkAgg(fig_año, master=graficos_frame)
            canvas_año.draw()
            canvas_año.get_tk_widget().grid(row=0, column=0, padx=5, pady=8)
            plt.close(fig_año)

            df_filtro['Hora'] = df_filtro['HoraIngreso'].dt.hour
            df_filtro['DiaSemana'] = df_filtro['HoraIngreso'].dt.day_name()
            tabla_heatmap = pd.pivot_table(df_filtro, index="DiaSemana", columns="Hora", values="ID", aggfunc="count", fill_value=0)
            dias_ordenados = ['Lunes', 'Martes', 'Miercoles', 'Jueves', 'Viernes', 'Sabado', 'Domingo']
            tabla_heatmap = tabla_heatmap.reindex(dias_ordenados)
            fig2, ax2 = plt.subplots(figsize=(5,2))
            sns.heatmap(tabla_heatmap, cmap="YlOrRd", ax=ax2)
            ax2.set_title("Flujo de pacientes por hora y día (todos los años)")
            ax2.set_xlabel("Hora del día")
            ax2.set_ylabel("Día de la semana")
            plt.tight_layout()
            canvas2 = FigureCanvasTkAgg(fig2, master=graficos_frame)
            canvas2.draw()
            canvas2.get_tk_widget().grid(row=0, column=1, padx=5, pady=8)
            plt.close(fig2)
        elif mes == "Todos":
            # Pacientes por mes y heatmap mensual
            fig_mes, ax_mes = plt.subplots(figsize=(3.6,2))
            conteo_mes = df_filtro.groupby(df_filtro['HoraIngreso'].dt.month)['ID'].count()
            conteo_mes.plot(kind="bar", ax=ax_mes, color="#F28E2B")
            ax_mes.set_title("Pacientes por mes")
            ax_mes.set_xlabel("Mes")
            ax_mes.set_ylabel("N° pacientes")
            plt.tight_layout()
            canvas_mes = FigureCanvasTkAgg(fig_mes, master=graficos_frame)
            canvas_mes.draw()
            canvas_mes.get_tk_widget().grid(row=0, column=0, padx=5, pady=8)
            plt.close(fig_mes)

            df_filtro['Hora'] = df_filtro['HoraIngreso'].dt.hour
            df_filtro['DiaSemana'] = df_filtro['HoraIngreso'].dt.day_name()
            tabla_heatmap = pd.pivot_table(df_filtro, index="DiaSemana", columns="Hora", values="ID", aggfunc="count", fill_value=0)
            dias_ordenados = ['Lunes', 'Martes', 'Miercoles', 'Jueves', 'Viernes', 'Sabado', 'Domingo']
            tabla_heatmap = tabla_heatmap.reindex(dias_ordenados)
            fig2, ax2 = plt.subplots(figsize=(5,2))
            sns.heatmap(tabla_heatmap, cmap="YlOrRd", ax=ax2)
            ax2.set_title(f"Flujo de pacientes por hora y día ({año})")
            ax2.set_xlabel("Hora del día")
            ax2.set_ylabel("Día de la semana")
            plt.tight_layout()
            canvas2 = FigureCanvasTkAgg(fig2, master=graficos_frame)
            canvas2.draw()
            canvas2.get_tk_widget().grid(row=0, column=1, padx=5, pady=8)
            plt.close(fig2)
        elif dia == "Todos":
            # Pacientes por día y heatmap día/semana
            fig_dia, ax_dia = plt.subplots(figsize=(3.6,2))
            conteo_dia = df_filtro.groupby(df_filtro['HoraIngreso'].dt.day)['ID'].count()
            conteo_dia.plot(kind="bar", ax=ax_dia, color="#76B041")
            ax_dia.set_title("Pacientes por día")
            ax_dia.set_xlabel("Día")
            ax_dia.set_ylabel("N° pacientes")
            plt.tight_layout()
            canvas_dia = FigureCanvasTkAgg(fig_dia, master=graficos_frame)
            canvas_dia.draw()
            canvas_dia.get_tk_widget().grid(row=0, column=0, padx=5, pady=8)
            plt.close(fig_dia)

            df_filtro['Hora'] = df_filtro['HoraIngreso'].dt.hour
            df_filtro['DiaSemana'] = df_filtro['HoraIngreso'].dt.day_name()
            tabla_heatmap = pd.pivot_table(df_filtro, index="DiaSemana", columns="Hora", values="ID", aggfunc="count", fill_value=0)
            dias_ordenados = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            tabla_heatmap = tabla_heatmap.reindex(dias_ordenados)
            fig2, ax2 = plt.subplots(figsize=(5,2))
            sns.heatmap(tabla_heatmap, cmap="YlOrRd", ax=ax2)
            ax2.set_title(f"Flujo de pacientes por hora y día ({año}-{mes})")
            ax2.set_xlabel("Hora del día")
            ax2.set_ylabel("Día de la semana")
            plt.tight_layout()
            canvas2 = FigureCanvasTkAgg(fig2, master=graficos_frame)
            canvas2.draw()
            canvas2.get_tk_widget().grid(row=0, column=1, padx=5, pady=8)
            plt.close(fig2)

    actualizar_filtros()
    actualizar_dashboard()
