from flask import Blueprint

from views.auth.auth import auth_bp
from views.book.book import book_bp

views_bp = Blueprint("views", __name__)

views_bp.register_blueprint(auth_bp)
views_bp.register_blueprint(book_bp)
