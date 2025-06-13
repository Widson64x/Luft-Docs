# routes/info.py
from flask import Blueprint, render_template

info = Blueprint('info', __name__)

@info.route('/info_login')
def login_info():
    """
    Página que informa que só é possível acessar via Luft Informa.
    """
    return render_template('info_login.html')
