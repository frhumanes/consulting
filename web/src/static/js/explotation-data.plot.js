

function init_bars(data, container) {
  /* edit these settings freely */  
  var w = Math.min($('#main').width(), 550),
      h = Math.min(500, data.length * 40),
      topMargin = 15,
      labelSpace = 120,
      innerMargin = w/2+labelSpace,
      outerMargin = 15,
      gap = 2,
      dataRange = d3.max(data.map(function(d) { return Math.max(d.barData1, d.barData2) }));
      leftLabel = "Hombres",
      rightLabel = "Mujeres";

  /* edit with care */
  var chartWidth = w - innerMargin - outerMargin,
      barWidth = Math.min(h / data.length, 30),
      yScale = d3.scale.linear().domain([0, data.length]).range([0, h-topMargin]),
      total = d3.scale.linear().domain([0, dataRange]).range([0, chartWidth - labelSpace/2]),
      commas = d3.format(",.3f");

  /* main panel */
  var vis = d3.select(container).append("svg")
      .attr("width", w)
      .attr("height", h);

  /* barData1 label */
  vis.append("text")
    .attr("class", "label")
    .text(leftLabel)
    .attr("x", w-innerMargin)
    .attr("y", topMargin-3)
    .attr("text-anchor", "end");

  /* barData2 label */
  vis.append("text")
    .attr("class", "label")
    .text(rightLabel)
    .attr("x", innerMargin)
    .attr("y", topMargin-3);

  /* female bars and data labels */ 
  var bar = vis.selectAll("g.bar")
      .data(data)
    .enter().append("g")
      .attr("class", "bar")
      .attr("transform", function(d, i) {
        return "translate(0," + (yScale(i) + topMargin) + ")";
      });

  var wholebar = bar.append("rect")
      .attr("width", w)
      .attr("height", barWidth-gap)
      .attr("fill", "none")
      .attr("pointer-events", "all");

  var highlight = function(c) {
    return function(d, i) {
      bar.filter(function(d, j) {
        return i === j;
      }).attr("class", c);
    };
  };

  bar
    .on("mouseover", highlight("highlight bar"))
    .on("mouseout", highlight("bar"));

  bar.append("rect")
      .attr("class", "femalebar")
      .attr("height", barWidth-gap);

  bar.append("text")
      .attr("class", "femalebar")
      .attr("dx", -3)
      .attr("dy", "1em")
      .attr("text-anchor", "end");

  bar.append("rect")
      .attr("class", "malebar")
      .attr("height", barWidth-gap)
      .attr("x", innerMargin);

  bar.append("text")
      .attr("class", "malebar")
      .attr("dx", 3)
      .attr("dy", "1em");

  /* sharedLabels */
  bar.append("text")
      .attr("class", "shared")
      .attr("x", w/2)
      .attr("dy", "1em")
      .attr("text-anchor", "middle")
      .text(function(d) { return d.sharedLabel; });

  var bars = d3.selectAll("g.bar")
      .data(data);
  bars.selectAll("rect.malebar")
    .transition()
      .attr("width", function(d) { return total(d.barData1); });
  bars.selectAll("rect.femalebar")
    .transition()
      .attr("x", function(d) { return innerMargin - total(d.barData2) - 2 * labelSpace; }) 
      .attr("width", function(d) { return total(d.barData2); });

  bars.selectAll("text.malebar")
      .text(function(d) { return commas(d.barData1); })
    .transition()
      .attr("x", function(d) { return innerMargin + total(d.barData1); });
  bars.selectAll("text.femalebar")
      .text(function(d) { return commas(d.barData2); })
    .transition()
      .attr("x", function(d) { return innerMargin - total(d.barData2) - 2 * labelSpace; });
}

function init_pie(data, container) {
  var width = Math.min($('#main').width(), 550),
    height = 500,
    radius = Math.min(width, height) / 2;

  var color = d3.scale.ordinal()
      .range(["#98abc5", "#8a89a6", "#7b6888", "#6b486b", "#a05d56", "#d0743c", "#ff8c00"]);

  var arc = d3.svg.arc()
      .outerRadius(radius - 10)
      .innerRadius(0);

  var pie = d3.layout.pie()
      .sort(null)
      .value(function(d) { return d.population; });

  var svg = d3.select(container).append("svg")
      .attr("width", width)
      .attr("height", height)
    .append("g")
      .attr("transform", "translate(" + width / 2 + "," + height / 2 + ")");

  var g = svg.selectAll(".arc")
      .data(pie(data))
    .enter().append("g")
      .attr("class", "arc");

  g.append("path")
      .attr("d", arc)
      .style("fill", function(d) { return color(d.data.age); });

  g.append("text")
      .attr("transform", function(d) { return "translate(" + arc.centroid(d) + ")"; })
      .attr("dy", ".35em")
      .style("text-anchor", "middle")
      .text(function(d) { return d.data.age; });
}

function init_donuts(dataset, container) {
  var width = Math.min($('#main').width(), 550),
      height = 430,
      radius = Math.min(width, height) / 2;

  var color = d3.scale.ordinal()
      .range(['#FFFFFF', '#468847', '#0088CC', '#999999', '#F89406', '#B94A48', '#202020']);

  var color_name = ['No diagnosticado','Ausente', 'Muy Leve', 'Leve', 'Moderada', 'Grave', 'Muy grave'];

  var pie = d3.layout.pie()
      .startAngle(-Math.PI / 2)
      .endAngle(Math.PI / 2)
      .sort(null);

  var arc = d3.svg.arc()
      .innerRadius(radius - 90)
      .outerRadius(radius - 10);

  var legend = d3.select(container).append("svg")
      .attr("class", "legend")
      .attr("width", radius)
      .attr("height", radius)
    .selectAll("g")
      .data(color_name)
    .enter().append("g")
      .attr("transform", function(d, i) { return "translate(0," + i * 20 + ")"; });

  legend.append("rect")
      .attr("width", 15)
      .attr("height", 15)
      .attr("stroke", '#ccc')
      .style("fill", color);

  legend.append("text")
      .attr("x", 21)
      .attr("y", 8)
      .attr("dy", ".35em")
      .text(function(d, i) { return d; });

  $.each(dataset, function(key, data) {

    var total = data.reduce(function(a,b){return a+b;});

    var svg = d3.select(container).append("svg")
        .attr("width", width)
        .attr("height", (height + 50)/ 2)
        .attr("class", key)
        .append("g")
        .attr("transform", "translate(" + width / 2 + "," + height / 2 + ")");

    var path = svg.selectAll("path")
        .data(pie(data))
        .enter().append("path")
        .attr("fill", function(d, i) { return color(i); })
        .attr("stroke", '#ccc')
        .attr("d", arc);

    var text = svg.selectAll("text-anchor")
        .data(pie(data))
        .enter().append("text")
        .attr("transform", function(d) { return "translate(" + arc.centroid(d) + ")"; })
        .attr("dy", ".35em")
        .style("text-anchor", "middle")
        .text(function(d, i) { return d.value?d.value+' ('+Math.round(d.value*100/total)+'%)':''; });


    var label_text = svg.append("text")
        .attr("text-anchor", "middle")
        .attr("dy", ".35em")
        .text(key);
  });

}