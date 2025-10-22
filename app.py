import os
from typing import override
from uuid import uuid4
from icecream import ic
from flask import Flask, abort, redirect, render_template, request
from flask_login import LoginManager, UserMixin, login_required, login_user, logout_user
from werkzeug.security import check_password_hash, generate_password_hash
import csv

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
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if username is None or password is None:
            return abort(400)  # TODO: Put correct code
        if User.get_by_username(username) is not None:
            return abort(400)  # TODO: Render error form
        hashed_password = generate_password_hash(password)
        id = uuid4()
        with open("users.csv", mode="a", encoding="utf-8") as csv_file:
            csv_writer = csv.writer(csv_file)
            csv_writer.writerow([id, username, hashed_password])
        if not login_user(User(id, username, hashed_password)):
            return abort(400)  # TODO: Put correct code
        return redirect("/")
    else:
        return render_template("sign_up.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
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
    else:
        return render_template("login.html")


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


@app.route("/clubes/criar", methods=["GET", "POST"])
@login_required
def criar_clubes():
    if request.method == "GET":
        return render_template("criar_clube.html")

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
