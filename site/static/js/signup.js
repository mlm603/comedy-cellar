var comedian_names = unique_comedians.map(a => a.comedian_name)

// initiate selected_comedians array as a global variable
// this will store all selected comedians and ultimately be passed in the POST action to add to the subscriptions pg table
var selected_comedians = []

// initiate index as a global variable
// this is used to create unique ids for the divs created when a comedian is selected, which aids in removing the divs if needed
var selected_comedians_index = 0

// Populate autocomplete options for comedian names
$("#signup_comedian_search").autocomplete({
    source: comedian_names,
    select: function(event, ui) {
        // get comedian name when selected from suggestions
        var selected_comedian_name = ui.item.value
        // if selected comedian wasn't already selected
        if (selected_comedians.indexOf(selected_comedian_name) == -1){
          comedian_name_split = selected_comedian_name.split(' ')
          // get comedian's initials to use in circle icon showing selected comedians
          comedian_initials = (comedian_name_split.length > 1 ? comedian_name_split[0][0] + comedian_name_split[1][0] : comedian_name_split[0][0])
          // add comedian to array
          selected_comedians.push(selected_comedian_name);
          // create circle with comedian's initials
          new_selected_comedian(selected_comedian_name, comedian_initials, selected_comedians_index);
          selected_comedians_index += 1;
        }
        $(this).val('');
        return false;
    }
});

// Create tooltip that hovers over selected comedian circles to show full comedian name
var tooltip = d3.select("body")
                .append("div")
                .style("position", "absolute")
                .style("z-index", "10")
                .style("visibility", "hidden")
                .attr("id", "tooltip")
                .html("<div id=name>name</div><div style='font-size: 10px; font-style: italic'>Click to remove</div>");

// Create a circle with the comedian's initials when selected
function new_selected_comedian(name, initials, index){
  d3.select("#selected_comedians")
    .append("div")
    .text(initials)
    .attr("class", "comedian_circle")
    .attr("onclick", "remove_comedian(this)")
    .attr("id", "comedian" + index)
    .attr("cname", name)
    .on("mouseover", ()=>{
                      d3.select("#tooltip")
                        .select("#name")
                        .text(name);
                      tooltip.style("visibility", "visible")
        })
    .on("mousemove", () => tooltip.style("top", (event.pageY-10)+"px").style("left",(event.pageX+10)+"px"))
    .on("mouseout", () => tooltip.style("visibility", "hidden"));
}

// remove comedian from selections
function remove_comedian(comedian){
  // remove circle with initials
  $("#"+ comedian.id).remove();
  // remove from selected_comedians array
  comedian_curr_index = selected_comedians.indexOf(comedian.getAttribute("cname"))
  selected_comedians.splice(comedian_curr_index, 1)
  tooltip.style("visibility", "hidden");
}

// display signup form as overlay on top of current page
function show_signup_form(){
  $("#overlay").css("display", "block");
}

function reset_form(){
  // reset selected_comedians array
  selected_comedians = []
  // remove divs for selected comedians
  for (i=0; i<selected_comedians_index; i++){
    $("#comedian"+i).remove();
  }
  // reset index
  selected_comedians_index = 0
  // clear input boxes
  $("#signup_comedian_search").val('');
  $("#user_email").val('');
  // hide signup form
  $("#overlay").css("display", "none");
  return false;
}

$("#form_submit").on('click', function(){
  // populate signup_data object to pass to POST action
  signup_data = {}
  signup_data["email"] = $("#user_email").val()
  signup_data["comedians"] = selected_comedians
  // verify email address is in proper format
  var regex = RegExp('[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}');
  email_valid = regex.test($("#user_email").val())
  if (email_valid){
    // POST json-ified version of signup_data object to write subscription details to pg table
    $.ajax({
      type: "POST",
      contentType: "application/json;charset=utf-8",
      url: "/",
      traditional: "true",
      data: JSON.stringify(signup_data),
      dataType: "json"
    })
    reset_form();
  } else {
    alert("Invalid Email")
  }
  
})