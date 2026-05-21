import { api } from "./client.js";

export async function postChurnMail(req) {
  const res = await api.post("/mail/churn-notification", req);
  return res.data;
}
