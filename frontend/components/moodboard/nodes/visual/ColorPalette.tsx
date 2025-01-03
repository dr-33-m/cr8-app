import { X, Plus } from "lucide-react";

interface ColorPaletteProps {
  colors: string[];
  onColorsChange: (colors: string[]) => void;
}

export function ColorPalette({ colors, onColorsChange }: ColorPaletteProps) {
  const addColor = (color: string) => {
    onColorsChange([...colors, color]);
  };

  const removeColor = (index: number) => {
    onColorsChange(colors.filter((_, i) => i !== index));
  };

  return (
    <div className="space-y-4">
      <h3 className="text-sm font-medium text-white">Color Palette</h3>

      <div className="flex flex-wrap gap-2">
        {colors.map((color, index) => (
          <div key={index} className="group relative">
            <div
              className="w-12 h-12 rounded-lg border-2 border-charcoal-700/50 cursor-pointer"
              style={{ backgroundColor: color }}
            />
            <button
              onClick={() => removeColor(index)}
              className="absolute -top-2 -right-2 p-1 rounded-full bg-charcoal-900/80 text-white opacity-0 group-hover:opacity-100 transition-opacity"
            >
              <X className="h-3 w-3" />
            </button>
          </div>
        ))}

        <label className="relative w-12 h-12 rounded-lg border-2 border-dashed border-charcoal-700/50 flex items-center justify-center cursor-pointer hover:border-blue-400/50 transition-colors">
          <input
            type="color"
            onChange={(e) => addColor(e.target.value)}
            className="opacity-0 absolute inset-0 w-full h-full cursor-pointer"
          />
          <Plus className="h-5 w-5 text-charcoal-400" />
        </label>
      </div>
    </div>
  );
}
