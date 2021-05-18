$(document).ready(function() {

//var stripe = Stripe('pk_test_51Hlgy6DbpRMio7qjWV9YNuBPiQIgD6PrBwO7oek37OEafhZiRjkfs42owvLto0eO8c6CCaiSAOUrXn0uPEJdai6Z00DUYXi551');
var stripe = Stripe('pk_live_51Hlgy6DbpRMio7qjB3uZkis2sPMKb6HmXUI8k5PNKvYgOK1jv2XfzqG5fNaRbEO68wJ7VaXXvISCKIF7Yj2rT01t00GFzi1FkX');

var elements = stripe.elements();
var stripe_info = $("#stripe_info").attr("data-stripe_info");
var chosen_mode_of_payment = $("#chosen_mode_of_payment").attr("data-chosen_mode_of_payment");

var card = elements.create('card', {
hidePostalCode: false,
style: {
 base: {
  iconColor: '#666EE8',
  color: '#fcd669',
  lineHeight: '40px',
  fontWeight: 300,
  fontFamily: '"Helvetica Neue", Helvetica, sans-serif',
  fontSize: '15px',

  '::placeholder': {
    color: '#CFD7E0',
   },
  },
 }
});

card.mount("#card-element");

card.on('change', ({error}) => {
  let displayError = document.getElementById('card-errors');
  if (error) {
    displayError.textContent = error.message;
  } else {
    displayError.textContent = '';
  }
});


var form = document.getElementById('payment-form');

form.addEventListener('submit', function(ev) {
  ev.preventDefault();
  var result = '';

    $('#submit').attr('style', 'display: none !important');
    $('#spinner').attr('style', 'display: inline-block !important');





  $.ajax({
    url: '/setup_payment_intent',
    type: "POST",
    data: {
        chosen_mode_of_payment: chosen_mode_of_payment,
        stripe_info: stripe_info,
    },
    dataType: "json",
    async: false,
    success: function (data) {

var cardholderName = document.getElementById('name');
var clientSecret = data.client_secret;
var cardElement = document.getElementById('card-element');

 stripe.confirmCardSetup(
    clientSecret,
    {
      payment_method: {
        card: card,
        billing_details: {
          name: cardholderName.value,
        },
      },
    }
  ).then(function(result) {
    if (result.error) {
    console.log(result.error.message);
    } else {
      var payment_id = result.setupIntent.payment_method;

        $.ajax({
    url: '/execute_card_payment',
    type: "POST",
    data: {
        chosen_mode_of_payment: chosen_mode_of_payment,
        stripe_info: stripe_info,
        payment_id: payment_id,
    },
    dataType: "json",
    async: false,
    success: function (result) {
    if(result.status == 'failure'){
        location.reload();
        return false;
    }
    else
    {
        window.location.href ="/success";
    }
    },
    error: function (error) {
    window.location.href ="/failure";
        console.log(error);
    }
});

    }
  });
    },
    error: function (error) {
        console.log(error);
    }
});

});

});