(function () {
  "use strict";
  var SPA = !!window.KM1_SPA;
  var STORE_KEY = "km1_leads";

  function $(sel, root) { return (root || document).querySelector(sel); }
  function $$(sel, root) { return Array.prototype.slice.call((root || document).querySelectorAll(sel)); }

  /* ---------- Menú móvil ---------- */
  var menuBtn = $(".menu-btn"), nav = $(".main-nav");
  if (menuBtn && nav) {
    menuBtn.addEventListener("click", function () {
      var open = nav.classList.toggle("open");
      menuBtn.setAttribute("aria-expanded", open ? "true" : "false");
    });
    nav.addEventListener("click", function (e) {
      if (e.target.closest("a")) { nav.classList.remove("open"); menuBtn.setAttribute("aria-expanded", "false"); }
    });
  }

  /* ---------- Router (solo vista previa de una sola página) ---------- */
  var pages = $$("main[data-page]");
  function currentPage() { return pages.filter(function (p) { return !p.hidden; })[0] || pages[0]; }
  function show(slug, anchor) {
    var target = pages.filter(function (p) { return p.dataset.page === slug; })[0];
    if (!target) return false;
    pages.forEach(function (p) { p.hidden = p !== target; });
    $$(".main-nav a, .site-footer a").forEach(function (a) {
      if (!a.dataset.nav) return;
      if (a.dataset.nav === slug) a.setAttribute("aria-current", "page"); else a.removeAttribute("aria-current");
    });
    document.title = target.dataset.title || document.title;
    if (anchor) {
      var el = target.querySelector("#" + CSS.escape(anchor));
      if (el) { setTimeout(function () { el.scrollIntoView({ behavior: "smooth" }); }, 30); return true; }
    }
    window.scrollTo(0, 0);
    onPageShown(target);
    return true;
  }
  if (SPA) {
    document.addEventListener("click", function (e) {
      var a = e.target.closest("a[href^='#']");
      if (!a) return;
      var id = a.getAttribute("href").slice(1);
      var anchor = a.dataset.anchor;
      if (pages.some(function (p) { return p.dataset.page === id; })) {
        e.preventDefault();
        if (location.hash !== "#" + id) history.pushState(null, "", "#" + id);
        show(id, anchor);
      } else if (id) {
        var el = currentPage().querySelector("#" + CSS.escape(id));
        if (el) { e.preventDefault(); el.scrollIntoView({ behavior: "smooth" }); }
      }
    });
    window.addEventListener("popstate", function () { show(location.hash.slice(1) || "inicio") || show("inicio"); });
  }

  function onPageShown(root) {
    renderAdmin();
    updateJourneys();
  }

  /* ---------- Recorrido en scroll ---------- */
  function updateJourneys() {
    $$("[data-journey]").forEach(function (j) {
      if (j.offsetParent === null) return;
      var r = j.getBoundingClientRect();
      var vh = window.innerHeight;
      var p = (vh * 0.5 - r.top) / Math.max(r.height, 1);
      p = Math.min(1, Math.max(0, p));
      j.style.setProperty("--p", (p * 100).toFixed(1) + "%");
    });
  }
  window.addEventListener("scroll", updateJourneys, { passive: true });
  window.addEventListener("resize", updateJourneys);

  /* ---------- Etapas del mapa ---------- */
  $$("[data-network]").forEach(function (net) {
    var map = $("[data-map]", net);
    $$(".stage", net).forEach(function (btn) {
      btn.addEventListener("click", function () {
        $$(".stage", net).forEach(function (b) { b.setAttribute("aria-pressed", b === btn ? "true" : "false"); });
        map.setAttribute("data-stage", btn.dataset.stage);
      });
    });
  });

  /* ---------- Prospectos ---------- */
  function loadLeads() {
    try { return JSON.parse(localStorage.getItem(STORE_KEY) || "[]"); } catch (e) { return []; }
  }
  function saveLead(lead) {
    try { var all = loadLeads(); all.unshift(lead); localStorage.setItem(STORE_KEY, JSON.stringify(all)); } catch (e) { /* sin almacenamiento */ }
  }
  function originTag(formEl) {
    var params = new URLSearchParams(location.search);
    var page = SPA ? (currentPage().dataset.page) : (document.body.dataset.page || "web");
    return {
      origen: params.get("utm_source") ? params.get("utm_source") + " / " + (params.get("utm_medium") || "sin medio") : "web directo",
      campana: params.get("utm_campaign") || "",
      pagina: page
    };
  }

  var FREE_MAIL = /@(gmail|hotmail|outlook|yahoo|live|icloud|aol|protonmail)\./i;

  function validateStep(step) {
    var ok = true;
    $$(".field", step).forEach(function (f) {
      var bad = false;
      var group = f.querySelector("[data-require-one]");
      if (group) bad = !group.querySelector("input:checked");
      var inputs = $$("input, select, textarea", f);
      inputs.forEach(function (inp) {
        if (!inp.required) return;
        if (inp.type === "radio") { if (!step.querySelector("input[name='" + inp.name + "']:checked")) bad = true; }
        else if (inp.type === "checkbox") { if (!inp.checked) bad = true; }
        else if (!inp.value.trim()) bad = true;
        else if (inp.type === "email" && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(inp.value.trim())) bad = true;
      });
      f.classList.toggle("invalid", bad);
      if (bad) ok = false;
    });
    if (!ok) {
      var first = step.querySelector(".invalid input, .invalid select, .invalid textarea");
      if (first) first.focus();
    }
    return ok;
  }

  $$("form[data-lead-form]").forEach(function (form) {
    var steps = $$(".form-step", form);
    var idx = 0;
    var bar = $$(".progress > div", form);
    function go(i) {
      idx = i;
      steps.forEach(function (s, n) { s.hidden = n !== i; });
      bar.forEach(function (b, n) { b.className = n < i ? "done" : (n === i ? "active" : ""); });
      var first = steps[i].querySelector("input, select, textarea");
      if (first) first.focus({ preventScroll: true });
      form.closest(".form-card").scrollIntoView({ behavior: "smooth", block: "start" });
    }
    $$("[data-next]", form).forEach(function (b) { b.addEventListener("click", function () { if (validateStep(steps[idx])) go(idx + 1); }); });
    $$("[data-prev]", form).forEach(function (b) { b.addEventListener("click", function () { go(idx - 1); }); });
    form.addEventListener("input", function (e) {
      var f = e.target.closest(".field");
      if (f && f.classList.contains("invalid")) f.classList.remove("invalid");
      if (e.target.matches("[data-corporate]")) {
        var hint = form.querySelector("[data-corp-hint]");
        if (hint) hint.hidden = !FREE_MAIL.test(e.target.value);
      }
    });
    form.addEventListener("change", function (e) {
      var f = e.target.closest(".field");
      if (f) f.classList.remove("invalid");
    });
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      if (!validateStep(steps[idx])) return;
      var data = {};
      new FormData(form).forEach(function (v, k) {
        if (data[k]) data[k] = [].concat(data[k], v); else data[k] = v;
      });
      var seg = form.dataset.leadForm;
      var tag = originTag(form);
      var lead = {
        id: "L" + Date.now(),
        fecha: new Date().toISOString(),
        segmento: seg,
        nombre: data.nombre || "",
        empresa: data.empresa || "",
        tipo: data.tipo || "",
        interes: [].concat(data.interes || []).join(", "),
        capital: data.capital || "",
        ciudad: data.ciudad || "",
        origen: tag.origen,
        pagina: tag.pagina,
        etapa: seg === "inversionista" ? 1 : 0,
        validacion: "Pendiente"
      };
      saveLead(lead);
      var card = form.closest(".form-card");
      form.hidden = true;
      var conf = $("[data-confirm]", card);
      conf.hidden = false;
      var tags = $("[data-tags]", conf);
      if (tags) {
        tags.innerHTML = "";
        ["Segmento: " + seg, "Origen: " + tag.origen, "Página: " + tag.pagina, seg === "inversionista" ? "Etapa: 1 · Registro y perfil" : "Estatus: nuevo"].forEach(function (t) {
          var s = document.createElement("span"); s.textContent = t; tags.appendChild(s);
        });
      }
      conf.setAttribute("tabindex", "-1");
      conf.focus();
      card.scrollIntoView({ behavior: "smooth", block: "start" });
      renderAdmin();
    });
  });

  /* ---------- Panel de prospectos (maqueta) ---------- */
  var SAMPLE = [
    { nombre: "Fondo de Infraestructura (ejemplo)", empresa: "Fondo institucional", segmento: "inversionista", tipo: "Institucional", interes: "Corredor", capital: "Más de 500 M MXN", origen: "linkedin / paid", pagina: "capital", etapa: 4, validacion: "Validado", fecha: "2026-09-28" },
    { nombre: "Ana R. (ejemplo)", empresa: "Grupo patrimonial familiar", segmento: "inversionista", tipo: "Family office", interes: "Paradero individual, Holding", capital: "25 a 100 M MXN", origen: "web directo", pagina: "capital", etapa: 2, validacion: "En revisión", fecha: "2026-10-01" },
    { nombre: "Luis M. (ejemplo)", empresa: "Terreno sobre carretera 45", segmento: "aliado", tipo: "Terreno", interes: "", capital: "", origen: "google / organic", pagina: "paraderos", etapa: 0, validacion: "En revisión", fecha: "2026-10-02" },
    { nombre: "Municipio (ejemplo)", empresa: "Dirección de Desarrollo Económico", segmento: "aliado", tipo: "Municipio", interes: "", capital: "", origen: "web directo", pagina: "paraderos", etapa: 0, validacion: "Pendiente", fecha: "2026-10-03" },
    { nombre: "Carla P. (ejemplo)", empresa: "Inversionista individual", segmento: "inversionista", tipo: "Inversionista individual", interes: "Compra compartida", capital: "Menos de 5 M MXN", origen: "facebook / social", pagina: "capital", etapa: 1, validacion: "Pendiente", fecha: "2026-10-04" },
    { nombre: "Transportes del Bajío (ejemplo)", empresa: "Flotilla", segmento: "viajero", tipo: "Flotillas y transporte", interes: "", capital: "", origen: "web directo", pagina: "contacto", etapa: 0, validacion: "Pendiente", fecha: "2026-10-04" }
  ];
  var STAGES = ["Registro y perfil", "Validación de capacidad", "Evaluación de perfil", "Data room", "Comité y documentación", "Alta y seguimiento"];
  var filter = "todos";
  function esc(s) { return String(s || "").replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); }
  function renderAdmin() {
    var body = $("[data-leads]");
    if (!body) return;
    var mine = loadLeads().map(function (l) { l.mine = true; return l; });
    var all = mine.concat(SAMPLE.map(function (l) { l.sample = true; return l; }));
    var count = function (fn) { return all.filter(fn).length; };
    var set = function (k, v) { var el = $("[data-kpi='" + k + "']"); if (el) el.textContent = v; };
    set("total", all.length);
    set("inversionista", count(function (l) { return l.segmento === "inversionista"; }));
    set("aliado", count(function (l) { return l.segmento === "aliado"; }));
    set("pendiente", count(function (l) { return l.validacion === "Pendiente"; }));
    var segPill = { inversionista: "p-inv", aliado: "p-ali", viajero: "p-via" };
    var valPill = { "Pendiente": "p-pend", "En revisión": "p-rev", "Validado": "p-ok", "No procede": "p-no" };
    body.innerHTML = all.filter(function (l) { return filter === "todos" || l.segmento === filter; }).map(function (l) {
      var stage = l.segmento === "inversionista"
        ? esc(l.etapa + " · " + STAGES[l.etapa - 1]) + '<div class="stage-bar">' + STAGES.map(function (_, i) { return '<i class="' + (i < l.etapa ? "on" : "") + '"></i>'; }).join("") + "</div>"
        : "<small>No aplica</small>";
      var date = (l.fecha || "").slice(0, 10);
      return "<tr>" +
        "<td><b>" + esc(l.nombre) + (l.sample ? '<span class="sample">ejemplo</span>' : "") + "</b><small>" + esc(l.empresa) + "</small></td>" +
        '<td><span class="pill ' + (segPill[l.segmento] || "") + '">' + esc(l.segmento) + "</span></td>" +
        "<td>" + esc(l.tipo) + "</td>" +
        "<td>" + esc(l.interes) + (l.capital ? "<br><small>" + esc(l.capital) + "</small>" : "") + "</td>" +
        "<td>" + esc(l.origen) + "<br><small>página: " + esc(l.pagina) + "</small></td>" +
        "<td>" + stage + "</td>" +
        '<td><span class="pill ' + (valPill[l.validacion] || "p-pend") + '">' + esc(l.validacion) + "</span></td>" +
        '<td style="font-variant-numeric:tabular-nums">' + esc(date) + "</td>" +
        "</tr>";
    }).join("");
  }
  $$("[data-filter]").forEach(function (b) {
    b.addEventListener("click", function () {
      filter = b.dataset.filter;
      $$("[data-filter]").forEach(function (x) { x.setAttribute("aria-pressed", x === b ? "true" : "false"); });
      renderAdmin();
    });
  });
  var clear = $("[data-clear-leads]");
  if (clear) clear.addEventListener("click", function () { try { localStorage.removeItem(STORE_KEY); } catch (e) {} renderAdmin(); });
  if (SPA) { if (!show(location.hash.slice(1))) show("inicio"); }
  else onPageShown(document);
})();
