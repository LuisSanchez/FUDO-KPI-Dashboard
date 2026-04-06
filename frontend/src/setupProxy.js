const { createProxyMiddleware } = require("http-proxy-middleware");

// Local dev: REACT_APP_BACKEND_URL is unset → falls back to localhost:8000
// Docker Compose: REACT_APP_BACKEND_URL=http://backend:8000 (set in docker-compose.yml)
const target = process.env.REACT_APP_BACKEND_URL || "http://localhost:8000";

module.exports = function (app) {
  app.use(
    "/api",
    createProxyMiddleware({
      target,
      changeOrigin: true,
    }),
  );
};
