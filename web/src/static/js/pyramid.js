/*
 *  Project: pyramid.js
 *  Description: jQuery plugin that allows you to create pyramids.
 *  Author: @ahmontero
 *  License: MIT license
 *
 *  jQuery lightweight plugin boilerplate
 *  Original author: @ajpiano
 *  Further changes, comments: @addyosmani
 *  Licensed under the MIT license
*/

// the semi-colon before the function invocation is a safety
// net against concatenated scripts and/or other plugins
// that are not closed properly.
;(function ( $, window, document, undefined ) {

    // undefined is used here as the undefined global
    // variable in ECMAScript 3 and is mutable (i.e. it can
    // be changed by someone else). undefined isn't really
    // being passed in so we can ensure that its value is
    // truly undefined. In ES5, undefined can no longer be
    // modified.

    // window and document are passed through as local
    // variables rather than as globals, because this (slightly)
    // quickens the resolution process and can be more
    // efficiently minified (especially when both are
    // regularly referenced in your plugin).

    // Create the defaults once
    var pluginName = 'Pyramid',
        defaults = {
            base: 400,
            top: 0,
            height: 400,
            slices: 4,
            slice_separation: 0.15,
            colours: ['red', 'yellow', 'green', 'blue'],
            text: ['123', '245', '15', '23'],
            text_size: 20,
        },
        svgns = 'http://www.w3.org/2000/svg',
        template =  ''+
                       ' <svg id="svg_root"'+
                            'width="360" height="360"'+
                            'viewBox="-10 -10 400 400"'+
                            'preserveAspectRatio="xMidYMid slice"'+
                            'xmlns="' +svgns+ '" version="1.1">'+
                        '</svg>'+
                    '';


    function Point(x, y){
        this.x = x;
        this.y = y;

        this.toString = function(){
            return 'Point x:' +this.x+ " y:" +this.y;
        }
    };

    // The actual plugin constructor
    function Plugin( element, options ) {
        this.element = $(element);

        // jQuery has an extend method that merges the
        // contents of two or more objects, storing the
        // result in the first object. The first object
        // is generally empty because we don't want to alter
        // the default options for future instances of the plugin
        this.options = $.extend( {}, defaults, options) ;

        this._defaults = defaults;
        this._name = pluginName;

        this.init();
    }

    Plugin.prototype.init = function () {
        // Place initialization logic here
        // You already have access to the DOM element and
        // the options via the instance, e.g. this.element
        // and this.options
        this.base = this.options.base;
        this.top = this.options.top;
        this.height = this.options.height;
        this.slices = this.options.slices;
        this.slice_separation = this.options.slice_separation;
        this.colours = this.options.colours;
        this.text = this.options.text;
        this.text_size = this.options.text_size || 20;
        this.pyramid = $(template).appendTo(this.element).on({
                                click: $.proxy(this.click, this)
                        });


        if (this.component){
            this.component.on('click', $.proxy(this.show, this));
        } else {
            this.element.on('click', $.proxy(this.show, this));
        }

        this.render();
    };

    Plugin.prototype.render = function () {
        var points = this.getPoints();

        //create bottom slice
        var coords = [points[0][0], points[0][1], points[1][1], points[1][0]];
        this.createPolygon(coords, this.text[0], this.colours[0], 1);

        //create middle slices
        for(var i=1; i<this.slices - 1; i++){
            //var coords = [points[i][2], points[i][3], points[i + 1][1], points[i + 1][0]]
            var coords = [points[i][2], points[i][3], points[i + 1][1], points[i + 1][0]]
            this.createPolygon(coords, this.text[i], this.colours[i], i + 1);
        }

        //create top slice
        coords = [points[this.slices-1][2],points[this.slices-1][3], points[this.slices][0], points[this.slices][1]];
        this.createPolygon(coords, this.text[this.slices - 1], this.colours[this.slices - 1], this.slices);
    }

    Plugin.prototype.createPolygon = function (points, text, colour, id){
        var middle_point = this.get_xy_middle(points[0], points[2]);
        var svg_root = this.element.parent('div').find('#svg_root');
        
        var path_points = points[0].x +' '+ points[0].y +','+
        points[1].x +' '+ points[1].y +','+
        points[2].x +' '+ points[2].y +','+
        points[3].x +' '+ points[3].y;

        var polygon = document.createElementNS(svgns,"polygon");
        polygon.setAttributeNS(null, "points", path_points);
        polygon.setAttributeNS(null, "fill", colour);
        polygon.setAttributeNS(null, "stroke", "black");

        var data = document.createTextNode(text);
        var text = document.createElementNS(svgns,"text");
        text.setAttributeNS(null, "x", middle_point.x);
        text.setAttributeNS(null, "y", middle_point.y+this.text_size/3);
        text.setAttributeNS(null, "font-size", this.text_size);
        text.setAttributeNS(null, "text-anchor", "middle");
        if(colour == '#FFFFFF') {
            text.setAttributeNS(null, "fill", "black");
        } else {
            text.setAttributeNS(null, "fill", "white");
        }
        text.appendChild(data);

        var data = document.createTextNode(id);
        var id = document.createElementNS(svgns,"id");
        id.appendChild(data);


        svg_root.append(polygon);
        svg_root.append(text);
        svg_root.append(id);

    }

    Plugin.prototype.click = function (e) {
        e.stopPropagation();
        e.preventDefault();
        var target = $(e.target).closest('polygon, text');

        if (target.length == 1) {
            switch(target[0].nodeName.toLowerCase()) {
                case 'polygon':
                    var nodetext =  $(target[0]).next();
                    var _text = nodetext.text();
                    var nodetext =  nodetext.next();
                    var _id = nodetext.text();
                    this.element.trigger({type: 'click', text:_text, id:_id});
                    break;

                case 'text':
                    var nodetext =  $(target[0]).next();
                    var _id = nodetext.text();
                    var _text = target.text();
                    this.element.trigger({type: 'click', text:_text, id:_id});
                    break;
            }
        }
    }

    Plugin.prototype.getPoints = function () {
        var a = new Point(0, this.height);
        var b = new Point(this.base, this.height);
        var c = new Point((this.base + this.top) / 2, 0);
        var d = new Point((this.base - this.top) / 2, 0);

        var middle_slice_separation = (this.slice_separation * (this.height / this.slices))/2;
        var k = (this.base - this.top) / (this.height * 2);

        var points = {};

        for(var i=0; i<=this.slices; i++){
            points[i] = []
            var y = this.height - i * this.height / this.slices;

            var yt = y - middle_slice_separation;
            var yb = y + middle_slice_separation;

            var xtl = k * (this.height - yt);
            var xtr = this.base - xtl;

            var xbl = k * (this.height - yb);
            var xbr = this.base - xbl;

            switch(i){
                case 0:
                    //bottom vertex
                    points[i].push(a);
                    points[i].push(b);
                    break;

                case this.slices:
                    //top vertex
                    points[i].push(c);
                    points[i].push(d);
                    break;

                default:
                    points[i].push(new Point(xbl, yb));
                    points[i].push(new Point(xbr, yb));
                    points[i].push(new Point(xtl, yt));
                    points[i].push(new Point(xtr, yt));
            }
        }
        return points;
    }

    Plugin.prototype.get_xy_middle = function(top, bottom){
        var y = bottom.y + (top.y - bottom.y)*0.5;
        var x = this.base * 0.5;
        return new Point(x, y);
    }

    // A really lightweight plugin wrapper around the constructor,
    // preventing against multiple instantiations
    $.fn[pluginName] = function ( options ) {
        return this.each(function () {
            if (!$.data(this, 'plugin_' + pluginName)) {
                $.data(this, 'plugin_' + pluginName,
                new Plugin( this, options ));
            }
        });
    }

})( jQuery, window, document );

