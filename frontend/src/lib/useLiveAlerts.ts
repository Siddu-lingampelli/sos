/** Backwards-compatible re-export: the socket is a per-tab singleton now. */
export {
  useLiveAlerts,
  reconnectLiveSocket,
  type LiveIncident,
  type LiveActivity,
  type LiveSystem,
  type WsState,
} from "./liveSocket";
