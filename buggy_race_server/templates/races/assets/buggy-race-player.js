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
  
const RACE_INFO = {
  title: "Race",
  description: "Description",
  qty_buggies: 0, // buggies that start
};

const RACETRACK_DATA = {
  path: null,
  lap_ength: null,
  start_point: null,
  transform: null
};

const BUGGY_ID_PREFIX = "buggy-"; // ensure buggy IDs don't collide
const BUGGY_ID_SOURCE = "username"; // or "user_id"
const BUGGY_RECT_HEIGHT = 6;
const BUGGY_RECT_WIDTH = 8;
const BUTTONS = document.getElementById("buttons");
const CLICK_DURATION = 1;
const CSS_DISABLED = "disabled";
const INFO_PANEL = document.getElementById("info-panel");
const IS_INVISIBLE_PATH = true; // force path stroke to be none? (CDC prevention)
const IS_JITTERED = false; // experimental bumpiness off the path
const IS_RANDOMISED_FOR_DEV = true; // only true pending real race data
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
const TIME_INDICATOR = document.getElementById("time-indicator");

var crosshairs;
var crosshairs_tracking_id = null;
var is_first_race = true;
var is_paused = true;
var lap_count = 1;
var leading_buggy_before = null;
var leading_buggy = null;
var race_json;
var racetrack_svg;
var resize_time_id = null;
var step_count = 0;
var  svg_buggies = {}; // keyed on id

// picked up from template/HTML definitions:
var race_url = RACE_LOG_JSON_URL;
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

function report(msg, css_class, extra_span){
  let p = document.createElement("p");
  p.innerText = msg;
  if (! css_class){
    let span = document.createElement("span");
    span.classList.add("ts");
    span.classList.add("now");
    span.innerText = get_time_string();
    p.prepend(span);
  } else {
    p.classList.add(css_class);
  }
  if (extra_span) {
    let span = document.createElement("span");
    span.innerText = extra_span;
    p.append(span);
  }
  RACELOG_DISPLAY.prepend(p)
}

function set_up_race(){
  report("preparing race", "system");
  if (race_json.title) {
    RACE_INFO.title = race_json.title;
  }
  RACE_INFO.description = race_json.description || "";
  let svg_tag = racetrack_svg.getElementsByTagName('svg');
  for (let attrib_name of ["viewBox"]) { // only 1 we care about (for now?)
    try {
      let val = svg_tag[0].attributes[attrib_name].value;
      if (val != undefined) {
        RACETRACK_SVG.setAttribute(attrib_name, val);
      }
    } catch (error) {
      console.log(error); // probably not fatal, so carry on
      report("warning: problem with SVG " + attrib_name, "system")
    }
  }

  let paths = racetrack_svg.getElementsByTagName('path');
  if (paths.length != 1) {
    report("error in racetrack (expected single path in SVG)", "alert");
    return
  }
  let racetrack_path = racetrack_svg.getElementsByTagName('path')[0];
  racetrack_path.setAttribute("id", RACETRACK_PATH_ID);
  if (IS_INVISIBLE_PATH){
    racetrack_path.setAttribute("stroke", "none");
  }
  RACETRACK_SVG.append(racetrack_path);
  RACETRACK_DATA.lap_length = Math.round(racetrack_path.getTotalLength());
  RACETRACK_DATA.start_point = racetrack_path.getPointAtLength(0);
  if (racetrack_path.attributes['transform']){
    RACETRACK_DATA.transform = racetrack_path.attributes['transform'].value;
  }
  RACETRACK_DATA.path = racetrack_path;
  
  RACETRACK_CANVAS.style.backgroundImage = "url(" + race_json.track_image_url + ")";
  RACE_INFO.qty_buggies = 0;
  for (let buggy of race_json.results) {
    if (buggy.race_position >= 0){
      svg_buggies[BUGGY_ID_PREFIX + buggy[BUGGY_ID_SOURCE]] = create_svg_buggy(buggy);
      RACE_INFO.qty_buggies += 1;
    }
  }
  crosshairs = document.createElementNS(NAMESPACE_SVG, 'use');
  crosshairs.setAttributeNS(NAMESPACE_XLINK, "xlink:href", "#crosshair-indicator");
  crosshairs.setAttribute("transform", RACETRACK_DATA.transform + " translate(4,3)");
  crosshairs.classList.add("display-none");
  RACETRACK_SVG.append(crosshairs);
  if (user_tracking_id){
    user_tracking_id = BUGGY_ID_PREFIX + user_tracking_id;
    if (svg_buggies[user_tracking_id]) {
      track_with_crosshairs(user_tracking_id, true)
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
  REPLAY_INDICATOR.classList.add("blink");
  PLAY_BUTTON.innerText = "PAUSE";
  PLAY_BUTTON.classList.add("btn-pause");
  PLAY_BUTTON.classList.remove("btn-play");
  RESET_BUTTON.classList.remove(CSS_DISABLED);
  is_paused = false;
  do_step();
}

function stop_replay(){
  REPLAY_INDICATOR.classList.remove("blink");
  PLAY_BUTTON.innerText = "PLAY";
  PLAY_BUTTON.classList.add("btn-play");
  PLAY_BUTTON.classList.remove("btn-pause");
  is_paused = true;
}

function reset_replay(){
  step_count = 0;
  lap_count = 1;
  is_paused = true;
  RESET_BUTTON.classList.add(CSS_DISABLED);
  PLAY_BUTTON.classList.remove(CSS_DISABLED);
  for (let buggy_id in svg_buggies){
    let buggy = svg_buggies[buggy_id];
    buggy.setAttribute('x', RACETRACK_DATA.start_point.x);
    buggy.setAttribute('y', RACETRACK_DATA.start_point.y);
    buggy.track_data = {
      distance: 0, // current distance along the (modular) track
      jitter: IS_JITTERED? (get_random(20)-10)/10 : 0
    };
  }
  display_time_string();
  if (! is_first_race){
    clear_race_log();
    crosshairs_tracking_id = null;
    crosshairs.classList.add("display-none");
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
      duration: CLICK_DURATION,
      onUpdate: () => {
        const point = RACETRACK_DATA.path.getPointAtLength(
          buggy.track_data.distance % RACETRACK_DATA.lap_length
        );
        point.x += buggy.track_data.jitter;
        point.y += buggy.track_data.jitter;
        buggy.setAttribute('x', point.x);
        buggy.setAttribute('y', point.y);
        if (crosshairs_tracking_id === buggy.id){
          crosshairs.setAttribute('x', point.x);
          crosshairs.setAttribute('y', point.y);  
        }
      }
    }
  ).then(function(){
    buggy.track_data.distance_moved = buggy.track_data.distance -
                                      buggy.track_data.distance_at_start;
    return buggy // value used in promise
  })
}

function track_with_crosshairs(buggy_id, want_tracking){
  if (crosshairs){
    if (want_tracking && svg_buggies[buggy_id]){
      crosshairs_tracking_id = buggy_id;
      let point = RACETRACK_DATA.path.getPointAtLength(
        svg_buggies[buggy_id].track_data.distance
      );
      crosshairs.setAttribute('x', point.x);
      crosshairs.setAttribute('y', point.y);
      crosshairs.classList.remove("display-none");
      let msg = "Tracking " + pretty_id(buggy_id);
      if (is_first_race){
        msg += " (click buggies to change)"
      }
      report(msg, "user-action");
    } else {
      crosshairs_tracking_id = null;
      crosshairs.classList.add("display-none");
    }
  }
}

function buggy_click(){
  track_with_crosshairs(this.id, crosshairs_tracking_id != this.id)
}

function end_race(msg){
  report(msg, "alert");
  PLAY_BUTTON.classList.add(CSS_DISABLED);
}

function pretty_id(buggy_id){
  return buggy_id.substr(BUGGY_ID_PREFIX.length);
}

function do_step(){
  display_time_string();

  if (step_count > 0) {
    for (let buggy_id in svg_buggies) {
      let buggy = svg_buggies[buggy_id];
      if (!leading_buggy || buggy.track_data.distance > leading_buggy.track_data.distance) {
        leading_buggy = buggy;
      }
    }
    if (leading_buggy && leading_buggy != leading_buggy_before) {
      report(pretty_id(leading_buggy.id) + " takes the lead");
      leading_buggy_before = leading_buggy;
    }
  }

  let step_promises = [];
  for (let buggy_id in svg_buggies){
    if (IS_RANDOMISED_FOR_DEV){
      step_promises.push(
        step_move(svg_buggies[buggy_id], get_random(30, 4))
      );
    }
  }
  Promise.all(step_promises).then((buggies) => {
    bump_now_report();
    let total_distances_moved = 0;
    for (let buggy of buggies) {
      total_distances_moved += buggy.track_data.distance_moved;
    }
    step_count += 1;
    if (step_count > MAX_STEPS) {
      stop_replay()
      end_race("race ended: no more events in log")
    } else if (total_distances_moved === 0) {
      // slightly risky if buggies can start again (they can't)
      stop_replay()
      end_race("race ended: no buggies moving");
    } else if (! is_paused) {
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
  if (RACETRACK_DATA.transform) {
    buggy_rect.setAttribute("transform", RACETRACK_DATA.transform);
  }
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
  if (PLAY_BUTTON.classList.contains("btn-play")){
    start_replay();
  } else {
    report("Paused replay", "user-action");
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
    report("Paused replay (press RESET again to reset!)", "user-action");
    stop_replay();
  }
});

window.onresize = on_resize;

(() => {
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
      report("maybe the race results/log file has not been uploaded yet", "system");
    } else {
      report("try adding ?race=xyx to the URL (xyz must be a valid race file name", "system");
    }
    report("cannot load race: missing the URL", "alert");
  } else {
    if (race_url.substr(-5) != ".json") {
      race_url += ".json";
    }
    report("loading race JSON", "system");
    console.log("loading race JSON from " + race_url);
    
    fetch(race_url).then((response) => {
      if (!response.ok) {
        throw new Error(`HTTP error: ${response.status} fetching race JSON`);
      }
      return response.json();
    }).then((json_data) => {
      race_json = json_data;
      if (! race_json.track_svg_url) {
        throw new Error("there's no racetrack SVG URL in the race JSON")
      }
      if (! race_json.race_log_url) {
        throw new Error("there's no race log URL in the race JSON")
      }
      report("loading resources", "system");
      fetch(race_json.race_log_url).then((response) => {
        if (!response.ok) {
          throw new Error(`HTTP error: ${response.status} fetching race log JSON`);
        }
        return response.json();
      }).then((json_data) => {
        // now SVG
        fetch(race_json.track_svg_url).then((response) => {
          if (!response.ok) {
            throw new Error(`HTTP error: ${response.status} fetching track SVG`);
          }
          return response.text();
        }).then((svg_src) => {
          try {
            var parser = new DOMParser();
            racetrack_svg = parser.parseFromString(svg_src, "image/svg+xml");
          } catch (error) {
            throw new Error("failed to parse SVG data")
          }
          set_up_race();
          setTimeout(function(){
            reset_replay();
          }, PAUSE_BEFORE_PLAY_ENABLE);
        })
      })
    })
    .catch((error) => {report(`cannot load race - ${error}`, "alert")})
  }
})();
