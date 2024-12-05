import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import { Slider } from "@/components/ui/slider";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Play,
  ChevronLeft,
  ChevronRight,
  RotateCcw,
  ZoomIn,
  Move,
  Palette,
  ArrowUpDown,
  Layers,
  ChevronDown,
  ChevronUp,
} from "lucide-react";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";

export const Route = createFileRoute("/project")({
  component: RouteComponent,
});

type SceneControl = {
  name: string;
  icon: React.ReactNode;
  color: string;
  control: React.ReactNode;
};

function RouteComponent() {
  const [selectedAsset, setSelectedAsset] = useState<number | null>(null);
  const [isControlsVisible, setIsControlsVisible] = useState<boolean>(true);
  const [isSceneControlsVisible, setIsSceneControlsVisible] =
    useState<boolean>(true);
  const [isAssetSelectionVisible, setIsAssetSelectionVisible] =
    useState<boolean>(true);
  const [isBottomControlsVisible, setIsBottomControlsVisible] =
    useState<boolean>(true);
  const [viewportImage, setViewportImage] = useState<string | null>(null);
  const websocketRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    // Establish WebSocket connection
    const ws = new WebSocket("ws://localhost:5001/browser");
    websocketRef.current = ws;

    ws.onopen = () => {
      console.log("WebSocket connection established");
      // Send initialization message
      ws.send(JSON.stringify({ action: "initialize" }));
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);

        // Handle viewport stream
        if (data.type === "frame") {
          // Directly use base64 data
          setViewportImage(`data:image/png;base64,${data.data}`);
        } else if (data.type === "viewport_stream_error") {
          console.error("Viewport stream error:", data.message);
          setViewportImage(null);
        }
      } catch (error) {
        console.error("Error parsing WebSocket message:", error);
      }
    };

    ws.onerror = (error) => {
      console.error("WebSocket error:", error);
    };

    ws.onclose = () => {
      console.log("WebSocket connection closed");
    };

    // Cleanup on component unmount
    return () => {
      if (ws) {
        ws.close();
      }
    };
  }, []);

  const handleStreamViewport = () => {
    if (
      websocketRef.current &&
      websocketRef.current.readyState === WebSocket.OPEN
    ) {
      websocketRef.current.send(
        JSON.stringify({
          command: "start_preview_rendering",
          params: {
            resolution_x: 1920,
            resolution_y: 1080,
            samples: 16,
            num_frames: 40,
          },
          // command: "start_broadcast",
        })
      );
    } else {
      console.error("WebSocket is not open");
    }
  };

  const sceneControls: SceneControl[] = [
    {
      name: "Color",
      icon: <Palette className="h-5 w-5 mr-2" />,
      color: "#0077B6",
      control: (
        <div className="flex space-x-4 mt-2">
          <div className="w-8 h-8 rounded-lg bg-red-500 cursor-pointer" />
          <div className="w-8 h-8 rounded-lg bg-green-500 cursor-pointer" />
          <div className="w-8 h-8 rounded-lg bg-blue-500 cursor-pointer" />
        </div>
      ),
    },
    {
      name: "Move",
      icon: <Move className="h-5 w-5 mr-2" />,
      color: "#5C0A98",
      control: (
        <div className="mt-4 mb-2">
          <Slider defaultValue={[50]} max={100} step={1} className="w-full" />
        </div>
      ),
    },
    {
      name: "Scale",
      icon: <ArrowUpDown className="h-5 w-5 mr-2" />,
      color: "#FF006E",
      control: (
        <div className="mt-4 mb-2">
          <Slider defaultValue={[50]} max={100} step={1} className="w-full" />
        </div>
      ),
    },
    {
      name: "Variation",
      icon: <Layers className="h-5 w-5 mr-2" />,
      color: "#FFD100",
      control: (
        <div className="flex space-x-2 mt-2">
          <Button variant="outline" size="sm" className="flex-1">
            V1
          </Button>
          <Button variant="outline" size="sm" className="flex-1">
            V2
          </Button>
          <Button variant="outline" size="sm" className="flex-1">
            V3
          </Button>
        </div>
      ),
    },
  ];

  return (
    <div className="relative w-full h-screen bg-[#1C1C1C] text-white overflow-hidden">
      {/* Full-screen 3D Preview */}
      <div className="absolute inset-0 bg-gradient-to-br from-[#2C2C2C] to-[#1C1C1C] z-10">
        {viewportImage ? (
          <img
            src={viewportImage}
            alt="Blender Viewport"
            className="w-full h-full object-cover"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-[#FFD100]">
            No viewport stream available
          </div>
        )}
      </div>
      <div className="absolute inset-0 bg-gradient-to-br from-[#2C2C2C] to-[#1C1C1C]">
        {/* This is where your 3D preview would go */}
      </div>

      {/* Overlay Controls */}
      <div
        className={`z-20 absolute inset-0 transition-opacity duration-300 ${isControlsVisible ? "opacity-100" : "opacity-0 pointer-events-none"}`}
      >
        {/* Left Sidebar - Scene Controls */}
        <div
          className={`absolute left-4 top-1/2 transform -translate-y-1/2 transition-all duration-300 ${isSceneControlsVisible ? "translate-x-0" : "-translate-x-full"}`}
        >
          <Button
            variant="ghost"
            size="icon"
            className="absolute -right-12 top-0 text-white hover:bg-white/10"
            onClick={() => setIsSceneControlsVisible(!isSceneControlsVisible)}
          >
            {isSceneControlsVisible ? (
              <ChevronLeft className="h-6 w-6" />
            ) : (
              <ChevronRight className="h-6 w-6" />
            )}
          </Button>
          <div className="backdrop-blur-md bg-white/5 rounded-lg p-4 w-80 max-h-[80vh] overflow-y-auto">
            <h2 className="text-xl font-semibold mb-4 text-white">
              Scene Controls
            </h2>
            <Accordion type="single" collapsible className="w-full space-y-2">
              {sceneControls.map((control, index) => (
                <AccordionItem
                  value={`item-${index}`}
                  key={index}
                  className="border-b border-white/10 pb-2"
                >
                  <AccordionTrigger
                    className={`hover:bg-white/10 rounded-lg px-3 py-2`}
                    style={{ color: control.color }}
                  >
                    <div className="flex items-center">
                      {control.icon}
                      <span>{control.name}</span>
                    </div>
                  </AccordionTrigger>
                  <AccordionContent>
                    <div className="mt-2 px-3">{control.control}</div>
                  </AccordionContent>
                </AccordionItem>
              ))}
            </Accordion>
          </div>
        </div>

        {/* Right Sidebar - Asset Selection */}
        <div
          className={`z-20 absolute right-4 top-1/2 transform -translate-y-1/2 transition-all duration-300 ${isAssetSelectionVisible ? "translate-x-0" : "translate-x-full"}`}
        >
          <Button
            variant="ghost"
            size="icon"
            className="absolute -left-12 top-0 text-white hover:bg-white/10"
            onClick={() => setIsAssetSelectionVisible(!isAssetSelectionVisible)}
          >
            {isAssetSelectionVisible ? (
              <ChevronRight className="h-6 w-6" />
            ) : (
              <ChevronLeft className="h-6 w-6" />
            )}
          </Button>
          <div className="backdrop-blur-md bg-white/5 rounded-lg p-4 w-80">
            <h2 className="text-xl font-semibold mb-4 text-white">
              Select Assets
            </h2>
            <Tabs defaultValue="Clothes" className="w-full">
              <TabsList className="grid w-full grid-cols-3 mb-4 bg-white/5">
                <TabsTrigger
                  value="Clothes"
                  className="data-[state=active]:bg-[#0077B6] data-[state=active]:text-white"
                >
                  Clothing
                </TabsTrigger>
                <TabsTrigger
                  value="Venues"
                  className="data-[state=active]:bg-[#5C0A98] data-[state=active]:text-white"
                >
                  Venues
                </TabsTrigger>
                <TabsTrigger
                  value="Performances"
                  className="data-[state=active]:bg-[#FF006E] data-[state=active]:text-white"
                >
                  Performances
                </TabsTrigger>
              </TabsList>
              <TabsContent value="Clothes" className="grid grid-cols-3 gap-2">
                {[1, 2, 3, 4, 5, 6].map((i) => (
                  <div
                    key={i}
                    className={`aspect-square bg-white/10 rounded-lg cursor-pointer hover:ring-2 hover:ring-[#FFD100] transition-all ${
                      selectedAsset === i ? "ring-2 ring-[#FFD100]" : ""
                    }`}
                    onClick={() => setSelectedAsset(i)}
                    role="button"
                    tabIndex={0}
                    aria-label={`Select asset ${i}`}
                  />
                ))}
              </TabsContent>
              <TabsContent value="Venues">
                <p className="text-white/70">Venues here</p>
              </TabsContent>
              <TabsContent value="Performances">
                <p className="text-white/70">Performances here</p>
              </TabsContent>
            </Tabs>
          </div>
        </div>

        {/* Bottom Controls */}
        <div
          className={`z-20 absolute bottom-4 left-1/2 transform -translate-x-1/2 transition-all duration-300 ${isBottomControlsVisible ? "translate-y-0" : "translate-y-full"}`}
        >
          <Button
            variant="ghost"
            size="icon"
            className="absolute left-1/2 -top-12 -translate-x-1/2 text-white hover:bg-white/10"
            onClick={() => setIsBottomControlsVisible(!isBottomControlsVisible)}
          >
            {isBottomControlsVisible ? (
              <ChevronDown className="h-6 w-6" />
            ) : (
              <ChevronUp className="h-6 w-6" />
            )}
          </Button>
          <div className="backdrop-blur-md bg-white/5 rounded-lg px-6 py-3 flex items-center space-x-6">
            <Button
              variant="ghost"
              size="icon"
              className="text-white hover:bg-white/10"
              title="Previous"
            >
              <ChevronLeft className="h-6 w-6" />
              <span className="sr-only">Previous</span>
            </Button>
            <Button
              variant="ghost"
              size="icon"
              className="text-[#FFD100] hover:bg-[#FFD100]/10"
              title="Play Preview"
              onClick={handleStreamViewport}
            >
              <Play className="h-6 w-6" />
              <span className="sr-only">Play Preview</span>
            </Button>
            <Button
              variant="ghost"
              size="icon"
              className="text-white hover:bg-white/10"
              title="Next"
            >
              <ChevronRight className="h-6 w-6" />
              <span className="sr-only">Next</span>
            </Button>
            <div className="h-8 w-px bg-white/20" />
            <Button
              variant="ghost"
              size="icon"
              className="text-white hover:bg-white/10"
              title="Rotate"
            >
              <RotateCcw className="h-5 w-5" />
              <span className="sr-only">Rotate</span>
            </Button>
            <Button
              variant="ghost"
              size="icon"
              className="text-white hover:bg-white/10"
              title="Zoom"
            >
              <ZoomIn className="h-5 w-5" />
              <span className="sr-only">Zoom</span>
            </Button>
            <Button
              variant="ghost"
              size="icon"
              className="text-white hover:bg-white/10"
              title="Pan"
            >
              <Move className="h-5 w-5" />
              <span className="sr-only">Pan</span>
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
