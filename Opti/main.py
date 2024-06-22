from pandas import read_excel
from gurobipy import Model, quicksum, GRB

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
    "Zanahoria", "Lechuga", "Tomate", "Brocoli", "Coliflor", "Apio", 
    "Manzana", "Platano", "Pera", "Naranja", "Durazno", "Piña", 
    "Leche", "Yogurt", "Flan", "Arroz con leche", "Mousse", 
    "Pan", "Cereal", "Galletones", "Barritas"
]
dias = range(5)
semanas = range(52)
regiones = range(16)

### Database
#Obtencion datos de demanda 
demandas = []
lectura_demanda = read_excel("Datos/Demanda_comida.xlsx")
for linea in lectura_demanda.iterrows():
    lista_linea = [dato for dato in linea[1]]
    demandas.append(lista_linea[1:])

#Obtencion datos aporte nutricional
aportes = []
lectura_aportes = read_excel("Datos/aporte_nutricional.xlsx")
for linea in lectura_aportes.iterrows():
    lista_linea = [dato for dato in linea[1][1:]]
    aportes.append(lista_linea)

#Obtencion datos costos de almacenamiento
costos_stg = []
lectura_costos_stg = read_excel("Datos/Costos_almacenamiento.xlsx")
for linea in lectura_costos_stg.iterrows():
    lista_linea = [dato for dato in linea[1][1:]]
    costos_stg.append(lista_linea)

#Obtencion datos costos alimentos
costos = []
lectura_costos = read_excel("Datos/Costos.xlsx")
for linea in lectura_costos.iterrows():
    lista_linea = [dato for dato in linea[1][1:]]
    costos.append(lista_linea)

#Obtencion datos requerimientos nutricionales
cantidades_nutrientes = []
lectura_requerimiento = read_excel("Datos/Requerimiento_nutricional.xlsx")
for linea in lectura_requerimiento.iterrows():
    lista_linea = [dato for dato in linea[1][1:]]
    cantidades_nutrientes.append(lista_linea[0])

#Obtencion datos disponibilidad
disponibilidad = []
lectura_disponibilidad = read_excel("Datos/Disponibilidad3.xlsx")
for linea in lectura_disponibilidad.iterrows():
    lista_linea = [dato for dato in linea[1][1:]]
    disponibilidad.append(lista_linea)

#Obtencion de lista de clases
lectura_clases = read_excel("Datos/Clases_binario.xlsx")
clases = [dato[1][0] for dato in lectura_clases.iterrows()]

# Fuente detallada en el informe
presupuesto = 300566878000


model = Model()

# Tiempo máximo de la ejecución del código
model.setParam("TimeLimit", 1800)

### Vars
w = model.addVars(comidas, dias, semanas, vtype=GRB.INTEGER, name="w_jdm")
x = model.addVars(comidas, dias, semanas, regiones, vtype=GRB.INTEGER, name="x_jdmr")
i = model.addVars(comidas, dias, semanas, regiones, vtype=GRB.INTEGER, name="i_jdmr")
z = model.addVars(comidas, dias, semanas, vtype=GRB.BINARY, name="z_jdm")

### Params
b = {(f): cantidades_nutrientes[f] for f in nutrientes } 
c = {(j, r): costos[j][r] for j in comidas for r in regiones}
a = {(j, f): aportes[j][f] for j in comidas for f in nutrientes}
q = {(r, m): demandas[r][m] for r in regiones for m in semanas}
n = {(j, m): disponibilidad[j][m] for j in comidas for m in semanas}
g = {(r, j): costos_stg[r][j] for r in regiones for j in comidas}
y = {(m): clases[m] for m in semanas}

### Restrs
#1
model.addConstrs(
    (quicksum(x[j, d, m, r] * a[j, f]for j in comidas) >= b[f] 
     for d in dias for m in semanas for r in regiones for f in nutrientes[:7]),
     name="Cantidad minima de nutrientes"
)
 
#2
# Gurobi no tiene soporte para restricciones de desigualdad (no igual),
# por lo que hay que separarla en 2 restricciones, esto equivale a un !=
model.addConstrs(
    ((z[j, d, m] - 10**-6) <= z[j, d+1, m] for j in comidas 
     for d in dias[:4] for m in semanas),
    name="No repetir comida 2 dias seguidos" 
)
model.addConstrs(
    (z[j, d+1, m] <= (z[j, d, m] + 10**-6)  for j in comidas 
     for d in dias[:4] for m in semanas),
    name="No repetir comida 2 dias seguidos" 
)

#3
model.addConstrs(
    (x[j, d, m, r] >= y[m]
    for j in comidas for d in dias for m in semanas for r in regiones),
    name= "Relacion entre X e Y"
)

#4
model.addConstrs(
    (z[j, d, m] <= y[m] for j in comidas for d in dias for m in semanas),
    name="Relacion entre Z e Y"
)

#5
model.addConstr(
    quicksum(
        quicksum(
            quicksum(
                quicksum(
                    c[j, r] * x[j, d, m, r] + g[r, j] * i[j, d, m, r]
                    for r in regiones
                ) for m in semanas
            ) for d in dias
        ) for j in comidas 
    ) <= presupuesto,
    name="No superar el presupuesto"
)

#6
model.addConstrs(
    (quicksum(x[j, d, m, r] + i[j, d, m, r] for j in comidas) >= q[r, m]
     for d in dias for m in semanas for r in regiones),
     name="Satisfacer demanda"
)

#7
model.addConstrs(
    (quicksum(w[j, d, m] for d in dias) <= n[j, m]
    for j in comidas for m in semanas),
    name="No se puede compras mas de la comida disponible"
)
 
#8
model.addConstrs(
    (i[j, 1, 1, r] == 0 for j in comidas for r in regiones),
    name="Inventario comienza vacio"
) 

#9
model.addConstrs(
    (i[j, 4, 51, r] == 0 for j in comidas for r in regiones),
    name="Inventario termina vacio"
)


#10
model.addConstrs(
    (i[j, d, m, r] == i[j, d-1, m, r] + w[j, d, m] - x[j, d, m, r] 
     for j in comidas for d in dias[1:] for r in regiones for m in semanas[1:]),
    name="Inventario luego de la primera semana"
) 

#11
model.addConstrs(
    (quicksum(z[j, d, m] for j in comidas[:6]) == 1
     for d in dias for m in semanas),
     name="Almuerzos completos con todos los tipos de comida"
)
model.addConstrs(
    (quicksum(z[j, d, m] for j in comidas[6:12]) == 1
     for d in dias for m in semanas),
     name="Almuerzos completos con todos los tipos de comida"
)
model.addConstrs(
    (quicksum(z[j, d, m] for j in comidas[12:18]) == 1
     for d in dias for m in semanas),
     name="Almuerzos completos con todos los tipos de comida"
)
model.addConstrs(
    (quicksum(z[j, d, m] for j in comidas[18:24]) == 1
     for d in dias for m in semanas),
     name="Almuerzos completos con todos los tipos de comida"
)


#12
model.addConstrs(
    (quicksum(z[j, d, m] for j in comidas[24:29]) == 1
         for d in dias for m in semanas),
    name="Desayunos completos con todos los tipos de comida"
)
model.addConstrs(
    (quicksum(z[j, d, m] for j in comidas[29:]) == 1
    for d in dias for m in semanas),
    name="Desayunos completos con todos los tipos de comida"
)

### Funcion objetivo
model.setObjective(
    quicksum(
        quicksum(
            quicksum(
                quicksum(
                    c[j, r] * x[j, d, m, r] + g[r, j] * i[j, d, m, r]
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


divisor = int(sum(z[j, d, m].x for j in comidas for d in dias for m in semanas))
def porcentajeador(x):
    return x * 100 / divisor

porcentajes = []
for j in comidas:
    porcentaje = round(porcentajeador(sum(z[j, d, m].x for d in dias for m in semanas)), 4)
    print(f"El porcentaje de {nombres_comidas[j]} es del {porcentaje}%")
    porcentajes.append(porcentaje)



carnes = list(zip(nombres_comidas[:6], porcentajes[6:]))
acompañamientos = list(zip(nombres_comidas[6:12], porcentajes[6:12]))
verduras = list(zip(nombres_comidas[12:18], porcentajes[12:18]))
frutas = list(zip(nombres_comidas[18:24], porcentajes[18:24]))
lacteos = list(zip(nombres_comidas[24:29], porcentajes[24:29]))
desayunos = list(zip(nombres_comidas[29:], porcentajes[29:]))

carnes = sorted(carnes, key=lambda lista: lista[1], reverse=True)
acompañamientos = sorted(acompañamientos, key=lambda lista: lista[1], reverse=True)
verduras = sorted(verduras, key=lambda lista: lista[1], reverse=True)
frutas = sorted(frutas, key=lambda lista: lista[1], reverse=True)
lacteos = sorted(lacteos, key=lambda lista: lista[1], reverse=True)
desayunos = sorted(desayunos, key=lambda lista: lista[1], reverse=True)

listas = [carnes, acompañamientos, verduras, frutas, lacteos, desayunos]

def maximo(lista):
    return max(lista, key=lambda lista: lista[1])[1]


carnes_max = [carnes[i][0] for i in range(len(carnes)) if carnes[i][1] == maximo(carnes)]
acompañamientos_max = [acompañamientos[i][0] for i in range(len(acompañamientos)) if acompañamientos[i][1] == maximo(acompañamientos)]
verduras_max = [verduras[i][0] for i in range(len(verduras)) if verduras[i][1] == maximo(verduras)]
frutas_max = [frutas[i][0] for i in range(len(frutas)) if frutas[i][1] == maximo(frutas)]
lacteos_max = [lacteos[i][0] for i in range(len(lacteos)) if lacteos[i][1] == maximo(lacteos)]
desayunos_max = [desayunos[i][0] for i in range(len(desayunos)) if desayunos[i][1] == maximo(desayunos)]

print("\n")

if len(carnes_max) == 1:
    print(f"La carne más consumida es: {carnes_max[0]}")
else:
    string = "Las carnes más consumidas son: "
    for i in range(len(carnes_max)-1):
        string += f"{carnes_max[i]} "
    print(string)

if len(acompañamientos_max) == 1:
    print(f"El acompañamiento más consumido es: {acompañamientos_max[0]}")
else:
    string = "Los acompañamientos más consumidos son: "
    for i in range(len(acompañamientos_max)):
        string += f"{acompañamientos_max[i]} "
    print(string)

if len(verduras_max) == 1:
    print(f"La verdura más consumida es: {verduras_max[0]}")
else:
    string = "Las verduras más consumidas son: "
    for i in range(len(verduras_max)):
        string += f"{verduras_max[i]} "
    print(string)

if len(frutas_max) == 1:
    print(f"La fruta más consumida es: {frutas_max[0]}")
else:
    string = "Las frutas más consumidas son: "
    for i in range(len(frutas_max)):
        string += f"{frutas_max[i]} "
    print(string)

if len(lacteos_max) == 1:
    print(f"El lácteo más consumido es: {lacteos_max[0]}")
else:
    string = "Los lácteos más consumidos son: "
    for i in range(len(lacteos_max)):
        string += f"{lacteos_max[i]} "
    print(string)

if len(desayunos_max) == 1:
    print(f"El desayuno más consumido es: {desayunos_max[0]}")
else:
    string = "Los desayunos más consumidos son: "
    for i in range(len(desayunos_max)):
        string += f"{desayunos_max[i]} "
    print(string)