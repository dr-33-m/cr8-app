import { AssetType } from "@/lib/services/polyhavenService";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";

interface AssetTypeTabsProps {
  selectedType: AssetType;
  onTypeChange: (type: AssetType) => void;
  className?: string;
}

export function AssetTypeTabs({
  selectedType,
  onTypeChange,
  className = "",
}: AssetTypeTabsProps) {
  return (
    <Tabs
      value={selectedType}
      onValueChange={(value) => onTypeChange(value as AssetType)}
      className={className}
    >
      <TabsList className="grid w-full grid-cols-3 bg-white/5 border border-white/10">
        <TabsTrigger value="hdris">HDRIs</TabsTrigger>
        <TabsTrigger value="textures">Textures</TabsTrigger>
        <TabsTrigger value="models">Models</TabsTrigger>
      </TabsList>
    </Tabs>
  );
}
