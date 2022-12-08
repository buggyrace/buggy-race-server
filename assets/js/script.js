// App initialization code goes here

// if both these elements are present on the page, do bulk-registration:
const USER_REGISTER_FORM_ID = "registerForm";
const USER_REGISTER_CSV_ID = "userdata";

function bulk_registration_by_ajax(bulk_register_form){
  const BULK_REGISTER_URL = "/admin/bulk-register/json";
  const USER_REGISTER_AUTH_ID = "authorisation_code";
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
  let csv_raw_rows = bulk_register_form[USER_REGISTER_CSV_ID].value.split("\n");
  let csv_rows_as_dicts = [];
  let header_row = [];
  console.log("number of rows: " + csv_raw_rows.length);
  let err_msg = null;
  for (let i=0; i<csv_raw_rows.length; i++) {
    let row = csv_raw_rows[i].split(/\s*,\s*/);
    if (i === 0) {
      if (row.length < 2 || row[0] != "username") {
        err_msg = "Missing header row: the first line should be something like 'username,password,...";
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
  if (err_msg) {
    update_status(err_msg, "alert-danger");
    $(bulk_register_form).slideDown("slow");
  } else {
    register_by_ajax(csv_rows_as_dicts, 0);
  }
}

$( document ).ready(function() {
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
      $json_modal_title.text(pretty_username + "’s buggy JSON");
      $json_payload.text(USER_BUGGY_JSON[username]);
      $json_modal.modal('show')
    };
    $json_buttons.addClass("btn btn-outline-secondary btn-sm");
    $json_buttons.on("click", display_json);
  }

  // for bulk registration, try to intervene with JavaScript to send
  // registration requests one by one with Ajax, because the bulk
  // registration is frustratingly timing out (sigh: cookiecutter+SqlAlchemy)
  let bulk_register_form = document.getElementById(USER_REGISTER_FORM_ID);
  if (bulk_register_form && document.getElementById(USER_REGISTER_CSV_ID)){
    bulk_register_form.addEventListener('submit', function(e){
      e.preventDefault();
      $(bulk_register_form).slideUp(
        "slow",
        function(){bulk_registration_by_ajax(bulk_register_form)}
      );
    });
  }

  const CSS_BTN_COLUMN_SHOWN = "btn-dark";
  const CSS_BTN_COLUMN_HIDDEN = "btn-outline-secondary";
  const ALL_COLUMNS = "all-columns";

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
      console.log(this.dataset.column + " = " + want_to_hide, want_to_hide);
      if ($(this)[0].dataset.column != ALL_COLUMNS) {
        show_or_hide_col_by_button(
          $(this)[0],
          want_to_hide
        );
      }
    });
    is_init_done = true; // now show/hide uses slow fade, so user notices
  }
});
