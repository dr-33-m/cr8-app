import { useState, useEffect, useCallback, useMemo } from "react";
import { ServerStatus } from "@/lib/types/serverStatus";
import { checkServerHealth, getServerMessage } from "@/lib/utils/healthCheck";

export const useServerHealth = () => {
  const [serverStatus, setServerStatus] = useState<ServerStatus>("healthy");
  const [isCheckingHealth, setIsCheckingHealth] = useState(true);

  const checkHealth = useCallback(async () => {
    try {
      const status = await checkServerHealth();
      setServerStatus(status);
    } finally {
      setIsCheckingHealth(false);
    }
  }, []);

  useEffect(() => {
    checkHealth();
    const interval = setInterval(checkHealth, 30000);
    return () => clearInterval(interval);
  }, [checkHealth]);

  const serverMessage = useMemo(
    () => getServerMessage(serverStatus),
    [serverStatus]
  );

  return {
    serverStatus,
    isCheckingHealth,
    serverMessage,
    checkHealth,
  };
};
