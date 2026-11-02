// /insta/: tabs, and the post viewer. A post opens at #p-<id>, so the back
// button closes it and every post has its own link.
(function () {
  var posts = JSON.parse(document.getElementById("insta-data").textContent);
  var byId = {};
  posts.forEach(function (p, i) { byId[p.id] = i; });

  var modal = document.querySelector(".modal");
  var post = modal.querySelector(".post");
  var track = modal.querySelector(".track");
  var dots = modal.querySelector(".dots");
  var left = modal.querySelector(".step.left"), right = modal.querySelector(".step.right");
  var prev = modal.querySelector(".nav.prev"), next = modal.querySelector(".nav.next");
  var text = modal.querySelector(".caption .text");
  var when = modal.querySelector(".when");
  var share = modal.querySelector(".share span");
  var tiles = Array.prototype.slice.call(document.querySelectorAll(".tile"));
  var current = -1, lastFocus = null;

  // Which posts the arrows move between: the ones visible under the current tab.
  function visible() {
    return tiles.filter(function (t) { return !t.hidden; }).map(function (t) { return byId[t.dataset.id]; });
  }

  function captionHTML(s) {
    var esc = s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
    return esc
      .replace(/(https?:\/\/[^\s<]+)/g, '<a href="$1" rel="noopener">$1</a>')
      .replace(/(^|\s)(#[\p{L}\p{N}_]+)/gu, '$1<span class="tag">$2</span>')
      .replace(/(^|\s)@([A-Za-z0-9_.]+)/g, '$1<a href="https://www.instagram.com/$2/" rel="noopener">@$2</a>');
  }

  function render(i) {
    var p = posts[i];
    current = i;
    var first = p.media[0];
    var r = first.width && first.height ? first.width / first.height : 1;
    post.style.setProperty("--r", Math.min(1.91, Math.max(0.8, r)).toFixed(4));

    track.innerHTML = "";
    dots.innerHTML = "";
    p.media.forEach(function (m, k) {
      var slide = document.createElement("div");
      slide.className = "slide";
      if (m.type === "video") {
        var v = document.createElement("video");
        v.src = m.src; v.poster = m.poster || m.thumb || ""; v.controls = true; v.playsInline = true; v.preload = "metadata";
        slide.appendChild(v);
      } else {
        var img = document.createElement("img");
        img.src = m.src; img.alt = ""; img.decoding = "async";
        if (k > 0) img.loading = "lazy";
        slide.appendChild(img);
      }
      track.appendChild(slide);
      if (p.media.length > 1) dots.appendChild(document.createElement("i"));
    });
    track.scrollLeft = 0;
    updateSteps();

    text.innerHTML = captionHTML(p.caption || "");
    var d = new Date(p.date);
    when.dateTime = p.date;
    when.textContent = d.toLocaleDateString("en-GB", { day: "numeric", month: "long", year: "numeric" });
    share.textContent = "Copy link";

    var list = visible(), at = list.indexOf(i);
    prev.hidden = at <= 0;
    next.hidden = at < 0 || at >= list.length - 1;
  }

  function slideIndex() { return track.clientWidth ? Math.round(track.scrollLeft / track.clientWidth) : 0; }
  function updateSteps() {
    var n = track.children.length, k = slideIndex();
    left.hidden = k <= 0;
    right.hidden = k >= n - 1;
    Array.prototype.forEach.call(dots.children, function (d, j) { d.className = j === k ? "on" : ""; });
  }
  track.addEventListener("scroll", function () { window.requestAnimationFrame(updateSteps); }, { passive: true });
  function step(dir) {
    var k = Math.max(0, Math.min(track.children.length - 1, slideIndex() + dir));
    track.scrollTo({ left: k * track.clientWidth, behavior: "smooth" });
  }
  left.addEventListener("click", function () { step(-1); });
  right.addEventListener("click", function () { step(1); });

  function go(dir) {
    var list = visible(), at = list.indexOf(current) + dir;
    if (at >= 0 && at < list.length) location.replace("#p-" + posts[list[at]].id);
  }
  prev.addEventListener("click", function () { go(-1); });
  next.addEventListener("click", function () { go(1); });

  function open(i) {
    if (modal.hidden) {
      lastFocus = document.activeElement;
      modal.hidden = false;
      document.body.classList.add("locked");
    }
    render(i);
    post.setAttribute("tabindex", "-1");
    post.focus({ preventScroll: true });
  }
  function shut() {
    if (modal.hidden) return;
    track.querySelectorAll("video").forEach(function (v) { v.pause(); });
    modal.hidden = true;
    document.body.classList.remove("locked");
    current = -1;
    if (lastFocus) lastFocus.focus({ preventScroll: true });
  }
  function fromHash() {
    var m = location.hash.match(/^#p-(.+)$/);
    if (m && m[1] in byId) open(byId[m[1]]); else shut();
  }
  window.addEventListener("hashchange", fromHash);

  // Closing: go back if we opened the post ourselves, otherwise just clear the hash.
  var openedHere = false;
  tiles.forEach(function (t) { t.addEventListener("click", function () { openedHere = true; }); });
  function close() {
    if (openedHere && history.length > 1) { openedHere = false; history.back(); }
    else history.replaceState(null, "", location.pathname + location.search), shut();
  }
  modal.querySelectorAll("[data-close]").forEach(function (b) { b.addEventListener("click", close); });

  document.addEventListener("keydown", function (e) {
    if (modal.hidden) return;
    if (e.key === "Escape") close();
    else if (e.key === "ArrowLeft") go(-1);
    else if (e.key === "ArrowRight") go(1);
  });

  modal.querySelector(".share").addEventListener("click", function () {
    var url = location.origin + location.pathname + "#p-" + posts[current].id;
    if (navigator.share && matchMedia("(pointer: coarse)").matches) { navigator.share({ url: url }).catch(function () {}); return; }
    navigator.clipboard.writeText(url).then(function () { share.textContent = "Link copied"; });
  });

  // Tabs
  document.querySelectorAll("button.tab").forEach(function (tab) {
    tab.addEventListener("click", function () {
      document.querySelectorAll("button.tab").forEach(function (t) { t.setAttribute("aria-selected", String(t === tab)); });
      var f = tab.dataset.filter;
      tiles.forEach(function (t) { t.hidden = f !== "all" && t.dataset.kind !== f; });
    });
  });

  // Light and dark: follows the phone unless the reader picks one (for this visit).
  document.querySelector(".bar-theme").addEventListener("click", function () {
    var root = document.documentElement;
    var dark = root.dataset.theme ? root.dataset.theme === "dark" : matchMedia("(prefers-color-scheme: dark)").matches;
    root.dataset.theme = dark ? "light" : "dark";
    try { sessionStorage.setItem("theme", root.dataset.theme); } catch (e) {}
  });

  fromHash();
})();
