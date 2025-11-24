export const sceneContextKeys = {
  all: ["scene-context"] as const,
  objects: () => [...sceneContextKeys.all, "objects"] as const,
};
