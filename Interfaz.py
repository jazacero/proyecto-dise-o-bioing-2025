import tkinter as tk
import os
import json
import csv
import pandas as pd
import numpy as np
import datetime
import datetime
from tkinter import messagebox, ttk
from paciente import Paciente
from cola_triage import GestorColas
from configuracion import ConfiguracionTiempos
from utils import verificar_alerta_tiempo, estado_alerta
from ml_predictor import predecir_tiempo_espera
from dashboard_gestion import abrir_dashboard_gestion


def signos_criticos_por_edad(edad, fc, spo2, fr, temp, ta):
        """
        Devuelve el número de signos vitales en zona crítica, usando rangos según edad (años).
        """
        criticos = 0
        try:
            if edad is None or str(edad).strip() == "":
                return criticos  # No evalúa si edad es desconocida
            edad = int(edad)
            # Definir rangos críticos por edad
            if edad < 1:
                fc_min, fc_max = 90, 180
                fr_min, fr_max = 30, 60
                ta_min = 70
                spo2_min = 92
                temp_min, temp_max = 36, 38.5
            elif 1 <= edad <= 5:
                fc_min, fc_max = 80, 160
                fr_min, fr_max = 20, 40
                ta_min = 80
                spo2_min = 92
                temp_min, temp_max = 36, 38.5
            elif 6 <= edad <= 12:
                fc_min, fc_max = 70, 130
                fr_min, fr_max = 16, 30
                ta_min = 90
                spo2_min = 92
                temp_min, temp_max = 36, 38.5
            elif 13 <= edad <= 17:
                fc_min, fc_max = 60, 120
                fr_min, fr_max = 12, 20
                ta_min = 90
                spo2_min = 92
                temp_min, temp_max = 36, 39
            else:
                # Adultos ≥18
                fc_min, fc_max = 40, 130
                fr_min, fr_max = 8, 30
                ta_min, ta_max = 90, 180
                spo2_min = 90
                temp_min, temp_max = 35, 39.5

            if fc is not None:
                if edad >= 18:
                    if fc < fc_min or fc > fc_max:
                        criticos += 1
                else:
                    if fc < fc_min or fc > fc_max:
                        criticos += 1
            if spo2 is not None and spo2 < spo2_min:
                criticos += 1
            if fr is not None:
                if edad >= 18:
                    if fr < fr_min or fr > fr_max:
                        criticos += 1
                else:
                    if fr < fr_min or fr > fr_max:
                        criticos += 1
            if temp is not None:
                if temp < temp_min or temp > temp_max:
                    criticos += 1
            if ta:
                try:
                    if "/" in ta:
                        sistolica = float(ta.split("/")[0])
                    else:
                        sistolica = float(ta)
                    if edad >= 18:
                        if sistolica < ta_min or sistolica > ta_max:
                            criticos += 1
                    else:
                        if sistolica < ta_min:
                            criticos += 1
                except Exception:
                    pass
        except Exception:
            pass
        return criticos

class InterfazTriage:
    def __init__(self, root):
        self.root = root
        self.root.title("Sistema Local de Triage")
        self.root.geometry("900x650")
        self.configuracion = ConfiguracionTiempos(modo="OPS")
        self.configuracion.cargar_tiempos_personalizados()
        self.gestor = None
        try:
            self.df_historico = pd.read_csv("historico_atenciones.csv", encoding="utf-8")
        except Exception:
            self.df_historico = pd.DataFrame()  

        self.crear_pantalla_inicio()

    def crear_pantalla_inicio(self):
        for widget in self.root.winfo_children():
            widget.destroy()

        frame = ttk.Frame(self.root)
        frame.pack(pady=80)

        ttk.Label(frame, text="Seleccione tipo de acceso:").pack(pady=10)
        ttk.Button(frame, text="Modo Administrador", command=self.menu_admin).pack(pady=5)
        ttk.Button(frame, text="Modo Personal de Salud", command=self.menu_personal).pack(pady=5)

    def menu_admin(self):
        for widget in self.root.winfo_children():
            widget.destroy()
        frame = ttk.LabelFrame(self.root, text="Opciones de Administrador")
        frame.pack(padx=40, pady=60, fill="both", expand=True)
        ttk.Button(frame, text="Dashboard de gestión", command=self.abrir_dashboard_admin).pack(pady=18, fill="x")
        ttk.Button(frame, text="Configurar tiempos de Triage", command=self.configurar_tiempos).pack(pady=18, fill="x")
        ttk.Button(frame, text="Configurar Personal de Turno", command=self.configurar_personal).pack(pady=18, fill="x")
        ttk.Button(frame, text="Volver", command=self.crear_pantalla_inicio).pack(pady=18, fill="x")

    def configurar_tiempos(self):
        for widget in self.root.winfo_children():
            widget.destroy()
        frame = ttk.LabelFrame(self.root, text="Configuración de tiempos por nivel de triaje")
        frame.pack(padx=20, pady=20, fill="both", expand=True)
        self.entradas_tiempos = {}
        for idx, nivel in enumerate(['I', 'II', 'III', 'IV', 'V']):
            ttk.Label(frame, text=f"Triage {nivel}:").grid(row=idx, column=0, padx=5, pady=5)
            var = tk.StringVar()
            self.entradas_tiempos[nivel] = var
            ttk.Entry(frame, textvariable=var, width=10).grid(row=idx, column=1)
        ttk.Button(frame, text="Guardar Configuración", command=self.guardar_configuracion).grid(row=6, columnspan=2, pady=10)
        ttk.Button(frame, text="Tiempos por defecto", command=self.usar_ops).grid(row=7, columnspan=2, pady=5)
        ttk.Button(frame, text="Volver", command=self.menu_admin).grid(row=8, columnspan=2, pady=5)

    def configurar_personal(self):
        for widget in self.root.winfo_children():
            widget.destroy()
        frame = ttk.LabelFrame(self.root, text="Personal de Turno")
        frame.pack(padx=20, pady=20, fill="both", expand=True)
        self.medicos_var = tk.StringVar()
        self.enfermeros_var = tk.StringVar()
        self.especialistas_var = tk.StringVar()
        ttk.Label(frame, text="Médicos en turno:").grid(row=0, column=0)
        ttk.Entry(frame, textvariable=self.medicos_var, width=10).grid(row=0, column=1)
        ttk.Label(frame, text="Enfermeros en turno:").grid(row=1, column=0)
        ttk.Entry(frame, textvariable=self.enfermeros_var, width=10).grid(row=1, column=1)
        ttk.Label(frame, text="Especialistas en turno:").grid(row=2, column=0)
        ttk.Entry(frame, textvariable=self.especialistas_var, width=10).grid(row=2, column=1)
        ttk.Button(frame, text="Guardar Personal de Turno", command=self.guardar_personal_turno).grid(row=3, columnspan=2, pady=10)
        ttk.Button(frame, text="Volver", command=self.menu_admin).grid(row=4, columnspan=2, pady=10)

    def guardar_personal_turno(self):
        try:
            # Chequear que todos los campos sean numéricos y no estén vacíos
            if not self.medicos_var.get().strip() or not self.enfermeros_var.get().strip() or not self.especialistas_var.get().strip():
                messagebox.showerror("Error", "Debes ingresar la cantidad de médicos, enfermeros y especialistas en turno.")
                return
            self.medicos_turno = int(self.medicos_var.get())
            self.enfermeros_turno = int(self.enfermeros_var.get())
            self.especialistas_turno = int(self.especialistas_var.get())
            messagebox.showinfo("Éxito", "Personal de turno guardado correctamente.")
        except ValueError:
            messagebox.showerror("Error", "Los valores deben ser números enteros.")
    def guardar_configuracion(self):
        try:
            if self.configuracion is None:
                self.configuracion = ConfiguracionTiempos()
            for nivel, var in self.entradas_tiempos.items():
                tiempo = int(var.get())
                self.configuracion.definir_tiempo(nivel, tiempo)
            self.configuracion.guardar_tiempos_personalizados()
            messagebox.showinfo("Éxito", "Configuración guardada correctamente.")
        except ValueError:
            messagebox.showerror("Error", "Todos los tiempos deben ser números enteros.")    
    def usar_ops(self):
        self.configuracion = ConfiguracionTiempos(modo="OPS")
        messagebox.showinfo("Configuración OPS", "Se han aplicado los tiempos estándar de la OPS.")
    
    def menu_personal(self):
        if not hasattr(self, 'medicos_turno') or not hasattr(self, 'enfermeros_turno') or not hasattr(self, 'especialistas_turno'):
            messagebox.showerror("Error", "El personal de turno debe estar completamente configurado antes de gestionar pacientes.")
            return

        self.gestor = GestorColas(self.configuracion.mostrar_configuracion())

        for widget in self.root.winfo_children():
            widget.destroy()

        self.frame_ingreso = ttk.LabelFrame(self.root, text="Ingreso de Pacientes")
        self.frame_ingreso.pack(fill="x", padx=10, pady=10)

        # Botones principales
        ttk.Button(self.frame_ingreso, text="Ingresar Manualmente", command=self.mostrar_formulario_manual).grid(row=0, column=0, padx=10, pady=5)
        ttk.Button(self.frame_ingreso, text="Buscar por ID", command=self.mostrar_formulario_id).grid(row=0, column=1, padx=10, pady=5)
        ttk.Button(self.frame_ingreso, text="Volver al inicio", command=self.crear_pantalla_inicio).grid(row=0, column=2, padx=10, pady=5)

        # Frame oculto para ingreso manual
        self.formulario_manual = ttk.Frame(self.root)
        # Frame oculto para ingreso por ID
        self.formulario_id = ttk.Frame(self.root)

        # Cola de espera
        self.frame_cola = ttk.LabelFrame(self.root, text="Cola de Espera")
        self.frame_cola.pack(fill="both", expand=True, padx=10, pady=10)

        self.lista_pacientes = tk.Listbox(self.frame_cola, height=20)
        self.lista_pacientes.pack(fill="both", expand=True)

        botones_frame = ttk.Frame(self.root)
        botones_frame.pack(pady=10)

        ttk.Button(botones_frame, text="Atender Siguiente", command=self.atender_paciente).pack(side="left", padx=5)
        ttk.Button(botones_frame, text="Ver/Editar Seleccionado", command=self.editar_paciente).pack(side="left", padx=5)
        ttk.Button(botones_frame, text="Atender Seleccionado", command=self.atender_seleccionado).pack(side="left", padx=5)
        ttk.Button(botones_frame, text="Ver Reevaluaciones", command=self.mostrar_reevaluaciones).pack(side="left", padx=5)

        self.programar_actualizacion()



    def ingresar_paciente(self):
        nombre = self.nombre_var.get().strip()
        triaje = self.triaje_var.get().strip().upper()

        if not nombre or triaje not in ["I", "II", "III", "IV", "V"]:
            messagebox.showerror("Error", "Por favor, ingrese nombre y nivel de triaje válido (I-V).")
            return

        try:
            edad = int(self.edad_var.get().strip()) if self.edad_var.get().strip() else None
        except ValueError:
            messagebox.showerror("Error", "Edad inválida.")
            return

        sexo = self.sexo_var.get().strip()
        id_paciente = self.id_var.get().strip()

        signos = {}
        try:
            if self.fc_var.get().strip():
                signos["FC"] = float(self.fc_var.get().strip())
            if self.spo2_var.get().strip():
                signos["SpO2"] = float(self.spo2_var.get().strip())
            if self.fr_var.get().strip():
                signos["FR"] = float(self.fr_var.get().strip())
            if self.temp_var.get().strip():
                signos["Temp"] = float(self.temp_var.get().strip())
            if self.ta_var.get().strip():
                signos["TA"] = self.ta_var.get().strip()  # tipo "120/80"
        except ValueError:
            messagebox.showerror("Error", "Alguno de los signos vitales es inválido.")
            return

        paciente = Paciente(
            nombre=nombre,
            nivel_triaje=triaje,
            edad=edad,
            sexo=sexo,
            id_paciente=id_paciente,
            signos_vitales=signos
        )

        self.gestor.agregar_paciente(paciente)
        self.guardar_o_actualizar_historia(paciente)
        self.actualizar_lista()
        self.root.update_idletasks()


        # ---------- ML: Mostrar tiempo estimado de espera ----------
        if hasattr(self, "df_historico") and not self.df_historico.empty:
            now = datetime.datetime.now()
            hora = now.hour
            mes = now.month
            dia_semana = now.weekday()
            # Cálculo de densidad por hora
            densidad_hora = self.df_historico[
                self.df_historico['HoraIngreso'].str.contains(f"{hora:02d}:", na=False)
            ]['TiempoEspera'].mean()
            if np.isnan(densidad_hora):
                densidad_hora = self.df_historico['TiempoEspera'].mean()
            nuevo_paciente_dict = {
                'Hora': hora,
                'Mes': mes,
                'Dia_Semana': dia_semana,
                'Pacientes_En_Cola': len(self.gestor.cola),
                'Densidad_Hora': densidad_hora,
                'Es_Feriado': 0,  # Mejora esto si quieres
                'Hora_Seno': np.sin(2 * np.pi * hora / 24),
                'Hora_Coseno': np.cos(2 * np.pi * hora / 24),
                'Es_Hora_Pico': int(hora in [7, 8, 9, 16, 17, 18, 19]),
                'Nivel_Triage': triaje,
            }
            tiempo_estimado = predecir_tiempo_espera(nuevo_paciente_dict, self.df_historico)
            hora_atencion = (now + datetime.timedelta(minutes=tiempo_estimado)).strftime("%H:%M")
            mensaje_ml = (f"Paciente ingresado.\n"
                        f"Tiempo estimado total de espera: {tiempo_estimado:.1f} min\n"
                        f"Hora estimada de atención: {hora_atencion}\n"
                        f"Tiempo actual en espera: 0.0 min")
            messagebox.showinfo("Predicción ML", mensaje_ml)
        else:
            messagebox.showinfo("Predicción ML", "Paciente ingresado. (No hay histórico para estimar el tiempo de espera)")

        # Limpiar los campos
        self.nombre_var.set("")
        self.triaje_var.set("")
        self.edad_var.set("")
        self.sexo_var.set("")
        self.id_var.set("")
        self.fc_var.set("")
        self.spo2_var.set("")
        self.fr_var.set("")
        self.temp_var.set("")
        self.ta_var.set("")

        # Ocultar formulario
        self.formulario_manual.pack_forget()
    
    def atender_seleccionado(self):
        seleccion = self.lista_pacientes.curselection()
        if not seleccion:
            messagebox.showwarning("Aviso", "Seleccione un paciente para atender.")
            return
        index = seleccion[0]
        paciente = self.gestor.obtener_paciente_por_indice(index)
        if paciente:
            paciente.registrar_atencion(datetime.datetime.now())
            self.guardar_o_actualizar_historia(paciente)
            self.guardar_evento_csv(paciente)  
            mensaje = f"Atendido manualmente: {paciente.nombre} (Triage {paciente.nivel_triaje})"
            self.gestor.eliminar_paciente(paciente)
            self.actualizar_lista()
            self.root.update_idletasks()
            messagebox.showinfo("Atención", mensaje)


    def atender_paciente(self):
        paciente = self.gestor.siguiente_paciente()
        if paciente:
            mensaje = f"Atendiendo a: {paciente.nombre} (Triage {paciente.nivel_triaje})\nTiempo de espera: {paciente.tiempo_espera():.1f} min"
            messagebox.showinfo("Atención", mensaje)
            paciente.registrar_atencion(datetime.datetime.now())
            self.guardar_o_actualizar_historia(paciente)
            self.guardar_evento_csv(paciente) 
            self.actualizar_lista()
            self.root.update_idletasks()

        else:
            messagebox.showinfo("Atención", "No hay pacientes en espera.")


    def editar_paciente(self):
        seleccion = self.lista_pacientes.curselection()
        if not seleccion:
            messagebox.showwarning("Aviso", "Seleccione un paciente para editar.")
            return

        index = seleccion[0]
        paciente = self.gestor.obtener_paciente_por_indice(index)
        if not paciente:
            messagebox.showerror("Error", "Paciente no encontrado.")
            return

        ventana = tk.Toplevel(self.root)
        ventana.title("Editar Paciente")

        # --- Datos generales
        ttk.Label(ventana, text="Nombre:").grid(row=0, column=0)
        nombre_var = tk.StringVar(value=paciente.nombre)
        ttk.Entry(ventana, textvariable=nombre_var).grid(row=0, column=1)

        ttk.Label(ventana, text="Nivel de Triage:").grid(row=1, column=0)
        triaje_var = tk.StringVar(value=paciente.nivel_triaje)
        ttk.Combobox(ventana, textvariable=triaje_var, values=["I", "II", "III", "IV", "V"], width=5).grid(row=1, column=1)

        ttk.Label(ventana, text="Edad:").grid(row=2, column=0)
        edad_var = tk.StringVar(value=str(paciente.edad) if paciente.edad is not None else "")
        ttk.Entry(ventana, textvariable=edad_var).grid(row=2, column=1)

        ttk.Label(ventana, text="Sexo:").grid(row=2, column=2)
        sexo_var = tk.StringVar(value=paciente.sexo)
        ttk.Combobox(ventana, textvariable=sexo_var, values=["M", "F", "Otro"], width=5).grid(row=2, column=3)

        # --- Signos vitales
        ttk.Label(ventana, text="FC (lpm):").grid(row=3, column=0)
        fc_var = tk.StringVar(value=str(paciente.signos_vitales.get("FC", "")))
        ttk.Entry(ventana, textvariable=fc_var).grid(row=3, column=1)

        ttk.Label(ventana, text="SpO₂ (%):").grid(row=3, column=2)
        spo2_var = tk.StringVar(value=str(paciente.signos_vitales.get("SpO2", "")))
        ttk.Entry(ventana, textvariable=spo2_var).grid(row=3, column=3)

        ttk.Label(ventana, text="FR (rpm):").grid(row=4, column=0)
        fr_var = tk.StringVar(value=str(paciente.signos_vitales.get("FR", "")))
        ttk.Entry(ventana, textvariable=fr_var).grid(row=4, column=1)

        ttk.Label(ventana, text="Temp (°C):").grid(row=4, column=2)
        temp_var = tk.StringVar(value=str(paciente.signos_vitales.get("Temp", "")))
        ttk.Entry(ventana, textvariable=temp_var).grid(row=4, column=3)

        ttk.Label(ventana, text="TA (mmHg):").grid(row=5, column=0)
        ta_var = tk.StringVar(value=paciente.signos_vitales.get("TA", ""))
        ttk.Entry(ventana, textvariable=ta_var).grid(row=5, column=1)

        # --- Tiempo actual en espera
        ttk.Label(ventana, text=f"Tiempo actual en espera: {paciente.tiempo_espera():.1f} min").grid(row=6, column=0, columnspan=2)

        # --- Tiempo estimado de espera (ML)
        tiempo_estimado_val = ""
        if hasattr(self, "df_historico") and not self.df_historico.empty:
            hora = paciente.ingreso.hour
            mes = paciente.ingreso.month
            dia_semana = paciente.ingreso.weekday()
            densidad_hora = self.df_historico[
                self.df_historico['HoraIngreso'].str.contains(f"{hora:02d}:", na=False)
            ]['TiempoEspera'].mean()
            if np.isnan(densidad_hora):
                densidad_hora = self.df_historico['TiempoEspera'].mean()
            nuevo_paciente_dict = {
                'Hora': hora,
                'Mes': mes,
                'Dia_Semana': dia_semana,
                'Pacientes_En_Cola': len(self.gestor.cola),
                'Densidad_Hora': densidad_hora,
                'Es_Feriado': 0,
                'Hora_Seno': np.sin(2 * np.pi * hora / 24),
                'Hora_Coseno': np.cos(2 * np.pi * hora / 24),
                'Es_Hora_Pico': int(hora in [7, 8, 9, 16, 17, 18, 19]),
                'Nivel_Triage': paciente.nivel_triaje,
            }
            tiempo_estimado_val = predecir_tiempo_espera(nuevo_paciente_dict, self.df_historico)
            ttk.Label(ventana, text=f"Tiempo estimado de espera (ML): {tiempo_estimado_val:.1f} min").grid(row=6, column=2, columnspan=2)

        # --- Guardar cambios
        def guardar():
            # --- SUGERENCIA DE TRIAGE SEGÚN SIGNOS VITALES Y EDAD ---
            try:
                fc_val = float(fc_var.get()) if fc_var.get().strip() else None
            except:
                fc_val = None
            try:
                spo2_val = float(spo2_var.get()) if spo2_var.get().strip() else None
            except:
                spo2_val = None
            try:
                fr_val = float(fr_var.get()) if fr_var.get().strip() else None
            except:
                fr_val = None
            try:
                temp_val = float(temp_var.get()) if temp_var.get().strip() else None
            except:
                temp_val = None
            ta_val = ta_var.get().strip() if ta_var.get().strip() else None
            edad_val = edad_var.get().strip() if edad_var.get().strip() else None

            n_criticos = signos_criticos_por_edad(
                edad_val, fc_val, spo2_val, fr_val, temp_val, ta_val
            )
            triaje_actual = triaje_var.get()

            if n_criticos >= 1 and triaje_actual not in ["I", "II"]:
                sugerido = "I" if n_criticos > 1 else "II"
                cambiar = messagebox.askyesno(
                    "Alerta de triage",
                    f"Signos vitales críticos detectados para la edad ({n_criticos} fuera de rango).\n"
                    f"Se recomienda clasificar como TRIAGE {sugerido}.\n"
                    f"¿Desea cambiar el triage a {sugerido} automáticamente?"
                )
                if cambiar:
                    triaje_var.set(sugerido)

            # --- Ahora sí guardar los cambios
            paciente.nombre = nombre_var.get()
            paciente.nivel_triaje = triaje_var.get()
            paciente.edad = int(edad_var.get()) if edad_var.get().strip() else None
            paciente.sexo = sexo_var.get()
            try:
                paciente.signos_vitales["FC"] = float(fc_var.get()) if fc_var.get().strip() else None
            except:
                paciente.signos_vitales["FC"] = None
            try:
                paciente.signos_vitales["SpO2"] = float(spo2_var.get()) if spo2_var.get().strip() else None
            except:
                paciente.signos_vitales["SpO2"] = None
            try:
                paciente.signos_vitales["FR"] = float(fr_var.get()) if fr_var.get().strip() else None
            except:
                paciente.signos_vitales["FR"] = None
            try:
                paciente.signos_vitales["Temp"] = float(temp_var.get()) if temp_var.get().strip() else None
            except:
                paciente.signos_vitales["Temp"] = None
            paciente.signos_vitales["TA"] = ta_var.get()
            self.gestor.reevaluar_cola()
            self.actualizar_lista()
            self.root.update_idletasks()
            ventana.destroy()

        ttk.Button(ventana, text="Guardar Cambios", command=guardar).grid(row=7, columnspan=4, pady=10)


    def actualizar_lista(self):
        self.lista_pacientes.delete(0, tk.END)
        tiempos = self.configuracion.mostrar_configuracion()

        for _, _, p in self.gestor.cola:
            color = self.obtener_color_alerta(p, tiempos)
            tiempo_espera = p.tiempo_espera()
            # --------- Estimación ML -----------
            tiempo_estimado = ""
            if hasattr(self, "df_historico") and not self.df_historico.empty:
                hora = p.ingreso.hour
                mes = p.ingreso.month
                dia_semana = p.ingreso.weekday()
                densidad_hora = self.df_historico[
                    self.df_historico['HoraIngreso'].str.contains(f"{hora:02d}:", na=False)
                ]['TiempoEspera'].mean()
                if np.isnan(densidad_hora):
                    densidad_hora = self.df_historico['TiempoEspera'].mean()
                nuevo_paciente_dict = {
                    'Hora': hora,
                    'Mes': mes,
                    'Dia_Semana': dia_semana,
                    'Pacientes_En_Cola': len(self.gestor.cola),
                    'Densidad_Hora': densidad_hora,
                    'Es_Feriado': 0,
                    'Hora_Seno': np.sin(2 * np.pi * hora / 24),
                    'Hora_Coseno': np.cos(2 * np.pi * hora / 24),
                    'Es_Hora_Pico': int(hora in [7, 8, 9, 16, 17, 18, 19]),
                    'Nivel_Triage': p.nivel_triaje,
                }
                tiempo_estimado_val = predecir_tiempo_espera(nuevo_paciente_dict, self.df_historico)
                if tiempo_estimado_val is not None:
                    tiempo_estimado = f" (Est: {tiempo_estimado_val:.1f} min)"
            etiqueta = f"{p.nombre} (Triage {p.nivel_triaje}) - {tiempo_espera:.1f} min{tiempo_estimado}"
            self.lista_pacientes.insert(tk.END, etiqueta)
            self.lista_pacientes.itemconfig(tk.END, {'fg': color})

    def obtener_color_alerta(self, paciente, tiempos_limite):
        estado = estado_alerta(paciente, tiempos_limite)
        if estado == "rojo":
            return "red"
        elif estado == "amarillo":
            return "orange"
        else:
            return "green"
    def mostrar_reevaluaciones(self):
        reevaluaciones = []
        tiempos = self.configuracion.mostrar_configuracion()

        for _, _, p in self.gestor.cola:
            if verificar_alerta_tiempo(p, tiempos):
                reevaluaciones.append(p)

        if not reevaluaciones:
            messagebox.showinfo("Reevaluación", "No hay pacientes que requieran reevaluación.")
            return

        ventana = tk.Toplevel(self.root)
        ventana.title("Pacientes para Reevaluación")

        lista = tk.Listbox(ventana, width=60, height=15)
        lista.pack(padx=10, pady=10)

        for p in reevaluaciones:
            tiempo = p.tiempo_espera()
            lista.insert(tk.END, f"{p.nombre} (Triage {p.nivel_triaje}) - {tiempo:.1f} min")
    def programar_actualizacion(self):
            self.actualizar_lista()
            self.root.after(10000, self.programar_actualizacion)
    
    def ingresar_por_id(self):
        id_paciente = self.id_var.get().strip()
        if not id_paciente:
            messagebox.showerror("Error", "Ingrese el ID del paciente.")
            return
        ruta = os.path.join("historias", f"{id_paciente}.json")
        if not os.path.isfile(ruta):
            messagebox.showerror("Error", f"No se encontró archivo para el ID {id_paciente}.")
            return

        try:
            with open(ruta, "r", encoding="utf-8") as f:
                datos = json.load(f)

            nombre = datos.get("nombre")
            triaje = datos.get("nivel_triaje")
            edad = datos.get("edad")
            sexo = datos.get("sexo")
            signos = datos.get("signos_vitales", {})
            hora_ingreso = datos.get("hora_ingreso")
            if hora_ingreso:
                ingreso_dt = datetime.datetime.fromisoformat(hora_ingreso)
            else:
                ingreso_dt = None

            if not nombre or not triaje:
                raise ValueError("Datos incompletos")
            paciente = Paciente(
                nombre=nombre,
                nivel_triaje=triaje,
                edad=edad,
                sexo=sexo,
                id_paciente=id_paciente,
                signos_vitales=signos,
                ingreso=ingreso_dt
            )
            self.gestor.agregar_paciente(paciente)
            self.actualizar_lista()
            self.root.update_idletasks()
            if hasattr(self, "df_historico") and not self.df_historico.empty:
                now = datetime.datetime.now()
                hora = now.hour
                mes = now.month
                dia_semana = now.weekday()
                densidad_hora = self.df_historico[
                    self.df_historico['HoraIngreso'].str.contains(f"{hora:02d}:", na=False)
                ]['TiempoEspera'].mean()
                if np.isnan(densidad_hora):
                    densidad_hora = self.df_historico['TiempoEspera'].mean()
                nuevo_paciente_dict = {
                    'Hora': hora,
                    'Mes': mes,
                    'Dia_Semana': dia_semana,
                    'Pacientes_En_Cola': len(self.gestor.cola),
                    'Densidad_Hora': densidad_hora,
                    'Es_Feriado': 0,  # Mejora esto si quieres
                    'Hora_Seno': np.sin(2 * np.pi * hora / 24),
                    'Hora_Coseno': np.cos(2 * np.pi * hora / 24),
                    'Es_Hora_Pico': int(hora in [7, 8, 9, 16, 17, 18, 19]),
                    'Nivel_Triage': paciente.nivel_triaje,
                }
                tiempo_estimado = predecir_tiempo_espera(nuevo_paciente_dict, self.df_historico)
                hora_atencion = (now + datetime.timedelta(minutes=tiempo_estimado)).strftime("%H:%M")
                mensaje_ml = (f"Paciente ingresado.\n"
                            f"Tiempo estimado total de espera: {tiempo_estimado:.1f} min\n"
                            f"Hora estimada de atención: {hora_atencion}\n"
                            f"Tiempo actual en espera: {paciente.tiempo_espera():.1f} min")
                messagebox.showinfo("Predicción ML", mensaje_ml)
            else:
                messagebox.showinfo("Predicción ML", "Paciente ingresado. (No hay histórico para estimar el tiempo de espera)")

            messagebox.showinfo("Éxito", f"Paciente {nombre} ingresado desde historia clínica.")
            self.formulario_id.pack_forget()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo cargar la historia del paciente:\n{e}")

    def mostrar_formulario_manual(self):
        self.formulario_id.pack_forget()
        self.formulario_manual.destroy()
        self.formulario_manual = ttk.LabelFrame(self.root, text="Formulario Manual")
        self.formulario_manual.pack(fill="x", padx=10, pady=5)

        # Variables
        self.nombre_var = tk.StringVar()
        self.triaje_var = tk.StringVar()
        self.edad_var = tk.StringVar()
        self.sexo_var = tk.StringVar()
        self.id_var = tk.StringVar()
        self.fc_var = tk.StringVar()
        self.spo2_var = tk.StringVar()
        self.fr_var = tk.StringVar()
        self.temp_var = tk.StringVar()
        self.ta_var = tk.StringVar()

        # Campos generales
        ttk.Label(self.formulario_manual, text="Nombre:").grid(row=0, column=0)
        ttk.Entry(self.formulario_manual, textvariable=self.nombre_var).grid(row=0, column=1)

        ttk.Label(self.formulario_manual, text="Nivel de Triage:").grid(row=0, column=2)
        ttk.Combobox(self.formulario_manual, textvariable=self.triaje_var,
                    values=["I", "II", "III", "IV", "V"], width=5).grid(row=0, column=3)

        ttk.Label(self.formulario_manual, text="Edad:").grid(row=1, column=0)
        ttk.Entry(self.formulario_manual, textvariable=self.edad_var).grid(row=1, column=1)

        ttk.Label(self.formulario_manual, text="Sexo:").grid(row=1, column=2)
        ttk.Combobox(self.formulario_manual, textvariable=self.sexo_var,
                    values=["M", "F", "Otro"], width=5).grid(row=1, column=3)

        ttk.Label(self.formulario_manual, text="ID Paciente:").grid(row=2, column=0)
        ttk.Entry(self.formulario_manual, textvariable=self.id_var).grid(row=2, column=1)

        # Signos vitales
        ttk.Label(self.formulario_manual, text="FC (lpm):").grid(row=3, column=0)
        ttk.Entry(self.formulario_manual, textvariable=self.fc_var).grid(row=3, column=1)

        ttk.Label(self.formulario_manual, text="SpO₂ (%):").grid(row=3, column=2)
        ttk.Entry(self.formulario_manual, textvariable=self.spo2_var).grid(row=3, column=3)

        ttk.Label(self.formulario_manual, text="FR (rpm):").grid(row=4, column=0)
        ttk.Entry(self.formulario_manual, textvariable=self.fr_var).grid(row=4, column=1)

        ttk.Label(self.formulario_manual, text="Temp (°C):").grid(row=4, column=2)
        ttk.Entry(self.formulario_manual, textvariable=self.temp_var).grid(row=4, column=3)

        ttk.Label(self.formulario_manual, text="TA (mmHg):").grid(row=5, column=0)
        ttk.Entry(self.formulario_manual, textvariable=self.ta_var).grid(row=5, column=1)
        # Botón de confirmación
        ttk.Button(self.formulario_manual, text="Confirmar Ingreso", command=self.ingresar_paciente).grid(row=6, columnspan=4, pady=10)

    def mostrar_formulario_id(self):
        self.formulario_manual.pack_forget()
        self.formulario_id.destroy()
        self.formulario_id = ttk.LabelFrame(self.root, text="Búsqueda por ID")
        self.formulario_id.pack(fill="x", padx=10, pady=5)

        self.id_var = tk.StringVar()
        ttk.Label(self.formulario_id, text="Ingrese ID del Paciente:").grid(row=0, column=0, padx=5)
        ttk.Entry(self.formulario_id, textvariable=self.id_var).grid(row=0, column=1, padx=5)
        ttk.Button(self.formulario_id, text="Buscar", command=self.ingresar_por_id).grid(row=0, column=2, padx=5)
    def guardar_o_actualizar_historia(self, paciente):
        if not paciente.id_paciente:
            return  # No se puede guardar sin ID

        os.makedirs("historias", exist_ok=True)
        ruta = os.path.join("historias", f"{paciente.id_paciente}.json")

        datos_nuevos = paciente.to_dict()

        if os.path.exists(ruta):
            with open(ruta, "r", encoding="utf-8") as f:
                datos_guardados = json.load(f)

            if datos_guardados != datos_nuevos:
                with open(ruta, "w", encoding="utf-8") as f:
                    json.dump(datos_nuevos, f, indent=4, ensure_ascii=False)
        else:
            with open(ruta, "w", encoding="utf-8") as f:
                json.dump(datos_nuevos, f, indent=4, ensure_ascii=False)
    import csv

    def guardar_evento_csv(self, paciente, archivo='historico_atenciones.csv'):
        def _v(valor):
            return valor if valor not in [None, ""] else '-'
        dt = paciente.ingreso if hasattr(paciente, "ingreso") else datetime.datetime.now()
        dias_letras = ['L', 'MA', 'MI', 'JU', 'VI', 'SA', 'DO']
        dia_letra = dias_letras[dt.weekday()]
        mes = dt.month
        pacientes_cola = len(self.gestor.cola)
        campos = [
            'ID', 'Nombre', 'Sexo', 'Edad', 'Nivel_Triage', 'HoraIngreso', 'HoraAtencion', 'TiempoEspera',
            'MedicosTurno', 'EnfermerosTurno', 'EspecialistasTurno', 'Dia', 'Mes', 'PacientesEnCola'
        ]
        fila = [
            paciente.id_paciente,
            paciente.nombre,
            _v(paciente.sexo),
            _v(paciente.edad),
            paciente.nivel_triaje,
            paciente.ingreso.strftime("%Y-%m-%d %H:%M:%S") if hasattr(paciente, "ingreso") else "-",
            paciente.hora_atencion.strftime("%Y-%m-%d %H:%M:%S") if hasattr(paciente, "hora_atencion") and paciente.hora_atencion else "-",
            paciente.tiempo_espera() if hasattr(paciente, "hora_atencion") and paciente.hora_atencion else "-",
            _v(getattr(self, 'medicos_turno', None)),
            _v(getattr(self, 'enfermeros_turno', None)),
            _v(getattr(self, 'especialistas_turno', None)),
            dia_letra,
            mes,
            pacientes_cola
        ]
        existe = os.path.exists(archivo)
        with open(archivo, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            if not existe:
                writer.writerow(campos)
            writer.writerow(fila)

    def abrir_dashboard_admin(self):
        # Si no hay una configuración aún, usar OPS por defecto
        if self.configuracion is None:
            self.configuracion = ConfiguracionTiempos(modo="OPS")
        abrir_dashboard_gestion(self.root, self.configuracion)


    
if __name__ == "__main__":
    root = tk.Tk()
    app = InterfazTriage(root)
    root.mainloop()
