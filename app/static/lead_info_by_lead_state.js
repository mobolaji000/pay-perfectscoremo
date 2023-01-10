$(document).ready(function() {

    //find detials of hos this works here: https://bbbootstrap.com/snippets/multiselect-dropdown-list-83601849
    var choicesForWhatServiceLeadIsInterestedIn = new Choices('#what_services_are_you_interested_in', {
        removeItemButton: true,
        // maxItemCount:5,
        // searchResultLimit:5,
        // renderChoiceLimit:5
      });

    $('#what_services_are_you_interested_in').data('choices', choicesForWhatServiceLeadIsInterestedIn);

});