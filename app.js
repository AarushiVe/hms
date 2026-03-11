const { createApp } = Vue;

createApp({
  data() {
    return {
      publicPage: "login",
      auth: { token: localStorage.getItem("token") || "", user: JSON.parse(localStorage.getItem("user") || "null") },
      loginForm: { username: "", password: "" },
      registerForm: { name: "", username: "", password: "", email: "", phone: "" },
      message: "",
      error: "",
      notifications: [],
      admin: {
        summary: {},
        doctors: [],
        appointments: [],
        searchQuery: "",
        searchResult: { doctors: [], patients: [] },
        newDoctor: { username: "", password: "", name: "", specialization: "" },
        slot: { doctor_id: null, date: "", start_time: "09:00", end_time: "17:00", is_available: true },
      },
      doctor: {
        appointments: [],
        availability: { date: "", start_time: "09:00", end_time: "17:00", is_available: true },
        treatment: { appointment_id: null, diagnosis: "", prescription: "", notes: "" },
      },
      patient: {
        dashboard: { upcoming: [] },
        doctors: [],
        history: [],
        specializationFilter: "",
        booking: { date: "", time: "" },
      },
    };
  },
  computed: {
    activeDoctorsCount() {
      return this.admin.doctors.filter((d) => d.is_active).length;
    },
    doctorCompletedCount() {
      return this.doctor.appointments.filter((a) => a.status === "completed").length;
    },
    doctorBookedCount() {
      return this.doctor.appointments.filter((a) => a.status === "booked").length;
    },
  },
  mounted() {
    const path = window.location.pathname;
    if (!this.auth.token && path === "/register") {
      this.publicPage = "register";
    }
    if (!this.auth.token && path === "/dashboard") {
      this.goPublic("login");
    }
    if (this.auth.token) {
      window.history.replaceState({}, "", "/dashboard");
      this.bootstrap();
    }
  },
  methods: {
    goPublic(page) {
      this.publicPage = page;
      window.history.replaceState({}, "", page === "register" ? "/register" : "/login");
    },

    statusBadge(status) {
      if (status === "completed") return "text-bg-success";
      if (status === "cancelled") return "text-bg-secondary";
      return "text-bg-primary";
    },

    async api(path, options = {}) {
      this.error = "";
      const headers = { "Content-Type": "application/json", ...(options.headers || {}) };
      if (this.auth.token) headers.Authorization = `Bearer ${this.auth.token}`;
      const res = await fetch(path, { ...options, headers });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Request failed");
      return data;
    },

    async login() {
      try {
        const data = await this.api("/api/auth/login", { method: "POST", body: JSON.stringify(this.loginForm) });
        this.auth.token = data.token;
        this.auth.user = data.user;
        localStorage.setItem("token", data.token);
        localStorage.setItem("user", JSON.stringify(data.user));
        this.message = "Logged in successfully";
        window.history.replaceState({}, "", "/dashboard");
        await this.bootstrap();
      } catch (e) {
        this.error = e.message;
      }
    },

    async register() {
      try {
        await this.api("/api/auth/register", { method: "POST", body: JSON.stringify(this.registerForm) });
        this.message = "Registration complete. Please log in.";
        this.goPublic("login");
      } catch (e) {
        this.error = e.message;
      }
    },

    async logout() {
      try {
        await this.api("/api/auth/logout", { method: "POST" });
      } catch (_) {
        // ignore token revoke failure on logout
      }
      localStorage.removeItem("token");
      localStorage.removeItem("user");
      this.auth = { token: "", user: null };
      this.goPublic("login");
      this.message = "Logged out";
    },

    async bootstrap() {
      this.message = "";
      if (this.auth.user.role === "admin") {
        await Promise.all([this.loadAdminSummary(), this.loadAdminDoctors(), this.loadAdminAppointments()]);
      }
      if (this.auth.user.role === "doctor") {
        await this.loadDoctorAppointments();
      }
      if (this.auth.user.role === "patient") {
        await Promise.all([this.loadPatientDashboard(), this.loadPatientDoctors(), this.loadPatientHistory(), this.loadNotifications()]);
      }
    },

    async loadAdminSummary() {
      this.admin.summary = await this.api("/api/admin/summary");
    },
    async loadAdminDoctors() {
      this.admin.doctors = (await this.api("/api/admin/doctors")).items;
    },
    async loadAdminAppointments() {
      this.admin.appointments = (await this.api("/api/admin/appointments")).items;
    },

    async createDoctor() {
      try {
        await this.api("/api/admin/doctors", { method: "POST", body: JSON.stringify(this.admin.newDoctor) });
        this.message = "Doctor created";
        this.admin.newDoctor = { username: "", password: "", name: "", specialization: "" };
        await this.loadAdminDoctors();
        await this.loadAdminSummary();
      } catch (e) {
        this.error = e.message;
      }
    },

    async createDoctorSlot() {
      try {
        if (!this.admin.slot.doctor_id || !this.admin.slot.date || !this.admin.slot.start_time || !this.admin.slot.end_time) {
          throw new Error("Please fill doctor, date, start time and end time");
        }
        const out = await this.api(`/api/admin/doctors/${this.admin.slot.doctor_id}/availability`, {
          method: "PUT",
          body: JSON.stringify({
            days: [
              {
                date: this.admin.slot.date,
                start_time: this.admin.slot.start_time,
                end_time: this.admin.slot.end_time,
                is_available: this.admin.slot.is_available,
              },
            ],
          }),
        });
        this.message = out.message || "Slot made and saved";
        this.admin.slot.date = "";
      } catch (e) {
        this.error = e.message;
      }
    },

    async toggleUser(user) {
      try {
        await this.api(`/api/admin/users/${user.id}/status`, { method: "PATCH", body: JSON.stringify({ is_active: !user.is_active }) });
        await this.loadAdminDoctors();
      } catch (e) {
        this.error = e.message;
      }
    },

    async adminSearch() {
      try {
        this.admin.searchResult = await this.api(`/api/admin/search?q=${encodeURIComponent(this.admin.searchQuery)}`);
        this.message = `Search done: ${this.admin.searchResult.doctors.length} doctors, ${this.admin.searchResult.patients.length} patients`;
      } catch (e) {
        this.error = e.message;
      }
    },

    async loadDoctorAppointments() {
      this.doctor.appointments = (await this.api("/api/doctor/appointments")).items;
    },

    async setDoctorStatus(id, status) {
      try {
        await this.api(`/api/doctor/appointments/${id}/status`, { method: "PATCH", body: JSON.stringify({ status }) });
        await this.loadDoctorAppointments();
      } catch (e) {
        this.error = e.message;
      }
    },

    openTreatment(a) {
      this.doctor.treatment = {
        appointment_id: a.id,
        diagnosis: a.treatment?.diagnosis || "",
        prescription: a.treatment?.prescription || "",
        notes: a.treatment?.notes || "",
      };
    },

    async saveTreatment() {
      try {
        const t = this.doctor.treatment;
        await this.api(`/api/doctor/appointments/${t.appointment_id}/treatment`, {
          method: "POST",
          body: JSON.stringify({ diagnosis: t.diagnosis, prescription: t.prescription, notes: t.notes }),
        });
        this.message = "Treatment saved";
        await this.loadDoctorAppointments();
      } catch (e) {
        this.error = e.message;
      }
    },

    async saveAvailability() {
      try {
        await this.api("/api/doctor/availability", { method: "PUT", body: JSON.stringify({ days: [this.doctor.availability] }) });
        this.message = "Availability updated";
      } catch (e) {
        this.error = e.message;
      }
    },

    async loadPatientDashboard() {
      this.patient.dashboard = await this.api("/api/patient/dashboard");
    },

    async loadPatientDoctors() {
      const q = this.patient.specializationFilter ? `?specialization=${encodeURIComponent(this.patient.specializationFilter)}` : "";
      this.patient.doctors = (await this.api(`/api/patient/doctors${q}`)).items;
    },

    async loadPatientHistory() {
      this.patient.history = (await this.api("/api/patient/history")).items;
    },

    async loadNotifications() {
      this.notifications = (await this.api("/api/notifications")).items;
    },

    getDoctorById(doctorId) {
      return this.patient.doctors.find((d) => d.id === doctorId);
    },

    resolveBookingInput(doctorId) {
      const doctor = this.getDoctorById(doctorId);
      if (!doctor) return null;
      const slots = (doctor.availability || []).filter((s) => s.is_available).sort((a, b) => {
        if (a.date === b.date) return a.start_time.localeCompare(b.start_time);
        return a.date.localeCompare(b.date);
      });

      if (!this.patient.booking.date && !this.patient.booking.time) {
        if (!slots.length) return null;
        this.patient.booking.date = slots[0].date;
        this.patient.booking.time = slots[0].start_time;
      } else if (this.patient.booking.date && !this.patient.booking.time) {
        const sameDay = slots.find((s) => s.date === this.patient.booking.date);
        if (sameDay) this.patient.booking.time = sameDay.start_time;
      }
      return { date: this.patient.booking.date, time: this.patient.booking.time };
    },

    async book(doctorId) {
      try {
        const resolved = this.resolveBookingInput(doctorId);
        if (!resolved || !resolved.date || !resolved.time) {
          throw new Error("No valid slot found. Ask admin/doctor to create availability first.");
        }
        await this.api("/api/patient/appointments", {
          method: "POST",
          body: JSON.stringify({ doctor_id: doctorId, date: resolved.date, time: resolved.time }),
        });
        this.message = `Appointment booked on ${resolved.date} at ${resolved.time}`;
        await this.loadPatientDashboard();
        await this.loadNotifications();
      } catch (e) {
        this.error = e.message;
      }
    },

    async cancelAppointment(id) {
      try {
        await this.api(`/api/patient/appointments/${id}`, { method: "DELETE" });
        this.message = "Appointment cancelled";
        await this.loadPatientDashboard();
      } catch (e) {
        this.error = e.message;
      }
    },

    async triggerExport() {
      try {
        const out = await this.api("/api/patient/export", { method: "POST" });
        this.message = `Export started. Job #${out.job_id}`;
      } catch (e) {
        this.error = e.message;
      }
    },
  },
}).mount("#app");
