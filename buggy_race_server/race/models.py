# -*- coding: utf-8 -*-
"""Race model."""
import datetime as datetime
import os
from sqlalchemy import delete, insert

# get the config settings (without the app context):
from buggy_race_server.config import ConfigSettings, ConfigSettingNames
from flask import current_app
from buggy_race_server.database import (
    Column,
    Model,
    SurrogatePK,
    db,
)
from buggy_race_server.buggy.models import Buggy
from buggy_race_server.user.models import User


def load_race_results(results_data, is_ignoring_warnings=False):
    """ results data has been read from JSON"""
    warnings = []
    valid_violation_names = [ rn.value for rn in Buggy.RuleNames]
    race_by_id = None
    race_by_title = None
    if race_id := results_data.get("race_id"):
        race_by_id = Race.get_by_id(race_id)
    if race_title := results_data.get("race_title"):
        race_by_title = Race.query.filter_by(title=race_title).first()
    if race_by_id and race_by_title and race_by_id != race_by_title:
        raise ValueError("Results data you uploaded is ambiguous: race_id and race_title find different races")
    race = race_by_id or race_by_title
    if race is None:
        raise ValueError("Cannot find race (neither race_id or race_title in the JSON data you uploaded match anything)")
    pretty_race_title = race.title or f"untitled race ({race_id})"
    total_buggies_entered = int(results_data.get("buggies_entered") or 100)
    total_buggies_started = int(results_data.get("buggies_started") or 111)
    total_buggies_finished = int(results_data.get("buggies_finished") or 1111)
    race.results_uploaded_at = datetime.datetime.now()
    if buggies_csv_url := results_data.get("buggies_csv_url"):
        race.buggies_csv_url = buggies_csv_url
    if race_log_url := results_data.get("race_log_url"):
        race.race_log_url = race_log_url
    if result_log_url := results_data.get("result_log_url"):
        race.result_log_url = result_log_url
    buggy_results = results_data.get("results")
    race.buggies_entered = 0
    race.buggies_started = 0
    race.buggies_finished = 0
    if not buggy_results: # might be correct... if there really were no buggies
        warnings.append(f"No results found inside uploaded JSON data")
        buggy_results = []
    user_values = User.query.with_entities(User.id, User.username).all()
    username_by_id = { uv[0]: uv[1] for uv in user_values }
    user_id_by_username = { uv[1]: uv[0] for uv in user_values }
    results = [] # will be used to mass-insert the race results
    usernames_in_race = {} # used to check for duplicate entries
    for i, bugres in enumerate(buggy_results):
        print(f"FIXME-looping {i} : {bugres}")
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
                warnings.append(
                    f"result ({i}) username (\"{username}\") does not match user_id"
                    f" ({user_id}), which is \"{username_by_id.get(user_id)}\")"
                )
            if username in usernames_in_race:
                usernames_in_race[username] += 1
            else:
                usernames_in_race[username] = 1
            race.buggies_entered += 1
            if violations_str := bugres.get("violations_str"):
                violations = []
                for v in violations_str.split(","):
                    if v.upper() in valid_violation_names:
                        violations.append(v)
                    else:
                        warnings.append(f"result ({i}) contains unknown rule violation: \"{v}\"")
                        print(f"FIXME ::::<><<>>>:::: {valid_violation_names}", flush=True)
                violations_str = ",".join(sorted(violations))
            if race_position < 0: # position -1 means buggy never started
                if not violations_str:
                    warnings.append(f"result ({i}) is a non-starter but has no rule violation")
            else:
                race.buggies_started += 1
                if race_position > 0:  # positive position means buggy finished
                    race.buggies_finished += 1
            result = {
                "race_id": race.id,
                "user_id": user_id,
                "race_position": race_position,
                "cost": cost,
            }
            for item in ["flag_color", "flag_color_secondary", "flag_pattern", "violations_str"]:
                result[item] = bugres.get(item) or ""
            results.append(result)
            print(f"FIXME::::: race.buggies_started = {race.buggies_started}, race.buggies_finished={race.buggies_finished}")
    multi_usernames = [ username for username in usernames_in_race if usernames_in_race[username] > 1]
    if multi_usernames:
        warnings.append(f"usernames with more than one buggy in this race: {', '.join(sorted(multi_usernames))}")
    print(f"FIXME results contains {len(results)} results:")
    for r in results:
        print(r)
    print("FIXME .................")
    if total_buggies_entered != race.buggies_entered:
        warnings.append(f"number of buggies entered ({total_buggies_entered}) does not match total ({race.buggies_entered})")
    if total_buggies_started != race.buggies_started:
        warnings.append(f"number of buggies started ({total_buggies_started}) does not match total ({race.buggies_started})")
    if total_buggies_finished != race.buggies_finished:
        warnings.append(f"number of buggies finished ({total_buggies_finished}) does not match total ({race.buggies_finished})")
    if not warnings or is_ignoring_warnings:
        db.session.execute(delete(RaceResult).where(RaceResult.race_id==race.id))
        db.session.execute(insert(RaceResult).values(results))
        db.session.commit()
    return [ f"Warning: {warning}" for warning in warnings ]



class Race(SurrogatePK, Model):
    """A race."""

    def get_default_race_time():
        # two minutes to midnight ;-)
        tomorrow = datetime.datetime.today() + datetime.timedelta(days=1)
        tomorrow = tomorrow.replace(hour=23, minute=58, second=0, microsecond=0)
        return tomorrow

    __tablename__ = "races"
    id = db.Column(db.Integer, primary_key=True)
    title = Column(db.String(80), unique=False, nullable=False, default="")
    desc = Column(db.Text(), unique=False, nullable=False, default="")
    created_at = Column(db.DateTime, nullable=False, default=datetime.datetime.utcnow)
    start_at = Column(db.DateTime, nullable=False, default=get_default_race_time())
    cost_limit = db.Column(db.Integer(), default=ConfigSettings.DEFAULTS[ConfigSettingNames.DEFAULT_RACE_COST_LIMIT.name])
    is_visible = db.Column(db.Boolean(), default=bool(ConfigSettings.DEFAULTS[ConfigSettingNames.IS_RACE_VISIBLE_BY_DEFAULT.name]))
    result_log_url = Column(db.String(255), unique=True, nullable=True)
    league = Column(db.String(32), unique=False, nullable=True, default="")
    results_uploaded_at = Column(db.DateTime, nullable=True)
    buggies_entered = db.Column(db.Integer, nullable=False, default=0)
    buggies_started = db.Column(db.Integer, nullable=False, default=0)
    buggies_finished = db.Column(db.Integer, nullable=False, default=0)
    buggies_csv_url = Column(db.String(255), nullable=True)
    race_log_url = Column(db.String(255), nullable=True)
    is_result_visible = db.Column(db.Boolean(), nullable=False, default=False)

    results = db.relationship('RaceResult', backref='race')

    def __init__(self, **kwargs):
        """Create instance."""
        db.Model.__init__(self, **kwargs)
        if self.league is None or self.league == "":
            self.league = current_app.config[ConfigSettingNames.DEFAULT_RACE_LEAGUE.name]

    def log_path(self):
        return os.path.join(self.league, self.start_at.strftime('%Y-%m-%d-%H-%M'))

    def slug(self):
        return self.start_at.strftime('%Y-%m-%d-%H-%M')

#      return f"{self.league}self.start_at.strftime('%Y-%m-%d-%H-%M')

class RaceResult(SurrogatePK, Model):

    """A buggy's race result 
    Note that this links to the user not the buggy, because buggy records are
    not constant: they can and will change between races (if you need to find
    the details of buggie at the time they were entered in a race, follow that
    race's buggies_csv_url).
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

