from pandas import read_excel
from gurobipy import Model, quicksum, GRB
from pprint import pprint


# Set timer 30 min

### Conjuntos
nutrientes = range(1, 10)
nombres_nutrientes = [
    "Proteinas", "Carbohidratos", "Vitaminas", "Minerales",
    "Calcio", "Magnesio", "Grasas", "Sodio", "Azucares"
]
comidas = list # Contar cuántas comidas hay
nombres_comidas = [
    "Carne", "Pavo", "Chamcho", "pollo"
] # Lista con los nombres de la comida, terminar
dias = range(1, 8)
semanas = range(1, 53)
regiones = range(1, 17)
ciclos = range(1, 5)

### Database
# Usar el read_excel de pandas
cantidades_nutrientes = list
costos = list
aportes = list
#presupuesto = int
demandas = list
disponibilidad = list
costos_stg = list


model = Model()

### Vars
w = model.addVars(comidas, dias, semanas, vtype=GRB.INTEGER, name="w_jdm")
x = model.addVars(comidas, dias, semanas, vtype=GRB.INTEGER, name="x_jdm")
y = model.addVars(dias, semanas, vtype=GRB.BINARY, name="y_dm") ### Es var o param)?
i = model.addVars(comidas, dias, semanas, vtype=GRB.INTEGER, name="i_jdm")
z = model.addVars(comidas, dias, semanas, vtype=GRB.BINARY, name="z_jdm")

### Params
b = {(f,s): cantidades_nutrientes[f][s] for f in nutrientes for s in ciclos}
c = {(j, m, r): costos[j][m][r] for j in comidas for m in semanas for r in regiones}
a = {(f, j): aportes[f][j] for f in nutrientes for j in comidas}
q = {(d, m): demandas[d][m] for d in dias for m in semanas}
n = {(j, m, r): disponibilidad[j][m][r] for j in comidas for m in semanas for r in regiones}
g = {j: costos_stg[j] for j in comidas}
# Params hay clases)?

### Restrs
#1
model.addConstrs(
    (quicksum(x[j, d, m] * a[f, j]for j in comidas) >= b[f, s] 
     for d in dias for m in semanas for f in nutrientes[:7] for s in ciclos),
     name="Cantidad minima de nutrientes"
)

#2
model.addConstrs(
    (quicksum(x[j, d, m] * a[f, j]for j in comidas) <= b[f, s] 
     for d in dias for m in semanas for f in nutrientes[7:] for s in ciclos),
     name="Cantidad maxima de nutrientes"
)

#3.1
model.addConstrs(
    (quicksum(z[j, d, m] for d in dias) <= 2 for j in comidas for m in semanas),
    name="Repeticiones de comida maxima"
)

#3.2
model.addConstrs(
    (z[j, d, m] != z[j, d+1, m] for j in comidas for d in dias[:7] for m in semanas),
    name="No repetir comida 2 dias seguidos" 
)

#4.1
model.addConstrs(
    (x[j, d, m] <= 100000000000000000000 * y[d, m]
    for j in comidas for d in dias for m in semanas),
    name="Relacion entre X e Y"
)

#4.2
#Falta agregarla

#5
model.addConstrs(
    (z[j, d, m] <= y[d, m] for j in comidas for d in dias for m in semanas),
    name="Relacion entre Z e Y"
)

#6
# Presupuesto, eliminar)?
""" model.addConstr(
    quicksum(
        quicksum(
            quicksum(
                quicksum(
                    c[j, m, r] * x[j, d, m] + g[j] * i[j, d, m] <= presupuesto
                    for r in regiones
                ) for m in semanas
            ) for d in dias
        ) for j in comidas
    ),
    name="No superar el presupuesto"
) """

#7
model.addConstrs(
    (quicksum(x[j, d, m] + i[j, d, m] for j in comidas) >= q[d, m]
     for d in dias for m in semanas),
     name="Satisfacer demanda"
)

#8
model.addConstrs(
    ((quicksum(w[j, d, m]) for d in dias) <= n[j, m, r]
    for j in comidas for r in regiones for m in semanas),
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
    (quicksum(z[j, d, m] for j in None) +
     quicksum(z[j, d, m] for j in None) +
     quicksum(z[j, d, m] for j in None) +
     quicksum(z[j, d, m] for j in None)
     for d in dias for m in semanas),
     name="Almuerzos completos con todos los tipos de comida"
)

#13
model.addConstrs(
    (quicksum(z[j, d, m] for j in None) +
    quicksum(z[j, d, m] for j in None)
    for d in dias for m in semanas),
    name="Desayunos completos con todos los tipos de comida"
)

### Funcion objetivo
model.setObjective(
    quicksum(
        quicksum(
            quicksum(
                quicksum(
                    c[j, m, r] * x[j, d, m] + g[j] * i[j, d, m]
                    for r in regiones
                ) for m in semanas
            ) for d in dias
        ) for j in comidas
    )
)


model.optimize()

### Manejo de resultados
print("\n"+"-"*25+"Manejo de resultados"+"-"*25+"\n")

print(f"El valor óptimo del problema es de ${model.objVal}\n")

# Hacer prints de 