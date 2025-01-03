import { LucideIcon } from "lucide-react";

export interface ProjectType {
  icon: LucideIcon;
  subtypes: string[];
}

export interface ProjectTemplate {
  id: string;
  name: string;
  thumbnail: string;
}

export interface ProjectFormData {
  name: string;
  description: string;
  type: string;
  subtype: string;
  template: string;
  moodboard: string;
}
