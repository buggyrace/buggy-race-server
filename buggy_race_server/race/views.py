# -*- coding: utf-8 -*-
"""Race views."""

import json
from datetime import datetime, timezone
import os
import re
from sqlalchemy import insert, and_, or_
from flask import (
    abort,
    Blueprint,
    current_app,
    flash,
    make_response,
    redirect,
    render_template,
    request,
    send_file,
    url_for,
)
from flask_login import current_user, login_required
from buggy_race_server.admin.forms import GeneralSubmitForm, SubmitWithConfirmForm
from buggy_race_server.admin.models import DbFile
from buggy_race_server.database import db
from buggy_race_server.race.forms import RaceForm, RaceDeleteForm, RaceResultsForm, RacetrackForm
from buggy_race_server.race.models import Race, RaceResult
from buggy_race_server.user.models import User
from buggy_race_server.utils import (
    admin_only,
    flash_errors,
    get_download_filename,
    get_flag_color_css_defs,
    get_temp_race_file_info,
    staff_only,
    join_to_project_root,
    servertime_str,
)
from buggy_race_server.config import ConfigSettingNames, ConfigSettings

blueprint = Blueprint("race", __name__, url_prefix="/races", static_folder="../static")

# race assets:
# Serving statically because it's more robust than trying to
# figure out how to exclude these from webpack, and even then it's
# too complex in the event of changes: keep it simple.
# Want it standalone because it's handy to be able to dev/run it
# in isolation outwith the race server, at least for now.

def _serve_race_asset_file(*args):
    full_filename = join_to_project_root(*args)
    if not os.path.exists(full_filename):
        # don't send full error page, as responses generally aren't
        # being seen by human user, but as a component on a page
        print(f"Race resource not found <{full_filename}>")
        return make_response(f"Race resource not found <{full_filename}>", 404)
    return send_file(full_filename)

@blueprint.route("/assets/tracks/<filename>")
def serve_racetrack_asset(filename):
    return _serve_race_asset_file(
        current_app.config[ConfigSettingNames._RACE_ASSETS_RACETRACK_PATH.name],
        filename
    )

@blueprint.route("/assets/img/<filename>")
def serve_race_player_image(filename):
    return _serve_race_asset_file(
        current_app.config[ConfigSettingNames._RACE_ASSETS_IMAGES_PATH.name],
        filename
    )

@blueprint.route("/assets/<filename>")
def serve_race_player_asset(filename):
    return _serve_race_asset_file(
        current_app.config[ConfigSettingNames._RACE_ASSETS_PATH.name],
        filename
    )

@blueprint.route("/", strict_slashes=False)
def show_public_races():
    """Race announcement page."""
    next_race=Race.query.filter(
        Race.is_visible==True,
        Race.start_at > datetime.now(timezone.utc)
      ).order_by(Race.start_at.asc()).first()
    races = db.session.query(Race).outerjoin(RaceResult).filter(
            Race.is_visible==True,
            Race.start_at < datetime.now(timezone.utc),
            or_(
                Race.is_abandoned==True,
                and_(
                    RaceResult.race_position > 0,
                    RaceResult.race_position <= 3
                )
            )
        ).order_by(Race.start_at.desc()).all()
    results = [ race.results for race in races ]
    flag_color_css_defs = get_flag_color_css_defs(
        [result for sublist in results for result in sublist]
    )
    return render_template(
        "races/index.html",
        flag_color_css_defs=flag_color_css_defs,
        next_race=next_race,
        races=races,
        replay_anchor=Race.get_replay_anchor(),
    )

@blueprint.route("races.json", strict_slashes=True)
def serve_races_json():
    filename = get_download_filename("races.json", want_datestamp=True)
    races=Race.query.filter(
        Race.is_visible==True,
        Race.start_at < datetime.now(timezone.utc)
      ).order_by(Race.start_at.asc())
    races_list = [
        {
            "id": race.id,
            "title": race.title,
            "start_at": servertime_str(
                current_app.config[ConfigSettingNames.BUGGY_RACE_SERVER_TIMEZONE.name],
                race.start_at
            ),
            "race_file_url": race.race_file_url if (
                race.is_result_visible and not race.is_abandoned
            ) else None,
            "is_abandoned": race.is_abandoned if race.is_result_visible else None
        }
        for race in races
    ]
    json_data = json.dumps(races_list, indent=1, separators=(',', ': '))
    output = make_response(json_data, 200)
    output.headers["Content-Disposition"] = f"attachment; filename={filename}"
    output.headers["Content-type"] = "application/json"
    output.headers["Content-length"] = len(json_data)
    return output

@blueprint.route("/<int:race_id>/replay")
def replay_race(race_id):
    race = Race.query.filter_by(id=race_id).first_or_404()
    if not (race.is_visible and race.is_result_visible):
        if current_user.is_anonymous or not current_user.is_staff:
            flash("The results of this race are not available yet", "warning")
            abort(403)
    if race.is_abandoned:
        flash("Race was abandoned: nothing to replay", "warning")
        abort(404)
    race_file_url = race.race_file_url
    if race_file_url and not (re.match(r"^https?://", race_file_url)):
        race_file_url = url_for(
            "race.serve_race_player_asset",
            filename=race_file_url
        )
    if player_url := current_app.config[ConfigSettingNames.BUGGY_RACE_PLAYER_URL.name]:
        anchor = Race.get_replay_anchor()
        return redirect(f"{player_url}?race={race_file_url}{anchor}")
    if current_user.is_anonymous:
        current_user_username = "nobody!" # ensure no username match with "!"
    else:
        current_user_username = current_user.username
    return render_template(
        "races/player.html",
        current_user_username=current_user_username,
        cachebuster=current_app.config[ConfigSettings.CACHEBUSTER_KEY],
        race_file_url=race_file_url,
    )

@blueprint.route("/<int:race_id>/result")
def show_race_results(race_id):
    race = Race.query.filter_by(id=race_id).first_or_404()

    if is_preview := not (race.is_visible and race.is_result_visible):
        if current_user.is_anonymous or not current_user.is_staff:
            flash("Results for this race are not available yet", "danger")
            flash("Either the results haven't been uploaded, or they haven't been published yet (maybe try again later?)", "info")
            abort(404)
        else:
            flash("Results for this race have not been published yet: you're seeing this preview because you're staff", "warning")

    all_results = db.session.query(
        RaceResult, User).outerjoin(User).filter(
            RaceResult.race_id==race.id
        ).order_by(RaceResult.race_position.asc()).all() 

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
        is_preview=is_preview,
        current_user_id=0 if current_user.is_anonymous else current_user.id,
        flag_color_css_defs=flag_color_css_defs,
        is_showing_usernames=current_app.config[ConfigSettingNames.IS_USERNAME_PUBLIC_IN_RESULTS.name],
        is_tied=is_tied,
        race=race,
        replay_anchor=Race.get_replay_anchor(),
        results=all_results,
        results_disqualified=results_disqualified,
        results_finishers=results_finishers,
        results_nonfinishers=results_nonfinishers,
    )

@blueprint.route("/<int:race_id>/race-file.json")
@blueprint.route("/<int:race_id>/race-file")
def serve_race_file(race_id):
    race = Race.query.filter_by(id=race_id).first_or_404()
    if not (race.is_visible and race.is_result_visible):
        if current_user.is_anonymous or not current_user.is_staff:
            flash("Race file not available yet", "danger")
            abort(403)
    if race.is_abandoned: # don't show race file
        flash("No race file: race was abandoned", "info")
        abort(404)
    if current_app.config[ConfigSettingNames.IS_STORING_RACE_FILES_IN_DB.name]:
        racefile = DbFile.query.filter_by(
            type=DbFile.RACE_FILE_TYPE,
            item_id=race_id
        ).first_or_404()
        json_response = make_response(racefile.contents)
        json_response.headers["Content-type"] = "application/json"
        return json_response
    else:
        if not race.race_file_url:
            abort(404)
        # Note: there's no validation on the URL here, including JSON
        # MIME-type, but if IS_STORING_RACE_FILES_IN_DB has been turned
        # off, that's perhaps unavoidable:
        return redirect(race.race_file_url)
