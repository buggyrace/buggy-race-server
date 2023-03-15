# -*- coding: utf-8 -*-
"""Buggy views."""

import csv
import re
from datetime import datetime

from flask import Blueprint, flash, redirect, render_template, request, url_for, abort, current_app
from flask_login import current_user, login_required
from buggy_race_server.race.forms import RaceForm
from buggy_race_server.race.models import Race
from buggy_race_server.utils import flash_errors
from buggy_race_server.config import ConfigSettingNames

blueprint = Blueprint("race", __name__, url_prefix="/races", static_folder="../static")

@blueprint.route("/", strict_slashes=False)
@login_required
def list_races():
    """Admin list of all races."""
    if not current_user.is_buggy_admin:
      abort(403)
    else:
      races = sorted(Race.query.all(), key=lambda race: (race.start_at))
      form = RaceForm(request.form)
      return render_template(
         "admin/races.html",
         races=races,
         form=form,
         date_today=datetime.today().date(),
      )

@blueprint.route("/new", methods=["GET", "POST"], strict_slashes=False)
@login_required
def new_race():
    """Create a new race."""
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
      return render_template(
         "admin/race_new.html",
         form=form,
         default_race_cost_limit=current_app.config[ConfigSettingNames.DEFAULT_RACE_COST_LIMIT.name],
      )

@blueprint.route("/<race_id>/edit", methods=["GET", "POST"])
@login_required
def edit_race(race_id):
    """Edit an existing race (differs from new race because may
       have some results?)."""
    if not current_user.is_buggy_admin:
        abort(403)
    race = Race.get_by_id(race_id)
    if race is None:
       flash("No such race", "danger")
       abort(404)
    form = RaceForm(request.form, obj=race)
    if request.method == "POST":
        if form.validate_on_submit():
            race.title = form.title.data.strip()
            race.desc = form.desc.data.strip()
            race.save()
            pretty_race_title = f"race \"{race.title}\"" if race.title else "untitled race"
            flash(f"OK, updated {pretty_race_title}", "success")
            return redirect(url_for("race.list_races"))
        else:
            pretty_race_title = f"race \"{race.title}\"" if race.title else "untitled race"
            flash(f"Did not update {pretty_race_title}", "danger")
            flash_errors(form)
    return render_template(
        "admin/race_edit.html",
        form=form,
    )

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
  