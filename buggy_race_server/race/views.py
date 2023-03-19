# -*- coding: utf-8 -*-
"""Buggy views."""

import csv
import re
from datetime import datetime

from flask import Blueprint, flash, redirect, render_template, request, url_for, abort, current_app
from flask_login import current_user, login_required
from buggy_race_server.race.forms import RaceForm, RaceDeleteForm
from buggy_race_server.race.models import Race
from buggy_race_server.utils import flash_errors, staff_only, admin_only
from buggy_race_server.config import ConfigSettingNames

blueprint = Blueprint("race", __name__, url_prefix="/races", static_folder="../static")

@blueprint.route("/", strict_slashes=False)
@login_required
@staff_only
def list_races():
    """Admin list of all races."""
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
    return edit_race(None)

@blueprint.route("/<race_id>/edit", methods=["GET", "POST"])
@login_required
@admin_only
def edit_race(race_id=None):
    """Edit an existing race (differs from new race because may
       have some results?)."""
    if race_id is None:
        race = None
        delete_form = None
    else:
        race = Race.get_by_id(race_id) if race_id else None
        if race is None:
            flash("No such race", "danger")
            abort(404)
        delete_form = RaceDeleteForm(race_id=race_id)
    form = RaceForm(request.form, obj=race)
    if request.method == "POST":
        if form.validate_on_submit():
            if race is None:
                race = Race.create(
                  title=form.title.data.strip(),
                  desc=form.desc.data.strip(),
                  cost_limit=form.cost_limit.data,
                  start_at=form.start_at.data,
                  is_visible=form.is_visible.data,
                )
                if race.start_at.date() < datetime.now().date():
                    success_msg = f"OK, created new race... even though it is in the past ({race.start_at.date()})"
                else:
                    success_msg = f"OK, created new race"
            else:
                race.title = form.title.data.strip()
                race.desc = form.desc.data.strip()
                race.start_at = form.start_at.data
                race.cost_limit = form.cost_limit.data
                race.is_visible = form.is_visible.data
                race.is_result_visible = form.is_result_visible.data
                race.results_uploaded_at = form.results_uploaded_at.data
                race.result_log_url = form.result_log_url.data
                race.buggies_csv_url = form.buggies_csv_url.data
                race.race_log_url = form.race_log_url.data
                race.save()
                pretty_title =  f"\"{race.title}\"" if race.title else "untitled race"
                success_msg = f"OK, updated {pretty_title}" 
            flash(success_msg, "success")
            return redirect(url_for("race.list_races"))
        else:
            if race:
                pretty_race_title = f"race \"{race.title}\"" if race.title else "untitled race"
                flash(f"Did not update {pretty_race_title}", "danger")
            else:
                flash(f"Did not create new race", "danger")
            flash_errors(form)
    return render_template(
        "admin/race_edit.html",
        form=form,
        race=race,
        default_race_cost_limit=current_app.config[ConfigSettingNames.DEFAULT_RACE_COST_LIMIT.name],
        default_is_race_visible=current_app.config[ConfigSettingNames.IS_RACE_VISIBLE_BY_DEFAULT.name],
        delete_form=delete_form,
    )

@blueprint.route("/<race_id>/delete", methods=["POST"])
@login_required
@admin_only
def delete_race(race_id):
    form = RaceDeleteForm(request.form)
    if form.validate_on_submit():
        if not form.is_confirmed.data:
            flash("Did not delete race (you didn't confirm it)", "danger")
            return redirect(url_for('race.edit_race', race_id=race_id))
        race = Race.get_by_id(race_id)
        if race is None:
            flash("Error: coudldn't find announcement to delete", "danger")
        else:
            race.delete()
            flash("OK, deleted race", "success")
    else:
      flash("Error: incorrect button wiring, nothing deleted", "danger")
    return redirect(url_for('race.list_races'))

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
  