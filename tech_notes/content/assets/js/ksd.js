// KeyshapeDiagram.js
// adds button-driven step/play control to SVG diagrams that have named
// markers on the timeline, using the KeyShape API.

if (! window.KsDiagram) {
  (function( KsDiagram, undefined ) {

    let init_seq_id = 0;
    
    const INIT_SEQ_PERIOD = 500, // pause between init retries
          KSD = "ksd",
          PREFIX = KSD + "-", // used for CSS classes
          KSD_RESET = "reset";
          KSD_RUN = "run";
          KSD_STEP = "step";
          KSD_STOP = "stop",  // but these used for classes *and* enums
          KSD_STOPPING = "stopping";
          TIMELINE_MARKER_END = "end", // override with data-ksd-end-marker
          ATTRIB_BTN_LABELS = "data-ksd-button-labels",
          ATTRIB_END_MARKER = "data-ksd-end-marker",
          ATTRIB_KSD_ID = "data-ksd-id", // indicates diagram is init'd
          ATTRIB_LAYOUT = "data-ksd-layout",
          ATTRIB_KSD_REJECT = "data-ksd-reject", // mark bad diagrams
          DEFAULT_LAYOUT = "bdc", // b=buttons d=diagram c=captions
          LABELS = {}; 

    // LABELS are the default (English) values displayed to user:
    // override with data-ksd-button-labels for custom or i18n values.
    LABELS[KSD_RESET]    = 'reset';
    LABELS[KSD_RUN]      = 'run';
    LABELS[KSD_STEP]     = 'step';
    LABELS[KSD_STOP]     = 'stop';
    LABELS[KSD_STOPPING] = 'stopping';
    
    const CLASS_KSD       = KSD,
          CLASS_BTN_BLOCK = PREFIX + "btn-block",
          CLASS_CAPTION   = PREFIX + "caption",
          CLASS_CAPTIONS  = PREFIX + "captions",
          CLASS_DISABLED  = PREFIX + "disabled",
          CLASS_HIDDEN    = PREFIX + "hidden",
          CLASS_NO_JS     = PREFIX + "no-js",
          CLASS_STOPPING  = PREFIX + "stopping";

    const BTN_EVENT_HANDLERS = {}
    BTN_EVENT_HANDLERS[KSD_STEP] = function step_event_handler(diagram){
      if (!this.classList.contains(CLASS_DISABLED)) {
        const ksd = diagram._ksd;
        ksd.is_run_mode = ksd.is_stopping = false;
        KsDiagram.set_button_text(ksd.button_stop, ksd.labels[KSD_STOP], true);
        KsDiagram.disable_buttons([ksd.button_step, ksd.button_run]);
        KsDiagram.enable_buttons([ksd.button_stop]);
        KsDiagram.run_step(diagram);
      }
    };
    BTN_EVENT_HANDLERS[KSD_RUN] = function step_event_handler(diagram){
      if (!this.classList.contains(CLASS_DISABLED)) {
        const ksd = diagram._ksd;
        ksd.is_stopping = false;
        ksd.is_run_mode = true;
        KsDiagram.set_button_text(ksd.button_stop, ksd.labels[KSD_STOP], true);
        KsDiagram.disable_buttons([ksd.button_step, ksd.button_run]);
        KsDiagram.enable_buttons([ksd.button_stop]);
        KsDiagram.run_step(diagram);
      }
    };
    BTN_EVENT_HANDLERS[KSD_STOP] = function step_event_handler(diagram){
      if (!this.classList.contains(CLASS_DISABLED)) {
        if (this.textContent === diagram._ksd.labels[KSD_RESET]) {
          KsDiagram.reset_animation(diagram._ksd.id);
        } else {
          const ksd = diagram._ksd;
          ksd.button_stop.classList.add(CLASS_STOPPING);
          KsDiagram.set_button_text(ksd.button_stop, ksd.labels[KSD_STOPPING]);
          ksd.is_stopping = true;
        }
      }
    }
    
    //---  Bindings to animation API: separated out here as a kindness, just
    //---  in case you want to have a go at extending these beyond Keyshape

    function get_timeline(diagram) {
      return diagram.timelines()[0]; // primary timeline
    }
    function get_timeline_markers(diagram) { // names, but in chrono order
      let m = diagram.timelines()[0].l.markers;
      return Object.keys(m).sort(function(a, b) {return m[a] - m[b]});
    }
    function set_timeline_range(diagram, from, to) {
      diagram._ksd.timeline.range(from, to);
    }
    function set_animation_finish_handler(diagram, func) {
      diagram._ksd.timeline.onfinish = func;
    }
    function play_animation(diagram) {
      diagram.globalPlay();
      diagram._ksd.timeline.play(); // see set_timeline_range() above
    }
    function pause_animation(diagram) {
      diagram._ksd.timeline.pause(0);
    }

    //---  end bindings ^

    function create_button(diagram, btn_type, container){
      let btn = document.createElement("button");
      btn.id = PREFIX + btn_type + "-" + diagram._ksd.id;
      btn.innerText=diagram._ksd.labels[btn_type];
      btn.classList.add(PREFIX + btn_type);
      btn.addEventListener("click", function(){
        BTN_EVENT_HANDLERS[btn_type].call(btn, diagram)
      }, false);
      container.append(btn);
      return btn;
    }

    function create_button_set(diagram){
      let btn_container = document.createElement("div");
      btn_container.id = CLASS_BTN_BLOCK + "-" + diagram._ksd.id;
      btn_container.classList.add(KSD, CLASS_BTN_BLOCK);
      diagram._ksd.button_step = create_button(diagram, KSD_STEP, btn_container);
      diagram._ksd.button_run = create_button(diagram, KSD_RUN, btn_container);
      diagram._ksd.button_stop = create_button(diagram, KSD_STOP, btn_container);
      return btn_container;
    }

    function has_initial_step_name(diagram) {
      return (diagram && diagram._ksd.timeline
        && diagram._ksd.markers.length > 1
        && diagram._ksd.timeline.marker(diagram._ksd.markers[0]) === 0)
    }

    function make_caption_id(diagram, cid) { // yes, it's long
      return PREFIX + CLASS_CAPTION + "-" + diagram._ksd.id + "-" + cid;
    }

    function init_diagram(id, container, diagram) {
      // all the KeyshapeDiagram properties, etc., are stored in ._ksd:
      diagram._ksd = {
        id: id,
        timeline: get_timeline(diagram),
        markers: get_timeline_markers(diagram),
        labels: {},
        captions: [],
        end_marker: container.getAttribute(ATTRIB_END_MARKER) || TIMELINE_MARKER_END,
        div_diagram: container,
        div_buttons: null, // set below, once labels are ready
        div_captions: document.createElement("div") // populated below
      };
      diagram._ksd.div_captions.classList.add(KSD);
      
      let custom_labels = {};
      let custom_labels_str = container.getAttribute(ATTRIB_BTN_LABELS);
      if (custom_labels_str) { // may be of form: "stop:Halt, reset: Again"
        if (custom_labels_str.indexOf("{") === -1) { // not looking like JSON
          let settings = custom_labels_str.split(/\s*,\s*/);
          for (let i=0; i<settings.length; i++) {
            let pair = settings[i].split(/\s*:\s*/);
            if (pair.length === 2) {
              custom_labels[pair[0].toLowerCase()] = pair[1];
            } else {
              console.log("KsDiagram: [" + id + "] warning: label data should be \"name:value\"");
            }
          }
        } else {
          try {
            custom_labels = JSON.parse(custom_labels);
          } catch (e) {
            console.log("KsDiagram: [" + id + "] label data is bad JSON, ignored");
            custom_labels = {}
          }
        }
      }
      Object.keys(LABELS).forEach(function(key) {
        diagram._ksd.labels[key] = custom_labels[key] || LABELS[key];
      });

      diagram._ksd.div_buttons = create_button_set(diagram);

      let caption_cntr = container.parentElement.getElementsByClassName(CLASS_CAPTIONS);
      if (caption_cntr.length === 0) {
        console.log("KsDiagram: [" + id + "] no captions");
      } else {
        if (caption_cntr.length > 1) {
          console.log("KsDiagram: [" + id + "] warning: expected only one class=\""
            + CLASS_CAPTIONS + "\" element, found " + caption_cntr.length);
        }
        caption_cntr = caption_cntr[0];
        caption_cntr.remove(); // replace with a constructed duplicate to...
        caption_cntr.removeAttribute("id"); // ...avoid possible id collisions
        caption_cntr.classList.remove(CLASS_CAPTIONS);
        let new_caption_cntr = document.createElement(caption_cntr.tagName);
        new_caption_cntr.classList.add(KSD, CLASS_CAPTIONS);
        new_caption_cntr.id = CLASS_CAPTIONS + "-" + id;
        let captions = [];
        for (let i=0; i<caption_cntr.children.length; i++) {
          captions.push(caption_cntr.children[i]);
        }
        let start_value = caption_cntr.getAttribute("start") || 1;
        for (let i=0; i<captions.length; i++) {
          let auto_id = "_" + i;
          if (i >= diagram._ksd.markers.length) {
            console.log("KsDiagram: [" + diagram._ksd.id + "] has more captions than markers");
          } else {
            auto_id = diagram._ksd.markers[i];
          }
          let c = captions[i];
          let cid = c.getAttribute(ATTRIB_KSD_ID) || c.id || auto_id;
          c.removeAttribute("id");
          let new_c = c.cloneNode(true);
          new_c.id = make_caption_id(diagram, cid);
          new_caption_cntr.append(new_c);
          new_c.classList.add(KSD, CLASS_CAPTION, CLASS_HIDDEN);
          new_c.setAttribute("value", i + start_value); // for <ol>
          diagram._ksd.captions.push(new_c);
          c.remove();
        }
        diagram._ksd.div_captions.append(new_caption_cntr);
      } // original caption_cntr garbage collected

      // layout: e.g., "b-d-c" where b=buttons, d=diagram, c=captions
      let items = {
        "b": diagram._ksd.div_buttons,
        "c": diagram._ksd.div_captions
      }
      let layout_str = container.getAttribute(ATTRIB_LAYOUT);
      if (layout_str) {
        layout_str = layout_str.toLowerCase().replace(/[^bdc]/g, '');
        if (layout_str.split("").sort().join("") != "bcd") { // missing any?
          layout_str = DEFAULT_LAYOUT
        }
      } else {
        layout_str = DEFAULT_LAYOUT
      }
      let layout = layout_str.split(""); // layout is: [top, middle, bottom]
      let is_before = true;
      let ref = container;
      for (let i=0; i<layout.length; i++) {
        if (layout[i] === "d") {
          is_before = false;
        } else {
          if (is_before) {
            ref.before(items[layout[i]]);
          } else {
            ref.after(items[layout[i]]);
            ref = items[layout[i]];
          }
        }
      }

      set_animation_finish_handler(diagram, function(){
        let ksd = diagram._ksd; // keyshape data
        if (ksd.is_stopping || ! ksd.is_run_mode) {
          ksd.is_stopping = ksd.is_run_mode = false;
          KsDiagram.set_button_text(ksd.button_stop, ksd.labels[KSD_RESET]);
          if (ksd.current_marker_index != undefined) { // is not last step
            KsDiagram.enable_buttons([ksd.button_step, ksd.button_run]);
          }
        } else if (ksd.current_marker_index != undefined) {
          KsDiagram.run_step(diagram); // auto run the next step
        } else { // end of run
          ksd.is_stopping = ksd.is_run_mode = false;
          KsDiagram.set_button_text(ksd.button_stop, ksd.labels[KSD_RESET]);
        }
        KsDiagram.enable_buttons([ksd.button_stop]);
      });
    }

    function scan_for_diagrams(scope){ // returns true if everything init'd
      if (scope === undefined) {
        scope = document;
      }
      let qty_svg_scripts = 0;
      let ksd_elements = scope.getElementsByClassName(KSD);
      let ksd_objects = [];
      for (let i=0; i < ksd_elements.length; i++) {
        let el = ksd_elements[i];
        if (el.getAttribute(ATTRIB_KSD_ID) || el.getAttribute(ATTRIB_KSD_REJECT)) {
          continue; // already handled this one
        }
        let tag = el.tagName.toUpperCase();
        if (tag === "OBJECT"){
          ksd_objects.push(el);
        } else if (tag === "SVG" && window.KeyshapeJS) {
          window.KeyshapeJS.globalPause();
          if (el.children.length > 0 &&
            el.children[el.children.length-1].tagName.toUpperCase() === "SCRIPT") {
            qty_svg_scripts += 1;
            if (qty_svg_scripts > 1) { // if there's > 1, we have a problem
              // animation(s) probably failing so: remove element, show warning
              // TODO: is there a less catastrophic save?
              console.log("KsDiagram: WARNING: inline SVGs contain duplicate KeyshapeJS scripts");
              console.log("KsDiagram: ...use _one_ external script (or embed in <objects>)");
              let warning = document.createElement("code");
              warning.textContent = "KsDiagram: SVG removed (duplicate <script>)";
              el.replaceWith(warning);
              continue;
            }
          }
          ksd_objects.push(el);
        } else { // abandon hope on this one
          el.setAttribute(ATTRIB_KSD_REJECT, "1");
        }
      }
      let is_init_complete = true;
      for (let i=0; i < ksd_objects.length; i++) {
        if (ksd_objects[i].contentDocument
          && ksd_objects[i].contentDocument.defaultView.KeyshapeJS) {
            KsDiagram.add_diagram(ksd_objects[i]);
        } else if (window.KeyshapeJS) {
          KsDiagram.add_diagram(ksd_objects[i]);
        } else {
          is_init_complete = false;
        }
      }
      return is_init_complete;
    }

    // KsDiagram's public properties and methods:
      
    KsDiagram.diagram_ids = [];
    KsDiagram.diagrams = {};  // diagrams keyed by ID

    KsDiagram.enable_buttons = function(btns){
      btns.forEach(function(b){
        b.classList.remove(CLASS_DISABLED);
        b.classList.remove(CLASS_STOPPING);
      });
    }
    KsDiagram.disable_buttons = function(btns){
      btns.forEach(function(b){
        b.classList.add(CLASS_DISABLED);
      });
    }
    KsDiagram.set_button_text = function(btn, text, is_unstopping) {
      if (is_unstopping) { // is_unstopping is special: CSS class is transient
        btn.classList.remove(CLASS_STOPPING);
      };
      btn.textContent = text;
    }

    KsDiagram.show_caption = function(anim_id, caption_id) {
      let d = KsDiagram.diagrams[anim_id];
      let full_caption_id = make_caption_id(d, caption_id);
      for (let i=0; i<d._ksd.captions.length; i++) {
        let c = d._ksd.captions[i];
        if (c.getAttribute("id") === full_caption_id) {
          c.classList.remove(CLASS_HIDDEN);
        } else {
          c.classList.add(CLASS_HIDDEN);
        }
      }
    }

    KsDiagram.reset_animation = function(anim_id) {
      let d = KsDiagram.diagrams[anim_id];
      pause_animation(d);
      d._ksd.current_marker_index = undefined;
      d._ksd.is_run_mode = d._ksd.is_stopping = false;
      if (has_initial_step_name(d)) {
        KsDiagram.show_caption(d._ksd.id, d._ksd.markers[0]);
      }
      KsDiagram.set_button_text(d._ksd.button_stop, d._ksd.labels[KSD_STOP], true);
      KsDiagram.enable_buttons([d._ksd.button_step, d._ksd.button_run]);
      KsDiagram.disable_buttons([d._ksd.button_stop]);
    }

    KsDiagram.run_step = function(diagram) {
      let ksd = diagram._ksd;
      if (ksd.timeline == undefined) {
        console.log("KsDiagram:  [" + ksd.id + "]no timeline found: cannot run animation");
        return;
      }
      if (ksd.current_marker_index == undefined) {
        if (has_initial_step_name(diagram)) {
          ksd.current_marker_index = 1;  // first marker is start
        } else {
          ksd.current_marker_index = 0;
        }
      } else {
        ksd.current_marker_index += 1;
      }
      KsDiagram.show_caption(ksd.id, ksd.markers[ksd.current_marker_index]);
      if (ksd._current_marker_index === 0){ // start of timeline
        set_timeline_range(diagram, 0, ksd.markers[ksd.current_marker_index]);
      } else if (ksd.markers[ksd.current_marker_index] === ksd.end_marker) {
        set_timeline_range(diagram, ksd.markers[ksd.current_marker_index-1], ksd.markers[ksd.current_marker_index]);
        ksd.current_marker_index = undefined;
      } else if (ksd.current_marker_index >= ksd.markers.length - 1) {
        ksd.current_marker_index = undefined; // end of timeline
      } else { // section of timeline
        set_timeline_range(diagram, ksd.markers[ksd.current_marker_index-1], ksd.markers[ksd.current_marker_index]);
      }
      if (ksd.current_marker_index >= ksd.markers.length - 1) {
        ksd.current_marker_index = undefined;
      }
      play_animation(diagram);
    }

    // Hide no-JavaScript content:
    // automatically run on load: probably never need to call this again
    // *unless* you add diagrams to the document _after_ this JS has loaded
    KsDiagram.hide_no_js_elements = function(){
      let elements_no_js = document.getElementsByClassName(CLASS_NO_JS);
      for (let i=0; i<elements_no_js.length; i++) {
        elements_no_js[i].classList.add(CLASS_HIDDEN);
      }
    }

    KsDiagram.add_diagram = function(container){
      let diagram = null;
      if (container.contentDocument && container.contentDocument.defaultView.KeyshapeJS) {
        diagram = container.contentDocument.defaultView.KeyshapeJS;
      } else if (container.tagName.toUpperCase() === 'SVG' && window.KeyshapeJS) {
        diagram = window.KeyshapeJS;
      } else {
        console.log("KsDiagram: can't implement diagram — needs object or svg");
        container.setAttribute(ATTRIB_KSD_REJECT, "1"); // mark as rejected
        return;
      }
      let id = container.getAttribute("id");
      let diagram_count = KsDiagram.diagram_ids.length;
      if (id == undefined) {
        id = "" + diagram_count;
      } else if (KsDiagram.diagrams[id] != undefined) {
        id = id + "" + diagram_count;
      }
      KsDiagram.diagram_ids.push(id);
      KsDiagram.diagrams[id] = diagram;
      container.setAttribute(ATTRIB_KSD_ID, id);
      console.log("KsDiagram: [" + id + "] added diagram");
      init_diagram(id, container, diagram);
      KsDiagram.reset_animation(id);
      return id;
    }

    // init() finds all the elements of tag type <object> and class "ksd".
    // Repeats on an interval every ½ second until all the diagrams
    // found are initialised. Delay is because Keyshape's own setup needs to
    // complete before ksd can manipulate it. This is a little rustic but...
    // it's only for setup and gets the job done. If diagrams are added to the
    // DOM later, explictly call init() to kick it off again.

    KsDiagram.init = function() {
      if (init_seq_id === 0) {
        console.log("KsDiagram: Initialising...");
        KsDiagram.hide_no_js_elements();
        if (! scan_for_diagrams()) { // if not immediate success...
          init_seq_id = setInterval(function () { //...try repeat
            if (scan_for_diagrams()) {
              clearInterval(init_seq_id);
              init_seq_id = 0;
            }
          }, INIT_SEQ_PERIOD); // until all candidates are init'd
        }
      }
    }
    
    // all set up: auto-detect and init diagrams, and hide no-JS fallback
    KsDiagram.init();

  }( window.KsDiagram = window.KsDiagram || {} ));
}
