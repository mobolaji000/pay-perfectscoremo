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
    $('input[name="invoice_total"]').attr('disabled', true);

    $('input[name="installment_date_1"]').attr('disabled', true);
    $('input[name="installment_date_2"]').attr('disabled', true);
    $('input[name="installment_date_3"]').attr('disabled', true);

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
            $('input[name="invoice_total"]').val(invoiceTotal());


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

    });

    $('input[name="diag_units"]').on('input', function() {
        $('input[name="diag_total"]').val(calculateDiagnosticTotal());
        $('input[name="invoice_total"]').val(invoiceTotal());
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
    });

    $('input[name="tp_product"]').change(function() {
        $('input[name="tp_total"]').val(calculateTestPrepTotal());
        $('input[name="invoice_total"]').val(invoiceTotal());
    });

    $('input[name="tp_units"]').on('input', function() {
        $('input[name="tp_total"]').val(calculateTestPrepTotal());
        $('input[name="invoice_total"]').val(invoiceTotal());
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
    });

    $('input[name="college_consultation"]').change(function() {
        $('input[name="college_apps_total"]').val(collegeAppsTotal());
        $('input[name="invoice_total"]').val(invoiceTotal());
    });

    $('input[name="college_apps_product"]').change(function() {
        $('input[name="college_apps_total"]').val(collegeAppsTotal());
        $('input[name="invoice_total"]').val(invoiceTotal());
        $('input[name="college_apps_units"]').attr('min', 1);
    });

    $('input[name="college_apps_units"]').on('input', function() {
        $('input[name="college_apps_total"]').val(collegeAppsTotal());
        $('input[name="invoice_total"]').val(invoiceTotal());
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
        $('input[name="invoice_total"]').val(invoiceTotal());
    });

    function invoiceTotal() {
        var diagnostic_total = $('input[name="diag_total"]').val() || 0;
        var adjust_total = $('input[name="adjust_total"]').val() || 0;
        var tp_total = $('input[name="tp_total"]').val() || 0;
        var college_apps_total = $('input[name="college_apps_total"]').val() || 0;
        return Number(diagnostic_total) + Number(adjust_total) + Number(tp_total) + Number(college_apps_total);
    }

    //    $('input[name="turn_on_installments"]','input[name="tp_products"]','input[name="college_apps_products"]').on('click', function() {
    //
    //    default_installment_date = (default_tp_date > default_college_apps_date) ? default_tp_date : default_college_apps_date
    //
    //    if ($('input[name="turn_on_installments"]').val() == "") {
    //            $('input[name="installment_date_1"]').val(default_installment_date);
    //        }
    //    }


    function setDefaultInstallmentDate() {
        default_installment_date = (default_tp_date > default_college_apps_date) ? default_tp_date : default_college_apps_date
        $('input[name="installment_date_1"]').val(default_installment_date);
    }


    $('input[name="turn_on_installments"]').on('click', function() {

        //default_installment_date = (default_tp_date > default_college_apps_date) ? default_tp_date : default_college_apps_date
        if ($(this).val() == "") {
            setDefaultInstallmentDate();
            //$('input[name="installment_date_1"]').val(default_installment_date);

            $('input[name="installment_date_1"]').attr('disabled', false);
            $('input[name="installment_date_2"]').attr('disabled', false);
            $('input[name="installment_date_3"]').attr('disabled', false);
            $(this).val("yes");
        } else {
            $('input[name="installment_date_1"]').attr('disabled', true);
            $('input[name="installment_date_2"]').attr('disabled', true);
            $('input[name="installment_date_3"]').attr('disabled', true);

            $('input[name="installment_date_1"]').val("");
            $('input[name="installment_date_2"]').val("");
            $('input[name="installment_date_3"]').val("");

            $(this).val("");
        }
    });




});