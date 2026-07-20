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
      selectedBlendObjectKey: "",
      isEmptyProject: false,
      _hasHydrated: false,
      setUser: (user) =>
        set({ userId: user.id, username: user.name, email: user.email ?? "" }),
      setUsername: (username) => set({ username }),
      setBlendFolder: (path) => set({ blendFolderPath: path }),
      setSelectedBlendFile: (filename, fullPath) =>
        set({ selectedBlendFile: filename, fullBlendFilePath: fullPath }),
      setSelectedBlendObject: (filename, objectKey) =>
        set({
          selectedBlendFile: filename,
          selectedBlendObjectKey: objectKey,
          // Local-only path: meaningless for a cloud file, and leaving a stale
          // value here would send a bogus blend_file_path in the socket auth.
          fullBlendFilePath: "",
        }),
      setEmptyProject: (value) => set({ isEmptyProject: value }),
      clearBlendSelection: () =>
        set({
          blendFolderPath: "",
          selectedBlendFile: "",
          fullBlendFilePath: "",
          selectedBlendObjectKey: "",
        }),
      reset: () =>
        set({
          userId: "",
          username: "",
          email: "",
          blendFolderPath: "",
          selectedBlendFile: "",
          fullBlendFilePath: "",
          selectedBlendObjectKey: "",
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
