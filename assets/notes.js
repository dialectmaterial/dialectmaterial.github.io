// Footnotes beside the text. On wide screens each note sits in the right
// margin next to the line that cites it; on narrower screens tapping the
// number opens the note in place. The full list stays at the end either way.
(function () {
  var prose = document.querySelector(".prose");
  if (!prose) return;
  var refs = Array.prototype.slice.call(prose.querySelectorAll("a.footnote"));
  if (!refs.length) return;
  var wide = matchMedia("(min-width: 1320px)");

  function noteHTML(ref) {
    var li = document.getElementById(decodeURIComponent(ref.hash.slice(1)));
    if (!li) return null;
    var copy = li.cloneNode(true);
    copy.querySelectorAll(".reversefootnote, .embed, iframe").forEach(function (el) { el.remove(); });
    return copy.innerHTML;
  }

  // Margin notes
  var side = [];
  refs.forEach(function (ref) {
    var html = noteHTML(ref);
    if (!html) return;
    var note = document.createElement("aside");
    note.className = "sidenote";
    note.innerHTML = '<span class="n">' + ref.textContent + "</span>" + html;
    note.hidden = true;
    prose.appendChild(note);
    side.push({ ref: ref, note: note });
  });

  function layout() {
    var on = wide.matches;
    prose.classList.toggle("has-sidenotes", on);
    side.forEach(function (s) { s.note.hidden = !on; });
    if (!on) return;
    var base = prose.getBoundingClientRect().top;
    // Wide figures reach into the margin: notes go below them, never over them.
    var blocks = Array.prototype.map.call(prose.querySelectorAll("figure, .embed, .footnotes"), function (el) {
      var r = el.getBoundingClientRect();
      return { top: r.top - base, bottom: r.bottom - base };
    });
    var floor = 0;
    side.forEach(function (s) {
      var top = Math.max(s.ref.getBoundingClientRect().top - base - 4, floor);
      var h = s.note.offsetHeight;
      blocks.forEach(function (b) { if (top < b.bottom && top + h > b.top) top = b.bottom + 12; });
      s.note.style.top = top + "px";
      floor = top + h + 14;
    });
  }

  // Tap-to-open notes
  refs.forEach(function (ref) {
    ref.addEventListener("click", function (e) {
      if (wide.matches) return;
      var html = noteHTML(ref);
      if (!html) return;
      e.preventDefault();
      var sup = ref.parentNode;
      var open = sup.nextElementSibling;
      if (open && open.classList.contains("fn-pop")) { open.remove(); ref.setAttribute("aria-expanded", "false"); return; }
      var pop = document.createElement("span");
      pop.className = "fn-pop";
      pop.setAttribute("role", "note");
      pop.innerHTML = html.replace(/<\/?p>/g, " ") +
        '<button type="button" class="fn-close" aria-label="Close note">×</button>';
      pop.querySelector(".fn-close").addEventListener("click", function () {
        pop.remove(); ref.setAttribute("aria-expanded", "false"); ref.focus();
      });
      sup.after(pop);
      ref.setAttribute("aria-expanded", "true");
    });
  });

  layout();
  wide.addEventListener("change", layout);
  if (window.ResizeObserver) new ResizeObserver(layout).observe(prose);
  window.addEventListener("load", layout);
})();
