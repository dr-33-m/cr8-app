import { useCallback } from "react";
import { useSceneConfigStore } from "@/store/sceneConfiguratorStore";
import { useCameraControl } from "./useCameraControl";
import { useLightControl } from "./useLightControl";
import { useMaterialControl } from "./useMaterialControl";
import { useObjectControl } from "./useObjectControl";

/**
 * Hook that combines scene configuration store with direct control hooks
 * for real-time updates to scene elements
 */
export function useSceneControls() {
  // Get store methods
  const {
    sceneConfiguration,
    updateSceneConfiguration,
    removeSceneConfiguration,
    setSceneConfiguration,
    resetSceneConfiguration,
  } = useSceneConfigStore();

  // Get direct control hooks
  const { updateCamera } = useCameraControl();
  const { updateLight } = useLightControl();
  const { updateMaterial } = useMaterialControl();
  const { updateObject } = useObjectControl();

  // Camera control
  const handleUpdateCamera = useCallback(
    (cameraName: string) => {
      // Update store
      updateSceneConfiguration("camera", { camera_name: cameraName });

      // Send direct update via WebSocket
      updateCamera(cameraName);
    },
    [updateSceneConfiguration, updateCamera]
  );

  // Light control
  const handleUpdateLight = useCallback(
    (lightName: string, color?: string | number[], strength?: number) => {
      // Update store
      const currentLights = sceneConfiguration.lights || [];
      const existingLightIndex = currentLights.findIndex(
        (l) => l.light_name === lightName
      );

      let updatedLights;
      if (existingLightIndex >= 0) {
        // Update existing light
        updatedLights = [...currentLights];
        const updatedLight = { ...updatedLights[existingLightIndex] };

        if (color !== undefined) {
          updatedLight.color =
            typeof color === "string" ? color : `rgb(${color.join(",")})`;
        }

        if (strength !== undefined) {
          updatedLight.strength = strength;
        }

        updatedLights[existingLightIndex] = updatedLight;
      } else {
        // Add new light
        updatedLights = [
          ...currentLights,
          {
            light_name: lightName,
            color:
              typeof color === "string"
                ? color
                : color
                  ? `rgb(${color.join(",")})`
                  : "#FFFFFF",
            strength: strength || 1.0,
          },
        ];
      }

      updateSceneConfiguration("lights", updatedLights);

      // Send direct update via WebSocket
      updateLight(lightName, color, strength);
    },
    [sceneConfiguration, updateSceneConfiguration, updateLight]
  );

  // Material control
  const handleUpdateMaterial = useCallback(
    (
      materialName: string,
      color?: string | number[],
      roughness?: number,
      metallic?: number
    ) => {
      // Update store
      const currentMaterials = sceneConfiguration.materials || [];
      const existingMaterialIndex = currentMaterials.findIndex(
        (m) => m.material_name === materialName
      );

      let updatedMaterials;
      if (existingMaterialIndex >= 0) {
        // Update existing material
        updatedMaterials = [...currentMaterials];
        const updatedMaterial = { ...updatedMaterials[existingMaterialIndex] };

        if (color !== undefined) {
          updatedMaterial.color =
            typeof color === "string" ? color : `rgb(${color.join(",")})`;
        }

        if (roughness !== undefined) {
          updatedMaterial.roughness = roughness;
        }

        if (metallic !== undefined) {
          updatedMaterial.metallic = metallic;
        }

        updatedMaterials[existingMaterialIndex] = updatedMaterial;
      } else {
        // Add new material
        updatedMaterials = [
          ...currentMaterials,
          {
            material_name: materialName,
            color:
              typeof color === "string"
                ? color
                : color
                  ? `rgb(${color.join(",")})`
                  : "#FFFFFF",
            roughness,
            metallic,
          },
        ];
      }

      updateSceneConfiguration("materials", updatedMaterials);

      // Send direct update via WebSocket
      updateMaterial(materialName, color, roughness, metallic);
    },
    [sceneConfiguration, updateSceneConfiguration, updateMaterial]
  );

  // Object control
  const handleUpdateObject = useCallback(
    (
      objectName: string,
      location?: number[],
      rotation?: number[],
      scale?: number[]
    ) => {
      // Update store
      const currentObjects = sceneConfiguration.objects || [];
      const existingObjectIndex = currentObjects.findIndex(
        (o) => o.object_name === objectName
      );

      let updatedObjects;
      if (existingObjectIndex >= 0) {
        // Update existing object
        updatedObjects = [...currentObjects];
        const updatedObject = { ...updatedObjects[existingObjectIndex] };

        if (location !== undefined) {
          updatedObject.location = location as [number, number, number];
        }

        if (rotation !== undefined) {
          updatedObject.rotation = rotation as [number, number, number];
        }

        if (scale !== undefined) {
          updatedObject.scale = scale as [number, number, number];
        }

        updatedObjects[existingObjectIndex] = updatedObject;
      } else {
        // Add new object
        updatedObjects = [
          ...currentObjects,
          {
            object_name: objectName,
            location: location as [number, number, number],
            rotation: rotation as [number, number, number],
            scale: scale as [number, number, number],
          },
        ];
      }

      updateSceneConfiguration("objects", updatedObjects);

      // Send direct update via WebSocket
      updateObject(objectName, location, rotation, scale);
    },
    [sceneConfiguration, updateSceneConfiguration, updateObject]
  );

  return {
    // Original store methods
    sceneConfiguration,
    updateSceneConfiguration,
    removeSceneConfiguration,
    setSceneConfiguration,
    resetSceneConfiguration,

    // Direct control methods
    updateCamera: handleUpdateCamera,
    updateLight: handleUpdateLight,
    updateMaterial: handleUpdateMaterial,
    updateObject: handleUpdateObject,
  };
}
