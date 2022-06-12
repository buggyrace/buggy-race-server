# -*- coding: utf-8 -*-
"""Buggy views."""
import os
import csv
import time
import re
import threading
from datetime import datetime
from flask import Blueprint, render_template, request, flash, redirect, url_for
from functools import wraps
from flask_login import login_required, current_user
from buggy_race_server.race.models import Race
from buggy_race_server.race.forms import RaceForm
from buggy_race_server.utils import flash_errors

blueprint = Blueprint("race", __name__, url_prefix="/races", static_folder="../static")

@blueprint.route("/")
@login_required
def list_races():
    """Admin list of all races."""
    if not current_user.is_buggy_admin:
      abort(403)
    else:
      races = sorted(Race.query.all(), key=lambda race: (race.start_at))
      form = RaceForm(request.form)
      return render_template("admin/races.html", races=races, form=form)

@blueprint.route("/new", methods=["GET", "POST"])
@login_required
def new_race():
    """Admin list of all races."""
    if not current_user.is_buggy_admin:
      abort(403)
    else:
      form = RaceForm(request.form)
      if request.method == "POST":
        if form.validate_on_submit():
            Race.create(
                title=form.title.data,
                desc=form.desc.data,
                cost_limit=form.cost_limit.data,
                start_at=form.start_at.data,
                is_visible=form.is_visible.data,
            )
            flash(f"Race created, to run at {form.start_at.data}", "success")
            return redirect(url_for("race.list_races"))
        else:
            flash("Did not create a race!", "danger")
            flash_errors(form)
      return render_template("races/new-race.html", form=form)

@blueprint.route("/<league>/<race_slug>/<data_format>")
@blueprint.route("/<league>/<race_slug>")
def race_results(league, race_slug, data_format=None):
    if data_format == 'csv':
        return "TODO:CSV"
    time_match = re.match(r"(\d{4}-\d{2}-\d{2})-(\d{2})-(\d{2})", race_slug)
    if not time_match: # YYY MM DD HH mm
        flash("No race matches those criteria", "warning")
        return redirect(url_for("public.announce_races"))
    time_str = f"{time_match.group(1)} {time_match.group(2)}:{time_match.group(3)}:00.000000"
    #start_at=datetime.fromisoformat(time_str).replace(second=0,microsecond=0)
    race = Race.query.filter_by(league=league, start_at=time_str).first()
    buggies = []
    with open('buggy_race_server/static/races/fy/2021-06-02-23-00.csv', newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            buggies.append(row)
    return render_template("races/result.html",
      league=league,
      slug=race_slug,
      race=race,
      buggies=buggies
    )
  