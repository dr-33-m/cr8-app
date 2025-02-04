type SupportedControl =
  | "activate"
  | "settings"
  | "color"
  | "strength"
  | "temperature"
  | "location"
  | "rotation"
  | "scale";

interface Camera {
  name: string;
  supported_controls: SupportedControl[];
}

interface Light {
  name: string;
  type: "AREA";
  supported_controls: SupportedControl[];
}

interface ControllableObject {
  name: string;
  type: "LIGHT" | "CAMERA";
  supported_controls: SupportedControl[];
}

export interface TemplateControls {
  cameras: Camera[];
  lights: Light[];
  materials: any[]; // Expanded this as needed
  objects: ControllableObject[];
}
