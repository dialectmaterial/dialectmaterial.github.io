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
    var esc = s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
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

    // A video taken off the page keeps playing its sound unless it is stopped first.
    track.querySelectorAll("video").forEach(function (v) { v.pause(); v.removeAttribute("src"); v.load(); });
    track.innerHTML = "";
    dots.innerHTML = "";
    p.media.forEach(function (m, k) {
      var slide = document.createElement("div");
      slide.className = "slide";
      if (m.type === "video") {
        slide.appendChild(makeVideo(m));
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
    syncVideos();

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
  track.addEventListener("scrollend", syncVideos);
  var settle;
  track.addEventListener("scroll", function () { clearTimeout(settle); settle = setTimeout(syncVideos, 150); }, { passive: true });

  // ---------- Video, played the way reels are: muted and looping as soon as it is
  // on screen; tap to pause, the speaker button for sound (remembered between posts).
  var soundOn = false;
  var ICON_MUTED = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 9h4l5-4v14l-5-4H4z" fill="currentColor"/><path d="M16.5 9.5l5 5M21.5 9.5l-5 5" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>';
  var ICON_SOUND = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 9h4l5-4v14l-5-4H4z" fill="currentColor"/><path d="M16.5 8.5a5 5 0 0 1 0 7M19 6a8.5 8.5 0 0 1 0 12" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>';

  function makeVideo(m) {
    var box = document.createElement("div");
    box.className = "vid paused";
    var v = document.createElement("video");
    v.src = m.src; v.poster = m.poster || m.thumb || "";
    v.muted = !soundOn; v.loop = true; v.playsInline = true; v.preload = "metadata";
    v.setAttribute("playsinline", "");
    var big = document.createElement("span");
    big.className = "vid-play";
    big.innerHTML = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M8 5.5v13l10.5-6.5z" fill="currentColor"/></svg>';
    var sound = document.createElement("button");
    sound.type = "button"; sound.className = "vid-sound";
    var bar = document.createElement("div");
    bar.className = "vid-bar";
    bar.innerHTML = "<i></i>";
    function paintSound() {
      sound.innerHTML = v.muted ? ICON_MUTED : ICON_SOUND;
      sound.setAttribute("aria-label", v.muted ? "Turn sound on" : "Turn sound off");
    }
    paintSound();
    v.addEventListener("click", function () { if (v.paused) v.play().catch(function () {}); else v.pause(); });
    v.addEventListener("play", function () { box.classList.remove("paused"); });
    v.addEventListener("pause", function () { box.classList.add("paused"); });
    v.addEventListener("volumechange", paintSound);
    v.addEventListener("timeupdate", function () {
      if (v.duration) bar.firstChild.style.width = (100 * v.currentTime / v.duration) + "%";
    });
    sound.addEventListener("click", function (e) {
      e.stopPropagation();
      soundOn = v.muted;
      v.muted = !soundOn;
      if (v.paused) v.play().catch(function () {});
    });
    bar.addEventListener("click", function (e) {
      var r = bar.getBoundingClientRect();
      if (v.duration) v.currentTime = v.duration * Math.min(1, Math.max(0, (e.clientX - r.left) / r.width));
    });
    big.addEventListener("click", function () { v.play().catch(function () {}); });
    box.appendChild(v); box.appendChild(big); box.appendChild(sound); box.appendChild(bar);
    return box;
  }

  // Play the video on the slide in view, pause every other one.
  function syncVideos() {
    var k = slideIndex();
    Array.prototype.forEach.call(track.children, function (slide, j) {
      var v = slide.querySelector("video");
      if (!v) return;
      if (j === k && !modal.hidden) {
        v.muted = !soundOn;
        v.play().catch(function () {
          // Sound needs a tap first on some browsers: start muted instead.
          v.muted = true;
          v.play().catch(function () {});
        });
      } else {
        v.pause();
      }
    });
  }
  function currentVideo() {
    var slide = track.children[slideIndex()];
    return slide && slide.querySelector("video");
  }
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
    var v = currentVideo();
    if (e.key === "Tab") {
      // Keep keyboard focus inside the open post.
      var f = Array.prototype.filter.call(modal.querySelectorAll("button, a[href], video"), function (el) { return !el.hidden && el.offsetParent !== null; });
      if (!f.length) return;
      var a = f[0], z = f[f.length - 1];
      if (e.shiftKey && (document.activeElement === a || document.activeElement === post)) { e.preventDefault(); z.focus(); }
      else if (!e.shiftKey && document.activeElement === z) { e.preventDefault(); a.focus(); }
      else if (!modal.contains(document.activeElement)) { e.preventDefault(); a.focus(); }
    }
    else if (e.key === "Escape") close();
    else if (v && (e.key === " " || e.key === "k")) { e.preventDefault(); if (v.paused) v.play().catch(function () {}); else v.pause(); }
    else if (v && e.key === "m") { soundOn = v.muted; v.muted = !soundOn; }
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

  // Light and dark: follows the phone unless the reader picks one (remembered).
  document.querySelector(".bar-theme").addEventListener("click", function () {
    var root = document.documentElement;
    var dark = root.dataset.theme ? root.dataset.theme === "dark" : matchMedia("(prefers-color-scheme: dark)").matches;
    root.dataset.theme = dark ? "light" : "dark";
    try { localStorage.setItem("theme", root.dataset.theme); } catch (e) {}
  });

  fromHash();
})();
