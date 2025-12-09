import csv
import os
from typing import override
from uuid import uuid4

from flask import Flask, abort, redirect, render_template, request
from flask_login import (
    LoginManager,
    UserMixin,
    current_user,
    login_required,
    login_user,
    logout_user,
)
from icecream import ic
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev")
login_manager = LoginManager(app)


class User(UserMixin):
    id: str
    username: str
    hashed_password: str

    def __init__(self, id: str, username: str, hashed_password: str):
        super().__init__()
        self.id = id
        self.username = username
        self.hashed_password = hashed_password

    @override
    def get_id(self) -> str:
        return self.id

    @staticmethod
    def get(id: str):
        with open("users.csv", mode="r", encoding="utf-8") as csv_file:
            csv_reader = csv.DictReader(csv_file)
            for line in csv_reader:
                if line["id"] == id:
                    return User(line["id"], line["username"], line["hashed_password"])
        return None

    @staticmethod
    def get_by_username(username: str):
        with open("users.csv", mode="r", encoding="utf-8") as csv_file:
            csv_reader = csv.DictReader(csv_file)
            for line in csv_reader:
                if line["username"] == username:
                    return User(line["id"], line["username"], line["hashed_password"])
        return None


@login_manager.user_loader
def load_user(id: str):
    return User.get(id)


@app.route("/")
def hello_world():
    return render_template("index.html")


@app.route("/sign_up", methods=["GET", "POST"])
def sign_up():
    if request.method == "GET":
        return render_template("sign_up.html")

    username = request.form.get("username")
    password = request.form.get("password")
    if username is None or password is None:
        return abort(400)  # TODO: Put correct code
    if User.get_by_username(username) is not None:
        return abort(400)  # TODO: Render error form
    hashed_password = generate_password_hash(password)
    id = uuid4()
    with open("users.csv", mode="a", encoding="utf-8", newline="") as csv_file:
        csv_writer = csv.writer(csv_file)
        csv_writer.writerow([id, username, hashed_password])
    if not login_user(User.get_by_username(username)):
        return abort(400)  # TODO: Put correct code
    return redirect("/")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    username = request.form.get("username")
    password = request.form.get("password")
    if username is None or password is None:
        return abort(400)  # TODO: Put correct code
    user = User.get_by_username(username)
    if user is None or not check_password_hash(user.hashed_password, password):
        return abort(400)  # TODO: Render error form
    if not login_user(user):
        return abort(400)  # TODO: Put correct code
    return redirect("/")


@app.route("/logout")
def logout():
    logout_user()
    return redirect("/")


@app.route("/clubes")
def clubes():
    query = request.form.get("search")
    lista_clubes = []

    with open("clubes.csv", mode="r", encoding="utf-8") as csv_file:
        csv_reader = csv.DictReader(csv_file)
        if query is None:
            for row in csv_reader:
                lista_clubes.append(row)
        else:
            for row in csv_reader:
                if (
                    query in row["name"].lower()
                    or query in row["description"].lower()
                    or query in row["categories"].lower()
                ):
                    lista_clubes.append(row)

    return render_template("clubes.html", clubes=lista_clubes)


@app.route("/clubes/<id>", methods=["GET", "POST"])
def clube(id: str):
    clube = None
    eventos = []

    with open("clubes.csv", mode="r", encoding="utf-8") as csv_file:
        csv_reader = csv.DictReader(csv_file)
        for row in csv_reader:
            if id == row["id"]:
                clube = row

    with open("eventos.csv", mode="r", encoding="utf-8") as csv_file:
        csv_reader = csv.DictReader(csv_file)
        for row in csv_reader:
            if id == row["club_id"]:
                eventos.append(row)
                eventos[-1]["user_confirmed"] = False

    with open("confirmed.csv", mode="r", encoding="utf-8") as csv_file:
        csv_reader = csv.DictReader(csv_file)
        for row in csv_reader:
            if current_user.id == row["user_id"]:
                for evento in eventos:
                    if evento["id"] == row["event_id"]:
                        evento["user_confirmed"] = True

    if request.method == "GET":
        return render_template("clube.html", clube=clube, eventos=eventos)

    if clube is None:
        abort(404)

    if not current_user.is_authenticated or current_user.id != clube["creator_id"]:
        abort(400)  # TODO: Put correct code

    id = str(uuid4())
    name = request.form.get("name")
    place = request.form.get("place")
    datetime = request.form.get("datetime")  # TODO: Represent as actual datetime

    data = [id, name, place, datetime, 0, clube["id"]]

    with open("eventos.csv", mode="a", encoding="utf-8", newline="") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(data)

    return redirect("/clubes/" + clube["id"])


@app.route("/clubes/confirmar/<event_id>")
@login_required
def confirm(event_id: str):
    clube_id = None
    eventos = []

    with open("eventos.csv", mode="r", encoding="utf-8") as csv_file:
        csv_reader = csv.reader(csv_file)
        for row in csv_reader:
            if event_id == row[0]:
                clube_id = row[-1]
            eventos.append(row)

    if clube_id is None:
        abort(404)

    with open("confirmed.csv", mode="r", encoding="utf-8") as csv_file:
        csv_reader = csv.DictReader(csv_file)
        for row in csv_reader:
            print(row)
            print(current_user.id)
            if event_id == row["event_id"] and current_user.id == row["user_id"]:
                return redirect("/clubes/" + clube_id)

    with open("eventos.csv", mode="w", encoding="utf-8") as csv_file:
        csv_writer = csv.writer(csv_file)
        for evento in eventos:
            if evento[-1] == clube_id:
                evento[-2] = str(int(evento[-2]) + 1)
            csv_writer.writerow(evento)

    with open("confirmed.csv", mode="a", encoding="utf-8", newline="") as csv_file:
        csv_writer = csv.writer(csv_file)
        csv_writer.writerow([event_id, current_user.id])

    return redirect("/clubes/" + clube_id)


@app.route("/clubes/criar", methods=["GET", "POST"])
@login_required
def criar_clubes():
    if request.method == "GET":
        return render_template("criar_clube.html")

    if not current_user.is_authenticated:
        abort(400)  # TODO: Put correct code

    id = str(uuid4())
    name = request.form.get("name")
    description = request.form.get("description")
    categories = request.form.get("categories")
    image = request.files.get("image")

    if image:
        image.save("static/assets/clubes/" + id + ".jpg")

    data = [id, name, description, categories, current_user.id]

    with open("clubes.csv", mode="a", encoding="utf-8", newline="") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(data)

    return redirect("/clubes")


if __name__ == "__main__":
    app.run(debug=True)
