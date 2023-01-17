$(document).ready(function() {

    // $('input[name="send_confirmation_to_lead"]').attr('disabled', true);
    //
    // $('#appointment_date_and_time').change(function() {
    //
    //     if ($(this).val() == "") {
    //         $('input[name="tp_product"]').prop('required', true);
    //
    //         $('input[name="tp_product"]').prop('checked', false);
    //
    //
    //         $('input[name="tp_product"]').attr('disabled', false);
    //         $('input[name="tp_units"]').attr('disabled', false);
    //         $('input[name="tp_units"]').val("1");
    //         $(this).val("yes");
    //     } else {
    //         $('input[name="tp_product"]').prop('required', false);
    //
    //         $('input[name="tp_product"]').prop('checked', false);
    //
    //         $('input[name="tp_product"]').attr('disabled', true);
    //         $('input[name="tp_units"]').attr('disabled', true);
    //         $('input[name="tp_units"]').val("");
    //         $('input[name="tp_total"]').val("");
    //         $(this).val("");
    //     }
    //
    //     $('input[name="tp_total"]').val(calculateTestPrepTotal());
    //     $('input[name="transaction_total"]').val(transactionTotal()).change();
    // });


    //find detials of hos this works here: https://bbbootstrap.com/snippets/multiselect-dropdown-list-83601849
    var choicesForWhatServiceLeadIsInterestedIn = new Choices('#what_services_are_they_interested_in', {
        removeItemButton: true,
        // maxItemCount:5,
        // searchResultLimit:5,
        // renderChoiceLimit:5
      });

    $('#what_services_are_they_interested_in').data('choices', choicesForWhatServiceLeadIsInterestedIn);


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

	// 	 $('select[name="what_services_are_they_interested_in"]').on('change', function() {
   //     console.log($('#what_services_are_they_interested_in').val());
	//    alert($('#what_services_are_they_interested_in').val());
   // });





});