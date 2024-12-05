import { Button } from "@/components/ui/button";
import { Slider } from "@/components/ui/slider";
import {
  Palette,
  Move,
  ArrowUpDown,
  Layers,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";

interface SceneControlsProps {
  isVisible: boolean;
  onToggleVisibility: () => void;
}

const controls = [
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

export function SceneControls({
  isVisible,
  onToggleVisibility,
}: SceneControlsProps) {
  return (
    <div
      className={`absolute left-4 top-1/2 transform -translate-y-1/2 transition-all duration-300 
      ${isVisible ? "translate-x-0" : "-translate-x-full"}`}
    >
      <Button
        variant="ghost"
        size="icon"
        className="absolute -right-12 top-0 text-white hover:bg-white/10"
        onClick={onToggleVisibility}
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
                <div className="mt-2 px-3">{control.control}</div>
              </AccordionContent>
            </AccordionItem>
          ))}
        </Accordion>
      </div>
    </div>
  );
}
