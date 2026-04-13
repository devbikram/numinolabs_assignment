import "@testing-library/jest-dom";

// jsdom does not implement ResizeObserver or scrollIntoView; mock them for cmdk/Command
global.ResizeObserver = class ResizeObserver {
  observe() {}
  unobserve() {}
  disconnect() {}
};

window.HTMLElement.prototype.scrollIntoView = function () {};
