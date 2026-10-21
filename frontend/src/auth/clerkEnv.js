export function clerkPublishableKey() {
  const value = import.meta.env.VITE_CLERK_PUBLISHABLE_KEY;
  return typeof value === "string" ? value.trim() : "";
}
