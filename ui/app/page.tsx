"use client";

import Flow from "@/components/flow";
import type {
  HammerType,
  MessageData,
  PhaseType,
  StateMachineMessage,
  StateType,
} from "@/lib/types";
import { useEffect, useState } from "react";
import io from "socket.io-client";

export default function Home() {
  const [dataList, setDataList] = useState<MessageData[]>([]);
  const [currentPhase, setCurrentPhase] = useState<PhaseType | null>(null);
  const [currentState, setCurrentState] = useState<StateType | null>(null);
  const [currentHammerType, setCurrentHammerType] = useState<HammerType | null>(
    null,
  );
  const [isConnected, setIsConnected] = useState<boolean>(false);

  useEffect(() => {
    const socket = io("http://localhost:5328");

    socket.on("data_update", (data: MessageData) => {
      console.log("Received data_update:", data);
      setDataList((prev) => [...prev, data]);
      if (data.type === "state_machine_data") {
        const smData = data as StateMachineMessage;
        setCurrentPhase(smData.data.phase);
        setCurrentState(smData.data.state);
        setCurrentHammerType(smData.data.known_hammer_type);
        setIsConnected(smData.data.connected);
      }
    });

    return () => {
      socket.disconnect();
    };
  }, []);

  return (
    <main>
      <Flow
        currentPhase={currentPhase}
        currentState={currentState}
        currentHammerType={currentHammerType}
        isConnected={isConnected}
      />
    </main>
  );
}
