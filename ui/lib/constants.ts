import { positionManager } from "@/lib/position-manager";
import { FlowState } from "@/lib/types";

export const NODE_STYLES = {
  blue: {
    background: "#e3f2fd",
    border: "1.5px solid #1976d2",
  },
  yellow: {
    background: "#fffde7",
    border: "1.5px solid #fbc02d",
  },
  pink: {
    background: "#fce4ec",
    border: "1.5px solid #d81b60",
  },
  green: {
    background: "#e8f5e9",
    border: "1.5px solid #388e3c",
  },
  purple: {
    background: "#ede7f6",
    border: "1.5px solid #512da8",
  },
  orange: {
    background: "#fff3e0",
    border: "1.5px solid #f57c00",
  },
} as const;

export interface NodeConfig {
  id: FlowState;
  label: string;
  position: { x: number; y: number };
  group: keyof typeof NODE_STYLES;
}

const {
  Idle,
  ArmVehicle,
  AscendToMSA,
  PreSearchGrid,
  NavigateToPoi,
  DescendPoi,
  NavigateToTower,
  InspectTower,
  TowerInspectionFinished,
  NavigateToHammerPickup,
  PrecisionLandHammerPickup,
  PickUpHammer,
  NavigateToHammerDropoff,
  PrecisionLandHammerDropoff,
  DropOffHammer,
  NavigateToHatDropoff,
  PrecisionLandHatDropoff,
  DropOffHat,
  ArmToRtl,
} = FlowState;

export const NODE_CONFIGS: NodeConfig[] = [
  // System
  {
    id: Idle,
    label: "Idle",
    position: { x: 50, y: 50 },
    group: "orange",
  },
  {
    id: ArmVehicle,
    label: "Arm the vehicle",
    position: { x: 300, y: 15 },
    group: "blue",
  },
  {
    id: AscendToMSA,
    label: "Ascend to MSA",
    position: { x: 300, y: 100 },
    group: "blue",
  },

  // Search
  {
    id: PreSearchGrid,
    label: "Search grid",
    position: { x: 100, y: 200 },
    group: "purple",
  },
  {
    id: NavigateToPoi,
    label: "Pilot POI Adjustment",
    position: { x: 100, y: 305 },
    group: "purple",
  },
  {
    id: DescendPoi,
    label: "Descend on POI",
    position: { x: 100, y: 305 },
    group: "purple",
  },

  // Tower
  {
    id: NavigateToTower,
    label: "Navigate to tower",
    position: { x: 400, y: 200 },
    group: "yellow",
  },
  {
    id: InspectTower,
    label: "Inspect tower",
    position: { x: 400, y: 305 },
    group: "yellow",
  },
  {
    id: TowerInspectionFinished,
    label: "Tower inspection finished",
    position: { x: 400, y: 410 },
    group: "yellow",
  },

  // Hammer pickup
  {
    id: NavigateToHammerPickup,
    label: "Navigate to hammer pickup",
    position: { x: 0, y: 200 },
    group: "green",
  },
  {
    id: PrecisionLandHammerPickup,
    label: "Precision land hammer pickup",
    position: { x: 0, y: 305 },
    group: "green",
  },
  {
    id: PickUpHammer,
    label: "Pick up hammer",
    position: { x: 0, y: 415 },
    group: "green",
  },

  // Hammer dropoff
  {
    id: NavigateToHammerDropoff,
    label: "Navigate to hammer dropoff",
    position: { x: 200, y: 200 },
    group: "pink",
  },
  {
    id: PrecisionLandHammerDropoff,
    label: "Precision land hammer dropoff",
    position: { x: 200, y: 305 },
    group: "pink",
  },
  {
    id: DropOffHammer,
    label: "Drop off hammer",
    position: { x: 200, y: 415 },
    group: "pink",
  },

  // Hat dropoff
  {
    id: NavigateToHatDropoff,
    label: "Navigate to hat dropoff",
    position: { x: 600, y: 200 },
    group: "purple",
  },
  {
    id: PrecisionLandHatDropoff,
    label: "Precision land hat dropoff",
    position: { x: 600, y: 305 },
    group: "purple",
  },
  {
    id: DropOffHat,
    label: "Drop off hat",
    position: { x: 600, y: 415 },
    group: "purple",
  },
  {
    id: ArmToRtl,
    label: "Arm to RTL",
    position: { x: 300, y: 750 },
    group: "blue",
  },
];

export async function getNodeConfigsWithPositions(): Promise<NodeConfig[]> {
  await positionManager.ensureLoaded();
  return NODE_CONFIGS.map((config) => {
    const savedPosition = positionManager.getPosition(config.id);
    return {
      ...config,
      position: savedPosition || config.position,
    };
  });
}

export const EDGE_PAIRS: [FlowState, FlowState][] = [
  [ArmVehicle, AscendToMSA],

  [AscendToMSA, PreSearchGrid],
  [PreSearchGrid, NavigateToPoi],
  [NavigateToPoi, DescendPoi],
  [DescendPoi, AscendToMSA],

  [AscendToMSA, NavigateToTower],
  [NavigateToTower, InspectTower],
  [InspectTower, TowerInspectionFinished],
  [TowerInspectionFinished, ArmToRtl],

  [AscendToMSA, NavigateToHammerPickup],
  [NavigateToHammerPickup, PrecisionLandHammerPickup],
  [PrecisionLandHammerPickup, PickUpHammer],
  [PickUpHammer, AscendToMSA],

  [AscendToMSA, NavigateToHammerDropoff],
  [NavigateToHammerDropoff, PrecisionLandHammerDropoff],
  [PrecisionLandHammerDropoff, DropOffHammer],
  [DropOffHammer, ArmToRtl],

  [AscendToMSA, NavigateToHatDropoff],
  [NavigateToHatDropoff, PrecisionLandHatDropoff],
  [PrecisionLandHatDropoff, DropOffHat],
  [DropOffHat, ArmToRtl],
];
