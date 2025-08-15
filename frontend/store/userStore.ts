import { create } from "zustand";
import { persist } from "zustand/middleware";

interface UserStoreState {
  username: string;
  blendFolderPath: string;
  selectedBlendFile: string;
  fullBlendFilePath: string;
  setUsername: (username: string) => void;
  setBlendFolder: (path: string) => void;
  setSelectedBlendFile: (filename: string, fullPath: string) => void;
  clearBlendSelection: () => void;
  reset: () => void;
}

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
