(function () {
  "use strict";

  const STORAGE_KEY = "game-dev-knowledge:last-reading-position:v1";
  const RESUME_SESSION_KEY = "game-dev-knowledge:resume-target:v1";
  const SAVE_INTERVAL_MS = 500;
  const REDIRECT_DELAY_MS = 1200;
  const COURSE_SEGMENT = "/courses/";
  const NOT_FOUND_HEADING = "404 - Not found";

  const isSafeCoursePath = (path) => {
    if (typeof path !== "string" || !path.startsWith("/") || path.startsWith("//") || path.includes("\\")) return false;
    try {
      const url = new URL(path, window.location.origin);
      return url.origin === window.location.origin && url.pathname === path && path.includes(COURSE_SEGMENT);
    } catch (_) {
      return false;
    }
  };

  const isCoursePage = () => isSafeCoursePath(window.location.pathname);
  const isNotFoundPage = () => document.querySelector("article h1")?.textContent.trim() === NOT_FOUND_HEADING;
  const isTrackableCoursePage = () => isCoursePage() && !isNotFoundPage();
  const isHomePage = () => {
    const path = window.location.pathname.replace(/index\.html$/, "");
    return path === "/" || path.endsWith("/Game-Development-Knowledge/");
  };

  function readProgress() {
    try {
      const value = JSON.parse(localStorage.getItem(STORAGE_KEY));
      return value && isSafeCoursePath(value.path) ? value : null;
    } catch (_) {
      return null;
    }
  }

  function writeProgress(value) {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(value));
  }

  function clearProgress() {
    localStorage.removeItem(STORAGE_KEY);
    sessionStorage.removeItem(RESUME_SESSION_KEY);
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

  function pageTitle(doc = document) {
    const titleHeading = doc.querySelector("article h1");
    if (!titleHeading) return doc.title;
    return Array.from(titleHeading.childNodes)
      .filter((node) => !(node.nodeType === 1 && node.classList.contains("headerlink")))
      .map((node) => node.textContent)
      .join("")
      .trim();
  }

  function saveProgress() {
    if (!isTrackableCoursePage()) return;
    const heading = nearestHeading();
    const maxScroll = Math.max(1, document.documentElement.scrollHeight - window.innerHeight);
    writeProgress({
      path: window.location.pathname,
      search: window.location.search.replace(/(?:\?|&)resume=1(?:&|$)/, "").replace(/[?&]$/, ""),
      title: pageTitle(),
      headingId: heading?.id || "",
      headingOffset: heading ? window.scrollY - (heading.getBoundingClientRect().top + window.scrollY) : 0,
      scrollY: window.scrollY,
      ratio: Math.min(1, Math.max(0, window.scrollY / maxScroll)),
      updatedAt: Date.now()
    });
  }

  function courseLandingPath(path) {
    if (!isSafeCoursePath(path)) return null;
    const match = path.match(/^(.*\/courses\/[^/]+\/)/);
    return match ? match[1] : null;
  }

  async function inspectPage(path) {
    if (!isSafeCoursePath(path)) return { status: "missing" };
    try {
      const response = await fetch(path, { cache: "no-store", credentials: "same-origin" });
      if (!response.ok) return { status: "missing" };
      const html = await response.text();
      const doc = new DOMParser().parseFromString(html, "text/html");
      if (doc.querySelector("article h1")?.textContent.trim() === NOT_FOUND_HEADING) return { status: "missing" };
      return { status: "ok", title: pageTitle(doc) };
    } catch (_) {
      return { status: "unknown" };
    }
  }

  async function resolveProgress(progress) {
    const target = await inspectPage(progress.path);
    if (target.status === "ok") return { progress, repaired: false };
    if (target.status === "unknown") return null;

    const landingPath = courseLandingPath(progress.path);
    if (landingPath && landingPath !== progress.path) {
      const landing = await inspectPage(landingPath);
      if (landing.status === "ok") {
        const repaired = {
          ...progress,
          path: landingPath,
          search: "",
          title: landing.title || progress.title,
          headingId: "",
          headingOffset: 0,
          scrollY: 0,
          ratio: 0,
          updatedAt: Date.now()
        };
        writeProgress(repaired);
        return { progress: repaired, repaired: true };
      }
      if (landing.status === "unknown") return null;
    }

    clearProgress();
    return null;
  }

  function restoreProgressIfRequested() {
    const expectedPath = sessionStorage.getItem(RESUME_SESSION_KEY);
    if (!isTrackableCoursePage() || expectedPath !== window.location.pathname) return;
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

  async function addResumePanel() {
    if (!isHomePage()) return;
    const stored = readProgress();
    if (!stored) return;
    const resolved = await resolveProgress(stored);
    if (!resolved) return;
    const { progress, repaired } = resolved;

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
    countdown.textContent = repaired
      ? "原阅读页面已调整，将自动返回这门课程的首页。"
      : "即将自动跳转；本次需要浏览首页可点“留在首页”。";
    const timer = window.setTimeout(() => resume(progress), REDIRECT_DELAY_MS);

    panel.querySelector('[data-action="resume"]').addEventListener("click", () => resume(progress));
    panel.querySelector('[data-action="stay"]').addEventListener("click", () => {
      window.clearTimeout(timer);
      countdown.textContent = "本次已留在首页；下次打开网站仍会自动续学。";
    });
    panel.querySelector('[data-action="clear"]').addEventListener("click", () => {
      window.clearTimeout(timer);
      clearProgress();
      panel.remove();
    });
  }

  async function recoverRemovedCoursePage() {
    if (!isCoursePage() || !isNotFoundPage()) return false;
    const landingPath = courseLandingPath(window.location.pathname);
    if (!landingPath || landingPath === window.location.pathname) {
      clearProgress();
      return false;
    }

    const landing = await inspectPage(landingPath);
    if (landing.status !== "ok") {
      if (landing.status === "missing") clearProgress();
      return false;
    }

    const previous = readProgress() || {};
    writeProgress({
      ...previous,
      path: landingPath,
      search: "",
      title: landing.title || previous.title || "课程首页",
      headingId: "",
      headingOffset: 0,
      scrollY: 0,
      ratio: 0,
      updatedAt: Date.now()
    });
    window.location.replace(landingPath);
    return true;
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

  async function boot() {
    installTracker();
    if (await recoverRemovedCoursePage()) return;
    restoreProgressIfRequested();
    await addResumePanel();
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot);
  else boot();
})();
