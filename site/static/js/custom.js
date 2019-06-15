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

  svg.selectAll("rect")
      .data(dataset)
      .enter()
      .append("rect")
      .attr("x", 0)
      .attr("y", (d, i) => (padding/2) + i * ((h - padding)/10))
      .attr("height", (h - padding * 2)/10)
      .attr("width", (d) => w - xScale(d[axis_values]) - padding/2)
      .attr("fill", fill_color)

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

var comedian_names = unique_comedians.map(a => a.comedian_name)

var selected_comedians = []

var selected_comedians_index = 0

$("#signup_comedian_search").autocomplete({
    source: comedian_names,
    select: function(event, ui) {
        var selected_comedian_name = ui.item.value
        if (selected_comedians.indexOf(selected_comedian_name) == -1){
          comedian_initials = selected_comedian_name.split(' ')[0][0] + selected_comedian_name.split(' ')[1][0]
          selected_comedians.push(selected_comedian_name);
          new_selected_comedian(selected_comedian_name, comedian_initials, selected_comedians_index);
          selected_comedians_index += 1;
        }
        $(this).val('');
        return false;
    }
});

var tooltip = d3.select("body")
                .append("div")
                .style("position", "absolute")
                .style("z-index", "10")
                .style("visibility", "hidden")
                .attr("id", "tooltip")
                .html("<div id=name>name</div><div style='font-size: 10px; font-style: italic'>Click to remove</div>");

function new_selected_comedian(name, initials, index){
  d3.select("#selected_comedians")
    .append("div")
    .text(initials)
    .attr("class", "comedian_circle")
    .attr("onclick", "remove_comedian(this)")
    .attr("id", "comedian" + index)
    .on("mouseover", ()=>{
                      d3.select("#tooltip")
                        .select("#name")
                        .text(name);
                      tooltip.style("visibility", "visible")
        })
    .on("mousemove", () => tooltip.style("top", (event.pageY-10)+"px").style("left",(event.pageX+10)+"px"))
    .on("mouseout", () => tooltip.style("visibility", "hidden"));
}

function remove_comedian(comedian){
  $("#"+ comedian.id).remove();
  tooltip.style("visibility", "hidden");
}

function show_signup_form(){
  $("#overlay").css("display", "block");
}

function exit_form(){
  reset_form();
}

function reset_form(){
  selected_comedians = []
  for (i=0; i<selected_comedians_index; i++){
    $("#comedian"+i).remove();
  }
  selected_comedians_index = 0
  $("#signup_comedian_search").val('');
  $("#user_email").val('');
  $("#overlay").css("display", "none");
  return false;
}

$("#form_submit").on('click', function(){
  signup_data = {}
  signup_data["email"] = $("#user_email").val()
  signup_data["comedians"] = selected_comedians
  console.log(JSON.stringify(signup_data))
  $.ajax({
    type: "POST",
    contentType: "application/json;charset=utf-8",
    url: "/",
    traditional: "true",
    data: JSON.stringify(signup_data),
    dataType: "json"
  })
  reset_form();
})

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
