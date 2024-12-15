export type SceneConfiguration = {
  camera?: {
    camera_name: string;
  };
  lights?: Array<{
    light_name: string;
    color: string;
    strength: number;
  }>;
  materials?: Array<{
    material_name: string;
    color: string;
    roughness?: number;
    metallic?: number;
  }>;
  objects?: Array<{
    object_name: string;
    location?: [number, number, number];
    rotation?: [number, number, number];
    scale?: [number, number, number];
  }>;
};

export type OnRemoveAssetFunction = (
  assetType: string, // the type of asset (camera, light, etc.)
  assetId?: string // optional specific identifier
) => void;
