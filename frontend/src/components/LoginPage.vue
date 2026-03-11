<template>
  <div class="auth-page">
    <div class="auth-left"></div>

    <div class="auth-right">
      <div class="card auth-card">
        <div class="card-body p-4 p-md-5">
          <h3 class="mb-4">Welcome Back</h3>

          <div class="mb-3">
            <label class="form-label">Username</label>
            <input v-model="form.username" class="form-control form-control-lg" placeholder="Enter username" />
          </div>

          <div class="mb-3">
            <label class="form-label">Password</label>
            <input v-model="form.password" type="password" class="form-control form-control-lg" placeholder="Enter password" />
          </div>

          <button class="btn btn-login w-100" @click="submit">LOGIN</button>

          <div v-if="error" class="alert alert-danger mt-3 py-2">{{ error }}</div>

          <p class="mt-3 mb-0 text-muted">
            New patient?
            <RouterLink to="/register">Create account</RouterLink>
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from "vue";
import { useRouter, RouterLink } from "vue-router";
import { api } from "../services/api";

const router = useRouter();
const error = ref("");

const form = reactive({
  username: "",
  password: "",
});

async function submit() {
  error.value = "";
  try {
    const data = await api("/api/auth/login", {
      method: "POST",
      body: JSON.stringify(form),
    });
    localStorage.setItem("token", data.token);
    localStorage.setItem("user", JSON.stringify(data.user));
    router.push("/dashboard");
  } catch (e) {
    error.value = e.message;
  }
}
</script>

<style scoped>
.auth-page {
  min-height: 100vh;
  display: grid;
  grid-template-columns: 1fr 1fr;
  background: #f3f5f9;
}

.auth-left {
  background: #223a57;
}

.auth-right {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1.5rem;
}

.auth-card {
  width: 100%;
  max-width: 450px;
  border-radius: 12px;
  border: 1px solid #d9dee8;
}

.btn-login {
  background: #1f2f46;
  color: #fff;
}

.btn-login:hover {
  background: #18253a;
  color: #fff;
}

@media (max-width: 992px) {
  .auth-page {
    grid-template-columns: 1fr;
  }

  .auth-left {
    display: none;
  }
}
</style>
