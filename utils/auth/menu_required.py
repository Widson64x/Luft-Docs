# utils/auth/menu_required.py

from functools import wraps
from flask import session, abort
from utils.auth.permissions import can

def menu_required(menu_name):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            menus = session.get('menus', [])
            if not can(menus, menu_name):
                abort(403)
            return f(*args, **kwargs)
        return wrapper
    return decorator
