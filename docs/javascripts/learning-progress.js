(function () {
  "use strict";

  const STORAGE_KEY = "game-dev-knowledge:last-reading-position:v1";
  const RESUME_SESSION_KEY = "game-dev-knowledge:resume-target:v1";
  const SAVE_INTERVAL_MS = 500;
  const REDIRECT_DELAY_MS = 1200;

  const isCoursePage = () => window.location.pathname.includes("/courses/");
  const isHomePage = () => {
    const path = window.location.pathname.replace(/index\.html$/, "");
    return path === "/" || path.endsWith("/Game-Development-Knowledge/");
  };

  function readProgress() {
    try {
      const value = JSON.parse(localStorage.getItem(STORAGE_KEY));
      return value && typeof value.path === "string" ? value : null;
    } catch (_) {
      return null;
    }
  }

  function nearestHeading() {
    const headings = Array.from(document.querySelectorAll("article h1[id], article h2[id], article h3[id], article h4[id]"));
    let current = null;
    for (const heading of headings) {
      if (heading.getBoundingClientRect().top <= 120) current = heading;
      else break;
    }
    return current;
  }

  function saveProgress() {
    if (!isCoursePage()) return;
    const heading = nearestHeading();
    const articleTitle = document.querySelector("article h1")?.textContent?.trim() || document.title;
    const maxScroll = Math.max(1, document.documentElement.scrollHeight - window.innerHeight);
    const value = {
      path: window.location.pathname,
      search: window.location.search.replace(/(?:\?|&)resume=1(?:&|$)/, "").replace(/[?&]$/, ""),
      title: articleTitle,
      headingId: heading?.id || "",
      headingOffset: heading ? window.scrollY - (heading.getBoundingClientRect().top + window.scrollY) : 0,
      scrollY: window.scrollY,
      ratio: Math.min(1, Math.max(0, window.scrollY / maxScroll)),
      updatedAt: Date.now()
    };
    localStorage.setItem(STORAGE_KEY, JSON.stringify(value));
  }

  function restoreProgressIfRequested() {
    const expectedPath = sessionStorage.getItem(RESUME_SESSION_KEY);
    if (!isCoursePage() || expectedPath !== window.location.pathname) return;
    sessionStorage.removeItem(RESUME_SESSION_KEY);
    const progress = readProgress();
    if (!progress || progress.path !== window.location.pathname) return;

    requestAnimationFrame(() => {
      requestAnimationFrame(() => {
        const heading = progress.headingId ? document.getElementById(progress.headingId) : null;
        if (heading) {
          const headingTop = heading.getBoundingClientRect().top + window.scrollY;
          window.scrollTo({ top: Math.max(0, headingTop + (progress.headingOffset || 0)), behavior: "auto" });
        } else {
          const maxScroll = Math.max(0, document.documentElement.scrollHeight - window.innerHeight);
          const fallback = Number.isFinite(progress.scrollY)
            ? Math.min(progress.scrollY, maxScroll)
            : maxScroll * (progress.ratio || 0);
          window.scrollTo({ top: Math.max(0, fallback), behavior: "auto" });
        }
      });
    });
  }

  function resume(progress) {
    sessionStorage.setItem(RESUME_SESSION_KEY, progress.path);
    window.location.assign(`${progress.path}${progress.search || ""}`);
  }

  function addResumePanel() {
    if (!isHomePage()) return;
    const progress = readProgress();
    if (!progress) return;

    const host = document.querySelector("article .md-content__inner") || document.querySelector("article");
    if (!host || document.getElementById("learning-resume-panel")) return;

    const panel = document.createElement("section");
    panel.id = "learning-resume-panel";
    panel.className = "learning-resume-panel";
    panel.innerHTML = `
      <strong>继续上次学习</strong>
      <span class="learning-resume-title"></span>
      <span class="learning-resume-actions">
        <button type="button" data-action="resume">立即继续</button>
        <button type="button" data-action="stay">留在首页</button>
        <button type="button" data-action="clear">清除记录</button>
      </span>
      <small data-role="countdown"></small>
    `;
    panel.querySelector(".learning-resume-title").textContent = progress.title;
    host.prepend(panel);

    const countdown = panel.querySelector('[data-role="countdown"]');
    countdown.textContent = "即将自动跳转；本次需要浏览首页可点“留在首页”。";
    const timer = window.setTimeout(() => resume(progress), REDIRECT_DELAY_MS);

    panel.querySelector('[data-action="resume"]').addEventListener("click", () => resume(progress));
    panel.querySelector('[data-action="stay"]').addEventListener("click", () => {
      window.clearTimeout(timer);
      countdown.textContent = "本次已留在首页；下次打开网站仍会自动续学。";
    });
    panel.querySelector('[data-action="clear"]').addEventListener("click", () => {
      window.clearTimeout(timer);
      localStorage.removeItem(STORAGE_KEY);
      panel.remove();
    });
  }

  function installTracker() {
    let timer = null;
    const scheduleSave = () => {
      if (timer) return;
      timer = window.setTimeout(() => {
        timer = null;
        saveProgress();
      }, SAVE_INTERVAL_MS);
    };
    window.addEventListener("scroll", scheduleSave, { passive: true });
    window.addEventListener("pagehide", saveProgress);
    document.addEventListener("visibilitychange", () => {
      if (document.visibilityState === "hidden") saveProgress();
    });
  }

  function boot() {
    restoreProgressIfRequested();
    addResumePanel();
    installTracker();
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot);
  else boot();
})();
