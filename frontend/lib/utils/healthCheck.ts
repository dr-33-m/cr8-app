import { ServerStatus, ServerMessage } from "../types/serverStatus";

const c8_engine_server = import.meta.env.VITE_CR8_ENGINE_SERVER;

export const getServerMessage = (serverStatus: ServerStatus): ServerMessage => {
  const now = new Date();
  // Convert to Johannesburg time
  const joburg = new Intl.DateTimeFormat("en-US", {
    timeZone: "Africa/Johannesburg",
    hour: "numeric",
    hour12: false,
  }).format(now);
  const hour = parseInt(joburg);

  if (hour >= 0 && hour < 6) {
    return {
      buttonText: "Offline",
      message: "Cr8 Engine will be online at 6am Johannesburg time",
    };
  }

  switch (serverStatus) {
    case "healthy":
      return {
        buttonText: "Create Project",
        message: "",
      };
    case "maintenance":
      return {
        buttonText: "Under Maintenance",
        message: "Cr8 Engine is currently under maintenance",
      };
    case "offline":
      return {
        buttonText: "Offline",
        message: "Cr8 Engine will be online at 6am Johannesburg time",
      };
    default:
      return {
        buttonText: "Starting Up",
        message: "Hold on while we wake up Cr8 Engine...",
      };
  }
};

export const checkServerHealth = async (): Promise<ServerStatus> => {
  const now = new Date();
  const joburg = new Intl.DateTimeFormat("en-US", {
    timeZone: "Africa/Johannesburg",
    hour: "numeric",
    hour12: false,
  }).format(now);
  const hour = parseInt(joburg);

  // If it's between 00:00 and 06:00 Johannesburg time
  if (hour >= 0 && hour < 6) {
    return "offline";
  }

  try {
    const response = await fetch(`${c8_engine_server}/health`);
    if (response.ok) {
      return "healthy";
    }

    const errorData = await response.json();
    // Check if it's an EAGAIN error
    if (errorData.detail && errorData.detail.includes("EAGAIN")) {
      return "unhealthy";
    }
    return "maintenance";
  } catch (error) {
    console.error("Server health check failed:", error);
    return "maintenance";
  }
};
