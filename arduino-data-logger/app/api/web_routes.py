from flask import Blueprint, render_template

web_bp = Blueprint('web_bp', __name__)

@web_bp.route('/')
def dashboard():
    return render_template('index.html')
