# -*- coding: utf-8 -*-
"""Admin views/controllers."""
from datetime import datetime, timezone
import os
import re
import json
import roman

from sqlalchemy.inspection import inspect

from flask import (
    abort,
    Blueprint,
    current_app,
    flash,
    make_response,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import login_required
from sqlalchemy import insert, delete

from buggy_race_server.admin.forms import (
    GeneralSubmitForm,
    SubmitWithConfirmForm,
)

from buggy_race_server.config import ConfigSettingNames
from buggy_race_server.database import db
from buggy_race_server.race.models import Race, Racetrack, RaceResult
from buggy_race_server.race.forms import (
    RaceDeleteForm,
    RaceForm,
    RaceResultsForm,
    RacetrackForm,
)
from buggy_race_server.user.models import User
from buggy_race_server.utils import (
    admin_only,
    flash_errors,
    get_download_filename,
    get_flag_color_css_defs,
    get_temp_race_file_info,
    get_url_protocol,
    join_to_project_root,
    staff_only,
)

blueprint = Blueprint(
    "admin_race",
    __name__,
    url_prefix="/admin/races",
    static_folder="../static"
)

def _download_race_json(race_id, want_buggies=False):
    """ produces the race file suitable for both downloading prior
    to running a race, and uploading with the results:
    This is useful because the URLs (especially of the result file)
    might have been added/become known _after_ the race was run and
    the (oringinal) results file was created.
    """
    race = Race.get_by_id(race_id)
    if race is None:
        flash("Error: coudldn't find race", "danger")
        abort(404)
    race_filename_base = f"race-{race.slug}"
    if current_app.config[ConfigSettingNames.IS_RACE_FILE_START_STAMPED.name]:
        if race.start_at:
            race_filename_base += race.start_at.strftime('-%Y-%m-%d-%H-%M-start')
        else:
            race_filename_base += "-start-unknown"
    filename = get_download_filename(
        f"{race_filename_base}.json",
        want_datestamp=current_app.config[ConfigSettingNames.IS_RACE_FILE_DATE_STAMPED.name]
    )
    json_data = race.get_race_data_json(want_buggies=want_buggies)
    output = make_response(json_data, 200)
    output.headers["Content-Disposition"] = f"attachment; filename={filename}"
    output.headers["Content-type"] = "application/json"
    output.headers["Content-length"] = len(json_data)
    return output

@blueprint.route("/", strict_slashes=False)
@login_required
@staff_only
def list_races():
    """Admin list of all races."""
    races = sorted(Race.query.all(), key=lambda race: (race.start_at))
    form = RaceForm(request.form)
    return render_template(
        "admin/races.html",
        date_today=datetime.today().date(),
        form=form,
        races=races,
        replay_anchor=Race.get_replay_anchor(),
    )

@blueprint.route("/new", methods=["GET", "POST"], strict_slashes=False)
@login_required
@staff_only
def new_race():
    return edit_race(None)

@blueprint.route("/temporary-race-file.json", methods=["GET"])
@login_required
@staff_only
def serve_temporary_race_file_json():
    temp_race_file_info = get_temp_race_file_info()
    temp_filename = temp_race_file_info.get("filename_with_path")
    if not (temp_filename or temp_race_file_info.get("is_available")):
        abort(404)
    with open(temp_filename, "r") as temp_race_file:
        json_data = temp_race_file.read()
    output = make_response(json_data, 200)
    # no Content-Disposition of attachment, because this is served for previews
    output.headers["Content-type"] = "application/json"
    output.headers["Content-length"] = len(json_data)
    return output

@blueprint.route("/<int:race_id>", methods=["GET"])
@login_required
@staff_only
def view_race(race_id):
    race = Race.query.filter_by(id=race_id).first_or_404() 
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
    race_file_is_local=bool(
        race.race_file_url and
        race.race_file_url.startswith(
            current_app.config[ConfigSettingNames.BUGGY_RACE_SERVER_URL.name]
        )
    )
    server_protocol = get_url_protocol(
                current_app.config[ConfigSettingNames.BUGGY_RACE_SERVER_URL.name]
    )
    return render_template(
        "admin/race.html",
        flag_color_css_defs=flag_color_css_defs,
        has_results=bool(len(all_results)),
        race_file_is_local=race_file_is_local,
        is_showing_usernames=current_app.config[ConfigSettingNames.IS_USERNAME_PUBLIC_IN_RESULTS.name],
        is_tied=is_tied,
        race=race,
        results_disqualified=results_disqualified,
        results_finishers=results_finishers,
        results_nonfinishers=results_nonfinishers,
        results=all_results,
        server_protocol=server_protocol,
        track_image_url=race.track_image_url, # separated for image file
        track_svg_url=race.track_svg_url, # separated for SVG include file
        urls_with_different_protocol_dict=race.urls_with_different_protocol_dict(server_protocol),
    )

@blueprint.route("/<int:race_id>/edit", methods=["GET", "POST"])
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
    # check existing races to suggest next autofill name
    race_title_pattern = re.compile(r"^Race ([ivx]+)", re.IGNORECASE)
    max_race_number = 0
    for existing_race in Race.query.filter(Race.title != None).all():
        if match := re.match(race_title_pattern, existing_race.title):
            try:
                race_number = roman.fromRoman(match.group(1))
                if race_number > max_race_number:
                    max_race_number = race_number
            except roman.InvalidRomanNumeralError:
                pass # can ignore badly formed numerals
    suggested_next_name = f"Race {roman.toRoman(max_race_number+1)}"

    form = RaceForm(request.form, obj=race)
    if request.method == "POST":
        if form.is_submitted() and form.validate():
            if race is None:
                # untitled races are allowed (so can be edited), but they're
                # unhelpful... so override it on creation, to discourage untitled
                new_title = form.title.data.strip()
                if new_title == "":
                    new_title = suggested_next_name
                    flash(f"No title provided, using \"{new_title}\" (you can edit this)", "warning")
                race = Race.create(
                  title=new_title,
                  desc=form.desc.data.strip(),
                  cost_limit=form.cost_limit.data,
                  start_at=form.start_at.data,
                  is_visible=form.is_visible.data,
                  is_result_visible=form.is_result_visible.data,
                  is_abandoned=form.is_abandoned.data,
                  track_image_url=form.track_image_url.data,
                  track_svg_url=form.track_svg_url.data,
                  lap_length=form.lap_length.data,
                  max_laps=form.max_laps.data,
                  is_dnf_position=form.is_dnf_position.data,
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
                race.is_abandoned = form.is_abandoned.data
                race.results_uploaded_at = form.results_uploaded_at.data
                race.race_file_url = form.race_file_url.data.strip() or None
                race.track_image_url = form.track_image_url.data
                race.track_svg_url = form.track_svg_url.data
                race.lap_length = form.lap_length.data
                race.max_laps = form.max_laps.data
                race.is_dnf_position = form.is_dnf_position.data
                race.save()
                pretty_title =  f"\"{race.title}\"" if race.title else "untitled race"
                success_msg = f"OK, updated {pretty_title}" 
            flash(success_msg, "success")
            return redirect(url_for("admin_race.list_races"))
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
        racetracks=Racetrack.query.order_by(Racetrack.title.asc(),).all(),
        default_race_cost_limit=current_app.config[ConfigSettingNames.DEFAULT_RACE_COST_LIMIT.name],
        default_is_dnf_position=current_app.config[ConfigSettingNames.IS_DNF_POSITION_DEFAULT.name],
        default_is_race_visible=current_app.config[ConfigSettingNames.IS_RACE_VISIBLE_BY_DEFAULT.name],
        delete_form=delete_form,
        is_storing_racefiles_in_db=current_app.config[ConfigSettingNames.IS_STORING_RACE_FILES_IN_DB.name],
        suggested_next_name=suggested_next_name,
    )

@blueprint.route("/<int:race_id>/abandon", methods=["GET", "POST"])
@login_required
@admin_only
def abandon_race(race_id):
    race = Race.get_by_id(race_id)
    if race is None:
        flash("Error: coudldn't find race", "danger")
        abort(404)
    form = SubmitWithConfirmForm(request.form)
    if request.method == "POST":
        if race.is_abandoned:
            flash("Note: race was already abandoned", "info")
        if form.is_submitted() and form.validate():
            if not form.is_confirmed.data:
                flash("Did not abandon race (you didn't confirm it)", "danger")
            else:
                race.is_abandoned = True
                race.race_file_url =  None
                race.results_uploaded_at = None
                race.buggies_entered = 0
                race.buggies_started = 0
                race.buggies_finished = 0
                race.save()
                db.session.execute(delete(RaceResult).where(RaceResult.race_id==race.id))
                db.session.commit()
                flash("OK, race abandoned", "info")
                return redirect(url_for('admin_race.view_race', race_id=race.id))
        else:
            flash_errors(form)
            flash("Did not abandon race", "danger")
    qty_results = RaceResult.query.filter_by(race_id=race.id).count()
    return render_template(
        "admin/race_abandon.html",
        form=form,
        race=race,
        qty_results=qty_results
    )

@blueprint.route("/<int:race_id>/upload-results", methods=["GET", "POST"])
@login_required
@admin_only
def upload_race_file(race_id):
    race = Race.get_by_id(race_id)
    if race is None:
        flash("Error: coudldn't find race", "danger")
        abort(404)
    form = RaceResultsForm(request.form)
    want_redirect_to_race = False
    if request.method == "POST":
        if form.is_submitted() and form.validate():
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
                        flash(
                            "Encoding error (maybe that wasn't a JSON file you uploaded, "
                            "or it contains unexpected characters?)",
                            "warning"
                        )
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
                                if current_app.config[ConfigSettingNames.IS_STORING_RACE_FILES_IN_DB.name]:
                                    race.store_race_file(result_data)
                                    url = current_app.config[ConfigSettingNames.BUGGY_RACE_SERVER_URL.name] \
                                        + url_for("race.serve_race_file", race_id=race.id)
                                    race.race_file_url = url
                                    flash(f"Stored race file on this server for use in replay (at {url})", "success")
                                race.results_uploaded_at = datetime.now(timezone.utc) 
                                race.save()
                                flash("OK, updated race results", "success")
                                if not (race.is_visible and race.is_result_visible):
                                    flash(
                                        "Note: this file isn't visible to students yet: "
                                        "edit race to change that",
                                        "info"
                                    )
                                want_redirect_to_race = True
                            else:
                                if len(warnings) == 1:
                                    msg = "Did not upload race results because there was a warning"
                                else:
                                    msg = f"Did not upload race results because there were {len(warnings)} warnings"
                                flash(msg, "danger")
                    delete_path = json_filename_with_path
                else:
                    flash("Missing JSON race file filename", "info")
            else:
                flash("Missing race file (no JSON found)", "info")
            if delete_path:
                try:
                    os.unlink(delete_path)
                except os.error as e:
                    # could sanitise this, but the diagnostic might be useful
                    flash(f"Problem deleting uploaded file: {e}", "warning")
        else:
            flash_errors(form)
            flash("Did not accept race results", "danger")
    if want_redirect_to_race:
        return redirect(url_for("admin_race.view_race", race_id=race.id))
    return render_template(
        "admin/race_upload.html",
        form=form,
        race=race,
    )

@blueprint.route("/<int:race_id>/download-race-file/with-buggies", methods=["GET"])
@login_required
@admin_only
def download_race_json_with_buggies(race_id):
    return _download_race_json(race_id, want_buggies=True)

@blueprint.route("/<int:race_id>/download-race-file", methods=["GET"])
@login_required
@admin_only
def download_race_json_without_buggies(race_id):
    return _download_race_json(race_id, want_buggies=False)
 
@blueprint.route("/<int:race_id>/delete", methods=["POST"])
@login_required
@admin_only
def delete_race(race_id):
    form = RaceDeleteForm(request.form)
    if form.is_submitted() and form.validate():
        if not form.is_confirmed.data:
            flash("Did not delete race (you didn't confirm it)", "danger")
            return redirect(url_for('admin_race.edit_race', race_id=race_id))
        race = Race.get_by_id(race_id)
        if race is None:
            flash("Error: coudldn't find race to delete", "danger")
        else:
            race.delete()
            flash("OK, deleted race", "success")
    else:
        flash("Error: incorrect button wiring, nothing deleted", "danger")
    return redirect(url_for('admin_race.list_races'))

@blueprint.route("/tracks/autofill", methods=['GET', 'POST'])
@login_required
@admin_only
def autofill_tracks():
    """ Reads the server-side track assets and adds them to the database if
    they are not already there. Specifically, it scans the track assets
    dir, matching the image and SVG files together (so consistent naming
    in those files is important) — this avoids explicit lists in config."""
    racetracks = Racetrack.query.order_by(
          Racetrack.title.asc(),
        ).all()
    tracks_by_img_url = {
        track.track_image_url: track for track in racetracks
    }
    TRACK_IMAGE_FILE_RE = re.compile(r"^racetrack-(\d+)\.(jpg|png)$")
    TRACK_PATH_FILE_RE = re.compile(r"^racetrack-(\d+)(?:-\w+)?-?(\d+)?.svg$")
    track_dir = join_to_project_root(
        current_app.config[ConfigSettingNames._RACE_ASSETS_RACETRACK_PATH.name]
    )
    img_filenames_by_number = {}
    dir_filenames = os.listdir(track_dir)
    for filename in dir_filenames:
        if m := re.match(TRACK_IMAGE_FILE_RE, filename):
            url = Racetrack.get_local_url_for_asset(filename)
            if url not in tracks_by_img_url:
                img_filenames_by_number[f"{ m.group(1) }"] = {
                    "track_image_url": Racetrack.get_local_url_for_asset(filename)
                }
    if img_filenames_by_number:
        for filename in dir_filenames:
            if m := re.match(TRACK_PATH_FILE_RE, filename):
                if proto_track := img_filenames_by_number.get(m.group(1)):
                    proto_track['track_svg_url'] = Racetrack.get_local_url_for_asset(filename)
                    if lap_length := m.group(2):
                        proto_track['lap_length'] = lap_length
    if request.method == "POST":
        new_tracks = [ ]
        if img_filenames_by_number:
            for number in img_filenames_by_number:
                proto_track = img_filenames_by_number[number]
                if proto_track.get('track_svg_url'):
                    new_tracks.append(
                        {
                            "title": f"Racetrack {number}",
                            "desc": "",
                            "track_image_url": proto_track["track_image_url"],
                            "track_svg_url": proto_track["track_svg_url"],
                            "lap_length": proto_track.get("lap_length") # may be none
                        }
                    )
                    flash(f"Added racetrack {number} to database", "success")
        if new_tracks:
            db.session.execute(insert(Racetrack.__table__), new_tracks)
            db.session.commit()
            racetracks = Racetrack.query.order_by(Racetrack.title.asc(),).all()
        else:
            flash("No new racetracks found to add", "warning")
    return render_template(
        "admin/racetracks.html",
        racetracks=racetracks,
        form=GeneralSubmitForm(),
    )

@blueprint.route("/tracks")
@login_required
@admin_only
def show_tracks():
    racetracks = Racetrack.query.order_by(
          Racetrack.title.asc(),
        ).all()
    return render_template(
        "admin/racetracks.html",
        racetracks=racetracks,
        form=GeneralSubmitForm(), # for autofill
        is_showing_example_racetracks=current_app.config[ConfigSettingNames.IS_SHOWING_EXAMPLE_RACETRACKS.name],
    )

@blueprint.route("tracks/<track_id>")
@login_required
@admin_only
def view_track(track_id):
    track = Racetrack.get_by_id(track_id) if track_id else None
    if track is None:
        flash("No such racetrack", "danger")
        abort(404)
    return render_template(
        "admin/racetrack_view.html",
        track=track,
        track_image_url=track.track_image_url, # separated for SVG include file
        track_svg_url=track.track_svg_url, # separated for SVG include file
    )

@blueprint.route("tracks/<track_id>/delete", methods=["POST"])
@login_required
@admin_only
def delete_track(track_id):
    track = Racetrack.get_by_id(track_id)
    if track is None:
        flash("Error: coudldn't find racetrack to delete", "danger")
    else:
        form = SubmitWithConfirmForm(request.form)
        if form.is_submitted() and form.validate():
            if not form.is_confirmed.data:
                flash("Did not delete track (you didn't confirm it)", "danger")
                return redirect(url_for('admin_race.edit_track', track_id=track_id))
            track.delete()
            flash("OK, deleted racetrack", "success")
        else:
            flash("Error: incorrect button wiring, nothing deleted", "danger")
            return redirect(url_for('admin_race.list_races'))

    return redirect(url_for('admin_race.show_tracks'))

@blueprint.route("tracks/new", methods=["GET", "POST"])
@login_required
@admin_only
def new_track():
    return edit_track(None)

@blueprint.route("tracks/<track_id>/edit", methods=["GET", "POST"])
@login_required
@admin_only
def edit_track(track_id):
    if track_id is None:
        track = None
        delete_form = None
    else:
        track = Racetrack.get_by_id(track_id) if track_id else None
        if track is None:
            flash("No such racetrack", "danger")
            abort(404)
        delete_form = SubmitWithConfirmForm()
    form = RacetrackForm(request.form, obj=track)
    if request.method == "POST":
        if form.is_submitted() and form.validate():
            if track is None:
                track = Racetrack.create(
                  title=form.title.data.strip(),
                  desc=form.desc.data.strip(),
                  track_image_url=form.track_image_url.data.strip(),
                  track_svg_url=form.track_svg_url.data.strip(),
                  lap_length=form.lap_length.data
                )
                success_msg = f"OK, created new racetrack"
            else:
                track.title = form.title.data.strip()
                track.desc = form.desc.data.strip()
                track.track_image_url=form.track_image_url.data.strip()
                track.track_svg_url=form.track_svg_url.data.strip()
                track.lap_length=form.lap_length.data
                track.save()
                pretty_title =  f"\"{track.title}\"" if track.title else "untitled track"
                success_msg = f"OK, updated {pretty_title}" 
            flash(success_msg, "success")
            return redirect(url_for("admin_race.show_tracks"))
        else:
            if track:
                pretty_title =  f"\"{track.title}\"" if track.title else "untitled track"
                flash(f"Did not update {pretty_title}", "danger")
            else:
                flash(f"Did not create new racetrack", "danger")
            flash_errors(form)
    return render_template(
        "admin/racetrack_edit.html",
        delete_form=delete_form,
        form=form,
        track=track,
    )

@blueprint.route("/replay-preview", methods=["GET", "POST"])
@login_required
@staff_only
def race_preview_tool():
    """ allows previews of race files irrespective of whether they are for
    races that are on the server (yet)"""
    temp_file_info = get_temp_race_file_info()
    is_temp_file_available = temp_file_info.get("is_available")
    tmp_file_name = temp_file_info.get("filename_with_path")
    created_at = temp_file_info.get("created_at")
    form = RaceResultsForm(request.form)
    want_delete = False # if true, delete the temp file
    if request.method == "POST":
        if form.is_submitted() and form.validate():
            if "results_json_file" in request.files:
                json_file = request.files['results_json_file']
                if json_file.filename:
                    json_file.filename = tmp_file_name
                    json_file.save(tmp_file_name)
                    try:
                        with open(tmp_file_name, "r") as read_file:
                            result_data = json.load(read_file)
                        # if there are different URLs there may be CORS errors
                        # in the player, so check for any URLs that don't
                        # match this server url and report with a danger flash?
                        result_data = ""
                    except UnicodeDecodeError as e:
                        flash(
                            "Encoding error (maybe that wasn't a JSON file you uploaded, "
                            "or it contained unexpected characters?)",
                            "warning"
                        )
                        want_delete = True
                    except json.decoder.JSONDecodeError as e:
                        flash("Failed to parse JSON data", "danger")
                        flash(str(e), "warning")
                        flash("No temporary race file available", "info")
                        want_delete = True
                else:
                    want_delete = True # because no results_json_file uploaded
                if not want_delete: # OK to preview!
                    return redirect(
                        url_for('admin.staff_race_replayer') + "?race=" +
                        url_for('admin_race.serve_temporary_race_file_json')
                    )
            else:
                want_delete = True # because no results_json_file uploaded
            if want_delete and is_temp_file_available:
                try:
                    os.unlink(tmp_file_name)
                    is_temp_file_available = False
                    flash("Deleted temporary race file from the race server", "info")
                except os.error as e:
                    print("[!] Faied to delete temporary race file: {e}")
                    flash("Failed to delete temporary race file from the race server", "warning")
        else:
            flash_errors(form)
            flash("Did not change temporary race file", "danger")
        if not is_temp_file_available:
            flash("There is currently no temporary race file up here on the race server", "info")
    return render_template(
        "admin/race_replay_preview.html",
        form=form,
        is_temp_file_available=is_temp_file_available,
        created_at=created_at,
    )
    
