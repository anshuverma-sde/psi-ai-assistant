/*!
 * PSI Assistant embed widget.
 * Usage: <script src="https://YOUR_APP/widget.js" data-assistant-token="ast_..." defer></script>
 * Optional: data-title="Ask us", data-position="left|right", data-color="#4f46e5"
 */
(function () {
  "use strict";
  var script = document.currentScript;
  if (!script || window.__psiAssistantLoaded) return;
  window.__psiAssistantLoaded = true;

  var token = script.getAttribute("data-assistant-token");
  if (!token) {
    console.error("[PSI Assistant] Missing data-assistant-token attribute.");
    return;
  }
  var origin = new URL(script.src).origin;
  var title = script.getAttribute("data-title") || "Ask our assistant";
  var side = script.getAttribute("data-position") === "left" ? "left" : "right";
  var color = script.getAttribute("data-color") || "#0f766e";
  var textColor = script.getAttribute("data-text-color") || "#ffffff";

  var root = document.createElement("div");
  root.setAttribute("data-psi-assistant", "");
  var shadow = root.attachShadow({ mode: "open" });
  shadow.innerHTML =
    "<style>" +
    ":host{all:initial}" +
    ".btn{position:fixed;bottom:20px;" + side + ":20px;z-index:2147483000;display:flex;align-items:center;gap:8px;" +
    "border:0;border-radius:999px;padding:12px 18px;background:" + color + ";color:" + textColor + ";font:600 14px/1 system-ui,sans-serif;" +
    "box-shadow:0 10px 25px rgba(15,23,42,.25);cursor:pointer}" +
    ".btn:focus-visible{outline:3px solid #a5b4fc;outline-offset:2px}" +
    ".panel{position:fixed;bottom:84px;" + side + ":20px;z-index:2147483000;width:min(400px,calc(100vw - 32px));" +
    "height:min(640px,calc(100vh - 110px));border-radius:16px;overflow:hidden;background:#fff;" +
    "box-shadow:0 20px 50px rgba(15,23,42,.3);border:1px solid #e2e8f0;display:none}" +
    ".panel.open{display:block}" +
    "iframe{width:100%;height:100%;border:0}" +
    "</style>" +
    '<div class="panel" role="dialog" aria-label="' + title.replace(/"/g, "&quot;") + '"></div>' +
    '<button class="btn" type="button" aria-expanded="false">' +
    '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>' +
    "<span></span></button>";

  var panel = shadow.querySelector(".panel");
  var button = shadow.querySelector(".btn");
  button.querySelector("span").textContent = title;
  var loaded = false;

  button.addEventListener("click", function () {
    var open = !panel.classList.contains("open");
    if (open && !loaded) {
      var frame = document.createElement("iframe");
      frame.src = origin + "/a/" + encodeURIComponent(token) + "?embed=1";
      frame.title = title;
      frame.allow = "clipboard-write";
      panel.appendChild(frame);
      loaded = true;
    }
    panel.classList.toggle("open", open);
    button.setAttribute("aria-expanded", String(open));
    button.querySelector("span").textContent = open ? "Close" : title;
  });

  (document.body || document.documentElement).appendChild(root);
})();
