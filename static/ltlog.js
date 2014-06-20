// for jslint
/*global $, webui, console, Handlebars, Measurement*/

// wrap in the jquery function so this script is only run
// once the webpage has loaded
//
templates = {};
//measurements = {};

$.cookie.json = true;

$(function () {
    "use strict";

    templates.enable = Handlebars.compile($("#enable_template").html());
    templates.plot = Handlebars.compile($("#plot_template").html());

    // action for python to complain with
    webui.actions.error = function (args) {
        console.log("error: " + args.text);
    };

    webui.actions.update_measurements = Measurement.update_measurements;
    webui.actions.update_data = Measurement.update_data;
    webui.actions.update_datas = Measurement.update_datas;
    webui.actions.got_data = Measurement.got_data;
});
