import { useEffect, useState } from "react";
import io, { Socket } from "socket.io-client";
import { toast } from "sonner";

export interface UseSocketReturn {
  socket: Socket | null;
  lastHeartbeatTime: number | null;
  timeSinceHeartbeat: string;
  heartbeatPulse: number;
}

export function useSocket(): UseSocketReturn {
  const [socket, setSocket] = useState<Socket | null>(null);
  const [lastHeartbeatTime, setLastHeartbeatTime] = useState<number | null>(
    null,
  );
  const [timeSinceHeartbeat, setTimeSinceHeartbeat] = useState<string>("--");
  const [heartbeatPulse, setHeartbeatPulse] = useState<number>(0);

  useEffect(() => {
    const newSocket = io("http://localhost:5328");
    setSocket(newSocket);

    newSocket.on("command_response", (response: any) => {
      console.log("Command response:", response);
      if (response.status === "error") {
        console.error("Command failed:", response.message);
        toast.error(`Command failed: ${response.message}`);
      } else {
        toast.success(response.message || "Command sent successfully");
      }
    });

    newSocket.on("machine_error", (error: any) => {
      console.error("Machine error:", error);
      toast.error(`Machine Error: ${error.message}`);
    });

    // track heartbeats
    newSocket.on("data_update", (data: any) => {
      if (data.type === "heartbeat") {
        setLastHeartbeatTime(Date.now());
        setHeartbeatPulse(prev => prev + 1);
      }
    });

    return () => {
      newSocket.disconnect();
    };
  }, []);

  // time since heartbeat
  useEffect(() => {
    const interval = setInterval(() => {
      if (lastHeartbeatTime) {
        const timeDiff = (Date.now() - lastHeartbeatTime) / 1000;
        if (timeDiff < 60) {
          setTimeSinceHeartbeat(`${timeDiff.toFixed(1)}s`);
        } else {
          setTimeSinceHeartbeat(
            `${Math.floor(timeDiff / 60)}m ${(timeDiff % 60).toFixed(0)}s`,
          );
        }
      } else {
        setTimeSinceHeartbeat("--");
      }
    }, 100);

    return () => clearInterval(interval);
  }, [lastHeartbeatTime]);

  return {
    socket,
    lastHeartbeatTime,
    timeSinceHeartbeat,
    heartbeatPulse,
  };
}
