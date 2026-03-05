<script setup>
import { ref, onMounted, onUnmounted, computed, watch } from "vue";
import { scannerAPI } from "../api/scanner";
import { useScanState } from "../composables/useScanState";
import { useGlobalWebSocket } from "../composables/useWebSocket";
import ScanProgress from "./ScanProgress.vue";
import {
  RefreshCw,
  Wifi,
  Activity,
  Network,
  GitBranch,
  X,
  Radar,
  CheckCircle,
  XCircle,
  Clock,
  Loader2,
  ChevronDown,
  ChevronUp,
  Server,
  Shield,
  Monitor,
  Cpu,
  Globe,
  Search,
  ArrowUpDown,
  Filter,
  Eye,
  EyeOff,
  Copy,
  Zap,
} from "lucide-vue-next";
import { useTheme } from "../composables/useTheme";
import { useToast } from "../composables/useToast";
import { usePermissions } from "../composables/usePermissions";
import ActiveScanBanner from "./ActiveScanBanner.vue";
import OSIcon from "./OSIcon.vue";
import NumberStepper from "./NumberStepper.vue";

const { isScanning, currentScanType, startScan, endScan, setScanId, externalCancelFlag } = useScanState();

// Este componente es dueño de escaneos que empiecen con 'full-scan'
const isMyOwnScan = computed(() => currentScanType.value.startsWith('full-scan'));
const otherScanActive = computed(() => isScanning.value && !isMyOwnScan.value);
const { isDark } = useTheme();
const ws = useGlobalWebSocket();
const toast = useToast();
const { canExecuteScans, canDeleteResources } = usePermissions();

const scanType = ref("single"); 
const singleHost = ref("");
const singleHostTimeout = ref(120);
const rangeStart = ref("192.168.0.1");
const rangeEnd = ref("192.168.0.10");
const hostTimeout = ref(120);
const concurrency = ref(20);
const loading = ref(false);
const error = ref("");
const results = ref([]);


const scanPhase = ref('idle'); 
const currentScanId = ref(null);
const activeHosts = ref([]);
const inactiveHosts = ref([]);
const totalHosts = ref(0);
const currentHost = ref('');
const currentHosts = ref([]); 
const currentIndex = ref(0);
const completedCount = ref(0);
const totalActive = ref(0);
const progressPercent = ref(0);
const progressMessage = ref('');
const batchSize = ref(0);

// State para ping progress
const pingCompleted = ref(0);
const pingActiveFound = ref(0);

// Flag para ignorar eventos WS después de cancelar
const scanCancelled = ref(false);

// State para los host results que van apareciendo en tiempo real
const liveResults = ref([]);

// State para historial
const showHistory = ref(false);
const historyItems = ref([]);
const historyTotal = ref(0);
const historyPage = ref(0);
const historyLimit = 20;
const loadingHistory = ref(false);
const historyDetail = ref(null);
const showHistoryDetail = ref(false);
const loadingHistoryDetail = ref(false);
const scanStartTime = ref(null);


const loadHistory = async () => {
  loadingHistory.value = true;
  try {
    const data = await scannerAPI.getFullScanHistory(historyPage.value * historyLimit, historyLimit);
    historyItems.value = data.items || [];
    historyTotal.value = data.total || 0;
  } catch (e) {
    toast.error('Error cargando historial');
  } finally {
    loadingHistory.value = false;
  }
};

const viewHistoryDetail = async (id) => {
  loadingHistoryDetail.value = true;
  showHistoryDetail.value = true;
  historyDetail.value = null;
  try {
    historyDetail.value = await scannerAPI.getFullScanHistoryDetail(id);
  } catch (e) {
    toast.error('Error cargando detalle');
    showHistoryDetail.value = false;
  } finally {
    loadingHistoryDetail.value = false;
  }
};

const deleteHistoryEntry = async (id) => {
  try {
    await scannerAPI.deleteFullScanHistory(id);
    toast.success('Registro eliminado');
    loadHistory();
  } catch (e) {
    toast.error('Error eliminando registro');
  }
};

const clearHistory = async () => {
  try {
    await scannerAPI.clearFullScanHistory();
    toast.success('Historial limpiado');
    historyItems.value = [];
    historyTotal.value = 0;
    historyPage.value = 0;
  } catch (e) {
    toast.error('Error limpiando historial');
  }
};

const saveToHistory = async (scanTypeVal, target, resultsList, statusVal, errorMsg = null) => {
  const duration = scanStartTime.value ? ((Date.now() - scanStartTime.value) / 1000) : null;
  const active = resultsList.filter(r => r.status === 'up' || r.status === 'success').length;
  const ports = resultsList.reduce((s, r) => s + (r.ports?.length || r.data?.ports?.length || 0), 0);
  const services = resultsList.reduce((s, r) => s + (r.services?.length || r.data?.services?.length || 0), 0);
  
  // Preparar los resultados para guardar (normalizar data wrapper de single scan)
  const normalizedResults = resultsList.map(r => {
    if (r.data) {
      return { ...r.data, _status: r.status, _message: r.message };
    }
    return r;
  });

  try {
    await scannerAPI.saveFullScanHistory({
      scan_type: scanTypeVal,
      target,
      hosts_scanned: resultsList.length,
      hosts_active: active,
      total_ports: ports,
      total_services: services,
      status: statusVal,
      duration_seconds: duration ? parseFloat(duration.toFixed(2)) : null,
      scan_results: normalizedResults,
      error_message: errorMsg,
    });
  } catch (e) {
    // No bloquear el flujo si falla
    console.warn('Error guardando historial:', e);
  }
};

const formatHistoryDate = (iso) => {
  if (!iso) return '—';
  const d = new Date(iso);
  return d.toLocaleDateString('es-MX', { day: '2-digit', month: 'short', year: 'numeric' }) + ' ' + d.toLocaleTimeString('es-MX', { hour: '2-digit', minute: '2-digit' });
};

const formatDurationShort = (seconds) => {
  if (!seconds) return '—';
  if (seconds < 60) return `${seconds.toFixed(1)}s`;
  const m = Math.floor(seconds / 60);
  const s = Math.round(seconds % 60);
  return `${m}m ${s}s`;
};

// Stats computadas
const scanStats = computed(() => {
  const up = liveResults.value.filter(r => r.status === 'up' || r.status === 'success').length;
  const errored = liveResults.value.filter(r => r.status === 'error').length;
  const ports = liveResults.value.reduce((sum, r) => sum + (r.ports?.length || 0), 0);
  const services = liveResults.value.reduce((sum, r) => sum + (r.services?.length || 0), 0);
  return { up, errored, totalPorts: ports, totalServices: services };
});

// Estado para resultados mejorados
const expandedHosts = ref(new Set());
const resultSearchQuery = ref('');
const resultSortKey = ref('host'); 
const resultSortAsc = ref(true);
const showInactive = ref(false);

const toggleHostExpand = (host) => {
  const s = new Set(expandedHosts.value);
  if (s.has(host)) s.delete(host);
  else s.add(host);
  expandedHosts.value = s;
};

const expandAll = () => {
  const all = (liveResults.value.length ? liveResults.value : results.value).map(r => r.host);
  expandedHosts.value = new Set(all);
};

const collapseAll = () => {
  expandedHosts.value = new Set();
};

const getPortCategory = (port) => {
  if (port <= 1023) return 'well-known';
  if (port <= 49151) return 'registered';
  return 'dynamic';
};

const getPortCategoryColor = (port) => {
  const cat = getPortCategory(port);
  if (cat === 'well-known') return 'from-emerald-500/20 to-emerald-600/10 border-emerald-500/30 text-emerald-300';
  if (cat === 'registered') return 'from-blue-500/20 to-blue-600/10 border-blue-500/30 text-blue-300';
  return 'from-amber-500/20 to-amber-600/10 border-amber-500/30 text-amber-300';
};



const getLatencyColor = (ms) => {
  if (!ms) return 'text-slate-500';
  if (ms < 5) return 'text-emerald-400';
  if (ms < 50) return 'text-green-400';
  if (ms < 100) return 'text-yellow-400';
  if (ms < 300) return 'text-orange-400';
  return 'text-red-400';
};

const getLatencyLabel = (ms) => {
  if (!ms) return '—';
  if (ms < 5) return 'Excelente';
  if (ms < 50) return 'Buena';
  if (ms < 100) return 'Normal';
  if (ms < 300) return 'Lenta';
  return 'Muy lenta';
};

const copyToClipboard = async (text) => {
  try {
    if (navigator.clipboard && window.isSecureContext) {
      await navigator.clipboard.writeText(text);
    } else {
      const ta = document.createElement('textarea');
      ta.value = text;
      ta.style.cssText = 'position:fixed;left:-9999px;top:-9999px';
      document.body.appendChild(ta);
      ta.select();
      document.execCommand('copy');
      document.body.removeChild(ta);
    }
    toast.success('Copiado al portapapeles');
  } catch {
    toast.error('No se pudo copiar');
  }
};

// Resultados filtrados y ordenados para la vista de rango
const filteredLiveResults = computed(() => {
  let items = liveResults.value;
  if (!showInactive.value) {
    items = items.filter(r => r.status === 'up' || r.status === 'success');
  }
  if (resultSearchQuery.value.trim()) {
    const q = resultSearchQuery.value.toLowerCase();
    items = items.filter(r => 
      r.host?.toLowerCase().includes(q) ||
      r.hostname?.toLowerCase().includes(q) ||
      r.vendor?.toLowerCase().includes(q) ||
      r.mac?.toLowerCase().includes(q) ||
      r.os?.name?.toLowerCase().includes(q) ||
      r.ports?.some(p => String(p.port).includes(q) || p.service?.toLowerCase().includes(q)) ||
      r.services?.some(s => s.service?.toLowerCase().includes(q) || s.product?.toLowerCase().includes(q))
    );
  }
  // Ordenar
  items = [...items].sort((a, b) => {
    let va, vb;
    switch (resultSortKey.value) {
      case 'host':
        va = a.host?.split('.').map(n => n.padStart(3, '0')).join('.') || '';
        vb = b.host?.split('.').map(n => n.padStart(3, '0')).join('.') || '';
        break;
      case 'ports':
        va = a.ports?.length || 0;
        vb = b.ports?.length || 0;
        break;
      case 'services':
        va = a.services?.length || 0;
        vb = b.services?.length || 0;
        break;
      case 'latency':
        va = a.latency_ms || 9999;
        vb = b.latency_ms || 9999;
        break;
      default:
        va = 0; vb = 0;
    }
    if (va < vb) return resultSortAsc.value ? -1 : 1;
    if (va > vb) return resultSortAsc.value ? 1 : -1;
    return 0;
  });
  return items;
});

const toggleSort = (key) => {
  if (resultSortKey.value === key) {
    resultSortAsc.value = !resultSortAsc.value;
  } else {
    resultSortKey.value = key;
    resultSortAsc.value = true;
  }
};

let abortController = null;
let removeWsListener = null;

onMounted(() => {
  // Escuchar progreso del full_range scan via WebSocket
  removeWsListener = ws.on('scan_progress', (data) => {
    if (data.scan_type !== 'full_range') return;
    if (currentScanId.value && data.scan_id !== currentScanId.value) return;
    
    handleScanProgress(data);
  });
});

onUnmounted(() => {
  if (removeWsListener) removeWsListener();
});

// Detectar cancelación externa (desde ActiveScanBanner u otro componente)
watch(externalCancelFlag, (cancelled) => {
  if (cancelled && isMyOwnScan.value && loading.value) {
    scanCancelled.value = true;
    error.value = "Escaneo cancelado";
    loading.value = false;
    scanPhase.value = 'idle';
    currentHosts.value = [];
    progressPercent.value = 0;
    progressMessage.value = '';
    endScan();
  }
});

const handleScanProgress = (data) => {
  // Ignorar eventos si el scan fue cancelado
  if (scanCancelled.value) return;
  
  // Capturar scan_id desde el primer evento del backend
  if (data.scan_id && !currentScanId.value) {
    currentScanId.value = data.scan_id;
    setScanId(data.scan_id);
  }
  
  progressPercent.value = data.progress || 0;
  progressMessage.value = data.message || '';
  
  switch (data.status) {
    case 'ping_phase':
      scanPhase.value = 'pinging';
      totalHosts.value = data.total;
      pingCompleted.value = 0;
      pingActiveFound.value = 0;
      break;
    
    case 'ping_progress':
      scanPhase.value = 'pinging';
      pingCompleted.value = data.completed || 0;
      pingActiveFound.value = data.active_found || 0;
      totalHosts.value = data.total;
      break;
      
    case 'ping_done':
      scanPhase.value = 'ping_done';
      activeHosts.value = data.active_hosts || [];
      inactiveHosts.value = data.inactive_hosts || [];
      totalActive.value = data.active_count || 0;
      totalHosts.value = data.total;
      break;
      
    case 'scanning_host':
      scanPhase.value = 'scanning';
      currentHost.value = data.current_host;
      currentHosts.value = data.current_hosts || [];
      completedCount.value = data.completed_count || completedCount.value;
      totalActive.value = data.total_active;
      break;
      
    case 'host_completed':
      scanPhase.value = 'scanning';
      completedCount.value = data.completed_count || (completedCount.value + 1);
      // Actualizar lista de IPs actualmente escaneando (viene del server)
      currentHosts.value = data.current_hosts || currentHosts.value.filter(h => h !== data.current_host);
      if (data.result) {
        liveResults.value.push(data.result);
      }
      break;
      
    case 'completed':
      scanPhase.value = 'completed';
      progressPercent.value = 100;
      currentHosts.value = [];
      completedCount.value = data.completed_count || completedCount.value;
      break;
  }
};

const scanSingle = async () => {
  if (!singleHost.value.trim()) {
    error.value = "Por favor ingrese un host";
    return;
  }

  loading.value = true;
  error.value = "";
  results.value = [];
  liveResults.value = [];
  scanPhase.value = 'scanning';
  scanStartTime.value = Date.now();
  abortController = new AbortController();
  startScan("full-scan-single", abortController);

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
    scanPhase.value = 'completed';
    // Guardar en historial
    await saveToHistory('single', singleHost.value, results.value, 'success');
  } catch (err) {
    if (err.name === "CanceledError" || err.code === "ERR_CANCELED") {
      error.value = "Escaneo cancelado por el usuario";
      await saveToHistory('single', singleHost.value, results.value, 'cancelled', 'Cancelado por el usuario');
    } else {
      error.value =
        "Error al escanear el host: " + (err.message || "desconocido");
      await saveToHistory('single', singleHost.value, [], 'error', err.message || 'desconocido');
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
  error.value = "";
  results.value = [];
  liveResults.value = [];
  activeHosts.value = [];
  inactiveHosts.value = [];
  currentHosts.value = [];
  scanPhase.value = 'pinging';
  currentIndex.value = 0;
  completedCount.value = 0;
  batchSize.value = 0;
  progressPercent.value = 0;
  progressMessage.value = 'Iniciando escaneo...';
  scanCancelled.value = false;
  currentScanId.value = null;
  scanStartTime.value = Date.now();
  abortController = new AbortController();
  startScan("full-scan-range", abortController);

  try {
    const startParts = rangeStart.value.split(".");
    const endParts = rangeEnd.value.split(".");

    if (startParts.length !== 4 || endParts.length !== 4) {
      error.value = "Formato de IP inválido";
      loading.value = false;
      endScan();
      return;
    }

    const startLast = parseInt(startParts[3]);
    const endLast = parseInt(endParts[3]);
    const startThird = parseInt(startParts[2]);
    const endThird = parseInt(endParts[2]);

    if (startParts[0] !== endParts[0] || startParts[1] !== endParts[1]) {
      error.value = "El rango debe estar en la misma red (los dos primeros octetos deben coincidir)";
      loading.value = false;
      endScan();
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

    totalHosts.value = hosts.length;

    // Llamar al nuevo endpoint que hace ping + full scan solo a activos
    const response = await scannerAPI.fullScanRange(
      hosts,
      true,
      abortController?.signal,
      hostTimeout.value,
      concurrency.value
    );

    // El scan_id viene del response
    currentScanId.value = response.scan_id;

  
    if (response.results && response.results.length > liveResults.value.length) {
      liveResults.value = response.results;
    }

    scanPhase.value = 'completed';
    toast.success(`Escaneo completado: ${response.active_count} activos de ${response.total}`);
    // Guardar en historial
    const rangeTarget = `${rangeStart.value} - ${rangeEnd.value}`;
    await saveToHistory('range', rangeTarget, liveResults.value, 'success');

  } catch (err) {
    if (err.name === "CanceledError" || err.code === "ERR_CANCELED") {
      error.value = "Escaneo cancelado por el usuario";
      const rangeTarget = `${rangeStart.value} - ${rangeEnd.value}`;
      await saveToHistory('range', rangeTarget, liveResults.value, 'cancelled', 'Cancelado por el usuario');
    } else {
      error.value = "Error al escanear el rango: " + (err.message || "desconocido");
      const rangeTarget = `${rangeStart.value} - ${rangeEnd.value}`;
      await saveToHistory('range', rangeTarget, liveResults.value, 'error', err.message || 'desconocido');
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
    // Marcar como cancelado para ignorar futuros eventos WS
    scanCancelled.value = true;
    
    // Enviar cancel_scan al backend via WebSocket
    if (currentScanId.value) {
      ws.send(JSON.stringify({
        type: 'cancel_scan',
        scan_id: currentScanId.value
      }));
    }
    
    abortController.abort();
    error.value = "Escaneo cancelado";
    loading.value = false;
    scanPhase.value = 'idle';
    currentHosts.value = [];
    progressPercent.value = 0;
    progressMessage.value = '';
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
    <ActiveScanBanner myScanType="fullscan" />

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

    <ScanProgress v-if="scanType === 'single'" :progress="scanProgress" />

    <!-- Panel de Progreso en Tiempo Real para Rango -->
    <div v-if="scanType === 'range' && scanPhase !== 'idle' && loading" 
      class="border rounded-2xl p-6 space-y-4"
      :class="isDark() 
        ? 'bg-gradient-to-br from-slate-900 via-slate-950 to-slate-900 border-slate-700/50' 
        : 'bg-gradient-to-br from-white via-slate-50 to-white border-slate-200'"
    >
      <!-- Barra de progreso -->
      <div>
        <div class="flex items-center justify-between mb-2">
          <span class="text-sm font-semibold" :class="isDark() ? 'text-slate-300' : 'text-slate-700'">
            {{ progressMessage }}
          </span>
          <span class="text-sm font-mono font-bold text-cyan-400">{{ Math.round(progressPercent) }}%</span>
        </div>
        <div class="w-full h-3 rounded-full overflow-hidden" :class="isDark() ? 'bg-slate-800' : 'bg-slate-200'">
          <div 
            class="h-full rounded-full transition-all duration-500 ease-out bg-cyan-600"
            :style="{ width: progressPercent + '%' }"
          ></div>
        </div>
      </div>

      <!-- Fase de Ping: info con progreso -->
      <div v-if="scanPhase === 'pinging'" class="space-y-3">
        <div class="flex items-center gap-3 p-4 rounded-xl" 
          :class="isDark() ? 'bg-cyan-900/20 border border-cyan-700/30' : 'bg-cyan-50 border border-cyan-200'">
          <div class="w-8 h-8 border-4 border-cyan-400 border-t-transparent rounded-full animate-spin"></div>
          <div class="flex-1">
            <p class="font-semibold" :class="isDark() ? 'text-cyan-300' : 'text-cyan-700'">Fase 1: Detectando hosts activos</p>
            <p class="text-sm" :class="isDark() ? 'text-slate-400' : 'text-slate-500'">
              {{ pingCompleted > 0 ? `Ping: ${pingCompleted}/${totalHosts} IPs verificadas` : `Haciendo ping a ${totalHosts} IPs...` }}
            </p>
          </div>
          <div v-if="pingCompleted > 0" class="text-right">
            <p class="text-lg font-bold text-green-400">{{ pingActiveFound }}</p>
            <p class="text-xs" :class="isDark() ? 'text-slate-400' : 'text-slate-500'">activas</p>
          </div>
        </div>
        <!-- Mini barra de progreso del ping -->
        <div v-if="pingCompleted > 0" class="px-1">
          <div class="w-full h-1.5 rounded-full overflow-hidden" :class="isDark() ? 'bg-slate-800' : 'bg-slate-200'">
            <div 
              class="h-full rounded-full transition-all duration-300 ease-out bg-gradient-to-r from-cyan-400 to-cyan-600"
              :style="{ width: Math.round((pingCompleted / totalHosts) * 100) + '%' }"
            ></div>
          </div>
          <p class="text-xs text-right mt-1" :class="isDark() ? 'text-slate-500' : 'text-slate-400'">
            {{ Math.round((pingCompleted / totalHosts) * 100) }}%
          </p>
        </div>
      </div>

      <!-- Fase Ping completado: resumen -->
      <div v-if="scanPhase === 'ping_done' || scanPhase === 'scanning'" class="grid grid-cols-3 gap-3">
        <div class="rounded-xl p-4 text-center border" 
          :class="isDark() ? 'bg-slate-800/50 border-slate-700/50' : 'bg-white border-slate-200'">
          <p class="text-2xl font-bold text-cyan-400">{{ totalHosts }}</p>
          <p class="text-xs mt-1" :class="isDark() ? 'text-slate-400' : 'text-slate-500'">Total IPs</p>
        </div>
        <div class="rounded-xl p-4 text-center border"
          :class="isDark() ? 'bg-green-900/20 border-green-700/30' : 'bg-green-50 border-green-200'">
          <p class="text-2xl font-bold text-green-400">{{ totalActive }}</p>
          <p class="text-xs mt-1" :class="isDark() ? 'text-slate-400' : 'text-slate-500'">Activas</p>
        </div>
        <div class="rounded-xl p-4 text-center border"
          :class="isDark() ? 'bg-slate-800/50 border-slate-700/50' : 'bg-white border-slate-200'">
          <p class="text-2xl font-bold" :class="isDark() ? 'text-slate-500' : 'text-slate-400'">{{ inactiveHosts.length }}</p>
          <p class="text-xs mt-1" :class="isDark() ? 'text-slate-400' : 'text-slate-500'">Inactivas (omitidas)</p>
        </div>
      </div>

      <!-- Resumen de progreso detallado -->
      <div v-if="scanPhase === 'scanning'" class="space-y-3">
        <!-- Contador de progreso -->
        <div class="grid grid-cols-4 gap-2">
          <div class="rounded-xl p-3 text-center border"
            :class="isDark() ? 'bg-blue-900/20 border-blue-700/30' : 'bg-blue-50 border-blue-200'">
            <p class="text-xl font-bold text-blue-400">{{ currentHosts.length }}</p>
            <p class="text-xs mt-0.5" :class="isDark() ? 'text-slate-400' : 'text-slate-500'">Escaneando ahora</p>
          </div>
          <div class="rounded-xl p-3 text-center border"
            :class="isDark() ? 'bg-emerald-900/20 border-emerald-700/30' : 'bg-emerald-50 border-emerald-200'">
            <p class="text-xl font-bold text-emerald-400">{{ completedCount }}</p>
            <p class="text-xs mt-0.5" :class="isDark() ? 'text-slate-400' : 'text-slate-500'">Completados</p>
          </div>
          <div class="rounded-xl p-3 text-center border"
            :class="isDark() ? 'bg-amber-900/20 border-amber-700/30' : 'bg-amber-50 border-amber-200'">
            <p class="text-xl font-bold text-amber-400">{{ totalActive - completedCount - currentHosts.length }}</p>
            <p class="text-xs mt-0.5" :class="isDark() ? 'text-slate-400' : 'text-slate-500'">Pendientes</p>
          </div>
          <div class="rounded-xl p-3 text-center border"
            :class="isDark() ? 'bg-slate-800/50 border-slate-700/50' : 'bg-white border-slate-200'">
            <p class="text-xl font-bold" :class="isDark() ? 'text-slate-400' : 'text-slate-500'">{{ inactiveHosts.length }}</p>
            <p class="text-xs mt-0.5" :class="isDark() ? 'text-slate-400' : 'text-slate-500'">Inactivas</p>
          </div>
        </div>

        <!-- IPs actualmente siendo escaneadas -->
        <div v-if="currentHosts.length > 0" 
          class="rounded-xl p-4 border"
          :class="isDark() ? 'bg-blue-900/15 border-blue-700/30' : 'bg-blue-50 border-blue-200'">
          <div class="flex items-center gap-2 mb-3">
            <div class="w-6 h-6 border-3 border-blue-400 border-t-transparent rounded-full animate-spin flex-shrink-0"></div>
            <p class="font-semibold text-sm" :class="isDark() ? 'text-blue-300' : 'text-blue-700'">
              Escaneando {{ currentHosts.length }} IPs simultáneamente
            </p>
            <span class="ml-auto px-2.5 py-1 rounded-lg text-xs font-bold" 
              :class="isDark() ? 'bg-blue-500/20 text-blue-300' : 'bg-blue-100 text-blue-700'">
              {{ completedCount }}/{{ totalActive }}
            </span>
          </div>
          <div class="flex flex-wrap gap-2">
            <div v-for="ip in currentHosts" :key="ip" 
              class="flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-mono font-semibold transition-all duration-300"
              :class="isDark() 
                ? 'bg-blue-500/15 text-blue-300 border border-blue-500/30' 
                : 'bg-blue-100 text-blue-700 border border-blue-200'">
              <span class="w-2 h-2 rounded-full bg-blue-400 animate-pulse"></span>
              {{ ip }}
            </div>
          </div>
        </div>
      </div>
    </div>

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
            Timeout
          </label>
          <NumberStepper v-model="singleHostTimeout" :min="30" :max="600" :step="10" unit="s"
            hint="Recomendado: 120s para escaneo completo"
            accent-color="cyan" :show-range="true" />
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
          Timeout por host
        </label>
        <NumberStepper v-model="hostTimeout" :min="30" :max="600" :step="10" unit="s"
          hint="Recomendado: 90-180s para escaneo completo"
          accent-color="cyan" :show-range="true" />
      </div>

      <!-- Concurrencia -->
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
              d="M13 10V3L4 14h7v7l9-11h-7z"
            />
          </svg>
          IPs simultáneas
        </label>
        <NumberStepper v-model="concurrency" :min="1" :max="50" unit="IPs"
          :presets="[5, 10, 20, 50]"
          accent-color="cyan" :show-range="true" />
        <p class="text-xs mt-1.5" :class="isDark() ? 'text-slate-500' : 'text-slate-400'">Más simultáneas = más rápido pero más carga de red</p>
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
        v-if="canExecuteScans"
        @click="handleScan"
        :disabled="loading || otherScanActive"
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
                : otherScanActive
                  ? "Otro escaneo en curso..."
                  : "Iniciar Escaneo Completo"
            }}
          </span>
        </div>
        <div
          v-if="!loading && !otherScanActive"
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

    <!-- ═══════════════════════════════════════════════════════════ -->
    <!-- RESULTADOS SINGLE SCAN - MEJORADOS -->
    <!-- ═══════════════════════════════════════════════════════════ -->
    <div v-if="scanType === 'single' && results.length" class="space-y-6">
      <div class="flex items-center justify-between">
        <h3 class="text-2xl font-bold flex items-center gap-3" :class="isDark() ? 'text-white' : 'text-slate-800'">
          <div class="w-10 h-10 bg-emerald-500/20 rounded-xl flex items-center justify-center">
            <CheckCircle class="w-5 h-5 text-emerald-400" />
          </div>
          Resultados del Escaneo
        </h3>
        <span class="px-4 py-2 rounded-xl font-semibold" :class="isDark() ? 'bg-slate-800 text-slate-300' : 'bg-slate-100 text-slate-600'">
          {{ results.length }} {{ results.length === 1 ? 'host' : 'hosts' }}
        </span>
      </div>

      <div class="grid gap-5">
        <div v-for="(r, i) in results" :key="i"
          class="group border rounded-2xl overflow-hidden transition-all duration-300 hover:shadow-2xl"
          :class="isDark()
            ? 'bg-gradient-to-br from-slate-900 via-slate-950 to-slate-900 border-slate-700/50 hover:border-cyan-500/30'
            : 'bg-white border-slate-200 hover:border-cyan-400/50'"
        >
          <!-- Header del host -->
          <div class="p-5 cursor-pointer" @click="toggleHostExpand(r.host)">
            <div class="flex justify-between items-start">
              <div class="flex items-center gap-4">
                <div class="w-14 h-14 rounded-xl flex items-center justify-center relative"
                  :class="{
                    'bg-gradient-to-br from-emerald-500/20 to-teal-500/20 border border-emerald-500/30': r.status === 'success',
                    'bg-gradient-to-br from-slate-700/50 to-slate-800/50 border border-slate-600': r.status === 'down',
                    'bg-gradient-to-br from-red-500/20 to-rose-500/20 border border-red-500/30': r.status === 'error',
                  }">
                  <Server class="w-6 h-6" :class="r.status === 'success' ? 'text-emerald-400' : r.status === 'down' ? 'text-slate-500' : 'text-red-400'" />
                  <div class="absolute -top-1 -right-1 w-3.5 h-3.5 rounded-full border-2"
                    :class="isDark() ? 'border-slate-900' : 'border-white'"
                    :style="{ backgroundColor: r.status === 'success' ? '#10b981' : r.status === 'down' ? '#64748b' : '#ef4444' }"></div>
                </div>
                <div>
                  <div class="flex items-center gap-2">
                    <p class="font-mono text-xl font-bold" :class="isDark() ? 'text-white' : 'text-slate-800'">{{ r.host }}</p>
                    <button @click.stop="copyToClipboard(r.host)" class="opacity-0 group-hover:opacity-100 p-1 rounded-md hover:bg-slate-700/50 transition-all" title="Copiar IP">
                      <Copy class="w-3.5 h-3.5" :class="isDark() ? 'text-slate-400' : 'text-slate-500'" />
                    </button>
                  </div>
                  <div class="flex items-center gap-3 mt-1">
                    <p v-if="r.data?.hostname" class="text-sm" :class="isDark() ? 'text-cyan-400' : 'text-cyan-600'">{{ r.data.hostname }}</p>
                    <span v-if="r.data?.latency_ms" class="text-xs font-mono px-2 py-0.5 rounded-full" :class="getLatencyColor(r.data.latency_ms)">
                      {{ r.data.latency_ms.toFixed(1) }}ms
                    </span>
                  </div>
                </div>
              </div>
              <div class="flex items-center gap-3">
                <span class="px-4 py-2 rounded-xl text-xs font-bold uppercase tracking-wider"
                  :class="{
                    'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30': r.status === 'success',
                    'bg-slate-700/50 text-slate-300 border border-slate-600': r.status === 'down',
                    'bg-red-500/20 text-red-300 border border-red-500/30': r.status === 'error',
                  }">
                  {{ r.status === 'success' ? '● Activo' : r.status === 'down' ? '○ Inactivo' : 'Error' }}
                </span>
                <ChevronDown class="w-5 h-5 transition-transform duration-300" 
                  :class="[expandedHosts.has(r.host) ? 'rotate-180' : '', isDark() ? 'text-slate-400' : 'text-slate-500']" />
              </div>
            </div>

            <!-- Resumen rápido (siempre visible) -->
            <div v-if="r.data" class="flex flex-wrap items-center gap-3 mt-4">
              <div v-if="r.data.vendor" class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs"
                :class="isDark() ? 'bg-slate-800/80 text-slate-300' : 'bg-slate-100 text-slate-600'">
                <Globe class="w-3.5 h-3.5 text-amber-400" />
                {{ r.data.vendor }}
              </div>
              <div v-if="r.data.mac" class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-mono"
                :class="isDark() ? 'bg-slate-800/80 text-slate-300' : 'bg-slate-100 text-slate-600'">
                <Cpu class="w-3.5 h-3.5 text-purple-400" />
                {{ r.data.mac }}
                <button @click.stop="copyToClipboard(r.data.mac)" class="opacity-0 group-hover:opacity-100 p-0.5 rounded ml-1 transition-all"
                  :class="isDark() ? 'hover:bg-slate-700/50' : 'hover:bg-slate-200'" title="Copiar MAC">
                  <Copy class="w-3 h-3" :class="isDark() ? 'text-slate-500' : 'text-slate-400'" />
                </button>
              </div>
              <div v-if="r.data.os" class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs"
                :class="isDark() ? 'bg-slate-800/80 text-slate-300' : 'bg-slate-100 text-slate-600'">
                <OSIcon :name="r.data.os.name" :size="14" />
                {{ r.data.os.name }}
                <span v-if="r.data.os.accuracy" class="ml-1 opacity-60">({{ r.data.os.accuracy }}%)</span>
              </div>
              <div class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold"
                :class="isDark() ? 'bg-emerald-500/10 text-emerald-300 border border-emerald-500/20' : 'bg-emerald-50 text-emerald-700 border border-emerald-200'">
                <Zap class="w-3.5 h-3.5" />
                {{ r.data.ports?.length || 0 }} puertos
              </div>
              <div class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold"
                :class="isDark() ? 'bg-purple-500/10 text-purple-300 border border-purple-500/20' : 'bg-purple-50 text-purple-700 border border-purple-200'">
                <Server class="w-3.5 h-3.5" />
                {{ r.data.services?.length || 0 }} servicios
              </div>
            </div>
          </div>

          <!-- Detalles expandibles -->
          <div v-if="expandedHosts.has(r.host) && r.data" class="border-t px-5 pb-5 pt-4 space-y-5"
            :class="isDark() ? 'border-slate-800 bg-slate-950/50' : 'border-slate-200 bg-slate-50/50'">
            
            <!-- Tabla de puertos -->
            <div v-if="r.data.ports?.length > 0">
              <h4 class="text-sm font-bold flex items-center gap-2 mb-3" :class="isDark() ? 'text-emerald-400' : 'text-emerald-600'">
                <Zap class="w-4 h-4" />
                Puertos Abiertos ({{ r.data.ports.length }})
              </h4>
              <div class="rounded-xl overflow-hidden border" :class="isDark() ? 'border-slate-800' : 'border-slate-200'">
                <table class="w-full text-sm">
                  <thead>
                    <tr :class="isDark() ? 'bg-slate-800/80' : 'bg-slate-100'">
                      <th class="text-left px-4 py-2.5 font-semibold text-xs uppercase tracking-wider" :class="isDark() ? 'text-slate-400' : 'text-slate-500'">Puerto</th>
                      <th class="text-left px-4 py-2.5 font-semibold text-xs uppercase tracking-wider" :class="isDark() ? 'text-slate-400' : 'text-slate-500'">Protocolo</th>
                      <th class="text-left px-4 py-2.5 font-semibold text-xs uppercase tracking-wider" :class="isDark() ? 'text-slate-400' : 'text-slate-500'">Servicio</th>
                      <th class="text-left px-4 py-2.5 font-semibold text-xs uppercase tracking-wider" :class="isDark() ? 'text-slate-400' : 'text-slate-500'">Categoría</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="(port, pi) in r.data.ports" :key="pi" class="transition-colors"
                      :class="isDark() 
                        ? (pi % 2 === 0 ? 'bg-slate-900/50' : 'bg-slate-900/20') + ' hover:bg-slate-800/70'
                        : (pi % 2 === 0 ? 'bg-white' : 'bg-slate-50') + ' hover:bg-slate-100'">
                      <td class="px-4 py-2.5 font-mono font-bold" :class="isDark() ? 'text-cyan-300' : 'text-cyan-700'">{{ port.port }}</td>
                      <td class="px-4 py-2.5 uppercase text-xs" :class="isDark() ? 'text-slate-400' : 'text-slate-500'">{{ port.protocol || 'tcp' }}</td>
                      <td class="px-4 py-2.5">
                        <span class="px-2 py-0.5 rounded-md text-xs font-medium" :class="isDark() ? 'bg-slate-800 text-slate-300' : 'bg-slate-200 text-slate-700'">
                          {{ port.service || 'unknown' }}
                        </span>
                      </td>
                      <td class="px-4 py-2.5">
                        <span class="px-2 py-0.5 rounded-md text-xs font-medium border bg-gradient-to-r" :class="getPortCategoryColor(port.port)">
                          {{ getPortCategory(port.port) === 'well-known' ? 'Conocidos' : getPortCategory(port.port) === 'registered' ? 'Registrado' : 'Dinámico' }}
                        </span>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>

            <!-- Tabla de servicios -->
            <div v-if="r.data.services?.length > 0">
              <h4 class="text-sm font-bold flex items-center gap-2 mb-3" :class="isDark() ? 'text-purple-400' : 'text-purple-600'">
                <Server class="w-4 h-4" />
                Servicios Detectados ({{ r.data.services.length }})
              </h4>
              <div class="rounded-xl overflow-hidden border" :class="isDark() ? 'border-slate-800' : 'border-slate-200'">
                <table class="w-full text-sm">
                  <thead>
                    <tr :class="isDark() ? 'bg-slate-800/80' : 'bg-slate-100'">
                      <th class="text-left px-4 py-2.5 font-semibold text-xs uppercase tracking-wider" :class="isDark() ? 'text-slate-400' : 'text-slate-500'">Puerto</th>
                      <th class="text-left px-4 py-2.5 font-semibold text-xs uppercase tracking-wider" :class="isDark() ? 'text-slate-400' : 'text-slate-500'">Servicio</th>
                      <th class="text-left px-4 py-2.5 font-semibold text-xs uppercase tracking-wider" :class="isDark() ? 'text-slate-400' : 'text-slate-500'">Producto</th>
                      <th class="text-left px-4 py-2.5 font-semibold text-xs uppercase tracking-wider" :class="isDark() ? 'text-slate-400' : 'text-slate-500'">Versión</th>
                      <th class="text-left px-4 py-2.5 font-semibold text-xs uppercase tracking-wider" :class="isDark() ? 'text-slate-400' : 'text-slate-500'">Extra</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="(svc, si) in r.data.services" :key="si" class="transition-colors"
                      :class="isDark() 
                        ? (si % 2 === 0 ? 'bg-slate-900/50' : 'bg-slate-900/20') + ' hover:bg-slate-800/70'
                        : (si % 2 === 0 ? 'bg-white' : 'bg-slate-50') + ' hover:bg-slate-100'">
                      <td class="px-4 py-2.5 font-mono font-bold" :class="isDark() ? 'text-cyan-300' : 'text-cyan-700'">{{ svc.port }}<span class="text-xs opacity-50">/{{ svc.protocol || 'tcp' }}</span></td>
                      <td class="px-4 py-2.5">
                        <span class="px-2 py-0.5 rounded-md text-xs font-medium" :class="isDark() ? 'bg-purple-500/20 text-purple-300 border border-purple-500/20' : 'bg-purple-100 text-purple-700'">
                          {{ svc.service || 'unknown' }}
                        </span>
                      </td>
                      <td class="px-4 py-2.5 font-medium" :class="isDark() ? 'text-slate-200' : 'text-slate-700'">{{ svc.product || '—' }}</td>
                      <td class="px-4 py-2.5">
                        <span v-if="svc.version" class="px-2 py-0.5 rounded-md text-xs font-mono" :class="isDark() ? 'bg-amber-500/15 text-amber-300 border border-amber-500/20' : 'bg-amber-50 text-amber-700 border border-amber-200'">
                          v{{ svc.version }}
                        </span>
                        <span v-else :class="isDark() ? 'text-slate-600' : 'text-slate-400'">—</span>
                      </td>
                      <td class="px-4 py-2.5 text-xs max-w-[200px] truncate" :class="isDark() ? 'text-slate-500' : 'text-slate-400'" :title="svc.extra">{{ svc.extra || '—' }}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>

            <!-- OS detallado -->
            <div v-if="r.data.os" class="flex items-center gap-4 p-4 rounded-xl" :class="isDark() ? 'bg-slate-800/50' : 'bg-blue-50'">
              <OSIcon :name="r.data.os.name" :size="36" :stroke-width="1.2" />
              <div class="flex-1">
                <p class="font-semibold" :class="isDark() ? 'text-slate-200' : 'text-slate-700'">{{ r.data.os.name }}</p>
                <div v-if="r.data.os.accuracy" class="mt-2 flex items-center gap-3">
                  <div class="flex-1 h-2 rounded-full overflow-hidden" :class="isDark() ? 'bg-slate-700' : 'bg-slate-200'">
                    <div class="h-full rounded-full transition-all duration-500 bg-gradient-to-r from-blue-500 to-cyan-400" :style="{ width: r.data.os.accuracy + '%' }"></div>
                  </div>
                  <span class="text-xs font-bold" :class="isDark() ? 'text-blue-300' : 'text-blue-600'">{{ r.data.os.accuracy }}%</span>
                </div>
              </div>
            </div>

            <!-- Latencia detallada -->
            <div v-if="r.data.latency_ms" class="flex items-center gap-3 p-3 rounded-xl" :class="isDark() ? 'bg-slate-800/30' : 'bg-slate-50'">
              <Zap class="w-4 h-4" :class="getLatencyColor(r.data.latency_ms)" />
              <span class="text-sm font-medium" :class="isDark() ? 'text-slate-300' : 'text-slate-600'">Latencia:</span>
              <span class="font-mono font-bold" :class="getLatencyColor(r.data.latency_ms)">{{ r.data.latency_ms.toFixed(2) }} ms</span>
              <span class="text-xs px-2 py-0.5 rounded-full" :class="isDark() ? 'bg-slate-800 text-slate-400' : 'bg-slate-200 text-slate-600'">
                {{ getLatencyLabel(r.data.latency_ms) }}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- ═══════════════════════════════════════════════════════════ -->
    <!-- RESULTADOS EN TIEMPO REAL - RANGO - MEJORADOS -->
    <!-- ═══════════════════════════════════════════════════════════ -->
    <div v-if="liveResults.length > 0" class="space-y-5">
      
      <!-- Header con estadísticas -->
      <div class="flex items-center justify-between flex-wrap gap-3">
        <h3 class="text-2xl font-bold flex items-center gap-3" :class="isDark() ? 'text-white' : 'text-slate-800'">
          <div class="w-10 h-10 bg-emerald-500/20 rounded-xl flex items-center justify-center">
            <CheckCircle class="w-5 h-5 text-emerald-400" />
          </div>
          Resultados en Tiempo Real
        </h3>
      </div>

      <!-- Stats bar -->
      <div class="grid grid-cols-2 md:grid-cols-4 gap-3">
        <div class="flex items-center gap-3 p-3 rounded-xl border"
          :class="isDark() ? 'bg-emerald-500/5 border-emerald-500/20' : 'bg-emerald-50 border-emerald-200'">
          <div class="w-10 h-10 rounded-lg flex items-center justify-center" :class="isDark() ? 'bg-emerald-500/20' : 'bg-emerald-100'">
            <CheckCircle class="w-5 h-5 text-emerald-400" />
          </div>
          <div>
            <p class="text-2xl font-bold" :class="isDark() ? 'text-emerald-300' : 'text-emerald-600'">{{ scanStats.up }}</p>
            <p class="text-xs" :class="isDark() ? 'text-slate-400' : 'text-slate-500'">Activos</p>
          </div>
        </div>
        <div class="flex items-center gap-3 p-3 rounded-xl border"
          :class="isDark() ? 'bg-red-500/5 border-red-500/20' : 'bg-red-50 border-red-200'">
          <div class="w-10 h-10 rounded-lg flex items-center justify-center" :class="isDark() ? 'bg-red-500/20' : 'bg-red-100'">
            <XCircle class="w-5 h-5 text-red-400" />
          </div>
          <div>
            <p class="text-2xl font-bold" :class="isDark() ? 'text-red-300' : 'text-red-600'">{{ liveResults.length - scanStats.up }}</p>
            <p class="text-xs" :class="isDark() ? 'text-slate-400' : 'text-slate-500'">Inactivos</p>
          </div>
        </div>
        <div class="flex items-center gap-3 p-3 rounded-xl border"
          :class="isDark() ? 'bg-cyan-500/5 border-cyan-500/20' : 'bg-cyan-50 border-cyan-200'">
          <div class="w-10 h-10 rounded-lg flex items-center justify-center" :class="isDark() ? 'bg-cyan-500/20' : 'bg-cyan-100'">
            <Zap class="w-5 h-5 text-cyan-400" />
          </div>
          <div>
            <p class="text-2xl font-bold" :class="isDark() ? 'text-cyan-300' : 'text-cyan-600'">{{ scanStats.totalPorts }}</p>
            <p class="text-xs" :class="isDark() ? 'text-slate-400' : 'text-slate-500'">Puertos</p>
          </div>
        </div>
        <div class="flex items-center gap-3 p-3 rounded-xl border"
          :class="isDark() ? 'bg-purple-500/5 border-purple-500/20' : 'bg-purple-50 border-purple-200'">
          <div class="w-10 h-10 rounded-lg flex items-center justify-center" :class="isDark() ? 'bg-purple-500/20' : 'bg-purple-100'">
            <Server class="w-5 h-5 text-purple-400" />
          </div>
          <div>
            <p class="text-2xl font-bold" :class="isDark() ? 'text-purple-300' : 'text-purple-600'">{{ scanStats.totalServices }}</p>
            <p class="text-xs" :class="isDark() ? 'text-slate-400' : 'text-slate-500'">Servicios</p>
          </div>
        </div>
      </div>

      <!-- Barra de herramientas: búsqueda, filtros, orden -->
      <div class="flex flex-wrap items-center gap-3 p-4 rounded-xl border"
        :class="isDark() ? 'bg-slate-900/80 border-slate-800' : 'bg-white border-slate-200'">
        
        <!-- Búsqueda -->
        <div class="relative flex-1 min-w-[200px]">
          <Search class="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2" :class="isDark() ? 'text-slate-500' : 'text-slate-400'" />
          <input v-model="resultSearchQuery" type="text" placeholder="Buscar IP, hostname, servicio, vendor..."
            class="w-full pl-10 pr-4 py-2.5 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-cyan-500/50"
            :class="isDark() ? 'bg-slate-800 border border-slate-700 text-white placeholder-slate-500' : 'bg-slate-50 border border-slate-300 text-slate-800 placeholder-slate-400'" />
        </div>

        <!-- Toggle inactivos -->
        <button @click="showInactive = !showInactive" class="flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium transition-all border"
          :class="showInactive
            ? (isDark() ? 'bg-cyan-500/20 border-cyan-500/30 text-cyan-300' : 'bg-cyan-100 border-cyan-300 text-cyan-700')
            : (isDark() ? 'bg-slate-800 border-slate-700 text-slate-400 hover:border-slate-600' : 'bg-slate-50 border-slate-300 text-slate-500 hover:border-slate-400')">
          <Eye v-if="showInactive" class="w-4 h-4" />
          <EyeOff v-else class="w-4 h-4" />
          Inactivos
        </button>

        <!-- Ordenar -->
        <div class="flex items-center gap-1 border rounded-lg overflow-hidden" :class="isDark() ? 'border-slate-700' : 'border-slate-300'">
          <button v-for="sortOpt in [{key: 'host', label: 'IP'}, {key: 'ports', label: 'Puertos'}, {key: 'services', label: 'Servicios'}, {key: 'latency', label: 'Latencia'}]"
            :key="sortOpt.key" @click="toggleSort(sortOpt.key)"
            class="px-3 py-2 text-xs font-medium transition-all flex items-center gap-1"
            :class="resultSortKey === sortOpt.key
              ? (isDark() ? 'bg-cyan-500/20 text-cyan-300' : 'bg-cyan-100 text-cyan-700')
              : (isDark() ? 'text-slate-400 hover:bg-slate-800' : 'text-slate-500 hover:bg-slate-100')">
            {{ sortOpt.label }}
            <ArrowUpDown v-if="resultSortKey === sortOpt.key" class="w-3 h-3" :class="resultSortAsc ? '' : 'rotate-180'" />
          </button>
        </div>

        <!-- Expandir/colapsar todo -->
        <div class="flex gap-1">
          <button @click="expandAll" class="p-2 rounded-lg transition-all" title="Expandir todo"
            :class="isDark() ? 'hover:bg-slate-800 text-slate-400 hover:text-slate-300' : 'hover:bg-slate-100 text-slate-500 hover:text-slate-700'">
            <ChevronDown class="w-4 h-4" />
          </button>
          <button @click="collapseAll" class="p-2 rounded-lg transition-all" title="Colapsar todo"
            :class="isDark() ? 'hover:bg-slate-800 text-slate-400 hover:text-slate-300' : 'hover:bg-slate-100 text-slate-500 hover:text-slate-700'">
            <ChevronUp class="w-4 h-4" />
          </button>
        </div>
      </div>

      <!-- Contador de resultados filtrados -->
      <div v-if="resultSearchQuery || !showInactive" class="text-xs" :class="isDark() ? 'text-slate-500' : 'text-slate-400'">
        Mostrando {{ filteredLiveResults.length }} de {{ liveResults.length }} resultados
      </div>

      <!-- Tarjetas de resultados mejoradas -->
      <div class="grid gap-4">
        <div v-for="(r, i) in filteredLiveResults" :key="r.host || i"
          class="group border rounded-2xl overflow-hidden transition-all duration-500 animate-fadeIn"
          :class="isDark()
            ? 'bg-gradient-to-br from-slate-900 via-slate-950 to-slate-900 border-slate-700/50 hover:border-cyan-500/30'
            : 'bg-white border-slate-200 hover:border-cyan-400/50'"
        >
          <!-- Header clickable -->
          <div class="p-5 cursor-pointer select-none" @click="toggleHostExpand(r.host)">
            <div class="flex justify-between items-start">
              <div class="flex items-center gap-4">
                <div class="w-14 h-14 rounded-xl flex items-center justify-center relative"
                  :class="(r.status === 'up' || r.status === 'success')
                    ? 'bg-gradient-to-br from-emerald-500/20 to-teal-500/20 border border-emerald-500/30'
                    : 'bg-gradient-to-br from-red-500/10 to-slate-800/50 border border-slate-700'">
                  <Server class="w-6 h-6" :class="(r.status === 'up' || r.status === 'success') ? 'text-emerald-400' : 'text-slate-500'" />
                  <div class="absolute -top-1 -right-1 w-3.5 h-3.5 rounded-full border-2"
                    :class="isDark() ? 'border-slate-900' : 'border-white'"
                    :style="{ backgroundColor: (r.status === 'up' || r.status === 'success') ? '#10b981' : '#64748b' }"></div>
                </div>
                <div>
                  <div class="flex items-center gap-2">
                    <p class="font-mono text-xl font-bold" :class="isDark() ? 'text-white' : 'text-slate-800'">{{ r.host }}</p>
                    <button @click.stop="copyToClipboard(r.host)" class="opacity-0 group-hover:opacity-100 p-1 rounded-md transition-all"
                      :class="isDark() ? 'hover:bg-slate-700/50' : 'hover:bg-slate-200'" title="Copiar IP">
                      <Copy class="w-3.5 h-3.5" :class="isDark() ? 'text-slate-400' : 'text-slate-500'" />
                    </button>
                  </div>
                  <div class="flex items-center gap-3 mt-1">
                    <p v-if="r.hostname" class="text-sm" :class="isDark() ? 'text-cyan-400' : 'text-cyan-600'">{{ r.hostname }}</p>
                    <span v-if="r.latency_ms" class="text-xs font-mono px-2 py-0.5 rounded-full" 
                      :class="isDark() ? 'bg-slate-800/80' : 'bg-slate-100'" >
                      <span :class="getLatencyColor(r.latency_ms)">{{ r.latency_ms.toFixed(1) }}ms</span>
                    </span>
                  </div>
                </div>
              </div>
              <div class="flex items-center gap-3">
                <span class="px-4 py-2 rounded-xl text-xs font-bold uppercase tracking-wider"
                  :class="(r.status === 'up' || r.status === 'success')
                    ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                    : 'bg-slate-700/50 text-slate-400 border border-slate-600'">
                  {{ (r.status === 'up' || r.status === 'success') ? '● Activo' : '○ Inactivo' }}
                </span>
                <ChevronDown class="w-5 h-5 transition-transform duration-300"
                  :class="[expandedHosts.has(r.host) ? 'rotate-180' : '', isDark() ? 'text-slate-400' : 'text-slate-500']" />
              </div>
            </div>

            <!-- Badges resumen rápido -->
            <div class="flex flex-wrap items-center gap-2 mt-4">
              <div v-if="r.vendor" class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs"
                :class="isDark() ? 'bg-slate-800/80 text-slate-300' : 'bg-slate-100 text-slate-600'">
                <Globe class="w-3.5 h-3.5 text-amber-400" />
                {{ r.vendor }}
              </div>
              <div v-if="r.mac" class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-mono"
                :class="isDark() ? 'bg-slate-800/80 text-slate-300' : 'bg-slate-100 text-slate-600'">
                <Cpu class="w-3.5 h-3.5 text-purple-400" />
                {{ r.mac }}
                <button @click.stop="copyToClipboard(r.mac)" class="opacity-0 group-hover:opacity-100 p-0.5 rounded hover:bg-slate-700/50 ml-1">
                  <Copy class="w-3 h-3" :class="isDark() ? 'text-slate-500' : 'text-slate-400'" />
                </button>
              </div>
              <div v-if="r.os?.name" class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs"
                :class="isDark() ? 'bg-slate-800/80 text-slate-300' : 'bg-slate-100 text-slate-600'">
                <OSIcon :name="r.os.name" :size="14" />
                {{ r.os.name }}
                <span v-if="r.os.accuracy" class="ml-1 opacity-60">({{ r.os.accuracy }}%)</span>
              </div>
              <div v-if="r.ports?.length" class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold"
                :class="isDark() ? 'bg-emerald-500/10 text-emerald-300 border border-emerald-500/20' : 'bg-emerald-50 text-emerald-700 border border-emerald-200'">
                <Zap class="w-3.5 h-3.5" />
                {{ r.ports.length }} puertos
              </div>
              <div v-if="r.services?.length" class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold"
                :class="isDark() ? 'bg-purple-500/10 text-purple-300 border border-purple-500/20' : 'bg-purple-50 text-purple-700 border border-purple-200'">
                <Server class="w-3.5 h-3.5" />
                {{ r.services.length }} servicios
              </div>
            </div>
          </div>

          <!-- Detalles expandidos -->
          <div v-if="expandedHosts.has(r.host) && (r.status === 'up' || r.status === 'success')" 
            class="border-t px-5 pb-5 pt-4 space-y-5 animate-slideDown"
            :class="isDark() ? 'border-slate-800 bg-slate-950/50' : 'border-slate-200 bg-slate-50/50'">
            
            <!-- Tabla de puertos -->
            <div v-if="r.ports?.length > 0">
              <h4 class="text-sm font-bold flex items-center gap-2 mb-3" :class="isDark() ? 'text-emerald-400' : 'text-emerald-600'">
                <Zap class="w-4 h-4" />
                Puertos Abiertos ({{ r.ports.length }})
              </h4>
              <div class="rounded-xl overflow-hidden border" :class="isDark() ? 'border-slate-800' : 'border-slate-200'">
                <div class="overflow-x-auto">
                  <table class="w-full text-sm">
                    <thead>
                      <tr :class="isDark() ? 'bg-slate-800/80' : 'bg-slate-100'">
                        <th class="text-left px-4 py-2.5 font-semibold text-xs uppercase tracking-wider" :class="isDark() ? 'text-slate-400' : 'text-slate-500'">Puerto</th>
                        <th class="text-left px-4 py-2.5 font-semibold text-xs uppercase tracking-wider" :class="isDark() ? 'text-slate-400' : 'text-slate-500'">Protocolo</th>
                        <th class="text-left px-4 py-2.5 font-semibold text-xs uppercase tracking-wider" :class="isDark() ? 'text-slate-400' : 'text-slate-500'">Servicio</th>
                        <th class="text-left px-4 py-2.5 font-semibold text-xs uppercase tracking-wider" :class="isDark() ? 'text-slate-400' : 'text-slate-500'">Categoría</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr v-for="(port, pi) in r.ports" :key="pi" class="transition-colors"
                        :class="isDark() 
                          ? (pi % 2 === 0 ? 'bg-slate-900/50' : 'bg-slate-900/20') + ' hover:bg-slate-800/70'
                          : (pi % 2 === 0 ? 'bg-white' : 'bg-slate-50') + ' hover:bg-slate-100'">
                        <td class="px-4 py-2.5 font-mono font-bold" :class="isDark() ? 'text-cyan-300' : 'text-cyan-700'">{{ port.port || port }}</td>
                        <td class="px-4 py-2.5 uppercase text-xs" :class="isDark() ? 'text-slate-400' : 'text-slate-500'">{{ port.protocol || 'tcp' }}</td>
                        <td class="px-4 py-2.5">
                          <span class="px-2 py-0.5 rounded-md text-xs font-medium" :class="isDark() ? 'bg-slate-800 text-slate-300' : 'bg-slate-200 text-slate-700'">
                            {{ port.service || 'unknown' }}
                          </span>
                        </td>
                        <td class="px-4 py-2.5">
                          <span class="px-2 py-0.5 rounded-md text-xs font-medium border bg-gradient-to-r" :class="getPortCategoryColor(port.port || port)">
                            {{ getPortCategory(port.port || port) === 'well-known' ? 'Conocidos' : getPortCategory(port.port || port) === 'registered' ? 'Registrado' : 'Dinámico' }}
                          </span>
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>
            </div>

            <!-- Tabla de servicios -->
            <div v-if="r.services?.length > 0">
              <h4 class="text-sm font-bold flex items-center gap-2 mb-3" :class="isDark() ? 'text-purple-400' : 'text-purple-600'">
                <Server class="w-4 h-4" />
                Servicios Detectados ({{ r.services.length }})
              </h4>
              <div class="rounded-xl overflow-hidden border" :class="isDark() ? 'border-slate-800' : 'border-slate-200'">
                <div class="overflow-x-auto">
                  <table class="w-full text-sm">
                    <thead>
                      <tr :class="isDark() ? 'bg-slate-800/80' : 'bg-slate-100'">
                        <th class="text-left px-4 py-2.5 font-semibold text-xs uppercase tracking-wider" :class="isDark() ? 'text-slate-400' : 'text-slate-500'">Puerto</th>
                        <th class="text-left px-4 py-2.5 font-semibold text-xs uppercase tracking-wider" :class="isDark() ? 'text-slate-400' : 'text-slate-500'">Servicio</th>
                        <th class="text-left px-4 py-2.5 font-semibold text-xs uppercase tracking-wider" :class="isDark() ? 'text-slate-400' : 'text-slate-500'">Producto</th>
                        <th class="text-left px-4 py-2.5 font-semibold text-xs uppercase tracking-wider" :class="isDark() ? 'text-slate-400' : 'text-slate-500'">Versión</th>
                        <th class="text-left px-4 py-2.5 font-semibold text-xs uppercase tracking-wider" :class="isDark() ? 'text-slate-400' : 'text-slate-500'">Extra</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr v-for="(svc, si) in r.services" :key="si" class="transition-colors"
                        :class="isDark() 
                          ? (si % 2 === 0 ? 'bg-slate-900/50' : 'bg-slate-900/20') + ' hover:bg-slate-800/70'
                          : (si % 2 === 0 ? 'bg-white' : 'bg-slate-50') + ' hover:bg-slate-100'">
                        <td class="px-4 py-2.5 font-mono font-bold" :class="isDark() ? 'text-cyan-300' : 'text-cyan-700'">
                          {{ svc.port }}<span class="text-xs opacity-50">/{{ svc.protocol || 'tcp' }}</span>
                        </td>
                        <td class="px-4 py-2.5">
                          <span class="px-2 py-0.5 rounded-md text-xs font-medium" :class="isDark() ? 'bg-purple-500/20 text-purple-300 border border-purple-500/20' : 'bg-purple-100 text-purple-700'">
                            {{ svc.service || 'unknown' }}
                          </span>
                        </td>
                        <td class="px-4 py-2.5 font-medium" :class="isDark() ? 'text-slate-200' : 'text-slate-700'">{{ svc.product || '—' }}</td>
                        <td class="px-4 py-2.5">
                          <span v-if="svc.version" class="px-2 py-0.5 rounded-md text-xs font-mono" :class="isDark() ? 'bg-amber-500/15 text-amber-300 border border-amber-500/20' : 'bg-amber-50 text-amber-700 border border-amber-200'">
                            v{{ svc.version }}
                          </span>
                          <span v-else :class="isDark() ? 'text-slate-600' : 'text-slate-400'">—</span>
                        </td>
                        <td class="px-4 py-2.5 text-xs max-w-[200px] truncate" :class="isDark() ? 'text-slate-500' : 'text-slate-400'" :title="svc.extra">{{ svc.extra || '—' }}</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>
            </div>

            <!-- OS detallado -->
            <div v-if="r.os" class="flex items-center gap-4 p-4 rounded-xl" :class="isDark() ? 'bg-slate-800/50' : 'bg-blue-50'">
              <OSIcon :name="r.os.name" :size="36" :stroke-width="1.2" />
              <div class="flex-1">
                <p class="font-semibold" :class="isDark() ? 'text-slate-200' : 'text-slate-700'">{{ r.os.name }}</p>
                <div v-if="r.os.accuracy" class="mt-2 flex items-center gap-3">
                  <div class="flex-1 h-2 rounded-full overflow-hidden" :class="isDark() ? 'bg-slate-700' : 'bg-slate-200'">
                    <div class="h-full rounded-full transition-all duration-500 bg-gradient-to-r from-blue-500 to-cyan-400" :style="{ width: r.os.accuracy + '%' }"></div>
                  </div>
                  <span class="text-xs font-bold" :class="isDark() ? 'text-blue-300' : 'text-blue-600'">{{ r.os.accuracy }}%</span>
                </div>
              </div>
            </div>

            <!-- Latencia -->
            <div v-if="r.latency_ms" class="flex items-center gap-3 p-3 rounded-xl" :class="isDark() ? 'bg-slate-800/30' : 'bg-slate-50'">
              <Zap class="w-4 h-4" :class="getLatencyColor(r.latency_ms)" />
              <span class="text-sm font-medium" :class="isDark() ? 'text-slate-300' : 'text-slate-600'">Latencia:</span>
              <span class="font-mono font-bold" :class="getLatencyColor(r.latency_ms)">{{ r.latency_ms.toFixed(2) }} ms</span>
              <span class="text-xs px-2 py-0.5 rounded-full" :class="isDark() ? 'bg-slate-800 text-slate-400' : 'bg-slate-200 text-slate-600'">
                {{ getLatencyLabel(r.latency_ms) }}
              </span>
            </div>

            <!-- Sin datos de puertos ni servicios -->
            <div v-if="!r.ports?.length && !r.services?.length" class="text-center py-6" :class="isDark() ? 'text-slate-500' : 'text-slate-400'">
              <Shield class="w-8 h-8 mx-auto mb-2 opacity-50" />
              <p class="text-sm">No se detectaron puertos ni servicios abiertos</p>
            </div>
          </div>
        </div>
      </div>

      <!-- Resumen final cuando se completó -->
      <div v-if="scanPhase === 'completed'" class="border rounded-2xl p-6"
        :class="isDark()
          ? 'bg-gradient-to-r from-emerald-900/20 to-teal-900/20 border-emerald-700/30'
          : 'bg-gradient-to-r from-emerald-50 to-teal-50 border-emerald-200'">
        <div class="flex items-center justify-between mb-4">
          <div class="flex items-center gap-3">
            <CheckCircle class="w-6 h-6 text-emerald-400" />
            <h4 class="font-bold text-lg" :class="isDark() ? 'text-emerald-300' : 'text-emerald-700'">Escaneo Completado</h4>
          </div>
          <span class="text-xs" :class="isDark() ? 'text-slate-500' : 'text-slate-400'">{{ new Date().toLocaleTimeString() }}</span>
        </div>
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div class="text-center p-3 rounded-xl" :class="isDark() ? 'bg-slate-900/50' : 'bg-white/80'">
            <p class="text-3xl font-bold text-cyan-400">{{ totalHosts }}</p>
            <p class="text-xs mt-1" :class="isDark() ? 'text-slate-400' : 'text-slate-500'">Total IPs</p>
          </div>
          <div class="text-center p-3 rounded-xl" :class="isDark() ? 'bg-slate-900/50' : 'bg-white/80'">
            <p class="text-3xl font-bold text-emerald-400">{{ totalActive }}</p>
            <p class="text-xs mt-1" :class="isDark() ? 'text-slate-400' : 'text-slate-500'">Activos</p>
            <div class="mt-1 h-1 rounded-full overflow-hidden" :class="isDark() ? 'bg-slate-800' : 'bg-slate-200'">
              <div class="h-full rounded-full bg-emerald-400 transition-all" :style="{ width: (totalHosts > 0 ? (totalActive/totalHosts*100) : 0) + '%' }"></div>
            </div>
          </div>
          <div class="text-center p-3 rounded-xl" :class="isDark() ? 'bg-slate-900/50' : 'bg-white/80'">
            <p class="text-3xl font-bold text-cyan-400">{{ scanStats.totalPorts }}</p>
            <p class="text-xs mt-1" :class="isDark() ? 'text-slate-400' : 'text-slate-500'">Puertos</p>
          </div>
          <div class="text-center p-3 rounded-xl" :class="isDark() ? 'bg-slate-900/50' : 'bg-white/80'">
            <p class="text-3xl font-bold text-purple-400">{{ scanStats.totalServices }}</p>
            <p class="text-xs mt-1" :class="isDark() ? 'text-slate-400' : 'text-slate-500'">Servicios</p>
          </div>
        </div>
      </div>
    </div>

    <!-- ═══════════════════════════════════════════════════════════ -->
    <!-- HISTORIAL DE ESCANEOS FULLSCAN -->
    <!-- ═══════════════════════════════════════════════════════════ -->
    <div class="border-t pt-6" :class="isDark() ? 'border-slate-800' : 'border-slate-200'">
      <button @click="showHistory = !showHistory; if (showHistory && !historyItems.length) loadHistory()"
        class="w-full flex items-center justify-between p-4 rounded-xl transition-all"
        :class="isDark() ? 'bg-slate-900/80 hover:bg-slate-800/80 border border-slate-700/50' : 'bg-slate-50 hover:bg-slate-100 border border-slate-200'">
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 rounded-xl flex items-center justify-center" :class="isDark() ? 'bg-indigo-500/20' : 'bg-indigo-100'">
            <Clock class="w-5 h-5" :class="isDark() ? 'text-indigo-400' : 'text-indigo-600'" />
          </div>
          <div class="text-left">
            <h3 class="font-bold text-lg" :class="isDark() ? 'text-white' : 'text-slate-800'">Historial de Escaneos</h3>
            <p class="text-xs" :class="isDark() ? 'text-slate-400' : 'text-slate-500'">Registro de todos los escaneos realizados</p>
          </div>
        </div>
        <div class="flex items-center gap-3">
          <span v-if="historyTotal > 0" class="px-3 py-1 rounded-lg text-xs font-bold" :class="isDark() ? 'bg-indigo-500/20 text-indigo-300' : 'bg-indigo-100 text-indigo-700'">
            {{ historyTotal }} registros
          </span>
          <ChevronDown class="w-5 h-5 transition-transform duration-300" :class="[showHistory ? 'rotate-180' : '', isDark() ? 'text-slate-400' : 'text-slate-500']" />
        </div>
      </button>

      <div v-if="showHistory" class="mt-4 space-y-4 animate-slideDown">
        <!-- Toolbar -->
        <div class="flex items-center justify-between">
          <button @click="loadHistory" class="flex items-center gap-2 px-3 py-2 rounded-lg text-sm transition-all"
            :class="isDark() ? 'bg-slate-800 hover:bg-slate-700 text-slate-300' : 'bg-slate-100 hover:bg-slate-200 text-slate-600'">
            <RefreshCw class="w-4 h-4" :class="{ 'animate-spin': loadingHistory }" />
            Actualizar
          </button>
          <button v-if="historyTotal > 0" @click="clearHistory" class="flex items-center gap-2 px-3 py-2 rounded-lg text-sm transition-all"
            :class="isDark() ? 'bg-red-500/10 hover:bg-red-500/20 text-red-400' : 'bg-red-50 hover:bg-red-100 text-red-600'">
            <X class="w-4 h-4" />
            Limpiar todo
          </button>
        </div>

        <!-- Loading -->
        <div v-if="loadingHistory" class="text-center py-8">
          <Loader2 class="w-6 h-6 animate-spin mx-auto mb-2" :class="isDark() ? 'text-indigo-400' : 'text-indigo-600'" />
          <p class="text-sm" :class="isDark() ? 'text-slate-400' : 'text-slate-500'">Cargando historial...</p>
        </div>

        <!-- Empty -->
        <div v-else-if="!historyItems.length" class="text-center py-12 rounded-xl border"
          :class="isDark() ? 'bg-slate-900/50 border-slate-800' : 'bg-slate-50 border-slate-200'">
          <Clock class="w-10 h-10 mx-auto mb-3 opacity-30" :class="isDark() ? 'text-slate-500' : 'text-slate-400'" />
          <p class="font-medium" :class="isDark() ? 'text-slate-400' : 'text-slate-500'">No hay escaneos registrados</p>
          <p class="text-xs mt-1" :class="isDark() ? 'text-slate-500' : 'text-slate-400'">Los escaneos se guardarán automáticamente</p>
        </div>

        <!-- Table -->
        <div v-else class="rounded-xl overflow-hidden border" :class="isDark() ? 'border-slate-800' : 'border-slate-200'">
          <div class="overflow-x-auto">
            <table class="w-full text-sm">
              <thead>
                <tr :class="isDark() ? 'bg-slate-800/80' : 'bg-slate-100'">
                  <th class="text-left px-4 py-3 font-semibold text-xs uppercase tracking-wider" :class="isDark() ? 'text-slate-400' : 'text-slate-500'">Fecha</th>
                  <th class="text-left px-4 py-3 font-semibold text-xs uppercase tracking-wider" :class="isDark() ? 'text-slate-400' : 'text-slate-500'">Usuario</th>
                  <th class="text-left px-4 py-3 font-semibold text-xs uppercase tracking-wider" :class="isDark() ? 'text-slate-400' : 'text-slate-500'">Tipo</th>
                  <th class="text-left px-4 py-3 font-semibold text-xs uppercase tracking-wider" :class="isDark() ? 'text-slate-400' : 'text-slate-500'">Objetivo</th>
                  <th class="text-center px-4 py-3 font-semibold text-xs uppercase tracking-wider" :class="isDark() ? 'text-slate-400' : 'text-slate-500'">Hosts</th>
                  <th class="text-center px-4 py-3 font-semibold text-xs uppercase tracking-wider" :class="isDark() ? 'text-slate-400' : 'text-slate-500'">Activos</th>
                  <th class="text-center px-4 py-3 font-semibold text-xs uppercase tracking-wider" :class="isDark() ? 'text-slate-400' : 'text-slate-500'">Puertos</th>
                  <th class="text-center px-4 py-3 font-semibold text-xs uppercase tracking-wider" :class="isDark() ? 'text-slate-400' : 'text-slate-500'">Servicios</th>
                  <th class="text-center px-4 py-3 font-semibold text-xs uppercase tracking-wider" :class="isDark() ? 'text-slate-400' : 'text-slate-500'">Duración</th>
                  <th class="text-center px-4 py-3 font-semibold text-xs uppercase tracking-wider" :class="isDark() ? 'text-slate-400' : 'text-slate-500'">Estado</th>
                  <th class="text-center px-4 py-3 font-semibold text-xs uppercase tracking-wider" :class="isDark() ? 'text-slate-400' : 'text-slate-500'">Acciones</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(entry, idx) in historyItems" :key="entry.id" class="transition-colors"
                  :class="isDark()
                    ? (idx % 2 === 0 ? 'bg-slate-900/50' : 'bg-slate-900/20') + ' hover:bg-slate-800/70'
                    : (idx % 2 === 0 ? 'bg-white' : 'bg-slate-50') + ' hover:bg-slate-100'">
                  <td class="px-4 py-3 text-xs" :class="isDark() ? 'text-slate-300' : 'text-slate-600'">
                    {{ formatHistoryDate(entry.created_at) }}
                  </td>
                  <td class="px-4 py-3">
                    <span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-xs font-medium"
                      :class="isDark() ? 'bg-blue-500/20 text-blue-300' : 'bg-blue-100 text-blue-700'">
                      {{ entry.username || 'Sistema' }}
                    </span>
                  </td>
                  <td class="px-4 py-3">
                    <span class="px-2 py-0.5 rounded-md text-xs font-medium"
                      :class="entry.scan_type === 'single'
                        ? (isDark() ? 'bg-cyan-500/20 text-cyan-300' : 'bg-cyan-100 text-cyan-700')
                        : (isDark() ? 'bg-purple-500/20 text-purple-300' : 'bg-purple-100 text-purple-700')">
                      {{ entry.scan_type === 'single' ? 'Individual' : 'Rango' }}
                    </span>
                  </td>
                  <td class="px-4 py-3 font-mono text-xs" :class="isDark() ? 'text-slate-200' : 'text-slate-800'">
                    {{ entry.target }}
                  </td>
                  <td class="px-4 py-3 text-center font-bold" :class="isDark() ? 'text-slate-200' : 'text-slate-700'">
                    {{ entry.hosts_scanned }}
                  </td>
                  <td class="px-4 py-3 text-center">
                    <span class="font-bold" :class="isDark() ? 'text-emerald-400' : 'text-emerald-600'">{{ entry.hosts_active }}</span>
                  </td>
                  <td class="px-4 py-3 text-center">
                    <span class="font-bold" :class="isDark() ? 'text-cyan-400' : 'text-cyan-600'">{{ entry.total_ports }}</span>
                  </td>
                  <td class="px-4 py-3 text-center">
                    <span class="font-bold" :class="isDark() ? 'text-purple-400' : 'text-purple-600'">{{ entry.total_services }}</span>
                  </td>
                  <td class="px-4 py-3 text-center text-xs font-mono" :class="isDark() ? 'text-slate-400' : 'text-slate-500'">
                    {{ formatDurationShort(entry.duration_seconds) }}
                  </td>
                  <td class="px-4 py-3 text-center">
                    <span class="px-2 py-0.5 rounded-full text-xs font-bold"
                      :class="{
                        'bg-emerald-500/20 text-emerald-300': entry.status === 'success',
                        'bg-red-500/20 text-red-300': entry.status === 'error',
                        'bg-amber-500/20 text-amber-300': entry.status === 'cancelled',
                      }">
                      <svg v-if="entry.status === 'success'" class="w-3.5 h-3.5 inline" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
                      <svg v-else-if="entry.status === 'cancelled'" class="w-3.5 h-3.5 inline" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="4.93" y1="4.93" x2="19.07" y2="19.07"/></svg>
                      <svg v-else class="w-3.5 h-3.5 inline" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
                    </span>
                  </td>
                  <td class="px-4 py-3 text-center">
                    <div class="flex items-center justify-center gap-1">
                      <button @click="viewHistoryDetail(entry.id)" class="p-1.5 rounded-lg transition-all" title="Ver detalle"
                        :class="isDark() ? 'hover:bg-slate-700 text-cyan-400' : 'hover:bg-slate-200 text-cyan-600'">
                        <Eye class="w-4 h-4" />
                      </button>
                      <button @click="deleteHistoryEntry(entry.id)" class="p-1.5 rounded-lg transition-all" title="Eliminar"
                        :class="isDark() ? 'hover:bg-red-500/20 text-red-400' : 'hover:bg-red-100 text-red-600'">
                        <X class="w-4 h-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- Pagination -->
          <div v-if="historyTotal > historyLimit" class="flex items-center justify-between px-4 py-3 border-t"
            :class="isDark() ? 'border-slate-700/50 bg-slate-800/50' : 'border-slate-200 bg-slate-50'">
            <span class="text-xs" :class="isDark() ? 'text-slate-400' : 'text-slate-500'">
              Mostrando {{ historyItems.length }} de {{ historyTotal }}
            </span>
            <div class="flex items-center gap-2">
              <button @click="historyPage > 0 && (historyPage--, loadHistory())" :disabled="historyPage === 0"
                class="px-3 py-1.5 rounded-lg text-xs font-medium transition-all"
                :class="historyPage === 0 ? (isDark() ? 'text-slate-600 cursor-not-allowed' : 'text-slate-300 cursor-not-allowed') : (isDark() ? 'bg-slate-700 text-slate-300 hover:bg-slate-600' : 'bg-slate-200 text-slate-700 hover:bg-slate-300')">
                ← Anterior
              </button>
              <span class="text-xs" :class="isDark() ? 'text-slate-400' : 'text-slate-500'">
                {{ historyPage + 1 }} / {{ Math.ceil(historyTotal / historyLimit) }}
              </span>
              <button @click="(historyPage + 1) * historyLimit < historyTotal && (historyPage++, loadHistory())"
                :disabled="(historyPage + 1) * historyLimit >= historyTotal"
                class="px-3 py-1.5 rounded-lg text-xs font-medium transition-all"
                :class="(historyPage + 1) * historyLimit >= historyTotal ? (isDark() ? 'text-slate-600 cursor-not-allowed' : 'text-slate-300 cursor-not-allowed') : (isDark() ? 'bg-slate-700 text-slate-300 hover:bg-slate-600' : 'bg-slate-200 text-slate-700 hover:bg-slate-300')">
                Siguiente →
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Modal Detalle Historial -->
    <teleport to="body">
      <div v-if="showHistoryDetail"
        class="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 p-4 overflow-y-auto"
        @click.self="showHistoryDetail = false">
        <div class="rounded-2xl p-6 max-w-5xl w-full shadow-2xl my-8 max-h-[calc(100vh-4rem)] overflow-y-auto"
          :class="isDark() ? 'bg-gradient-to-br from-slate-900 via-slate-950 to-slate-900 border border-slate-700/50' : 'bg-white border border-slate-200'">
          
          <div class="flex items-center justify-between mb-6">
            <h3 class="text-xl font-bold flex items-center gap-3" :class="isDark() ? 'text-white' : 'text-slate-800'">
              <div class="w-10 h-10 rounded-xl flex items-center justify-center" :class="isDark() ? 'bg-indigo-500/20' : 'bg-indigo-100'">
                <Eye class="w-5 h-5" :class="isDark() ? 'text-indigo-400' : 'text-indigo-600'" />
              </div>
              Detalle del Escaneo
            </h3>
            <button @click="showHistoryDetail = false" class="p-1.5 rounded-lg transition-colors" :class="isDark() ? 'hover:bg-slate-800' : 'hover:bg-slate-200'">
              <X class="w-5 h-5" :class="isDark() ? 'text-slate-400' : 'text-slate-600'" />
            </button>
          </div>

          <div v-if="loadingHistoryDetail" class="text-center py-12">
            <Loader2 class="w-8 h-8 animate-spin mx-auto mb-3" :class="isDark() ? 'text-indigo-400' : 'text-indigo-600'" />
            <p class="text-sm" :class="isDark() ? 'text-slate-400' : 'text-slate-500'">Cargando detalle...</p>
          </div>

          <div v-else-if="historyDetail" class="space-y-5">
            <!-- Info cards -->
            <div class="grid grid-cols-2 md:grid-cols-4 gap-3">
              <div class="rounded-xl p-3 border text-center" :class="isDark() ? 'bg-slate-800/50 border-slate-700/50' : 'bg-slate-50 border-slate-200'">
                <p class="text-2xl font-bold" :class="isDark() ? 'text-cyan-400' : 'text-cyan-600'">{{ historyDetail.hosts_scanned }}</p>
                <p class="text-xs mt-1" :class="isDark() ? 'text-slate-400' : 'text-slate-500'">Escaneados</p>
              </div>
              <div class="rounded-xl p-3 border text-center" :class="isDark() ? 'bg-slate-800/50 border-slate-700/50' : 'bg-slate-50 border-slate-200'">
                <p class="text-2xl font-bold" :class="isDark() ? 'text-emerald-400' : 'text-emerald-600'">{{ historyDetail.hosts_active }}</p>
                <p class="text-xs mt-1" :class="isDark() ? 'text-slate-400' : 'text-slate-500'">Activos</p>
              </div>
              <div class="rounded-xl p-3 border text-center" :class="isDark() ? 'bg-slate-800/50 border-slate-700/50' : 'bg-slate-50 border-slate-200'">
                <p class="text-2xl font-bold" :class="isDark() ? 'text-cyan-400' : 'text-cyan-600'">{{ historyDetail.total_ports }}</p>
                <p class="text-xs mt-1" :class="isDark() ? 'text-slate-400' : 'text-slate-500'">Puertos</p>
              </div>
              <div class="rounded-xl p-3 border text-center" :class="isDark() ? 'bg-slate-800/50 border-slate-700/50' : 'bg-slate-50 border-slate-200'">
                <p class="text-2xl font-bold" :class="isDark() ? 'text-purple-400' : 'text-purple-600'">{{ historyDetail.total_services }}</p>
                <p class="text-xs mt-1" :class="isDark() ? 'text-slate-400' : 'text-slate-500'">Servicios</p>
              </div>
            </div>

            <!-- Meta info -->
            <div class="flex flex-wrap items-center gap-3 text-sm">
              <span class="px-3 py-1.5 rounded-lg flex items-center gap-1.5" :class="isDark() ? 'bg-slate-800 text-slate-300' : 'bg-slate-100 text-slate-600'">
                <svg v-if="historyDetail.scan_type === 'single'" class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/></svg>
                <svg v-else class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2 12h6"/><path d="M22 12h-6"/><path d="M12 2v6"/><path d="M12 22v-6"/><circle cx="12" cy="12" r="4"/></svg>
                {{ historyDetail.scan_type === 'single' ? 'Individual' : 'Rango' }}
              </span>
              <span class="px-3 py-1.5 rounded-lg font-mono" :class="isDark() ? 'bg-slate-800 text-slate-300' : 'bg-slate-100 text-slate-600'">
                {{ historyDetail.target }}
              </span>
              <span class="px-3 py-1.5 rounded-lg flex items-center gap-1.5" :class="isDark() ? 'bg-slate-800 text-slate-300' : 'bg-slate-100 text-slate-600'">
                <svg class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
                {{ formatDurationShort(historyDetail.duration_seconds) }}
              </span>
              <span class="px-3 py-1.5 rounded-lg flex items-center gap-1.5" :class="isDark() ? 'bg-slate-800 text-slate-300' : 'bg-slate-100 text-slate-600'">
                <svg class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>
                {{ formatHistoryDate(historyDetail.created_at) }}
              </span>
              <span class="px-3 py-1.5 rounded-lg font-bold"
                :class="{
                  'bg-emerald-500/20 text-emerald-300': historyDetail.status === 'success',
                  'bg-red-500/20 text-red-300': historyDetail.status === 'error',
                  'bg-amber-500/20 text-amber-300': historyDetail.status === 'cancelled',
                }">
                <span class="flex items-center gap-1">
                  <svg v-if="historyDetail.status === 'success'" class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
                  <svg v-else-if="historyDetail.status === 'cancelled'" class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="4.93" y1="4.93" x2="19.07" y2="19.07"/></svg>
                  <svg v-else class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
                  {{ historyDetail.status === 'success' ? 'Exitoso' : historyDetail.status === 'cancelled' ? 'Cancelado' : 'Error' }}
                </span>
              </span>
            </div>

            <!-- Error -->
            <div v-if="historyDetail.error_message" class="rounded-xl p-4 border" :class="isDark() ? 'bg-red-500/10 border-red-500/30' : 'bg-red-50 border-red-200'">
              <p class="text-sm" :class="isDark() ? 'text-red-300' : 'text-red-600'">{{ historyDetail.error_message }}</p>
            </div>

            <!-- Resultados detallados por host -->
            <div v-if="historyDetail.scan_results?.length">
              <h4 class="font-bold mb-3 flex items-center gap-2" :class="isDark() ? 'text-slate-200' : 'text-slate-800'">
                <Server class="w-5 h-5" :class="isDark() ? 'text-cyan-400' : 'text-cyan-600'" />
                Resultados por Host ({{ historyDetail.scan_results.length }})
              </h4>
              <div class="space-y-3 max-h-[60vh] overflow-y-auto pr-1">
                <div v-for="(r, idx) in historyDetail.scan_results" :key="idx"
                  class="border rounded-xl overflow-hidden"
                  :class="isDark() ? 'border-slate-800' : 'border-slate-200'">
                  
                  <!-- Host header -->
                  <div class="p-4 cursor-pointer" @click="toggleHostExpand(r.host || r.ip || ('host-' + idx))"
                    :class="isDark() ? 'bg-slate-900/80 hover:bg-slate-800/80' : 'bg-slate-50 hover:bg-slate-100'">
                    <div class="flex items-center justify-between">
                      <div class="flex items-center gap-3">
                        <div class="w-3 h-3 rounded-full" :style="{ backgroundColor: (r.status === 'up' || r._status === 'success') ? '#10b981' : '#64748b' }"></div>
                        <span class="font-mono font-bold" :class="isDark() ? 'text-white' : 'text-slate-800'">{{ r.host || r.ip }}</span>
                        <span v-if="r.hostname" class="text-xs" :class="isDark() ? 'text-cyan-400' : 'text-cyan-600'">{{ r.hostname }}</span>
                        <span v-if="r.vendor" class="text-xs px-2 py-0.5 rounded" :class="isDark() ? 'bg-slate-800 text-slate-400' : 'bg-slate-200 text-slate-500'">{{ r.vendor }}</span>
                      </div>
                      <div class="flex items-center gap-3 text-xs">
                        <span v-if="r.ports?.length" class="font-bold" :class="isDark() ? 'text-emerald-400' : 'text-emerald-600'">{{ r.ports.length }} puertos</span>
                        <span v-if="r.services?.length" class="font-bold" :class="isDark() ? 'text-purple-400' : 'text-purple-600'">{{ r.services.length }} servicios</span>
                        <span v-if="r.os?.name" class="text-xs flex items-center gap-1" :class="isDark() ? 'text-blue-400' : 'text-blue-600'"><OSIcon :name="r.os.name" :size="12" /> {{ r.os.name }}</span>
                        <ChevronDown class="w-4 h-4 transition-transform duration-200" :class="[expandedHosts.has(r.host || r.ip || ('host-' + idx)) ? 'rotate-180' : '', isDark() ? 'text-slate-500' : 'text-slate-400']" />
                      </div>
                    </div>
                  </div>

                  <!-- Host expanded details -->
                  <div v-if="expandedHosts.has(r.host || r.ip || ('host-' + idx))" class="border-t p-4 space-y-4"
                    :class="isDark() ? 'border-slate-800 bg-slate-950/50' : 'border-slate-200 bg-white'">
                    
                    <!-- Basic info -->
                    <div class="flex flex-wrap gap-2 text-xs">
                      <span v-if="r.mac" class="px-2 py-1 rounded-lg font-mono" :class="isDark() ? 'bg-slate-800 text-slate-300' : 'bg-slate-100 text-slate-600'">MAC: {{ r.mac }}</span>
                      <span v-if="r.latency_ms" class="px-2 py-1 rounded-lg" :class="isDark() ? 'bg-slate-800' : 'bg-slate-100'">
                        <span :class="getLatencyColor(r.latency_ms)">{{ r.latency_ms.toFixed(1) }}ms</span>
                      </span>
                      <span v-if="r.os?.accuracy" class="px-2 py-1 rounded-lg" :class="isDark() ? 'bg-slate-800 text-blue-300' : 'bg-blue-50 text-blue-600'">OS: {{ r.os.accuracy }}% confianza</span>
                    </div>

                    <!-- Ports table -->
                    <div v-if="r.ports?.length">
                      <p class="font-semibold text-xs mb-2" :class="isDark() ? 'text-emerald-400' : 'text-emerald-600'">Puertos ({{ r.ports.length }})</p>
                      <div class="rounded-lg overflow-hidden border" :class="isDark() ? 'border-slate-800' : 'border-slate-200'">
                        <table class="w-full text-xs">
                          <thead>
                            <tr :class="isDark() ? 'bg-slate-800/80' : 'bg-slate-100'">
                              <th class="text-left px-3 py-2" :class="isDark() ? 'text-slate-400' : 'text-slate-500'">Puerto</th>
                              <th class="text-left px-3 py-2" :class="isDark() ? 'text-slate-400' : 'text-slate-500'">Proto</th>
                              <th class="text-left px-3 py-2" :class="isDark() ? 'text-slate-400' : 'text-slate-500'">Servicio</th>
                            </tr>
                          </thead>
                          <tbody>
                            <tr v-for="(p, pi) in r.ports" :key="pi" :class="isDark() ? (pi % 2 === 0 ? 'bg-slate-900/50' : '') : (pi % 2 === 0 ? 'bg-white' : 'bg-slate-50')">
                              <td class="px-3 py-1.5 font-mono font-bold" :class="isDark() ? 'text-cyan-300' : 'text-cyan-700'">{{ p.port || p }}</td>
                              <td class="px-3 py-1.5 uppercase" :class="isDark() ? 'text-slate-500' : 'text-slate-400'">{{ p.protocol || 'tcp' }}</td>
                              <td class="px-3 py-1.5" :class="isDark() ? 'text-slate-300' : 'text-slate-600'">{{ p.service || '—' }}</td>
                            </tr>
                          </tbody>
                        </table>
                      </div>
                    </div>

                    <!-- Services table -->
                    <div v-if="r.services?.length">
                      <p class="font-semibold text-xs mb-2" :class="isDark() ? 'text-purple-400' : 'text-purple-600'">Servicios ({{ r.services.length }})</p>
                      <div class="rounded-lg overflow-hidden border" :class="isDark() ? 'border-slate-800' : 'border-slate-200'">
                        <table class="w-full text-xs">
                          <thead>
                            <tr :class="isDark() ? 'bg-slate-800/80' : 'bg-slate-100'">
                              <th class="text-left px-3 py-2" :class="isDark() ? 'text-slate-400' : 'text-slate-500'">Puerto</th>
                              <th class="text-left px-3 py-2" :class="isDark() ? 'text-slate-400' : 'text-slate-500'">Servicio</th>
                              <th class="text-left px-3 py-2" :class="isDark() ? 'text-slate-400' : 'text-slate-500'">Producto</th>
                              <th class="text-left px-3 py-2" :class="isDark() ? 'text-slate-400' : 'text-slate-500'">Versión</th>
                            </tr>
                          </thead>
                          <tbody>
                            <tr v-for="(svc, si) in r.services" :key="si" :class="isDark() ? (si % 2 === 0 ? 'bg-slate-900/50' : '') : (si % 2 === 0 ? 'bg-white' : 'bg-slate-50')">
                              <td class="px-3 py-1.5 font-mono font-bold" :class="isDark() ? 'text-cyan-300' : 'text-cyan-700'">{{ svc.port }}/{{ svc.protocol || 'tcp' }}</td>
                              <td class="px-3 py-1.5" :class="isDark() ? 'text-slate-300' : 'text-slate-600'">{{ svc.service || '—' }}</td>
                              <td class="px-3 py-1.5 font-medium" :class="isDark() ? 'text-slate-200' : 'text-slate-700'">{{ svc.product || '—' }}</td>
                              <td class="px-3 py-1.5">
                                <span v-if="svc.version" class="px-1.5 py-0.5 rounded text-xs font-mono" :class="isDark() ? 'bg-amber-500/15 text-amber-300' : 'bg-amber-50 text-amber-700'">v{{ svc.version }}</span>
                                <span v-else :class="isDark() ? 'text-slate-600' : 'text-slate-400'">—</span>
                              </td>
                            </tr>
                          </tbody>
                        </table>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </teleport>

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
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(12px); }
  to { opacity: 1; transform: translateY(0); }
}
.animate-fadeIn {
  animation: fadeIn 0.4s ease-out;
}
@keyframes slideDown {
  from { opacity: 0; max-height: 0; }
  to { opacity: 1; max-height: 2000px; }
}
.animate-slideDown {
  animation: slideDown 0.35s ease-out;
}
/* Tabla con scrollbar horizontal sutil */
.overflow-x-auto {
  scrollbar-width: thin;
  scrollbar-color: rgba(100,116,139,0.3) transparent;
}
.overflow-x-auto::-webkit-scrollbar {
  display: block;
  height: 4px;
}
.overflow-x-auto::-webkit-scrollbar-track {
  background: transparent;
}
.overflow-x-auto::-webkit-scrollbar-thumb {
  background-color: rgba(100,116,139,0.3);
  border-radius: 4px;
}
</style>
