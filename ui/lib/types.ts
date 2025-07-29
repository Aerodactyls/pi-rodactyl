export enum PhaseType {
  SEARCH = 0,
  TOWER = 1,
  HAMMER_PICKUP = 2,
  HAMMER_DROPOFF = 3,
  HAT_DROPOFF = 4,
}

export enum StateType {
  IDLE = 0,
  ARM = 1,
  ASCEND_MSA = 2,
  NAVIGATE = 3,
  // PRECISION_DESCENT = 4,
  // ALIGN_NEXT_TO_TOWER = 5,
  // DESCEND_NEXT_TO_TOWER = 6,
  // CIRCLE_TOWER = 7,
  PRECISION_LANDING = 8,
  PAYLOAD_ACTION = 9,
  ARM_TO_RTL = 10,
  SEARCH_GRID = 11,
  INSPECT_TOWER = 12,
  DESCEND_POI = 13,
  TOWER_INSPECTION_FINISHED = 14,
  POI_ADJUSTMENT = 15,
}

export enum HammerType {
  CLAW = 0,
  BALLPEEN = 1,
  UNKNOWN = 2,
}

export interface HeartbeatData {
  //
}

export interface StateMachineData {
  phase: PhaseType;
  state: StateType;
  connected: boolean;

  known_hammer_type: HammerType;
  tower_pos_found: boolean;
  claw_pickup_pos_found: boolean;
  ballpeen_pickup_pos_found: boolean;
  hammer_dropoff_pos_found: boolean;
}

export enum FlowState {
  Idle = "Idle",
  ArmVehicle = "ArmVehicle",
  AscendToMSA = "AscendToMSA",
  PreSearchGrid = "PreSearchGrid",
  NavigateToPoi = "NavigateToPoi",
  DescendPoi = "DescendPoi",
  NavigateToTower = "NavigateToTower",
  InspectTower = "InspectTower",
  TowerInspectionFinished = "TowerInspectionFinished",
  NavigateToHammerPickup = "NavigateToHammerPickup",
  PrecisionLandHammerPickup = "PrecisionLandHammerPickup",
  PickUpHammer = "PickUpHammer",
  NavigateToHammerDropoff = "NavigateToHammerDropoff",
  PrecisionLandHammerDropoff = "PrecisionLandHammerDropoff",
  DropOffHammer = "DropOffHammer",
  NavigateToHatDropoff = "NavigateToHatDropoff",
  PrecisionLandHatDropoff = "PrecisionLandHatDropoff",
  DropOffHat = "DropOffHat",
  ArmToRtl = "ArmToRtl",
}

export type PhaseState = { phase: PhaseType | null; state: StateType };
export type FlowTarget = { phase: PhaseType | null; state: StateType };

// prettier-ignore
const phaseFlowPairs = [
  [{ phase: null, state: StateType.IDLE }, FlowState.Idle],
  [{ phase: null, state: StateType.ARM }, FlowState.ArmVehicle],
  [{ phase: null, state: StateType.ASCEND_MSA }, FlowState.AscendToMSA],
  [{ phase: null, state: StateType.ARM_TO_RTL }, FlowState.ArmToRtl],
  
  [{ phase: PhaseType.SEARCH, state: StateType.SEARCH_GRID }, FlowState.PreSearchGrid],
  [{ phase: PhaseType.SEARCH, state: StateType.POI_ADJUSTMENT }, FlowState.NavigateToPoi],
  [{ phase: PhaseType.SEARCH, state: StateType.DESCEND_POI }, FlowState.DescendPoi],
  
  [{ phase: PhaseType.TOWER, state: StateType.NAVIGATE }, FlowState.NavigateToTower],
  [{ phase: PhaseType.TOWER, state: StateType.INSPECT_TOWER }, FlowState.InspectTower],
  [{ phase: PhaseType.TOWER, state: StateType.TOWER_INSPECTION_FINISHED }, FlowState.TowerInspectionFinished],
  
  [{ phase: PhaseType.HAMMER_PICKUP, state: StateType.NAVIGATE }, FlowState.NavigateToHammerPickup],
  [{ phase: PhaseType.HAMMER_PICKUP, state: StateType.PRECISION_LANDING }, FlowState.PrecisionLandHammerPickup],
  [{ phase: PhaseType.HAMMER_PICKUP, state: StateType.PAYLOAD_ACTION }, FlowState.PickUpHammer],
  
  [{ phase: PhaseType.HAMMER_DROPOFF, state: StateType.NAVIGATE }, FlowState.NavigateToHammerDropoff],
  [{ phase: PhaseType.HAMMER_DROPOFF, state: StateType.PRECISION_LANDING }, FlowState.PrecisionLandHammerDropoff],
  [{ phase: PhaseType.HAMMER_DROPOFF, state: StateType.PAYLOAD_ACTION }, FlowState.DropOffHammer],
  
  [{ phase: PhaseType.HAT_DROPOFF, state: StateType.NAVIGATE }, FlowState.NavigateToHatDropoff],
  [{ phase: PhaseType.HAT_DROPOFF, state: StateType.PRECISION_LANDING }, FlowState.PrecisionLandHatDropoff],
  [{ phase: PhaseType.HAT_DROPOFF, state: StateType.PAYLOAD_ACTION }, FlowState.DropOffHat],
] as const satisfies ReadonlyArray<readonly [PhaseState, FlowState]>;

export class PhaseStateMap<V> {
  private map = new Map<string, V>();

  private key(phaseState: PhaseState): string {
    return `${phaseState.phase ?? "null"}-${phaseState.state}`;
  }

  set(phaseState: PhaseState, value: V): this {
    this.map.set(this.key(phaseState), value);
    return this;
  }

  get(phaseState: PhaseState): V | undefined {
    return this.map.get(this.key(phaseState));
  }

  has(phaseState: PhaseState): boolean {
    return this.map.has(this.key(phaseState));
  }
}

const phaseToFlow = new PhaseStateMap<FlowState>();
const flowToPhase = new Map<FlowState, PhaseState>();

for (const [phaseState, flowState] of phaseFlowPairs) {
  phaseToFlow.set(phaseState, flowState);
  flowToPhase.set(flowState, phaseState);
}

export function getFlowState(
  phase: PhaseType,
  state: StateType,
): FlowState | undefined {
  let result = phaseToFlow.get({ phase, state });
  if (result) {
    return result;
  }

  return phaseToFlow.get({ phase: null, state });
}

export function getPhaseState(flow: FlowState): FlowTarget | undefined {
  return flowToPhase.get(flow);
}

type Message<T extends string, D> = {
  type: T;
  data: D;
};

export type HeartbeatMessage = Message<"heartbeat", HeartbeatData>;
export type StateMachineMessage = Message<
  "state_machine_data",
  StateMachineData
>;

export type MessageData = HeartbeatMessage | StateMachineMessage;
