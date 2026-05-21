import { api } from "./client.js";

const TYPE_TO_PATH = {
  ghost_ticket: "/triggers/ghost-ticket",
  reclamation: "/triggers/reclamation",
  reclamation_review: "/triggers/reclamation-review",
  rightsizing: "/triggers/rightsizing",
  renewal_alert: "/triggers/renewal-alert",
};

export async function postTrigger(type, req) {
  const path = TYPE_TO_PATH[type];
  if (!path) throw new Error(`Unknown trigger type: ${type}`);
  const res = await api.post(path, req);
  return res.data;
}
