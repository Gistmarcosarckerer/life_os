from flask import Blueprint, redirect, render_template, request, url_for

from backend.services.security_service import authenticate, login_user, logout_user

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    error = ""
    next_url = request.args.get("next") or "/"
    if request.method == "POST":
        password = request.form.get("password", "")
        next_url = request.form.get("next") or "/"
        if authenticate(password):
            login_user()
            return redirect(next_url if next_url.startswith("/") else "/")
        error = "Senha invalida."
    return render_template("login.html", error=error, next_url=next_url)


@auth_bp.route("/logout", methods=["GET", "POST"])
def logout():
    logout_user()
    return redirect(url_for("auth.login"))
