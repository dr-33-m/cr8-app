export interface Animation {
  id: string;
  name: string;
  thumbnail: string;
  template_type: "camera" | "light" | "product_animation";
  templateData: any;
  is_public: boolean;
  created_at: string;
  updated_at: string;
  creator_id: string;
}

export interface AnimationCategory {
  name: string;
  animations: Animation[];
}

export interface AnimationResponse {
  success: boolean;
  message: string;
  data?: any;
}
