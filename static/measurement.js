// use selfcalling functions to localize variable scope

// think about using a downsampling algorithm like this: https://github.com/sveinn-steinarsson/flot-downsample/

(function () {
    "use strict";
    /*global $, console, webui*/

    function Measurement(name) {
        // name is unique identifying the instrument taking the data.
        this.name = name;
        
        // enable element is the minimized measurement name which
        // can be clicked to start plotting.
        this.enable_el = $("#" + this.name + "-enable");
        this.enable_el.click(this.enable.bind(this));
        
        // plot element is the div containing the flot, ylabel and close button.
        this.plot_el = $("#" + this.name + "-plot");
        $(".close", this.plot_el).click(this.disable.bind(this));
        $(".ylabel", this.plot_el).html(this.name);
        
        this.get_data();
        
        var plotopts = {};
        this.data = [];
        this.plot = $.plot($(".flot", this.plot_el), this.data, plotopts);
        
        this.plot_el.hide();
//        this.plot_el.disable();
        
        $(window).resize(function () {
            if (this.plot_el.is(":visible")) {
                this.plot.resize();
                this.plot.setupGrid();
                this.plot.draw();
            }
        }.bind(this));
    }
    
    Measurement.prototype.enable = function () {
        this.enable_el.hide();
        this.plot_el.show();
    };
    
    Measurement.prototype.disable = function () {
        this.plot_el.hide();
        this.enable_el.show();
    };
    
    Measurement.prototype.get_data = function () {
        // asks server for data for this measurement
        webui.call("get_data", {name: this.name});
    };
    
    Measurement.prototype.update_data = function (data) {
        $.each(data, function (k, v) {
            this.data.push([k, v]);
        }.bind(this));
        this.plot_el.show();
        this.plot.setData([this.data]);
        this.plot.setupGrid();
        this.plot.draw();
        this.plot_el.hide();
    };
    
    // make Measurement a global variable
    window.Measurement = Measurement;
}());
