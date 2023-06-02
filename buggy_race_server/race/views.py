# -*- coding: utf-8 -*-
"""Race views."""

import json
from datetime import datetime, timezone
import os
import re
from flask import (
    Blueprint, flash, redirect, render_template, request,
    url_for, abort, current_app, send_file
)
from flask_login import current_user, login_required
from buggy_race_server.database import db
from buggy_race_server.race.forms import RaceForm, RaceDeleteForm, RaceResultsForm
from buggy_race_server.race.models import Race, RaceResult
from buggy_race_server.user.models import User
from buggy_race_server.utils import (
    admin_only,
    flash_errors,
    get_flag_color_css_defs,
    servertime_str,
    staff_only,
    join_to_project_root,
)
from buggy_race_server.config import ConfigSettingNames, ConfigSettings

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
                if race.start_at.date() < datetime.now(timezone.utc).date():
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

@blueprint.route("/<race_id>/upload-results", methods=["GET", "POST"])
@login_required
@admin_only
def upload_results(race_id):
    race = Race.get_by_id(race_id)
    if race is None:
        flash("Error: coudldn't find race", "danger")
        abort(404)
    form = RaceResultsForm(request.form)
    if request.method == "POST":
        if form.validate_on_submit():
            is_ignoring_warnings = form.is_ignoring_warnings.data
            is_overwriting_urls = form.is_overwriting_urls.data
            # not robust, but pragmatically...
            # we can anticipate only one admin uploading one race at a time
            delete_path = None
            if "results_json_file" in request.files:
                json_file = request.files['results_json_file']
                if json_file.filename:
                    json_filename_with_path = os.path.join(
                        current_app.config['UPLOAD_FOLDER'],
                        f"results-{str(race_id).zfill(4)}.json"
                    )
                    json_file.save(json_filename_with_path)
                    try:
                        with open(json_filename_with_path, "r") as read_file:
                            result_data = json.load(read_file)
                    except UnicodeDecodeError as e:
                        flash("Encoding error (maybe that wasn't a good JSON file you uploaded?)", "warning")
                    except json.decoder.JSONDecodeError as e:
                        flash("Failed to parse JSON data", "danger")
                        flash(str(e), "warning")
                        flash("No data was accepted", "info")
                    if result_data:
                        try:
                            warnings = race.load_race_results(
                                result_data,
                                is_ignoring_warnings=is_ignoring_warnings,
                                is_overwriting_urls=is_overwriting_urls
                            )
                        except ValueError as e:
                            flash(f"Failed to load race results: {e}", "danger")
                        else:
                            for warning in warnings:
                                flash(warning, "warning")
                            if not warnings or is_ignoring_warnings:
                                flash("OK, updated race results", "success")
                            else:
                                if len(warnings) == 1:
                                    msg = "Did not upload race results because there was a warning"
                                else:
                                    msg = "Did not upload race results because there were warnings"
                                flash(msg, "danger")
                    delete_path = json_filename_with_path
                else:
                    flash("NO json_file.filename", "info")
            else:
                flash("NO results_json_file was false", "info")
            if delete_path:
                try:
                    os.unlink(delete_path)
                except os.error as e:
                    # could sanitise this, but the diagnostic might be useful
                    flash(f"Problem deleting uploaded file: {e}", "warning")
        else:
            flash_errors(form)
            flash("Did not accept race results", "danger")
    return render_template(
        "admin/race_upload.html",
        form=form,
        race=race,
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
            flash("Error: coudldn't find race to delete", "danger")
        else:
            race.delete()
            flash("OK, deleted race", "success")
    else:
      flash("Error: incorrect button wiring, nothing deleted", "danger")
    return redirect(url_for('race.list_races'))

@blueprint.route("/<race_id>/result")
def show_race_results(race_id):
    race = Race.query.filter_by(id=race_id).first_or_404()
 
    all_results = db.session.query(
        RaceResult, User).outerjoin(User).filter(
            RaceResult.race_id==race.id
        ).order_by(RaceResult.race_position.asc()).all()
 
    # all_results = RaceResult.query.filter_by(race_id=race_id).order_by(RaceResult.race_position.asc())
    results_finishers = [(res, user)  for (res, user) in all_results if res.race_position > 0 ]
    results_nonfinishers = [(res, user) for (res, user) in all_results if res.race_position == 0 ]
    results_disqualified = [(res, user) for (res, user) in all_results if res.race_position < 0 ]
    is_tied = {}
    prev_pos = 0
    for (res, _) in results_finishers:
        if res.race_position == prev_pos:
            is_tied[prev_pos] = "="
        prev_pos = res.race_position
    flag_color_css_defs = get_flag_color_css_defs([res for (res, _) in all_results])
    return render_template(
        "races/result.html",
        current_user_id=0 if current_user.is_anonymous else current_user.id,
        flag_color_css_defs=flag_color_css_defs,
        is_showing_usernames=current_app.config[ConfigSettingNames.IS_USERNAME_PUBLIC_IN_RESULTS.name],
        is_tied=is_tied,
        race=race,
        results_disqualified=results_disqualified,
        results_finishers=results_finishers,
        results_nonfinishers=results_nonfinishers,
    )

# temporary /assets/ filename while developing/experimenting in beta
@blueprint.route("/assets/<filename>")
def serve_race_player_asset(filename):
    """ Serving statically because it's more robust than trying to
        figure out how to exclude this from webpack, and even then it's
        too complex in the event of changes: keep it simple.
        Want it standalone because it's handy to be able to dev/run it
        in isolation outwith the race server, at least for now."""
    full_filename = join_to_project_root(
        "buggy_race_server", "templates", "races", "assets", filename
    )
    if not os.path.exists(full_filename):
        abort(404)
    return send_file(full_filename)
  
@blueprint.route("/<race_id>/replay")
def replay_race(race_id):
    race = Race.query.filter_by(id=race_id).first_or_404()
    result_log_url = race.result_log_url
    if result_log_url and not (re.match(r"^https?://", result_log_url)):
        result_log_url = url_for(
            "race.serve_race_player_asset",
            filename=result_log_url
        )
    if not (race.is_visible and race.is_result_visible):
        if current_user.is_anonymous or not current_user.is_staff:
            flash("The results of this race are not available yet", "warning")
            abort(403)
    return render_template(
        "races/player.html",
        cachebuster=current_app.config[ConfigSettings.CACHEBUSTER_KEY],
        result_log_url=result_log_url,
    )
