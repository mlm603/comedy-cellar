// const w = 500;
// const h = 300;
const xpadding = 20;
const ypadding = 40;



function populate_dash(comedian_name){
  selected_comedian_single_val = summary_stats.filter(d => d.comedian_name === comedian_name)[0]

  // month in json is in a weird string format, so parsing it to be mm/dd/yy
  month_lookup = {'Jan':'01', 'Feb':'02', 'Mar':'03', 'Apr':'04', 'May':'05', 'June':'06', 'July':'07', 'Aug':'08', 'Sept':'09', 'Oct':'10', 'Nov':'11', 'Dec':'12'}
  mr_show = selected_comedian_single_val.most_recent_show_timestamp
  mr_show_string = mr_show.substring(mr_show.indexOf(',')+2, mr_show.indexOf(':')-3)
  mr_show_arr = mr_show_string.split(' ')
  mr_show_final = month_lookup[mr_show_arr[1]] + "/" + mr_show_arr[0] + "/" + mr_show_arr[2].substring(2,4)

  // updating single value tiles
  $("#previous_shows_value").text(selected_comedian_single_val.previous_shows);
  $("#upcoming_shows_value").text(selected_comedian_single_val.upcoming_shows);
  $("#most_recent_show_value").text(mr_show_final);

  selected_comedian_day_of_week = day_of_week_stats.filter(d => d.comedian_name === comedian_name)

  make_column_chart(dataset = selected_comedian_day_of_week, div = "day_of_week_chart", axis_values = "show_count", fill_color = "#4f2d7f", font_color = "black")

  selected_comedian_upcoming_shows = upcoming_shows.filter(d => d.comedian_name === comedian_name)

  add_to_table(selected_comedian_upcoming_shows)
}

function make_column_chart(dataset, div, axis_values, fill_color, font_color){

  var $container = $('.chart_container')

  w = $container.width()
  h = $container.height()

// Generates chart of top 10 comedians based on selected dataset
  day_abbr_lookup = {'Sunday':'Su', 'Monday':'M', 'Tuesday':'Tu', 'Wednesday':'W', 'Thursday':'Th', 'Friday':'F', 'Saturday':'Sa'}

  const svg = d3.select("#" + div)
              .append("svg")
              .attr("width", '100%')
              .attr("height", '100%')
              .attr('viewBox','0 0 '+w+' '+h)
              .style("background-color", "rgba(0,0,0,0.05)");

  const yScale = d3.scaleLinear()
                   .domain([0, d3.max(dataset, (d) => d[axis_values])])
                   .range([ypadding, h - ypadding * 2]);

  x_axis_increment = (w - xpadding * 2)/7

  const xScale = d3.scaleOrdinal()
                   .domain(['Su', 'M', 'Tu', 'W', 'Th', 'F', 'Sa'])
                   .range([xpadding, xpadding + x_axis_increment, xpadding + x_axis_increment*2, xpadding + x_axis_increment*3, xpadding + x_axis_increment*4, xpadding + x_axis_increment*5, xpadding + x_axis_increment*6]);

  const gap = 5

  // create columns
  svg.selectAll("rect") 
      .data(dataset) 
      .enter() 
      .append("rect")
      .attr("x", (d) => xScale(day_abbr_lookup[d.show_day_of_week]) + gap /2) 
      .attr("y", (d) => h - yScale(d[axis_values]) - ypadding) 
      .attr("height", (d) => yScale(d[axis_values]))
      .attr("width",  ((w - xpadding * 2) / 7) - gap) 
      .attr("fill", fill_color)
      .attr("id", (d) => d.show_day_of_week)

  // add show count numbers to top of columns

  svg.selectAll(".chart_label")
      .data(dataset)
      .enter()
      .append("text")
      .attr("x", (d) => xScale(day_abbr_lookup[d.show_day_of_week]) + gap /2) 
      .attr("y", (d) => h - yScale(d[axis_values]) - ypadding) 
      .attr("transform", "translate(" + (((w - xpadding * 2) / 7 - 5) / 2) + ", -5)")
      .attr("text-anchor", "middle")
      .attr("font-size", "16px")
      .text((d) => d.show_count)

  // add xAxis labels

  // svg.selectAll(".chart_axis_label")
  //     .data(day_abbr_lookup)
  //     .enter()
  //     .append("text")
  //     .attr("x", (d) => xScale(day_abbr_lookup[d.show_day_of_week]) + gap /2) 
  //     .attr("y", (d) => h - yScale(d[axis_values]) - ypadding) 
  //     .attr("transform", "translate(" + (((w - xpadding * 2) / 7 - 5) / 2) + ", -5)")
  //     .attr("text-anchor", "middle")
  //     .text((d) => d.show_count)

  const xAxis = d3.axisBottom(xScale)

  svg.append("g")
    .attr("transform", "translate(" + (gap / 2 + ((w - xpadding * 2) / 7 - 5) / 2) + "," +(h-ypadding) + ")")
    .call(xAxis)
    .attr("font-size", "16px")

}

function add_to_table(dataset){
  months = ["Jan", "Feb", "Mar", "Apr", "May", "June", "July", "Aug", "Sept", "Oct", "Nov", "Dec"]
  $(".rowtest").remove()
  if (dataset.length > 0){
    $("#no_upcoming_shows").css("display", "none")
    $("#upcoming_shows_table").css("display", "")
    new_rows = ""
    for (i in dataset){
      show = dataset[i]
      show_timestamp = new Date(show.show_timestamp)
      new_rows = new_rows 
          + "<div class='rTableRow rowtest'>" 
          + "<div class='rTableCell small_cell'>" 
          + months[show_timestamp.getMonth()] + " " + show_timestamp.getDate()
          + "</div><div class='rTableCell small_cell'>" 
          + show_timestamp.getHours() + ":" + (show_timestamp.getMinutes() == 0 ? "00" : show_timestamp.getMinutes())
          + "</div><div class='rTableCell small_cell'>" 
          + show.show_day_of_week 
          + "</div><div class='rTableCell small_cell'>" 
          + show.location + "</div><div class='rTableCell'>" 
          + show.other_comedians 
          + "</div>"
          + "</div>"
    }
    $("#upcoming_shows_table").append(new_rows)
  } else {
    $("#no_upcoming_shows").css("display", "block")
    $("#upcoming_shows_table").css("display", "none")
  }
}

populate_dash('Judah Friedlander')
