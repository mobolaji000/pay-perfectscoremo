$(document).ready(function() {

    //find detials of hos this works here: https://bbbootstrap.com/snippets/multiselect-dropdown-list-83601849
    var choicesForWhatServiceLeadIsInterestedIn = new Choices('#what_services_are_you_interested_in', {
        removeItemButton: true,
        // maxItemCount:5,
        // searchResultLimit:5,
        // renderChoiceLimit:5
      });

    $('#what_services_are_you_interested_in').data('choices', choicesForWhatServiceLeadIsInterestedIn);




     $('select[name="lead_salutation"]').val(result.lead_salutation);
	$('input[name="lead_name"]').val(result.lead_name);
     $('input[name="lead_email"]').val(result.lead_email);
     $('input[name="lead_phone_number"]').val(result.lead_phone_number);

	 $('select[name="grade_level"]').val(result.grade_level);
	 $('input[name="recent_test_score"]').val(result.recent_test_score);


	 // find details of how this works here: https://github.com/Choices-js/Choices

		var services_you_are_interested_in = result.what_services_are_you_interested_in;
		// you will have to remember to change the list above anytime you make a change to the items in the "what_services_are_you_interested_in" select
		var all_services = ["PSAT/PACT","SAT/ACT","College Admissions Counselling","General Tutoring","Other"];

		 var new_choices = [];

		 for (let k = 0; k < all_services.length; k++) {
			 if(services_you_are_interested_in.includes(all_services[k])){
				 new_choices[k] = { value: all_services[k], label: all_services[k], disabled: false, selected: true };
			 }
			 else
			 {
				 new_choices[k] = { value: all_services[k], label: all_services[k], disabled: false, selected: false };
			 }
		}

		 var choicesForWhatServiceLeadIsInterestedIn = $('#what_services_are_you_interested_in').data('choices');

		 console.log(services_you_are_interested_in);

		 choicesForWhatServiceLeadIsInterestedIn.removeActiveItems();
		 choicesForWhatServiceLeadIsInterestedIn.clearChoices();
		 choicesForWhatServiceLeadIsInterestedIn.setChoices(new_choices, 'value', 'label', true,);

          $('textarea[name="details_on_what_service_you_are_interested_in"]').val(result.details_on_what_service_you_are_interested_in);
     $('textarea[name="miscellaneous_notes"]').val(result.miscellaneous_notes);
     $('select[name="how_did_you_hear_about_us"]').val(result.how_did_you_hear_about_us);
          $('textarea[name="details_on_how_you_heard_about_us"]').val(result.details_on_how_you_heard_about_us);
          
});