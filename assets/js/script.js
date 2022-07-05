// App initialization code goes here

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
});
