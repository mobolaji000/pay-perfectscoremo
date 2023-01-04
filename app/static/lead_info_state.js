$(document).ready(function() {
    // By Default Disable radio button
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


});