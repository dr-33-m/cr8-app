import { create } from "zustand";
import { persist } from "zustand/middleware";
import { UserStoreState } from "@/lib/types/stores";

const useUserStore = create<UserStoreState>()(
  persist(
    (set) => ({
      username: "",
      blendFolderPath: "",
      selectedBlendFile: "",
      fullBlendFilePath: "",
      setUsername: (username) => set({ username }),
      setBlendFolder: (path) => set({ blendFolderPath: path }),
      setSelectedBlendFile: (filename, fullPath) =>
        set({ selectedBlendFile: filename, fullBlendFilePath: fullPath }),
      clearBlendSelection: () =>
        set({
          blendFolderPath: "",
          selectedBlendFile: "",
          fullBlendFilePath: "",
        }),
      reset: () =>
        set({
          username: "",
          blendFolderPath: "",
          selectedBlendFile: "",
          fullBlendFilePath: "",
        }),
    }),
    {
      name: "user-storage",
    }
  )
);

export default useUserStore;
