import functools
import os

from flask import (
    Blueprint, Flask, g, redirect, render_template, request, session, url_for
)

bp = Blueprint('guga', __name__, url_prefix='/guga')

@bp.route('/')
def guga():
    return render_template('guga/guga.html',
                           background_image_url=url_for("static", filename="/guga/MyGO_background.png"),
                           panel_image_url=url_for("static", filename="/guga/gugugaga.png"),
    )
