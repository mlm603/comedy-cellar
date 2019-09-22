var email = email

// if "All Emails" is selected, check all individ comedian boxes
$('#all_comeds').change(
	function(){
		if(this.checked){
			$("input:checkbox.individ_comed").prop('checked',true);
		} else{
			$("input:checkbox.individ_comed").prop('checked',false);
		}
	}
)

// if an individual comedian is unchecked, uncheck "All Emails"
$('.individ_comed').change(
	function(){
		if(!this.checked){
			$('#all_comeds').prop('checked',false);
		}
	}
)

// submit unsubscribe selections and update dim_subscriptions
$("#unsubscribe_submit").on('click', function(){
  // populate signup_data object to pass to POST action
  unsubscribe_data = {}
  unsubscribe_data["email"] = email
  selected_comedians = []
  $.each($("input:checked"), function(){
  		if ($(this).val() != "all"){
    		selected_comedians.push($(this).val());
    	}
	});
  unsubscribe_data["comedians"] = selected_comedians
  $.ajax({
  	type: "POST",
	  contentType: "application/json;charset=utf-8",
	  url: "/unsubscribe",
	  traditional: "true",
	  data: JSON.stringify(unsubscribe_data),
	  dataType: "json",
	  success: function(data){
	  	window.location = "/unsubscribe_success";
	  },
	  error: function(data){
	  	window.location = "/unsubscribe_success";
	  }
	})
  
})