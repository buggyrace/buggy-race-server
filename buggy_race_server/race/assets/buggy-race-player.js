/* =====================================================================
   buggy race runner: 
   accepts a race "results JSON" file URL
   (via ?race= if standalone, otherwise from RACE_LOG_JSON_URL if
   embedded on the race server)

   - loads the race, and linked resources
   - replays the events

   www.buggyrace.net

   =====================================================================*/

const PATTERN_CHECK = "check";
const PATTERN_DSTRIPE = "dstripe";
const PATTERN_HSTRIPE = "hstripe";
const PATTERN_PLAIN = "plain";
const PATTERN_SPOT = "spot";
const PATTERN_VSTRIPE = "vstripe";

const VALID_PATTERNS = [
  PATTERN_CHECK, PATTERN_DSTRIPE, PATTERN_HSTRIPE,
  PATTERN_PLAIN, PATTERN_SPOT, PATTERN_VSTRIPE
];

const EVENT_BUGGY = 'b';
const EVENT_TYPE = 'e';
const EVENT_DELTA = 'd';
const EVENT_STRING = 's';

const EVENT_TYPE_FINISH = 'f';
const EVENT_TYPE_ATTACK_PREFIX = 'a';

const RACE_INFO = {
  title: "Race",
  description: "Description",
  qty_buggies: 0, // buggies that start
  events: [], // [[ {s: 1, b: buggy_id, e: event_type, t: target_buggy_id, d:distance_delta }, ... ] , ...]
  qty_steps: 0,
};

const RACETRACK_DATA = {
  path: null,
  lap_length: null,
  start_point: null,
  transform: null
};

function half_str(w, h){
  return "translate(" + (-w/2) + "," + (-h/2) + ")";
}

const BUGGY_ID_PREFIX = "buggy-"; // ensure buggy IDs don't collide
const BUGGY_ID_SOURCE = "username"; // or "user_id"
const BUGGY_RECT_HEIGHT = 6;
const BUGGY_RECT_WIDTH = 8;
const BUGGY_RECT_TRANSFORM = half_str(BUGGY_RECT_WIDTH, BUGGY_RECT_HEIGHT);
const BUTTONS = document.getElementById("buttons");
const CSS_ALERT = "alert";
const CSS_BLINK = "blink";
const CSS_BTN_FF = "btn-ff";
const CSS_BTN_PAUSE = "btn-pause";
const CSS_BTN_PLAY = "btn-play";
const CSS_DISABLED = "disabled";
const CSS_DISPLAY_NONE = "display-none"
const CSS_EVENT = "event";
const CSS_FAST_FWD = "is-fast-fwd"; // when it is running fast
const CSS_SYSTEM = "system";
const CSS_TRACKING = "tracking";
const CSS_USER_ACTION = "user-action";
const FAST_FORWARD_BUTTON = document.getElementById("btn-ff");
const FAST_FORWARD_SPEED_UP = 8;
const FF_BTN_FAST = "FAST";
const FF_BTN_NORMAL = "ACTUAL";
const INFO_PANEL = document.getElementById("info-panel");
const IS_INVISIBLE_PATH = true; // force path stroke to be none? (CDC prevention)
const IS_JITTERED = false; // experimental bumpiness off the path
const IS_RANDOMISED_FOR_DEV = false; // only true pending real race data
const MAX_STEPS = 100; // used by random race generator, pending real events
const NAMESPACE_SVG = "http://www.w3.org/2000/svg";
const NAMESPACE_XLINK = "http://www.w3.org/1999/xlink";
const PAUSE_BEFORE_PLAY_ENABLE = 2000; // ms
const PAUSE_BEFORE_TRACK_REVEAL = 500; // ms
const PLAY_BUTTON = document.getElementById("btn-play");
const RACE_URL_VAR_NAME = "race";
const RACELOG_DISPLAY = document.getElementById("race-log");
const RACETRACK_CANVAS = document.getElementById("race-canvas");
const RACETRACK_PATH_ID = "race-path";
const RACETRACK_SVG = document.getElementById("racetrack-svg")
const RACETRACK_SVG_DEFS = RACETRACK_SVG.querySelector("defs");
const REPLAY_INDICATOR = document.getElementById("replay-indicator");
const RESET_BUTTON = document.getElementById("btn-reset");
const SCREEN_MASK = document.getElementById("screen-mask");
const STEP_DURATION_IN_S = 1;
const TIME_INDICATOR = document.getElementById("time-indicator");

var crosshairs;
var crosshairs_tracking_id = null;
var is_fast_fwd = false;
var is_first_race = true;
var is_paused = true;
var lap_count = 1;
var leading_buggy_before = null;
var leading_buggy = null;
var race_json;
var racetrack_svg;
var resize_time_id = null;
var step_count = 0;
var qty_finish_events = 0; // if > 0, we have a winner so stop reporting "lead"
var svg_buggies = {}; // keyed on id

// picked up from template/HTML definitions:
var race_url = RACE_RESULTS_JSON_URL;
var user_tracking_id = USER_TRACKING_ID;

function get_query_var(var_name){
  let query = window.location.search.substring(1);
  let vars = query.split("&");
  for (var i=0;i<vars.length;i++) {
    let pair = vars[i].split("=");
    if (pair[0] == var_name){
      return pair[1];
    }
  }
  return(null);
}

function ends_with(long, short) {
return short.length > 0 && long.substr(short.length * -1)==short;
}

function get_random(max, min) {
  min = min || 0;
  return min + Math.round(Math.random() * (max-min))
}

function plural(qty, single, multi){
  if (qty === 1) return "1 " + single;
  return qty + " " + (multi || (single + "s"))
}

function get_time_string(){
  let mins = Math.floor(step_count / 60);
  mins = mins > 99? mins : ("0" + mins).slice(-2);
  return mins + ":" + ("0" + step_count % 60).slice(-2);
}

function bump_now_report(){
  for (let ts of RACELOG_DISPLAY.querySelectorAll(".now")){
    ts.classList.remove("now");
  }
}

function clear_race_log(){
  RACELOG_DISPLAY.replaceChildren();
}

function freeze_racelog_height(){
  /*
    a horrible hack to stop the race log expanding as its content grows
    ...after failing with various CSS layouts including calc().
    Forces racelog height and max-height to be explicitly set, so it doesn't
    grow when more elements are added to its content (which overflow isn't
    graciously absorbing).
  */
  let h_parent = Math.floor(INFO_PANEL.getBoundingClientRect().height);
  let h_buttons = Math.floor(BUTTONS.getBoundingClientRect().height);
  let h = (h_parent - h_buttons * 2) + "px";
  RACELOG_DISPLAY.style.height = h;
  RACELOG_DISPLAY.style.maxHeight = h;
}

function on_resize(){
  // let it collapse so the browser can resize its container
  // ...then fix it up after a timeout to let it settle
  RACELOG_DISPLAY.style.maxHeight = "2rem"; 
  if (resize_time_id){
    clearTimeout(resize_time_id);
  }
  resize_time_id = setTimeout(freeze_racelog_height, 100);
}

function display_time_string() {
  TIME_INDICATOR.innerText = get_time_string() + "/LAP" + lap_count;
}

function get_span(text, css_class) {
  let span = document.createElement("span");
  span.classList.add(css_class);
  span.innerText = text;
  return span;
}

function report(text, css_class, text2){
  let p = document.createElement("p");
  if (css_class === CSS_EVENT){
    let timestamp = get_span(get_time_string(), "ts");
    timestamp.classList.add("now");
  }
  if (css_class){
    p.classList.add(css_class);
  }
  p.append(get_span(text, "m1"));
  if (text2) {
    p.append(get_span(text2, "m2"));
  }
  RACELOG_DISPLAY.prepend(p);
}

function report_event(text, buggy_id){
  let p = document.createElement("p");
  p.classList.add(CSS_EVENT);
  let timestamp = get_span(get_time_string(), "ts");
  timestamp.classList.add("now");
  p.append(timestamp);
  if (buggy_id) {
    let bspan = get_span(pretty_id(buggy_id), "buggy");
    bspan.classList.add(buggy_id, "mr");
    if (crosshairs_tracking_id === buggy_id){
      bspan.classList.add(CSS_TRACKING);
    }
    p.append(bspan);
  }
  let texts = text.split(/(\[\w+\])/);
  for (t of texts) {
    let span;
    let usermatch = t.match(/\[(\w+)\]/); // inline username: allow tracking
    if (usermatch){
      let username = usermatch[1];
      span = get_span(username, "buggy");
      span.classList.add("buggy-" + username);
    } else {
      span = get_span(t, "m1");
    }
    p.append(span);
  }
  RACELOG_DISPLAY.prepend(p);
}

function set_up_race(){
  report("preparing race", CSS_SYSTEM);
  RACE_INFO.title = race_json.title || "Untitled race";
  RACE_INFO.description = race_json.description || "";
  RACE_INFO.events = race_json.events || [];
  if (RACE_INFO.events.length > 0) {
    RACE_INFO.qty_steps = RACE_INFO.events.length;
  } else {
    report("race didn't start: no events to replay", CSS_ALERT)
  }

  let svg_tag = racetrack_svg.getElementsByTagName('svg');
  for (let attrib_name of ["viewBox"]) { // only 1 we care about (for now?)
    try {
      let val = svg_tag[0].attributes[attrib_name].value;
      if (val != undefined) {
        RACETRACK_SVG.setAttribute(attrib_name, val);
      }
    } catch (error) {
      console.log(error); // probably not fatal, so carry on
      report("warning: problem with SVG " + attrib_name, CSS_SYSTEM)
    }
  }

  let paths = racetrack_svg.getElementsByTagName("path");
  if (paths.length != 1) {
    report("error in racetrack (expected single path in SVG)", CSS_ALERT);
    return
  }
  let racetrack_path = racetrack_svg.getElementsByTagName("path")[0];
  racetrack_path.setAttribute("id", RACETRACK_PATH_ID);
  if (IS_INVISIBLE_PATH){
    racetrack_path.setAttribute("stroke", "none");
  }
  RACETRACK_SVG.append(racetrack_path);
  RACETRACK_DATA.lap_length = Math.round(racetrack_path.getTotalLength());
  RACETRACK_DATA.start_point = racetrack_path.getPointAtLength(0);
  RACETRACK_DATA.transform = racetrack_path.attributes["transform"]?
    racetrack_path.attributes["transform"].value : "translate(0,0)";
  RACETRACK_DATA.path = racetrack_path;
  RACETRACK_CANVAS.style.backgroundImage = "url(" + race_json.track_image_url + ")";
  RACE_INFO.qty_buggies = 0;
  let legacyproof_buggies = race_json.buggies || race_json.results; // deprecated: used to be "results"
  for (let buggy of legacyproof_buggies) {
    if (buggy.race_position >= 0){
      svg_buggies[BUGGY_ID_PREFIX + buggy[BUGGY_ID_SOURCE]] = create_svg_buggy(buggy);
      RACE_INFO.qty_buggies += 1;
    }
  }
  crosshairs = document.createElementNS(NAMESPACE_SVG, "use");
  crosshairs.setAttributeNS(NAMESPACE_XLINK, "xlink:href", "#crosshair-indicator");
  crosshairs.setAttribute("transform", RACETRACK_DATA.transform);
  crosshairs.classList.add(CSS_DISPLAY_NONE);
  RACETRACK_SVG.append(crosshairs);
  if (RACE_INFO.qty_buggies > 0){
    if (user_tracking_id){
      user_tracking_id = BUGGY_ID_PREFIX + user_tracking_id;
      if (svg_buggies[user_tracking_id]) {
        track_with_crosshairs(user_tracking_id, true)
      }
    }
    if (! crosshairs_tracking_id) {
      report("Click on a buggy to track it", CSS_USER_ACTION);
    }
  }
  setTimeout(
    function(){
      SCREEN_MASK.style.opacity = 0;
      // see CSS #screen-mask transition (4s)
      setTimeout(function(){SCREEN_MASK.remove()}, 4000);
    },
    PAUSE_BEFORE_TRACK_REVEAL
  )
}

function start_replay(){
  REPLAY_INDICATOR.classList.add(CSS_BLINK);
  PLAY_BUTTON.innerText = "PAUSE";
  PLAY_BUTTON.classList.add(CSS_BTN_PAUSE);
  PLAY_BUTTON.classList.remove(CSS_BTN_PLAY);
  RESET_BUTTON.classList.remove(CSS_DISABLED);
  FAST_FORWARD_BUTTON.classList.remove(CSS_DISABLED);
  FAST_FORWARD_BUTTON.innerText = "FAST";
  is_fast_fwd = false;
  leading_buggy_before = null;
  leading_buggy = null;
  is_paused = false;
  if (step_count == 0){
    report_event("race starts");
  }
  do_step();
}

function stop_replay(){
  REPLAY_INDICATOR.classList.remove(CSS_BLINK);
  PLAY_BUTTON.innerText = "PLAY";
  PLAY_BUTTON.classList.add(CSS_BTN_PLAY);
  PLAY_BUTTON.classList.remove(CSS_BTN_PAUSE);
  FAST_FORWARD_BUTTON.classList.add(CSS_DISABLED);
  FAST_FORWARD_BUTTON.classList.remove(CSS_FAST_FWD);
  FAST_FORWARD_BUTTON.innerText = FF_BTN_FAST;
  is_fast_fwd = false;
  is_paused = true;
}

function reset_replay(){
  step_count = 0;
  lap_count = 1;
  is_paused = true;
  RESET_BUTTON.classList.add(CSS_DISABLED);
  PLAY_BUTTON.classList.remove(CSS_DISABLED);
  FAST_FORWARD_BUTTON.classList.add(CSS_DISABLED);
  FAST_FORWARD_BUTTON.classList.remove(CSS_FAST_FWD);
  FAST_FORWARD_BUTTON.innerText = FF_BTN_FAST;
  is_fast_fwd = false;
  for (let buggy_id in svg_buggies){
    let buggy = svg_buggies[buggy_id];
    buggy.setAttribute("x", RACETRACK_DATA.start_point.x);
    buggy.setAttribute("y", RACETRACK_DATA.start_point.y);
    buggy.track_data = {
      distance: 0, // current distance along the (modular) track
      jitter: IS_JITTERED? (get_random(20)-10)/10 : 0
    };
  }
  display_time_string();
  if (! is_first_race){
    clear_race_log();
    crosshairs_tracking_id = null;
    crosshairs.classList.add(CSS_DISPLAY_NONE);
  }
  is_first_race = false;
  report(
    RACE_INFO.title,
    "title",
    " <" + plural(RACE_INFO.qty_buggies, "starting buggy", "starting buggies") + ">"
  );
}

function init_track_data(buggy){
  buggy.track_data = {
    distance: 0, // current distance along the (modular) track
    jitter: IS_JITTERED? (get_random(20)-10)/10 : 0
  };
}

function ff_multiplier(){ return is_fast_fwd? 1/FAST_FORWARD_SPEED_UP : 1}

function resolve_after_1_second(x) {
  return new Promise((resolve) => {
    setTimeout(() => {resolve(x);}, 1000 * ff_multiplier())
  });
}
async function pause_1_second() {
  await resolve_after_1_second(true);
}

function step_move(buggy, distance_to_move){
  if (buggy.track_data == undefined) {
    init_track_data(buggy)
  }
  buggy.track_data.distance_at_start = buggy.track_data.distance;
  buggy.track_data.distance_moved = 0; // new step, haven't moved yet
  buggy.track_data.target_distance = Math.round(
    buggy.track_data.distance + distance_to_move
  );
  lap_count = Math.max(
    lap_count, Math.ceil(buggy.track_data.distance/RACETRACK_DATA.lap_length)
  );
  return gsap.timeline().to(
    buggy.track_data,
    {
      distance: buggy.track_data.target_distance,
      repeat: 0, // no repetition!
      ease: "none",
      duration: 1 * ff_multiplier(),
      onUpdate: () => {
        const point = RACETRACK_DATA.path.getPointAtLength(
          buggy.track_data.distance % RACETRACK_DATA.lap_length
        );
        point.x += buggy.track_data.jitter;
        point.y += buggy.track_data.jitter;
        buggy.setAttribute("x", point.x);
        buggy.setAttribute("y", point.y);
        if (crosshairs_tracking_id === buggy.id){
          crosshairs.setAttribute("x", point.x);
          crosshairs.setAttribute("y", point.y);  
        }
      }
    }
  ).then(function(){
    buggy.track_data.distance_moved = buggy.track_data.distance -
                                      buggy.track_data.distance_at_start;
    return buggy // value used in promise
  })
}

function track_buggy_in_event_log(buggy_id){
  let mentions = RACELOG_DISPLAY.getElementsByClassName(CSS_TRACKING);
  while( mentions.length > 0) {
    for (let mention of mentions){
      mention.classList.remove(CSS_TRACKING);
    }
    // sometimes misses one (race condition?)
    mentions = RACELOG_DISPLAY.getElementsByClassName(CSS_TRACKING);
  }
  if (buggy_id) {
    mentions = RACELOG_DISPLAY.getElementsByClassName(buggy_id);
    for (let mention of mentions){
      mention.classList.add(CSS_TRACKING);
    }  
  }
}

function track_with_crosshairs(buggy_id, want_tracking){
  if (crosshairs){
    if (want_tracking && svg_buggies[buggy_id]){
      crosshairs_tracking_id = buggy_id;
      let point = RACETRACK_DATA.path.getPointAtLength(
        svg_buggies[buggy_id].track_data.distance % RACETRACK_DATA.lap_length
      );
      crosshairs.setAttribute("x", point.x);
      crosshairs.setAttribute("y", point.y);
      crosshairs.classList.remove(CSS_DISPLAY_NONE);
      let msg = "Tracking " + pretty_id(buggy_id);
      if (is_first_race){
        msg += " (click buggies to change)"
      }
      report(msg, CSS_USER_ACTION);
      track_buggy_in_event_log(buggy_id);
    } else {
      crosshairs_tracking_id = null;
      crosshairs.classList.add("display-none");
      track_buggy_in_event_log(null);
    }
  }
}

function buggy_click(){
  track_with_crosshairs(this.id, crosshairs_tracking_id != this.id)
}

function end_race(msg){
  report(msg, CSS_ALERT);
  PLAY_BUTTON.classList.add(CSS_DISABLED);
}

function pretty_id(buggy_id){
  return buggy_id.substr(BUGGY_ID_PREFIX.length);
}

function do_step(){
  display_time_string();
  let step_promises = [];
  if (step_count >= RACE_INFO.qty_steps) {
    stop_replay();
    end_race("Race ended: no more events in log");
    return;
  }
  if (IS_RANDOMISED_FOR_DEV){
    for (let buggy_id in svg_buggies){
      if (IS_RANDOMISED_FOR_DEV){
        step_promises.push(
          step_move(svg_buggies[buggy_id], get_random(30, 4))
        );
      }
    }
  } else {
    for (let event of RACE_INFO.events[step_count]) {
      let buggy_id = event[EVENT_BUGGY];
      let buggy = svg_buggies[BUGGY_ID_PREFIX + buggy_id];
      let delta = event[EVENT_DELTA]; // TODO parseFloat
      let event_type = event[EVENT_TYPE];
      if (buggy && delta){
          step_promises.push(step_move(buggy, delta));
      }
      if (event_type) {
        if (event_type == EVENT_TYPE_FINISH) {
          qty_finish_events += 1;
          // TODO finish line wave chequered flag/confetti?
        } else if (event_type[0] == EVENT_TYPE_ATTACK_PREFIX) {
          // TODO animation/graphic etc
        }
      }
      if (event[EVENT_STRING]) {
        report_event(event[EVENT_STRING], BUGGY_ID_PREFIX+buggy_id)
      }
    }
  }
  if (step_promises.length === 0) {
    step_promises = [ pause_1_second() ]
  }
  Promise.all(step_promises).then((buggies) => {
    bump_now_report();
    if (step_count > 0) {
      for (let buggy_id in svg_buggies) {
        let buggy = svg_buggies[buggy_id];
        if (!leading_buggy || buggy.track_data.distance > leading_buggy.track_data.distance) {
          leading_buggy = buggy;
        }
      }
      if (qty_finish_events===0 && leading_buggy && leading_buggy != leading_buggy_before) {
        report_event("takes the lead", leading_buggy.id);
        leading_buggy_before = leading_buggy;
      }
    }
    step_count += 1;
    if (! is_paused) {
      do_step()
    }
  });
}

function create_svg_buggy(buggy_data){
  // a lot of trial and effort behind this deceptively simple function
  // returns the SVG buggy (flag) after adding it to the track SVG
  let custom_pattern = document.createElementNS(NAMESPACE_SVG, 'pattern');
  let attribs = {
    id: "pat-" + buggy_data[BUGGY_ID_SOURCE],
    width: BUGGY_RECT_WIDTH, height: BUGGY_RECT_HEIGHT,
    x: "0", y: "0",
  }
  for (let k in attribs){
    custom_pattern.setAttribute(k, attribs[k]);
  }
  var pat_substrate = document.createElementNS(NAMESPACE_SVG, 'use');
  pat_substrate.setAttributeNS(
    NAMESPACE_XLINK, "xlink:href", "#flag-"+PATTERN_PLAIN
  );
  pat_substrate.setAttributeNS(null, "fill", buggy_data.flag_color);
  custom_pattern.appendChild(pat_substrate);
  if (buggy_data.flag_pattern != PATTERN_PLAIN
    && VALID_PATTERNS.includes(buggy_data.flag_pattern)) {
    var pat_secondary = document.createElementNS(NAMESPACE_SVG, 'use');
    pat_secondary.setAttributeNS(
      NAMESPACE_XLINK, "xlink:href", "#flag-" + buggy_data.flag_pattern
    );
    pat_secondary.setAttributeNS(null, "fill", buggy_data.flag_color_secondary);
    custom_pattern.appendChild(pat_secondary);
  }
  RACETRACK_SVG_DEFS.appendChild(custom_pattern);
  let buggy_rect = document.createElementNS(NAMESPACE_SVG, 'rect');
  buggy_rect.setAttribute("width", BUGGY_RECT_WIDTH);
  buggy_rect.setAttribute("height", BUGGY_RECT_HEIGHT);
  buggy_rect.setAttributeNS(
    null, "fill", "url(#pat-" + buggy_data[BUGGY_ID_SOURCE] + ")"
  );
  buggy_rect.setAttribute(
    "id", BUGGY_ID_PREFIX + buggy_data[BUGGY_ID_SOURCE]
  );
  buggy_rect.setAttribute(
    "transform", RACETRACK_DATA.transform + " " + BUGGY_RECT_TRANSFORM
  );
  buggy_rect.setAttribute("class", "svg-buggy");
  init_track_data(buggy_rect);
  buggy_rect.addEventListener("click", buggy_click);
  RACETRACK_SVG.appendChild(buggy_rect);
  return buggy_rect;
}

PLAY_BUTTON.addEventListener("click", function(){
  if (PLAY_BUTTON.classList.contains(CSS_DISABLED)){
    return
  }
  if (PLAY_BUTTON.classList.contains(CSS_BTN_PLAY)){
    start_replay();
  } else {
    report("Paused replay", CSS_USER_ACTION);
    stop_replay();
  }
});

RESET_BUTTON.addEventListener("click", function(){
  if (RESET_BUTTON.classList.contains(CSS_DISABLED)){
    return
  } 
  if (is_paused) {
    reset_replay();
  } else {
    // if currently running — pause instead of reset
    report("Paused replay (press RESET again to reset!)", CSS_USER_ACTION);
    stop_replay();
  }
});

FAST_FORWARD_BUTTON.addEventListener("click", function(){
  if (FAST_FORWARD_BUTTON.classList.contains(CSS_DISABLED)) {
    return
  }
  is_fast_fwd = ! FAST_FORWARD_BUTTON.classList.contains(CSS_FAST_FWD);
  if (is_fast_fwd) {
    FAST_FORWARD_BUTTON.classList.add(CSS_FAST_FWD);
    FAST_FORWARD_BUTTON.innerText = FF_BTN_NORMAL;
  } else {
    FAST_FORWARD_BUTTON.classList.remove(CSS_FAST_FWD);
    FAST_FORWARD_BUTTON.innerText = FF_BTN_FAST;
  }
})

RACELOG_DISPLAY.addEventListener("click", function(e){
  if (e.target.classList.contains("buggy")){
    e.preventDefault();
    let buggy_id = BUGGY_ID_PREFIX + e.target.innerText;
    track_with_crosshairs(buggy_id, crosshairs_tracking_id != buggy_id);
  }
});

window.onresize = on_resize;

(() => {
  // because here we are, with JS reveal the critical interface elements
  BUTTONS.classList.remove("hidden");
  RACELOG_DISPLAY.classList.remove("hidden");

  let httpRequest = new XMLHttpRequest();
  if (!httpRequest) {
    report("cannot load race: no XMLHTTP instance");
    return false;
  }
  freeze_racelog_height();
  /* if embedded (on the race server), RACE_LOG_JSON_URL will be defined */
  let is_running_embedded = race_url!=undefined && race_url.indexOf("{")===-1;
  if (! is_running_embedded) {
    race_url = get_query_var(RACE_URL_VAR_NAME);
  }
  if (!race_url) {
    if (is_running_embedded) {
      report("maybe the race results/log file has not been uploaded yet", CSS_SYSTEM);
    } else {
      report("try adding ?race=xyx to the URL (xyz must be a valid race file name", CSS_SYSTEM);
    }
    report("cannot load race: missing the URL", CSS_ALERT);
  } else {
    if (race_url.substr(-5) != ".json") {
      race_url += ".json";
    }
    report("loading race JSON", CSS_SYSTEM);
    console.log("loading race JSON from " + race_url);
    
    fetch(race_url).then((response) => {
      if (!response.ok) {
        throw new Error(`HTTP error: ${response.status} fetching race JSON`);
      }
      return response.json();
    })
    .then((json_data) => {
      race_json = json_data;
      if (! race_json.track_svg_url) {
        throw new Error("there's no racetrack SVG URL in the race JSON")
      }
      report("loading resources", CSS_SYSTEM);
      return fetch(race_json.track_svg_url).then((response) => {
        if (!response.ok) {
          throw new Error(`HTTP error: ${response.status} fetching track SVG`);
        }
        return response.text();
      })
    })
    .then((svg_src) => {
      try {
        var parser = new DOMParser();
        racetrack_svg = parser.parseFromString(svg_src, "image/svg+xml");
      } catch (error) {
        throw new Error("failed to parse SVG data")
      }
      set_up_race();
      setTimeout(function(){reset_replay()}, PAUSE_BEFORE_PLAY_ENABLE);
    })
    .catch((error) => {
      report(`cannot load race - ${error}`, CSS_ALERT);
      TIME_INDICATOR.innerText = "NO-RACE";
    });
  }
})();
