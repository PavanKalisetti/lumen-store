var CONTAINER_ID = "reviews";
var STATUS_ID = "reviews-status";
var REFERENCE_ID = "render-reference";
var TELEMETRY_URL = "/api/storefront/render-receipt";

function reviewsContainer() {
  return document.getElementById(CONTAINER_ID);
}

function setStatus(text) {
  var status = document.getElementById(STATUS_ID);
  if (status) {
    status.textContent = text;
  }
}

async function loadReviews(slug) {
  var response = await fetch("/api/products/" + encodeURIComponent(slug) + "/reviews", {
    headers: { Accept: "application/json" }
  });
  if (!response.ok) {
    throw new Error("reviews unavailable");
  }
  return response.json();
}

function renderReviews(payload) {
  var container = reviewsContainer();
  if (!container) {
    return 0;
  }
  container.innerHTML = "";
  var fragments = payload.html_fragments || [];
  fragments.forEach(function (fragment) {
    container.insertAdjacentHTML("beforeend", fragment);
  });
  if (!fragments.length) {
    container.insertAdjacentHTML("beforeend", '<p class="muted">No reviews yet.</p>');
  }
  return fragments.length;
}

function summarise(payload) {
  if (!payload.count) {
    return "No reviews yet.";
  }
  var label = payload.count === 1 ? "review" : "reviews";
  return payload.count + " " + label + " · average " + payload.average + " of 5";
}

function writeReference(reference) {
  var container = reviewsContainer();
  var slot = document.getElementById(REFERENCE_ID);
  if (!slot && container) {
    container.insertAdjacentHTML(
      "beforeend",
      '<p class="byline">Render <span id="' + REFERENCE_ID + '"></span></p>'
    );
    slot = document.getElementById(REFERENCE_ID);
  }
  if (slot) {
    slot.textContent = reference || "";
  }
}

async function recordRender() {
  var response = await fetch(TELEMETRY_URL, {
    headers: { "X-Render-Complete": "1", Accept: "application/json" }
  });
  if (!response.ok) {
    return;
  }
  var data = await response.json();
  writeReference(data.reference);
}

async function refresh(slug) {
  try {
    var payload = await loadReviews(slug);
    var rendered = renderReviews(payload);
    setStatus(summarise(payload));
    if (rendered > 0) {
      await recordRender();
    }
  } catch (error) {
    setStatus("Reviews could not be loaded.");
  }
}

async function submitReview(slug, form) {
  var data = new FormData(form);
  var response = await fetch("/api/products/" + encodeURIComponent(slug) + "/reviews", {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "application/json" },
    body: JSON.stringify({
      author: data.get("author") || "",
      rating: Number(data.get("rating") || 5),
      body: data.get("body") || ""
    })
  });
  if (!response.ok) {
    setStatus("That review could not be posted.");
    return;
  }
  form.reset();
  await refresh(slug);
}

function init() {
  var container = reviewsContainer();
  if (!container) {
    return;
  }
  var slug = container.dataset.slug;
  if (!slug) {
    return;
  }
  var form = document.getElementById("review-form");
  if (form) {
    form.addEventListener("submit", function (event) {
      event.preventDefault();
      submitReview(slug, form);
    });
  }
  refresh(slug);
}

document.addEventListener("DOMContentLoaded", init);
