﻿/*
 * Copyright 2010 ITA Software, Inc.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

// Base for data manipulation
// TODO: A global variable? I hate you.
base = 0;

// Generate ticks, passed as an option to Flot
function tickGenerator(range) {
    bases = ['', 'K', 'M', 'G', 'T'];
    for(interval = 0; interval < bases.length; interval++) {
        if(range.max / (Math.pow(base, interval)) <= base) {
            break;
        }
    }

    final_base = Math.pow(base, interval);

    var noTicks = 0.3 * Math.sqrt($(".graph").height());
    
    var delta = ((range.max - range.min) / final_base) / noTicks,
        size, generator, unit, formatter, i, magn, norm;

    // pretty rounding of base-10 numbers
    var dec = -Math.floor(Math.log(delta) / Math.LN10);

    magn = Math.pow(10, -dec);
    norm = delta / magn; // norm is between 1.0 and 10.0
    
    if (norm < 1.5)
        size = 1;
    else if (norm < 3) {
        size = 2;
        // special case for 2.5, requires an extra decimal
        if (norm > 2.25) {
            size = 2.5;
            ++dec;
        }
    }
    else if (norm < 7.5)
        size = 5;
    else
        size = 10;

    size *= magn;
    size *= final_base;

    var ticks = [];
    x = 0;
    for(tick = range.min; tick < range.max+size; tick+=size) {
        ticks[x++] = tick;
    }
    return ticks;
}

// Format ticks for displayed, passed as option to Flot
function tickFormatter(val, axis) {
    bases = ['', 'K', 'M', 'G', 'T'];
    for(interval = 0; interval < bases.length; interval++) {
        if(axis.max / (Math.pow(base, interval)) <= base) {
            break;
        }
    }

    //return val + '--' + (val / (Math.pow(base, interval))).toFixed(axis.tickDecimals) + bases[interval];
    return (val / (Math.pow(base, interval))).toFixed(axis.tickDecimals) + bases[interval];
}

// Format a label, passed to Flot
function labelFormatter(label, series) {
    return label.replace(/_/g, " ");
}

// Takes the raw data and sets up required Flot formatting options
function formatGraph(element, data) {
    base = data[2];

    data[0]['yaxis']['ticks'] = tickGenerator;
    data[0]['yaxis']['tickFormatter'] = tickFormatter;

    // TODO: Cleanup legend and axis label creation
    data[0]['legend'] = {}
    data[0]['legend']['container'] = $(element).next(".legend");
    data[0]['legend']['labelFormatter'] = labelFormatter;
    return data;
}

// Execute setup code when page loads
$(document).ready(function() {
    // Bind the graph time range selection buttons
    $(".options ul li").click(function() {
        graph = $(this).closest(".graph_container").find('.graph');
        time = new Date();
        end = parseInt(time.getTime() / 1000);

        $(this).closest('.graph_container').find('.options .selected').removeClass('selected');
        $(this).addClass('selected');

        // Depending on which button is hit, change the behavior
        // TODO: Look at possibilities at cleaning this up

        if($(this).hasClass('zoom')) {
            return;
        }

        $(this).closest('.graph_container').find('.zoom').css('visibility', 'hidden');

        if($(this).hasClass('reset')) {
            graph.addClass('ajax');
            autoFetchData();
            return;
        } else if($(this).hasClass('day')) {
            start = parseInt(end - 60 * 60 * 24);
        } else if($(this).hasClass('week')) {
            start = parseInt(end - 60 * 60 * 24 * 7);
        } else if($(this).hasClass('month')) {
            start = parseInt(end - 60 * 60 * 24 * 30);
        } else if($(this).hasClass('year')) {
            start = parseInt(end - 60 * 60 * 24 * 365);
        }

        graph.removeClass('ajax');

        serviceData = $(graph).data();
        $.getJSON('/railroad/parserrd/' + serviceData['host'] + '/' + serviceData['service'] + '/' + start + '/' + end + '/' + serviceData['res'], function(data) {
            data = formatGraph(graph, data);
            $.plot($(graph), data[1], data[0]);
        });
       
    });

    // Loop over the things to be graphed and produce graphs for each
    $(".graph").each(function(index, element) {

        // Store the graph data for usage later
        path = $(element).html();
        splitPath = path.split("/");
        $(element).data('host', splitPath[0]);
        $(element).data('service', splitPath[1]);
        $(element).data('res', splitPath[4]);

        $.getJSON('/railroad/parserrd/' + path, function(data) {
            $(element).html("");
            data = formatGraph(element, data);
            $.plot($(element), data[1], data[0]);
            if(data[0]['yaxis']['label']) {
                $(element).before("<div class='ylabel'>" + data[0]['yaxis']['label'] + "</div>");
            }
        });

        // Allow for zooming
        $(element).bind("plotselected", function (event, ranges) {
            serviceData = $(element).data();
            $.getJSON('/railroad/parserrd/' + serviceData['host'] + '/' + serviceData['service'] + '/' + parseInt(ranges.xaxis.from/1000) + '/' + parseInt(ranges.xaxis.to/1000) + '/' + serviceData['res'], function(data) {
                data = formatGraph(element, data);
                $(element).removeClass('ajax');
                $.plot($(element), data[1], data[0]);
                zoom = $(element).closest('.graph_container').find('.zoom');
                selected = $(element).closest('.graph_container').find('.selected');
                selected.removeClass('selected');
                zoom.css('visibility', 'visible');
                zoom.addClass('selected');
            });
            
        });

    });


    function autoFetchData() {
        $(".graph.ajax").each(function(index, element) {
            serviceData = $(element).data();
            time = new Date();
            end = parseInt(time.getTime() / 1000);
            start = parseInt(end - 60 * 60 * 24);
            $.getJSON('/railroad/parserrd/' + serviceData['host'] + '/' + serviceData['service'] + '/' + start + '/' + end + '/' + serviceData['res'], function(data) {
                data = formatGraph(element, data);
                $.plot($(element), data[1], data[0]);
            });
            $(element).closest('.graph_container').find('.update').html("updated: " + time.toString());
            $(element).closest('.graph_container').find('.update').css('visibility', 'visible');
        });
        // TODO: Change both timeouts before deploying!
        setTimeout(autoFetchData, 10 * 1000);
    }
    setTimeout(autoFetchData, 1 * 1000);
});

