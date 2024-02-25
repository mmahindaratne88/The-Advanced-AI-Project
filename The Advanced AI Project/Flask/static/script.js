// static/script.js

// Purpose: This JavaScript code is designed to prevent the user from navigating away
// from the current page using the browser's back button. It achieves this by
// manipulating the browser history using the pushState method.

// Action on page load: Set up an event listener for the window.onload event.
window.onload = function () {
  // Manipulate the browser history by adding a new state with null data and an empty title.
  window.history.pushState(null, "", window.location.href);

  // Set up an event listener for the window.onpopstate event, which is triggered
  // when the user navigates using the browser's back or forward buttons.
  window.onpopstate = function () {
    // Ensure that the current state is maintained by pushing a new state
    // with null data and an empty title.
    window.history.pushState(null, "", window.location.href);
  };
};

