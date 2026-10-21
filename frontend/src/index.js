import React from "react";
import ReactDOM from "react-dom/client";
import "./index.css";
import App from "./App";
import ClerkGate from "./auth/ClerkGate";
import { clerkPublishableKey } from "./auth/clerkEnv";

const publishableKey = clerkPublishableKey();
const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(
  <React.StrictMode>
    {publishableKey ? <ClerkGate publishableKey={publishableKey} /> : <App />}
  </React.StrictMode>,
);
