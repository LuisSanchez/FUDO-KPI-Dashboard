import { renderHook, act, waitFor } from "@testing-library/react";
import useAuth from "../useAuth";
import * as client from "../../api/client";

jest.mock("../../api/client");

beforeEach(() => {
  jest.clearAllMocks();
  client.fetchAuthConfig.mockResolvedValue({
    oauth_enabled: false,
    client_id: "",
    require_auth: false,
  });
  client.fetchMe.mockResolvedValue({ authenticated: false });
});

test("loads config and anonymous user on mount", async () => {
  const { result } = renderHook(() => useAuth());
  await waitFor(() => expect(result.current.loading).toBe(false));
  expect(result.current.config.oauth_enabled).toBe(false);
  expect(result.current.user).toBeNull();
});

test("signInWithCredential sets user", async () => {
  client.loginWithGoogle.mockResolvedValue({
    authenticated: true,
    email: "a@b.com",
  });
  const { result } = renderHook(() => useAuth());
  await waitFor(() => expect(result.current.loading).toBe(false));

  await act(async () => {
    await result.current.signInWithCredential("cred");
  });
  expect(result.current.user.email).toBe("a@b.com");
});

test("signOut clears user", async () => {
  client.loginWithGoogle.mockResolvedValue({ authenticated: true, email: "a@b.com" });
  client.logout.mockResolvedValue({ ok: true });
  const { result } = renderHook(() => useAuth());
  await waitFor(() => expect(result.current.loading).toBe(false));
  await act(async () => {
    await result.current.signInWithCredential("cred");
  });
  await act(async () => {
    await result.current.signOut();
  });
  expect(result.current.user).toBeNull();
});

test("refresh failure leaves user null", async () => {
  client.fetchAuthConfig.mockRejectedValue(new Error("network"));
  const { result } = renderHook(() => useAuth());
  await waitFor(() => expect(result.current.loading).toBe(false));
  expect(result.current.user).toBeNull();
});
