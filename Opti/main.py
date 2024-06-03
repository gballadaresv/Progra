from pandas import read_excel
from gurobipy import Model, quicksum, GRB
from pprint import pprint
from collections import defaultdict
from openpyxl import load_workbook

# Set timer 30 min

### Conjuntos
nutrientes = range(0, 9)
nombres_nutrientes = [
    "Proteinas", "Carbohidratos", "Vitaminas", "Minerales",
    "Calcio", "Magnesio", "Grasas", "Sodio", "Azucares"
]
comidas = range(0, 33)
nombres_comidas = [
    "Carne", "Pavo", "Chancho", "Pollo", "Atun", "Huevo",
    "Porotos", "Pure", "Arroz", "Fideos", "Papas", "Lentejas",
    "Zanahoria", "Lechuga", "Tomate", "Brocoli", "Coliflor", "Apio", "Manzana", 
    "Platano", "Pera", "Naranja", "Durazno", "Piña", "Leche",
    "Yogurt", "Flan", "Arroz con leche", "Mousse", "Pan",
    "Cereal", "Galletones", "Barritas"
] # Lista con los nombres de la comida, terminar
dias = range(0, 5)
semanas = range(0, 52)
regiones = range(0, 16)

### Database
# Usar el read_excel de pandas
path_aporte_nutricional = "Datos/aporte_nutricional.xlsx"
path_costos_almacenamiento = "Datos/Costos_almacenamiento.xlsx"
path_costos = "Datos/Costos.xlsx"
path_demanda_comida = "Datos/Demanda_comida.xlsx"
path_disponibilidad = "Datos/Disponibilidad.xlsx"
path_requerimiento = "Datos/Requerimiento_nutricional.xlsx"

#Obtencion datos de demanda 
demandas = [[524822 for i in range(0,5)] for i in range(0,52)]

#Obtencion datos aporte nutricional
aportes = []
lectura_aportes = read_excel(path_aporte_nutricional)
for linea in lectura_aportes.iterrows():
    lista_linea = [dato for dato in linea[1][1:]]
    aportes.append(lista_linea)

#Obtencion datos costos de almacenamiento

costos_stg = []
lectura_costos_stg = read_excel(path_costos_almacenamiento)
for linea in lectura_costos_stg.iterrows():
    lista_linea = [dato for dato in linea[1][1:]]
    costos_stg.append(lista_linea[0])

#Obtencion datos costos alimentos
costos = []
lectura_costos = read_excel(path_costos)
for linea in lectura_costos.iterrows():
    lista_linea = [dato for dato in linea[1][1:]]
    costos.append(lista_linea)

#Obtencion datos requerimientos nutricionales
cantidades_nutrientes = []
lectura_requerimiento = read_excel(path_requerimiento)
for linea in lectura_requerimiento.iterrows():
    lista_linea = [dato for dato in linea[1][1:]]
    cantidades_nutrientes.append(lista_linea[0])

#Obtencion datos disponibilidad
disponibilidad = []
lectura_disponibilidad = read_excel(path_disponibilidad)
for linea in lectura_disponibilidad.iterrows():
    lista_linea = [dato for dato in linea[1][1:]]
    disponibilidad.append(lista_linea)

presupuesto = 300566878



model = Model()

### Vars
w = model.addVars(comidas, dias, semanas, vtype=GRB.INTEGER, name="w_jdm")
x = model.addVars(comidas, dias, semanas, vtype=GRB.INTEGER, name="x_jdm")
y = model.addVars(dias, semanas, vtype=GRB.BINARY, name="y_dm") ### Es var o param)?
i = model.addVars(comidas, dias, semanas, vtype=GRB.INTEGER, name="i_jdm")
z = model.addVars(comidas, dias, semanas, vtype=GRB.BINARY, name="z_jdm")

### Params
b = {(f): cantidades_nutrientes[f] for f in nutrientes } #LISTO
c = {(j, r): costos[j][r] for j in comidas for r in regiones} #LISTO
a = {(j, f): aportes[j][f] for j in comidas for f in nutrientes}  #LISTO
q = {(m, d): demandas[m][d] for m in semanas for d in dias} #Demanda puesta diaria y semanalmente por region, elegir cual usar
n = {(j, m): disponibilidad[j][m] for j in comidas for m in semanas} #
g = {r: costos_stg[r] for r in regiones} #LISTO
# Params hay clases)?

### Restrs
#1
model.addConstrs(
    (quicksum(x[j, d, m] * a[j, f]for j in comidas) >= b[f] 
     for d in dias for m in semanas for f in nutrientes[:7]),
     name="Cantidad minima de nutrientes"
)

#2
model.addConstrs(
    (quicksum(x[j, d, m] * a[j, f]for j in comidas) <= b[f] 
     for d in dias for m in semanas for f in nutrientes[7:]),
     name="Cantidad maxima de nutrientes"
)

#3.1
model.addConstrs(
    (quicksum(z[j, d, m] for d in dias) <= 2 for j in comidas for m in semanas),
    name="Repeticiones de comida maxima"
)

#3.2
model.addConstrs(
    ((z[j, d, m] - 10**-6) <= z[j, d+1, m] for j in comidas 
     for d in dias[:4] for m in semanas),
    name="No repetir comida 2 dias seguidos" 
)

#3.3
model.addConstrs(
    (z[j, d+1, m] <= (z[j, d, m] + 10**-6)  for j in comidas 
     for d in dias[:4] for m in semanas),
    name="No repetir comida 2 dias seguidos" 
)

#4.1
model.addConstrs(
    (x[j, d, m] <= 100000000000000000000 * y[d, m]
    for j in comidas for d in dias for m in semanas),
    name="Relacion entre X e Y"
)

#4.2
model.addConstrs(
    (y[d, m] <= x[j, d, m]
    for j in comidas for d in dias for m in semanas),
    name= "Relacion entre X e Y"
)

#5
model.addConstrs(
    (z[j, d, m] <= y[d, m] for j in comidas for d in dias for m in semanas),
    name="Relacion entre Z e Y"
)

#6
# Presupuesto
model.addConstr(
    quicksum(
        quicksum(
            quicksum(
                quicksum(
                    c[j, r] * x[j, d, m] + g[r] * i[j, d, m]
                    for r in regiones
                ) for m in semanas
            ) for d in dias
        ) for j in comidas 
    ) <= presupuesto,
    name="No superar el presupuesto"
) 

#7
model.addConstrs(
    (quicksum(x[j, d, m] + i[j, d, m] for j in comidas) >= q[m, d]
     for d in dias for m in semanas),
     name="Satisfacer demanda"
)

#8
model.addConstrs(
    (quicksum(w[j, d, m] for d in dias) <= n[j, m]
    for j in comidas for m in semanas),
    name="No se puede compras mas de la comida disponible"
)

#9
model.addConstrs(
    (i[j, 1, 1] == 0 for j in comidas), name="Inventario comienza vacio"
)

#10
model.addConstrs(
    (i[j, d, 1] == i[j, d-1, 1] + w[j, d, 1] - x[j, d, 1] for j in comidas for d in dias[1:]),
    name="Primera semana de inventario"
)

#11
model.addConstrs(
    (i[j, d, m] == i[j, d-1, m] + w[j, d, m] - x[j, d, m] for j in comidas for d in dias[1:] for m in semanas[1:]),
    name="Inventario luego de la primera semana"
)

#12
# Completar indices
model.addConstrs(
    (quicksum(z[j, d, m] for j in comidas[:6]) +
     quicksum(z[j, d, m] for j in comidas[6:13]) +
     quicksum(z[j, d, m] for j in comidas[13:19]) +
     quicksum(z[j, d, m] for j in comidas[19:25]) >= 4
     for d in dias for m in semanas),
     name="Almuerzos completos con todos los tipos de comida"
)

#13
model.addConstrs(
    (quicksum(z[j, d, m] for j in comidas[25:30]) +
    quicksum(z[j, d, m] for j in comidas[30:]) >= 2
    for d in dias for m in semanas),
    name="Desayunos completos con todos los tipos de comida"
)

### Funcion objetivo
model.setObjective(
    quicksum(
        quicksum(
            quicksum(
                quicksum(
                    c[j, r] * x[j, d, m] + g[r] * i[j, d, m]
                    for r in regiones
                ) for m in semanas
            ) for d in dias
        ) for j in comidas
    )
)


model.optimize()

### Manejo de resultados
print("\n"+"-"*25+"Manejo de resultados"+"-"*25+"\n")

print(f"El valor óptimo del problema es de ${model.ObjVal}\n")

# Hacer prints de 