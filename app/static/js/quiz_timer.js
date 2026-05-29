// Quiz response time tracker
// Sets data-response-time hidden input to (now - questionRenderTime) on form submit.
(function () {
  let questionStart = Date.now();

  function armTimer() {
    questionStart = Date.now();
  }

  document.body.addEventListener("htmx:beforeRequest", function (evt) {
    const form = evt.detail.elt;
    if (!form || !form.matches || !form.matches("[data-quiz-form]")) return;
    const input = form.querySelector("[data-response-time]");
    if (input) {
      input.value = String(Date.now() - questionStart);
    }
  });

  document.body.addEventListener("htmx:afterSwap", armTimer);

  // initial arm on full page load
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", armTimer);
  } else {
    armTimer();
  }
})();
