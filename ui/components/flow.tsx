import {
  Background,
  BackgroundVariant,
  ControlButton,
  Controls,
  MiniMap,
  ReactFlow,
} from "@xyflow/react";
import React from "react";
import "@xyflow/react/dist/style.css";
import { ControlPanel } from "@/components/control-panel";
import { TransitionDialog } from "@/components/transition-dialog";
import {
  ResizableHandle,
  ResizablePanel,
  ResizablePanelGroup,
} from "@/components/ui/resizable";
import { useFlowLogic } from "@/hooks/use-flow-logic";
import { useSocket } from "@/hooks/use-socket";
import { HammerType, PhaseType, StateType } from "@/lib/types";
import { Pin, PinOff, Save } from "lucide-react";

export default function Flow({
  currentPhase,
  currentState,
  currentHammerType,
  isConnected: mavlinkConnected,
}: {
  currentPhase: PhaseType | null;
  currentState: StateType | null;
  currentHammerType: HammerType | null;
  isConnected: boolean;
}) {
  const socketData = useSocket();

  const {
    nodes,
    edges,
    onNodesChange,
    onEdgesChange,
    nodesDraggable,
    toggleNodesDraggable,
    displayState,
    webSocketFlowState,
    connectionPort,
    isConnected,
    selectedNodeForTransition,
    showTransitionDialog,
    handleConnect,
    handleDisconnect,
    handleNodeClick,
    handleConfirmTransition,
    handleCancelTransition,
    handleManualOverride,
    setConnectionPort,
    savePositions,
  } = useFlowLogic({
    currentPhase,
    currentState,
    mavlinkConnected,
    socketData,
  });

  const { lastHeartbeatTime, timeSinceHeartbeat, heartbeatPulse } = socketData;

  return (
    <div className="fixed inset-0 h-screen w-screen">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeClick={handleNodeClick}
        nodesDraggable={nodesDraggable}
        nodesConnectable={false}
        elementsSelectable={true}
        proOptions={{ hideAttribution: true }}
      >
        <Controls position="top-left" showInteractive={false}>
          <ControlButton
            onClick={toggleNodesDraggable}
            title={nodesDraggable ? "Lock nodes" : "Unlock nodes"}
          >
            {nodesDraggable ? <Pin /> : <PinOff />}
          </ControlButton>
          <ControlButton onClick={savePositions} title="Save positions">
            <Save />
          </ControlButton>
        </Controls>
        <MiniMap zoomable pannable />
        <Background variant={BackgroundVariant.Dots} gap={12} size={1} />
      </ReactFlow>

      <ResizablePanelGroup
        direction="horizontal"
        className="pointer-events-none fixed top-0 right-0 z-10 h-screen w-screen"
      >
        <ResizablePanel />
        <ResizableHandle className="invisible mt-4 h-3/4" />
        <ResizablePanel
          defaultSize={20}
          minSize={15}
          maxSize={50}
          className="pointer-events-auto mt-4 mr-4 h-3/4 w-64"
        >
          <ControlPanel
            displayState={displayState}
            webSocketFlowState={webSocketFlowState ?? null}
            lastHeartbeatTime={lastHeartbeatTime}
            timeSinceHeartbeat={timeSinceHeartbeat}
            heartbeatPulse={heartbeatPulse}
            isConnected={isConnected}
            connectionPort={connectionPort}
            setConnectionPort={setConnectionPort}
            handleConnect={handleConnect}
            handleDisconnect={handleDisconnect}
            currentPhase={currentPhase}
            currentState={currentState}
            currentHammerType={currentHammerType}
            handleManualOverride={handleManualOverride}
          />
        </ResizablePanel>
      </ResizablePanelGroup>

      <TransitionDialog
        showTransitionDialog={showTransitionDialog}
        selectedNodeForTransition={selectedNodeForTransition}
        handleConfirmTransition={handleConfirmTransition}
        handleCancelTransition={handleCancelTransition}
        setShowTransitionDialog={(show) => {
          if (!show) handleCancelTransition();
        }}
      />
    </div>
  );
}
