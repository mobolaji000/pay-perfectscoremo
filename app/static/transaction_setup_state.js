$(document).ready(function() {
    // By Default Disable radio button
    $('input[name="tp_product"]').attr('disabled', true);
    $('input[name="tp_units"]').attr('disabled', true);
    $('input[name="tp_total"]').attr('disabled', true);

    $('input[name="diag_units"]').attr('disabled', true);
    $('input[name="diag_total"]').attr('disabled', true);

    $('input[name="college_consultation"]').attr('disabled', true);
    $('input[name="college_apps_product"]').attr('disabled', true);
    $('input[name="college_apps_units"]').attr('disabled', true);
    $('input[name="college_apps_total"]').attr('disabled', true);

    $('input[name="adjust_total"]').prop('readonly', true);
    $('input[name="adjustment_explanation"]').prop('readonly', true);
    $('input[name="transaction_total"]').attr('disabled', true);


    function addDays(numberOfDaysToAdd) {
        var someDate = new Date();
        someDate.setDate(someDate.getDate() + numberOfDaysToAdd);

        //var dd = someDate.getDate();
        var dd = (someDate.getDate() + 1 < 10) ? "0" + (someDate.getDate() + 1) : someDate.getDate() + 1
        //var mm = m = someDate.getMonth() + 1;
        var mm = (someDate.getMonth() + 1 < 10) ? "0" + (someDate.getMonth() + 1) : someDate.getMonth() + 1
        var yy = someDate.getFullYear();

        var someFormattedDate = yy + '-' + mm + '-' + dd;

        return someFormattedDate;
    }

    var default_tp_date = default_college_apps_date = "";

    $('input[name="tp_product"]').on('click', function() {
        var selected_tp = $('input[name="tp_product"]:checked').attr("id");
        if (selected_tp.includes("12wks")) {
            default_tp_date = addDays(42);
        } else if (selected_tp.includes("8wks")) {
            default_tp_date = addDays(23);
        } else {
            default_tp_date = "";
        }

        if ($('input[name="turn_on_installments"]').val() != "") {
            setDefaultInstallmentDate();
        }

    });

    $('input[name="college_apps_product"]').on('click', function() {
        var selected_college_apps = $('input[name="college_apps_product"]:checked').attr("id");
        if (selected_college_apps.includes("apps-2") || selected_college_apps.includes("apps-3")) {
            default_college_apps_date = addDays(25);
        } else {
            default_college_apps_date = "";
        }

        if ($('input[name="turn_on_installments"]').val() != "") {
            setDefaultInstallmentDate();
        }
    });


    $('input[name="was_diagnostic_purchased"]').on('click', function() {


        if ($(this).val() == "") {
            $('input[name="diag_units"]').attr('disabled', false);
            $('input[name="diag_total"]').attr('disabled', false);

            $('input[name="diag_units"]').prop('required', true);
            $('input[name="diag_total"]').prop('required', true);

            $('input[name="diag_units"]').val("1");

            $('input[name="diag_total"]').val(calculateDiagnosticTotal());
            $('input[name="transaction_total"]').val(transactionTotal());


            $(this).val("yes")
        } else {
            $('input[name="diag_units"]').attr('disabled', true);
            $('input[name="diag_total"]').attr('disabled', true);

            $('input[name="diag_units"]').prop('required', false);
            $('input[name="diag_total"]').prop('required', false);

            $('input[name="diag_units"]').val("");
            $('input[name="diag_total"]').val("");
            $(this).val("");
        }

         $('input[name="diag_total"]').val(calculateDiagnosticTotal());
        $('input[name="transaction_total"]').val(transactionTotal());

    });

    $('input[name="diag_units"]').on('input', function() {
        $('input[name="diag_total"]').val(calculateDiagnosticTotal());
        $('input[name="transaction_total"]').val(transactionTotal());
    });

    function calculateDiagnosticTotal() {
        var diag_units = $('input[name="diag_units"]').val() || 0;
        var diag_price = 50;
        return Number(diag_units) * Number(diag_price);
    }

    $('#was_test_prep_purchased').change(function() {
        if ($(this).val() == "") {
            $('input[name="tp_product"]').prop('required', true);
            $('input[name="tp_product"]').prop('checked', false);


            $('input[name="tp_product"]').attr('disabled', false);
            $('input[name="tp_units"]').attr('disabled', false);
            $('input[name="tp_units"]').val("1");
            $(this).val("yes");
        } else {
            $('input[name="tp_product"]').prop('required', false);
            $('input[name="tp_product"]').prop('checked', false);

            $('input[name="tp_product"]').attr('disabled', true);
            $('input[name="tp_units"]').attr('disabled', true);
            $('input[name="tp_units"]').val("");
            $('input[name="tp_total"]').val("");
            $(this).val("");
        }

        $('input[name="tp_total"]').val(calculateTestPrepTotal());
        $('input[name="transaction_total"]').val(transactionTotal());
    });

    $('input[name="tp_product"]').change(function() {
        $('input[name="tp_total"]').val(calculateTestPrepTotal());
        $('input[name="transaction_total"]').val(transactionTotal());
    });

    $('input[name="tp_units"]').on('input', function() {
        $('input[name="tp_total"]').val(calculateTestPrepTotal());
        $('input[name="transaction_total"]').val(transactionTotal());
    });

    function calculateTestPrepTotal() {
        var tp_units = $('input[name="tp_units"]').val() || 0;
        var tp_product = $('input[name="tp_product"]:checked').val() || 0;
        return Number(tp_units) * Number(tp_product);
    }

    $('#was_college_apps_purchased').change(function() {
        if ($(this).val() == "") {
            $('input[name="college_consultation"]').prop('required', true);
            $('input[name="college_apps_product"]').prop('required', true);
            $('input[name="college_apps_units"]').prop('required', true);

            $('input[name="college_consultation"]').prop('checked', false);
            $('input[name="college_apps_product"]').prop('checked', false);

            $('input[name="college_consultation"]').prop('disabled', false);
            $('input[name="college_apps_product"]').prop('disabled', false);
            $('input[name="college_apps_units"]').prop('disabled', false);
            $('input[name="college_apps_units"]').val("1");
            $(this).val("yes")
        } else {
            $('input[name="college_consultation"]').prop('required', false);
            $('input[name="college_apps_product"]').prop('required', false);
            $('input[name="college_apps_units"]').prop('required', true);

            $('input[name="college_consultation"]').prop('checked', false);
            $('input[name="college_apps_product"]').prop('checked', false);

            $('input[name="college_consultation"]').prop('disabled', true);
            $('input[name="college_apps_product"]').prop('disabled', true);
            $('input[name="college_apps_units"]').prop('disabled', true);

            $('input[name="college_apps_units"]').val("");
            $('input[name="college_apps_total"]').val("");
            $(this).val("");
        }

         $('input[name="college_apps_total"]').val(collegeAppsTotal());
        $('input[name="transaction_total"]').val(transactionTotal());
    });

    $('input[name="college_consultation"]').change(function() {
        $('input[name="college_apps_total"]').val(collegeAppsTotal());
        $('input[name="transaction_total"]').val(transactionTotal());
    });

    $('input[name="college_apps_product"]').change(function() {
        $('input[name="college_apps_total"]').val(collegeAppsTotal());
        $('input[name="transaction_total"]').val(transactionTotal());
        $('input[name="college_apps_units"]').attr('min', 1);
    });

    $('input[name="college_apps_units"]').on('input', function() {
        $('input[name="college_apps_total"]').val(collegeAppsTotal());
        $('input[name="transaction_total"]').val(transactionTotal());
    });

    function collegeAppsTotal() {
        var college_consultation = $('input[name="college_consultation"]:checked').val() || 0;
        var college_apps_units = $('input[name="college_apps_units"]').val() || 0;
        var college_apps_product = $('input[name="college_apps_product"]:checked').val() || 0;
        return Number(college_consultation) + (Number(college_apps_units) * Number(college_apps_product));
    }

    $('#adjustment_explanation,#adjust_total').change(function() {
        if ($(this).val() != "") {
            $('input[name="adjust_total"]').prop('required', true);
            $('input[name="adjustment_explanation"]').prop('required', true);
        }
    });

    $('#adjustment_explanation,#adjust_total').on('click', function() {
        $('input[name="adjust_total"]').prop('readonly', false);
        $('input[name="adjustment_explanation"]').prop('readonly', false);
    });

    $('input[name="adjust_total"]').on('input', function() {
        $('input[name="transaction_total"]').val(transactionTotal());
    });

    function transactionTotal() {
        var diagnostic_total = $('input[name="diag_total"]').val() || 0;
        var adjust_total = $('input[name="adjust_total"]').val() || 0;
        var tp_total = $('input[name="tp_total"]').val() || 0;
        var college_apps_total = $('input[name="college_apps_total"]').val() || 0;
        return Number(diagnostic_total) + Number(adjust_total) + Number(tp_total) + Number(college_apps_total);
    }


    function setDefaultInstallmentDate() {
        default_installment_date = (default_tp_date > default_college_apps_date) ? default_tp_date : default_college_apps_date
    }


    $('input[name="turn_on_installments"]').on('click', function() {

        if ($(this).val() == "") {
            setDefaultInstallmentDate();
            $('input[name="mark_as_paid"]').prop('checked', false);
            $('input[name="mark_as_paid"]').val("");

            $(this).val("yes");
        } else {

            $(this).val("");
        }
    });


    $('input[name="mark_as_paid"]').on('click', function() {


        if ($(this).val() == "") {

            $('input[name="turn_on_installments"]').prop('checked', false);

            $('input[name="send_text_and_email"]').prop('checked', false);
            $('input[name="send_text_and_email"]').val("");

            $(this).val("yes");
        } else {

            setDefaultInstallmentDate();

            $(this).val("");
        }
    });



    $('input[name="send_text_and_email"]').on('click', function() {
        if ($(this).val() == "") {

        $('input[name="mark_as_paid"]').prop('checked', false);
            $('input[name="mark_as_paid"]').val("");

            $(this).val("yes");
        } else {
            $(this).val("");
        }
    });

     $('input[name="ask_for_student_info"]').on('click', function() {
        if ($(this).val() == "") {
            $(this).val("yes");
        } else {
            $(this).val("");
        }
    });


// add and delete rows



    $("#addrow").on("click", function () {

    var counter = $('input[name="installment_counter"]').val();

    alert(counter);

    if (Number(counter) < 12)
{
        document.getElementById("more_than_12_installments_message").hidden=true;

        var newRow = $("<tr>");
        var cols = "";




        cols += '<td><input type="date" class="form-control" name="date_' + counter + '" required/></td>';
        cols += '<td><input type="number" class="form-control installment_amounts" min="1" name="amount_' + counter + '" required/></td>';

        cols += '<td><input type="button" id="ibtnDel" class="ibtnDel btn btn-md btn-danger "  value="Delete"></td>';
        //add </tr> to last col ? no, because that is how jquery works?
        newRow.append(cols);
        $("table.order-list").append(newRow);
        var today = new Date().toISOString().split('T')[0];
        document.getElementsByName("date_"+counter )[0].setAttribute('min', today);
        counter++;
        $('input[name="installment_counter"]').val(counter);
        //client-side counter is always one more; actual number has been set server-side
        }
        else
        {

        document.getElementById("more_than_12_installments_message").hidden=false;

        }

    });



    $("table.order-list").on("click", ".ibtnDel", function (event) {
    var counter = $('input[name="installment_counter"]').val();
        $(this).closest("tr").remove();
        counter--;
        $('input[name="installment_counter"]').val(counter);
        if (Number(counter) == 1)
        {
        document.getElementById("installment_not_equal_total_message_1").hidden=true;
        document.getElementById("installment_not_equal_total_message_2").hidden=true;
            $('input[name="create_transaction_button"]').attr('disabled', false);
             $('input[name="modify_transaction_button"]').attr('disabled', false);
        }
        //client-side counter is always one more; actual number has been set server-side
    });

     $("table.order-list").on('input', ".installment_amounts", function() {

     var installment_total = 0;
     var amount = '';
      var counter = $('input[name="installment_counter"]').val();

     for (let k = 1; k < counter; k++) {

     amount = 'amount_'.concat(k);
     	installment_total = Number(installment_total) +  Number($("input[name="+amount+"]").val());
		}

		 if (installment_total != transactionTotal()) {
		 document.getElementById("installment_not_equal_total_message_1").hidden=false;
            $('input[name="create_transaction_button"]').attr('disabled', true);

            document.getElementById("installment_not_equal_total_message_2").hidden=false;
            $('input[name="modify_transaction_button"]').attr('disabled', true);
        }
        else{
        document.getElementById("installment_not_equal_total_message_1").hidden=true;
            $('input[name="create_transaction_button"]').attr('disabled', false);

             document.getElementById("installment_not_equal_total_message_2").hidden=true;
            $('input[name="modify_transaction_button"]').attr('disabled', false);
        }

    });

});