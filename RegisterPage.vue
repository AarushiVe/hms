<template>
  <div class="auth-page">
    <div class="auth-left"></div>

    <div class="auth-right">
      <div class="card auth-card">
        <div class="card-body p-4 p-md-5">
          <h3 class="mb-4">Create Patient Account</h3>

          <div class="row g-2">
            <div class="col-md-6">
              <label class="form-label">Name</label>
              <input v-model="form.name" class="form-control" />
            </div>
            <div class="col-md-6">
              <label class="form-label">Username</label>
              <input v-model="form.username" class="form-control" />
            </div>
            <div class="col-md-6">
              <label class="form-label">Email</label>
              <input v-model="form.email" class="form-control" />
            </div>
            <div class="col-md-6">
              <label class="form-label">Phone</label>
              <input v-model="form.phone" class="form-control" />
            </div>
            <div class="col-12">
              <label class="form-label">Password</label>
              <input v-model="form.password" type="password" class="form-control" />
            </div>
          </div>

          <button class="btn btn-login w-100 mt-3" @click="submit">REGISTER</button>

          <div v-if="message" class="alert alert-info mt-3 py-2">{{ message }}</div>
          <div v-if="error" class="alert alert-danger mt-3 py-2">{{ error }}</div>

          <p class="mt-3 mb-0 text-muted">
            Already have an account?
            <RouterLink to="/login">Go to login</RouterLink>
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from "vue";
import { RouterLink } from "vue-router";
import { api } from "../services/api";

const message = ref("");
const error = ref("");

const form = reactive({
  name: "",
  username: "",
  email: "",
  phone: "",
  password: "",
});

async function submit() {
  message.value = "";
  error.value = "";
  try {
    await api("/api/auth/register", {
      method: "POST",
      body: JSON.stringify(form),
    });
    message.value = "Registration done. You can login now.";
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
  max-width: 520px;
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
