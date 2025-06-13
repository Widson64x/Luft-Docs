from flask import Blueprint, render_template
from utils.data.module_utils import carregar_modulos

user_bp = Blueprint('user', __name__)

@user_bp.route("/user/<username>", methods=["POST"])
def user_profile(username):
    modulos, _ = carregar_modulos()
    print(username)
    return render_template('index.html', modulos=modulos, modulo_atual=None)
