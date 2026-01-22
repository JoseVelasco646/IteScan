<script setup>
import { ref, onMounted } from "vue";
import { scannerAPI } from "../api/scanner";
import { useScanState } from "../composables/useScanState";
import { useScanProgress } from "../composables/useScanProgress";
import ScanProgress from "./ScanProgress.vue";
import {
  RefreshCw,
  Wifi,
  Activity,
  Network,
  GitBranch,
  X,
  Radar,
} from "lucide-vue-next";
import { useTheme } from "../composables/useTheme";

const { isScanning, startScan, endScan } = useScanState();
const { isDark } = useTheme();
const { scanProgress, setupProgressListener } = useScanProgress();

const scanType = ref("single"); 
const singleHost = ref("");
const singleHostTimeout = ref(120);
const rangeStart = ref("192.168.0.1");
const rangeEnd = ref("192.168.0.10");
const hostTimeout = ref(120);
const loading = ref(false);
const error = ref("");
const results = ref([]);

onMounted(() => {
  setupProgressListener();
});

let abortController = null;

const scanAndSave = async (host) => {
  let isDown = false;

  try {
    const pingResponse = await scannerAPI.pingHosts(
      [host],
      abortController?.signal
    );
    const pingResults = pingResponse?.results || pingResponse || [];
    const pingData = pingResults[0] || {};
    isDown = pingData.status === "down";
  } catch (pingErr) {
  }

  try {
    const fullResponse = await scannerAPI.fullScan(
      host,
      true,
      abortController?.signal,
      hostTimeout.value
    );
    const fullResult = fullResponse?.result || fullResponse;

    return {
      host,
      status: "success",
      message: "Escaneado y guardado",
      data: fullResult,
    };
  } catch (err) {
    if (err.name === "CanceledError" || err.code === "ERR_CANCELED") {
      throw err;
    }
    return {
      host,
      status: "error",
      message: err.response?.data?.detail || err.message || "Error al escanear",
    };
  }
};

const scanSingle = async () => {
  if (!singleHost.value.trim()) {
    error.value = "Por favor ingrese un host";
    return;
  }

  loading.value = true;
  startScan("full-scan-single");
  error.value = "";
  results.value = [];
  abortController = new AbortController();

  try {
    const fullResponse = await scannerAPI.fullScan(
      singleHost.value,
      true,
      abortController?.signal,
      singleHostTimeout.value
    );
    const fullResult = fullResponse?.result || fullResponse;
    
    results.value = [{
      host: singleHost.value,
      status: "success",
      message: "Escaneado y guardado",
      data: fullResult,
    }];
  } catch (err) {
    if (err.name === "CanceledError" || err.code === "ERR_CANCELED") {
      error.value = "Escaneo cancelado por el usuario";
    } else {
      error.value =
        "Error al escanear el host: " + (err.message || "desconocido");
    }
  } finally {
    loading.value = false;
    endScan();
    abortController = null;
  }
};

const scanRange = async () => {
  if (!rangeStart.value.trim() || !rangeEnd.value.trim()) {
    error.value = "Por favor ingrese tanto la IP inicial como la final";
    return;
  }

  loading.value = true;
  startScan("full-scan-range");
  error.value = "";
  results.value = [];
  abortController = new AbortController();

  try {
    const startParts = rangeStart.value.split(".");
    const endParts = rangeEnd.value.split(".");

    if (startParts.length !== 4 || endParts.length !== 4) {
      error.value = "Formato de IP inválido";
      loading.value = false;
      return;
    }

    const startLast = parseInt(startParts[3]);
    const endLast = parseInt(endParts[3]);
    const startThird = parseInt(startParts[2]);
    const endThird = parseInt(endParts[2]);

    if (startParts[0] !== endParts[0] || startParts[1] !== endParts[1]) {
      error.value =
        "El rango debe estar en la misma red (los dos primeros octetos deben coincidir)";
      loading.value = false;
      return;
    }

    const hosts = [];
    for (let third = startThird; third <= endThird; third++) {
      const start = third === startThird ? startLast : 1;
      const end = third === endThird ? endLast : 254;
      for (let last = start; last <= end; last++) {
        hosts.push(`${startParts[0]}.${startParts[1]}.${third}.${last}`);
      }
    }

    const concurrency = 20; 
    const results_temp = [];
    let lastUpdate = 0;
    const updateInterval = Math.max(1, Math.floor(hosts.length / 20)); 

    for (let i = 0; i < hosts.length; i += concurrency) {
      if (abortController?.signal.aborted) {
        break;
      }

      const batch = hosts.slice(i, i + concurrency);
      const batchPromises = batch.map((host) => scanAndSave(host));

      try {
        const batchResults = await Promise.all(batchPromises);
        results_temp.push(...batchResults);

        const shouldUpdate =
          results_temp.length - lastUpdate >= updateInterval ||
          i + concurrency >= hosts.length;

        if (shouldUpdate) {
          results.value = [...results_temp];
          lastUpdate = results_temp.length;
        }
      } catch (err) {
        if (err.name === "CanceledError" || err.code === "ERR_CANCELED") {
          throw err;
        }
      }
    }

    results.value = [...results_temp];
  } catch (err) {
    if (err.name === "CanceledError" || err.code === "ERR_CANCELED") {
      error.value = "Escaneo cancelado por el usuario";
    } else {
      error.value =
        "Error al escanear el rango: " + (err.message || "desconocido");
    }
  } finally {
    loading.value = false;
    endScan();
    abortController = null;
  }
};

const handleScan = () => {
  if (scanType.value === "single") {
    scanSingle();
  } else {
    scanRange();
  }
};

const cancelScan = () => {
  if (abortController) {
    abortController.abort();
    error.value = "Escaneo cancelado";
    loading.value = false;
    endScan();
  }
};

const quickFillRange = (preset) => {
  if (preset === "small") {
    rangeStart.value = "192.168.0.1";
    rangeEnd.value = "192.168.0.10";
  } else if (preset === "medium") {
    rangeStart.value = "192.168.0.1";
    rangeEnd.value = "192.168.0.50";
  } else if (preset === "full") {
    rangeStart.value = "192.168.0.1";
    rangeEnd.value = "192.168.0.254";
  } else if (preset === "large") {
    rangeStart.value = "192.168.0.1";
    rangeEnd.value = "192.168.10.254";
  }
};
</script>

<template>
  <div class="space-y-8">
    <!-- HEADER -->
    <div
      class="relative border rounded-3xl p-8 shadow-2xl overflow-hidden"
      :class="
        isDark()
          ? 'bg-gradient-to-br from-slate-900 via-slate-950 to-slate-900 border-slate-700/50'
          : 'bg-gradient-to-br from-white via-slate-50 to-white border-slate-200'
      "
    >
      <div class="absolute inset-0 opacity-5">
        <div
          class="absolute top-0 left-0 w-96 h-96 rounded-full blur-3xl"
          :class="isDark() ? 'bg-cyan-500' : 'bg-cyan-400'"
        ></div>
        <div
          class="absolute bottom-0 right-0 w-96 h-96 rounded-full blur-3xl"
          :class="isDark() ? 'bg-blue-500' : 'bg-blue-400'"
        ></div>
      </div>

      <div class="relative z-10">
        <div class="flex items-center gap-4 mb-3">
          <div
            class="w-14 h-14 bg-gradient-to-br from-cyan-500 to-blue-600 rounded-2xl flex items-center justify-center shadow-lg shadow-cyan-500/30"
          >
            <Radar class="w-7 h-7 text-white" />
          </div>
          <div>
            <h2
              class="text-3xl font-extrabold mb-2 tracking-tight"
              :class="isDark() ? 'text-white' : 'text-slate-800'"
            >
              Full <span class="text-cyan-400">Scan</span>
            </h2>
            <p
              class="font-tagesschrift text-lg font-semibold mb-2 tracking-wide text-s"
              :class="isDark() ? 'text-gray-200' : 'text-slate-600'"
            >
              Escaneo completo de la red
            </p>
          </div>
        </div>
      </div>
    </div>

    <ScanProgress :progress="scanProgress" />

    <div
      class="bg-gradient-to-r from-blue-500/10 to-cyan-500/10 border border-blue-400/30 rounded-2xl p-6 backdrop-blur-sm"
    >
      <div class="flex items-start gap-4">
        <div
          class="w-10 h-10 bg-blue-500/20 rounded-xl flex items-center justify-center flex-shrink-0 mt-1"
        >
          <svg
            class="w-5 h-5 text-blue-400"
            fill="currentColor"
            viewBox="0 0 20 20"
          >
            <path
              fill-rule="evenodd"
              d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z"
              clip-rule="evenodd"
            />
          </svg>
        </div>
        <div class="flex-1">
          <h3 class="text-lg font-bold text-blue-300 mb-3">
            Capacidades del escaneo
          </h3>
          <div class="grid md:grid-cols-2 gap-3 text-sm">
            <div class="flex items-center gap-2 text-slate-300">
              <svg
                class="w-5 h-5 text-emerald-400"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M5 13l4 4L19 7"
                />
              </svg>
              <span>Resolución de Hostname y MAC</span>
            </div>
            <div class="flex items-center gap-2 text-slate-300">
              <svg
                class="w-5 h-5 text-emerald-400"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M5 13l4 4L19 7"
                />
              </svg>
              <span>Escaneo de puertos (1-1024)</span>
            </div>
            <div class="flex items-center gap-2 text-slate-300">
              <svg
                class="w-5 h-5 text-emerald-400"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M5 13l4 4L19 7"
                />
              </svg>
              <span>Detección de servicios y SO</span>
            </div>
            <div class="flex items-center gap-2 text-slate-300">
              <svg
                class="w-5 h-5 text-emerald-400"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M5 13l4 4L19 7"
                />
              </svg>
              <span>Guardado automático en BD</span>
            </div>
          </div>
          <div
            class="mt-4 flex items-center gap-2 bg-yellow-500/10 border border-yellow-500/30 rounded-lg p-3"
          >
            <svg
              class="w-5 h-5 text-yellow-400 flex-shrink-0"
              fill="currentColor"
              viewBox="0 0 20 20"
            >
              <path
                fill-rule="evenodd"
                d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
                clip-rule="evenodd"
              />
            </svg>
            <span class="text-yellow-300 text-sm font-medium"
              >Escaneo intensivo: ~90-180 segundos por host</span
            >
          </div>
        </div>
      </div>
    </div>

    <div class="grid md:grid-cols-2 gap-4">
      <button
        @click="scanType = 'single'"
        :class="[
          'group relative py-6 rounded-2xl font-semibold transition-all duration-300 overflow-hidden',
          scanType === 'single'
            ? 'bg-slate-800 border-2 border-slate-600 text-white shadow-lg'
            : 'bg-slate-900/50 border border-slate-700 text-slate-400 hover:border-slate-600 hover:bg-slate-800/50',
        ]"
      >
        <div class="relative z-10 flex items-center justify-center gap-3">
          <span>Host Individual</span>
        </div>
        <div
          v-if="scanType !== 'single'"
          class="absolute inset-0 bg-gradient-to-br from-slate-700/0 to-slate-600/0 group-hover:from-slate-700/10 group-hover:to-slate-600/10 transition-all duration-300"
        ></div>
      </button>

      <button
        @click="scanType = 'range'"
        :class="[
          'group relative py-6 rounded-2xl font-semibold transition-all duration-300 overflow-hidden',
          scanType === 'range'
            ? 'bg-slate-800 border-2 border-slate-600 text-white shadow-lg'
            : 'bg-slate-900/50 border border-slate-700 text-slate-400 hover:border-slate-600 hover:bg-slate-800/50',
        ]"
      >
        <div class="relative z-10 flex items-center justify-center gap-3">
          <svg
            class="w-6 h-6"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9"
            />
          </svg>
          <span>Rango de IPs</span>
        </div>
        <div
          v-if="scanType !== 'range'"
          class="absolute inset-0 bg-gradient-to-br from-cyan-500/0 to-blue-600/0 group-hover:from-cyan-500/5 group-hover:to-blue-600/5 transition-all duration-300"
        ></div>
      </button>
    </div>

    <div
      class="border rounded-3xl p-8 shadow-xl"
      :class="
        isDark()
          ? 'bg-gradient-to-br from-slate-900 via-slate-950 to-slate-900 border-slate-700/50'
          : 'bg-gradient-to-br from-white via-slate-50 to-white border-slate-200'
      "
    >
      <div v-if="scanType === 'single'">
        <label
          class="flex items-center gap-2 text-sm font-semibold mb-3"
          :class="isDark() ? 'text-slate-300' : 'text-slate-700'"
        >
          <svg
            class="w-5 h-5"
            :class="isDark() ? 'text-cyan-400' : 'text-cyan-600'"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9"
            />
          </svg>
          Host Objetivo
        </label>
        <div class="relative">
          <input
            v-model="singleHost"
            placeholder="Ej: 192.168.0.1"
            class="w-full border rounded-xl px-5 py-4 pl-12 focus:ring-2 outline-none transition-all"
            :class="
              isDark()
                ? 'bg-slate-800/50 border-slate-600 text-white placeholder-slate-500 focus:ring-cyan-500/50 focus:border-cyan-500/50'
                : 'bg-white border-slate-300 text-slate-800 placeholder-slate-400 focus:ring-cyan-400 focus:border-cyan-400'
            "
          />
          <svg
            class="w-5 h-5 absolute left-4 top-1/2 -translate-y-1/2"
            :class="isDark() ? 'text-slate-500' : 'text-slate-400'"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
        </div>

        <div class="mt-6">
          <label
            class="flex items-center gap-2 text-sm font-semibold mb-3"
            :class="isDark() ? 'text-slate-300' : 'text-slate-700'"
          >
            <svg
              class="w-5 h-5"
              :class="isDark() ? 'text-cyan-400' : 'text-cyan-600'"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            Timeout (segundos)
          </label>
          <div class="flex items-center gap-4">
            <input
              v-model.number="singleHostTimeout"
              type="number"
              min="30"
              max="600"
              class="w-32 rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-cyan-500/60 font-mono text-lg"
              :class="isDark() ? 'bg-slate-800/50 border border-slate-600 text-white' : 'bg-white border border-slate-300 text-slate-800'"
            />
            <span
              class="text-sm"
              :class="isDark() ? 'text-slate-400' : 'text-slate-500'"
            >
              Recomendado: 120s para escaneo completo
            </span>
          </div>
        </div>
      </div>

      <!-- RANGE -->
      <div v-else class="space-y-6">
        <div>
          <label
            class="flex items-center gap-2 text-sm font-semibold mb-3"
            :class="isDark() ? 'text-slate-300' : 'text-slate-700'"
          >
            <svg
              class="w-5 h-5"
              :class="isDark() ? 'text-cyan-400' : 'text-cyan-600'"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M4 6h16M4 12h16M4 18h16"
              />
            </svg>
            Rango de Direcciones IP
          </label>
          <div class="grid md:grid-cols-2 gap-4">
            <div class="relative">
              <input
                v-model="rangeStart"
                placeholder="IP inicial"
                class="w-full border rounded-xl px-4 py-4 pl-11 focus:outline-none focus:ring-2 transition-all"
                :class="
                  isDark()
                    ? 'bg-slate-800/50 border-slate-600 text-white placeholder-slate-500 focus:ring-cyan-500/60 focus:border-cyan-500/50'
                    : 'bg-white border-slate-300 text-slate-800 placeholder-slate-400 focus:ring-cyan-400 focus:border-cyan-400'
                "
              />
              <svg
                class="w-4 h-4 text-emerald-400 absolute left-4 top-1/2 -translate-y-1/2"
                fill="currentColor"
                viewBox="0 0 20 20"
              >
                <path
                  fill-rule="evenodd"
                  d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-8.707l-3-3a1 1 0 00-1.414 1.414L10.586 9H7a1 1 0 100 2h3.586l-1.293 1.293a1 1 0 101.414 1.414l3-3a1 1 0 000-1.414z"
                  clip-rule="evenodd"
                />
              </svg>
            </div>
            <div class="relative">
              <input
                v-model="rangeEnd"
                placeholder="IP final"
                class="w-full border rounded-xl px-4 py-4 pl-11 focus:outline-none focus:ring-2 transition-all"
                :class="
                  isDark()
                    ? 'bg-slate-800/50 border-slate-600 text-white placeholder-slate-500 focus:ring-cyan-500/60 focus:border-cyan-500/50'
                    : 'bg-white border-slate-300 text-slate-800 placeholder-slate-400 focus:ring-cyan-400 focus:border-cyan-400'
                "
              />
              <svg
                class="w-4 h-4 text-red-400 absolute left-4 top-1/2 -translate-y-1/2"
                fill="currentColor"
                viewBox="0 0 20 20"
              >
                <path
                  fill-rule="evenodd"
                  d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-8.707l-3-3a1 1 0 00-1.414 1.414L10.586 9H7a1 1 0 100 2h3.586l-1.293 1.293a1 1 0 101.414 1.414l3-3a1 1 0 000-1.414z"
                  clip-rule="evenodd"
                />
              </svg>
            </div>
          </div>

      <div class="mt-6">
        <label
          class="flex items-center gap-2 text-sm font-semibold mb-3"
          :class="isDark() ? 'text-slate-300' : 'text-slate-700'"
        >
          <svg
            class="w-5 h-5"
            :class="isDark() ? 'text-cyan-400' : 'text-cyan-600'"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
          Timeout por host (segundos)
        </label>
        <div class="flex items-center gap-4">
          <input
            v-model.number="hostTimeout"
            type="number"
            min="30"
            max="600"
            class="w-32 rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-cyan-500/60 font-mono text-lg"
            :class="isDark() ? 'bg-slate-800/50 border border-slate-600 text-white' : 'bg-white border border-slate-300 text-slate-800'"
          />
          <span
            class="text-sm"
            :class="isDark() ? 'text-slate-400' : 'text-slate-500'"
          >
            Recomendado: 90-180s para escaneo completo
          </span>
        </div>
      </div>
          <div class="grid grid-cols-2 gap-2">
            <button
              @click="quickFillRange('small')"
              class="group bg-slate-900/80 hover:bg-slate-800 border border-slate-700 hover:border-slate-600 rounded-lg p-2.5 transition-all duration-200 flex items-center gap-2"
            >
              <div
                class="w-8 h-8 bg-slate-800 group-hover:bg-slate-700 rounded-md flex items-center justify-center transition-colors"
              >
                <span
                  class="text-lg font-bold text-slate-300 group-hover:text-white"
                  >10</span
                >
              </div>
              <span
                class="text-xs text-slate-400 group-hover:text-slate-300 font-medium"
                >Hosts</span
              >
            </button>
            <button
              @click="quickFillRange('medium')"
              class="group bg-slate-900/80 hover:bg-slate-800 border border-slate-700 hover:border-slate-600 rounded-lg p-2.5 transition-all duration-200 flex items-center gap-2"
            >
              <div
                class="w-8 h-8 bg-slate-800 group-hover:bg-slate-700 rounded-md flex items-center justify-center transition-colors"
              >
                <span
                  class="text-lg font-bold text-slate-300 group-hover:text-white"
                  >50</span
                >
              </div>
              <span
                class="text-xs text-slate-400 group-hover:text-slate-300 font-medium"
                >Hosts</span
              >
            </button>
            <button
              @click="quickFillRange('full')"
              class="group bg-slate-900/80 hover:bg-slate-800 border border-slate-700 hover:border-slate-600 rounded-lg p-2.5 transition-all duration-200 flex items-center gap-2"
            >
              <div
                class="w-8 h-8 bg-slate-800 group-hover:bg-slate-700 rounded-md flex items-center justify-center transition-colors"
              >
                <span
                  class="text-sm font-bold text-slate-300 group-hover:text-white"
                  >254</span
                >
              </div>
              <span
                class="text-xs text-slate-400 group-hover:text-slate-300 font-medium"
                >Subred</span
              >
            </button>
            <button
              @click="quickFillRange('large')"
              class="group bg-slate-900/80 hover:bg-slate-800 border border-amber-600/50 hover:border-amber-500 rounded-lg p-2.5 transition-all duration-200 flex items-center gap-2"
            >
              <div
                class="w-8 h-8 bg-slate-800 group-hover:bg-amber-900/30 rounded-md flex items-center justify-center transition-colors"
              >
                <span
                  class="text-xs font-bold text-slate-300 group-hover:text-amber-400"
                  >2.5K</span
                >
              </div>
              <span
                class="text-xs text-slate-400 group-hover:text-amber-300 font-medium"
                >Masivo</span
              >
            </button>
          </div>
        </div>
      </div>
    </div>

    <div class="space-y-3">
      <button
        @click="handleScan"
        :disabled="loading || isScanning"
        class="group w-full py-5 rounded-2xl font-bold text-lg transition-all duration-300 bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-600 hover:to-teal-700 disabled:from-slate-700 disabled:to-slate-800 disabled:cursor-not-allowed shadow-xl hover:shadow-2xl hover:shadow-emerald-500/30 disabled:shadow-none text-white relative overflow-hidden"
      >
        <div class="relative z-10 flex items-center justify-center gap-3">
          <svg
            v-if="!loading"
            class="w-6 h-6 group-hover:scale-110 transition-transform"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M13 10V3L4 14h7v7l9-11h-7z"
            />
          </svg>
          <svg
            v-else
            class="w-6 h-6 animate-spin"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
            />
          </svg>
          <span>
            {{
              loading
                ? "Escaneando..."
                : isScanning
                  ? "Otro escaneo en curso..."
                  : "Iniciar Escaneo Completo"
            }}
          </span>
        </div>
        <div
          v-if="!loading && !isScanning"
          class="absolute inset-0 bg-gradient-to-r from-white/0 via-white/10 to-white/0 -translate-x-full group-hover:translate-x-full transition-transform duration-700"
        ></div>
      </button>

      <button
        v-if="loading"
        @click="cancelScan"
        class="w-full py-4 rounded-xl bg-gradient-to-r from-red-600 to-rose-700 hover:from-red-700 hover:to-rose-800 transition-all text-white font-semibold shadow-lg hover:shadow-xl hover:shadow-red-500/30 flex items-center justify-center gap-2"
      >
        <svg
          class="w-5 h-5"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M6 18L18 6M6 6l12 12"
          />
        </svg>
        <span>Cancelar Escaneo</span>
      </button>
    </div>

    <div
      v-if="error"
      class="bg-gradient-to-r from-red-500/10 to-rose-500/10 border border-red-500/40 rounded-2xl p-5 backdrop-blur-sm"
    >
      <div class="flex items-start gap-3">
        <div
          class="w-10 h-10 bg-red-500/20 rounded-xl flex items-center justify-center flex-shrink-0"
        >
          <svg
            class="w-5 h-5 text-red-400"
            fill="currentColor"
            viewBox="0 0 20 20"
          >
            <path
              fill-rule="evenodd"
              d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
              clip-rule="evenodd"
            />
          </svg>
        </div>
        <div>
          <h4 class="font-bold text-red-300 mb-1">Error en el escaneo</h4>
          <p class="text-sm text-red-200">{{ error }}</p>
        </div>
      </div>
    </div>

    <div v-if="results.length" class="space-y-6">
      <div class="flex items-center justify-between">
        <h3 class="text-2xl font-bold text-white flex items-center gap-3">
          <div
            class="w-10 h-10 bg-emerald-500/20 rounded-xl flex items-center justify-center"
          >
            <svg
              class="w-5 h-5 text-emerald-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4"
              />
            </svg>
          </div>
          Resultados del Escaneo
        </h3>
        <span
          class="px-4 py-2 bg-slate-800 rounded-xl text-slate-300 font-semibold"
        >
          {{ results.length }} {{ results.length === 1 ? "host" : "hosts" }}
        </span>
      </div>

      <div class="grid gap-4">
        <div
          v-for="(r, i) in results"
          :key="i"
          class="group bg-gradient-to-br from-slate-900 via-slate-950 to-slate-900 border border-slate-700/50 rounded-2xl p-6 hover:border-slate-600 transition-all duration-300 hover:shadow-xl stagger-item-scale"
        >
          <div class="flex justify-between items-start mb-4">
            <div class="flex items-center gap-3">
              <div
                class="w-12 h-12 rounded-xl flex items-center justify-center font-mono font-bold text-lg"
                :class="{
                  'bg-emerald-500/20 text-emerald-400': r.status === 'success',
                  'bg-slate-700/50 text-slate-400': r.status === 'down',
                  'bg-red-500/20 text-red-400': r.status === 'error',
                }"
              >
                {{ i + 1 }}
              </div>
              <div>
                <p class="font-mono text-lg font-bold text-white">
                  {{ r.host }}
                </p>
                <p class="text-sm text-slate-400 mt-0.5">{{ r.message }}</p>
              </div>
            </div>
            <span
              class="px-4 py-2 rounded-xl text-xs font-bold uppercase tracking-wider"
              :class="{
                'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30':
                  r.status === 'success',
                'bg-slate-700/50 text-slate-300 border border-slate-600':
                  r.status === 'down',
                'bg-red-500/20 text-red-300 border border-red-500/30':
                  r.status === 'error',
              }"
            >
              {{
                r.status === "success"
                  ? "Exitoso"
                  : r.status === "down"
                    ? "Inactivo"
                    : "Error"
              }}
            </span>
          </div>

          <div
            v-if="r.data"
            class="grid md:grid-cols-3 gap-4 mt-4 pt-4 border-t border-slate-800"
          >
            <div v-if="r.data.hostname" class="flex items-center gap-2 text-sm">
              <svg
                class="w-4 h-4 text-cyan-400 flex-shrink-0"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z"
                />
              </svg>
              <span class="text-slate-300 font-medium">{{
                r.data.hostname
              }}</span>
            </div>
            <div v-if="r.data.mac" class="flex items-center gap-2 text-sm">
              <svg
                class="w-4 h-4 text-purple-400 flex-shrink-0"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z"
                />
              </svg>
              <span class="text-slate-300 font-mono text-xs">{{
                r.data.mac
              }}</span>
            </div>
            <div v-if="r.data.vendor" class="flex items-center gap-2 text-sm">
              <svg
                class="w-4 h-4 text-amber-400 flex-shrink-0"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"
                />
              </svg>
              <span class="text-slate-300">{{ r.data.vendor }}</span>
            </div>
            <div v-if="r.data.os" class="flex items-center gap-2 text-sm">
              <svg
                class="w-4 h-4 text-blue-400 flex-shrink-0"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
                />
              </svg>
              <span class="text-slate-300">{{ r.data.os.name }}</span>
            </div>
            <div class="flex items-center gap-2 text-sm">
              <svg
                class="w-4 h-4 text-emerald-400 flex-shrink-0"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M8 9l3 3-3 3m5 0h3M5 20h14a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"
                />
              </svg>
              <span class="text-slate-300">
                <span class="font-bold text-white">{{
                  r.data.ports?.length || 0
                }}</span>
                puertos
              </span>
            </div>
            <div class="flex items-center gap-2 text-sm">
              <svg
                class="w-4 h-4 text-pink-400 flex-shrink-0"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"
                />
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
                />
              </svg>
              <span class="text-slate-300">
                <span class="font-bold text-white">{{
                  r.data.services?.length || 0
                }}</span>
                servicios
              </span>
            </div>
          </div>
        </div>
        
        <div class="mt-6">
          <label
            class="flex items-center gap-2 text-sm font-semibold mb-3"
            :class="isDark() ? 'text-slate-300' : 'text-slate-700'"
          >
            <svg
              class="w-5 h-5"
              :class="isDark() ? 'text-cyan-400' : 'text-cyan-600'"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            Timeout por host (segundos)
          </label>
          <div class="flex items-center gap-4">
            <input
              v-model.number="hostTimeout"
              type="number"
              min="30"
              max="600"
              class="w-32 rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-cyan-500/60 font-mono text-lg"
              :class="isDark() ? 'bg-slate-800/50 border border-slate-600 text-white' : 'bg-white border border-slate-300 text-slate-800'"
            />
            <span
              class="text-sm"
              :class="isDark() ? 'text-slate-400' : 'text-slate-500'"
            >
              Recomendado: 90-180s para escaneo completo
            </span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
<style scoped>
.preset-btn {
  padding: 0.5rem 1rem;
  border-radius: 0.5rem;
  background-color: rgb(15 23 42);
  border: 1px solid rgb(51 65 85);
  color: rgb(203 213 225);
  transition: all 0.15s;
}
.preset-btn:hover {
  background-color: rgb(30 41 59);
}
* {
  scrollbar-width: none; 
  -ms-overflow-style: none; 
}

*::-webkit-scrollbar {
  display: none; 
}
</style>
