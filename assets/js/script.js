// App initialization code goes here

// if both these elements are present on the page, do bulk-registration:
const USER_REGISTER_FORM_ID = "registerForm";
const USER_REGISTER_CSV_ID = "userdata";

function bulk_registration_by_ajax(bulk_register_form){
  const USER_REGISTER_AUTH_ID = "authorisation_code";
  const USER_REGISTER_IS_JSON_ID = "is_json";
  const USER_REGISTER_CSRF_ID = "csrf_token";
  const USER_REGISTER_PROGRESS_ID = "registration-progress";
  const USER_REGISTER_STATUS_ID = "registration-status";
  
  const $reg_container = $("#"+USER_REGISTER_PROGRESS_ID);
  const $progress_list = $reg_container.find("ul");
  const $status_div = $("#"+USER_REGISTER_STATUS_ID);
  const authcode = bulk_register_form[USER_REGISTER_AUTH_ID].value;
  const csrf_token = bulk_register_form[USER_REGISTER_CSRF_ID].value;

  let qty_reg_ok = 0;
  let qty_reg_fail = 0;
  let qty_reg_total = 0;

  function get_reg_progress_str() {
    if (qty_reg_total === 0) {
      return "No CSV lines to process";
    } else {
      let running_total = qty_reg_ok + qty_reg_fail;
      let percent = Math.round(100 * running_total/qty_reg_total);
      return (
        percent + "% " + running_total
        + " (OK: " + qty_reg_ok  + ", fail: " + qty_reg_fail + ") of "
        + qty_reg_total
      );
    }
  }

  function register_next(csv_rows_as_dicts, reg_index){
    reg_index += 1;
    if (reg_index < qty_reg_total) {
      register_by_ajax(csv_rows_as_dicts, reg_index);
    } else {
      $status_div.text(
        get_reg_progress_str(reg_index, qty_reg_total)
        + " FINISHED"
      );
      console.log("FIXME NO MORE CSV ROWS TO INSERT: update the 'don't interrupt' message")
    }

  }

  function register_by_ajax(csv_rows_as_dicts, reg_index){
    qty_reg_total = csv_rows_as_dicts.length;
    $status_div.text(get_reg_progress_str());
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
    request_data[USER_REGISTER_IS_JSON_ID] = 1
    request_data[USER_REGISTER_CSV_ID] = userdata_as_csv;
    let new_status = "danger";
    $.post(
        "/admin/bulk-register/", request_data
    ).done(function(data, textStatus, errorThrown) {
      if (data && data.status === "OK") {
        new_status = "ok";
      }
    })
    .always(function() {
      $user_element.removeClass("list-group-item-warning");
      if (new_status === "ok") {
        qty_reg_ok += 1;
        $user_element.addClass("list-group-item-success");
        $user_status.text("OK");
      } else {
        qty_reg_fail += 1;
        $user_element.addClass("list-group-item-danger");
        $user_status.text("fail");
      }
      register_next(csv_rows_as_dicts, reg_index);
    })
  }

  $reg_container.slideDown("slow");
  let csv_raw_rows = bulk_register_form[USER_REGISTER_CSV_ID].value.split("\n");
  let csv_rows_as_dicts = [];
  let header_row = [];
  console.log("number of rows: " + csv_raw_rows.length);
  for (let i=0; i<csv_raw_rows.length; i++) {
    let row = csv_raw_rows[i].split(/\s*,\s*/);
    if (i === 0) {
      if (row.length < 2 || row[0] != "username") {
        $status_div.text("Cannot process CSV: missing header row?");
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
  if (csv_rows_as_dicts.length === 0) {
    $status_div.text("Cannot process CSV: only found a header row, no data");
  } else {
    console.log(csv_rows_as_dicts);
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
});
