type SupportedControl =
  | "activate"
  | "settings"
  | "color"
  | "strength"
  | "temperature"
  | "location"
  | "rotation"
  | "scale";

interface BaseControl {
  id: string; // original name with prefix
  name: string; // original name with prefix (for backward compatibility)
  displayName: string; // name without prefix for UI display
  supported_controls: SupportedControl[];
}

interface Camera extends BaseControl {
  type: string;
}

interface Light extends BaseControl {
  type: string;
  light_type: string;
}

interface Material extends BaseControl {
  type: string;
}

interface ControllableObject extends BaseControl {
  type: string;
  object_type: string;
}

export interface TemplateControls {
  cameras: Camera[];
  lights: Light[];
  materials: Material[];
  objects: ControllableObject[];
}
