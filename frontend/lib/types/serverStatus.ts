export type ServerStatus = "healthy" | "unhealthy" | "maintenance" | "offline";

export interface ServerMessage {
  buttonText: string;
  message: string;
}
