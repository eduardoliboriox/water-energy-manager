from flask import Flask, render_template, request, redirect, url_for, flash
import json
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = "chave-super-secreta"

ARQUIVO_DADOS = "consumos.json"

# -----------------------
# Utilitários de arquivo
# -----------------------
def carregar_dados():
    if os.path.exists(ARQUIVO_DADOS):
        with open(ARQUIVO_DADOS, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except:
                return []
    return []

def salvar_dados(dados):
    with open(ARQUIVO_DADOS, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)

# -----------------------
# Cálculo de Energia
# -----------------------
def calcular_energia(anterior, atual, tarifa=0.903602, incluir_taxas=True):
    consumo = atual - anterior
    valor_consumo = consumo * tarifa
    taxas_fixas = 0
    
    if incluir_taxas:
        taxas_fixas = 0.17 + 1.27 + 0.02 + 10.67

    total = valor_consumo + taxas_fixas
    return consumo, valor_consumo, taxas_fixas, total

# -----------------------
# Cálculo de Água
# -----------------------
def calcular_agua_sem_decimal(anterior, atual):
    diff = atual - anterior
    unidades = int(round(diff * 1000))
    if unidades < 0:
        unidades = 0

    faixas = [
        (10, 6.080),
        (10, 11.783),
        (10, 17.990)
    ]

    total = 0
    restante = unidades

    for limite, preco in faixas:
        usar = min(restante, limite)
        total += usar * preco
        restante -= usar
        if restante <= 0:
            break

    if restante > 0:
        total += restante * faixas[-1][1]

    return unidades, total

# -----------------------
# Rotas
# -----------------------
@app.route("/")
def index():
    return render_template("index.html")

# Energia
@app.route("/energia", methods=["GET", "POST"])
def energia():
    resultado = None

    if request.method == "POST":
        anterior = float(request.form["anterior"])
        atual = float(request.form["atual"])
        tarifa = float(request.form["tarifa"])
        incluir_taxas = "taxas" in request.form

        consumo, valor, taxas, total = calcular_energia(anterior, atual, tarifa, incluir_taxas)

        dados = carregar_dados()
        dados.append({
            "tipo": "energia_simulacao",
            "data": datetime.now().strftime("%m/%Y"),
            "anterior": anterior,
            "atual": atual,
            "consumo": consumo,
            "total": total,
            "timestamp": datetime.now().isoformat()
        })
        salvar_dados(dados)

        resultado = {
            "consumo": consumo,
            "valor": valor,
            "taxas": taxas,
            "total": total
        }

    return render_template("energia.html", resultado=resultado)

# Água
@app.route("/agua", methods=["GET", "POST"])
def agua():
    resultado = None

    if request.method == "POST":
        anterior = float(request.form["anterior"])
        atual = float(request.form["atual"])

        unidades, total = calcular_agua_sem_decimal(anterior, atual)

        dados = carregar_dados()
        dados.append({
            "tipo": "agua_simulacao",
            "data": datetime.now().strftime("%m/%Y"),
            "anterior": anterior,
            "atual": atual,
            "consumo_unidades": unidades,
            "total": total,
            "timestamp": datetime.now().isoformat()
        })
        salvar_dados(dados)

        resultado = {
            "unidades": unidades,
            "total": total
        }

    return render_template("agua.html", resultado=resultado)

# Contas reais
@app.route("/contas", methods=["GET", "POST"])
def contas():
    if request.method == "POST":
        tipo = request.form["tipo"]
        referencia = request.form["referencia"]
        consumo = request.form["consumo"]
        valor = float(request.form["valor"])

        dados = carregar_dados()
        dados.append({
            "tipo": tipo.lower(),
            "referencia": referencia,
            "consumo_informado": consumo,
            "valor_real": valor,
            "data_registro": datetime.now().strftime("%d/%m/%Y %H:%M")
        })
        salvar_dados(dados)

        flash("Conta registrada com sucesso!", "success")
        return redirect(url_for("contas"))

    return render_template("contas.html")

# Histórico
@app.route("/historico")
def historico():
    dados = carregar_dados()
    return render_template("historico.html", dados=dados)

# -----------------------
# Run
# -----------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
