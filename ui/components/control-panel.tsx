import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";
import { FlowState, HammerType, PhaseType, StateType } from "@/lib/types";
import { getNodeConfig } from "@/lib/utils";
import { motion } from "motion/react";
import React, { useState } from "react";

export function ControlPanel({
  displayState,
  webSocketFlowState,
  lastHeartbeatTime,
  timeSinceHeartbeat,
  heartbeatPulse,
  isConnected,
  connectionPort,
  setConnectionPort,
  handleConnect,
  handleDisconnect,
  currentPhase,
  currentState,
  currentHammerType,
  handleManualOverride,
}: {
  displayState: FlowState;
  webSocketFlowState: FlowState | null;
  lastHeartbeatTime: number | null;
  timeSinceHeartbeat: string;
  heartbeatPulse: number;
  isConnected: boolean;
  connectionPort: string;
  setConnectionPort: (port: string) => void;
  handleConnect: () => void;
  handleDisconnect: () => void;
  currentPhase: PhaseType | null;
  currentState: StateType | null;
  currentHammerType: HammerType | null;
  handlePhaseChange?: (phase: PhaseType) => void;
  handleStateChange?: (state: StateType) => void;
  handleManualOverride?: (changes: {
    new_phase?: PhaseType;
    new_state?: StateType;
    new_hammer_type?: HammerType;
  }) => void;
}) {
  const currentNodeConfig = getNodeConfig(displayState);
  const [selectedHammerType, setSelectedHammerType] =
    useState<HammerType | null>(null);
  const [selectedPhase, setSelectedPhase] = useState<PhaseType | null>(null);
  const [selectedState, setSelectedState] = useState<StateType | null>(null);
  const [rotationCount, setRotationCount] = useState(0);

  const hasOverrideValues =
    selectedPhase !== null ||
    selectedState !== null ||
    selectedHammerType !== null;

  const isOverrideDisabled = !hasOverrideValues;

  const handleManualOverrideClick = () => {
    if (!handleManualOverride) return;

    const changes: {
      new_phase?: PhaseType;
      new_state?: StateType;
      new_hammer_type?: HammerType;
    } = {};

    if (selectedPhase !== null) {
      changes.new_phase = selectedPhase;
    }
    if (selectedState !== null) {
      changes.new_state = selectedState;
    }
    if (selectedHammerType !== null) {
      changes.new_hammer_type = selectedHammerType;
    }

    handleManualOverride(changes);
  };

  const handleReset = () => {
    setSelectedPhase(null);
    setSelectedState(null);
    setSelectedHammerType(null);
    setRotationCount((prev) => prev + 1);
  };

  return (
    <Card className="flex h-full w-full flex-col">
      <CardHeader>
        <CardTitle>Drone Control</CardTitle>
        <CardDescription>
          {currentNodeConfig?.label ?? "Unknown state"}
        </CardDescription>
        <div className="text-muted-foreground text-xs">
          Click on any node to transition to that state
        </div>
      </CardHeader>

      <CardContent className="flex flex-col gap-3">
        <Separator />

        <div className="space-y-1">
          <div className="flex items-center justify-between">
            <span className="text-muted-foreground text-sm">Phase</span>
            <div className="flex items-center gap-2">
              <span className="text-xs font-medium">
                {currentPhase !== null ? PhaseType[currentPhase] : "Unknown"}
              </span>
              <Badge
                variant="outline"
                className="w-6 text-center font-mono text-xs"
              >
                {currentPhase ?? "?"}
              </Badge>
            </div>
          </div>

          <div className="flex items-center justify-between">
            <span className="text-muted-foreground text-sm">State</span>
            <div className="flex items-center gap-2">
              <span className="text-xs font-medium">
                {currentState !== null ? StateType[currentState] : "Unknown"}
              </span>
              <Badge
                variant="outline"
                className="w-6 text-center font-mono text-xs"
              >
                {currentState ?? "?"}
              </Badge>
            </div>
          </div>

          <div className="flex items-center justify-between">
            <span className="text-muted-foreground text-sm">Hammer Type</span>
            <div className="flex items-center gap-2">
              <span className="text-xs font-medium">
                {currentHammerType !== null
                  ? HammerType[currentHammerType]
                  : "Unknown"}
              </span>
              <Badge
                variant="outline"
                className="w-6 text-center font-mono text-xs"
              >
                {currentHammerType ?? "?"}
              </Badge>
            </div>
          </div>
        </div>

        <Separator />

        <div className="flex items-center justify-between text-sm">
          <div className="flex items-center">
            <motion.div
              className={`mr-2 h-2 w-2 rounded-full ${
                !lastHeartbeatTime
                  ? "bg-muted"
                  : Date.now() - lastHeartbeatTime < 2000
                    ? "bg-green-500"
                    : Date.now() - lastHeartbeatTime < 5000
                      ? "bg-yellow-500"
                      : "bg-red-500"
              }`}
              animate={{
                scale: [1, 1.3, 1],
                opacity: [1, 0.7, 1],
              }}
              transition={{
                duration: 0.3,
                ease: "easeOut",
              }}
              key={heartbeatPulse} // This triggers the animation on each heartbeat
            />
            <span className="text-muted-foreground">Time Since Heartbeat:</span>
          </div>
          <div className="flex items-center">
            <span
              className={`font-mono ${
                !lastHeartbeatTime
                  ? "text-muted-foreground"
                  : Date.now() - lastHeartbeatTime < 2000
                    ? "text-green-600"
                    : Date.now() - lastHeartbeatTime < 5000
                      ? "text-yellow-600"
                      : "text-red-600"
              }`}
            >
              {timeSinceHeartbeat}
            </span>
            {!lastHeartbeatTime && (
              <span className="text-muted-foreground ml-1 text-xs">
                (no heartbeat yet)
              </span>
            )}
          </div>
        </div>

        {webSocketFlowState && (
          <Badge variant="default" className="w-fit">
            ✓ Connected
          </Badge>
        )}

        {!webSocketFlowState && (
          <Badge variant="outline" className="w-fit">
            ⚠ No data
          </Badge>
        )}

        <Separator />

        <div>
          <h4 className="mb-2 text-sm font-medium">MAVLink Connection</h4>
          <div className="mb-2">
            <Label htmlFor="port-input" className="mb-1 text-xs">
              Port:
            </Label>
            <Input
              id="port-input"
              type="number"
              value={connectionPort}
              onChange={(e) => setConnectionPort(e.target.value)}
              disabled={isConnected}
              placeholder="14552"
              min="1"
              max="65535"
              className="text-sm"
            />
          </div>
          <div className="flex gap-2">
            <Button
              onClick={handleConnect}
              disabled={isConnected}
              className="flex-1"
              size="sm"
              variant="default"
            >
              Connect
            </Button>
            <Button
              onClick={handleDisconnect}
              disabled={!isConnected}
              className="flex-1"
              size="sm"
              variant="destructive"
            >
              Disconnect
            </Button>
          </div>
        </div>

        <Separator />

        <div>
          <div className="mb-2 flex items-center justify-between">
            <h4 className="text-sm font-medium">Manual Override</h4>
            <Button
              variant="ghost"
              size="sm"
              onClick={handleReset}
              className="h-6 w-6 p-0"
            >
              <motion.svg
                className="h-3 w-3"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
                animate={{ rotate: -rotationCount * 360 }}
                transition={{ duration: 0.4, ease: "easeOut" }}
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                />
              </motion.svg>
            </Button>
          </div>
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <Label
                htmlFor="phase-select"
                className="text-muted-foreground text-sm"
              >
                Phase
              </Label>
              <Select
                value={selectedPhase?.toString() ?? ""}
                onValueChange={(value) =>
                  setSelectedPhase(
                    value === "null" ? null : (Number(value) as PhaseType),
                  )
                }
              >
                <SelectTrigger
                  className="h-9 w-40 font-mono"
                  size="sm"
                  id="phase-select"
                >
                  <SelectValue placeholder="Select phase" />
                </SelectTrigger>
                <SelectContent className="font-mono">
                  <SelectItem value="null">
                    <span className="text-muted-foreground">Clear</span>
                  </SelectItem>
                  {Object.entries(PhaseType)
                    .filter(([, value]) => typeof value === "number")
                    .map(([key, value]) => (
                      <SelectItem key={value} value={value.toString()}>
                        {key}
                      </SelectItem>
                    ))}
                </SelectContent>
              </Select>
            </div>

            <div className="flex items-center justify-between">
              <Label
                htmlFor="state-select"
                className="text-muted-foreground text-sm"
              >
                State
              </Label>
              <Select
                value={selectedState?.toString() ?? ""}
                onValueChange={(value) =>
                  setSelectedState(
                    value === "null" ? null : (Number(value) as StateType),
                  )
                }
              >
                <SelectTrigger
                  className="h-9 w-40 font-mono"
                  size="sm"
                  id="state-select"
                >
                  <SelectValue placeholder="Select state" />
                </SelectTrigger>
                <SelectContent className="font-mono">
                  <SelectItem value="null">
                    <span className="text-muted-foreground">Clear</span>
                  </SelectItem>
                  {Object.entries(StateType)
                    .filter(([, value]) => typeof value === "number")
                    .map(([key, value]) => (
                      <SelectItem key={value} value={value.toString()}>
                        {key}
                      </SelectItem>
                    ))}
                </SelectContent>
              </Select>
            </div>

            <div className="flex items-center justify-between">
              <Label
                htmlFor="hammer-type-select"
                className="text-muted-foreground text-sm"
              >
                Hammer Type
              </Label>
              <Select
                value={selectedHammerType?.toString() ?? ""}
                onValueChange={(value) =>
                  setSelectedHammerType(
                    value === "null" ? null : (Number(value) as HammerType),
                  )
                }
              >
                <SelectTrigger
                  className="h-9 w-40 font-mono"
                  size="sm"
                  id="hammer-type-select"
                >
                  <SelectValue placeholder="Select hammer type" />
                </SelectTrigger>
                <SelectContent className="font-mono">
                  <SelectItem value="null">
                    <span className="text-muted-foreground">Clear</span>
                  </SelectItem>
                  {Object.entries(HammerType)
                    .filter(([, value]) => typeof value === "number")
                    .map(([key, value]) => (
                      <SelectItem key={value} value={value.toString()}>
                        {key}
                      </SelectItem>
                    ))}
                </SelectContent>
              </Select>
            </div>

            <Button
              onClick={handleManualOverrideClick}
              disabled={isOverrideDisabled}
              className="w-full cursor-pointer"
              size="sm"
            >
              Update
            </Button>
          </div>
        </div>
      </CardContent>

      <CardFooter></CardFooter>
    </Card>
  );
}
