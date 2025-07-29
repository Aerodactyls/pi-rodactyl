import { UseSocketReturn } from "@/hooks/use-socket";
import { EDGE_PAIRS, getNodeConfigsWithPositions } from "@/lib/constants";
import { positionManager } from "@/lib/position-manager";
import {
  FlowState,
  getFlowState,
  getPhaseState,
  HammerType,
  PhaseType,
  StateType,
} from "@/lib/types";
import { createNodeStyle, getNextStates, getNodeConfig } from "@/lib/utils";
import {
  MarkerType,
  useEdgesState,
  useNodesState,
  type Edge,
  type Node,
  type NodeChange,
} from "@xyflow/react";
import { useCallback, useEffect, useMemo, useState } from "react";
import { toast } from "sonner";

export function useFlowLogic({
  currentPhase,
  currentState,
  mavlinkConnected,
  socketData,
}: {
  currentPhase: PhaseType | null;
  currentState: StateType | null;
  mavlinkConnected: boolean;
  socketData: UseSocketReturn;
}) {
  const { socket } = socketData;

  const [nodesDraggable, setNodesDraggable] = useState(false);
  const [selectedNext, setSelectedNext] = useState<FlowState | null>(null);
  const [isTransitioning, setIsTransitioning] = useState(false);
  const [connectionPort, setConnectionPort] = useState<string>("14550");
  const [isConnected, setIsConnected] = useState<boolean>(false);
  const [backendConnected, setBackendConnected] = useState<boolean>(false);
  const [selectedNodeForTransition, setSelectedNodeForTransition] =
    useState<FlowState | null>(null);
  const [showTransitionDialog, setShowTransitionDialog] =
    useState<boolean>(false);
  const [positionsLoaded, setPositionsLoaded] = useState(false);

  // Get flow state
  const webSocketFlowState = useMemo(() => {
    if (currentPhase !== null && currentState !== null) {
      return getFlowState(currentPhase, currentState);
    }
    return null;
  }, [currentPhase, currentState]);

  const displayState = webSocketFlowState ?? FlowState.ArmVehicle;

  // Initialize nodes and edges
  const initialNodes = useMemo((): Node[] => [], []);

  const initialEdges = useMemo(
    (): Edge[] =>
      EDGE_PAIRS.map(([source, target]) => ({
        id: `e${source}-${target}`,
        source,
        target,
        type: "smoothstep",
        markerEnd: { type: MarkerType.ArrowClosed },
      })),
    [],
  );

  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

  // Load positions on mount
  useEffect(() => {
    const loadPositions = async () => {
      const nodesWithPositions = await getNodeConfigsWithPositions();
      const formattedNodes = nodesWithPositions.map((config) => ({
        id: config.id,
        position: config.position,
        data: { label: config.label },
        style: createNodeStyle(config, false, false),
      }));
      setNodes(formattedNodes);
      setPositionsLoaded(true);
    };
    loadPositions();
  }, [setNodes]);

  // Custom onNodesChange that saves positions
  const handleNodesChange = useCallback(
    (changes: NodeChange[]) => {
      onNodesChange(changes);

      // Save positions for moved nodes
      changes.forEach((change) => {
        if (change.type === "position" && change.position && change.id) {
          positionManager.setPosition(change.id as FlowState, change.position);
        }
      });
    },
    [onNodesChange],
  );

  // Update connection status
  useEffect(() => {
    if (webSocketFlowState) {
      setBackendConnected(true);
    } else {
      setBackendConnected(false);
    }
    setIsConnected(mavlinkConnected);
  }, [webSocketFlowState, mavlinkConnected]);

  // Update node styles
  useEffect(() => {
    setNodes((nds) =>
      nds.map((node) => {
        const config = getNodeConfig(node.id as FlowState);
        if (!config) return node;

        return {
          ...node,
          style: createNodeStyle(
            config,
            node.id === displayState,
            isTransitioning,
          ),
        };
      }),
    );
  }, [displayState, isTransitioning, setNodes]);

  const toggleNodesDraggable = useCallback(() => {
    setNodesDraggable((prev) => !prev);
  }, []);

  const handleNextStateSelect = useCallback((value: string) => {
    setSelectedNext(value as FlowState);
  }, []);

  const sendTransitionCommand = useCallback(
    (targetState: FlowState) => {
      if (!socket) {
        console.error("Socket not connected");
        return false;
      }

      const targetPhaseState = getPhaseState(targetState);
      if (!targetPhaseState) {
        console.error(
          "Could not determine phase/state for target:",
          targetState,
        );
        return false;
      }

      setIsTransitioning(true);

      const command = {
        type: "change_command",
        data: {
          ...(targetPhaseState.phase !== null && {
            new_phase: targetPhaseState.phase,
          }),
          new_state: targetPhaseState.state,
        },
      };

      console.log("Sending transition command:", command);
      socket.emit("send_command", command);

      setTimeout(() => {
        setIsTransitioning(false);
        setSelectedNext(null);
      }, 1000);

      return true;
    },
    [socket],
  );

  const handleProceedToNext = useCallback(() => {
    const nextStates = getNextStates(displayState);
    const targetState = nextStates.length === 1 ? nextStates[0] : selectedNext;

    if (!targetState) {
      console.error("No target state selected");
      return;
    }

    sendTransitionCommand(targetState);
  }, [sendTransitionCommand, displayState, selectedNext]);

  const handleConnect = useCallback(() => {
    if (!socket) {
      console.error("Socket not connected");
      return;
    }

    const port = parseInt(connectionPort);
    if (isNaN(port) || port < 1 || port > 65535) {
      toast.error("Invalid port number");
      return;
    }

    const command = {
      type: "connect",
      data: { port },
    };

    console.log("Sending connect command:", command);
    socket.emit("send_command", command);
    toast.info("Connecting...");
  }, [socket, connectionPort]);

  const handleDisconnect = useCallback(() => {
    if (!socket) {
      console.error("Socket not connected");
      return;
    }

    const command = {
      type: "disconnect",
      data: {},
    };

    console.log("Sending disconnect command:", command);
    socket.emit("send_command", command);
    toast.info("Disconnecting...");
  }, [socket]);

  const handleNodeClick = useCallback(
    (event: any, node: any) => {
      const flowState = node.id as FlowState;

      if (flowState === displayState) {
        toast.info("Already in this state");
        return;
      }

      setSelectedNodeForTransition(flowState);
      setShowTransitionDialog(true);
    },
    [displayState],
  );

  const handleConfirmTransition = useCallback(() => {
    if (!selectedNodeForTransition) {
      console.error("No node selected");
      return;
    }

    setShowTransitionDialog(false);
    const success = sendTransitionCommand(selectedNodeForTransition);

    if (success) {
      setTimeout(() => {
        setSelectedNodeForTransition(null);
      }, 1000);
    } else {
      setSelectedNodeForTransition(null);
    }
  }, [selectedNodeForTransition, sendTransitionCommand]);

  const handleCancelTransition = useCallback(() => {
    setShowTransitionDialog(false);
    setSelectedNodeForTransition(null);
  }, []);

  const handleManualOverride = useCallback(
    (changes: {
      new_phase?: PhaseType;
      new_state?: StateType;
      new_hammer_type?: HammerType;
    }) => {
      if (!socket) {
        console.error("Socket not connected");
        return;
      }

      const command = {
        type: "change_command",
        data: changes,
      };

      console.log("Sending manual override command:", command);
      socket.emit("send_command", command);
      // toast.info("Applying manual override...");
    },
    [socket],
  );

  const savePositions = useCallback(async () => {
    await positionManager.save();
    toast.success("Positions saved!");
  }, []);

  return {
    // State
    nodesDraggable,
    selectedNext,
    isTransitioning,
    connectionPort,
    setConnectionPort,
    isConnected,
    backendConnected,
    selectedNodeForTransition,
    showTransitionDialog,
    setShowTransitionDialog,
    webSocketFlowState,
    displayState,

    // Nodes and edges
    nodes,
    edges,
    onNodesChange: handleNodesChange,
    onEdgesChange,

    // Event handlers
    toggleNodesDraggable,
    handleNextStateSelect,
    handleProceedToNext,
    handleConnect,
    handleDisconnect,
    handleNodeClick,
    handleConfirmTransition,
    handleCancelTransition,
    handleManualOverride,

    // Position management
    savePositions,
  };
}
