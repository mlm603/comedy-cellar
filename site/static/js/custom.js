d3.select("body")
  .append("div")

const w = 500;
const h = 300;
const padding = 20;

const svg = d3.select("main")
              .append("svg")
              .attr("width", w)
              .attr("height", h);

const xScale = d3.scaleLinear()
                 .domain([0, d3.max(frequent_comedians, (d) => d.show_count)])
                 .range([h-padding/2,padding/2]);

svg.selectAll("rect")
    .data(frequent_comedians)
    .enter()
    .append("rect")
    .attr("x", 0)
    .attr("y", (d, i) => (padding/2) + i * ((h - padding)/10))
    .attr("height", (h - padding * 2)/10)
    .attr("width", (d) => w - xScale(d.show_count) - padding/2)
    .attr("class","bar")

svg.selectAll("text")
    .data(frequent_comedians)
    .enter()
    .append("text")
    .text((d) => (d.comedian_name + " - " + d.show_count))
    .attr("x", padding/2)
    .attr("y", (d, i) => (padding/2) + i * ((h - padding)/10) + 17)
    .attr("class", "bar_label")

var comedian_names = unique_comedians.map(a => a.comedian_name)

var selected_comedians = []

$("#signup_comedian_search").autocomplete({
    source: comedian_names,
    select: function(event, ui) {
        alert(ui.item.value);
        selected_comedians.push(ui.item.value);
        console.log(selected_comedians);
        $(this).val('');
        return false;
    }
});

// $("#signup_comedian_search").on('click', function(){alert('hi')})

// svg.append("g")
//     .attr("class", "y axis")
//     .
//     .call(yAxis);

// svg.selectAll("rect")
//   .data(frequent_comedians)
//   .enter()
//   .append("rect")
//   .attr("x", 0)
//   .attr("y", (d, i) => (padding/2) + i * ((h - padding)/10))
//   .attr("height", (h - padding * 2)/10)
//   .attr("width", (d) => w - xScale(d.show_count) - padding/2)
//   .attr("fill","#4f2d7f")
//   .attr("class","bar")
//   .attr("comedian_name", (d) => d.comedian_name)
//   .attr("show_count", (d) => d.show_count)
// });
