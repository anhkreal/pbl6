import { create } from 'zustand';

interface UIState {
  pinAction?: { label: string; onConfirm: () => void };
  showPinModal: boolean;
  openPin: (label: string, onConfirm: () => void) => void;
  closePin: () => void;
}

export const useUIStore = create<UIState>(set => ({
  pinAction: undefined,
  showPinModal: false,
  openPin: (label, onConfirm) => set({ pinAction: { label, onConfirm }, showPinModal: true }),
  closePin: () => set({ showPinModal: false, pinAction: undefined })
}));