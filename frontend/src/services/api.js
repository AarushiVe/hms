export async function api(path, options = {}) {
  const token = localStorage.getItem("token");
  const isAuthEndpoint = path.startsWith("/api/auth/");
  const headers = {
    "Content-Type": "application/json",
    ...(options.headers || {}),
  };

  // Do not send stale auth headers to login/register endpoints.
  if (token && !isAuthEndpoint) {
    headers.Authorization = `Bearer ${token}`;
  }

  let response;
  try {
    response = await fetch(path, {
      ...options,
      headers,
    });
  } catch (e) {
    throw new Error("Request failed. Check backend server and try again.");
  }

  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.error || "Request failed");
  }

  return data;
}
