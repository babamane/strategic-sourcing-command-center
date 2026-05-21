import { useState } from "react";
import { postTrigger } from "../api/triggerClient.js";
import { postChurnMail } from "../api/mailClient.js";
import { useAppStore } from "../store/useAppStore.js";

export function useTrigger() {
  const [preview, setPreview] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchPreview = async (type, req) => {
    setLoading(true);
    setError(null);
    try {
      const data = type === "churn_mail"
        ? await postChurnMail({ ...req, confirmed: false })
        : await postTrigger(type, { ...req, confirmed: false });
      setPreview(data);
    } catch (err) {
      setError(err.message ?? "Preview failed.");
    } finally {
      setLoading(false);
    }
  };

  const dispatch = async (type, req) => {
    setLoading(true);
    setError(null);
    try {
      const data = type === "churn_mail"
        ? await postChurnMail({ ...req, confirmed: true })
        : await postTrigger(type, { ...req, confirmed: true });
      setResult(data);
      useAppStore.getState().addDispatchedRec(data);
    } catch (err) {
      setError(err.message ?? "Dispatch failed.");
    } finally {
      setLoading(false);
    }
  };

  const reset = () => {
    setPreview(null);
    setResult(null);
    setError(null);
  };

  return { preview, result, loading, error, fetchPreview, dispatch, reset };
}
