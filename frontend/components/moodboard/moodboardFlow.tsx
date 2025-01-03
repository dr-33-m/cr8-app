import { useCallback } from "react";
import ReactFlow, {
  Background,
  Controls,
  Node,
  Edge,
  useNodesState,
  useEdgesState,
  addEdge,
} from "reactflow";
import "reactflow/dist/style.css";
import { VisualNode } from "./nodes/VisualNode";
import { TextualNode } from "./nodes/TextualNode";
import { ContextualNode } from "./nodes/ContextualNode";
import { SummaryNode } from "./nodes/SummaryNode";
import { isBrowser } from "@/lib/utils";

const nodeTypes = {
  visual: VisualNode,
  textual: TextualNode,
  contextual: ContextualNode,
  summary: SummaryNode,
};

const initialNodes: Node[] = [
  {
    id: "visual",
    type: "visual",
    position: { x: 400, y: 50 },
    data: {},
  },
  {
    id: "textual",
    type: "textual",
    position: { x: 100, y: 500 },
    data: {},
  },
  {
    id: "contextual",
    type: "contextual",
    position: { x: 700, y: 500 },
    data: {},
  },
  {
    id: "summary",
    type: "summary",
    position: { x: 400, y: 800 },
    data: {},
  },
];

const initialEdges: Edge[] = [
  {
    id: "visual-textual",
    source: "visual",
    target: "textual",
    type: "smoothstep",
    animated: true,
    className: "animated-edge",
  },
  {
    id: "visual-contextual",
    source: "visual",
    target: "contextual",
    type: "smoothstep",
    animated: true,
    className: "animated-edge",
  },
  {
    id: "textual-summary",
    source: "textual",
    target: "summary",
    type: "smoothstep",
    animated: true,
    className: "animated-edge",
  },
  {
    id: "contextual-summary",
    source: "contextual",
    target: "summary",
    type: "smoothstep",
    animated: true,
    className: "animated-edge",
  },
];

export function MoodboardFlow() {
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

  const onConnect = useCallback(
    (params: any) => {
      setEdges((eds) =>
        addEdge(
          {
            ...params,
            type: "smoothstep",
            animated: true,
            className: "animated-edge",
          },
          eds
        )
      );
    },
    [setEdges]
  );

  return (
    <div className="h-full w-full bg-cr8-charcoal">
      {isBrowser ? (
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          nodeTypes={nodeTypes}
          defaultViewport={{ x: 0, y: 0, zoom: 0.6 }}
          fitView
        >
          <Background className="bg-cr8-charcoal" />
          <Controls />
        </ReactFlow>
      ) : null}
    </div>
  );
}
