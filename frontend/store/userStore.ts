import { type IdTokenClaims } from "@logto/react";
import { create } from "zustand";
import { persist } from "zustand/middleware";

interface UserStoreState {
  userInfo?: IdTokenClaims;
  setUserInfo: (userInfo: IdTokenClaims) => void;
  resetUserInfo: () => void; // Add reset functionality
}

const useUserStore = create<UserStoreState>()(
  persist(
    (set) => ({
      userInfo: undefined,
      setUserInfo: (userInfo) => set({ userInfo }),
      resetUserInfo: () => set({ userInfo: undefined }), // Reset userInfo to initial state
    }),
    {
      name: "user-storage",
    }
  )
);

export default useUserStore;
