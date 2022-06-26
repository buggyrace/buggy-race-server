# -*- coding: utf-8 -*-
"""Oauth Routes"""

from flask import Blueprint, redirect, request, url_for, current_app
from flask_login import login_required, current_user
from buggy_race_server.lib.http import Http, Url
import os

blueprint = Blueprint("oauth", __name__, url_prefix="/oauth")

http = Http({
    'Content-Type': 'application/json',
    'Accept': 'application/json'
})

@blueprint.route('/github')
@login_required
def github():
    """Redirect to github login url"""
    # TODO: Add state to prevent CORS attacks
    return redirect(str(Url.of('https://github.com/login/oauth/authorize', {
        'client_id': current_app.config['GITHUB_CLIENT_ID'],
        'redirect_uri': url_for('oauth.github_callback', _external=True),
        'allow_signup': 'true',
        'scope': 'user repo'
    })))

@blueprint.route('/github/callback')
@login_required
def github_callback():
    code = request.args.get('code')

    # TODO: Add state here too
    response = http.post('https://github.com/login/oauth/access_token', {}, {
        'client_id': current_app.config['GITHUB_CLIENT_ID'],
        'client_secret': current_app.config['GITHUB_CLIENT_SECRET'],
        'code': code,
        'redirect_uri': url_for('oauth.github_callback', _external=True)
    })

    current_user.github_access_token = response.json()['access_token']
    current_user.github_username = current_user.github.get('/user').json()['login']
    current_user.save()

    return redirect(url_for('user.settings'))
