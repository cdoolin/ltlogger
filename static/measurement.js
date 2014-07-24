// use selfcalling functions to localize variable scope

// think about using a downsampling algorithm like this: https://github.com/sveinn-steinarsson/flot-downsample/

(function () {
    "use strict";
    /*global $, console, webui*/

    var the_future = -1;

    function Measurement(name, attrs) {
        // data stuff
        // name is unique identifying the instrument taking the data.
        this.name = name;
        // ta, tb required properties of attrs
        this.ta = attrs.ta;
        this.tb = attrs.tb;
        // will update later if supplied
        this.label = "";
        this.units = "";
        this.data = [];

        if (this.ta < Measurement.t0 || Measurement.t0 === undefined)
            Measurement.t0 = this.ta;
        if (this.tb > Measurement.t3 || Measurement.t3 === undefined)
            Measurement.t3 = this.tb;

        // load enabled state from cookies
        this.enabled = Boolean($.cookie(this.name));

        //
        // generate html
        //

        // enable element is the minimized measurement name which
        // can be clicked to start plotting.
        this.enable_el = $(templates.enable({name: this.name}));
        $("#enables").append(this.enable_el);
        this.enable_el.click(this.enable.bind(this));

        // plot element is the div containing the flot, ylabel and close button.
        this.plot_el = $(templates.plot({name: this.name}));
        $("#plots").append(this.plot_el);
        $(".close", this.plot_el).click(this.disable.bind(this));

        this.update_label(attrs.label, attrs.units);


        var plotopts = {
            xaxis: {mode: 'time', timezone: "browser"},
            selection: {mode: 'x'},
            series: {
                points: {show: false},
                lines: {show: true}
            }
        };

        var flot_el = $(".flot", this.plot_el);
        this.plot = $.plot(flot_el, this.data, plotopts);

        flot_el.bind("plotselected", function (e, ranges) {
            Measurement.set_lims(ranges.xaxis.from, ranges.xaxis.to);
            this.plot.clearSelection();
        }.bind(this));

        $(window).resize(function () {
            if (this.enabled) {
                this.plot.resize();
                this.plot.setupGrid();
                this.plot.draw();
            }
        }.bind(this));

        if (this.enabled)
            this.enable();
        else this.disable();
    }

    Measurement.prototype.enable = function () {
        this.enable_el.hide();
        this.plot_el.show();

        Measurement.s_active[this.name] = this;
        this.req_lim(Measurement.t0, Measurement.t3);
        webui.call("subscribe", {name: this.name});

        this.enabled =  true;
        $.cookie(this.name, true);
    };

    Measurement.prototype.disable = function () {
        this.plot_el.hide();
        this.enable_el.show();

        if(this.name in Measurement.s_active) {
            delete Measurement.s_active[this.name];
        }
        webui.call("unsubscribe", {name: this.name});

        this.enabled =  false;
        $.cookie(this.name, false);
    };


    Measurement.prototype.req_lim = function (t1, t2) {
        // call this to change time range of this measurement
        // if necessary data isn't cached, get downsampled data from
        // the server.

        var N  = Measurement.number_datas();
        if (this.downsampled === false &&
            t1 >= this.data[0][0] &&
            t2 <= this.data[this.data.length-1][0]) {
            this.data = this.get_local_data(t1, t2);
            this.redraw();

        } else {
            webui.call("get_data", {
                name: this.name,
                ta: t1,
                tb: t2,
                n: N
            });
        }
    };

    Measurement.prototype.got_data = function (data, downsampled) {
        // server gave us new window of data.
        this.data = data;
        this.downsampled = downsampled;
        this.redraw();
    };

    Measurement.prototype.redraw = function () {
        // redraw plot
        $.each(this.plot.getXAxes(), function(_, axis) {
            var opts = axis.options;
            opts.min = Measurement.t1;
            opts.max = Measurement.t2;
        });

        this.plot.setData([this.data]);
        this.plot.setupGrid();
        this.plot.draw();
    };

    Measurement.prototype.get_local_data = function (t1, t2) {
        // return around N datapoints spanning t1 to t2.
        var data = [];
        var i = 0;
        var N = this.data.length;

        // find first data point in window
        while (i < N && this.data[i][0] < t1) {i++;}
        // push one data point before window
        if (i > 0) data.push(this.data[i-1]);
        // push all data in the window
        while (i < N && this.data[i][0] < t2) {
            data.push(this.data[i]);
            i++;
        }
        // push one data point after window
        if (i < N) data.push(this.data[i]);

        return data;
    };

    Measurement.prototype.update_data = function (data) {
        // new datapoint has been measured
        if (data.length < 1)
            return;

        if (this.data.length > 0) {
            if (this.data[this.data.length-1][0] > data[0][0])
                console.log("warning: " + this.name + " data out of order.");
        }

        var t3 = data[data.length-1][0];
        if (t3 > Measurement.t3) {
            Measurement.t3 = t3;
            if (Measurement.active)
                Measurement.t2 = t3;
        }
        if (t3 > this.tb)
            this.tb = t3;

        this.data = this.data.concat(data);

        Measurement.redraw();
    };

    Measurement.prototype.update_label = function (label, units) {
        if (label !== undefined)
            this.label = label;
        if (units !== undefined)
            this.units = units;

        var ylabel = this.name;
        if (this.label.length > 0)
            ylabel = this.label;

        if (this.units.length > 0)
            ylabel += " (" + this.units + ")";

        $(".ylabel", this.plot_el).html(ylabel);
    };


    //
    // Static properties of Measurement
    //

    // all measurements
    Measurement.s = {};
    // and only active ones.
    Measurement.s_active = {};

    Measurement.update_measurements = function (args) {
        $.each(args.measurements, function (name, attrs) {
            if (Measurement.s[name] === undefined) {
                Measurement.s[name] =
                    new Measurement(name, attrs);
            } else {
                if (attrs.ta < Measurement.s[name].ta)
                    Measurement.s[name].ta = attrs.ta;
                if (attrs.tb > Measurement.s[name].tb)
                    Measurement.s[name].tb = attrs.tb;
                if (attrs.label !== undefined || attrs.units !== undefined)
                    Measurement.s[name].update_label(attrs.label, attrs.units);
            }
        });

        if(Measurement.t1 === undefined || Measurement.t2 === undefined)
            Measurement.set_lims();
    };

    Measurement.update_data = function (args) {
        if (Measurement.s[args.name] !== undefined) {
            Measurement.s[args.name].update_data(args.data);
        } else {
            console.log("got data for unknown measurement \"" + args.name + "\"");
        }
    };

    Measurement.number_datas = function () {
        // returns max number of datapoints a plot should have
        // currently 80% of the pixel width of the plot container.
        return Math.round($("#plots").width() * 0.8);
    };

    Measurement.last_draw = 0;
    Measurement.redraw = function () {
        if ($.now() - Measurement.last_draw > 333) {
            $.each(Measurement.s, function (name, m) {
                m.redraw();
            });
            Measurement.last_draw = $.now();
        }
    };
    // t0 (t3) oldest (newest) datapoint. Measurements responsible for updating these
    Measurement.t0 = undefined;
    Measurement.t3 = undefined;
    // plot limits so all plots have same time range
    Measurement.t1 = undefined;
    Measurement.t2 = undefined;
    // wether plots should be updating with data in real time
    Measurement.active = true;


    Measurement.set_lims = function (t1, t2) {
        if (t1 === undefined) t1 = Measurement.t0;
        if (t2 === undefined) t2 = Measurement.t3;
        Measurement.t1 = t1;
        Measurement.t2 = t2;

        if ((Measurement.t3 - t2) < 5000)
            Measurement.active = true;
        else
            Measurement.active = false;

        // if (Measurement.active && Object.keys(Measurement.s_active).length > 0)
        //     setTimeout(Measurement.request_datas, 1000);

        $.each(Measurement.s_active, function (name, m) {
            m.req_lim(t1, t2);
        });
    };

    Measurement.got_data = function (args) {
        if (Measurement.s[args.name] !== undefined)
            Measurement.s[args.name].got_data(args.data, args.downsampled);
    };


    // Measurement.downsample = function (data, n) {
    //     // downsample data to about n datapoints by skipping data
    //     if (data.length < n) return data;
    //
    //     var keep_skip = n / (data.length - n);
    //     var newdata = [];
    //
    //     var j = 1;
    //     // always keep first datapoint.
    //     newdata.push(data[0]);
    //     if (keep_skip > 1) {
    //         // keep more points than skip
    //         var skip = Math.round(keep_skip);
    //         for (j = 1; j < data.length - 1; j++) {
    //             if (j % skip !== 0)
    //                 newdata.push(data[j]);
    //         }
    //     } else {
    //         // skip more points than keep
    //         var keep = Math.round(1 / keep_skip);
    //         for (j = 1; j < data.length - 1; j++) {
    //             if (j % keep === 0)
    //                 newdata.push(data[j]);
    //         }
    //     }
    //     // always keep last datapoint
    //     newdata.push(data[data.length-1]);
    //     return newdata;
    // };

    $(function() {
        $("#reset-time").click(function () {
            Measurement.set_lims(undefined, undefined);
        });
    });

    // make Measurement a global variable
    window.Measurement = Measurement;
}());
