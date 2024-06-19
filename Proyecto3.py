import sqlite3
import tkinter as tk
from tkinter import messagebox

def conectar_bd():
    try:
        return sqlite3.connect('diagnostico_cardiaco.db')
    except sqlite3.Error as e:
        messagebox.showerror("Error de conexión", f"No se pudo conectar a la base de datos: {e}")
        return None

def obtener_sintomas():
    conn = conectar_bd()
    if conn is None:
        return []
    cursor = conn.cursor()
    cursor.execute('SELECT nombre FROM sintomas')
    resultados = cursor.fetchall()
    conn.close()
    return [resultado[0] for resultado in resultados]

def obtener_enfermedades():
    conn = conectar_bd()
    if conn is None:
        return []
    cursor = conn.cursor()
    cursor.execute('SELECT id, nombre, descripcion FROM enfermedades')
    resultados = cursor.fetchall()
    conn.close()
    return {resultado[0]: {'nombre': resultado[1], 'descripcion': resultado[2]} for resultado in resultados}

def obtener_relaciones():
    conn = conectar_bd()
    if conn is None:
        return []
    cursor = conn.cursor()
    cursor.execute('SELECT id_sintoma, id_enfermedad, peso FROM relacion')
    resultados = cursor.fetchall()
    conn.close()
    relaciones = {}
    for resultado in resultados:
        id_sintoma, id_enfermedad, peso = resultado
        if id_sintoma not in relaciones:
            relaciones[id_sintoma] = []
        relaciones[id_sintoma].append({'id_enfermedad': id_enfermedad, 'peso': peso})
    return relaciones

def diagnosticar(sintomas_seleccionados, edad, imc):
    enfermedades = obtener_enfermedades()
    relaciones = obtener_relaciones()
    
    enfermedad_puntajes = {id: 0 for id in enfermedades}

    for sintoma_id, intensidad in sintomas_seleccionados.items():
        if sintoma_id in relaciones:
            for relacion in relaciones[sintoma_id]:
                enfermedad_puntajes[relacion['id_enfermedad']] += relacion['peso'] * intensidad

    max_puntaje = max(enfermedad_puntajes.values())
    enfermedad_id = max(enfermedad_puntajes, key=enfermedad_puntajes.get)
    
    if max_puntaje > 0:
        base_probabilidad = (max_puntaje / sum(enfermedad_puntajes.values())) * 100

        if edad > 60:
            base_probabilidad += 20
        if imc > 25:
            base_probabilidad += 20

        if base_probabilidad > 100:
            base_probabilidad = 100

        if base_probabilidad < 30:
            probabilidad_clasificacion = "baja"
        elif base_probabilidad < 70:
            probabilidad_clasificacion = "media"
        else:
            probabilidad_clasificacion = "alta"

        return enfermedades[enfermedad_id]['nombre'], enfermedades[enfermedad_id]['descripcion'], probabilidad_clasificacion
    else:
        return None, None, None

class SistemaExpertoApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Sistema Experto de Enfermedades Cardíacas")
        self.root.geometry("600x400")
        self.root.resizable(False, False)

        self.sintomas = obtener_sintomas()
        if not self.sintomas:
            messagebox.showerror("Error", "No se encontraron síntomas en la base de datos.")
            root.destroy()
            return

        self.sintomas_seleccionados = {}
        self.current_sintoma_index = 0

        self.edad = tk.IntVar()
        self.estatura = tk.DoubleVar()
        self.peso = tk.DoubleVar()

        self.label_edad = tk.Label(root, text="Edad:", font=("Arial", 12))
        self.label_edad.pack(pady=5)
        self.entry_edad = tk.Entry(root, textvariable=self.edad)
        self.entry_edad.pack(pady=5)

        self.label_estatura = tk.Label(root, text="Estatura (cm):", font=("Arial", 12))
        self.label_estatura.pack(pady=5)
        self.entry_estatura = tk.Entry(root, textvariable=self.estatura)
        self.entry_estatura.pack(pady=5)

        self.label_peso = tk.Label(root, text="Peso (kg):", font=("Arial", 12))
        self.label_peso.pack(pady=5)
        self.entry_peso = tk.Entry(root, textvariable=self.peso)
        self.entry_peso.pack(pady=5)

        self.start_button = tk.Button(root, text="Iniciar Diagnóstico", command=self.start_diagnosis, font=("Arial", 12), bg="blue", fg="white")
        self.start_button.pack(pady=20)

    def start_diagnosis(self):
        self.edad_valor = self.edad.get()
        self.estatura_valor = self.estatura.get()
        self.peso_valor = self.peso.get()

        if not self.edad_valor or not self.estatura_valor or not self.peso_valor:
            messagebox.showerror("Error", "Por favor, complete todos los campos antes de iniciar el diagnóstico.")
            return

        self.label_edad.pack_forget()
        self.entry_edad.pack_forget()
        self.label_estatura.pack_forget()
        self.entry_estatura.pack_forget()
        self.label_peso.pack_forget()
        self.entry_peso.pack_forget()
        self.start_button.pack_forget()

        self.label = tk.Label(self.root, text="¿Con qué intensidad presenta el siguiente síntoma?", font=("Arial", 14))
        self.label.pack(pady=20)

        self.sintoma_label = tk.Label(self.root, text="", font=("Arial", 14, "bold"))
        self.sintoma_label.pack(pady=10)

        self.radio_var = tk.IntVar()
        self.radio_var.set(0)

        self.radio_buttons_frame = tk.Frame(self.root)
        self.radio_buttons_frame.pack(pady=10)

        for i in range(6):
            tk.Radiobutton(self.radio_buttons_frame, text=str(i), variable=self.radio_var, value=i, font=("Arial", 12)).pack(side="left", padx=5)

        self.next_button = tk.Button(self.root, text="Siguiente", command=self.siguiente_sintoma, font=("Arial", 12), bg="green", fg="white")
        self.next_button.pack(pady=20)

        self.actualizar_pregunta()

    def siguiente_sintoma(self):
        intensidad = self.radio_var.get()
        sintoma = self.sintomas[self.current_sintoma_index]
        sintoma_id = self.obtener_id_sintoma(sintoma)
        self.sintomas_seleccionados[sintoma_id] = intensidad

        self.current_sintoma_index += 1
        self.radio_var.set(0)

        if self.current_sintoma_index < len(self.sintomas):
            self.actualizar_pregunta()
        else:
            self.mostrar_resultado()

    def obtener_id_sintoma(self, sintoma):
        conn = conectar_bd()
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM sintomas WHERE nombre = ?', (sintoma,))
        resultado = cursor.fetchone()
        conn.close()
        return resultado[0] if resultado else None

    def actualizar_pregunta(self):
        if self.current_sintoma_index < len(self.sintomas):
            self.sintoma_label.config(text=f"{self.sintomas[self.current_sintoma_index]}")
            self.radio_var.set(0)
        else:
            self.mostrar_resultado()

    def mostrar_resultado(self):
        imc = self.peso_valor / ((self.estatura_valor / 100) ** 2)
        enfermedad, descripcion, probabilidad = diagnosticar(self.sintomas_seleccionados, self.edad_valor, imc)

        if enfermedad:
            resultado = f"Es posible que tenga '{enfermedad}' con una probabilidad {probabilidad}.\nDescripción: {descripcion}"
        else:
            resultado = "No se pudo determinar la enfermedad con los síntomas proporcionados."

        messagebox.showinfo("Resultado", resultado)
        self.root.destroy()

root = tk.Tk()
app = SistemaExpertoApp(root)
root.mainloop()

