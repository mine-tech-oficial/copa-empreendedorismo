from flask import Flask, render_template, request
import csv

app = Flask(__name__)

@app.route("/")
def hello_world():
    return render_template("index.html")

@app.route("/clubes")
def clubes():
    query = request.form.get("search")
    lista_clubes = []

    with open("clubes.csv", mode="r", encoding="utf-8") as csv_file:
        csv_reader = csv.DictReader(csv_file)
        if query == None:
            for row in csv_reader:
                lista_clubes.append(row)
        else:
            for row in csv_reader:
                if query in row["name"].lower() or query in row["description"].lower() or query in row["categories"].lower():
                    lista_clubes.append(row)

    return render_template("clubes.html", clubes=lista_clubes)

@app.get("/clubes/criar")
def formulario_clubes():
    return render_template("criar_clube.html")

@app.post("/clubes/criar")
def criar_clube():
    name = request.form.get("name")
    description = request.form.get("description")
    categories = request.form.get("categories")

    print(name)
    print(description)
    print(categories)

    data = [name, description, categories]

    with open("clubes.csv", mode="a", encoding="utf-8", newline="") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(data)

    return render_template("clubes.html")

if __name__ == "__main__":
    app.run(debug=True)
