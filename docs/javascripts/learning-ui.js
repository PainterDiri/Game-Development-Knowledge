(function () {
  "use strict";

  function enhanceDetails() {
    const details = Array.from(document.querySelectorAll("article details"));
    if (!details.length) return;

    details.forEach((item) => {
      const summary = item.querySelector(":scope > summary");
      const text = summary ? summary.textContent : "";
      item.classList.toggle("is-hint", /提示/.test(text));
      item.classList.toggle("is-solution", /答案|解析|参考|方案/.test(text));
    });

    if (details.length < 2 || document.querySelector(".answer-toolbar")) return;
    const first = details[0];
    const toolbar = document.createElement("div");
    toolbar.className = "answer-toolbar";
    toolbar.setAttribute("role", "group");
    toolbar.setAttribute("aria-label", "折叠内容控制");
    toolbar.innerHTML = `
      <span>按需查看：</span>
      <button type="button" data-action="hints">展开提示</button>
      <button type="button" data-action="close">全部收起</button>
    `;

    toolbar.querySelector('[data-action="hints"]').addEventListener("click", () => {
      details.forEach((item) => {
        item.open = item.classList.contains("is-hint");
      });
    });
    toolbar.querySelector('[data-action="close"]').addEventListener("click", () => {
      details.forEach((item) => { item.open = false; });
    });
    first.before(toolbar);
  }

  function boot() {
    enhanceDetails();
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot);
  else boot();
})();
