<template>
  <div class="container py-4 dashboard-shell">
    <div class="d-flex justify-content-between align-items-center mb-3">
      <div>
        <h4 class="mb-0">Hospital Desk</h4>
        <small class="text-muted">{{ user?.name }} ({{ user?.role }})</small>
      </div>
      <button class="btn btn-outline-danger" @click="logout">Logout</button>
    </div>

    <div class="row g-3">
      <div class="col-lg-3">
        <div class="card sidebar-card mb-3">
          <div class="card-body">
            <h6 class="mb-1">{{ user?.name }}</h6>
            <p class="text-muted small mb-2 text-capitalize">Logged in as: {{ user?.role }}</p>
            <div class="d-grid gap-2">
            </div>
          </div>
        </div>
      </div>

      <div class="col-lg-9">
        <section v-if="user?.role === 'admin'">
      <div class="row g-3 mb-3">
        <div class="col-md-3">
          <div class="card metric-card metric-admin">
            <div class="card-body"><small>Total Doctors</small><h5>{{ admin.summary.doctors || 0 }}</h5></div>
          </div>
        </div>
        <div class="col-md-3">
          <div class="card metric-card metric-admin">
            <div class="card-body"><small>Total Patients</small><h5>{{ admin.summary.patients || 0 }}</h5></div>
          </div>
        </div>
        <div class="col-md-3">
          <div class="card metric-card metric-admin">
            <div class="card-body"><small>All Appointments</small><h5>{{ admin.summary.appointments || 0 }}</h5></div>
          </div>
        </div>
        <div class="col-md-3">
          <div class="card metric-card metric-admin">
            <div class="card-body"><small>Today Visits</small><h5>{{ admin.summary.today_appointments || 0 }}</h5></div>
          </div>
        </div>
      </div>

      <div v-if="admin.summary" class="card mb-3">
        <div class="card-body">
          <h6 class="mb-3">Quick Overview</h6>
          <canvas ref="chartEl" height="90"></canvas>
        </div>
      </div>

      <div class="card mb-3">
        <div class="card-body">
          <h6>Add New Doctor</h6>
          <div class="row g-2">
            <div class="col-md-3"><input v-model="admin.newDoctor.username" class="form-control" placeholder="Username" /></div>
            <div class="col-md-3"><input v-model="admin.newDoctor.password" type="password" class="form-control" placeholder="Password" /></div>
            <div class="col-md-3"><input v-model="admin.newDoctor.name" class="form-control" placeholder="Name" /></div>
            <div class="col-md-2"><input v-model="admin.newDoctor.specialization" class="form-control" placeholder="Specialization" /></div>
            <div class="col-md-1"><button class="btn btn-primary w-100" @click="createDoctor">Add</button></div>
          </div>
        </div>
      </div>

      <div class="card mb-3">
        <div class="card-body">
          <h6>Create Availability Slot</h6>
          <div class="row g-2">
            <div class="col-md-3">
              <select class="form-select" v-model.number="admin.slot.doctor_id">
                <option :value="null">Select doctor</option>
                <option v-for="d in admin.doctors" :key="d.id" :value="d.id">{{ d.name }} ({{ d.specialization }})</option>
              </select>
            </div>
            <div class="col-md-2"><input v-model="admin.slot.date" type="date" class="form-control" /></div>
            <div class="col-md-2"><input v-model="admin.slot.start_time" type="time" step="1800" class="form-control" /></div>
            <div class="col-md-2"><input v-model="admin.slot.end_time" type="time" step="1800" class="form-control" /></div>
            <div class="col-md-2">
              <select class="form-select" v-model="admin.slot.is_available">
                <option :value="true">Available</option>
                <option :value="false">Not available</option>
              </select>
            </div>
            <div class="col-md-1"><button class="btn btn-secondary w-100" @click="createDoctorSlot">Save</button></div>
          </div>
        </div>
      </div>

      <div class="card mb-3">
        <div class="card-body">
          <div class="row g-2">
            <div class="col-md-10"><input v-model="admin.searchQuery" class="form-control" placeholder="Search doctor/patient/name/id/contact" /></div>
            <div class="col-md-2"><button class="btn btn-outline-dark w-100" @click="adminSearch">Search</button></div>
          </div>
          <small class="text-muted">Search result: {{ admin.searchResult.doctors.length }} doctors, {{ admin.searchResult.patients.length }} patients</small>
        </div>
      </div>

      <div class="card mb-3">
        <div class="card-body">
          <h6>Doctor List</h6>
          <div class="table-responsive">
            <table class="table table-sm">
              <thead><tr><th>Name</th><th>Specialization</th><th>Status</th><th></th></tr></thead>
              <tbody>
                <tr v-for="d in admin.doctors" :key="d.id">
                  <td>{{ d.name }}</td>
                  <td>{{ d.specialization }}</td>
                  <td>{{ d.is_active ? "Active" : "Blocked" }}</td>
                  <td class="d-flex gap-1">
                    <button class="btn btn-sm btn-outline-warning" @click="toggleUser(d)">{{ d.is_active ? "Block" : "Enable" }}</button>
                    <button class="btn btn-sm btn-outline-danger" @click="removeDoctor(d)">Remove</button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <div class="card">
        <div class="card-body">
          <h6>Appointment Register</h6>
          <div class="table-responsive">
            <table class="table table-sm">
              <thead><tr><th>ID</th><th>Date</th><th>Time</th><th>Doctor</th><th>Patient</th><th>Status</th></tr></thead>
              <tbody>
                <tr v-for="a in admin.appointments" :key="a.id">
                  <td>{{ a.id }}</td>
                  <td>{{ a.date }}</td>
                  <td>{{ a.time }}</td>
                  <td>{{ a.doctor }}</td>
                  <td>{{ a.patient }}</td>
                  <td>{{ a.status }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
        </section>

        <section v-if="user?.role === 'doctor'">
      <div class="row g-3 mb-3">
        <div class="col-md-4">
          <div class="card metric-card metric-doctor">
            <div class="card-body"><small>Total Cases</small><h5>{{ doctor.appointments.length }}</h5></div>
          </div>
        </div>
        <div class="col-md-4">
          <div class="card metric-card metric-doctor">
            <div class="card-body"><small>Completed</small><h5>{{ doctorCompletedCount() }}</h5></div>
          </div>
        </div>
        <div class="col-md-4">
          <div class="card metric-card metric-doctor">
            <div class="card-body"><small>Booked</small><h5>{{ doctorBookedCount() }}</h5></div>
          </div>
        </div>
      </div>

      <div class="card mb-3">
        <div class="card-body">
          <h6>Set My Availability (Next 7 Days)</h6>
          <div class="row g-2">
            <div class="col-md-3"><input v-model="doctor.availability.date" type="date" class="form-control" /></div>
            <div class="col-md-2"><input v-model="doctor.availability.start_time" type="time" step="1800" class="form-control" /></div>
            <div class="col-md-2"><input v-model="doctor.availability.end_time" type="time" step="1800" class="form-control" /></div>
            <div class="col-md-3">
              <select class="form-select" v-model="doctor.availability.is_available">
                <option :value="true">Available</option>
                <option :value="false">Not available</option>
              </select>
            </div>
            <div class="col-md-2"><button class="btn btn-primary w-100" @click="saveAvailability">Save</button></div>
          </div>
        </div>
      </div>

      <div class="card mb-3">
        <div class="card-body">
          <h6>My Appointments</h6>
          <div class="table-responsive">
            <table class="table table-sm">
              <thead><tr><th>ID</th><th>Date</th><th>Time</th><th>Patient</th><th>Status</th><th>Action</th></tr></thead>
              <tbody>
                <tr v-for="a in doctor.appointments" :key="a.id">
                  <td>{{ a.id }}</td>
                  <td>{{ a.date }}</td>
                  <td>{{ a.time }}</td>
                  <td>{{ a.patient_name }}</td>
                  <td><span class="badge" :class="statusBadge(a.status)">{{ a.status }}</span></td>
                  <td class="d-flex gap-1">
                    <button class="btn btn-sm btn-success" @click="setDoctorStatus(a.id, 'completed')">Complete</button>
                    <button class="btn btn-sm btn-secondary" @click="setDoctorStatus(a.id, 'cancelled')">Cancel</button>
                    <button class="btn btn-sm btn-outline-dark" @click="openTreatment(a)">Treatment</button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <div class="card" v-if="doctor.treatment.appointment_id">
        <div class="card-body">
          <h6>Update Treatment (Appointment #{{ doctor.treatment.appointment_id }})</h6>
          <div class="row g-2">
            <div class="col-md-4"><input v-model="doctor.treatment.diagnosis" class="form-control" placeholder="Diagnosis" /></div>
            <div class="col-md-4"><input v-model="doctor.treatment.prescription" class="form-control" placeholder="Prescription" /></div>
            <div class="col-md-4"><input v-model="doctor.treatment.notes" class="form-control" placeholder="Notes" /></div>
          </div>
          <button class="btn btn-primary btn-sm mt-2" @click="saveTreatment">Save Treatment</button>
        </div>
      </div>
        </section>

        <section v-if="user?.role === 'patient'">
      <div class="row g-3 mb-3">
        <div class="col-md-4">
          <div class="card metric-card metric-patient">
            <div class="card-body"><small>Upcoming Visits</small><h5>{{ patient.dashboard.upcoming.length }}</h5></div>
          </div>
        </div>
        <div class="col-md-4">
          <div class="card metric-card metric-patient">
            <div class="card-body"><small>Past Records</small><h5>{{ patient.history.length }}</h5></div>
          </div>
        </div>
        <div class="col-md-4">
          <div class="card metric-card metric-patient">
            <div class="card-body"><small>Alerts</small><h5>{{ notifications.length }}</h5></div>
          </div>
        </div>
      </div>

      <div class="card mb-3">
        <div class="card-body">
          <div class="d-flex justify-content-between align-items-center">
            <h6 class="mb-0">Find Doctor and Book Slot</h6>
          </div>
          <div class="row g-2 mt-2">
            <div class="col-md-5"><input v-model="patient.specializationFilter" class="form-control" placeholder="Filter specialization" /></div>
            <div class="col-md-3"><input v-model="patient.booking.date" type="date" class="form-control" /></div>
            <div class="col-md-2"><input v-model="patient.booking.time" type="time" step="1800" class="form-control" /></div>
            <div class="col-md-2"><button class="btn btn-outline-dark w-100" @click="loadPatientDoctors">Search</button></div>
          </div>
        </div>
      </div>

      <div class="card mb-3">
        <div class="card-body">
          <h6>Available Doctors</h6>
          <div class="table-responsive">
            <table class="table table-sm">
              <thead><tr><th>Name</th><th>Specialization</th><th>Availability</th><th></th></tr></thead>
              <tbody>
                <tr v-for="d in patient.doctors" :key="d.id">
                  <td>{{ d.name }}</td>
                  <td>{{ d.specialization }}</td>
                  <td class="small text-muted">
                    <span v-if="!(d.availability || []).filter(x => x.is_available).length">No slots</span>
                    <span v-else>{{ (d.availability || []).filter(x => x.is_available).slice(0,2).map(x => x.date + ' ' + x.start_time + '-' + x.end_time).join(', ') }}</span>
                  </td>
                  <td><button class="btn btn-sm btn-primary" @click="book(d.id)">Book Slot</button></td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <div class="card mb-3">
        <div class="card-body">
          <h6>Upcoming Appointments</h6>
          <div class="table-responsive">
            <table class="table table-sm">
              <thead><tr><th>ID</th><th>Date</th><th>Time</th><th>Doctor</th><th>Status</th><th></th></tr></thead>
              <tbody>
                <tr v-for="a in patient.dashboard.upcoming" :key="a.id">
                  <td>{{ a.id }}</td>
                  <td>{{ a.date }}</td>
                  <td>{{ a.time }}</td>
                  <td>{{ a.doctor }}</td>
                  <td>{{ a.status }}</td>
                  <td class="d-flex gap-1">
                    <button class="btn btn-sm btn-outline-warning" @click="rescheduleAppointment(a)">Reschedule</button>
                    <button class="btn btn-sm btn-outline-danger" @click="cancelAppointment(a.id)">Cancel</button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <div class="card mb-3">
        <div class="card-body">
          <h6>Treatment History</h6>
          <div class="table-responsive">
            <table class="table table-sm">
              <thead><tr><th>Date</th><th>Doctor</th><th>Diagnosis</th><th>Prescription</th></tr></thead>
              <tbody>
                <tr v-for="h in patient.history" :key="h.appointment_id">
                  <td>{{ h.date }}</td>
                  <td>{{ h.doctor }}</td>
                  <td>{{ h.diagnosis || "-" }}</td>
                  <td>{{ h.prescription || "-" }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <div class="card">
        <div class="card-body">
          <h6>Recent Notifications</h6>
          <ul class="mb-0">
            <li v-for="n in notifications" :key="n.id">{{ n.message }}</li>
          </ul>
        </div>
      </div>
        </section>

        <div v-if="error" class="alert alert-danger mt-3">{{ error }}</div>
        <div v-if="message" class="alert alert-info mt-3">{{ message }}</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { nextTick, onBeforeUnmount, onMounted, ref } from "vue";
import Chart from "chart.js/auto";
import { useRouter } from "vue-router";
import { api } from "../services/api";

const router = useRouter();
const error = ref("");
const message = ref("");
const user = ref(JSON.parse(localStorage.getItem("user") || "null"));
const chartEl = ref(null);
let chartInstance = null;

const admin = ref({
  summary: {},
  doctors: [],
  appointments: [],
  searchQuery: "",
  searchResult: { doctors: [], patients: [] },
  newDoctor: { username: "", password: "", name: "", specialization: "" },
  slot: { doctor_id: null, date: "", start_time: "09:00", end_time: "17:00", is_available: true },
});

const doctor = ref({
  appointments: [],
  availability: { date: "", start_time: "09:00", end_time: "17:00", is_available: true },
  treatment: { appointment_id: null, diagnosis: "", prescription: "", notes: "" },
});

const patient = ref({
  dashboard: { upcoming: [] },
  doctors: [],
  history: [],
  specializationFilter: "",
  booking: { date: "", time: "" },
});

const notifications = ref([]);

function drawChart() {
  if (!admin.value.summary || !chartEl.value) return;
  if (chartInstance) {
    chartInstance.destroy();
  }

  chartInstance = new Chart(chartEl.value, {
    type: "bar",
    data: {
      labels: ["Doctors", "Patients", "Appointments", "Today"],
      datasets: [
        {
          label: "Count",
          data: [
            admin.value.summary.doctors || 0,
            admin.value.summary.patients || 0,
            admin.value.summary.appointments || 0,
            admin.value.summary.today_appointments || 0,
          ],
          backgroundColor: ["#6c757d", "#0d6efd", "#198754", "#fd7e14"],
        },
      ],
    },
    options: {
      responsive: true,
      plugins: {
        legend: { display: false },
      },
    },
  });
}

function statusBadge(status) {
  if (status === "completed") return "text-bg-success";
  if (status === "cancelled") return "text-bg-secondary";
  return "text-bg-primary";
}

function doctorCompletedCount() {
  return doctor.value.appointments.filter((a) => a.status === "completed").length;
}

function doctorBookedCount() {
  return doctor.value.appointments.filter((a) => a.status === "booked").length;
}

async function loadAdminSummary() {
  admin.value.summary = await api("/api/admin/summary");
  await nextTick();
  drawChart();
}

async function loadAdminDoctors() {
  admin.value.doctors = (await api("/api/admin/doctors")).items;
}

async function loadAdminAppointments() {
  admin.value.appointments = (await api("/api/admin/appointments")).items;
}

async function createDoctor() {
  error.value = "";
  try {
    await api("/api/admin/doctors", {
      method: "POST",
      body: JSON.stringify(admin.value.newDoctor),
    });
    message.value = "Doctor profile added";
    admin.value.newDoctor = { username: "", password: "", name: "", specialization: "" };
    await loadAdminDoctors();
    await loadAdminSummary();
  } catch (e) {
    error.value = e.message;
  }
}

async function createDoctorSlot() {
  error.value = "";
  try {
    if (!admin.value.slot.doctor_id || !admin.value.slot.date) {
      throw new Error("Please select doctor and date");
    }
    const out = await api(`/api/admin/doctors/${admin.value.slot.doctor_id}/availability`, {
      method: "PUT",
      body: JSON.stringify({ days: [admin.value.slot] }),
    });
    message.value = out.message || "Slot saved successfully";
  } catch (e) {
    error.value = e.message;
  }
}

async function adminSearch() {
  error.value = "";
  try {
    admin.value.searchResult = await api(`/api/admin/search?q=${encodeURIComponent(admin.value.searchQuery)}`);
  } catch (e) {
    error.value = e.message;
  }
}

async function toggleUser(d) {
  error.value = "";
  try {
    await api(`/api/admin/users/${d.id}/status`, {
      method: "PATCH",
      body: JSON.stringify({ is_active: !d.is_active }),
    });
    await loadAdminDoctors();
  } catch (e) {
    error.value = e.message;
  }
}

async function removeDoctor(d) {
  error.value = "";
  try {
    const ok = window.confirm(`Remove doctor ${d.name}?`);
    if (!ok) return;
    await api(`/api/admin/doctors/${d.id}`, { method: "DELETE" });
    message.value = "Doctor removed from active list";
    await loadAdminDoctors();
    await loadAdminSummary();
  } catch (e) {
    error.value = e.message;
  }
}

async function loadDoctorAppointments() {
  doctor.value.appointments = (await api("/api/doctor/appointments")).items;
}

async function saveAvailability() {
  error.value = "";
  try {
    await api("/api/doctor/availability", {
      method: "PUT",
      body: JSON.stringify({ days: [doctor.value.availability] }),
    });
    message.value = "Availability updated";
  } catch (e) {
    error.value = e.message;
  }
}

async function setDoctorStatus(id, status) {
  error.value = "";
  try {
    await api(`/api/doctor/appointments/${id}/status`, {
      method: "PATCH",
      body: JSON.stringify({ status }),
    });
    await loadDoctorAppointments();
  } catch (e) {
    error.value = e.message;
  }
}

function openTreatment(a) {
  doctor.value.treatment = {
    appointment_id: a.id,
    diagnosis: a.treatment?.diagnosis || "",
    prescription: a.treatment?.prescription || "",
    notes: a.treatment?.notes || "",
  };
}

async function saveTreatment() {
  error.value = "";
  try {
    const t = doctor.value.treatment;
    await api(`/api/doctor/appointments/${t.appointment_id}/treatment`, {
      method: "POST",
      body: JSON.stringify({
        diagnosis: t.diagnosis,
        prescription: t.prescription,
        notes: t.notes,
      }),
    });
    message.value = "Treatment details saved";
    await loadDoctorAppointments();
  } catch (e) {
    error.value = e.message;
  }
}

async function loadPatientDashboard() {
  patient.value.dashboard = await api("/api/patient/dashboard");
}

async function loadPatientDoctors() {
  const q = patient.value.specializationFilter
    ? `?specialization=${encodeURIComponent(patient.value.specializationFilter)}`
    : "";
  patient.value.doctors = (await api(`/api/patient/doctors${q}`)).items;
}

async function loadPatientHistory() {
  patient.value.history = (await api("/api/patient/history")).items;
}

async function loadNotifications() {
  notifications.value = (await api("/api/notifications")).items;
}

function resolveBookingInput(doctorId) {
  const d = patient.value.doctors.find((x) => x.id === doctorId);
  if (!d) return null;
  const slots = (d.availability || []).filter((x) => x.is_available);
  if (!patient.value.booking.date && !patient.value.booking.time) {
    if (!slots.length) return null;
    patient.value.booking.date = slots[0].date;
    patient.value.booking.time = slots[0].start_time;
  }
  if (patient.value.booking.date && !patient.value.booking.time) {
    const sameDate = slots.find((x) => x.date === patient.value.booking.date);
    if (sameDate) patient.value.booking.time = sameDate.start_time;
  }
  return { date: patient.value.booking.date, time: patient.value.booking.time };
}

async function book(doctorId) {
  error.value = "";
  try {
    const slot = resolveBookingInput(doctorId);
    if (!slot || !slot.date || !slot.time) {
      throw new Error("No valid slot available");
    }
    await api("/api/patient/appointments", {
      method: "POST",
      body: JSON.stringify({
        doctor_id: doctorId,
        date: slot.date,
        time: slot.time,
      }),
    });
    message.value = "Appointment booked";
    await loadPatientDashboard();
    await loadNotifications();
  } catch (e) {
    error.value = e.message;
  }
}

async function cancelAppointment(id) {
  error.value = "";
  try {
    await api(`/api/patient/appointments/${id}`, { method: "DELETE" });
    message.value = "Appointment cancelled";
    await loadPatientDashboard();
  } catch (e) {
    error.value = e.message;
  }
}

async function rescheduleAppointment(a) {
  error.value = "";
  try {
    const dateInput = window.prompt("Enter new date (YYYY-MM-DD):", a.date);
    if (!dateInput) return;
    const timeInput = window.prompt("Enter new time (HH:MM, only :00 or :30):", a.time);
    if (!timeInput) return;
    await api(`/api/patient/appointments/${a.id}`, {
      method: "PUT",
      body: JSON.stringify({ date: dateInput, time: timeInput }),
    });
    message.value = "Appointment rescheduled";
    await loadPatientDashboard();
  } catch (e) {
    error.value = e.message;
  }
}

onMounted(async () => {
  if (!localStorage.getItem("token")) {
    router.push("/login");
    return;
  }

  try {
    if (user.value?.role === "admin") {
      await loadAdminSummary();
      await loadAdminDoctors();
      await loadAdminAppointments();
    }
    if (user.value?.role === "doctor") {
      await loadDoctorAppointments();
    }
    if (user.value?.role === "patient") {
      await loadPatientDashboard();
      await loadPatientDoctors();
      await loadPatientHistory();
      await loadNotifications();
    }
  } catch (e) {
    error.value = e.message;
  }
});

onBeforeUnmount(() => {
  if (chartInstance) {
    chartInstance.destroy();
  }
});

function logout() {
  localStorage.removeItem("token");
  localStorage.removeItem("user");
  router.push("/login");
}
</script>

<style scoped>
.dashboard-shell .card {
  border-radius: 10px;
}

.sidebar-card {
  position: sticky;
  top: 12px;
}

.metric-card {
  border: 1px solid #e9ecef;
}

.metric-card h5 {
  margin: 0;
  font-weight: 700;
}

.metric-admin {
  background: #f8f9fa;
}

.metric-doctor {
  background: #f5f7ff;
}

.metric-patient {
  background: #f4fbf7;
}

@media (max-width: 991px) {
  .sidebar-card {
    position: static;
  }
}
</style>
