$(document).ready(function() {

    $('#full-payment-options').on('click', function() {

        $('#full-payment-div').attr('style', 'display: block !important');
        $('#installment-payment-div').attr('style', 'display: none !important');


        $('input[name="installment-payment"]').prop('required', false);
        $('input[name="installment-payment"]').attr('disabled', true);
        $('input[name="full-payment"]').attr('disabled', false);

        $("#full-payment-div").detach().appendTo('#holding-div');
        $("#full-payment-div").show();
        $("#full-payment-div").css("visibility", "visible");

    });

    $('#installment-payment-options').on('click', function() {

        $('#installment-payment-div').attr('style', 'display: block !important');
        $('#full-payment-div').attr('style', 'display: none !important');

        $('input[name="full-payment"]').prop('required', false);
        $('input[name="full-payment"]').attr('disabled', true);
        $('input[name="installment-payment"]').attr('disabled', false);

        $("#installment-payment-div").detach().appendTo('#holding-div');
        $("#installment-payment-div").show();
        $("#installment-payment-div").css("visibility", "visible");
    });




var form=document.getElementById('invoice');//retrieve the form as a DOM element

var stripe_info = $("#stripe_info").attr("data-stripe_info");


    var input = document.createElement('input');//prepare a new input DOM element
    input.setAttribute('name', 'stripe_info');//set the param name
    input.setAttribute('value', stripe_info);//set the value
    input.setAttribute('type', 'hidden');//set the type, like "hidden" or other
    form.appendChild(input);//append the input to the form


});