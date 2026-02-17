/**
 * Frontend entrypoint (Vite + React).
 *
 * Responsibilities:
 * - Import global CSS bundles (see `index.css` and `main.css`).
 * - Create the React root and render the top-level `App` component.
 *
 * Notes:
 * - The DOM mount node is the element with id `root` from `index.html`.
 * - React `StrictMode` is enabled to surface potential side-effects during
 *   development.
 */
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "./index.css";
import App from "./App.tsx";
import "./main.css";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
