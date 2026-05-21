import { create } from "zustand";

export const useAppStore = create(set => ({
  vendor: "All",
  department: "All",
  selectedYear: "All",
  selectedSku: "All",
  selectedSeatType: "All",
  activeView: "overview",
  chatOpen: false,
  pendingConfirm: null,
  dispatchedRecs: [],

  enterDashboard: false,

  setVendor: vendor => set({ vendor }),
  setDepartment: department => set({ department }),
  setYear: selectedYear => set({ selectedYear }),
  setSku: selectedSku => set({ selectedSku }),
  setSeatType: selectedSeatType => set({ selectedSeatType }),
  setView: activeView => set({ activeView }),
  toggleChat: () => set(state => ({ chatOpen: !state.chatOpen })),
  setChatOpen: chatOpen => set({ chatOpen }),
  setPendingConfirm: pendingConfirm => set({ pendingConfirm }),
  clearConfirm: () => set({ pendingConfirm: null }),
  addDispatchedRec: rec => set(state => ({ dispatchedRecs: [rec, ...state.dispatchedRecs] })),
  setEnterDashboard: enterDashboard => set({ enterDashboard }),
}));
