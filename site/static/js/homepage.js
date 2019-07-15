const w = 500;
const h = 300;
const padding = 20;

function make_top10_bar_chart(div, dataset, axis_values, fill_color, font_color){
// Generates chart of top 10 comedians based on selected dataset

  const svg = d3.select(div)
              .append("svg")
              .attr('viewBox', '0 0 ' + w + ' ' + h);

  const xScale = d3.scaleLinear()
                   .domain([0, d3.max(dataset, (d) => d[axis_values])])
                   .range([h-padding/2,padding/2]);

  // create bars
  svg.selectAll("rect") 
      .data(dataset) 
      .enter() 
      .append("rect")
      .attr("x", 0) 
      .attr("y", (d, i) => (padding/2) + i * ((h - padding)/10)) 
      .attr("height", (h - padding * 2)/10) 
      .attr("width", (d) => w - xScale(d[axis_values]) - padding/2) 
      .attr("fill", fill_color)

  // put text left-aligned inside of bars
  svg.selectAll("text")
      .data(dataset)
      .enter()
      .append("text")
      .text((d) => (d.comedian_name + " - " + d[axis_values]))
      .attr("x", padding/2)
      .attr("y", (d, i) => (padding/2) + i * ((h - padding)/10) + 17)
      .attr("fill", font_color)

}

// generate chart of top 10 comedians by number of shows
make_top10_bar_chart(div = "#top_comedians", dataset = frequent_comedians, axis_values = "show_count", fill_color = "#4f2d7f", font_color = "white")

// generate chart of top 10 comedians by number of days since last show
make_top10_bar_chart(div = "#dry_spells", dataset = dry_spell_comedians, axis_values = "days_since_last_show", fill_color = "#62bad4", font_color = "black")
