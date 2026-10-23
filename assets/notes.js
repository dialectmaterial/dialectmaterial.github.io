// Footnotes open where they're cited, only when the reader clicks the number.
// On wide screens the note appears in the right margin beside its line; on
// narrower screens it opens under the paragraph. Click again (or ×) to close.
// The full list stays at the end either way.
(function () {
  var prose = document.querySelector(".prose");
  if (!prose) return;
  var refs = Array.prototype.slice.call(prose.querySelectorAll("a.footnote"));
  if (!refs.length) return;
  var wide = matchMedia("(min-width: 1360px)");
  var open = [];  // {ref, el}

  function noteHTML(ref) {
    var li = document.getElementById(decodeURIComponent(ref.hash.slice(1)));
    if (!li) return null;
    var copy = li.cloneNode(true);
    copy.querySelectorAll(".reversefootnote, .embed, iframe").forEach(function (el) { el.remove(); });
    return copy.innerHTML;
  }

  function close(item) {
    item.el.remove();
    item.ref.setAttribute("aria-expanded", "false");
    open = open.filter(function (o) { return o !== item; });
    layout();
  }

  function build(ref, html) {
    var el;
    if (wide.matches) {
      el = document.createElement("aside");
      el.className = "sidenote";
      el.innerHTML = '<span class="n">' + ref.textContent + "</span>" + html;
      prose.appendChild(el);
    } else {
      el = document.createElement("span");
      el.className = "fn-pop";
      el.innerHTML = html.replace(/<\/?p>/g, " ");
      ref.parentNode.after(el);
    }
    el.setAttribute("role", "note");
    var x = document.createElement("button");
    x.type = "button"; x.className = "fn-close"; x.setAttribute("aria-label", "Close note"); x.textContent = "×";
    el.appendChild(x);
    var item = { ref: ref, el: el };
    x.addEventListener("click", function () { close(item); ref.focus(); });
    return item;
  }

  // Margin notes sit level with their line, below any earlier open note,
  // and never over a wide picture.
  function layout() {
    if (!wide.matches) return;
    var base = prose.getBoundingClientRect().top;
    var blocks = Array.prototype.map.call(prose.querySelectorAll("figure, .embed"), function (el) {
      var r = el.getBoundingClientRect();
      return { top: r.top - base, bottom: r.bottom - base };
    });
    var floor = 0;
    open.slice().sort(function (a, b) { return refs.indexOf(a.ref) - refs.indexOf(b.ref); }).forEach(function (o) {
      var top = Math.max(o.ref.getBoundingClientRect().top - base - 4, floor);
      var h = o.el.offsetHeight;
      blocks.forEach(function (b) { if (top < b.bottom && top + h > b.top) top = b.bottom + 12; });
      o.el.style.top = top + "px";
      floor = top + h + 14;
    });
  }

  refs.forEach(function (ref) {
    ref.setAttribute("aria-expanded", "false");
    ref.addEventListener("click", function (e) {
      var html = noteHTML(ref);
      if (!html) return;
      e.preventDefault();
      var already = open.filter(function (o) { return o.ref === ref; })[0];
      if (already) { close(already); return; }
      open.push(build(ref, html));
      ref.setAttribute("aria-expanded", "true");
      layout();
    });
  });

  // Switching between wide and narrow closes everything, so nothing is left in the wrong place.
  wide.addEventListener("change", function () { open.slice().forEach(close); });
  if (window.ResizeObserver) new ResizeObserver(layout).observe(prose);
})();
