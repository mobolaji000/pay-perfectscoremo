$(document).ready(function() {

    //find detials of hos this works here: https://bbbootstrap.com/snippets/multiselect-dropdown-list-83601849
    var choicesForWhatServiceLeadIsInterestedIn = new Choices('#what_services_are_you_interested_in', {
        removeItemButton: true,
        // maxItemCount:5,
        // searchResultLimit:5,
        // renderChoiceLimit:5
      });

    $('#what_services_are_you_interested_in').data('choices', choicesForWhatServiceLeadIsInterestedIn);


var lead_salutation = $("#lead").attr("data-lead_salutation");
var lead_name = $("#lead").attr("data-lead_name");
var lead_email = $("#lead").attr("data-lead_email");
var lead_phone_number = $("#lead").attr("data-lead_phone_number");
var grade_level = $("#lead").attr("data-grade_level");
var recent_test_score = $("#lead").attr("data-recent_test_score");
var what_services_are_you_interested_in = $("#lead").attr("data-what_services_are_you_interested_in");
var details_on_what_service_you_are_interested_in = $("#lead").attr("data-details_on_what_service_you_are_interested_in");
var miscellaneous_notes = $("#lead").attr("data-miscellaneous_notes");
var how_did_you_hear_about_us = $("#lead").attr("data-how_did_you_hear_about_us");
var details_on_how_you_heard_about_us = $("#lead").attr("data-details_on_how_you_heard_about_us");




     $('select[name="lead_salutation"]').val(lead_salutation);
	$('input[name="lead_name"]').val(lead_name);
     $('input[name="lead_email"]').val(lead_email);
     $('input[name="lead_phone_number"]').val(lead_phone_number);

	 $('select[name="grade_level"]').val(grade_level);
	 $('input[name="recent_test_score"]').val(recent_test_score);


	 // find details of how this works here: https://github.com/Choices-js/Choices

		var services_you_are_interested_in = what_services_are_you_interested_in;
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

          $('textarea[name="details_on_what_service_you_are_interested_in"]').val(details_on_what_service_you_are_interested_in);

		  //NO, DON'T SHOW miscellaneous_notes!!! This is where you keep your private thoughts about the lead
		  //$('textarea[name="miscellaneous_notes"]').val(miscellaneous_notes);


     $('select[name="how_did_you_hear_about_us"]').val(how_did_you_hear_about_us);
          $('textarea[name="details_on_how_you_heard_about_us"]').val(details_on_how_you_heard_about_us);

});