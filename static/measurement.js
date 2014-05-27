// use selfcalling functions to localize variable scope

// think about using a downsampling algorithm like this: https://github.com/sveinn-steinarsson/flot-downsample/

(function () {
    "use strict";
    /*global $, console, webui*/

    function Measurement(name) {
        this.name = name;
//        console.log("initing " + name);
        
        this.checkel = $("#" + this.name + "-check");
        this.checkel.change(this.check_change.bind(this));
        
        this.plotel = $("#" + this.name + "-plot");
        
        this.get_data();
        
        var plotopts = {
            yaxis: {
            }
        };
        this.data = [];
        this.plot = $.plot(this.plotel, this.data, plotopts);
    }
    
    Measurement.prototype.checked = function () {
        return this.checkel.prop("checked");
    };
            
    Measurement.prototype.check_change = function (e) {
        if (this.checked()) {
            this.plotel.show();
        } else {
            this.plotel.hide();
        }
    };
    
    Measurement.prototype.get_data = function () {
        // asks server for data for this measurement
        webui.call("get_data", {name: this.name});
    };
    
    Measurement.prototype.update_data = function (data) {
        $.each(data, function (k, v) {
            this.data.push([k, v]);
        }.bind(this));
        this.plot.setData([this.data]);
        this.plot.setupGrid();
        this.plot.draw();
    };
    
    // make Measurement a global variable
    window.Measurement = Measurement;
}());