// App initialization code goes here

// if both these elements are present on the page, do bulk-registration:
const USER_REGISTER_FORM_ID = "registerForm";
const USER_REGISTER_CSV_ID = "userdata";

let csv_upload_file_contents = "";
const USER_REGISTER_CSV_FILE = "csv_file";
const USER_REGISTER_CSV_EXAMPLE = "example-csv";
const USER_REGISTER_CSV_EXAMPLE_TRIGGER = "example-csv-trigger";

function bulk_registration_by_ajax(bulk_register_form){
  const BULK_REGISTER_URL = "/admin/users/register/json";
  const USER_REGISTER_AUTH_ID = "auth_code";
  const USER_REGISTER_CSRF_ID = "csrf_token";
  const USER_REGISTER_PROGRESS_ID = "registration-progress";
  const USER_REGISTER_STATUS_ID = "registration-status";
  
  const $reg_container = $("#"+USER_REGISTER_PROGRESS_ID);
  const $progress_list = $reg_container.find("ul");
  const $status_div = $("#"+USER_REGISTER_STATUS_ID);
  const authcode = bulk_register_form[USER_REGISTER_AUTH_ID].value;
  const csrf_token = bulk_register_form[USER_REGISTER_CSRF_ID].value;

  const USER_REGISTER_QTY_RECORDS = "reg-qty-records";
  const USER_REGISTER_QTY_FAIL = "reg-qty-fail";
  const USER_REGISTER_QTY_OK = "reg-qty-ok";
  const USER_REGISTER_QTY_DONE = "reg-qty-done";
  const USER_REGISTER_QTY_PERCENT = "reg-qty-done-percent";

  const $qty_displays = {}
  $qty_displays[USER_REGISTER_QTY_RECORDS] = $("#"+USER_REGISTER_QTY_RECORDS);
  $qty_displays[USER_REGISTER_QTY_FAIL] = $("#"+USER_REGISTER_QTY_FAIL);
  $qty_displays[USER_REGISTER_QTY_OK] = $("#"+USER_REGISTER_QTY_OK);
  $qty_displays[USER_REGISTER_QTY_DONE] = $("#"+USER_REGISTER_QTY_DONE);
  $qty_displays[USER_REGISTER_QTY_PERCENT] = $("#"+USER_REGISTER_QTY_PERCENT);

  let qty_reg_ok = 0;
  let qty_reg_fail = 0;
  let qty_reg_total = 0;

  function reset_display(){
    qty_reg_ok = 0;
    qty_reg_fail = 0;
    qty_reg_total = 0;
    update_reg_progress();
    $status_div.empty();
    $progress_list.empty();
  }

  function update_status(message, css_class) {
    for (let msg_div of $status_div.children()){
      if (msg_div.innerText == message){
        return; // already displaying this message, break out
      }
    }
    let $new_msg = $("<div/>");
    $new_msg.addClass([css_class, "alert"]);
    $new_msg.text(message);
    $status_div.append($new_msg);
  }

  function update_reg_progress() {
    if (qty_reg_total === 0) {
      // should be caught before calling
    } else {
      let running_total = qty_reg_ok + qty_reg_fail;
      $qty_displays[USER_REGISTER_QTY_RECORDS].text(qty_reg_total);
      $qty_displays[USER_REGISTER_QTY_FAIL].text(qty_reg_fail);
      $qty_displays[USER_REGISTER_QTY_OK].text(qty_reg_ok);
      $qty_displays[USER_REGISTER_QTY_DONE].text(running_total);
      $qty_displays[USER_REGISTER_QTY_PERCENT].text(
        Math.round(100 * running_total/qty_reg_total)
      );
    }
  }

  function register_next(csv_rows_as_dicts, reg_index){
    reg_index += 1;
    if (reg_index < qty_reg_total) {
      register_by_ajax(csv_rows_as_dicts, reg_index);
    } else {
      if (qty_reg_total > 0 && qty_reg_ok === qty_reg_total) {
        update_status("OK, finished!", "alert-success");
      }
      $(bulk_register_form).slideDown("slow");
    }
  }

  function register_by_ajax(csv_rows_as_dicts, reg_index){
    qty_reg_total = csv_rows_as_dicts.length;
    update_reg_progress();
    let userdata = csv_rows_as_dicts[reg_index];
    let $user_element = $("<li>");
    let $user_status = $("<span>");
    $user_element.text(userdata['username']);
    $user_element.addClass("list-group-item-warning");
    $user_status.text("?");
    $user_element.append($user_status);
    $progress_list.append($user_element);
    // create CSV with username as the first column
    let cols = ["username"];
    let values = [userdata['username']];
    for (let col in csv_rows_as_dicts[reg_index]){
      if (col != "username"){
        cols.push(col);
        values.push(csv_rows_as_dicts[reg_index][col]);
      }
    }
    let userdata_as_csv = cols.join(",") + "\n" + values.join(",");
    let request_data = {};
    request_data[USER_REGISTER_CSRF_ID] = csrf_token;
    request_data[USER_REGISTER_AUTH_ID] = authcode;
    request_data[USER_REGISTER_CSV_ID] = userdata_as_csv;
    let new_status = "danger";
    $.post(BULK_REGISTER_URL, request_data)
    .done(function(data, textStatus, errorThrown) {
      if (data) {
        if (data.status === "OK") {
          new_status = "ok";
        } else {
          update_status(data.error, "alert-danger");
        }
      }
    })
    .always(function() {
      $user_element[0].className = "";
      if (new_status === "ok") {
        qty_reg_ok += 1;
        $user_element.addClass("list-group-item-success");
        $user_status.text("OK");
      } else {
        qty_reg_fail += 1;
        $user_element.addClass("list-group-item-danger");
        $user_status.text("fail");
      }
      update_reg_progress();
      register_next(csv_rows_as_dicts, reg_index);
    })
  }

  reset_display();
  $reg_container.slideDown("slow");
  let csv_raw_rows = [];
  let csv_rows_as_dicts = [];
  let header_row = [];
  let example_csv = document.getElementById(USER_REGISTER_CSV_EXAMPLE);
  let ideal_header_items = ("" + example_csv? example_csv.dataset.headerRow : "").split(",");
  let err_msg = null;
  if (! authcode) {
    err_msg = "You must supply the authorisation code";
  } else {
    if (csv_upload_file_contents){ // use uploaded file
      csv_raw_rows = csv_upload_file_contents.split("\n");
    } else { // use textarea's contents
      csv_raw_rows = bulk_register_form[USER_REGISTER_CSV_ID].value.split("\n");
    }
    for (let i=0; i<csv_raw_rows.length; i++) {
      let row = csv_raw_rows[i].split(/\s*,\s*/);
      if (i === 0) {
        let missing_cols = [];
        for (let colname of ideal_header_items){
          if (! row.includes(colname)){
            missing_cols.push(colname);
          }
        }
        if (row.length < 2) {
          if (ideal_header_items.length > 0) {
            err_msg = "Missing header row: the first line should look something like this: " + ideal_header_items.join(",");
          } else {
            err_msg = "Missing header row: the first line should have the column titles";
          }
          break;
        } else if (missing_cols.length == 1) {
          err_msg = "The header row (first line) is missing this column: " + missing_cols[0];
          break;
        } else if (missing_cols.length > 1) {
          err_msg = "The header row (first line) is missing these columns: " + missing_cols.join(", ");
          break;
        } else {
          header_row = row;
        }
      } else {
        if (row.length == header_row.length) {
          let user_data = {};
          for (let j=0; j<header_row.length; j++) {
            user_data[header_row[j]] = row[j]
          }
          csv_rows_as_dicts.push(user_data);
        }
      }
    }
    if (! err_msg && csv_rows_as_dicts.length === 0) {
      err_msg = "Cannot process CSV: found a header row, but no data"
    }
  }
  if (err_msg) {
    update_status(err_msg, "alert-danger");
    $(bulk_register_form).slideDown("slow");
  } else {
    register_by_ajax(csv_rows_as_dicts, 0);
  }
}

/* code for prettifying a countdown deadline (project submission) */
const secs_in_hour = 60 * 60;
const secs_in_day = secs_in_hour * 24;
const secs_in_week = secs_in_day * 7;
const deadline_css_classes = ["alert-info", "alert-success", "alert-warning", "alert-danger"];
const deadline_container=document.getElementById("deadline-container");
const deadline_display=document.getElementById("deadline-countdown");

function plural_s(num, noun){
  return num + " " + noun + (num == 1? "": "s") + " ";
}

function run_countdown(){
  deadline = new Date(deadline_display.dataset.deadline);
  let delta_s = Math.floor((deadline-Date.now())/1000);
  let msg = "";
  let css_class="alert-info";
  if (delta_s <= 0) {
    msg = "deadline has passed"
  } else {
    let weeks = Math.floor(delta_s / secs_in_week);
    if (weeks > 0) {
      msg = plural_s(weeks, "week");
      css_class="alert-success";
    } else {
      css_class="alert-warning";
    }
    delta_s -= weeks * secs_in_week;
    let days = Math.floor(delta_s / secs_in_day);
    if (days > 0) {
      msg += plural_s(days, "day");
    }
    delta_s -= days * secs_in_day;
    if (weeks == 0) {
      let hours = Math.floor(delta_s / secs_in_hour);
      if (hours > 0) {
        msg += plural_s(hours, "hour");
      } else if (days == 0) {
        msg = "less than an hour";
      }
      if (days == 0){
        css_class="alert-danger";
      }
    }
    msg += " to go"
    window.setTimeout(run_countdown, 60000); // every minute
  }
  deadline_display.innerText=msg;
  for (class_name of deadline_css_classes) {
    if (class_name == css_class){
      deadline_container.classList.add(class_name);
    } else {
      deadline_container.classList.remove(class_name);
    }
  }
}

$(function() {
  TASK_PATH = "/project/tasks";
  const TASK_RE = new RegExp('#task-(\\d)-(\\w+)', 'i');
  if (window.location.pathname.slice(0, TASK_PATH.length)==TASK_PATH){
    match = window.location.hash.match(TASK_RE);
    let flash_msgs = document.getElementById("flash-msgs");
    if (flash_msgs && match) {
      let phase = match[1];
      let name = match[2].toUpperCase();
      let full_name = phase + "-" + name;
      if (! document.getElementById("task-" + full_name.toLowerCase())){
          message = "There's no task called " + full_name +"!";
          task_404_outer = document.createElement("div");
          task_404_outer.classList.add("col-sm-12", "alert", "alert-danger");
          task_404_inner = document.createElement("div");
          task_404_inner.classList.add("container");
          task_404_close = document.createElement("a");
          task_404_close.setAttribute("href", "#");
          task_404_close.setAttribute("title", "Close");
          task_404_close.dataset.dismiss="alert";
          task_404_close.innerHTML = "&times;";
          task_404_close.classList.add("close");
          task_404_inner.innerText = message;
          task_404_inner.appendChild(task_404_close);
          task_404_outer.appendChild(task_404_inner);
          flash_msgs.appendChild(task_404_outer);
      }
    }
  }
  if (typeof USER_BUGGY_JSON !== "undefined") {
    //----------------------------------------------------------
    // if this page has users' buggy json available,
    // turn any json-btn (spans) into clickable buttons that
    // populate the popup with JSON.
    // Can't easily do this in-line in the templates because
    // jsquery and bootstrap.js aren't loaded until afterwards
    //----------------------------------------------------------
    var $json_buttons = $(".json-btn");
    var $json_modal = $("#jsonModal");
    var $json_payload = $("#json-payload");
    var $json_modal_title =$("#json-title");
    var display_json = function() {
      let username = this.getAttribute("data-username");
      const hyphen_regex = /_/g;
      let pretty_username = username.replace(hyphen_regex, "-");
      $json_modal_title.text(pretty_username + "'s buggy JSON");
      $json_payload.text(USER_BUGGY_JSON[username]);
      $json_modal.modal('show')
    };
    $json_buttons.addClass("btn btn-outline-secondary btn-white btn-sm");
    $json_buttons.on("click", display_json);
  }

  // for bulk registration, try to intervene with JavaScript to send
  // registration requests one by one with Ajax, because the bulk
  // registration is frustratingly timing out (sigh: cookiecutter+SqlAlchemy)
  let bulk_register_form = document.getElementById(USER_REGISTER_FORM_ID);
  if (bulk_register_form && document.getElementById(USER_REGISTER_CSV_ID)){
    let csv_file_upload = document.getElementById(USER_REGISTER_CSV_FILE);
    csv_file_upload.addEventListener("change", function(){
      let GetCsvFile = new FileReader();
      GetCsvFile .onload=function(){
        csv_upload_file_contents = GetCsvFile.result;
      }
      GetCsvFile.readAsText(this.files[0]);
    });
    bulk_register_form.addEventListener('submit', function(e){
      e.preventDefault();
      bulk_register_form.classList.remove("d-none");
      $(bulk_register_form).slideUp(
        "slow",
        function(){bulk_registration_by_ajax(bulk_register_form)}
      );
    });
  }
  // hide the example CSV unless user clicks button to show (toggle) it
  let bulk_reg_example_trigger = document.getElementById(USER_REGISTER_CSV_EXAMPLE_TRIGGER);
  if (bulk_reg_example_trigger){
    let example_csv = document.getElementById(USER_REGISTER_CSV_EXAMPLE);
    if (example_csv){
      example_csv.classList.add("d-none");
      trigger_btn = document.createElement("button");
      trigger_btn.classList.add("btn", "btn-sm", "btn-outline-secondary");
      trigger_btn.innerText = "Show example";
      trigger_btn.addEventListener("click", function(e){
        e.preventDefault(); // we're inside a form
        example_csv.classList.toggle('d-none');
      });
      bulk_reg_example_trigger.replaceWith(trigger_btn);
    }
  }

  const CSS_BTN_COLUMN_SHOWN = "btn-dark";
  const CSS_BTN_COLUMN_HIDDEN = "btn-outline-secondary";
  const ALL_COLUMNS = "all-columns";
  let btn_all_columns;

  let $user_column_toggle_div = $("#user-column-toggles");
  if ($user_column_toggle_div){
    let is_init_done = false;

    function show_or_hide_col_by_button(btn, want_to_hide){
      let css_class = btn.dataset.column;
      localStorage.setItem(css_class, want_to_hide);
      let $elements = $("."+css_class);
      if (want_to_hide) {
        btn.classList.remove(CSS_BTN_COLUMN_SHOWN);
        btn.classList.add(CSS_BTN_COLUMN_HIDDEN);
        if (is_init_done) {
          $elements.fadeOut("slow");
        } else {
          $elements.hide();
        }
      } else {
        btn.classList.remove(CSS_BTN_COLUMN_HIDDEN);
        btn.classList.add(CSS_BTN_COLUMN_SHOWN);
        if (is_init_done) {
          $elements.fadeIn("slow");
        } else {
          $elements.show();
        }
      }
      if (css_class === ALL_COLUMNS) {
        $user_column_toggle_div.find("button").each(function(){
          if ($(this)[0].dataset.column != ALL_COLUMNS) {
            show_or_hide_col_by_button($(this)[0], want_to_hide)
          }
        });
      } else if (want_to_hide && btn_all_columns){
        // "All columns" not marked as "shown" if any cols are hidden
        btn_all_columns.classList.remove(CSS_BTN_COLUMN_SHOWN);
        btn_all_columns.classList.add(CSS_BTN_COLUMN_HIDDEN);
      }
    }

    $user_column_toggle_div.find("button").each(function(){
      $(this).on("click", function(e){
        show_or_hide_col_by_button(
          e.target,
          e.target.classList.contains(CSS_BTN_COLUMN_SHOWN)
        )
      });
      let want_to_hide = localStorage.getItem(this.dataset.column)=="true";
      if ($(this)[0].dataset.column == ALL_COLUMNS) {
        btn_all_columns = this;
      } else {
        show_or_hide_col_by_button(
          $(this)[0],
          want_to_hide
        );
      }
    });
    is_init_done = true; // now show/hide uses slow fade, so user notices
  }

  let $task_counts = $(".task-count");
  if ($task_counts){

    function toggle_task_display(){
      let $tasks_box = $(".phase-tasks-"+this.dataset.phase);
      let is_hidden = this.dataset.is_hidden == "1";
      if (is_hidden){
        $tasks_box.slideDown("slow");
        this.innerText = "Hide " + this.dataset.text
      } else {
        $tasks_box.slideUp("slow")
        this.innerText = "Show " + this.dataset.text
      }
      this.dataset.is_hidden = is_hidden? "0" : "1"; // toggle
    }

    $task_counts.each(function(){
      // collapse any box which doesn't have texts
      let $tasks_box = $(".phase-tasks-"+this.dataset.phase);
      let is_hidden = $tasks_box.find(".task-text").length == 0;
      this.dataset.text = this.innerText;
      this.dataset.is_hidden = is_hidden? "0" : "1";
      this.classList.add("btn", "btn-outline-primary", "btn-white");
      this.addEventListener("click", toggle_task_display);
      this.dispatchEvent(new Event("click"));
    });

    let $goto_btns = $(".btn-goto-text");
    if ($goto_btns){
      // need to unhide phase if trying to jump to anchor within it
      function reveal_goto_target(){
        let toggle_btn = document.getElementById("toggle-btn-" + this.dataset.phase);
        if (toggle_btn && toggle_btn.dataset.is_hidden == "1"){
          toggle_btn.dispatchEvent(new Event("click"));
        }  
      }
      $(".btn-goto-text").each(function(){
        this.addEventListener("click", reveal_goto_target)
      });
    }

    let authcode_box = document.getElementById('change-password-authcode');
    // be kind: hide authcode when an admin changes their _own_ password
    if (authcode_box){
      const current_username = authcode_box.dataset.username;
      const admin_usernames_str = authcode_box.dataset.admins;
      const admins = admin_usernames_str? admin_usernames_str.split(",") : [];
      const username_input = document.getElementById('username');
      function is_auth_needed(){
        return (
          (username_input.value != current_username)
          && admins.includes(username_input.value)
        )
      }

      if (current_username && username_input) {
        if (! is_auth_needed()) {
          authcode_box.classList.add("hidden");
        }

        function show_auth_code(){
          let is_auth_needed_var = is_auth_needed();
          if (is_auth_needed_var){
            $(authcode_box).slideDown();
          } else {
            $(authcode_box).slideUp();
          }
        }

        username_input.addEventListener("change", show_auth_code);
      }
    }
  }

  if (deadline_display){
    run_countdown();
  }

  const modal_user_button = document.getElementById("btn-to-user-texts");
  if (modal_user_button) {
    const JSON_BUGGY_URL = "/admin/json/latest-json/"
    const JSON_TEXT_URL = "/admin/json/text/";
    const modal_title = document.getElementById("texts-modal-label");
    const modal_text_body = document.getElementById("modal-text-body");
    const modal_timestamp = document.getElementById("modal-timestamp");
    $('#texts-modal').on('show.bs.modal', function (event) {
      modal_text_body.innerText = "";
      modal_timestamp.innerText = "";
      let $button = $(event.relatedTarget); // Button that triggered the modal
      let text_id = $button.data("textid");
      let user_id = $button.data("uid");
      let username = $button.data("un");
      let taskname = $button.data("tn");
      let ajax_url, title_str, thru_button_str;
      if ($button.data("buggy")) {
        ajax_url = JSON_BUGGY_URL + user_id;
        title_str = username + "'s uploaded JSON";
        thru_button_str = username + "'s buggy";
      } else if ($button.data("comment")) {
        title_str = "Comment on " + username;
        modal_text_body.innerText = $button.data("comment");
      } else {
        ajax_url = JSON_TEXT_URL + text_id;
        title_str = username + "'s text for " + taskname;
        thru_button_str = username + "'s texts";
      }
      modal_title.innerText = title_str;
      if (ajax_url) {
        $.ajax(ajax_url, {dataType: "json"})
          .done(function(json_data) {
            modal_text_body.classList.add("task-text");
            modal_text_body.classList.remove("alert-danger");
            modal_text_body.innerText=json_data.text;
            if (json_data.uploaded_at){
              modal_timestamp.innerHTML="<em>Uploaded:</em>: " + json_data.uploaded_at;
            } else if (json_data.modified_at){
              modal_timestamp.innerHTML="<em>Updated:</em>: " + json_data.modified_at;
            } else if (json_data.created_at){
              modal_timestamp.innerHTML="<em>Created:</em>: " + json_data.created_at;
            }
          })
        .fail(function(response) {
          modal_text_body.classList.add("alert-danger");
          modal_text_body.classList.remove("task-text");
          modal_text_body.innerText="Error: " + response.status + " " + response.statusText
        })
      }
      if (thru_button_str) {
        modal_user_button.classList.remove("hidden")
        modal_user_button.innerHTML = thru_button_str;
        modal_user_button.setAttribute("href", $button.attr("href"));
      } else {
        modal_user_button.classList.add("hidden");
      }
    });
  }

  const CSS_INNER_BTN = "inner-btn";
  const CSS_BTN_DEFAUT = "btn-primary";
  const CSS_BTN_SUCCESS = "btn-success";
  const CSS_BTN_FAIL = "btn-danger";
  function reset_all_copy_buttons(){
    let copy_btns = document.getElementsByClassName(CSS_INNER_BTN);
    for (let btn of copy_btns){
      btn.classList.add(CSS_BTN_DEFAUT);
      btn.classList.remove(CSS_BTN_SUCCESS, CSS_BTN_FAIL);
    }
  }
  $(".copy-to-clipboard").each(function(){
    let target = document.getElementById(this.dataset.target);
    if (target){
      let copybtn = document.createElement("button");
      copybtn.classList.add("btn", "btn-sm", CSS_INNER_BTN, CSS_BTN_DEFAUT);
      copybtn.innerHTML="<span class='icon-copy'></span> Copy";
      this.prepend(copybtn); // appended to container
      copybtn.addEventListener("click", function(e){
        reset_all_copy_buttons();
        navigator.clipboard.writeText(target.innerText).then(
          () => { /* copy success */
                  this.classList.add(CSS_BTN_SUCCESS);
                  this.classList.remove(CSS_BTN_DEFAUT, CSS_BTN_FAIL)
                },
          () => { /* copy fail */
                  this.classList.add(CSS_BTN_FAIL);
                  this.classList.remove(CSS_BTN_DEFAUT, CSS_BTN_SUCCESS)
                }
        );
      });
    }
  })
});
$(function() {
  // code for the race-picker... needs jQuery to dismiss bootstrap modal :-(
  const TRACK_PICKER_MODAL = document.getElementById("track-picker-modal");
  if (TRACK_PICKER_MODAL) {
    // this means we're in the new/edit race page, so a bunch of assumptions
    // about what is in the DOM are made
    const $TRACK_PICKER_MODAL = $("#track-picker-modal"); // needed to dismiss, sigh
    const $CONFIRM_MODAL = $("#confirm-modal");
    const CONFIRM_MSG = document.getElementById("confirm-msg");
    const INSERT_CONFIRM_BTN = document.getElementById("confirm-track-insert");
    const RACE_SUBMIT_BTN = document.getElementById("race-submit-btn");
    const REMINDER_BTN_TXT  = document.getElementById("reminder-btn-text");
    const TRACK_CARDS = document.querySelectorAll(".card.racetrack");
    const TRACK_EDIT_VIEW_BTNS = document.getElementsByClassName("track-view-edit-btns");
    const TRACK_PICKER_BTN_ROW = document.getElementById("track-picker-btn-row");
    const TRACK_PICKER_CONTROLS = document.getElementsByClassName("track-picker-control");

    const RACE_TRACK_INPUTS = {
      "track_image_url": document.querySelector('input[name="track_image_url"]'),
      "track_svg_url": document.querySelector('input[name="track_svg_url"]'),
      "lap_length": document.querySelector('input[name="lap_length"]')
    }

    var selected_card = null;

    // suppress "normal" HTML actions on the racetrack cards
    for (let el of TRACK_EDIT_VIEW_BTNS){
      el.classList.add("hidden");
    }

    for (let card of TRACK_CARDS){
      card.classList.add("race-clickable");
      card.addEventListener(
        "click",
        function(e){
          e.preventDefault();
          selected_card = card;
          CONFIRM_MSG.innerText = `Insert URLs and lap length from "${card.dataset.title}" into race?`;
          REMINDER_BTN_TXT.innerText = RACE_SUBMIT_BTN.value;
          // non-trivial to dismiss bootstrap modal without jQuery :-(
          $TRACK_PICKER_MODAL.modal("hide");
          $CONFIRM_MODAL.modal("show");
        }
      )
    }

    INSERT_CONFIRM_BTN.addEventListener(
      "click",
      function(){
        if (selected_card){
          RACE_TRACK_INPUTS["track_image_url"].value = selected_card.dataset.trackImageUrl;
          RACE_TRACK_INPUTS["track_svg_url"].value = selected_card.dataset.trackSvgUrl;
          RACE_TRACK_INPUTS["lap_length"].value = selected_card.dataset.lapLength;  
        } else {
          console.error("unexpected: no racetrack selected")
        }
      }
    )

    // setup done, finally reveal the interface
    TRACK_PICKER_BTN_ROW.classList.remove("hidden");
    for (let el of TRACK_PICKER_CONTROLS){
      el.classList.remove("bg-white");
      el.classList.add("alert-info");
    }
  }
})

$(function() {
  const $admin_more_btn = $("#admin-more-btn");
  const HTML_SHOW_EXTRA_NAV = "&bull;&bull;&bull;";
  const HTML_HIDE_EXTRA_NAV = "&bull;&times;&bull;";
  const $admin_management_btns = $("#admin-management-btns");
  if ($admin_more_btn.length && $admin_management_btns.length) {
    $admin_more_btn.data("want-more", "yes");
    $admin_more_btn.on("click", function(e){
      e.preventDefault();
      if ($admin_more_btn.data("want-more") === "yes"){
        $admin_management_btns.slideDown();
        $admin_more_btn.html(HTML_HIDE_EXTRA_NAV);
        $admin_more_btn.data("want-more", "no");
      } else {
        $admin_management_btns.slideUp();
        $admin_more_btn.html(HTML_SHOW_EXTRA_NAV);
        $admin_more_btn.data("want-more", "yes");
      }
    })
    $admin_more_btn.removeClass("hidden");
  }
})
