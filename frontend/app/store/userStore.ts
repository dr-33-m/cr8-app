import { create } from "zustand";
import { persist } from "zustand/middleware";
import { UserStoreState } from "@/lib/types/stores";

const useUserStore = create<UserStoreState>()(
  persist(
    (set) => ({
      userId: "",
      username: "",
      email: "",
      blendFolderPath: "",
      selectedBlendFile: "",
      fullBlendFilePath: "",
      isEmptyProject: false,
      _hasHydrated: false,
      setUser: (user) =>
        set({ userId: user.id, username: user.name, email: user.email ?? "" }),
      setUsername: (username) => set({ username }),
      setBlendFolder: (path) => set({ blendFolderPath: path }),
      setSelectedBlendFile: (filename, fullPath) =>
        set({ selectedBlendFile: filename, fullBlendFilePath: fullPath }),
      setEmptyProject: (value) => set({ isEmptyProject: value }),
      clearBlendSelection: () =>
        set({
          blendFolderPath: "",
          selectedBlendFile: "",
          fullBlendFilePath: "",
        }),
      reset: () =>
        set({
          userId: "",
          username: "",
          email: "",
          blendFolderPath: "",
          selectedBlendFile: "",
          fullBlendFilePath: "",
          isEmptyProject: false,
        }),
    }),
    {
      name: "user-storage",
      onRehydrateStorage: () => (state) => {
        if (state) {
          state._hasHydrated = true;
        }
      },
    }
  )
);

export default useUserStore;
