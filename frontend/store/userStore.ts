import { type IdTokenClaims } from "@logto/react";
import { create } from "zustand";
import { persist } from "zustand/middleware";

interface UserStoreState {
  userInfo?: IdTokenClaims;
  setUserInfo: (userInfo: IdTokenClaims) => void;
  resetUserInfo: () => void;
}

const useUserStore = create<UserStoreState>()(
  persist(
    (set): UserStoreState => ({
      userInfo: undefined,
      setUserInfo: (userInfo) => set({ userInfo }),
      resetUserInfo: () => set({ userInfo: undefined }),
    }),
    {
      name: "user-storage",
    }
  )
);

export default useUserStore;
