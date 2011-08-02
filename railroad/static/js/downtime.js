$(document).ready(function() {
    var downtime = JSON.parse($('#downtimegraph').text());
    $('#downtimegraph').text('');

    var flot_data = []
    var yaxis_bits = [];
    var min_date = downtime[0].start_time;
    var max_date = downtime[0].end_time;

    for (var i=0; i<downtime.length; i++) {
        var dt = downtime[i]
        flot_data.push({
            'label': dt.expr,
            'data': [
                new Date(dt.start_time * 1000),
                dt.key,
                new Date(dt.end_time * 1000),
                dt.expr,
            ],
        });
        yaxis_bits.push([i+1, dt.expr]);
        if (dt.start_time < min_date) {
            min_date = dt.start_time;
        }
        if (dt.max_time > max_date) {
            max_date = dt.end_time;
        }
    }
    min_date = new Date(min_date * 1000);
    max_date = new Date(max_date * 1000);

    if (min_date < new Date()) {
        min_date = new Date();
    }

    var flot_options = {
        "series": {
            "gantt": {
                "active": true,
                "show": true,
                "barHeight": 5,
            },
        },
        "xaxis": {
            "min": min_date,
            "max": max_date,
            "mode": "time",
        },
        "yaxis": {
            "min": 0.5,
            "max": yaxis_bits.length+0.5,
            "ticks": yaxis_bits,
        },
    }

    $.plot($('#downtimegraph'), flot_data, flot_options);
});
