$(document).ready(function() {


    //find detials of hos this works here: https://bbbootstrap.com/snippets/multiselect-dropdown-list-83601849
    var choicesForWhatServiceLeadIsInterestedIn = new Choices('#what_services_are_they_interested_in', {
        removeItemButton: true,
        // maxItemCount:5,
        // searchResultLimit:5,
        // renderChoiceLimit:5
      });

    $('#what_services_are_they_interested_in').data('choices', choicesForWhatServiceLeadIsInterestedIn);

    var today = new Date().toISOString().slice(0, 16);
        document.getElementsByName("appointment_date_and_time" )[0].setAttribute('min', today);


 $('input[name="search_query"]').on('input', function() {
	//alert($(this).val());
	if ( $(this).val() != "")
	{
        $('input[name="start_date"]').attr('disabled', true);
        $('input[name="end_date"]').attr('disabled', true);
        }
        else
        {
        $('input[name="start_date"]').attr('disabled', false);
        $('input[name="end_date"]').attr('disabled', false);
        }
    });


    $('input[name="start_date"]').on('input', function() {
	//alert($(this).val());
	if ( $(this).val() != "")
	{
        $('input[name="search_query"]').attr('disabled', true);
        $('input[name="end_date"]').attr('required', true);
        }
        else
        {
        $('input[name="search_query"]').attr('disabled', false);
        $('input[name="end_date"]').attr('required', false);
        }
    });

     $('input[name="end_date"]').on('input', function() {
	//alert($(this).val());
	if ( $(this).val() != "")
	{
        $('input[name="search_query"]').attr('disabled', true);
        $('input[name="start_date"]').attr('required', true);
        }
        else
        {
        $('input[name="search_query"]').attr('disabled', false);
        $('input[name="start_date"]').attr('required', false);
        }
    });

    $('a[name="search_link"]').on('click', function() {
        document.getElementById("modify_lead_info").hidden=false;
    });

     $('input[name="send_confirmation_to_lead"]').on('click', function() {
        if ($(this).val() == "" || $(this).val() == "no") {
            $(this).val("yes")
        } else {
            $(this).val("no");
        }
    });

    $('input[name="appointment_completed"]').on('click', function() {
        if ($(this).val() == "" || $(this).val() == "no") {
            $(this).val("yes")
        } else {
            $(this).val("no");
        }
    });

});