import { ReactNode, useState } from "react";
import { Button } from "@/components/ui/button";
import { Slider } from "@/components/ui/slider";
import { Sun, Camera, Layers, ChevronLeft, ChevronRight } from "lucide-react";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { SceneConfiguration } from "@/lib/types/sceneConfig";
import { useVisibilityStore } from "@/store/controlsVisibilityStore";

interface SceneControlsProps {
  sceneConfiguration: SceneConfiguration;
  onUpdateSceneConfiguration: (
    key: keyof SceneConfiguration,
    value: any
  ) => void;
}

type ControlItem = {
  name: string;
  icon: ReactNode;
  color: string;
  control:
    | ReactNode
    | ((props: {
        selectedColor: string;
        setSelectedColor: (color: string) => void;
      }) => ReactNode);
};

export function SceneControls({
  sceneConfiguration,
  onUpdateSceneConfiguration,
}: SceneControlsProps) {
  const isVisible = useVisibilityStore((state) => state.isSceneControlsVisible);
  const toggleVisibility = useVisibilityStore(
    (state) => state.toggleSceneControls
  );
  const [lightConfig, setLightConfig] = useState({
    light_name: "controllable_Bottom_AreaLight",
    color: "#FFFFFF",
    strength: 50,
  });

  const handleUpdateLightConfig = (updates: Partial<typeof lightConfig>) => {
    setLightConfig((prev) => {
      const updatedConfig = { ...prev, ...updates };
      onUpdateSceneConfiguration("lights", updatedConfig); // Assuming this updates the scene externally
      return updatedConfig;
    });
  };

  const controls: ControlItem[] = [
    {
      name: "Light Controls",
      icon: <Sun className="h-5 w-5 mr-2" />,
      color: "#FFD100",
      control: ({
        selectedColor,
        setSelectedColor,
      }: {
        selectedColor: string;
        setSelectedColor: (color: string) => void;
      }) => (
        <div className="space-y-4">
          <div className="space-y-2">
            <label className="text-sm font-medium text-white">
              Select Light
            </label>
            <Select
              onValueChange={(value) =>
                handleUpdateLightConfig({ light_name: value })
              }
              value={lightConfig.light_name}
            >
              <SelectTrigger className="w-full">
                <SelectValue placeholder="Choose light" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="controllable_Left_AreaLight">
                  Left Area Light
                </SelectItem>
                <SelectItem value="controllable_Right_AreaLight">
                  Right Area Light
                </SelectItem>
                <SelectItem value="controllable_Top_AreaLight">
                  Top Area Light
                </SelectItem>
                <SelectItem value="controllable_Bottom_AreaLight">
                  Bottom Area Light
                </SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium text-white">Color</label>
            <Popover>
              <PopoverTrigger asChild>
                <Button
                  variant="outline"
                  className="w-full h-8 border border-white/20 bg-white/5 hover:bg-white/10"
                >
                  <div className="flex items-center justify-between w-full">
                    <span className="text-white">Select color</span>
                    <div
                      className="w-6 h-6 rounded-full border border-white/20"
                      style={{ backgroundColor: selectedColor }}
                    />
                  </div>
                </Button>
              </PopoverTrigger>
              <PopoverContent className="w-64 bg-cr8-charcoal border border-white/20 p-3 mt-2">
                <div className="grid grid-cols-5 gap-2 mb-2">
                  {[
                    "#FF0000",
                    "#00FF00",
                    "#0000FF",
                    "#FFFF00",
                    "#FF00FF",
                    "#00FFFF",
                    "#FFA500",
                    "#800080",
                    "#FFC0CB",
                    "#A52A2A",
                  ].map((color) => (
                    <Button
                      key={color}
                      variant="outline"
                      className="w-full h-8 rounded-md p-0 overflow-hidden"
                      onClick={() => handleUpdateLightConfig({ color })}
                    >
                      <div
                        className="w-full h-full"
                        style={{ backgroundColor: color }}
                      />
                    </Button>
                  ))}
                </div>
                <div className="flex items-center space-x-2">
                  <div
                    className="w-8 h-8 rounded border border-white/20"
                    style={{ backgroundColor: lightConfig.color }}
                  />
                  <input
                    type="color"
                    value={selectedColor}
                    onChange={(e) =>
                      handleUpdateLightConfig({ color: e.target.value })
                    }
                    className="w-full bg-cr8-charcoal border border-white/20 rounded h-8 cursor-pointer"
                  />
                </div>
              </PopoverContent>
            </Popover>
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium text-white">Strength</label>
            <Slider
              defaultValue={[lightConfig.strength]}
              min={100}
              max={1000}
              step={100}
              className="w-full"
              onValueChange={(values) =>
                handleUpdateLightConfig({ strength: values[0] })
              }
            />
          </div>
        </div>
      ),
    },
    {
      name: "Camera Controls",
      icon: <Camera className="h-5 w-5 mr-2" />,
      color: "#0077B6",
      control: (
        <div className="mt-2">
          <Select
            onValueChange={(value) =>
              onUpdateSceneConfiguration("camera", { camera_name: value })
            }
            value={sceneConfiguration.camera?.camera_name}
          >
            <SelectTrigger className="w-full">
              <SelectValue placeholder="Select camera" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="controllable_Main_Camera">
                Main Camera
              </SelectItem>
              <SelectItem value="controllable_GodView_Camera">
                GodView Camera
              </SelectItem>
              <SelectItem value="controllable_TopView_Camera">
                TopView Camera
              </SelectItem>
            </SelectContent>
          </Select>
        </div>
      ),
    },
    {
      name: "Variation",
      icon: <Layers className="h-5 w-5 mr-2" />,
      color: "#FF006E",
      control: (
        <div className="flex space-x-2 mt-2">
          {[
            { value: "V1", label: "V1" },
            { value: "V2", label: "V2" },
            { value: "V3", label: "V3" },
          ].map((item, index) => (
            <Button
              key={index}
              variant="outline"
              size="sm"
              className="flex-1"
              onClick={() => console.log(item.value)} // Replace with actual logic
            >
              {item.label}
            </Button>
          ))}
        </div>
      ),
    },
  ];

  return (
    <div
      className={`absolute left-4 top-1/2 transform -translate-y-1/2 transition-all duration-300 
      ${isVisible ? "translate-x-0" : "-translate-x-full"}`}
    >
      <Button
        variant="ghost"
        size="icon"
        className="absolute -right-12 top-0 text-white hover:bg-white/10"
        onClick={toggleVisibility}
      >
        {isVisible ? (
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
          {controls.map((control, index) => (
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
                <div className="mt-2 px-3">
                  {typeof control.control === "function"
                    ? control.control({
                        selectedColor: lightConfig.color,
                        setSelectedColor: (color) =>
                          setLightConfig((prev) => ({ ...prev, color })),
                      })
                    : control.control}
                </div>
              </AccordionContent>
            </AccordionItem>
          ))}
        </Accordion>
      </div>
    </div>
  );
}
