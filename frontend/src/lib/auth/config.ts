export function authConfig() {
  const secure = ["1", "true", "t", "yes", "y", "on"].includes((process.env.AUTH_SECURE_COOKIE ?? "").toLowerCase());
  return { origin: process.env.AUTH_ORIGIN ?? "http://localhost:3000",
    backend: process.env.BACKEND_INTERNAL_URL ?? "http://localhost:8000",
    cookieName: secure ? "__Host-recephub_session" : "recephub_session" };
}
