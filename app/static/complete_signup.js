$(document).ready(function() {

  var selected_cards = {};

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


//////////////////////////////////////////////////////////////////////////////////////////////////////////////////


    $('#installment-payment-options').on('click', function() {

     $('#installment-payment-div').attr('style', 'display: block !important');
        $('#full-payment-div').attr('style', 'display: none !important');

        $('input[name="full-payment"]').prop('required', false);
        $('input[name="full-payment"]').attr('disabled', true);
        $('input[name="installment-payment"]').attr('disabled', false);

        $("#installment-payment-div").detach().appendTo('#holding-div');
        $("#installment-payment-div").show();
        $("#installment-payment-div").css("visibility", "visible");

    var show_ach_override = $("#show_ach_override").attr("data-show_ach_override");

    if (show_ach_override === 'True')
    {
    $('#selectorToHideACHInstallment').attr('style', 'display: block !important');
        $("#selectorToHideACHInstallment").show();
        $("#selectorToHideACHInstallment").css("visibility", "visible");
    }
    else
    {
    $('#selectorToHideACHInstallment').attr('style', 'display: none !important');
    $("#selectorToHideACHInstallment").css("visibility", "hidden");
    }

    });



    //////////////////////////////////////////////////////////////////////////////////////////////////////////////////



       // Example starter JavaScript for disabling form submissions if there are invalid fields
  // Example starter JavaScript for disabling form submissions if there are invalid fields
  (function () {
    'use strict'

    // Fetch all the forms we want to apply custom Bootstrap validation styles to
    var forms = document.querySelectorAll('#complete_signup_form')

    // Loop over them and prevent submission
    Array.prototype.slice.call(forms)
      .forEach(
      function (form) {
        form.addEventListener('submit', function (event) {
          if (!checkValidity()) {
          alert('Some fields contain errors. Try again.');
            event.preventDefault()
            event.stopPropagation()
          }
          else{
          //alert('Remember that your student information and choice of days for one-on-one will not be processed until you make a payment on the next page.');
           var form=document.getElementById('complete_signup_form');//retrieve the form as a DOM element
      var input = document.createElement('input');//prepare a new input DOM element
      input.setAttribute('name', 'all_days_for_one_on_one');//set the param name
      input.setAttribute('value', JSON.stringify(selected_cards));//set the value
      input.setAttribute('type', 'hidden');//set the type, like "hidden" or other
      form.appendChild(input);//append the input to the form

          }

          //form.classList.add('was-validated')


          function checkValidity() {
        var student_info_present = false;
        var parent_info_distinct = false;
        var one_on_one_info_present = false;

        var ask_for_student_info = $("#ask_for_student_info").attr("data-ask_for_student_info");
        var ask_for_student_availability = $("#ask_for_student_availability").attr("data-ask_for_student_availability");



//check if onboarding info was selected
        if (ask_for_student_availability == 'yes')
        {
            for(var key in selected_cards) {
    if(selected_cards[key] != "")
    {
         one_on_one_info_present = true;
         break;
    }
 }


 if(one_on_one_info_present)
 {
  document.getElementById('day_for_one_on_one_info_and_error').style.color="green";
  document.getElementById('day_for_one_on_one_info_and_error').innerHTML="Select as many options as work for you by clicking the cards.";
 }
 else
 {
         document.getElementById('day_for_one_on_one_info_and_error').innerHTML="You must select at least one option for your one-on-one session.";
         document.getElementById('day_for_one_on_one_info_and_error').style.color="red";
 }
        }

        if (ask_for_student_info == 'yes')
        {
        var student_first_name = $("#student_first_name").val();
        var student_last_name = $("#student_last_name").val();
        var student_email = $("#student_email").val();
        var student_phone_number = $("#student_phone_number").val();
        var parent_1_phone_number = $("#parent_1_phone_number").val();
        var parent_2_phone_number = $("#parent_2_phone_number").val();

        //var cards = document.getElementsByName('day_for_one_on_one');

 //check if parent info duplicates student info


 if ((parent_1_phone_number == '' && parent_2_phone_number == '') || (((parent_1_phone_number.length == 10 && parent_2_phone_number.length == 10) || (parent_1_phone_number.length == 10 && parent_2_phone_number.length == 0) || (parent_1_phone_number.length == 0 && parent_2_phone_number.length == 10)) && parent_1_phone_number != parent_2_phone_number && student_phone_number != parent_1_phone_number && student_phone_number != parent_2_phone_number))
    {
    document.getElementById('parent_1_info_error_message').style.visibility="hidden";
     document.getElementById('parent_1_info_error_message').style.display="none";
     document.getElementById("parent_1_info_error_message").hidden=true;

     document.getElementById('parent_2_info_error_message').style.visibility="hidden";
     document.getElementById('parent_2_info_error_message').style.display="none";
     document.getElementById("parent_2_info_error_message").hidden=true;

    parent_info_distinct = true;
    }
    else
    {

       document.getElementById('parent_1_info_error_message').style.visibility="visible";
             document.getElementById('parent_1_info_error_message').style.display="block";
             document.getElementById("parent_1_info_error_message").hidden=false;
             document.getElementById('parent_1_info_error_message').style.color="red";

              document.getElementById('parent_2_info_error_message').style.visibility="visible";
             document.getElementById('parent_2_info_error_message').style.display="block";
             document.getElementById("parent_2_info_error_message").hidden=false;
             document.getElementById('parent_2_info_error_message').style.color="red";

             parent_info_distinct = false;
   }


//check if student info is missing

   if (student_first_name != '' && student_last_name != '' && student_email != '' && student_phone_number != '')
    {
     document.getElementById('student_info_error_message').style.visibility="hidden";
     document.getElementById('student_info_error_message').style.display="none";
     document.getElementById("student_info_error_message").hidden=true;
    student_info_present = true;

    }
    else
    {
              document.getElementById('student_info_error_message').style.visibility="visible";
             document.getElementById('student_info_error_message').style.display="block";
             document.getElementById("student_info_error_message").hidden=false;
             document.getElementById('student_info_error_message').style.color="red";
            student_info_present = false;
   }

         return student_info_present && parent_info_distinct && one_on_one_info_present;
      }
      else
      {
      return true;
      }
      }



        }, false)

        })
    })();



    //////////////////////////////////////////////////////////////////////////////////////////////////////////////////



  (function () {
    'use strict'

    // Fetch all the forms we want to apply custom Bootstrap validation styles to
    var cards = document.getElementsByName('day_for_one_on_one');


    // Loop over them and prevent submission
    Array.prototype.slice.call(cards)
      .forEach(function (card) {
        card.addEventListener('click', function (event) {
         var backgroundColor = window.getComputedStyle(card).getPropertyValue("background-color");

        function nameToRGB(name) {
    // Create fake div
    let fakeDiv = document.createElement("div");
    fakeDiv.style.color = name;
    document.body.appendChild(fakeDiv);

    // Get color of div
    let cs = window.getComputedStyle(fakeDiv),
        pv = cs.getPropertyValue("color");

    // Remove div after obtaining desired color value
    document.body.removeChild(fakeDiv);

    return pv;
  }
        if(backgroundColor == nameToRGB('white')){
          card.style.setProperty("background-color", 'LightGreen', 'important');
          selected_cards[card.textContent] = card.textContent.replace(/(\r\n|\n|\r)/gm,"");
        }
        else if (backgroundColor == nameToRGB('LightGreen')){
          //card.style.backgroundColor == 'white'
          card.style.setProperty("background-color", 'white', 'important');
          selected_cards[card.textContent] = '';
        }
          //form.classList.add('was-validated')
        })
      })

    })();


  //////////////////////////////////////////////////////////////////////////////////////////////////////////////////


 var form=document.getElementById('complete_signup_form');//retrieve the form as a DOM element
      var stripe_info = $("#stripe_info").attr("data-stripe_info");
      var input = document.createElement('input');//prepare a new input DOM element
      input.setAttribute('name', 'stripe_info');//set the param name
      input.setAttribute('value', stripe_info);//set the value
      input.setAttribute('type', 'hidden');//set the type, like "hidden" or other
      form.appendChild(input);//append the input to the form

});