# -*- coding: utf-8 -*-
"""Race model."""
from datetime import datetime, timedelta, timezone
import os
import re
import json
from sqlalchemy import delete, insert

# get the config settings (without the app context):
from buggy_race_server.config import ConfigSettings, ConfigSettingNames
from flask import current_app, url_for
from buggy_race_server.database import (
    Column,
    Model,
    SurrogatePK,
    db,
)
from buggy_race_server.buggy.models import Buggy
from buggy_race_server.lib.race_specs import RuleNames
from buggy_race_server.user.models import User
from buggy_race_server.utils import servertime_str

class Racetrack(SurrogatePK, Model):

    def is_local(self):
        server_url = current_app.config[ConfigSettingNames.BUGGY_RACE_SERVER_URL.name]
        return (
            self.track_image_url is not None
            and
            self.track_svg_url is not None
            and
            self.track_image_url.startswith(server_url)
            and
            self.track_svg_url.startswith(server_url)
        )

    @staticmethod
    def get_local_url_for_asset(filename):
        server_url = current_app.config[ConfigSettingNames.BUGGY_RACE_SERVER_URL.name]
        path_url = url_for("race.serve_racetrack_asset", filename=filename)
        return f"{server_url}/{path_url}"


    """ Racetrack used to populate race-construction pages
    There's no foreign key relationship with Race beacuse Racetracks
    are really just furnishing URLs to the interface, and it's the
    URLs which are going into the race records. They key relationship
    here is that the SVG and image (JPG) URLs are linked by being the
    same track.
    Note URL combinations could be unique, but individual URLs don't
    need to be. But not enforced here for now.
    """
    __tablename__ = "racetracks"
    id = Column(db.Integer, primary_key=True)
    title = Column(db.String(80), unique=False, nullable=False, default="")
    desc = Column(db.Text(), unique=False, nullable=False, default="")
    track_image_url = Column(db.String(255), unique=False, nullable=True)
    track_svg_url = Column(db.String(255), unique=False, nullable=True)
    lap_length = Column(db.Integer, nullable=True)

    def __init__(self, **kwargs):
        """Create instance."""
        db.Model.__init__(self, **kwargs)


class Race(SurrogatePK, Model):
    """A race."""

    def get_default_race_time():
        # two minutes to midnight ;-)
        tomorrow = datetime.today() + timedelta(days=1)
        tomorrow = tomorrow.replace(hour=23, minute=58, second=0, microsecond=0)
        return tomorrow

    __tablename__ = "races"
    id = db.Column(db.Integer, primary_key=True)
    title = Column(db.String(80), unique=False, nullable=False, default="")
    desc = Column(db.Text(), unique=False, nullable=False, default="")
    created_at = Column(db.DateTime, nullable=False, default=datetime.now(timezone.utc))
    start_at = Column(db.DateTime, nullable=False, default=get_default_race_time())
    cost_limit = db.Column(db.Integer(), default=ConfigSettings.DEFAULTS[ConfigSettingNames.DEFAULT_RACE_COST_LIMIT.name])
    is_visible = db.Column(db.Boolean(), default=bool(ConfigSettings.DEFAULTS[ConfigSettingNames.IS_RACE_VISIBLE_BY_DEFAULT.name]))
    result_log_url = Column(db.String(255), unique=True, nullable=True)
    league = Column(db.String(32), unique=False, nullable=True, default="")
    results_uploaded_at = Column(db.DateTime, nullable=True)
    buggies_entered = db.Column(db.Integer, nullable=False, default=0)
    buggies_started = db.Column(db.Integer, nullable=False, default=0)
    buggies_finished = db.Column(db.Integer, nullable=False, default=0)
    race_log_url = Column(db.String(255), unique=True, nullable=True)
    is_result_visible = db.Column(db.Boolean(), nullable=False, default=False)
    track_image_url = Column(db.String(255), unique=False, nullable=True)
    track_svg_url = Column(db.String(255), unique=False, nullable=True)
    max_laps = db.Column(db.Integer(),  nullable=True)
    lap_length = Column(db.Integer, nullable=True)

    results = db.relationship('RaceResult', backref='race', cascade="all, delete")
    racefile = db.relationship('RaceFile', backref='race', cascade="all, delete")

    def __init__(self, **kwargs):
        """Create instance."""
        db.Model.__init__(self, **kwargs)
        if self.league is None or self.league == "":
            self.league = current_app.config[ConfigSettingNames.DEFAULT_RACE_LEAGUE.name]

    def log_path(self):
        return os.path.join(self.league, self.start_at.strftime('%Y-%m-%d-%H-%M'))

    @property
    def slug(self):
        if self.title:
            s = re.sub(r"[^a-z0-9]+", "-", self.title.strip().lower())
            s = re.sub(r"(^-+|-+$)", "", s)
            s = re.sub(r"--+", "-", s)
        else:
            s = "untitled"
        return f"{self.id}-{s}"

    @property
    def has_urls(self):
        return bool (self.result_log_url or self.race_log_url)

    @property
    def start_at_servertime(self):
        """ Allows Jinja to display day/month/time as separate elements"""
        return servertime_str(
            current_app.config[ConfigSettingNames.BUGGY_RACE_SERVER_TIMEZONE.name],
            self.start_at,
            want_datetime=True # otherwise we get a string
        )

    @staticmethod
    def get_replay_anchor():
        """ returns empty string or the replay anchor prefixed with #
            This method is protecting against easy mistake of config setting
            already having a # at the start — and we've got no easy way of
            policing individual config setting validation like this (yet)
        """
        anchor = ""
        if anchor := current_app.config[ConfigSettingNames.BUGGY_RACE_PLAYER_ANCHOR.name]:
            if not anchor.startswith("#"):
                anchor = f"#{anchor}"
        return anchor

    @staticmethod
    def get_duplicate_urls(race_id, result_log_url, race_log_url):
        """ Returns list of fields with duplicate (non-unique) URLs for a race"""
        dup_fields = {}
        race_id = race_id or 0
        if result_log_url or race_log_url:
            if races := Race.query.filter(
                  Race.id!=race_id).filter(
                  (Race.result_log_url==result_log_url) |
                  (Race.race_log_url==race_log_url)
                ).all():
                dup_fields = {}
                for race in races:
                    if result_log_url and race.result_log_url == result_log_url:
                        dup_fields["result_log_url"] = True
                    if race_log_url and race.race_log_url == race_log_url:
                        dup_fields["race_log_url"] = True
        return dup_fields.keys()


    def load_race_results(self, results_data, is_ignoring_warnings=False, is_overwriting_urls=True):
        """ results data has been read from JSON"""
        if race_id := results_data.get("race_id"):
            if str(self.id) != race_id:
                # if JSON data contains a race ID, it must match
                raise ValueError(f"Results data you uploaded has wrong race ID ({results_data.get('race_id')}) for this race ({self.id})")
        result_log_url = results_data.get("result_log_url")
        race_log_url = results_data.get("race_log_url")
        dup_fields = Race.get_duplicate_urls(self.id, result_log_url, race_log_url)
        if dup_fields:
            raise ValueError(
                f"Already got a race with the same URL for {' and '.join(dup_fields)}"
            )
        warnings = []
        uploaded_title = results_data.get("race_title")
        if (self.title or uploaded_title) and self.title != uploaded_title:
            warnings.append(
                f"JSON data you uploaded has wrong race title for this race?"
                f" Expected \"{self.title}\", uploaded \"{uploaded_title}\""
            )
        total_buggies_entered = int(results_data.get("buggies_entered") or 0)
        total_buggies_started = int(results_data.get("buggies_started") or 0)
        total_buggies_finished = int(results_data.get("buggies_finished") or 0)
        valid_violation_names = [ rn.value for rn in RuleNames]
        if buggy_results := results_data.get("buggies"):
            if buggy_results[0] and buggy_results[0].get('race_position') is None:
                buggy_results = []
                warnings.append("Buggies found in race file, but no results (race positions are missing: was this file output from a race?)")
        elif buggy_results := results_data.get("results"): # old format of file used "results"
            warnings.append("Results found but in an out-of-date format (can still use them... for now)")
        if not buggy_results:
            warnings.append(f"No results found inside uploaded JSON data")
            buggy_results = []
        qty_buggies_entered = 0
        qty_buggies_started = 0
        qty_buggies_finished = 0
        user_values = User.query.with_entities(User.id, User.username).all()
        username_by_id = { uv[0]: uv[1] for uv in user_values }
        user_id_by_username = { uv[1]: uv[0] for uv in user_values }
        results = [] # will be used to mass-insert the race results
        usernames_in_race = {} # used to check for duplicate entries
        for i, bugres in enumerate(buggy_results):
            race_position = bugres.get("race_position")
            if race_position is None:
                raise ValueError(f"missing race_position in result ({i})")
            else:
                race_position = int(race_position)
            cost = bugres.get("cost")
            if cost is None:
                raise ValueError(f"missing cost in result ({i})")
            user_id = bugres.get("user_id")
            username = bugres.get("username")
            if user_id is None and username is None:
                raise ValueError(f"missing user in result ({i})")
            if user_id or username:
                if not user_id:
                    user_id = user_id_by_username.get(username)
                elif not username:
                    username = username_by_id.get(user_id)
                if (
                    username_by_id.get(user_id) != username
                    or
                    user_id_by_username.get(username) != user_id
                ):
                    if found_user_id := user_id_by_username.get(username):
                        if wrong_username := username_by_id.get(user_id):
                            wrong_username = f"which is \"{ wrong_username }\""
                        else:
                            wrong_username = "which is missing"
                        warnings.append(
                            f"result ({i}) username \"{username}\" does not match user_id"
                            f" {user_id} ({wrong_username}) — match on username finds id={found_user_id} instead"
                        )
                        user_id = found_user_id
                        bugres[user_id] = found_user_id # if warnings ignored, use this
                    elif found_username := username_by_id.get(user_id):
                        if wrong_id := user_id_by_username.get(username):
                            wrong_id = f"which is { wrong_id }"
                        else:
                            wrong_id = "which is missing"
                        warnings.append(
                            f"result ({i}) user id {user_id} does not match username"
                            f" \"{username}\" ({wrong_id}) — match on id finds \"{found_username}\" instead"
                        )
                        bugres[username] = found_username # if warnings ignored, carry on
                    else: # couldn't resolve either username or id
                        raise ValueError(f"no user found with either username \"{username}\" or an id of {user_id} ({i})")
                if username in usernames_in_race:
                    usernames_in_race[username] += 1
                else:
                    usernames_in_race[username] = 1
                qty_buggies_entered += 1
                if violations_str := bugres.get("violations_str"):
                    violations = []
                    for v in violations_str.split(","):
                        if v.upper() in valid_violation_names:
                            violations.append(v)
                        else:
                            warnings.append(f"result ({i}) contains unknown rule violation: \"{v}\"")
                    violations_str = ",".join(sorted(violations))
                if race_position < 0: # position -1 means buggy never started
                    if not violations_str:
                        warnings.append(f"result ({i}) is a non-starter but has no rule violation")
                else:
                    qty_buggies_started += 1
                    if race_position > 0:  # positive position means buggy finished
                        qty_buggies_finished += 1
                result = {
                    "race_id": self.id,
                    "user_id": user_id,
                    "race_position": race_position,
                    "cost": cost,
                }
                for item in ["flag_color", "flag_color_secondary", "flag_pattern", "violations_str"]:
                    result[item] = bugres.get(item) or ""
                results.append(result)
        multi_usernames = [ username for username in usernames_in_race if usernames_in_race[username] > 1]
        if multi_usernames:
            warnings.append(f"usernames with more than one buggy in this race: {', '.join(sorted(multi_usernames))}")
        if total_buggies_entered != qty_buggies_entered:
            warnings.append(f"number of buggies entered ({qty_buggies_entered}) does not match total in JSON ({total_buggies_entered})")
        if total_buggies_started != qty_buggies_started:
            warnings.append(f"number of buggies started ({qty_buggies_started}) does not match total in JSON ({total_buggies_started})")
        if total_buggies_finished != qty_buggies_finished:
            warnings.append(f"number of buggies finished ({qty_buggies_finished}) does not match total in JSON ({total_buggies_finished})")
        if not warnings or is_ignoring_warnings:
            db.session.execute(delete(RaceResult).where(RaceResult.race_id==self.id))
            if results:
                # TODO: not having results is problematic — see issue #129
                db.session.execute(insert(RaceResult).values(results))
            self.results_uploaded_at = datetime.now(timezone.utc)
            self.buggies_entered = qty_buggies_entered
            self.buggies_started = qty_buggies_started
            self.buggies_finished = qty_buggies_finished
            if results_data.get("result_log_url"):
                if self.result_log_url:
                    if is_overwriting_urls:
                        self.result_log_url = results_data.get("result_log_url")
                    else:
                        warnings.append("Did not overwrite race result log URL")
                else:
                    self.result_log_url = results_data.get("result_log_url")
            if results_data.get("race_log_url"):
                if self.race_log_url:
                    if is_overwriting_urls:
                        self.race_log_url = results_data.get("race_log_url")
                    else:
                        warnings.append("Did not overwrite race events log URL")
                else:
                    self.race_log_url = results_data.get("race_log_url")
            db.session.commit()
        return [ f"Warning: {warning}" for warning in warnings ]

    def get_race_data_json(self, want_buggies=False):
        all_results = db.session.query(
            RaceResult, User
        ).outerjoin(User).filter(
            RaceResult.race_id==self.id
        ).order_by(RaceResult.race_position.asc()).all()
        buggies = []
        if want_buggies:
            buggies = db.session.query(
                Buggy, User
            ).outerjoin(Buggy).filter(
                Buggy.user_id==User.id,
                User.is_active==True,
                User.is_student==True,
            ).order_by(User.username.asc()).all()
        race_data_dict = {
            "result_log_url": self.result_log_url,
            "title": self.title,
            "description": self.desc,
            "track_image_url": self.track_image_url,
            "track_svg_url": self.track_svg_url,
            "lap_length": self.lap_length,
            "race_log_url": self.race_log_url,
            "max_laps": 0,
            "start_at": servertime_str(
                current_app.config[ConfigSettingNames.BUGGY_RACE_SERVER_TIMEZONE.name],
                self.start_at
            ),
            "league": self.league,
            "buggies": [
                buggy.get_dict(user=user) for (buggy, user) in buggies
            ],
            "buggies_entered": self.buggies_entered,
            "buggies_started": self.buggies_started,
            "buggies_finished": self.buggies_finished,
            "results":  [
                {
                    "username": user.username,
                    "user_id": user.id,
                    "flag_color": res.flag_color,
                    "flag_color_secondary": res.flag_color_secondary,
                    "flag_pattern": res.flag_pattern,
                    "cost": res.cost,
                    "race_position": res.race_position,
                    "violations_str": res.violations_str
                } for (res, user) in all_results
            ],
            "version": "1.0"
        }
        return json.dumps(race_data_dict, indent=1, separators=(',', ': '))


    def store_race_file(self, race_file_contents):
        """ check IS_STORING_RACE_FILES_IN_DB before using race files """
        if type(race_file_contents) != str:
            race_file_contents = json.dumps(race_file_contents)
        race_file_db = RaceFile.query.filter_by(race_id=self.id).first()
        if race_file_db is None:
            race_file_db = RaceFile.create(
                race_id=self.id,
                contents=race_file_contents
            )
        else:
            race_file_db.contents = race_file_contents
        race_file_db.save()

class RaceResult(SurrogatePK, Model):

    """A buggy's race result 
    Note that this links to the user not the buggy, because buggy records are
    not constant: they can and will change between races (if you need to find
    the details of buggie at the time they were entered in a race, follow that
    race's JSON file).
    """
    __tablename__ = "results"
    id = db.Column(db.Integer, primary_key=True)
    race_id = db.Column(db.Integer, db.ForeignKey('races.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    flag_color = db.Column(db.String(32), nullable=False, default=Buggy.DEFAULTS["flag_color"])
    flag_color_secondary = db.Column(db.String(32), nullable=False, default=Buggy.DEFAULTS["flag_color_secondary"])
    flag_pattern = db.Column(db.String(32), nullable=False, default=Buggy.DEFAULTS["flag_pattern"])
    cost = db.Column(db.Integer, nullable=True)
    race_position = db.Column(db.Integer, nullable=False, default=0)
    violations_str = db.Column(db.String(255), nullable=True)

class RaceFile(SurrogatePK, Model):
    """A "race file" that holds everything needed to replay a race (some
    of which — such a full buggy specs — is not currently used once the
    race has been run (but a better replayer could, in future, exploit)).
    The race file is in reality a JSON file produced by downloading a race
    from the server, and then updated by the process of running a race.
    Storing these in the database is a convenience that avoids handling
    uploaded files: see IS_STORING_RACE_FILES_IN_DB if you don't want to
    use this mechanism (and instead host them elsewhere, e.g., on GitHub
    pages). The URL for the race file (whether it's on this server or
    external) is in race.result_log_url (formerly call the result log
    file, but refactored to be the more general "race file").
    These are _not_ stored as a column in the race model to avoid
    ORM inefficiency in case these files are large — it's very likely this
    would work fine as a column in the Race table, but breaking it out
    here maybe allows future efficiency investigation.
    """
    __tablename__ = "racefiles"
    id = db.Column(db.Integer, primary_key=True) # not used in practice?
    race_id = db.Column(db.Integer, db.ForeignKey('races.id'), nullable=False)
    contents = db.Column(db.Text(), unique=False, nullable=False, default="")
