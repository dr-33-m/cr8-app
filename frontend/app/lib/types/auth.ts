export interface AuthUser {
  id: string;
  name: string;
  email: string | null;
  picture: string | null;
}

export type AuthContext =
  | { isAuthenticated: true; user: AuthUser; accessToken: string | null }
  | { isAuthenticated: false; user: null; accessToken: null };

export interface UserProfile {
  id: string;
  logto_id: string;
  email: string | null;
  name: string | null;
  is_approved: boolean;
  created_at: string;
}
