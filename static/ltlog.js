// for jslint
/*global $, webui, console, Handlebars, Measurement*/

// initialize Foundation
$(document).foundation();

// wrap in the jquery function so this script is only run
// once the webpage has loaded
var templates = {};
var measurements = {};

$(function () {
    "use strict";
    
    // compile templates
    templates.measurements = Handlebars.compile($("#measurements_template").html());
    templates.plots = Handlebars.compile($("#plots_template").html());
    
    // action for python to complain with
    webui.actions.error = function (args) {
        console.log("error: " + args.text);
    };
    
    webui.actions.update_measurements = function (args) {
        // update measurements called when page loaded to give
        // a list of measurement names being logged
        // expect args.names - list of all types of measurements

        
        $("#measurements").html(templates.measurements({names: args.names}));
        $("#plots").html(templates.plots({names: args.names}));
        
        $.each(args.names, function (i) {
            if (measurements[args.names[i]] === undefined) {
                measurements[args.names[i]] = new Measurement(args.names[i]);
            }
        });
    };
    
    webui.actions.update_data = function (args) {
        if (measurements[args.name] !== undefined) {
            measurements[args.name].update_data(args.data);
        } else {
            console.log("got data for unknown measurement \"" + args.name + "\"");
        }
    };
    
//    webui.onopen = function () {
//        webui.call("get_measurements", {});
//    };

    
    
});


