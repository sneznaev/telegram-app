from flask import Blueprint

gallery_bp = Blueprint('gallery', __name__, template_folder='templates', static_folder='static')

from . import views
