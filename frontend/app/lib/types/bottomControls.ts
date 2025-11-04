// Chat-related interfaces
export interface InboxMention {
  id: string;
  display: string;
  type: string;
  source: "inbox";
}

export interface SceneMention {
  id: string;
  display: string;
  type: string;
  source: "scene";
}

export interface ChatInputProps {
  inboxMentions: InboxMention[];
  sceneMentions: SceneMention[];
  renderInboxSuggestion: (
    suggestion: any,
    search: string,
    highlightedDisplay: React.ReactNode,
    index: number,
    focused: boolean
  ) => React.ReactNode;
  renderSceneSuggestion: (
    suggestion: any,
    search: string,
    highlightedDisplay: React.ReactNode,
    index: number,
    focused: boolean
  ) => React.ReactNode;
  onSendMessage: () => void;
}

// Navigation-related interfaces
export interface DPadProps {
  onPanUp: () => void;
  onPanDown: () => void;
  onPanLeft: () => void;
  onPanRight: () => void;
}

export interface OrbitProps {
  onOrbitUp: () => void;
  onOrbitDown: () => void;
  onOrbitLeft: () => void;
  onOrbitRight: () => void;
}

export interface ZoomProps {
  onZoomIn: () => void;
  onZoomOut: () => void;
}

// Additional bottom controls interfaces
export interface ChatActionsProps {
  onSendMessage: () => void;
}

export interface BottomControlsProps {
  children?: React.ReactNode;
}

// Hook interfaces
export type AnimationState = "playing" | "paused" | "playing_reverse";

export interface MentionData {
  id: string;
  name: string;
  type: "inbox" | "scene";
  itemType: string;
  source: "inbox" | "scene";
}

export type ViewportMode = "solid" | "rendered";
